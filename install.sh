#!/bin/bash
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/home/OutlookAPI"
PIP="/www/server/panel/pyenv/bin/pip"
PYTHON="/www/server/panel/pyenv/bin/python"
GUNICORN="/www/server/panel/pyenv/bin/gunicorn"
SUPERVISOR_CONF="/etc/supervisor/conf.d/outlookapi.conf"
REPO_URL="https://github.com/2024baibai/OutlookAPI.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  OutlookAPI 一键部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# ---- 1. 克隆/更新代码 ----
echo -e "\n${YELLOW}[1/4] 拉取代码...${NC}"
if [ -d "$APP_DIR" ]; then
    echo "目录已存在，拉取最新代码..."
    cd "$APP_DIR"
    git pull
else
    cd /home
    git clone "$REPO_URL"
    cd "$APP_DIR"
fi

# ---- 2. 安装 Python 依赖 ----
echo -e "\n${YELLOW}[2/4] 安装 Python 依赖...${NC}"
$PIP install -r requirements.txt
$PIP install gunicorn

# ---- 3. 安装 supervisor ----
echo -e "\n${YELLOW}[3/4] 安装 supervisor...${NC}"
if command -v supervisord &> /dev/null; then
    echo "supervisor 已安装，跳过"
else
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y supervisor
    elif command -v yum &> /dev/null; then
        yum install -y epel-release && yum install -y supervisor
    else
        echo -e "${RED}无法识别包管理器，请手动安装 supervisor${NC}"
        exit 1
    fi
fi

# 确保 supervisor 开机自启并启动
systemctl enable supervisord 2>/dev/null || systemctl enable supervisor 2>/dev/null || true
systemctl start supervisord 2>/dev/null || systemctl start supervisor 2>/dev/null || true

# ---- 4. 配置 supervisor ----
echo -e "\n${YELLOW}[4/4] 配置 supervisor 守护进程...${NC}"

# 创建日志目录
mkdir -p /var/log/outlookapi

cat > "$SUPERVISOR_CONF" << EOF
[program:outlookapi]
command=${GUNICORN} -w 2 -b 0.0.0.0:5000 --timeout 120 "app:create_app()"
directory=${APP_DIR}
user=root
autostart=true
autorestart=true
startsecs=5
startretries=3
stopwaitsecs=10
redirect_stderr=true
stdout_logfile=/var/log/outlookapi/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=FLASK_DEBUG="false"
EOF

# 重新加载并启动
supervisorctl reread
supervisorctl update
supervisorctl restart outlookapi 2>/dev/null || supervisorctl start outlookapi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "应用目录: ${APP_DIR}"
echo -e "访问地址: http://<服务器IP>:5000/admin"
echo -e "查看状态: supervisorctl status outlookapi"
echo -e "查看日志: tail -f /var/log/outlookapi/app.log"
echo -e "重启应用: supervisorctl restart outlookapi"
echo -e "${GREEN}========================================${NC}"
