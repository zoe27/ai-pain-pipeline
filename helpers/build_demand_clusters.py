#!/usr/bin/env python3
"""
Build Demand Clusters (G2)

Reads demand signals, applies AI clustering judgment,
and assembles structured demand clusters with scores.

Usage:
    python3 helpers/build_demand_clusters.py growth_zhihu_2026-09-01_001
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import jsonschema


def load_schema(schema_name: str) -> Dict:
    """Load JSON schema"""
    schema_path = Path(f"contracts/{schema_name}.schema.json")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_demand_signals(growth_id: str) -> Dict:
    """Load G1 demand signals"""
    signals_path = Path(f"runs/{growth_id}/g1_demand_signals.json")
    
    if not signals_path.exists():
        raise FileNotFoundError(
            f"Demand signals not found: {signals_path}\n"
            f"Run 'python3 helpers/build_demand_signals.py {growth_id}' first"
        )
    
    with open(signals_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_judgment(growth_id: str) -> Dict:
    """Load G2 clustering judgment from AI"""
    judgment_path = Path(f"runs/{growth_id}/_judgments/g2.json")
    
    if not judgment_path.exists():
        raise FileNotFoundError(
            f"Judgment file not found: {judgment_path}\n\n"
            f"Please create it by running the demand-cluster skill.\n"
            f"The AI should cluster signals and calculate demand scores."
        )
    
    with open(judgment_path, 'r', encoding='utf-8') as f:
        judgment = json.load(f)
    
    # Validate judgment structure
    if 'clusters' not in judgment:
        raise ValueError("Judgment must contain 'clusters' field")
    
    return judgment


def assemble_demand_clusters(growth_id: str, signals_data: Dict, judgment: Dict) -> Dict:
    """
    Assemble demand clusters from signals + AI judgment
    
    Enriches AI clusters with signal data
    """
    ai_clusters = judgment['clusters']
    signals = signals_data['signals']
    
    # Build signal lookup map
    signal_map = {s['platform_id']: s for s in signals}
    
    # Enrich clusters with signal details
    enriched_clusters = []
    for cluster in ai_clusters:
        question_ids = cluster.get('question_ids', [])
        
        # Calculate aggregate stats
        total_views = 0
        total_answers = 0
        follower_counts = []
        
        top_questions = []
        for qid in question_ids[:5]:  # Top 5
            sig = signal_map.get(qid)
            if sig:
                engagement = sig.get('engagement', {})
                view_count = engagement.get('view_count', 0)
                answer_count = engagement.get('answer_count', 0)
                follower_count = engagement.get('follower_count', 0)
                
                total_views += view_count
                total_answers += answer_count
                if follower_count:
                    follower_counts.append(follower_count)
                
                top_questions.append({
                    'question_id': qid,
                    'title': sig.get('title', ''),
                    'url': sig.get('url', ''),
                    'view_count': view_count,
                    'answer_count': answer_count,
                })
        
        # Assemble enriched cluster
        enriched = {
            'cluster_id': cluster['cluster_id'],
            'label': cluster['label'],
            'description': cluster.get('description', ''),
            'question_ids': question_ids,
            'question_count': len(question_ids),
            'demand_score': cluster.get('demand_score', 0),
            'score_breakdown': cluster.get('score_breakdown', {}),
            'total_view_count': total_views,
            'avg_answer_count': total_answers / max(len(question_ids), 1),
            'avg_follower_count': sum(follower_counts) / max(len(follower_counts), 1) if follower_counts else 0,
            'keywords': cluster.get('keywords', []),
            'trend': cluster.get('trend', 'unknown'),
            'top_questions': top_questions,
        }
        
        enriched_clusters.append(enriched)
    
    # Sort by demand_score
    enriched_clusters.sort(key=lambda c: c['demand_score'], reverse=True)
    
    # Assemble output
    output = {
        'growth_id': growth_id,
        'created_at': datetime.now().isoformat(),
        'clusters': enriched_clusters,
        'metadata': {
            'total_signals': len(signals),
            'total_clusters': len(enriched_clusters),
            'clustering_method': 'AI-based semantic clustering',
            'score_weights': judgment.get('clustering_summary', {}).get('score_weights', {
                'volume_weight': 0.25,
                'engagement_weight': 0.35,
                'intent_weight': 0.25,
                'freshness_weight': 0.15,
            }),
        }
    }
    
    return output


def main():
    parser = argparse.ArgumentParser(description='Build demand clusters (G2)')
    parser.add_argument('growth_id', help='Growth ID (e.g., growth_zhihu_2026-09-01_001)')
    args = parser.parse_args()
    
    # Load demand signals
    print(f"Loading demand signals for {args.growth_id}...")
    try:
        signals_data = load_demand_signals(args.growth_id)
        print(f"  Found {len(signals_data['signals'])} signals")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return
    
    # Load AI judgment
    print(f"Loading AI clustering judgment from _judgments/g2.json...")
    try:
        judgment = load_judgment(args.growth_id)
        print(f"  AI clustered into {len(judgment['clusters'])} demand clusters")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nTo create the judgment file:")
        print("1. Use Claude with the demand-cluster skill")
        print(f"2. Provide the signals from: runs/{args.growth_id}/g1_demand_signals.json")
        print(f"3. Save the AI output to: runs/{args.growth_id}/_judgments/g2.json")
        return
    
    # Assemble demand clusters
    print("Assembling demand clusters...")
    demand_clusters = assemble_demand_clusters(args.growth_id, signals_data, judgment)
    
    # Validate against schema
    print("Validating against schema...")
    schema = load_schema('demand_cluster')
    try:
        jsonschema.validate(instance=demand_clusters, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed:")
        print(f"  {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return
    
    # Save output
    run_dir = Path(f"runs/{args.growth_id}")
    output_path = run_dir / "g2_demand_clusters.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(demand_clusters, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Demand clusters created: {output_path}")
    print(f"\nTop 3 clusters by demand score:")
    for i, cluster in enumerate(demand_clusters['clusters'][:3], 1):
        print(f"  {i}. {cluster['label']} (Score: {cluster['demand_score']}, Questions: {cluster['question_count']})")
    
    print(f"\nNext: python3 helpers/build_growth_opportunities.py {args.growth_id}")


if __name__ == '__main__':
    main()
