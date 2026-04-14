import re
import email
import email.header
import imaplib
import time
import traceback
from datetime import datetime, timedelta
from dateutil.parser import parse
import requests
from loguru import logger


class OauthEmailReceiver:
    """
    使用oauth2.0协议登录微软邮箱
    """
    ec = None
    client_id = '9e5f94bc-e8a4-4e73-b8be-63364c29d753'

    def __init__(self, email, passwd, client_id=None):
        self.email = email
        self.passwd = passwd
        self.server = 'outlook.live.com'
        self.client_id = client_id if client_id else self.client_id

    def generate_auth_string(self, user, token):
        return f"user={user}\1auth=Bearer {token}\1\1"

    def get_accesstoken(self, refresh_token):
        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token.replace('$$', '').replace('$', ''),
        }
        for _ in range(3):
            try:
                ret = requests.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data=data)
                return ret.json().get('access_token')
            except Exception:
                pass
        return None

    def login(self):
        self.access_token = self.get_accesstoken(self.passwd)
        if not self.access_token:
            return False
        try:
            self.mail = imaplib.IMAP4_SSL('outlook.live.com')
            self.mail.authenticate('XOAUTH2', lambda x: self.generate_auth_string(self.email, self.access_token))
            return True
        except Exception:
            return False

    def tuple_to_str(self, tuple_):
        if tuple_[1]:
            return tuple_[0].decode(tuple_[1])
        if isinstance(tuple_[0], bytes):
            return tuple_[0].decode('gbk')
        return tuple_[0]

    def fetch_email_body(self, item):
        try:
            ret, data = self.mail.fetch(item, '(RFC822)')
            msg = email.message_from_string(data[0][1].decode('utf-8'))
            sub_text = email.header.decode_header(str(msg.get('subject')))
            From_text = email.header.decode_header(str(msg.get('From')))
            To_text = email.header.decode_header(str(msg.get('To')))
            ts = parse(msg.get('Date')).timestamp()

            sub_detail = self.tuple_to_str(sub_text[0]) if sub_text[0] else ''
            content = ''
            for part in msg.walk():
                if not part.is_multipart():
                    content_type = part.get_content_type()
                    if not part.get_filename() and content_type in ('text/html', 'text/plain'):
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            # 尝试多种编码方式解码
                            for encoding in ('utf-8', 'gbk', 'gb2312'):
                                try:
                                    content += payload.decode(encoding)
                                    break
                                except (UnicodeDecodeError, LookupError):
                                    continue
                            else:
                                # 所有编码都失败，使用 utf-8 并忽略错误
                                content += payload.decode('utf-8', errors='ignore')
                        elif payload:
                            content += str(payload)
            return {
                'Subject': sub_detail,
                'content': content,
                'From': self.tuple_to_str(From_text[0]),
                'To': self.tuple_to_str(To_text[0]),
                'Date': ts,
            }
        except Exception as e:
            logger.error(f'fetch_email_body 失败: {e}')

    def get_last_email(self, index=-1, num=10):
        try:
            try:
                self.mail.noop()
            except Exception:
                logger.info(f"IMAP连接已断开，尝试重新登录: {self.email}")
                if not self.login():
                    logger.error(f"IMAP重新登录失败: {self.email}")
                    return []

            msgs = []
            since = (datetime.now().date() - timedelta(days=10)).strftime('%d-%b-%Y')
            for folder in ('INBOX', 'Junk'):
                self.mail.select(folder)
                _, items = self.mail.search(None, f'SINCE {since}')
                for emailid in items[0].split()[::-1][:num]:
                    msgs.append(self.fetch_email_body(emailid))
            return msgs
        except Exception:
            logger.error(f'收邮件错误:\n{traceback.format_exc()}')
            return []


class OutlookGraphClient:
    """
    通过 Microsoft Graph API 获取 Outlook 邮件的客户端
    """
    ec = None
    TOKEN_URL = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    client_id = '9e5f94bc-e8a4-4e73-b8be-63364c29d753'

    def __init__(self, email, passwd, client_id=None):
        self.email = email
        self.passwd = passwd
        self.server = 'outlook.live.com'
        self.client_id = client_id if client_id else self.client_id
        self.refresh_token = self.passwd.replace('$$', '').replace('$', '')

    def login(self):
        self.access_token = self._get_access_token()
        if not self.access_token:
            return False
        self.ec = OauthEmailReceiver(self.email, self.refresh_token, self.client_id)
        self.ec.client_id = self.client_id
        self.ec.access_token = self.access_token
        if not self.ec.login():
            self.ec = None
        return True

    def login_with_existing_token(self, access_token: str):
        """使用已有的 access_token 初始化客户端，跳过 OAuth 请求"""
        self.access_token = access_token
        self.ec = OauthEmailReceiver(self.email, self.refresh_token, self.client_id)
        self.ec.client_id = self.client_id
        self.ec.access_token = access_token
        if not self.ec.login():
            self.ec = None
        return True

    def _get_access_token(self) -> str:
        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        resp = None
        try:
            resp = requests.post(self.TOKEN_URL, data=data)
            resp.raise_for_status()
            res = resp.json()
            self.scope = res.get('scope', '')
            new_refresh_token = res.get('refresh_token')
            if new_refresh_token:
                self.refresh_token = new_refresh_token
            return res.get('access_token')
        except Exception:
            if resp is not None:
                logger.error(f'【{self.email}】获取 access_token 失败: {resp.text}')
        return None

    def fetch_message_body(self, message_id: str, as_text: bool = True) -> dict:
        url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Prefer': 'text' if as_text else 'html',
            'Accept': 'application/json',
        }
        resp = requests.get(url, headers=headers, params={'$select': 'subject,from,receivedDateTime,body'})
        resp.raise_for_status()
        data = resp.json()
        return {
            'Subject': data.get('subject'),
            'content': data.get('body', {}).get('content'),
            'From': data.get('from', {}).get('emailAddress', {}).get('address'),
            'To': self.email,
            'Date': parse(data['receivedDateTime']).timestamp(),
        }

    def get_last_email(self, index=-1, num=10, as_html=False) -> list:
        if self.ec:
            return self.ec.get_last_email(num=num)
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }
        try:
            resp = requests.get(
                'https://graph.microsoft.com/v1.0/me/messages',
                headers=headers,
                params={'$top': num, '$select': 'id,receivedDateTime'}
            )
            resp.raise_for_status()
            messages = resp.json().get('value', [])
        except Exception:
            return []

        recent_msgs = []
        now = time.time()
        cutoff = 20 * 24 * 3600
        for msg in messages:
            if now - parse(msg['receivedDateTime']).timestamp() > cutoff:
                continue
            try:
                body = self.fetch_message_body(msg['id'], as_text=not as_html)
            except requests.HTTPError as e:
                if e.response.status_code == 401:
                    self.access_token = self._get_access_token()
                    body = self.fetch_message_body(msg['id'], as_text=not as_html)
                else:
                    raise
            recent_msgs.append(body)
            if len(recent_msgs) >= num:
                break
        return recent_msgs
