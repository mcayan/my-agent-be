@echo off
REM 后端启动脚本 (Windows)

echo 正在启动后端服务...

REM 检查虚拟环境
if not exist "venv" (
    echo 未找到虚拟环境，正在创建...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt

REM 检查 .env 文件
if not exist ".env" (
    echo 警告: 未找到 .env 文件
    echo 请创建 .env 文件并配置数据库连接
    exit /b 1
)

REM 启动服务
echo 正在启动 FastAPI 服务...
uvicorn main:app --reload --host 0.0.0.0 --port 8000

