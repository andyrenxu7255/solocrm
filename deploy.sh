#!/bin/bash
set -e

# SoloCRM 一键部署脚本
# 用法：bash deploy.sh

echo "🚀 SoloCRM 一键部署脚本"
echo "========================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose 未安装，请先安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

# 获取项目路径
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/agents-workspaces}"
PROJECT_DIR="$WORKSPACE/solocrm"
REPO_URL="${REPO_URL:-https://github.com/andyrenxu7255/solocrm.git}"

echo "📂 工作区：$WORKSPACE"
echo "📂 项目目录：$PROJECT_DIR"
echo ""

# 克隆代码（如果不存在）
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📥 克隆代码..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    echo "✅ 代码克隆完成"
else
    echo "✅ 代码已存在"
fi

cd "$PROJECT_DIR"

# 安装 CLI（如果系统有 Python）
if command -v python &> /dev/null; then
    echo "🔧 安装 SoloCRM CLI..."
    python -m pip install -e .
    echo "✅ CLI 安装完成"
else
    echo "⚠️  未找到 Python，跳过 CLI 安装"
fi

# 配置环境变量
if [ ! -f ".env" ]; then
    echo "⚙️  配置环境变量..."
    cp .env.example .env
    
    echo ""
    echo "请输入你的 AI API Key:"
    read -s OPENAI_API_KEY
    echo ""
    
    echo "请输入 API Base URL (直接回车使用默认 OpenAI):"
    read OPENAI_API_BASE
    OPENAI_API_BASE=${OPENAI_API_BASE:-https://api.openai.com/v1}
    
    # 生成随机密码
    if command -v openssl &> /dev/null; then
        POSTGRES_PASSWORD=$(openssl rand -hex 16)
        SECRET_KEY=$(openssl rand -hex 32)
    else
        POSTGRES_PASSWORD=$(python -c 'import secrets; print(secrets.token_hex(16))')
        SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
    fi
    
    # 写入配置
    sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_API_KEY/" .env
    sed -i "s|OPENAI_API_BASE=.*|OPENAI_API_BASE=$OPENAI_API_BASE|" .env
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    
    echo "✅ 配置完成"
else
    echo "✅ 环境变量已配置"
fi

echo ""
echo "🐳 启动 Docker 服务..."
$COMPOSE_CMD up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 15

echo ""
echo "🔍 健康检查..."

# 检查数据库
if $COMPOSE_CMD exec -T db pg_isready -U solocrm &> /dev/null; then
    echo "✅ 数据库运行正常"
else
    echo "❌ 数据库启动失败"
    $COMPOSE_CMD logs db
    exit 1
fi

# 检查后端
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "⚠️  后端服务可能还在启动中..."
fi

# 检查前端
if curl -s http://localhost:3000 &> /dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "⚠️  前端服务可能还在启动中..."
fi

echo ""
echo "========================"
echo "🎉 部署完成！"
echo "========================"
echo ""
echo "🌐 浏览器访问：http://localhost:3000"
echo "📱 OpenClaw IM: 直接在对话中使用"
echo ""
echo "📝 重要信息："
echo "   数据库密码：$POSTGRES_PASSWORD"
echo "   (已保存在 .env 文件)"
echo ""
echo "💡 常用命令："
echo "   查看日志：docker compose logs -f"
echo "   停止服务：docker compose down"
echo "   重启服务：docker compose restart"
echo "   审计检查：solocrm audit summary --json"
echo "   失败追溯：solocrm audit errors --json"
echo "   安装 CLI：python -m pip install -e ."
echo "   健康检查：solocrm doctor --json"
echo ""
echo "📖 文档：https://github.com/andyrenxu7255/solocrm"
echo ""
