#!/bin/bash

# 后端启动脚本

echo "正在启动后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "未找到虚拟环境，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "警告: 未找到 .env 文件"
    echo "请创建 .env 文件并配置数据库连接"
    exit 1
fi

# 启动服务
echo "正在启动 FastAPI 服务..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000

