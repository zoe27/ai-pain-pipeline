"""Stage 1 assembler: combine filtered source posts + Claude judgments into PainPointBatch.

Inputs (read from runs/{pipeline_id}/):
    - _raw/top50.json            normalized post records (source, title, selftext, ups, num_comments, permalink)
    - _judgments/stage1.json     ordered list of {sentiment, keywords} matching top50.json by index

Output:
    - 1_pain_points.json         valid PainPointBatch per contracts/pain_point.schema.json

Usage:
    python3 helpers/build_pain_batch.py <pipeline_id>
    python3 helpers/build_pain_batch.py pipe_2026-05-20_001
"""
import json
import uuid
import datetime
import pathlib
import sys
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "pain_point.schema.json"
KW_RE = re.compile(r"^[a-z0-9][a-z0-9 +#.-]*$")
SENTIMENT_ENUM = {"negative", "positive", "neutral", "mixed"}

# Deterministic UUID v5 namespace — same permalink always produces same id.
# This makes stage 1 idempotent so stage 2 judgments don't break on rerun.
PAIN_NS = uuid.uuid5(uuid.NAMESPACE_URL, "ai-pipeline-arch:pain-radar")
VALID_SOURCES = {"reddit", "hackernews", "github_issues", "producthunt"}


def post_source_url(post: dict) -> str:
    source = post.get("source", "reddit")
    if source == "hackernews":
        oid = post.get("object_id") or post["permalink"].split("id=")[-1]
        return f"https://news.ycombinator.com/item?id={oid}"
    if source == "reddit":
        return f"https://reddit.com{post['permalink']}"
    if "source_url" in post:
        return post["source_url"]
    raise ValueError(f"cannot build source_url for source={source!r}")


def post_stable_id(post: dict) -> str:
    source = post.get("source", "reddit")
    if source == "hackernews":
        return f"hackernews:{post.get('object_id') or post['permalink']}"
    if source == "github_issues":
        repo = post.get("repo") or post.get("source_label", "")
        oid = post.get("object_id") or ""
        return f"github_issues:{repo}#{oid}"
    if source == "producthunt":
        return f"producthunt:{post.get('object_id', '')}"
    if source == "reddit":
        return f"reddit:{post.get('object_id') or post['permalink']}"
    return f"{source}:{post.get('permalink', post.get('object_id', ''))}"


def build(pipeline_id: str, source_file: str = "_raw/top50.json") -> dict:
    run_dir = ROOT / "runs" / pipeline_id
    posts_path = run_dir / source_file
    judg_path = run_dir / "_judgments" / "stage1.json"
    out_path = run_dir / "1_pain_points.json"

    if not posts_path.exists():
        raise FileNotFoundError(f"missing input: {posts_path}")
    if not judg_path.exists():
        raise FileNotFoundError(f"missing judgments: {judg_path}")

    posts = json.loads(posts_path.read_text())
    judgments = json.loads(judg_path.read_text())

    if len(posts) != len(judgments):
        raise ValueError(f"length mismatch: posts={len(posts)} judgments={len(judgments)}")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    pain_points = []
    for post, j in zip(posts, judgments):
        source = post.get("source", "reddit")
        if source not in VALID_SOURCES:
            raise ValueError(f"invalid source {source!r}")
        if j["sentiment"] not in SENTIMENT_ENUM:
            raise ValueError(f"invalid sentiment {j['sentiment']!r}")
        for kw in j["keywords"]:
            if not KW_RE.match(kw):
                raise ValueError(f"invalid keyword {kw!r}")

        pain_points.append({
            "id": str(uuid.uuid5(PAIN_NS, post_stable_id(post))),
            "source": source,
            "source_url": post_source_url(post),
            "title": post["title"],
            "raw_content": post.get("selftext", ""),
            "signals": {
                "upvotes": int(post["ups"]),
                "comments_count": int(post["num_comments"]),
                "sentiment": j["sentiment"],
            },
            "extracted_keywords": j["keywords"],
            "extracted_at": now,
        })

    batch = {
        "pipeline_id": pipeline_id,
        "generated_at": now,
        "count": len(pain_points),
        "pain_points": pain_points,
    }

    out_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ wrote {out_path.relative_to(ROOT)} ({out_path.stat().st_size} bytes, {batch['count']} pain points)")

    # strict schema validation
    import jsonschema
    jsonschema.validate(batch, json.loads(SCHEMA_PATH.read_text()))
    print("✓ jsonschema validation passed")

    return batch


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    build(sys.argv[1])


if __name__ == "__main__":
    main()
