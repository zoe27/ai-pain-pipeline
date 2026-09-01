#!/usr/bin/env python3
"""
Build Zhihu Answer Drafts (G4)

Reads growth opportunities, applies AI answer generation,
and assembles publication-ready answer drafts.

Usage:
    python3 helpers/build_zhihu_answers.py growth_zhihu_2026-09-01_001
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import jsonschema


def load_schema(schema_name: str) -> Dict:
    """Load JSON schema"""
    schema_path = Path(f"contracts/{schema_name}.schema.json")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_growth_opportunities(growth_id: str) -> Dict:
    """Load G3 growth opportunities"""
    opps_path = Path(f"runs/{growth_id}/g3_growth_opportunities.json")
    
    if not opps_path.exists():
        raise FileNotFoundError(
            f"Growth opportunities not found: {opps_path}\n"
            f"Run 'python3 helpers/build_growth_opportunities.py {growth_id}' first"
        )
    
    with open(opps_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_product_context(growth_id: str) -> Dict:
    """Load product context"""
    context_path = Path(f"runs/{growth_id}/product_context.json")
    
    if not context_path.exists():
        raise FileNotFoundError(f"Product context not found: {context_path}")
    
    with open(context_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_judgment(growth_id: str) -> Dict:
    """Load G4 answer generation judgment from AI"""
    judgment_path = Path(f"runs/{growth_id}/_judgments/g4.json")
    
    if not judgment_path.exists():
        raise FileNotFoundError(
            f"Judgment file not found: {judgment_path}\n\n"
            f"Please create it by running the zhihu-answer-writer skill.\n"
            f"The AI should generate answer drafts for top questions."
        )
    
    with open(judgment_path, 'r', encoding='utf-8') as f:
        judgment = json.load(f)
    
    # Validate judgment structure
    if 'answers' not in judgment:
        raise ValueError("Judgment must contain 'answers' field")
    
    return judgment


def load_demand_signals(growth_id: str) -> Dict:
    """Load G1 demand signals (optional, for existing_answer passthrough)."""
    path = Path(f"runs/{growth_id}/g1_demand_signals.json")
    if not path.exists():
        return {'signals': []}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assemble_zhihu_answers(
    growth_id: str,
    opportunities: Dict,
    product_ctx: Dict,
    judgment: Dict,
    signals_data: Optional[Dict] = None,
) -> Dict:
    """
    Assemble Zhihu answer drafts from opportunities + AI judgment
    """
    ai_answers = judgment['answers']
    
    # Enrich with source data
    enriched_answers = []
    
    # Build question lookup
    question_map = {}
    for opp in opportunities['zhihu_opportunities']:
        cluster_id = opp['cluster_id']
        for q in opp.get('top_questions', []):
            question_map[q['question_id']] = {
                'cluster_id': cluster_id,
                'question_data': q,
            }

    signal_map = {}
    if signals_data:
        signal_map = {s['platform_id']: s for s in signals_data.get('signals', [])}
    
    for answer in ai_answers:
        question_id = answer.get('question_id')
        q_info = question_map.get(question_id, {})
        q_data = q_info.get('question_data', {})
        sig = signal_map.get(question_id, {})
        raw_signals = q_data.get('signals', {})
        source_metadata = {
            k: raw_signals[k]
            for k in ('view_count', 'follower_count', 'answer_count', 'created_at', 'latest_activity')
            if k in raw_signals
        }
        
        enriched = {
            'answer_id': answer.get('answer_id', f"ans_{len(enriched_answers) + 1:03d}"),
            'cluster_id': answer.get('cluster_id') or q_info.get('cluster_id', 'unknown'),
            'platform': 'zhihu',
            'question_id': question_id,
            'question_title': answer.get('question_title') or q_data.get('title', ''),
            'question_url': answer.get('question_url') or q_data.get('url', ''),
            'question_detail': answer.get('question_detail', ''),
            'source_metadata': source_metadata,
            'generated_answer': answer.get('generated_answer', {}),
            'opportunity_score': answer.get('opportunity_score', 0),
            'signals': answer.get('signals', {}),
            'metadata': answer.get('metadata', {}),
            'publish_status': 'pending',
            'published_at': None,
            'published_url': None,
        }
        existing = answer.get('existing_answer') or sig.get('existing_answer')
        if existing:
            enriched['existing_answer'] = existing
        
        enriched_answers.append(enriched)
    
    # Calculate metadata
    by_priority = {'urgent': 0, 'high': 0, 'medium': 0, 'low': 0}
    by_cluster = {}
    word_counts = []
    total_reach = 0
    
    for answer in enriched_answers:
        # Priority distribution
        priority = answer.get('metadata', {}).get('publish_recommendation', {}).get('priority', 'medium')
        by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # By cluster
        cluster_id = answer['cluster_id']
        by_cluster[cluster_id] = by_cluster.get(cluster_id, 0) + 1
        
        # Word count
        word_count = answer.get('generated_answer', {}).get('word_count', 0)
        if word_count:
            word_counts.append(word_count)
        
        # Reach
        view_count = answer.get('source_metadata', {}).get('view_count', 0)
        if view_count:
            total_reach += view_count
    
    # Assemble output
    output = {
        'growth_id': growth_id,
        'created_at': datetime.now().isoformat(),
        'product_title': product_ctx['product_info']['name'],
        'zhihu_answers': enriched_answers,
        'metadata': {
            'total_answers': len(enriched_answers),
            'by_priority': by_priority,
            'by_cluster': by_cluster,
            'estimated_total_reach': total_reach,
            'avg_word_count': sum(word_counts) // max(len(word_counts), 1) if word_counts else 0,
            'generation_notes': judgment.get('notes', ''),
        }
    }
    
    return output


def main():
    parser = argparse.ArgumentParser(description='Build Zhihu answer drafts (G4)')
    parser.add_argument('growth_id', help='Growth ID (e.g., growth_zhihu_2026-09-01_001)')
    args = parser.parse_args()
    
    # Load growth opportunities
    print(f"Loading growth opportunities for {args.growth_id}...")
    try:
        opportunities = load_growth_opportunities(args.growth_id)
        print(f"  Found opportunities for {len(opportunities['zhihu_opportunities'])} clusters")
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
    print(f"Loading AI answer drafts from _judgments/g4.json...")
    try:
        judgment = load_judgment(args.growth_id)
        print(f"  AI generated {len(judgment['answers'])} answer drafts")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nTo create the judgment file:")
        print("1. Use Claude with the zhihu-answer-writer skill")
        print(f"2. Provide opportunities from: runs/{args.growth_id}/g3_growth_opportunities.json")
        print(f"3. Provide product from: runs/{args.growth_id}/product_context.json")
        print(f"4. Save the AI output to: runs/{args.growth_id}/_judgments/g4.json")
        return
    
    # Assemble answer drafts
    print("Assembling Zhihu answer drafts...")
    signals_data = load_demand_signals(args.growth_id)
    answer_drafts = assemble_zhihu_answers(
        args.growth_id,
        opportunities,
        product_ctx,
        judgment,
        signals_data,
    )
    
    # Validate against schema
    print("Validating against schema...")
    schema = load_schema('zhihu_answer_draft')
    try:
        jsonschema.validate(instance=answer_drafts, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed:")
        print(f"  {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return
    
    # Save output
    run_dir = Path(f"runs/{args.growth_id}")
    output_path = run_dir / "g4_zhihu_answers.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(answer_drafts, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Zhihu answer drafts created: {output_path}")
    print(f"\nSummary:")
    print(f"  Total answers: {answer_drafts['metadata']['total_answers']}")
    print(f"  By priority:")
    for priority in ['urgent', 'high', 'medium', 'low']:
        count = answer_drafts['metadata']['by_priority'].get(priority, 0)
        if count > 0:
            print(f"    • {priority}: {count}")
    print(f"  Avg word count: {answer_drafts['metadata']['avg_word_count']}")
    print(f"  Estimated reach: {answer_drafts['metadata']['estimated_total_reach']:,} views")
    
    print(f"\n✅ All done! Review answers and copy-paste to Zhihu.")
    print(f"\nNext: Generate digest for easy review")
    print(f"  python3 helpers/digest.py runs/{args.growth_id}/g4_zhihu_answers.json")


if __name__ == '__main__':
    main()
