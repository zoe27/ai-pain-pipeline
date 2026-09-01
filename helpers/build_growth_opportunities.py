#!/usr/bin/env python3
"""
Build Growth Opportunities (G3)

Reads demand clusters, applies AI opportunity analysis,
and assembles actionable growth recommendations.

Usage:
    python3 helpers/build_growth_opportunities.py growth_zhihu_2026-09-01_001
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

import jsonschema


def load_schema(schema_name: str) -> Dict:
    """Load JSON schema"""
    schema_path = Path(f"contracts/{schema_name}.schema.json")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_demand_clusters(growth_id: str) -> Dict:
    """Load G2 demand clusters"""
    clusters_path = Path(f"runs/{growth_id}/g2_demand_clusters.json")
    
    if not clusters_path.exists():
        raise FileNotFoundError(
            f"Demand clusters not found: {clusters_path}\n"
            f"Run 'python3 helpers/build_demand_clusters.py {growth_id}' first"
        )
    
    with open(clusters_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_product_context(growth_id: str) -> Dict:
    """Load product context"""
    context_path = Path(f"runs/{growth_id}/product_context.json")
    
    if not context_path.exists():
        raise FileNotFoundError(f"Product context not found: {context_path}")
    
    with open(context_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_judgment(growth_id: str) -> Dict:
    """Load G3 opportunity judgment from AI"""
    judgment_path = Path(f"runs/{growth_id}/_judgments/g3.json")
    
    if not judgment_path.exists():
        raise FileNotFoundError(
            f"Judgment file not found: {judgment_path}\n\n"
            f"Please create it by running the growth-opportunity skill.\n"
            f"The AI should analyze clusters and generate growth opportunities."
        )
    
    with open(judgment_path, 'r', encoding='utf-8') as f:
        judgment = json.load(f)
    
    # Validate judgment structure
    if 'zhihu_opportunities' not in judgment:
        raise ValueError("Judgment must contain 'zhihu_opportunities' field")
    
    return judgment


def assemble_growth_opportunities(
    growth_id: str,
    clusters_data: Dict,
    product_ctx: Dict,
    judgment: Dict
) -> Dict:
    """
    Assemble growth opportunities from clusters + AI judgment
    """
    # Use AI judgment as base
    opportunities = judgment['zhihu_opportunities']
    
    # Calculate summary stats
    total_clusters = len(clusters_data['clusters'])
    total_zhihu_questions = sum(len(opp.get('top_questions', [])) for opp in opportunities)
    seo_opportunities_count = sum(len(opp.get('seo_opportunities', [])) for opp in opportunities)
    
    # Get top priority clusters
    top_priority = judgment.get('summary', {}).get('top_priority', [])
    if not top_priority:
        # Fallback: top 3 by demand score
        sorted_opps = sorted(opportunities, key=lambda o: o.get('demand_score', 0), reverse=True)
        top_priority = [o['cluster_id'] for o in sorted_opps[:3]]
    
    # Calculate estimated reach
    estimated_reach = sum(
        opp.get('total_view_count', 0) for opp in opportunities
    )
    
    # Assemble output
    output = {
        'growth_id': growth_id,
        'created_at': datetime.now().isoformat(),
        'product_title': product_ctx['product_info']['name'],
        'zhihu_opportunities': opportunities,
        'summary': {
            'total_clusters': total_clusters,
            'total_zhihu_questions': total_zhihu_questions,
            'seo_opportunities_count': seo_opportunities_count,
            'top_priority': top_priority,
            'estimated_reach': estimated_reach,
        }
    }
    
    return output


def main():
    parser = argparse.ArgumentParser(description='Build growth opportunities (G3)')
    parser.add_argument('growth_id', help='Growth ID (e.g., growth_zhihu_2026-09-01_001)')
    args = parser.parse_args()
    
    # Load demand clusters
    print(f"Loading demand clusters for {args.growth_id}...")
    try:
        clusters_data = load_demand_clusters(args.growth_id)
        print(f"  Found {len(clusters_data['clusters'])} clusters")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return
    
    # Load product context
    print(f"Loading product context...")
    try:
        product_ctx = load_product_context(args.growth_id)
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return
    
    # Load AI judgment
    print(f"Loading AI opportunity analysis from _judgments/g3.json...")
    try:
        judgment = load_judgment(args.growth_id)
        print(f"  AI identified {len(judgment['zhihu_opportunities'])} opportunity clusters")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nTo create the judgment file:")
        print("1. Use Claude with the growth-opportunity skill")
        print(f"2. Provide clusters from: runs/{args.growth_id}/g2_demand_clusters.json")
        print(f"3. Provide product from: runs/{args.growth_id}/product_context.json")
        print(f"4. Save the AI output to: runs/{args.growth_id}/_judgments/g3.json")
        return
    
    # Assemble growth opportunities
    print("Assembling growth opportunities...")
    growth_opps = assemble_growth_opportunities(
        args.growth_id,
        clusters_data,
        product_ctx,
        judgment
    )
    
    # Validate against schema
    print("Validating against schema...")
    schema = load_schema('growth_opportunity')
    try:
        jsonschema.validate(instance=growth_opps, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed:")
        print(f"  {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return
    
    # Save output
    run_dir = Path(f"runs/{args.growth_id}")
    output_path = run_dir / "g3_growth_opportunities.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(growth_opps, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Growth opportunities created: {output_path}")
    print(f"\nSummary:")
    print(f"  Total clusters: {growth_opps['summary']['total_clusters']}")
    print(f"  Zhihu questions to answer: {growth_opps['summary']['total_zhihu_questions']}")
    print(f"  SEO page opportunities: {growth_opps['summary']['seo_opportunities_count']}")
    print(f"  Estimated reach: {growth_opps['summary']['estimated_reach']:,} views")
    print(f"\nTop priority clusters:")
    for cluster_id in growth_opps['summary']['top_priority'][:3]:
        for opp in growth_opps['zhihu_opportunities']:
            if opp['cluster_id'] == cluster_id:
                print(f"  • {opp['cluster_label']} (Score: {opp['demand_score']})")
                break
    
    print(f"\nNext: python3 helpers/build_zhihu_answers.py {args.growth_id}")


if __name__ == '__main__':
    main()
