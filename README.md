# 微软邮箱批量管理系统

基于Flask蓝图模式构建的微软邮箱批量管理网站，支持邮箱批量管理、定时令牌刷新和验证码提取API。

## 项目结构

```
OutlookAPI/
├── app.py                      # 应用主文件
├── config.py                   # 配置文件
├── extensions.py               # Flask扩展初始化
├── models.py                   # 数据库模型
├── tasks.py                    # 定时任务
├── utils.py                    # 工具函数
├── example_emails.txt          # 示例邮箱文件
├── blueprints/                 # 蓝图模块
│   ├── __init__.py
│   ├── admin.py               # 管理面板蓝图
│   └── api.py                 # API接口蓝图
├── templates/                  # 模板文件
│   ├── base.html              # 基础模板
│   ├── login.html             # 登录页面
│   ├── admin/
│   │   └── index.html         # 管理面板模板
│   └── api/
│       └── docs.html          # API文档模板
├── static/                     # 静态文件
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── main.js            # JavaScript文件
└── tools/                      # 工具模块
    ├── database.py            # 数据库工具
    ├── imap_email.py          # 邮箱操作
    └── refresh_outlook.py     # 令牌刷新
```

## 功能特性

### 1. 基于Flask蓝图模式
- **admin蓝图**: 管理面板，支持Basic Auth认证
- **api蓝图**: API接口，无需认证

### 2. 邮箱批量管理
- 批量添加邮箱（支持CSV和TXT格式）
- 批量删除邮箱操作
- 邮箱信息查看和管理
- 令牌状态监控

### 3. 定时任务系统
- 使用Flask-APScheduler
- 每24小时自动刷新过期令牌
- 清理过期邮件记录

### 4. 验证码提取API
- 无权限API接口：`/api?email=xxxx`
- 自动登录指定邮箱
- 获取最近5封邮件
- 筛选@tiktok.com发件人邮件
- 智能提取验证码（支持多种格式）
- 只返回最近3分钟内的验证码

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
export FLASK_DEBUG=true
export PORT=5000
```

### 3. 运行应用
```bash
python app.py
```

### 4. 访问系统
- 主页: http://localhost:5000/
- 管理面板: http://localhost:5000/admin
- API文档: http://localhost:5000/api/docs
- 验证码API: http://localhost:5000/api?email=xxx

## API接口

### 获取验证码
```
GET /api?email={邮箱地址}
```

**响应示例:**
```json
{
    "success": true,
    "data": {
        "code": "123456",
        "sender": "noreply@tiktok.com",
        "subject": "Your verification code",
        "received_time": "2025-09-09 14:30:15"
    },
    "message": "成功获取验证码"
}
```

### 健康检查
```
GET /api/health
```

## 数据库模型

### OutlookEmail（邮箱信息）
- email: 邮箱地址
- email_password: 邮箱密码
- client_id: 客户端ID
- refresh_token: 刷新令牌
- access_token: 访问令牌
- expire_time: 令牌过期时间

### EmailRecord（邮件记录）
- email: 邮箱地址
- sender: 发件人
- subject: 邮件主题
- content: 邮件内容
- received_time: 接收时间

## 配置说明

### Basic Auth认证
- 默认用户名: admin
- 默认密码: password123
- 可在config.py中修改

### 邮箱文件格式
支持两种格式：

1. **CSV格式**:
```
email,password,client_id,refresh_token
user@example.com,password,client123,token123
```

2. **TXT格式**:
```
user@example.com----password----client123----token123
```

## 验证码提取规则

系统支持多种验证码格式：
1. `>(\d{6})<` - HTML标签中的6位数字
2. `(\d{6})` - 邮件主题中的6位数字
3. `\n(\d{6})\r` - 换行符间的6位数字

## 技术栈

- **后端框架**: Flask + Flask蓝图
- **数据库**: SQLAlchemy ORM
- **定时任务**: Flask-APScheduler
- **前端**: HTML5 + CSS3 + JavaScript
- **邮箱API**: Microsoft Graph API
- **日志**: Loguru

## 开发规范

### 1. 蓝图结构
- 每个蓝图独立管理路由和逻辑
- 模板文件统一放在templates目录
- 静态文件统一放在static目录

### 2. 模板继承
- 使用base.html作为基础模板
- 所有页面继承base模板
- 分模块组织模板文件

### 3. 静态文件组织
- CSS文件放在static/css/
- JavaScript文件放在static/js/
- 响应式设计，支持移动端

### 4. 错误处理
- 统一的错误处理机制
- 友好的错误提示
- 完整的日志记录

## 许可证

MIT License
