import re
from dateutil.parser import parse
from datetime import datetime, timedelta
import imaplib
import poplib
from dateutil.parser import parse
import requests
import time 
import os
import email
import email.header
import requests
from loguru import logger
from dateutil.parser import parse


class OauthEmailReceiver:
    """
    使用oauth2.0协议登录微软邮箱
    """
    ec=None
    client_id='9e5f94bc-e8a4-4e73-b8be-63364c29d753'
    def __init__(self,email,passwd,client_id=None):
        self.email=email
        self.passwd=passwd
        self.server='outlook.live.com'
        self.client_id=client_id if client_id else self.client_id
        

    def generate_auth_string(self,user, token):
        auth_string = f"user={user}\1auth=Bearer {token}\1\1"
        return auth_string


    def get_accesstoken(self,refresh_token):
        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token.replace('$$','').replace('$',''),
            # 'scope':'https%3A%2F%2Fgraph.microsoft.com%2Fmail.read'
        }
        for _ in range(3):
            try:
                ret = requests.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data=data)
                # print(ret.text)
                return ret.json().get('access_token')
            except:
                import traceback
                traceback.print_exc()
                pass 
        return None
    
    def get_accesstokenv2(self,refresh_token):
        data = {
            'client_id': '9e5f94bc-e8a4-4e73-b8be-63364c29d753',
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope':'https%3A%2F%2Fgraph.microsoft.com%2Fmail.read'
        }
        for _ in range(3):
            try:
                ret = requests.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data=data)
                # print(ret.text)
                return ret.json().get('access_token')
            except:
                pass 
        return None

    def login(self):
        self.access_token=self.get_accesstoken(self.passwd)
        if not self.access_token:
            return False
        
        # print(self.access_token,self.generate_auth_string(self.email, self.access_token))
        try:
            self.mail = imaplib.IMAP4_SSL('outlook.live.com')
            self.mail.authenticate('XOAUTH2', lambda x: self.generate_auth_string(self.email, self.access_token))
            return True
        except:
            import traceback
            # traceback.print_exc()
            # logger.error(f'登录邮箱[{self.email}]失败:\n{traceback.format_exc()}')
            return False
    
    def tuple_to_str(self,tuple_):
        """
        元组转为字符串输出
        :param tuple_: 转换前的元组，QQ邮箱格式为(b'\xcd\xf5\xd4\xc6', 'gbk')或者(b' <XXXX@163.com>', None)，163邮箱格式为('<XXXX@163.com>', None)
        :return: 转换后的字符串
        """
        if tuple_[1]:
            out_str = tuple_[0].decode(tuple_[1])
        else:
            if isinstance(tuple_[0], bytes):
                out_str = tuple_[0].decode('gbk')
            else:
                out_str = tuple_[0]
        return out_str

    def fetch_email_body(self, item):
        try:
            ret, data = self.mail.fetch(item, '(RFC822)')
            msg = email.message_from_string(data[0][1].decode('utf-8'))
            sub = msg.get('subject')
            sub_text = email.header.decode_header(str(sub))
            #发件人
            From = msg.get('From')
            From_text = email.header.decode_header(str(From))
            #收件人
            To = msg.get('To')
            To_text = email.header.decode_header(str(To))
            #时间
            Date = msg.get('Date')
            #'Thu, 21 Nov 2024 06:55:25 -0800' -> timestamp
            Date_text = parse(Date)
            ts=Date_text.timestamp()
            
            # 主题
            sub_detail = ''
            if sub_text[0]:
                sub_detail = self.tuple_to_str(sub_text[0])
            # print(sub_detail)
            content=""
            for part in msg.walk():
                if not part.is_multipart():
                    content_type = part.get_content_type()
                    name = part.get_filename()
                    if not name:
                        txt = str(part.get_payload(decode=True))
                        if content_type == 'text/html':
                            # mail.store(item, '-FLAGS', '\\SEEN')  设为已读
                            # print(txt)
                            content+=txt
                        if content_type == 'text/plain':
                            # mail.store(item, '-FLAGS', '\\SEEN')  设为已读
                            # print(txt)
                            content+=txt
                    else:
                        # 有附件
                        pass
            return {
                "Subject": sub_detail,
                "content": content,
                "From": self.tuple_to_str(From_text[0]),
                "To": self.tuple_to_str(To_text[0]),
                "Date": ts

            }
        except Exception as e:
            print(e)

    def get_last_email(self, index=-1, num=10):
        """
        获取最新的一封邮件
        """
        try:
            # 检测 IMAP 连接是否仍然有效，断开则重连
            try:
                self.mail.noop()
            except Exception:
                logger.info(f"IMAP连接已断开，尝试重新登录: {self.email}")
                if not self.login():
                    logger.error(f"IMAP重新登录失败: {self.email}")
                    return []

            msgs=[]
            #收件箱
            self.mail.select('INBOX')
            # 检查邮件:
            #获取最近10天的邮件
            today_date = datetime.now().date()
            yesterday_date = today_date - timedelta(days=10)
            resp, items = self.mail.search(None, f'SINCE {yesterday_date.strftime("%d-%b-%Y")}')
            items = items[0].split()
            for emailid in items[::-1][:num]:
                msgs.append(self.fetch_email_body(emailid))
            #垃圾箱
            self.mail.select('Junk')
            # 检查邮件:
            resp, items = self.mail.search(None, f'SINCE {yesterday_date.strftime("%d-%b-%Y")}')
            items = items[0].split()
            for emailid in items[::-1][:num]:
                msgs.append(self.fetch_email_body(emailid))
            return msgs
        except:
            import traceback
            logger.error(f'收邮件错误:\n{traceback.format_exc()}')
            return []
    

class OutlookGraphClient:
    """
    A client for fetching Outlook emails via Microsoft Graph API.
    Initialize with a credential string of the form:
    "email----password----client_id----refresh_token"
    or set it in the environment variable OUTLOOK_CRED.
    """

    ec=None

    TOKEN_URL = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    client_id='9e5f94bc-e8a4-4e73-b8be-63364c29d753'

    def __init__(self,email,passwd,client_id=None):
        self.email=email
        self.passwd=passwd
        self.server='outlook.live.com'

        self.client_id=client_id if client_id else self.client_id

        # Clean up the refresh token
        self.refresh_token = self.passwd.replace('$$', '').replace('$', '')
    
    def login(self):
        # Obtain initial access token
        self.access_token = self._get_access_token()
        if not self.access_token:
            return False 
        
        # if 'Mail.Read' in self.scope:
        access_token=self.access_token
        self.ec=OauthEmailReceiver(self.email,self.refresh_token,self.client_id)
        self.ec.client_id=self.client_id
        self.ec.access_token=access_token
        if not self.ec.login():
            self.ec=None
            # return False
        return True
        


    def _get_access_token(self) -> str:
        """
        Exchange the refresh token for a new access token.
        Retries up to 3 times on failure.
        """
        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        resp=None
        for _ in range(1):
            try:
                resp = requests.post(self.TOKEN_URL, data=data)
                # print(resp.text)
                
                resp.raise_for_status()
                res=resp.json()
                self.scope=res['scope']
                
                return resp.json().get('access_token')
            except Exception:
                if resp is not None:
                    logger.error(f'【{self.email}】 获取邮箱access_token失败:{resp.text}')
                time.sleep(1)
                continue
        return False

    def fetch_message_body(self, message_id: str, as_text: bool = True) -> dict:
        """
        Fetch the full content of a single message by ID.
        Returns a dict with keys: Subject, content, From, To, Date.
        """
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
        Prefer='text' if as_text else 'html'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Prefer':Prefer,
            'Accept': 'application/json'
        }
        params = {'$select': 'subject,from,receivedDateTime,body'}
        
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        received_ts = parse(data['receivedDateTime']).timestamp()
        return {
            'Subject': data.get('subject'),
            'content': data.get('body', {}).get('content'),
            'From': data.get('from', {}).get('emailAddress', {}).get('address'),
            'To': self.email,
            'Date': received_ts
        }

    def get_last_email(self, index=-1,num=10) -> list:
        """
        Fetch the latest `top` messages and return those received within `within_days` days.
        Each message is returned as the same dict format as fetch_message_body.
        """
        if self.ec:
            return self.ec.get_last_email(num=num)
        endpoint = "https://graph.microsoft.com/v1.0/me/messages"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        params = {'$top': num, '$select': 'id,receivedDateTime'}
        try:
            resp = requests.get(endpoint, headers=headers, params=params)
            resp.raise_for_status()
            messages = resp.json().get('value', [])
        except:
            if self.ec:
                return self.ec.get_last_email(num=num)
            else:
                return []

        recent_msgs = []
        now = time.time()
        cutoff = 20 * 24 * 3600
        cnt=0
        for msg in messages:
            recv_ts = parse(msg['receivedDateTime']).timestamp()
            if now - recv_ts <= cutoff:
                cnt+=1
                # Refresh token if expired, assume expired if 401
                try:
                    body = self.fetch_message_body(msg['id'], as_text=True)
                except requests.HTTPError as e:
                    if e.response.status_code == 401:
                        self.access_token = self._get_access_token()
                        body = self.fetch_message_body(msg['id'], as_text=True)
                    else:
                        raise
                recent_msgs.append(body)
                if cnt>=num:
                    break

        return recent_msgs



if __name__ == '__main__':
    emails = 'ninyvobkqv44@outlook.com----pkgmlgtbv577----9e5f94bc-e8a4-4e73-b8be-63364c29d753----M.C557_SN1.0.U.-ClEDTHzX5ioGUCXC0KfG3ftik4Cnz4uneUP7NUZdH1NbJPJ*K0dVW3wHAJhf!2W4R2qcUwOP33jFwcgglgm9dhQtS7TCmgVMBLndxfug0aq147jYiMYb5tnq1X1j5jqIa0Xisu*jvFyKJEIHlPh8v4sESWuhwEz75d7mXCkbwzQ8ZM7Lvnz7AA72ePrTyGOs*we02kX71FeEiZi6bIhHd1xroFyXJoRIj27NpwXj9WXcRUJNBDMOvcTD79tRNYsa4lCpT3z3rb6ajn5HDPWM1elL0mUiRCRUJFODbevFYlZH3*zUefTdzt6Pr3nxHsPO4KTjg6nWApI5Brpr0Uoi6w917u4yASV3J4Lam3mnSQQ7xzsiZ5OiCRARVrHMtV5IMPqeYSpFne7P4W7OCs31pnsqPcWppSNUe5fRJcumLawy'
    for e in emails.split('\n'):
        emailss = e.split('----')[0]
        passwd = e.split('----')[1]
        client_id = e.split('----')[2] if len(e.split('----')) > 2 else ''
        refresh_token = e.split('----')[3] if len(e.split('----')) > 3 else ''
        pop3_ec=OutlookGraphClient(email=emailss,passwd=refresh_token if refresh_token else passwd,client_id=client_id if client_id else None)
        # pop3_ec.email_receiver.client_id='dbc8e03a-b00c-46bd-ae65-b683e7707cb0'
        # pop3_ec.email_receiver2.client_id='9e5f94bc-e8a4-4e73-b8be-63364c29d753'
        login_status=pop3_ec.login()
        print(emailss,login_status)

        email=pop3_ec.get_last_email(num=10)
        if email:
            for emai in email:
                time_local = time.localtime(emai['Date'])
                #转字符串
                time_local = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                print(emailss,emai['From'],time_local,emai['Subject'])
