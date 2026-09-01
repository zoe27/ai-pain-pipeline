#!/bin/bash
# 快速设置和运行自动化系统

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🚀 AI Pain Pipeline - 快速启动"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 激活虚拟环境
echo "📦 激活虚拟环境..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "⚠️  虚拟环境不存在，创建中..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
fi
echo ""

# 安装/更新依赖
echo "📦 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ 依赖已安装"
echo ""

# 检查 Python 版本
echo "🐍 Python 版本:"
python --version
echo ""

# 检查已安装的包
echo "📦 已安装的关键包:"
pip list | grep -E "flask|markdown|jsonschema|PyYAML|pytrends" || echo "  (正在安装...)"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "✨ 环境准备完成！"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "现在可以运行："
echo ""
echo "  [1] 启动 Decision Dashboard (Web 界面)"
echo "      python decision_dashboard.py --port 8080"
echo ""
echo "  [2] 启动 Pipeline Orchestrator (自动化引擎)"
echo "      python pipeline_orchestrator.py run"
echo ""
echo "  [3] 测试示例 Pipeline (已有数据)"
echo "      python pipeline_orchestrator.py status --pipeline-id pipe_2026-06-07_001"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# 提示用户选择
read -p "要启动什么？[1=Dashboard / 2=Orchestrator / 3=查看状态 / Enter=退出]: " choice

case $choice in
    1)
        echo ""
        echo "🌐 启动 Decision Dashboard..."
        echo "访问: http://localhost:8080"
        echo ""
        python decision_dashboard.py --port 8080
        ;;
    2)
        echo ""
        echo "🤖 启动 Pipeline Orchestrator..."
        echo ""
        python pipeline_orchestrator.py run
        ;;
    3)
        echo ""
        echo "📊 查看 Pipeline 状态..."
        echo ""
        if [ -f "runs/pipe_2026-06-07_001/_state.json" ]; then
            python pipeline_orchestrator.py status --pipeline-id pipe_2026-06-07_001
        else
            echo "⚠️  示例 Pipeline 状态文件不存在"
            echo "运行以下命令创建新 Pipeline:"
            echo "  python pipeline_orchestrator.py run"
        fi
        ;;
    *)
        echo ""
        echo "👋 已退出。随时运行 ./setup_and_run.sh 重新开始"
        echo ""
        ;;
esac
