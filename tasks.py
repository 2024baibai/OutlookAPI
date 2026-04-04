from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import current_app
from sqlalchemy import or_
from models import OutlookEmail
from extensions import db
from utils import refresh_email_token
from loguru import logger

def refresh_single_email_sync(app, email_id):
    """刷新单个邮箱令牌的函数"""
    try:
        with app.app_context():
            email_obj = OutlookEmail.query.get(email_id)
            if not email_obj:
                return {'email_id': email_id, 'success': False, 'error': '邮箱不存在'}
            
            try:
                success = refresh_email_token(email_obj)
                return {
                    'email_id': email_id,
                    'email': email_obj.email,
                    'success': success,
                    'error': None if success else '刷新失败'
                }
            finally:
                db.session.remove()
            
    except Exception as e:
        logger.error(f"刷新邮箱令牌失败 {email_id}: {e}")
        return {
            'email_id': email_id,
            'success': False,
            'error': str(e)
        }

def refresh_expired_tokens():
    """定时任务：刷新过期的邮箱令牌（并发处理）"""
    logger.info("开始执行定时任务：刷新过期令牌")
    
    try:
        # 获取当前Flask应用实例
        app = current_app._get_current_object()
        
        with app.app_context():
            # 查询过期的邮箱（包括 expire_time 为 NULL 的新导入邮箱）
            expired_emails = OutlookEmail.query.filter(
                or_(
                    OutlookEmail.expire_time == None,
                    OutlookEmail.expire_time <= datetime.utcnow()
                )
            ).all()
            
            if not expired_emails:
                logger.info("没有需要刷新的过期令牌")
                return
            
            logger.info(f"找到 {len(expired_emails)} 个过期邮箱，开始并发刷新（最大并发数：15）")
            
            # 使用线程池并发刷新
            success_count = 0
            failed_count = 0
            results = []
            
            # 使用线程池，最大15个并发线程
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 提交所有刷新任务
                future_to_email = {
                    executor.submit(refresh_single_email_sync, app, email.id): email 
                    for email in expired_emails
                }
                
                # 收集结果
                for future in as_completed(future_to_email):
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        success_count += 1
                        logger.info(f"成功刷新邮箱: {result.get('email', result['email_id'])}")
                    else:
                        failed_count += 1
                        logger.warning(f"刷新邮箱失败: {result.get('email', result['email_id'])}, 错误: {result['error']}")
            
            logger.info(f"定时任务完成：成功刷新 {success_count} 个，失败 {failed_count} 个，总共处理 {len(expired_emails)} 个过期邮箱")
        
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")

def cleanup_old_email_records():
    """清理30天前的邮件记录"""
    try:
        app = current_app._get_current_object()
        
        with app.app_context():
            from models import EmailRecord
            
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            old_records = EmailRecord.query.filter(
                EmailRecord.received_time <= thirty_days_ago
            )
            
            count = old_records.count()
            if count > 0:
                old_records.delete()
                db.session.commit()
                logger.info(f"清理了 {count} 条30天前的邮件记录")
        
    except Exception as e:
        logger.error(f"清理邮件记录失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
