#!/bin/bash

echo "🚀 启动BOSS直聘风格职位推荐系统"

# 检查是否安装了依赖
if [ ! -d "backend/venv" ]; then
    echo "📦 安装后端依赖..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 启动后端服务
echo "🔧 启动后端服务 (端口: 8000)..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 启动前端服务
echo "🎨 启动前端服务 (端口: 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ 服务启动完成！"
echo "📍 前端地址: http://localhost:3000"
echo "📍 后端API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
