#!/usr/bin/env python3
"""
Stage 4 Helper: Build PRD from agent judgment + opportunity

Merges _judgments/stage4.json with 3_opportunity.json into 4_prd.json
Applies strict schema validation.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import uuid


def build_prd(pipeline_id: str) -> dict:
    """
    Read Stage 4 agent judgment + Stage 3 opportunity.
    Merge into 4_prd.json.
    """
    pid_path = Path("runs") / pipeline_id
    
    # Load inputs
    stage4_path = pid_path / "_judgments" / "stage4.json"
    stage3_path = pid_path / "3_opportunity.json"
    
    if not stage4_path.exists():
        raise FileNotFoundError(f"{stage4_path} not found. Run Stage 4 agent first.")
    if not stage3_path.exists():
        raise FileNotFoundError(f"{stage3_path} not found. Stage 3 must complete first.")
    
    with open(stage4_path) as f:
        stage4_judgment = json.load(f)
    with open(stage3_path) as f:
        stage3_opportunity = json.load(f)
    
    # Build PRD
    prd = {
        "pipeline_id": pipeline_id,
        "opportunity_id": str(uuid.uuid4()),  # Reference to Stage 3
        "created_at": datetime.utcnow().isoformat() + "Z",
        "product_title": stage3_opportunity.get("title", "Untitled Product"),
        "product_vision": stage4_judgment.get("product_vision", ""),
        "target_user_stories": stage4_judgment.get("target_user_stories", []),
        "core_features": stage4_judgment.get("core_features", []),
        "acceptance_criteria": stage4_judgment.get("acceptance_criteria", []),
        "success_metrics": stage4_judgment.get("success_metrics", {}),
        "constraints_and_assumptions": stage4_judgment.get("constraints_and_assumptions", {}),
        "risks_and_mitigations": stage4_judgment.get("risks_and_mitigations", []),
        "competitive_positioning": stage4_judgment.get("competitive_positioning", {}),
        "monetization_model": stage4_judgment.get("monetization_model", {}),
        "timeline_estimate_weeks": stage4_judgment.get("timeline_estimate_weeks", 8),
    }
    
    # Validate against schema
    validate_prd_schema(prd)
    
    # Write output
    output_path = pid_path / "4_prd.json"
    with open(output_path, "w") as f:
        json.dump(prd, f, indent=2)
    
    print(f"✅ PRD written to {output_path}")
    return prd


def validate_prd_schema(prd: dict):
    """
    Minimal validation of required fields.
    Full validation would use jsonschema library.
    """
    required_fields = [
        "pipeline_id", "product_title", "product_vision",
        "target_user_stories", "core_features", "acceptance_criteria",
        "success_metrics", "competitive_positioning", "monetization_model"
    ]
    
    for field in required_fields:
        if field not in prd or not prd[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate user stories
    if len(prd.get("target_user_stories", [])) < 3:
        raise ValueError("Must have at least 3 user stories")
    
    for story in prd["target_user_stories"]:
        if not all(k in story for k in ["persona", "story", "acceptance"]):
            raise ValueError(f"User story missing required keys: {story}")
    
    # Validate features
    if len(prd.get("core_features", [])) < 3:
        raise ValueError("Must have at least 3 core features")
    
    for feat in prd["core_features"]:
        if feat.get("priority") not in ["p0", "p1", "p2", "p3"]:
            raise ValueError(f"Invalid priority: {feat.get('priority')}")
    
    print("✅ PRD schema validation passed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 helpers/build_prd.py <pipeline_id>")
        print("Example: python3 helpers/build_prd.py pipe_2026-06-15_001")
        sys.exit(1)
    
    pid = sys.argv[1]
    prd = build_prd(pid)
    print(f"PRD generated for {pid}")
