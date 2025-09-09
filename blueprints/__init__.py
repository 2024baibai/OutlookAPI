"""
Flask蓝图模块初始化

这个包包含了应用的所有蓝图：
- admin: 管理面板蓝图
- api: API接口蓝图
"""

from .admin import admin_bp
from .api import api_bp

__all__ = ['admin_bp', 'api_bp']