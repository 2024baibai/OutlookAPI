import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///outlook_manager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Basic Auth配置
    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME') or 'admin'
    BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD') or 'password'
    
    # APScheduler配置
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'
    
    # 定时任务配置
    REFRESH_INTERVAL_HOURS = 24