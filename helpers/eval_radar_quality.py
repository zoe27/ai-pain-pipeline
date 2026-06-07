"""Evaluate pain-radar fetch quality against a labeled benchmark or pipeline snapshot.

Metrics (see docs/radar_quality.md):
  - pain_recall: fraction of labeled pain_candidate posts still kept after filter
  - pain_precision: fraction of kept posts that are labeled pain_candidate
  - product_launch_leak_rate: fraction of kept posts labeled product_launch
  - kept_count: posts surviving filter

Usage:
    # Compare v0.4 (legacy) vs v0.5 (quality filter) on frozen benchmark
    python3 helpers/eval_radar_quality.py --benchmark benchmarks/radar_quality_pipe_2026-06-06_002.json

    # Eval a live pipeline top50 against same benchmark labels
    python3 helpers/eval_radar_quality.py --pipeline pipe_2026-06-06_002 --config configs/radar.example.yaml
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "helpers"))

from radar_common import (  # noqa: E402
    KIND_LAUNCH,
    KIND_PAIN,
    filter_posts,
    filter_posts_legacy,
    load_yaml,
)


def post_key(post: dict) -> str:
    return str(post.get("object_id", post.get("permalink", "")))


def simulate_filter(
    posts: list[dict],
    *,
    config: dict,
    legacy: bool,
    min_score: int = 10,
    keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[dict]:
    keywords = keywords or []
    exclude_keywords = exclude_keywords or []
    if legacy:
        return filter_posts_legacy(
            posts,
            min_score=min_score,
            keywords=keywords,
            exclude_keywords=exclude_keywords,
        )
    return filter_posts(
        posts,
        min_score=min_score,
        keywords=keywords,
        exclude_keywords=exclude_keywords,
        config=config,
    )


def compute_metrics(
    kept: list[dict],
    labels: dict[str, str],
) -> dict:
    pain_ids = {k for k, v in labels.items() if v == KIND_PAIN}
    launch_ids = {k for k, v in labels.items() if v == KIND_LAUNCH}

    kept_keys = [post_key(p) for p in kept]
    kept_pain = [k for k in kept_keys if labels.get(k) == KIND_PAIN]
    kept_launch = [k for k in kept_keys if labels.get(k) == KIND_LAUNCH]

    n_kept = len(kept_keys)
    n_pain = len(pain_ids)
    pain_recall = len(kept_pain) / n_pain if n_pain else 1.0
    pain_precision = len(kept_pain) / n_kept if n_kept else 0.0
    launch_leak = len(kept_launch) / n_kept if n_kept else 0.0

    return {
        "kept_count": n_kept,
        "kept_pain_count": len(kept_pain),
        "kept_launch_count": len(kept_launch),
        "labeled_pain_count": n_pain,
        "pain_recall": round(pain_recall, 4),
        "pain_precision": round(pain_precision, 4),
        "product_launch_leak_rate": round(launch_leak, 4),
        "kept_ids": kept_keys,
        "missed_pain_ids": sorted(pain_ids - set(kept_pain)),
        "leaked_launch_ids": sorted(set(kept_launch)),
    }


def check_pass(metrics: dict, criteria: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if metrics["pain_recall"] < criteria.get("pain_recall_min", 1.0):
        failures.append(
            f"pain_recall {metrics['pain_recall']:.2%} < {criteria['pain_recall_min']:.0%}"
        )
    if metrics["pain_precision"] < criteria.get("pain_precision_min", 0.75):
        failures.append(
            f"pain_precision {metrics['pain_precision']:.2%} < {criteria['pain_precision_min']:.0%}"
        )
    if metrics["product_launch_leak_rate"] > criteria.get("product_launch_leak_max", 0.0):
        failures.append(
            f"product_launch_leak_rate {metrics['product_launch_leak_rate']:.2%} "
            f"> {criteria['product_launch_leak_max']:.0%}"
        )
    if metrics["kept_count"] < criteria.get("min_kept", 1):
        failures.append(
            f"kept_count {metrics['kept_count']} < {criteria['min_kept']}"
        )
    return len(failures) == 0, failures


def load_benchmark(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def filter_kwargs_from_config(config: dict) -> dict:
    flt = config.get("filters") or {}
    hn = next(
        (s for s in (config.get("sources") or []) if s.get("type") == "hackernews"),
        {},
    )
    from radar_common import effective_keywords, global_filters

    return {
        "min_score": int(hn.get("min_points", 10)),
        "keywords": effective_keywords(hn.get("keywords") or [], config),
        "exclude_keywords": global_filters(config)["exclude_keywords"],
    }


def print_report(name: str, metrics: dict, passed: bool | None, failures: list[str]) -> None:
    print(f"\n## {name}")
    print(f"- kept: {metrics['kept_count']} posts")
    print(f"- pain_recall: {metrics['pain_recall']:.1%} ({metrics['kept_pain_count']}/{metrics['labeled_pain_count']} pain kept)")
    print(f"- pain_precision: {metrics['pain_precision']:.1%}")
    print(f"- product_launch_leak_rate: {metrics['product_launch_leak_rate']:.1%}")
    if metrics["missed_pain_ids"]:
        print(f"- missed pain: {metrics['missed_pain_ids']}")
    if metrics["leaked_launch_ids"]:
        print(f"- leaked launches: {metrics['leaked_launch_ids']}")
    if passed is not None:
        print(f"- PASS: {'yes' if passed else 'no'}")
        for f in failures:
            print(f"  - {f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=pathlib.Path, help="Labeled benchmark JSON")
    parser.add_argument("--pipeline", help="Pipeline id to eval _raw/top50.json")
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=ROOT / "configs" / "radar.example.yaml",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="Write JSON report (e.g. runs/pid/_eval/radar_quality.json)",
    )
    args = parser.parse_args()

    if not args.benchmark and not args.pipeline:
        parser.error("Provide --benchmark and/or --pipeline")

    config = load_yaml(args.config)
    fk = filter_kwargs_from_config(config)
    criteria = {
        "pain_recall_min": 1.0,
        "pain_precision_min": 0.75,
        "product_launch_leak_max": 0.0,
        "min_kept": 3,
    }
    posts: list[dict] = []
    labels: dict[str, str] = {}

    if args.benchmark:
        bench = load_benchmark(args.benchmark)
        posts = bench["posts"]
        labels = bench["labels"]
        criteria = bench.get("success_criteria", criteria)
        bench_id = bench.get("id", args.benchmark.stem)
        if bench.get("filter"):
            fk = {**fk, **bench["filter"]}
    elif args.pipeline:
        top50 = ROOT / "runs" / args.pipeline / "_raw" / "top50.json"
        if not top50.is_file():
            raise SystemExit(f"Missing {top50}")
        posts = json.loads(top50.read_text())
        bench_path = ROOT / "benchmarks" / f"radar_quality_{args.pipeline}.json"
        if bench_path.is_file():
            bench = load_benchmark(bench_path)
            labels = bench["labels"]
            criteria = bench.get("success_criteria", criteria)
        bench_id = args.pipeline

    legacy_metrics = compute_metrics(
        simulate_filter(posts, config=config, legacy=True, **fk),
        labels,
    )
    quality_metrics = compute_metrics(
        simulate_filter(posts, config=config, legacy=False, **fk),
        labels,
    )

    legacy_pass, legacy_fail = check_pass(legacy_metrics, criteria)
    quality_pass, quality_fail = check_pass(quality_metrics, criteria)

    print(f"# Radar quality eval — {bench_id}")
    print(f"Config: {args.config.relative_to(ROOT)}")
    print_report("v0.4 legacy (no quality filter)", legacy_metrics, legacy_pass, legacy_fail)
    print_report("v0.6 quality filter", quality_metrics, quality_pass, quality_fail)

    delta_precision = quality_metrics["pain_precision"] - legacy_metrics["pain_precision"]
    delta_leak = legacy_metrics["product_launch_leak_rate"] - quality_metrics["product_launch_leak_rate"]
    print("\n## Delta (v0.6 − v0.4)")
    print(f"- pain_precision: {delta_precision:+.1%}")
    print(f"- launch leak reduction: {delta_leak:+.1%}")
    print(f"- kept_count: {quality_metrics['kept_count'] - legacy_metrics['kept_count']:+d}")

    report = {
        "benchmark_id": bench_id,
        "config": str(args.config.relative_to(ROOT)),
        "success_criteria": criteria,
        "legacy": {**legacy_metrics, "pass": legacy_pass},
        "quality": {**quality_metrics, "pass": quality_pass},
        "delta": {
            "pain_precision": round(delta_precision, 4),
            "launch_leak_reduction": round(delta_leak, 4),
            "kept_count": quality_metrics["kept_count"] - legacy_metrics["kept_count"],
        },
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(f"\n→ wrote {args.output}")

    if not quality_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
