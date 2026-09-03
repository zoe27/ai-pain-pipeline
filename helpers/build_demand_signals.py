#!/usr/bin/env python3
"""
Build Demand Signals (G1)

Reads raw fetched data, applies AI judgment (from _judgments/g1.json),
and assembles structured demand signals.

Usage:
    python3 helpers/build_demand_signals.py growth_zhihu_2026-09-01_001
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import jsonschema


def load_schema(schema_name: str) -> Dict:
    """Load JSON schema"""
    schema_path = Path(f"contracts/{schema_name}.schema.json")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_raw_data(growth_id: str) -> Dict:
    """Load raw fetched data"""
    raw_path = Path(f"runs/{growth_id}/_raw/raw_zhihu_questions.json")
    
    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw data not found: {raw_path}\n"
            f"Run 'python3 helpers/fetch_zhihu.py {growth_id}' first"
        )
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_judgment(growth_id: str) -> Dict:
    """Load G1 judgment from AI"""
    judgment_path = Path(f"runs/{growth_id}/_judgments/g1.json")
    
    if not judgment_path.exists():
        raise FileNotFoundError(
            f"Judgment file not found: {judgment_path}\n\n"
            f"Please create it by running the demand-radar skill.\n"
            f"The AI should analyze the raw data and output intent-filtered signals."
        )
    
    with open(judgment_path, 'r', encoding='utf-8') as f:
        judgment = json.load(f)
    
    # Validate judgment structure
    if 'filtered_signals' not in judgment:
        raise ValueError("Judgment must contain 'filtered_signals' field")
    
    return judgment


def assemble_demand_signals(growth_id: str, raw_data: Dict, judgment: Dict) -> Dict:
    """
    Assemble demand signals from raw data + AI judgment
    
    This is deterministic assembly - no AI calls here
    """
    filtered_signals = judgment['filtered_signals']
    raw_questions = raw_data.get('questions', [])
    
    # Build a lookup map: question_id -> raw question data
    raw_map = {q['question_id']: q for q in raw_questions}
    
    # Assemble complete signals
    signals = []
    for filtered in filtered_signals:
        question_id = filtered.get('question_id')
        platform = filtered.get('platform', 'zhihu')
        
        # Get raw data for this question
        raw_q = raw_map.get(question_id, {})
        
        # Construct signal_id
        signal_id = f"{platform}_q_{question_id}"
        
        # Assemble complete signal
        signal = {
            'signal_id': signal_id,
            'platform': platform,
            'content_type': 'question',
            'platform_id': question_id,
            'url': raw_q.get('url', f"https://www.zhihu.com/question/{question_id}"),
            'title': raw_q.get('title', ''),
            'detail': raw_q.get('detail', ''),
            'created_at': raw_q.get('created_at'),
            'author': raw_q.get('author', 'Unknown'),
            'engagement': {
                'follower_count': raw_q.get('follower_count', 0),
                'answer_count': raw_q.get('answer_count', 0),
                'view_count': raw_q.get('view_count', 0),
                'upvote_count': 0,  # Not applicable for Zhihu questions
                'comment_count': raw_q.get('answer_count', 0),  # Use answer_count
            },
            'latest_activity': raw_q.get('latest_activity'),
            'topics': raw_q.get('topics', []),
            'intent_detected': filtered.get('intent_detected', False),
            'intent_type': filtered.get('intent_type'),
            'relevance_score': filtered.get('relevance_score', 0),
            'commercial_intent': filtered.get('commercial_intent', 'low'),
            'keywords_matched': filtered.get('keywords_matched', []),
            'reasoning': filtered.get('reasoning', ''),
            'language': 'zh',  # Zhihu is Chinese
        }
        if raw_q.get('existing_answer'):
            signal['existing_answer'] = raw_q['existing_answer']
        
        signals.append(signal)
    
    # Count by platform
    by_platform = {}
    already_answered = 0
    for sig in signals:
        platform = sig['platform']
        by_platform[platform] = by_platform.get(platform, 0) + 1
        if (sig.get('existing_answer') or {}).get('answered'):
            already_answered += 1
    
    # Assemble output
    output = {
        'growth_id': growth_id,
        'created_at': datetime.now().isoformat(),
        'signals': signals,
        'metadata': {
            'raw_count': len(raw_questions),
            'filtered_count': len(signals),
            'by_platform': by_platform,
            'keywords_searched': raw_data.get('keywords_searched', []),
            'date_range': raw_data.get('date_range', '30_days'),
            'platforms_used': list(set(s['platform'] for s in signals)),
            'already_answered_count': already_answered,
        }
    }
    
    return output


def main():
    parser = argparse.ArgumentParser(description='Build demand signals (G1)')
    parser.add_argument('growth_id', help='Growth ID (e.g., growth_zhihu_2026-09-01_001)')
    args = parser.parse_args()
    
    # Load raw data
    print(f"Loading raw data for {args.growth_id}...")
    try:
        raw_data = load_raw_data(args.growth_id)
        print(f"  Found {len(raw_data.get('questions', []))} raw questions")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return
    
    # Load AI judgment
    print(f"Loading AI judgment from _judgments/g1.json...")
    try:
        judgment = load_judgment(args.growth_id)
        print(f"  AI filtered to {len(judgment['filtered_signals'])} signals with intent")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nTo create the judgment file:")
        print("1. Use Claude with the demand-radar skill")
        print(f"2. Provide the raw data from: runs/{args.growth_id}/_raw/raw_zhihu_questions.json")
        print(f"3. Save the AI output to: runs/{args.growth_id}/_judgments/g1.json")
        return
    
    # Assemble demand signals
    print("Assembling demand signals...")
    demand_signals = assemble_demand_signals(args.growth_id, raw_data, judgment)
    
    # Validate against schema
    print("Validating against schema...")
    schema = load_schema('demand_signal')
    try:
        jsonschema.validate(instance=demand_signals, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed:")
        print(f"  {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return
    
    # Save output
    run_dir = Path(f"runs/{args.growth_id}")
    output_path = run_dir / "g1_demand_signals.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(demand_signals, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Demand signals created: {output_path}")
    print(f"\nSummary:")
    print(f"  Raw questions: {demand_signals['metadata']['raw_count']}")
    print(f"  Filtered signals: {demand_signals['metadata']['filtered_count']}")
    print(f"  Filter rate: {demand_signals['metadata']['filtered_count'] / max(demand_signals['metadata']['raw_count'], 1) * 100:.1f}%")
    print(f"\nNext: python3 helpers/build_demand_clusters.py {args.growth_id}")


if __name__ == '__main__':
    main()
