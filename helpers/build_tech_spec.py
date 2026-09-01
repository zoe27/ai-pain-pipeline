#!/usr/bin/env python3
"""
Stage 5 Helper: Build Tech Spec from agent judgment + PRD

Merges _judgments/stage5.json with 4_prd.json into 5_tech_spec.json
Applies strict schema validation.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import uuid


def build_tech_spec(pipeline_id: str) -> dict:
    """
    Read Stage 5 agent judgment + Stage 4 PRD.
    Merge into 5_tech_spec.json.
    """
    pid_path = Path("runs") / pipeline_id
    
    # Load inputs
    stage5_path = pid_path / "_judgments" / "stage5.json"
    stage4_path = pid_path / "4_prd.json"
    
    if not stage5_path.exists():
        raise FileNotFoundError(f"{stage5_path} not found. Run Stage 5 agent first.")
    if not stage4_path.exists():
        raise FileNotFoundError(f"{stage4_path} not found. Stage 4 must complete first.")
    
    with open(stage5_path) as f:
        stage5_judgment = json.load(f)
    with open(stage4_path) as f:
        stage4_prd = json.load(f)
    
    # Build Tech Spec
    tech_spec = {
        "pipeline_id": pipeline_id,
        "prd_id": str(uuid.uuid4()),  # Reference to Stage 4
        "created_at": datetime.utcnow().isoformat() + "Z",
        "product_title": stage4_prd.get("product_title", "Untitled Product"),
        "architecture_overview": stage5_judgment.get("architecture_overview", {}),
        "tech_stack": stage5_judgment.get("tech_stack", {}),
        "system_design": stage5_judgment.get("system_design", []),
        "api_contracts": stage5_judgment.get("api_contracts", []),
        "database_schema": stage5_judgment.get("database_schema", {}),
        "deployment_architecture": stage5_judgment.get("deployment_architecture", {}),
        "security_considerations": stage5_judgment.get("security_considerations", {}),
        "scalability_plan": stage5_judgment.get("scalability_plan", {}),
        "development_phases": stage5_judgment.get("development_phases", []),
        "estimated_effort_hours": stage5_judgment.get("estimated_effort_hours", 0),
    }
    
    # Validate against schema
    validate_tech_spec_schema(tech_spec)
    
    # Write output
    output_path = pid_path / "5_tech_spec.json"
    with open(output_path, "w") as f:
        json.dump(tech_spec, f, indent=2)
    
    print(f"✅ Tech Spec written to {output_path}")
    return tech_spec


def validate_tech_spec_schema(spec: dict):
    """
    Minimal validation of required fields.
    """
    required_fields = [
        "pipeline_id", "product_title", "architecture_overview",
        "tech_stack", "system_design", "api_contracts",
        "database_schema", "deployment_architecture",
        "security_considerations", "scalability_plan", "development_phases"
    ]
    
    for field in required_fields:
        if field not in spec or not spec[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate architecture overview
    arch = spec.get("architecture_overview", {})
    if not arch.get("diagram_description"):
        raise ValueError("architecture_overview must have diagram_description")
    
    # Validate API contracts
    if len(spec.get("api_contracts", [])) < 2:
        raise ValueError("Must define at least 2 API contracts")
    
    # Validate database schema
    db = spec.get("database_schema", {})
    if not db.get("tables") or len(db["tables"]) < 1:
        raise ValueError("database_schema must define at least 1 table")
    
    # Validate development phases
    if len(spec.get("development_phases", [])) < 2:
        raise ValueError("Must define at least 2 development phases")
    
    print("✅ Tech Spec schema validation passed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 helpers/build_tech_spec.py <pipeline_id>")
        print("Example: python3 helpers/build_tech_spec.py pipe_2026-06-15_001")
        sys.exit(1)
    
    pid = sys.argv[1]
    spec = build_tech_spec(pid)
    print(f"Tech Spec generated for {pid}")
