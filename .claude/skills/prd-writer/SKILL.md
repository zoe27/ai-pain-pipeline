# PRD Writer Skill

> **Stage 4: Product Requirements Document**  
> Transforms an approved opportunity into a detailed, actionable PRD with user stories, feature breakdown, and success metrics.

## Mission

Write a comprehensive Product Requirements Document (PRD) that serves as the source of truth for Stage 5 (architecture design) and Stage 6 (development).

## Input

- `runs/{pid}/3_opportunity.json` — Opportunity + commercial_assessment + opportunity_score
- `runs/{pid}/3_opportunity.digest.zh.md` — Executive summary
- User decision: **GO** from decision point ①

## Output

- `runs/{pid}/_judgments/stage4.json` — Agent's PRD judgments (structured)
- `runs/{pid}/4_prd.json` — Full PRD (schema: [`contracts/prd.schema.json`](../../../contracts/prd.schema.json))
- `runs/{pid}/4_prd.md` — Human-readable PRD (Markdown)
- `runs/{pid}/4_prd.zh.md` — Chinese version (if i18n requested)

## Process

### Step 1: Read Context

1. Load `3_opportunity.json`
2. Review the opportunity_score, tier, and recommendation
3. Check `external_signals_summary` for market signals
4. Note `target_personas` and `market_size` (TAM/SAM/SOM)

### Step 2: Define Product Vision

1. Craft a concise product vision (1–3 sentences) that connects the pain point to the solution
2. Define north star metric (what does success look like?)
3. Identify the core value proposition vs competitors

Example:
```
Vision: "A PDF processing toolkit that intelligently detects 
rotated pages, normalizes Unicode, and repairs form fields 
with 99% accuracy — replacing expensive cloud services and 
unreliable open-source libraries."

North Star: "% of user documents processed without manual 
intervention reaching 98+ within 6 months."
```

### Step 3: Write User Stories

For each target persona from Stage 3:
- **User Story Format**: "As a [persona], I want to [action] so that [benefit]"
- **Acceptance Criteria**: 3–5 concrete, testable criteria per story
- **Priority**: Map to features (next step)

Example:
```json
{
  "persona": "Research Professor",
  "story": "As a research professor, I want to batch-process 500 scanned paper PDFs with automatic rotation and OCR so that I can digitize my lab archives in under 2 hours instead of manually rotating each page.",
  "acceptance": [
    "System detects and corrects rotated pages in < 100ms per page",
    "Unicode characters with diacritics (é, ñ, ü) render correctly in output",
    "Batch processing shows progress bar and ETA",
    "User can export results as searchable PDFs"
  ]
}
```

### Step 4: Feature Breakdown

For each major user story, define 5–15 core features:

- **Name**: Clear, user-centric name
- **Description**: What it does, not how
- **Priority**: P0 (must-have), P1 (should-have), P2 (nice-to-have), P3 (backlog)
- **Effort**: Estimated hours (discussed with architect in Stage 5)
- **Dependencies**: Which other features must be done first
- **Acceptance Criteria**: 1–5 per feature

Example:
```json
{
  "name": "Automatic Page Rotation Detection",
  "description": "Analyzes PDF page orientation and auto-corrects upside-down or sideways scans",
  "priority": "p0",
  "effort_hours": 40,
  "dependencies": [],
  "acceptance_criteria": [
    "Detects 180°, 90°, and 270° rotations",
    "Accuracy >= 99% on test set of 1000 diverse PDFs",
    "Processing time < 100ms per page on standard CPU",
    "Gracefully handles mixed-orientation documents"
  ]
}
```

### Step 5: Acceptance Criteria (Product Level)

Define 5–20 acceptance criteria for the **entire product**:

- **Criterion**: What needs to be true (user-facing behavior)
- **Definition of Done**: Specific, measurable state
- **Verification**: How you'll know it's done (automated test, manual QA, analytics)

Example:
```json
{
  "criterion": "Batch PDF processing works at scale",
  "definition_of_done": "System can process 10,000 pages without memory leaks or crashes",
  "verification_method": "automated_test"
}
```

### Step 6: Success Metrics

Define the north star + key metrics that will be measured in Stage 9:

```json
{
  "north_star": "% of user documents requiring zero manual intervention",
  "key_metrics": [
    {
      "metric": "Successful processing rate",
      "baseline": "85% (from OCR + form issues observed in Stage 1)",
      "target": "98%",
      "measurement_window": "weekly"
    },
    {
      "metric": "Average processing time per page",
      "baseline": "Unknown (assumes current tools)",
      "target": "< 100ms",
      "measurement_window": "daily"
    },
    {
      "metric": "User satisfaction (NPS)",
      "baseline": "0 (pre-launch)",
      "target": "50+",
      "measurement_window": "monthly"
    }
  ]
}
```

### Step 7: Constraints & Assumptions

**Constraints** (what limits us):
- Technical: "Must run on Windows 7+ due to enterprise customers"
- Business: "Budget: $50k for MVP"
- Legal: "Must comply with GDPR for EU users"

**Assumptions** (what we believe but haven't proven):
- "Users prefer CLI over web UI for batch processing"
- "Enterprise customers will pay $100/month for unlimited processing"

### Step 8: Risks & Mitigations

For each major risk, define mitigation:

```json
{
  "risk": "Open-source PDF libraries have Unicode bugs that take weeks to fix",
  "probability": "medium",
  "impact": "high",
  "mitigation": "Fork the library and maintain patches ourselves for the first year; evaluate switching to proprietary library if issues persist"
}
```

### Step 9: Competitive Positioning

- **Unique Value Prop**: Why us over Textract / Acrobat / PyMuPDF?
- **Why Us**: 2–5 key advantages (speed, cost, accuracy, ease, support)
- **Market Window**: Is there urgency? (e.g., "competitors are all moving upmarket")

### Step 10: Monetization Model

- **Model**: Freemium / subscription / pay-per-use / one-time / hybrid?
- **Strategy**: Pricing tiers, volume discounts, enterprise deals?
- **Target ARR**: Revenue goal from Stage 3 commercial assessment
- **CAC**: Customer acquisition cost target

### Step 11: Timeline Estimate

MVP implementation time in weeks (feeds Stage 5 / Stage 6 planning).

---

## Output Format

### `stage4.json` (Agent Judgment)

Structured data that helpers will merge into final PRD:

```json
{
  "product_vision": "...",
  "target_user_stories": [ { "persona": "...", "story": "...", "acceptance": [...] } ],
  "core_features": [ { "name": "...", "priority": "p0", "effort_hours": 40, ... } ],
  "acceptance_criteria": [ { "criterion": "...", "definition_of_done": "...", "verification_method": "..." } ],
  "success_metrics": { "north_star": "...", "key_metrics": [...] },
  "constraints_and_assumptions": { "technical_constraints": [...], "assumptions": [...] },
  "risks_and_mitigations": [ { "risk": "...", "mitigation": "..." } ],
  "competitive_positioning": { "unique_value_prop": "...", "why_us_over_competitors": [...] },
  "monetization_model": { "model_type": "subscription", "pricing_strategy": "...", "target_arr": 100000 },
  "timeline_estimate_weeks": 8
}
```

### `4_prd.json` (Final)

`build_prd.py` will merge `stage4.json` + `3_opportunity.json` into final schema (`contracts/prd.schema.json`).

### `4_prd.md` (Human Readable)

Formatted Markdown version for easy reading (generated by `digest.py`).

---

## Quality Checklist

Before submitting `stage4.json`:

- [ ] Product vision connects pain → solution
- [ ] 3–5 user stories per target persona
- [ ] Each story has 3–5 acceptance criteria
- [ ] 5–15 core features, clearly prioritized (P0/P1/P2)
- [ ] Feature effort estimates are realistic
- [ ] 5–20 product-level acceptance criteria
- [ ] Success metrics are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- [ ] Constraints & assumptions listed
- [ ] 2–5 major risks with mitigations
- [ ] Unique positioning vs competitors is clear
- [ ] Monetization model aligns with market size (Stage 3)
- [ ] MVP timeline is 4–16 weeks (if > 16 weeks, suggest phasing)

---

## Decision Point ②

After this stage, a human reviews:
1. Does the PRD match the opportunity?
2. Are acceptance criteria testable?
3. Is the timeline realistic?
4. Should we proceed to Stage 5 (architecture)?

**Decision**: PROCEED → Stage 5 · REVISE → back to Step 2 · CANCEL → feedback pool

---

## Helper

- `python3 helpers/build_prd.py <pid>` — Merges `stage4.json` + `3_opportunity.json` → `4_prd.json`
- `python3 helpers/build_i18n.py <pid> --stage 4` — Generates `.i18n.json` + `.zh.md`
- `python3 helpers/digest.py runs/<pid>/4_prd.json` — Human-readable digest

---

## References

- Opportunity schema: [`contracts/opportunity.schema.json`](../../../contracts/opportunity.schema.json)
- PRD schema: [`contracts/prd.schema.json`](../../../contracts/prd.schema.json)
- Example PRD: `runs/pipe_2026-06-15_001/4_prd.md` (goal: populate soon)
