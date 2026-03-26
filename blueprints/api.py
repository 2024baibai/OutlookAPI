from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
from sqlalchemy import func
from models import OutlookEmail
from tools.imap_email import OutlookGraphClient
from utils import process_email_messages
from loguru import logger
import time

api_bp = Blueprint('api', __name__, url_prefix='/api', template_folder='../templates')

# 客户端缓存字典 {email: {'client': client_instance, 'expire_time': timestamp}}
client_cache = {}

def get_cached_client(email, email_obj):
    """获取缓存的客户端或创建新的客户端"""
    current_time = time.time()
    cache_duration = 10 * 60  # 10分钟
    
    # 检查缓存是否存在且未过期
    if email in client_cache:
        cached_data = client_cache[email]
        if current_time < cached_data['expire_time']:
            logger.info(f"使用缓存的客户端: {email}")
            return cached_data['client']
        else:
            # 缓存过期，删除
            logger.info(f"客户端缓存已过期，删除: {email}")
            del client_cache[email]
    
    # 创建新的客户端
    logger.info(f"创建新的客户端: {email}")
    refresh_token = email_obj.refresh_token or email_obj.email_password
    client = OutlookGraphClient(
        email=email_obj.email,
        passwd=refresh_token,
        client_id=email_obj.client_id
    )
    
    # 尝试登录
    login_result = client.login()
    if not login_result:
        return None
    
    # 存储到缓存
    client_cache[email] = {
        'client': client,
        'expire_time': current_time + cache_duration
    }
    
    return client

def clear_expired_cache():
    """清理过期的缓存"""
    current_time = time.time()
    expired_emails = []
    
    for email, cached_data in client_cache.items():
        if current_time >= cached_data['expire_time']:
            expired_emails.append(email)
    
    for email in expired_emails:
        del client_cache[email]
        logger.info(f"清理过期缓存: {email}")

@api_bp.route('/', methods=['GET'])
def get_verification_code():
    """获取验证码API接口"""
    try:
        # 清理过期缓存
        clear_expired_cache()
        
        email = request.args.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': '邮箱参数不能为空'
            }), 400
        
        # 查询邮箱是否存在
        email_obj = OutlookEmail.query.filter(func.lower(OutlookEmail.email) == email.lower()).first()
        if not email_obj:
            return jsonify({
                'success': False,
                'message': f'邮箱 {email} 不存在于系统中'
            }), 404
        
        # 获取缓存的客户端或创建新的客户端
        client = get_cached_client(email, email_obj)
        if not client:
            return jsonify({
                'success': False,
                'message': f'邮箱 {email} 登录失败，请检查令牌是否有效'
            }), 401
        
        # 获取最近5封邮件
        messages = client.get_last_email(num=5)
        if not messages:
            return jsonify({
                'success': False,
                'message': '获取邮件失败或没有新邮件'
            })
        
        # 处理邮件，筛选TikTok邮件并提取验证码
        result = process_email_messages(email, messages)
        
        if result:
            return jsonify({
                'success': True,
                'data': {
                    'code': result['code'],
                    'sender': result['sender'],
                    'subject': result['subject'],
                    'received_time': result['received_time']
                },
                'message': '成功获取验证码'
            })
        else:
            return jsonify({
                'success': False,
                'message': '未找到最近1分钟内来自@tiktok.com的验证码邮件'
            })
    
    except Exception as e:
        logger.error(f"API获取验证码失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取验证码失败: {str(e)}'
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': 'API服务正常运行',
        'timestamp': datetime.utcnow().isoformat()
    })


@api_bp.route('/docs', methods=['GET'])
def api_docs():
    """API文档页面"""
    return render_template('api/docs.html')
