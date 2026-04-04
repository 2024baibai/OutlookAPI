import re
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from flask import request, Response, current_app
from models import OutlookEmail, EmailRecord
from extensions import db
from tools.imap_email import OutlookGraphClient
from tools.refresh_outlook import do_refresh_token
from loguru import logger
import time 

def check_auth(username, password):
    """检查Basic Auth凭据"""
    return (username == current_app.config['BASIC_AUTH_USERNAME'] and 
            password == current_app.config['BASIC_AUTH_PASSWORD'])

def authenticate():
    """发送401响应"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    """Basic Auth装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def parse_email_file(file_content):
    """解析上传的邮箱文件"""
    emails = []
    try:
        # 尝试CSV格式
        if file_content.startswith('email,') or ',' in file_content:
            reader = csv.DictReader(io.StringIO(file_content))
            for row in reader:
                if 'email' in row and 'password' in row:
                    emails.append({
                        'email': row.get('email', '').strip(),
                        'password': row.get('password', '').strip(),
                        'client_id': row.get('client_id', '9e5f94bc-e8a4-4e73-b8be-63364c29d753').strip(),
                        'refresh_token': row.get('refresh_token', '').strip()
                    })
        else:
            # 按行分割格式: email----password----client_id----refresh_token
            lines = file_content.strip().split('\n')
            for line in lines:
                if '----' in line:
                    parts = line.split('----')
                    if len(parts) >= 2:
                        emails.append({
                            'email': parts[0].strip(),
                            'password': parts[1].strip(),
                            'client_id': parts[2].strip() if len(parts) > 2 else '9e5f94bc-e8a4-4e73-b8be-63364c29d753',
                            'refresh_token': parts[3].strip() if len(parts) > 3 else ''
                        })
    except Exception as e:
        logger.error(f"解析邮箱文件失败: {e}")
    
    return emails

def refresh_email_token(email_obj):
    """刷新单个邮箱的令牌"""
    try:
        refresh_token = email_obj.refresh_token or email_obj.email_password
        result = do_refresh_token(email_obj.client_id, refresh_token)
        
        if result and result.get('refresh_token'):
            email_obj.refresh_token = result['refresh_token']
            email_obj.access_token = result.get('access_token')
            # 设置为30天后需要重新刷新（refresh_token 有效期约90天，提前刷新保留余量）
            email_obj.expire_time = datetime.utcnow() + timedelta(days=30)
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"刷新邮箱{email_obj.email}令牌失败: {e}")
        return False

def extract_verification_code(msg):
    """从邮件中提取验证码"""
    content = msg.get('content', '')
    subject = msg.get('Subject', '')
    
    # 提取规则
    code1 = re.findall(r'>(\d{6})<', content)
    code2 = re.findall(r'(\d{6})', subject)
    code3 = re.findall(r'\n(\d{6})\r', content)
    
    code = code1 if code1 else code2 if code2 else code3 if code3 else None
    return code[0] if code else None

def process_email_messages(email, messages):
    """处理邮件消息，筛选TikTok邮件并提取验证码"""
    results = []
    now = datetime.utcnow()
    one_minute_ago = time.time() - 60*3
    new_records = []

    for msg in messages:
        sender = msg.get('From', '')
        received_time = msg.get('Date', 0)
        # print(f"Processing email from {sender} received at {received_time};Subject: {msg.get('Subject', '')} ; {received_time-one_minute_ago}")
        # 只处理@tiktok.com的邮件
        if 'tiktok.com' in sender and received_time >= one_minute_ago:
            code = extract_verification_code(msg)
            if code:
                # 将时间戳转换为datetime对象
                received_datetime = datetime.fromtimestamp(received_time) if isinstance(received_time, (int, float)) else now

                # 先检查是否已存在相同的邮件记录
                existing_record = EmailRecord.query.filter_by(
                    email=email,
                    subject=msg.get('Subject', ''),
                    sender=sender,
                    received_time=received_datetime
                ).first()

                if not existing_record:
                    email_record = EmailRecord(
                        email=email,
                        subject=msg.get('Subject', ''),
                        content=msg.get('content', ''),
                        sender=sender,
                        received_time=received_datetime
                    )
                    new_records.append(email_record)
                    logger.info(f"保存新邮件记录: {email} - {msg.get('Subject', '')}")
                else:
                    logger.debug(f"邮件记录已存在，跳过保存: {email} - {msg.get('Subject', '')}")

                results.append({
                    'code': code,
                    'sender': sender,
                    'subject': msg.get('Subject', ''),
                    'received_time': received_datetime.isoformat()
                })

    # 批量提交新邮件记录
    if new_records:
        try:
            db.session.add_all(new_records)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"批量保存邮件记录失败: {e}")

    # 返回最新的验证码
    if results:
        return sorted(results, key=lambda x: x['received_time'], reverse=True)[0]
    return None
