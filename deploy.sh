#!/bin/bash

# 确保脚本抛出遇到的错误
set -e

# 更新软件包列表
echo "正在更新软件包列表..."
sudo apt-get update

# 安装 Python3, pip, MySQL Server
echo "正在安装 Python3, pip 和 MySQL..."
sudo apt-get install -y python3 python3-pip python3-venv mysql-server libmysqlclient-dev pkg-config

# 启动 MySQL 服务
echo "正在启动 MySQL 服务..."
sudo systemctl start mysql
sudo systemctl enable mysql

# 配置 MySQL 数据库
# 注意：生产环境中建议手动配置更安全的密码
DB_NAME="android_api"
DB_USER="root"
DB_PASS="123456"

echo "正在创建数据库 ${DB_NAME}..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "ALTER USER '${DB_USER}'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_PASS}';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 创建虚拟环境
echo "正在创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "正在安装 Python 依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 运行应用
echo "部署完成！正在启动应用..."
echo "应用将运行在 http://0.0.0.0:5000"
python3 app.py
