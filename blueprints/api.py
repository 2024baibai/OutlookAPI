from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
from sqlalchemy import func
from models import OutlookEmail
from extensions import db
from tools.imap_email import OutlookGraphClient
from utils import process_email_messages
from loguru import logger
import time
import threading

api_bp = Blueprint('api', __name__, url_prefix='/api', template_folder='../templates')

# 客户端缓存字典 {email: {'client': client_instance, 'expire_time': timestamp}}
client_cache = {}
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 100

def _close_client(client):
    """安全关闭客户端的IMAP连接"""
    try:
        if client and client.ec and hasattr(client.ec, 'mail'):
            client.ec.mail.logout()
    except Exception:
        pass

def get_cached_client(email, email_obj):
    """获取缓存的客户端或创建新的客户端"""
    current_time = time.time()
    cache_duration = 10 * 60  # 10分钟
    
    with _cache_lock:
        # 检查缓存是否存在且未过期
        if email in client_cache:
            cached_data = client_cache[email]
            if current_time < cached_data['expire_time']:
                logger.info(f"使用缓存的客户端: {email}")
                return cached_data['client']
            else:
                # 缓存过期，关闭连接并删除
                logger.info(f"客户端缓存已过期，删除: {email}")
                _close_client(cached_data['client'])
                del client_cache[email]
    
    # 创建新的客户端（在锁外执行网络IO）
    logger.info(f"创建新的客户端: {email}")
    refresh_token = email_obj.refresh_token or email_obj.email_password
    client = OutlookGraphClient(
        email=email_obj.email,
        passwd=refresh_token,
        client_id=email_obj.client_id
    )
    
    # 如果DB中有未过期的access_token（created_at当作过期时间），直接复用
    now = datetime.utcnow()
    if email_obj.access_token and email_obj.created_at and email_obj.created_at > now:
        logger.info(f"复用DB中的access_token: {email}")
        client.access_token = email_obj.access_token
    
    # 尝试登录（有access_token时跳过HTTP获取token，只做IMAP连接）
    login_result = client.login()
    if not login_result:
        # access_token可能过期，清除后重试完整登录
        if client.access_token:
            logger.info(f"复用access_token登录失败，尝试完整登录: {email}")
            client.access_token = None
            login_result = client.login()
        if not login_result:
            return None
    
    # 登录成功后，同步更新DB中的token信息
    try:
        email_obj.access_token = client.access_token
        email_obj.created_at = now + timedelta(minutes=55)
        email_obj.refresh_token = client.refresh_token
        email_obj.expire_time = now + timedelta(days=30)
        db.session.commit()
        logger.info(f"已同步更新token到DB: {email}")
    except Exception as e:
        db.session.rollback()
        logger.warning(f"同步token到DB失败: {email}, {e}")
    
    with _cache_lock:
        # 缓存满时清理最旧的
        if len(client_cache) >= _MAX_CACHE_SIZE:
            oldest_email = min(client_cache, key=lambda k: client_cache[k]['expire_time'])
            _close_client(client_cache[oldest_email]['client'])
            del client_cache[oldest_email]
            logger.info(f"缓存已满，清理最旧: {oldest_email}")
        
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
    
    with _cache_lock:
        for email, cached_data in client_cache.items():
            if current_time >= cached_data['expire_time']:
                expired_emails.append(email)
        
        for email in expired_emails:
            _close_client(client_cache[email]['client'])
            del client_cache[email]
            logger.info(f"清理过期缓存: {email}")

@api_bp.route('/', methods=['GET'])
def get_verification_code():
    """获取验证码API接口"""
    try:
        # 清理过期缓存
        clear_expired_cache()
        
        email = request.args.get('email')
        html_mode = request.args.get('html') == '1'  # 检测 HTML 模式
        
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
            
        # ========== HTML 模式：返回原始邮件内容 ==========
        if html_mode:
            messages = client.get_last_email(num=30, as_html=True)
            
            # 按时间倒序排序（最新的在最前面）
            messages = sorted(messages, key=lambda x: x.get('Date', 0), reverse=True) if messages else []
            
            # 格式化邮件数据供模板使用
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    'from_addr': msg.get('From', 'Unknown'),
                    'subject': msg.get('Subject', '(无主题)'),
                    'date_str': datetime.fromtimestamp(msg.get('Date', 0)).strftime('%Y-%m-%d %H:%M:%S') if msg.get('Date') else 'Unknown',
                    'content': msg.get('content', '')
                })
            
            return render_template('api/email_list.html', email=email, messages=formatted_messages)
        
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
        db.session.rollback()
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
