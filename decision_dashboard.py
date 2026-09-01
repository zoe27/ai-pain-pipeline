#!/usr/bin/env python3
"""
Simple Web Dashboard for Pipeline Decisions

启动方式：
  python3 decision_dashboard.py --port 8080

访问：http://localhost:8080
"""

from flask import Flask, render_template_string, request, jsonify
from pathlib import Path
import json
from datetime import datetime
from pipeline_orchestrator import PipelineState

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Pain Pipeline - Decision Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 30px; }
        .pipeline-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .pipeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .pipeline-id { font-size: 18px; font-weight: bold; color: #2563eb; }
        .stage-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .stage-complete { background: #d1fae5; color: #065f46; }
        .stage-waiting { background: #fef3c7; color: #92400e; }
        .stage-failed { background: #fee2e2; color: #991b1b; }
        .decision-box {
            background: #fef9c3;
            border-left: 4px solid #eab308;
            padding: 15px;
            margin: 15px 0;
        }
        .decision-title { font-weight: bold; margin-bottom: 10px; }
        .decision-options {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary { background: #2563eb; color: white; }
        .btn-success { background: #16a34a; color: white; }
        .btn-warning { background: #ea580c; color: white; }
        .btn-danger { background: #dc2626; color: white; }
        button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .stage-timeline {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
            position: relative;
        }
        .stage-item {
            text-align: center;
            flex: 1;
            position: relative;
        }
        .stage-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            margin: 0 auto 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
        }
        .stage-dot.complete { background: #16a34a; }
        .stage-dot.current { background: #2563eb; }
        .stage-dot.pending { background: #d1d5db; color: #6b7280; }
        .stage-line {
            position: absolute;
            top: 15px;
            left: 50%;
            right: -50%;
            height: 2px;
            background: #d1d5db;
            z-index: -1;
        }
        .stage-line.complete { background: #16a34a; }
        .digest-link {
            color: #2563eb;
            text-decoration: none;
            font-weight: 500;
        }
        .digest-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Pain Pipeline Dashboard</h1>
        
        {% for pipeline in pipelines %}
        <div class="pipeline-card">
            <div class="pipeline-header">
                <div class="pipeline-id">{{ pipeline.pipeline_id }}</div>
                <div>
                    {% if pipeline.waiting_decision %}
                    <span class="stage-badge stage-waiting">
                        🚦 等待决策点 {{ pipeline.waiting_decision }}
                    </span>
                    {% else %}
                    <span class="stage-badge stage-complete">
                        Stage {{ pipeline.current_stage }} 完成
                    </span>
                    {% endif %}
                </div>
            </div>
            
            <div class="stage-timeline">
                {% for i in range(10) %}
                <div class="stage-item">
                    <div class="stage-dot {% if i < pipeline.current_stage %}complete{% elif i == pipeline.current_stage %}current{% else %}pending{% endif %}">
                        {{ i }}
                    </div>
                    <div style="font-size: 11px; color: #6b7280;">
                        {{ pipeline.stage_names[i] }}
                    </div>
                    {% if i < 9 %}
                    <div class="stage-line {% if i < pipeline.current_stage %}complete{% endif %}"></div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            {% if pipeline.opportunity_title %}
            <div style="margin: 12px 0; padding: 12px; background: #f0f9ff; border-radius: 6px; font-size: 14px;">
                <strong>{{ pipeline.opportunity_title }}</strong>
                {% if pipeline.opportunity_score %}
                · 分数 <strong>{{ pipeline.opportunity_score }}</strong> ({{ pipeline.opportunity_tier }})
                {% endif %}
                {% if pipeline.recommendation %}
                · 建议 <strong>{{ pipeline.recommendation }}</strong>
                {% endif %}
            </div>
            {% endif %}
            
            {% if pipeline.waiting_decision %}
            <div class="decision-box">
                <div class="decision-title">
                    🚦 决策点 {{ pipeline.waiting_decision }}: {{ pipeline.decision_name }}
                </div>
                <div>
                    请查看:
                    {% for link in pipeline.review_links %}
                    <a href="{{ link.url }}" class="digest-link" target="_blank">{{ link.name }}</a>
                    {% if not loop.last %} · {% endif %}
                    {% endfor %}
                </div>
                <div class="decision-options">
                    {% for option in pipeline.decision_options %}
                    <button class="btn-{% if option == 'GO' or option == 'PROCEED' or option == 'MERGE' or option == 'SCALE' %}success{% elif option == 'WAIT' or option == 'REVISE' or option == 'REQUEST_CHANGES' or option == 'OPTIMIZE' %}warning{% else %}danger{% endif %}"
                            onclick="makeDecision('{{ pipeline.pipeline_id }}', {{ pipeline.waiting_decision }}, '{{ option }}')">
                        {{ option }}
                    </button>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
        {% endfor %}
        
        {% if not pipelines %}
        <div class="pipeline-card" style="text-align: center; color: #6b7280;">
            <p>暂无可展示的 Pipeline</p>
            <p style="margin-top: 10px; font-size: 14px;">
                先跑 Stage 1–3，或运行 <code>python3 pipeline_orchestrator.py run</code>
            </p>
        </div>
        {% endif %}
    </div>
    
    <script>
        function makeDecision(pipelineId, decisionPoint, decision) {
            if (!confirm(`确认决策: ${decision}?`)) return;
            
            fetch('/api/decide', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pipeline_id: pipelineId,
                    decision_point: decisionPoint,
                    decision: decision
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('✅ 决策已记录');
                    location.reload();
                } else {
                    alert('❌ 决策失败: ' + data.error);
                }
            })
            .catch(err => alert('❌ 网络错误: ' + err));
        }
        
        // 每 30 秒自动刷新
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""


STAGE_ARTIFACTS = {
    0: "domain_context.json",
    1: "1_pain_points.json",
    2: "2_scored_pain_points.json",
    3: "3_opportunity.json",
    4: "4_prd.json",
    5: "5_tech_spec.json",
    7: "7_code_delivery.json",
    8: "8_deployment.json",
    9: "9_growth_metrics.json",
}

# decision_point -> (completed_stage, next_stage_artifact)
DECISION_BREAKPOINTS = {
    1: (3, "4_prd.json"),
    2: (5, "7_code_delivery.json"),
    3: (7, "8_deployment.json"),
    4: (9, None),
}


def infer_stage_from_files(pid_dir: Path) -> int:
    """从 runs/{pid}/ 下的产出文件推断当前完成的最高 stage。"""
    current = 0
    for stage, artifact in STAGE_ARTIFACTS.items():
        if (pid_dir / artifact).exists():
            current = max(current, stage)
    if current >= 5 and (pid_dir / "6_codebase").is_dir():
        current = max(current, 6)
    return current


def infer_waiting_decision(pid_dir: Path, current_stage: int, recorded_decisions: dict) -> int | None:
    """推断是否在决策点等待（无 _state.json 时用文件存在性启发式判断）。"""
    for dp, (after_stage, next_artifact) in DECISION_BREAKPOINTS.items():
        if str(dp) in recorded_decisions:
            continue
        if current_stage >= after_stage:
            if next_artifact is None or not (pid_dir / next_artifact).exists():
                return dp
    return None


def build_review_links(pipeline_id: str, waiting_decision: int) -> list[dict]:
    """决策点对应的 digest 链接。"""
    links = []
    if waiting_decision == 1:
        for name, path in [
            ("机会摘要 (中文)", "3_opportunity.digest.zh.md"),
            ("Opportunity Digest", "3_opportunity.digest.md"),
        ]:
            if Path(f"runs/{pipeline_id}/{path}").exists():
                links.append({"name": name, "url": f"/view/{pipeline_id}/{path}"})
    elif waiting_decision == 2:
        for name, path in [
            ("PRD Digest", "4_prd.digest.md"),
            ("Tech Spec Digest", "5_tech_spec.digest.md"),
        ]:
            if Path(f"runs/{pipeline_id}/{path}").exists():
                links.append({"name": name, "url": f"/view/{pipeline_id}/{path}"})
    elif waiting_decision == 3:
        links.append({
            "name": "Code Delivery",
            "url": f"/view/{pipeline_id}/7_code_delivery.json",
        })
    elif waiting_decision == 4:
        links.append({
            "name": "Growth Metrics",
            "url": f"/view/{pipeline_id}/9_growth_metrics.digest.md",
        })
    return links


def load_opportunity_summary(pid_dir: Path) -> dict:
    """读取 Stage 3 机会摘要（若有）。"""
    opp_path = pid_dir / "3_opportunity.json"
    if not opp_path.exists():
        return {}
    try:
        opp = json.loads(opp_path.read_text())
        score = opp.get("opportunity_score") or {}
        return {
            "opportunity_title": opp.get("title"),
            "opportunity_score": score.get("score"),
            "opportunity_tier": score.get("tier"),
            "recommendation": opp.get("recommendation"),
        }
    except (json.JSONDecodeError, OSError):
        return {}


def get_active_pipelines():
    """获取所有可展示的 pipeline（支持 _state.json 与纯文件态 runs）。"""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        return []

    pipelines = []
    for pid_dir in runs_dir.iterdir():
        if not pid_dir.is_dir() or not pid_dir.name.startswith("pipe_"):
            continue

        has_output = any((pid_dir / a).exists() for a in STAGE_ARTIFACTS.values())
        has_state = (pid_dir / "_state.json").exists()
        if not has_output and not has_state:
            continue

        stage_names = ["领域", "雷达", "ICE", "研究", "PRD", "架构", "编码", "测试", "部署", "运营"]

        if has_state:
            state = PipelineState(pid_dir.name)
            current_stage = state.state["current_stage"]
            waiting_decision = state.is_waiting_decision()
            recorded_decisions = state.state.get("decisions") or {}
        else:
            current_stage = infer_stage_from_files(pid_dir)
            recorded_decisions = {}
            waiting_decision = infer_waiting_decision(pid_dir, current_stage, recorded_decisions)

        pipeline_info = {
            "pipeline_id": pid_dir.name,
            "current_stage": current_stage,
            "waiting_decision": waiting_decision,
            "stage_names": stage_names,
            **load_opportunity_summary(pid_dir),
        }

        if waiting_decision:
            dp_info = PipelineState.DECISION_POINTS[waiting_decision]
            pipeline_info["decision_name"] = dp_info["name"]
            pipeline_info["decision_options"] = dp_info["options"]
            pipeline_info["review_links"] = build_review_links(pid_dir.name, waiting_decision)

        pipelines.append(pipeline_info)

    pipelines.sort(key=lambda p: p["pipeline_id"], reverse=True)
    return pipelines


@app.route('/')
def index():
    """Dashboard 首页"""
    pipelines = get_active_pipelines()
    return render_template_string(HTML_TEMPLATE, pipelines=pipelines)


@app.route('/api/decide', methods=['POST'])
def api_decide():
    """API: 记录决策"""
    data = request.json
    pipeline_id = data.get('pipeline_id')
    decision_point = data.get('decision_point')
    decision = data.get('decision')
    
    if not all([pipeline_id, decision_point, decision]):
        return jsonify({"success": False, "error": "Missing parameters"}), 400
    
    try:
        pid_dir = Path(f"runs/{pipeline_id}")
        had_state = (pid_dir / "_state.json").exists()
        state = PipelineState(pipeline_id)
        if not had_state:
            inferred = infer_stage_from_files(pid_dir)
            if inferred > 0:
                state.state["current_stage"] = inferred
        state.record_decision(decision_point, decision, reviewer="web_dashboard")
        state.save_state()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/view/<pipeline_id>/<path:filename>')
def view_file(pipeline_id, filename):
    """查看文件"""
    file_path = Path(f"runs/{pipeline_id}/{filename}")
    if not file_path.exists():
        return f"File not found: {filename}", 404
    
    content = file_path.read_text(encoding='utf-8')
    
    if filename.endswith('.json'):
        return f"<pre>{content}</pre>"
    elif filename.endswith('.md'):
        # 简单的 Markdown 渲染
        import markdown
        html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
                pre {{ background: #f5f5f5; padding: 15px; border-radius: 6px; overflow-x: auto; }}
                code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #f5f5f5; font-weight: 600; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
    else:
        return content


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"🌐 Decision Dashboard 已启动")
    print(f"{'='*60}")
    print(f"\n访问: http://{args.host}:{args.port}\n")
    
    app.run(host=args.host, port=args.port, debug=True)
