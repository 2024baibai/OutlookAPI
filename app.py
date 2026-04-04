from flask import Flask, redirect, url_for, render_template
from config import Config
from extensions import db, scheduler
from models import OutlookEmail, EmailRecord
from blueprints import admin_bp, api_bp
from tasks import refresh_expired_tokens, cleanup_old_email_records
import os

def create_app():
    """应用工厂函数"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    scheduler.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 每次请求结束后确保 Session 释放连接回池
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    # 配置定时任务
    @scheduler.task('interval', id='refresh_tokens', hours=app.config['REFRESH_INTERVAL_HOURS'])
    def scheduled_refresh_tokens():
        with app.app_context():
            refresh_expired_tokens()
    
    @scheduler.task('interval', id='cleanup_records', hours=24)
    def scheduled_cleanup():
        with app.app_context():
            cleanup_old_email_records()
    
    # 启动调度器
    if not scheduler.running:
        scheduler.start()
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('login.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # 开发环境下运行
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    print(f"""
    ===================================
    微软邮箱批量管理系统启动成功！
    ===================================
    管理页面: http://localhost:{port}/admin
    API接口: http://localhost:{port}/api?email=xxx
    
    默认登录信息:
    用户名: {app.config['BASIC_AUTH_USERNAME']}
    密码: {app.config['BASIC_AUTH_PASSWORD']}
    
    定时任务: 每{app.config['REFRESH_INTERVAL_HOURS']}小时刷新过期令牌
    ===================================
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)