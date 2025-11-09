from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from models import OutlookEmail, EmailRecord
from extensions import db
from utils import requires_auth, parse_email_file, refresh_email_token
import asyncio
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates')

def is_token_expired(email_obj):
    """检查邮箱令牌是否过期"""
    if not email_obj.expire_time:
        # 如果没有过期时间，认为已过期
        return True
    
    # 提前5分钟认为过期，避免使用即将过期的令牌
    buffer_time = timedelta(minutes=5)
    return datetime.utcnow() + buffer_time >= email_obj.expire_time

def refresh_single_email_token(app, email_id):
    """刷新单个邮箱令牌的线程函数"""
    try:
        with app.app_context():
            # 在新线程中需要重新查询数据库对象
            email = OutlookEmail.query.get(email_id)
            if not email:
                return {'email_id': email_id, 'success': False, 'error': '邮箱不存在'}
            
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                success = loop.run_until_complete(refresh_email_token(email))
                return {
                    'email_id': email_id,
                    'email': email.email,
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

@admin_bp.route('/')
@requires_auth
def index():
    """管理首页"""
    emails = OutlookEmail.query.order_by(OutlookEmail.created_at.desc()).all()
    email_records = EmailRecord.query.order_by(EmailRecord.received_time.desc()).limit(50).all()
    
    # 为每个邮箱添加过期状态信息
    email_status_list = []
    for email in emails:
        status = 'unknown'
        if email.expire_time:
            now = datetime.utcnow()
            buffer_time = timedelta(minutes=5)
            if email.expire_time > now + buffer_time:
                status = 'valid'
            elif email.expire_time > now:
                status = 'expiring_soon'  # 5分钟内过期
            else:
                status = 'expired'
        else:
            status = 'unknown'
        
        email_status_list.append({
            'email': email,
            'status': status
        })
    
    return render_template('admin/index.html', 
                          email_status_list=email_status_list,
                          emails=emails,  # 保持兼容性
                          email_records=email_records)

@admin_bp.route('/upload', methods=['POST'])
@requires_auth
def upload_emails():
    """批量上传邮箱"""
    if 'file' not in request.files:
        flash('没有选择文件', 'danger')
        return redirect(url_for('admin.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件', 'danger')
        return redirect(url_for('admin.index'))
    
    try:
        file_content = file.read().decode('utf-8')
        emails = parse_email_file(file_content)
        
        if not emails:
            flash('文件格式错误或没有有效的邮箱数据', 'danger')
            return redirect(url_for('admin.index'))
        
        added_count = 0
        for email_data in emails:
            existing_email = OutlookEmail.query.filter_by(email=email_data['email']).first()
            if not existing_email:
                new_email = OutlookEmail(
                    email=email_data['email'],
                    email_password=email_data['password'],
                    client_id=email_data['client_id'],
                    refresh_token=email_data.get('refresh_token', email_data['password'])
                )
                db.session.add(new_email)
                added_count += 1
        
        db.session.commit()
        flash(f'成功添加 {added_count} 个邮箱', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'上传失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/delete/<int:email_id>', methods=['POST'])
@requires_auth
def delete_email(email_id):
    """删除单个邮箱"""
    email = OutlookEmail.query.get_or_404(email_id)
    try:
        db.session.delete(email)
        db.session.commit()
        flash(f'成功删除邮箱 {email.email}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/refresh/<int:email_id>', methods=['POST'])
@requires_auth
def refresh_token(email_id):
    """刷新单个邮箱令牌"""
    email = OutlookEmail.query.get_or_404(email_id)
    
    # 检查是否需要刷新
    if not is_token_expired(email):
        flash(f'邮箱 {email.email} 的令牌尚未过期，无需刷新', 'info')
        return redirect(url_for('admin.index'))
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(refresh_email_token(email))
        loop.close()
        
        if success:
            flash(f'成功刷新邮箱 {email.email} 的令牌', 'success')
        else:
            flash(f'刷新邮箱 {email.email} 的令牌失败', 'danger')
    except Exception as e:
        flash(f'刷新失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/batch_refresh', methods=['POST'])
@requires_auth
def batch_refresh():
    """批量刷新过期的邮箱令牌（多线程）"""
    emails = OutlookEmail.query.all()
    
    # 筛选出需要刷新的邮箱（过期的）
    expired_emails = []
    for email in emails:
        if is_token_expired(email):
            expired_emails.append(email)
    
    if not expired_emails:
        flash('没有需要刷新的邮箱（所有令牌都未过期）', 'info')
        return redirect(url_for('admin.index'))
    
    logger.info(f"开始批量刷新 {len(expired_emails)} 个过期邮箱的令牌")
    
    # 获取当前Flask应用实例
    app = current_app._get_current_object()
    
    # 使用多线程刷新
    success_count = 0
    failed_count = 0
    results = []
    
    try:
        # 使用线程池，最大5个并发线程
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有刷新任务
            future_to_email = {
                executor.submit(refresh_single_email_token, app, email.id): email 
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
                    logger.error(f"刷新邮箱失败: {result.get('email', result['email_id'])}, 错误: {result['error']}")
        
        # 显示结果
        if success_count > 0:
            flash(f'批量刷新完成：成功 {success_count} 个，失败 {failed_count} 个，总共处理 {len(expired_emails)} 个过期邮箱', 'success')
        else:
            flash(f'批量刷新失败：{failed_count} 个邮箱刷新失败', 'danger')
            
        logger.info(f"批量刷新完成：成功 {success_count}，失败 {failed_count}")
        
    except Exception as e:
        logger.error(f"批量刷新过程中发生错误: {e}")
        flash(f'批量刷新过程中发生错误：{str(e)}', 'danger')
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/clear_all', methods=['POST'])
@requires_auth
def clear_all():
    """清空所有邮箱"""
    try:
        EmailRecord.query.delete()
        OutlookEmail.query.delete()
        db.session.commit()
        flash('已清空所有邮箱和邮件记录', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'清空失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin.index'))
