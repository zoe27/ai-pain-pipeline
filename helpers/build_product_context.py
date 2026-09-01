#!/usr/bin/env python3
"""
Build Product Context (G0)

Creates product_context.json from user input and AI judgment.

Usage:
    python3 helpers/build_product_context.py growth_zhihu_2026-09-01_001
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import jsonschema


def load_schema(schema_name: str) -> Dict:
    """Load JSON schema"""
    schema_path = Path(f"contracts/{schema_name}.schema.json")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_judgment(judgment: Dict):
    """Validate judgment structure"""
    required_fields = ['product_info', 'scan_config']
    for field in required_fields:
        if field not in judgment:
            raise ValueError(f"Missing required field in judgment: {field}")
    
    # Validate product_info
    product_info = judgment['product_info']
    required_product_fields = ['name', 'description', 'core_capabilities', 'target_keywords']
    for field in required_product_fields:
        if field not in product_info:
            raise ValueError(f"Missing required field in product_info: {field}")
    
    # Validate keywords
    keywords = product_info['target_keywords']
    if not isinstance(keywords, list) or len(keywords) < 3:
        raise ValueError(f"target_keywords must be a list with at least 3 items, got: {keywords}")


def load_judgment(growth_id: str) -> Dict:
    """Load judgment from _judgments/g0.json"""
    judgment_path = Path(f"runs/{growth_id}/_judgments/g0.json")
    
    if not judgment_path.exists():
        raise FileNotFoundError(
            f"Judgment file not found: {judgment_path}\n\n"
            f"Please create it first by running the product-focus skill.\n"
            f"The file should contain output from the AI analyzing your product."
        )
    
    with open(judgment_path, 'r', encoding='utf-8') as f:
        judgment = json.load(f)
    
    validate_judgment(judgment)
    return judgment


def assemble_product_context(growth_id: str, judgment: Dict, product_input: Dict) -> Dict:
    """
    Assemble product_context.json from judgment
    
    This is deterministic assembly - no AI calls here
    """
    return {
        'growth_id': growth_id,
        'created_at': datetime.now().isoformat(),
        'product_input': product_input,
        'product_info': judgment['product_info'],
        'scan_config': judgment['scan_config'],
        'connected_accounts': {},  # Phase 2
        'linked_pipeline_id': None,
    }


def main():
    parser = argparse.ArgumentParser(description='Build product context (G0)')
    parser.add_argument('growth_id', help='Growth ID (e.g., growth_zhihu_2026-09-01_001)')
    parser.add_argument('--product-url', help='Product website URL')
    parser.add_argument('--github-repo', help='GitHub repository URL')
    parser.add_argument('--description', help='Manual product description')
    args = parser.parse_args()
    
    # Create run directory
    run_dir = Path(f"runs/{args.growth_id}")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "_judgments").mkdir(exist_ok=True)
    (run_dir / "_raw").mkdir(exist_ok=True)
    
    # Determine product input type
    product_input = {}
    if args.product_url:
        product_input = {
            'type': 'url',
            'value': args.product_url,
            'github_repo': None,
            'manual_description': None
        }
    elif args.github_repo:
        product_input = {
            'type': 'github',
            'value': args.github_repo,
            'github_repo': args.github_repo,
            'manual_description': None
        }
    elif args.description:
        product_input = {
            'type': 'manual',
            'value': args.description,
            'github_repo': None,
            'manual_description': args.description
        }
    else:
        print("No product input provided. Please use one of:")
        print("  --product-url https://example.com")
        print("  --github-repo https://github.com/user/repo")
        print("  --description 'Product description...'")
        print("\nThen, create _judgments/g0.json using the product-focus skill.")
        return
    
    # Load judgment
    print(f"Loading judgment from runs/{args.growth_id}/_judgments/g0.json...")
    try:
        judgment = load_judgment(args.growth_id)
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nTo create the judgment file:")
        print("1. Use Claude with the product-focus skill")
        print(f"2. Provide product input: {product_input['value']}")
        print(f"3. Save the output to: runs/{args.growth_id}/_judgments/g0.json")
        return
    
    # Assemble product context
    print("Assembling product context...")
    product_context = assemble_product_context(args.growth_id, judgment, product_input)
    
    # Validate against schema
    print("Validating against schema...")
    schema = load_schema('product_context')
    try:
        jsonschema.validate(instance=product_context, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed:")
        print(f"  {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return
    
    # Save output
    output_path = run_dir / "product_context.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(product_context, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Product context created: {output_path}")
    print(f"\nProduct: {product_context['product_info']['name']}")
    print(f"Keywords: {len(product_context['product_info']['target_keywords'])}")
    print(f"Competitors: {len(product_context['product_info'].get('competitors', []))}")
    print(f"\nNext: python3 helpers/fetch_zhihu.py {args.growth_id}")


if __name__ == '__main__':
    main()
