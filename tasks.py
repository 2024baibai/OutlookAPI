import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import OutlookEmail
from extensions import db
from utils import refresh_email_token
from loguru import logger

def refresh_single_email_async(email_id):
    """异步刷新单个邮箱令牌的函数"""
    try:
        # 在新线程中需要重新查询数据库对象
        email_obj = OutlookEmail.query.get(email_id)
        if not email_obj:
            return {'email_id': email_id, 'success': False, 'error': '邮箱不存在'}
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(refresh_email_token(email_obj))
            return {
                'email_id': email_id,
                'email': email_obj.email,
                'success': success,
                'error': None if success else '刷新失败'
            }
        finally:
            loop.close()
            
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
        # 查询过期的邮箱
        expired_emails = OutlookEmail.query.filter(
            OutlookEmail.expire_time <= datetime.utcnow()
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
        with ThreadPoolExecutor(max_workers=15) as executor:
            # 提交所有刷新任务
            future_to_email = {
                executor.submit(refresh_single_email_async, email.id): email 
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
        db.session.rollback()
