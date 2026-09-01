#!/bin/bash
# 完整演示：Dashboard + Pipeline 同时运行

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🚀 AI Pain Pipeline 完整演示"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv .venv"
    exit 1
fi

# 安装依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt 2>/dev/null || {
    echo "⚠️  依赖安装可能需要一些时间..."
    pip install -r requirements.txt
}
echo "✅ 依赖已就绪"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "📋 选择运行模式"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  [1] 完整模式 - 同时运行 Dashboard + Pipeline Orchestrator"
echo "      (推荐：体验完整自动化流程)"
echo ""
echo "  [2] 仅 Dashboard - 查看已有 Pipeline 状态"
echo "      (适合：只想查看进度，不启动新流程)"
echo ""
echo "  [3] 仅 Orchestrator - 运行 Pipeline 自动化"
echo "      (适合：后台运行，不需要 Web 界面)"
echo ""
echo "  [4] 演示模式 - 使用已有数据快速演示"
echo "      (适合：第一次使用，想快速看效果)"
echo ""

read -p "请选择 [1-4]: " choice
echo ""

case $choice in
    1)
        echo "═══════════════════════════════════════════════════════════"
        echo "🌐 模式 1: 完整模式"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "这将在两个终端窗口中运行："
        echo "  • 终端 1: Decision Dashboard (Web UI)"
        echo "  • 终端 2: Pipeline Orchestrator (自动化引擎)"
        echo ""
        echo "步骤："
        echo "  1. 在当前终端运行 Dashboard"
        echo "  2. 打开新终端，运行以下命令："
        echo ""
        echo "     source .venv/bin/activate"
        echo "     python pipeline_orchestrator.py run"
        echo ""
        echo "  3. 在浏览器访问: http://localhost:8080"
        echo ""
        read -p "按 Enter 启动 Dashboard..."
        python decision_dashboard.py --port 8080
        ;;
    
    2)
        echo "═══════════════════════════════════════════════════════════"
        echo "📊 模式 2: 仅 Dashboard"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "启动 Web 界面查看 Pipeline 状态..."
        echo "访问: http://localhost:8080"
        echo ""
        python decision_dashboard.py --port 8080
        ;;
    
    3)
        echo "═══════════════════════════════════════════════════════════"
        echo "🤖 模式 3: 仅 Orchestrator"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "运行 Pipeline 自动化引擎..."
        echo ""
        python pipeline_orchestrator.py run
        ;;
    
    4)
        echo "═══════════════════════════════════════════════════════════"
        echo "🎬 模式 4: 演示模式"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        
        # 检查是否有示例数据
        if [ -f "runs/pipe_2026-06-07_001/3_opportunity.json" ]; then
            echo "✅ 发现示例 Pipeline: pipe_2026-06-07_001"
            echo ""
            echo "这个 Pipeline 已完成 Stage 0-3，现在演示 Stage 4 (PRD 撰写)："
            echo ""
            
            DEMO_PID="pipe_2026-06-07_001"
            
            # 检查是否已有 stage4.json
            if [ -f "runs/$DEMO_PID/_judgments/stage4.json" ]; then
                echo "✅ Stage 4 判断文件已存在"
                echo ""
                echo "运行 Helper 生成 PRD..."
                python helpers/build_prd.py $DEMO_PID
                
                if [ $? -eq 0 ]; then
                    echo ""
                    echo "✅ PRD 生成成功！"
                    echo ""
                    echo "查看文件:"
                    echo "  • JSON:     runs/$DEMO_PID/4_prd.json"
                    
                    # 生成 digest
                    if python helpers/digest.py runs/$DEMO_PID/4_prd.json 2>/dev/null; then
                        echo "  • Digest:   runs/$DEMO_PID/4_prd.digest.md"
                    fi
                    
                    echo ""
                    echo "下一步:"
                    echo "  1. 查看 PRD: cat runs/$DEMO_PID/4_prd.json | python -m json.tool"
                    echo "  2. 继续 Stage 5: 在 Claude Code 中运行 'tech-architect' skill"
                    echo "  3. 或启动 Dashboard 查看: python decision_dashboard.py --port 8080"
                else
                    echo "❌ PRD 生成失败，检查 stage4.json 格式"
                fi
            else
                echo "ℹ️  Stage 4 判断文件不存在"
                echo ""
                echo "要继续演示，需要："
                echo "  1. 在 Claude Code 中打开: .claude/skills/prd-writer/SKILL.md"
                echo "  2. 按照指南写 runs/$DEMO_PID/_judgments/stage4.json"
                echo "  3. 然后重新运行此脚本"
                echo ""
                echo "或者查看已完成的 Stage 3 输出："
                echo "  cat runs/$DEMO_PID/3_opportunity.json | python -m json.tool"
            fi
        else
            echo "ℹ️  没有找到示例数据"
            echo ""
            echo "启动新的 Pipeline 演示："
            echo ""
            
            NEW_PID="pipe_demo_$(date +%Y%m%d)"
            echo "Pipeline ID: $NEW_PID"
            echo ""
            
            mkdir -p runs/$NEW_PID/{_raw,_judgments}
            
            echo "创建目录结构..."
            echo "  ✅ runs/$NEW_PID/_raw/"
            echo "  ✅ runs/$NEW_PID/_judgments/"
            echo ""
            echo "下一步:"
            echo "  1. 运行 Stage 1: python helpers/fetch_radar.py $NEW_PID --config configs/radar.example.yaml"
            echo "  2. 在 Claude Code 中运行 'pain-radar' skill"
            echo "  3. 或启动完整 Orchestrator: python pipeline_orchestrator.py run --pipeline-id $NEW_PID"
        fi
        ;;
    
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac
