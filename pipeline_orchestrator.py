#!/usr/bin/env python3
"""
AI Pain Pipeline Orchestrator

自动化运行整个 pipeline，人只需要在 4 个决策点 review。

使用方式：
  python3 pipeline_orchestrator.py run --mode continuous
  python3 pipeline_orchestrator.py run --pipeline-id pipe_2026-06-15_001
  python3 pipeline_orchestrator.py approve --pipeline-id pipe_2026-06-15_001 --decision-point 1 --decision GO
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Literal, Optional
import subprocess


class PipelineState:
    """Pipeline 状态机"""
    
    # Stage 状态
    STAGES = {
        0: "domain_focus",
        1: "pain_radar",
        2: "ice_scoring",
        3: "user_research",
        4: "prd_writing",
        5: "tech_architecture",
        6: "coding",
        7: "testing",
        8: "deployment",
        9: "operations"
    }
    
    # 决策点
    DECISION_POINTS = {
        1: {"after_stage": 3, "name": "GO/NO-GO", "options": ["GO", "WAIT", "NO-GO"]},
        2: {"after_stage": 5, "name": "方案审批", "options": ["PROCEED", "REVISE", "CANCEL"]},
        3: {"after_stage": 7, "name": "上线放行", "options": ["MERGE", "REQUEST_CHANGES", "BLOCK"]},
        4: {"after_stage": 9, "name": "商业策略", "options": ["SCALE", "OPTIMIZE", "SUNSET", "PIVOT"]}
    }
    
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.state_file = Path(f"runs/{pipeline_id}/_state.json")
        self.load_state()
    
    def load_state(self):
        """加载 pipeline 状态"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "pipeline_id": self.pipeline_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "current_stage": 0,
                "stage_status": {},
                "decisions": {},
                "mode": "manual"  # manual | auto | continuous
            }
    
    def save_state(self):
        """保存状态"""
        self.state["updated_at"] = datetime.utcnow().isoformat() + "Z"
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def mark_stage_complete(self, stage: int, output_file: str):
        """标记 stage 完成"""
        self.state["stage_status"][str(stage)] = {
            "status": "complete",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "output_file": output_file
        }
        self.state["current_stage"] = stage
        self.save_state()
    
    def mark_stage_failed(self, stage: int, error: str):
        """标记 stage 失败"""
        self.state["stage_status"][str(stage)] = {
            "status": "failed",
            "failed_at": datetime.utcnow().isoformat() + "Z",
            "error": error
        }
        self.save_state()
    
    def is_waiting_decision(self) -> Optional[int]:
        """检查是否在等待决策"""
        current = self.state["current_stage"]
        for dp_num, dp_info in self.DECISION_POINTS.items():
            if current == dp_info["after_stage"]:
                if str(dp_num) not in self.state["decisions"]:
                    return dp_num
        return None
    
    def record_decision(self, decision_point: int, decision: str, reviewer: str = "human"):
        """记录决策"""
        self.state["decisions"][str(decision_point)] = {
            "decision": decision,
            "reviewer": reviewer,
            "decided_at": datetime.utcnow().isoformat() + "Z"
        }
        self.save_state()
    
    def get_decision(self, decision_point: int) -> Optional[str]:
        """获取决策"""
        return self.state["decisions"].get(str(decision_point), {}).get("decision")


class PipelineOrchestrator:
    """Pipeline 自动化编排器"""
    
    def __init__(self, pipeline_id: str, config: dict = None):
        self.pipeline_id = pipeline_id
        self.state = PipelineState(pipeline_id)
        self.config = config or {}
        self.pid_path = Path(f"runs/{pipeline_id}")
        self.pid_path.mkdir(parents=True, exist_ok=True)
        (self.pid_path / "_raw").mkdir(exist_ok=True)
        (self.pid_path / "_judgments").mkdir(exist_ok=True)
    
    def run_stage(self, stage: int) -> bool:
        """运行指定 stage"""
        stage_name = PipelineState.STAGES[stage]
        print(f"\n{'='*60}")
        print(f"🚀 Running Stage {stage}: {stage_name}")
        print(f"{'='*60}\n")
        
        try:
            if stage == 0:
                return self._run_stage_0()
            elif stage == 1:
                return self._run_stage_1()
            elif stage == 2:
                return self._run_stage_2()
            elif stage == 3:
                return self._run_stage_3()
            elif stage == 4:
                return self._run_stage_4()
            elif stage == 5:
                return self._run_stage_5()
            elif stage == 6:
                return self._run_stage_6_7()
            elif stage == 7:
                return True  # Stage 7 包含在 Stage 6 中
            elif stage == 8:
                return self._run_stage_8()
            elif stage == 9:
                return self._run_stage_9()
            else:
                print(f"❌ Unknown stage: {stage}")
                return False
        except Exception as e:
            print(f"❌ Stage {stage} failed: {e}")
            self.state.mark_stage_failed(stage, str(e))
            return False
    
    def _run_helper(self, script: str, *args) -> bool:
        """运行 helper 脚本"""
        cmd = ["python3", f"helpers/{script}", self.pipeline_id] + list(args)
        print(f"  → {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ❌ Failed: {result.stderr}")
            return False
        print(f"  ✅ Success")
        return True
    
    def _run_stage_0(self) -> bool:
        """Stage 0: 领域定向 (可选)"""
        print("⏭️  Stage 0 是可选的，跳过...")
        return True
    
    def _run_stage_1(self) -> bool:
        """Stage 1: 痛点雷达"""
        print("📡 抓取痛点数据...")
        config = self.config.get("radar_config", "configs/radar.market_balanced.yaml")
        
        if not self._run_helper("fetch_radar.py", "--config", config):
            return False
        
        print("\n⏳ 等待 Agent 写 stage1.json...")
        print("   请在 Claude Code 中运行 'pain-radar' skill")
        print("   完成后按 Enter 继续...")
        input()
        
        if not (self.pid_path / "_judgments" / "stage1.json").exists():
            print("❌ stage1.json 不存在")
            return False
        
        if not self._run_helper("build_pain_batch.py"):
            return False
        
        if not self._run_helper("digest.py", f"runs/{self.pipeline_id}/1_pain_points.json"):
            return False
        
        self.state.mark_stage_complete(1, "1_pain_points.json")
        return True
    
    def _run_stage_2(self) -> bool:
        """Stage 2: ICE 评分"""
        print("📊 ICE 评分...")
        
        print("\n⏳ 等待 Agent 写 stage2.json...")
        print("   请在 Claude Code 中运行 'score-pain' skill")
        print("   完成后按 Enter 继续...")
        input()
        
        if not (self.pid_path / "_judgments" / "stage2.json").exists():
            print("❌ stage2.json 不存在")
            return False
        
        if not self._run_helper("build_scored_batch.py"):
            return False
        
        if not self._run_helper("digest.py", f"runs/{self.pipeline_id}/2_scored_pain_points.json"):
            return False
        
        self.state.mark_stage_complete(2, "2_scored_pain_points.json")
        return True
    
    def _run_stage_3(self) -> bool:
        """Stage 3: 用户研究"""
        print("🔬 用户研究...")
        
        print("\n⏳ 等待 Agent 写 stage3.json...")
        print("   请在 Claude Code 中运行 'user-research' skill")
        print("   完成后按 Enter 继续...")
        input()
        
        if not (self.pid_path / "_judgments" / "stage3.json").exists():
            print("❌ stage3.json 不存在")
            return False
        
        if not self._run_helper("build_opportunity.py"):
            return False
        
        if not self._run_helper("digest.py", f"runs/{self.pipeline_id}/3_opportunity.json"):
            return False
        
        self.state.mark_stage_complete(3, "3_opportunity.json")
        
        # 触发决策点 ①
        self._notify_decision_point(1)
        return True
    
    def _run_stage_4(self) -> bool:
        """Stage 4: PRD 撰写"""
        print("📝 PRD 撰写...")
        
        print("\n⏳ 等待 Agent 写 stage4.json...")
        print("   请在 Claude Code 中运行 'prd-writer' skill")
        print("   完成后按 Enter 继续...")
        input()
        
        if not (self.pid_path / "_judgments" / "stage4.json").exists():
            print("❌ stage4.json 不存在")
            return False
        
        if not self._run_helper("build_prd.py"):
            return False
        
        if not self._run_helper("digest.py", f"runs/{self.pipeline_id}/4_prd.json"):
            return False
        
        self.state.mark_stage_complete(4, "4_prd.json")
        return True
    
    def _run_stage_5(self) -> bool:
        """Stage 5: 技术架构"""
        print("🏗️  技术架构...")
        
        print("\n⏳ 等待 Agent 写 stage5.json...")
        print("   请在 Claude Code 中运行 'tech-architect' skill")
        print("   完成后按 Enter 继续...")
        input()
        
        if not (self.pid_path / "_judgments" / "stage5.json").exists():
            print("❌ stage5.json 不存在")
            return False
        
        if not self._run_helper("build_tech_spec.py"):
            return False
        
        if not self._run_helper("digest.py", f"runs/{self.pipeline_id}/5_tech_spec.json"):
            return False
        
        self.state.mark_stage_complete(5, "5_tech_spec.json")
        
        # 触发决策点 ②
        self._notify_decision_point(2)
        return True
    
    def _run_stage_6_7(self) -> bool:
        """Stage 6-7: 编码 + 测试"""
        print("💻 编码 + 测试...")
        print("\n   这个阶段需要开发者手动完成：")
        print("   1. 在 Git repo 中编写代码")
        print("   2. 运行测试")
        print("   3. 提交 PR")
        print("   4. CI/CD 通过")
        print("\n   完成后按 Enter 继续...")
        input()
        
        self.state.mark_stage_complete(6, "git_repo")
        self.state.mark_stage_complete(7, "7_code_delivery.json")
        
        # 触发决策点 ③
        self._notify_decision_point(3)
        return True
    
    def _run_stage_8(self) -> bool:
        """Stage 8: 部署"""
        print("🚀 部署...")
        print("\n   这个阶段需要 DevOps/SRE 完成：")
        print("   1. 部署到 staging")
        print("   2. 验证健康检查")
        print("   3. 部署到 production")
        print("   4. 启动监控")
        print("\n   完成后按 Enter 继续...")
        input()
        
        self.state.mark_stage_complete(8, "8_deployment.json")
        return True
    
    def _run_stage_9(self) -> bool:
        """Stage 9: 运营"""
        print("📊 运营 + 增长...")
        print("\n   这个阶段持续运行，收集数据：")
        print("   - 每周生成增长报告")
        print("   - 每月触发决策点 ④")
        print("\n   按 Enter 标记完成...")
        input()
        
        self.state.mark_stage_complete(9, "9_growth_metrics.json")
        
        # 触发决策点 ④
        self._notify_decision_point(4)
        return True
    
    def _notify_decision_point(self, decision_point: int):
        """通知决策点到达"""
        dp_info = PipelineState.DECISION_POINTS[decision_point]
        print(f"\n{'🚦'*20}")
        print(f"🚦 决策点 {decision_point}: {dp_info['name']}")
        print(f"{'🚦'*20}")
        print(f"\n可选决策: {', '.join(dp_info['options'])}")
        print(f"\n请查看:")
        
        if decision_point == 1:
            print(f"  - runs/{self.pipeline_id}/3_opportunity.digest.md")
            print(f"  - opportunity_score + recommendation")
        elif decision_point == 2:
            print(f"  - runs/{self.pipeline_id}/4_prd.digest.md")
            print(f"  - runs/{self.pipeline_id}/5_tech_spec.digest.md")
        elif decision_point == 3:
            print(f"  - GitHub PR + CI/CD 结果")
            print(f"  - 测试覆盖率 + 安全扫描")
        elif decision_point == 4:
            print(f"  - runs/{self.pipeline_id}/9_growth_metrics.digest.md")
            print(f"  - DAU/MAU/ARR 指标")
        
        print(f"\n审批命令:")
        print(f"  python3 pipeline_orchestrator.py approve \\")
        print(f"    --pipeline-id {self.pipeline_id} \\")
        print(f"    --decision-point {decision_point} \\")
        print(f"    --decision [{'|'.join(dp_info['options'])}]")
        print()
    
    def wait_for_decision(self, decision_point: int) -> str:
        """等待决策"""
        dp_info = PipelineState.DECISION_POINTS[decision_point]
        
        while True:
            decision = self.state.get_decision(decision_point)
            if decision:
                print(f"✅ 决策点 {decision_point} 已批准: {decision}")
                return decision
            
            print(f"⏳ 等待决策点 {decision_point} 审批...")
            print(f"   选项: {', '.join(dp_info['options'])}")
            time.sleep(10)  # 每 10 秒检查一次
    
    def run_full_pipeline(self):
        """运行完整 pipeline"""
        print(f"\n{'='*60}")
        print(f"🎯 Pipeline: {self.pipeline_id}")
        print(f"{'='*60}\n")
        
        current_stage = self.state.state["current_stage"]
        
        # Stage 1-3: 发现阶段
        for stage in range(max(1, current_stage), 4):
            if not self.run_stage(stage):
                print(f"\n❌ Pipeline 在 Stage {stage} 失败")
                return
        
        # 决策点 ①
        if self.state.is_waiting_decision() == 1:
            decision = self.wait_for_decision(1)
            if decision == "NO-GO":
                print("❌ Pipeline 被拒绝")
                return
            elif decision == "WAIT":
                print("⏸️  Pipeline 暂停")
                return
        
        # Stage 4-5: 设计阶段
        for stage in range(4, 6):
            if not self.run_stage(stage):
                print(f"\n❌ Pipeline 在 Stage {stage} 失败")
                return
        
        # 决策点 ②
        if self.state.is_waiting_decision() == 2:
            decision = self.wait_for_decision(2)
            if decision == "CANCEL":
                print("❌ Pipeline 被取消")
                return
            elif decision == "REVISE":
                print("🔄 返回 Stage 4 修改")
                return
        
        # Stage 6-7: 实现阶段
        for stage in range(6, 8):
            if not self.run_stage(stage):
                print(f"\n❌ Pipeline 在 Stage {stage} 失败")
                return
        
        # 决策点 ③
        if self.state.is_waiting_decision() == 3:
            decision = self.wait_for_decision(3)
            if decision == "BLOCK":
                print("❌ 上线被阻止")
                return
            elif decision == "REQUEST_CHANGES":
                print("🔄 返回 Stage 6 修改")
                return
        
        # Stage 8: 部署
        if not self.run_stage(8):
            print("\n❌ Pipeline 在 Stage 8 失败")
            return
        
        # Stage 9: 运营
        if not self.run_stage(9):
            print("\n❌ Pipeline 在 Stage 9 失败")
            return
        
        print("\n" + "="*60)
        print("🎉 Pipeline 完成！")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="AI Pain Pipeline Orchestrator")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行 pipeline")
    run_parser.add_argument("--pipeline-id", help="Pipeline ID (如 pipe_2026-06-15_001)")
    run_parser.add_argument("--mode", choices=["manual", "auto", "continuous"], default="manual")
    run_parser.add_argument("--config", help="配置文件路径")
    
    # approve 命令
    approve_parser = subparsers.add_parser("approve", help="审批决策点")
    approve_parser.add_argument("--pipeline-id", required=True)
    approve_parser.add_argument("--decision-point", type=int, required=True, choices=[1, 2, 3, 4])
    approve_parser.add_argument("--decision", required=True)
    approve_parser.add_argument("--reviewer", default="human")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="查看 pipeline 状态")
    status_parser.add_argument("--pipeline-id", required=True)
    
    args = parser.parse_args()
    
    if args.command == "run":
        pipeline_id = args.pipeline_id or f"pipe_{datetime.now().strftime('%Y-%m-%d')}_001"
        orchestrator = PipelineOrchestrator(pipeline_id)
        orchestrator.run_full_pipeline()
    
    elif args.command == "approve":
        state = PipelineState(args.pipeline_id)
        state.record_decision(args.decision_point, args.decision, args.reviewer)
        print(f"✅ 决策点 {args.decision_point} 已批准: {args.decision}")
    
    elif args.command == "status":
        state = PipelineState(args.pipeline_id)
        print(json.dumps(state.state, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
