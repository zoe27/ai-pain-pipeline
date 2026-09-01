#!/usr/bin/env python3
"""
完全自动化的 Pipeline Orchestrator
集成 Claude API，无需手动触发 Agent

使用方式:
  export ANTHROPIC_API_KEY=your-key-here
  python3 pipeline_orchestrator_auto.py run --pipeline-id pipe_2026-06-07_001
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess

# 检查 API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
USE_API = ANTHROPIC_API_KEY is not None

if USE_API:
    try:
        import anthropic
    except ImportError:
        print("❌ 需要安装 anthropic 包: pip install anthropic")
        USE_API = False


class AutoPipelineOrchestrator:
    """完全自动化的 Pipeline 编排器"""
    
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.pid_path = Path(f"runs/{pipeline_id}")
        self.client = None
        
        if USE_API:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def _call_claude(self, system_prompt: str, user_prompt: str, model="claude-3-5-sonnet-20241022") -> str:
        """调用 Claude API"""
        if not self.client:
            raise RuntimeError("Claude API 未配置，请设置 ANTHROPIC_API_KEY")
        
        message = self.client.messages.create(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        return message.content[0].text
    
    def _run_helper(self, script: str, *args) -> bool:
        """运行 helper 脚本"""
        cmd = ["python3", f"helpers/{script}", self.pipeline_id] + list(args)
        print(f"  → {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ {result.stderr}")
            return False
        print(f"  ✅ Success")
        return True
    
    def run_stage_1_auto(self) -> bool:
        """Stage 1: 自动生成痛点分析"""
        print("\n📡 Stage 1: 痛点雷达")
        
        # 读取原始数据
        raw_dir = self.pid_path / "_raw"
        if not raw_dir.exists():
            print("❌ _raw 目录不存在，先运行 fetch_radar.py")
            return False
        
        # 收集所有原始数据
        raw_data = []
        for json_file in raw_dir.glob("*.json"):
            if json_file.name.endswith("_top.json"):
                continue
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        raw_data.extend(data[:10])  # 每个源取前 10 条
            except:
                continue
        
        print(f"  找到 {len(raw_data)} 条原始数据")
        
        # 构建 prompt
        system_prompt = """你是痛点分析专家。分析用户痛点数据，为每条提取：
1. sentiment: frustrated / annoyed / curious / celebrating (情感分类)
2. keywords: 3-7 个关键词

输出 JSON 格式:
{
  "pain_points": [
    {
      "source_id": "原始 ID",
      "sentiment": "frustrated",
      "keywords": ["keyword1", "keyword2", ...]
    }
  ]
}
"""
        
        user_prompt = f"分析以下痛点数据:\n\n{json.dumps(raw_data[:50], ensure_ascii=False, indent=2)}"
        
        # 调用 Claude
        print("  🤖 调用 Claude API 分析...")
        response = self._call_claude(system_prompt, user_prompt)
        
        # 解析 JSON
        try:
            # 提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                stage1_data = json.loads(json_match.group())
            else:
                stage1_data = json.loads(response)
            
            # 保存判断
            judgment_file = self.pid_path / "_judgments" / "stage1.json"
            judgment_file.parent.mkdir(exist_ok=True)
            with open(judgment_file, "w") as f:
                json.dump(stage1_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ stage1.json 已生成")
            
            # 运行 helper
            return self._run_helper("build_pain_batch.py")
            
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            return False
    
    def run_stage_4_auto(self) -> bool:
        """Stage 4: 自动生成 PRD"""
        print("\n📝 Stage 4: PRD 撰写")
        
        # 读取 Stage 3 数据
        stage3_file = self.pid_path / "3_opportunity.json"
        if not stage3_file.exists():
            print("❌ 3_opportunity.json 不存在")
            return False
        
        with open(stage3_file) as f:
            opportunity = json.load(f)
        
        # 读取 skill 指南
        skill_file = Path(".claude/skills/prd-writer/SKILL.md")
        with open(skill_file) as f:
            skill_guide = f.read()
        
        # 构建 prompt
        system_prompt = f"""你是产品经理专家。根据以下指南撰写 PRD:

{skill_guide}

输出严格的 JSON 格式，包含:
- product_vision
- target_user_stories (数组)
- core_features (数组)
- acceptance_criteria (数组)
- success_metrics (对象)
- constraints_and_assumptions (对象)
- risks_and_mitigations (对象)
- competitive_positioning (对象)
- monetization_model (对象)
- timeline_estimate_weeks (数字)
"""
        
        user_prompt = f"""基于以下 Opportunity 撰写 PRD:

{json.dumps(opportunity, ensure_ascii=False, indent=2)}

请输出完整的 stage4.json 格式。"""
        
        # 调用 Claude
        print("  🤖 调用 Claude API 生成 PRD...")
        response = self._call_claude(system_prompt, user_prompt, model="claude-3-5-sonnet-20241022")
        
        # 解析并保存
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                stage4_data = json.loads(json_match.group())
            else:
                stage4_data = json.loads(response)
            
            judgment_file = self.pid_path / "_judgments" / "stage4.json"
            with open(judgment_file, "w") as f:
                json.dump(stage4_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ stage4.json 已生成")
            
            # 运行 helper
            return self._run_helper("build_prd.py")
            
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            print(f"  Response: {response[:500]}")
            return False
    
    def run_auto_pipeline(self, start_stage: int = 1):
        """自动运行整个 pipeline"""
        print(f"\n{'='*60}")
        print(f"🤖 完全自动化 Pipeline: {self.pipeline_id}")
        print(f"{'='*60}\n")
        
        if not USE_API:
            print("❌ Claude API 未配置")
            print("\n设置方法:")
            print("  export ANTHROPIC_API_KEY=your-key-here")
            print("  pip install anthropic")
            return
        
        # 根据现有数据判断从哪个 stage 开始
        if start_stage <= 1 and not (self.pid_path / "1_pain_points.json").exists():
            if not self.run_stage_1_auto():
                return
        
        # Stage 2-3 类似实现（这里简化）
        
        # Stage 4
        if start_stage <= 4 and (self.pid_path / "3_opportunity.json").exists():
            if not self.run_stage_4_auto():
                return
        
        print("\n🎉 自动化完成！")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="完全自动化 Pipeline Orchestrator")
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--pipeline-id", required=True)
    run_parser.add_argument("--start-stage", type=int, default=1)
    
    args = parser.parse_args()
    
    if args.command == "run":
        orchestrator = AutoPipelineOrchestrator(args.pipeline_id)
        orchestrator.run_auto_pipeline(args.start_stage)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
