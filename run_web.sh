#!/bin/bash
# Flow 复楼 MA Agent - Streamlit Web UI 启动脚本

echo "🚀 启动 Flow 复楼 - 智能社交营销AI代理 Web界面..."
echo ""

# 检查streamlit是否安装
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 正在安装 Streamlit..."
    python3 -m pip install streamlit -q
fi

# 获取本机IP
IP=$(hostname -I | awk '{print $1}')

echo "📝 使用方法:"
echo "  1. 本地访问: http://localhost:8501"
echo "  2. 局域网访问: http://$IP:8501"
echo ""
echo "⚙️  配置LLM:"
echo "  - 在左侧边栏选择提供商并输入API Key"
echo "  - 或设置环境变量: export LLM_PROVIDER=deepseek"
echo "  - export DEEPSEEK_API_KEY=your_key"
echo ""
echo "🌐 正在启动服务..."
echo ""

# 启动streamlit
python3 -m streamlit run streamlit_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
