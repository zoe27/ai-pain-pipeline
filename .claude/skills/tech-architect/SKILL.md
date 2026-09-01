# Tech Architect Skill

> **Stage 5: Technical Architecture & Design**  
> Transforms PRD into detailed technical specification with system design, API contracts, database schema, and deployment architecture.

## Mission

Design a complete technical architecture that enables Stage 6 developers to write code without ambiguity. Output should be architecture diagrams (text-based), tech stack decisions with justification, database schema, API contracts, and a phased development plan.

## Input

- `runs/{pid}/4_prd.json` — PRD with features, constraints, timeline
- `runs/{pid}/4_prd.digest.md` — Executive summary
- User decision: **PROCEED** from decision point ②

## Output

- `runs/{pid}/_judgments/stage5.json` — Agent's architecture judgments
- `runs/{pid}/5_tech_spec.json` — Full tech spec (schema: [`contracts/tech_spec.schema.json`](../../../contracts/tech_spec.schema.json))
- `runs/{pid}/5_tech_spec.md` — Mermaid diagrams + detailed spec
- Codebase skeleton (optional): Git repo scaffold with `/api`, `/frontend`, `/tests` directories

## Process

### Step 1: Read PRD Context

1. Load `4_prd.json`
2. Understand core features and their priorities (P0/P1/P2)
3. Note constraints (technical, business, legal)
4. Check timeline_estimate_weeks (feeds development phases)
5. Review from Stage 3: TAM/SAM/SOM (scale questions)

### Step 2: High-Level Architecture

Choose 1 of these architectural patterns based on PRD:

#### Pattern A: Monolith + SPA
**Use when**: MVP, <50k DAU, simple domain  
**Components**: Node/Python + React/Vue + PostgreSQL  
**Pros**: Fast to build, simple ops  
**Cons**: Scaling limits at ~10k concurrent users

#### Pattern B: Microservices (AWS/GCP)
**Use when**: Need scaling from day 1, complex domain (e.g., video processing)  
**Components**: Node + React + PostgreSQL + Redis + Message Queue (SQS/Kafka)  
**Pros**: Independent scaling  
**Cons**: Operational complexity (Stage 8 needs more setup)

#### Pattern C: Serverless (Vercel + Supabase)
**Use when**: Low initial traffic, cost-sensitive, primarily CRUD  
**Components**: Next.js (Vercel) + Supabase (Postgres + Auth + Storage)  
**Pros**: Pay-per-use, scales to millions, minimal ops  
**Cons**: Cold start latency, limited DB transactions

#### Pattern D: Single-Page App + API Gateway
**Use when**: Real-time collaboration, WebSocket needs  
**Components**: React + Node (Socket.io) + PostgreSQL + Redis Pub/Sub  
**Pros**: Real-time, responsive  
**Cons**: More complex debugging

**Your decision**: Choose 1, write rationale (why this pattern for this product).

### Step 3: Tech Stack Selection

For each layer, choose from battle-tested options:

#### Frontend
- **Framework**: React 19 / Next.js 15 / Vue 3 / Svelte 5 (pick one)
- **Build tool**: Vite (fast, modern)
- **UI components**: shadcn/ui (Tailwind) / Radix UI / Chakra UI
- **State mgmt**: TanStack Query (fetch) + Zustand (local)
- **Testing**: Vitest + Playwright
- **Linting**: ESLint + Prettier

**Decision template:**
```
Frontend: Next.js 15 (chosen for SEO + SSR + API routes)
  - TypeScript, Tailwind CSS, shadcn/ui for consistency
  - TanStack Query for server-state management
  - Zustand for client-state
  - Vitest (unit) + Playwright (e2e) for testing
```

#### Backend
- **Language + Runtime**: Node.js + Express / Fastify / Hono, or Python + FastAPI / Django
- **API style**: REST or GraphQL
- **Auth**: JWT + Refresh tokens (or OAuth2 for social)
- **DB driver**: Prisma (Node) / SQLAlchemy (Python)
- **Logging**: Winston / Pino (Node) / Structlog (Python)
- **Error tracking**: Sentry
- **Testing**: Jest / Pytest

**Decision template:**
```
Backend: Node.js + Fastify (chosen for speed + TypeScript support)
  - FastAPI? No, need real-time features
  - Prisma ORM for type-safe DB access
  - JWT + refresh tokens in Redis
  - Sentry for error tracking + logging
  - Jest for unit tests
```

#### Database
- **Primary**: PostgreSQL (battle-tested, ACID)
- **Cache layer**: Redis (for sessions, rate limiting, real-time)
- **Search**: Elasticsearch (if text search needed) or PostgreSQL full-text search
- **File storage**: S3 or Cloudinary or local + CDN

**Decision template:**
```
Database: PostgreSQL 15 (chosen for JSON fields + reliability)
  - Redis for sessions, caching, rate limiting
  - No search engine needed yet (use PG full-text)
  - S3 + CloudFront for file storage
```

#### Infrastructure
- **Compute**: Vercel (frontend) + Railway (backend) + Neon (DB)
- **Or**: AWS (EC2 + RDS + CloudFront)
- **Or**: GCP (Cloud Run + Cloud SQL)
- **CI/CD**: GitHub Actions (free, good integration)
- **Monitoring**: Sentry (errors) + PostHog (product) + Better Uptime (status)

**Decision template:**
```
Infrastructure: Vercel + Railway + Neon + GitHub Actions
  - Chosen for simplicity + free tier coverage
  - Vercel handles frontend auto-deploy
  - Railway handles backend (easy scaling)
  - Neon for serverless PostgreSQL
  - GitHub Actions for CI/CD
```

### Step 4: System Design Diagram

Use ASCII or Mermaid to show data flow:

```
┌─────────────────────────────────────────────────────┐
│                    Internet                         │
└────────┬────────────────────────────────────────────┘
         │
    ┌────▼─────┐
    │ Cloudflare│ (CDN, DDoS)
    └────┬──────┘
         │
    ┌────▼─────────────────────────────────┐
    │  Vercel (Next.js Frontend)           │
    │  - React components + SSR            │
    │  - API Routes → Backend               │
    └────┬──────────────────────────────────┘
         │
    ┌────▼──────────────────┐
    │  Railway Backend      │
    │  - Fastify + Express  │
    │  - Business logic     │
    │  - Queue jobs        │
    └────┬──────────────────┘
         │
    ┌────┴──────────┬────────────────┐
    │               │                │
┌───▼────┐    ┌───▼──────┐    ┌──────▼────┐
│ Neon   │    │ Redis    │    │   S3      │
│ PostgreSQL   │ Sessions │    │ Files     │
│ Data   │    │ Cache    │    │ Storage   │
└────────┘    └──────────┘    └───────────┘
```

### Step 5: Database Schema

For each table, define:
- **Name**: Clear, singular (e.g., `user`, `document`, `processing_job`)
- **Columns**: Type, nullable, defaults, constraints
- **Primary key**: Usually `id` (UUID v4)
- **Foreign keys**: Relationships to other tables
- **Indexes**: Queries that will be heavy
- **Partitioning** (if large): By date, user_id, etc.

Example:
```json
{
  "name": "documents",
  "columns": [
    { "name": "id", "type": "UUID", "nullable": false, "default": "gen_random_uuid()" },
    { "name": "user_id", "type": "UUID", "nullable": false },
    { "name": "filename", "type": "VARCHAR(255)", "nullable": false },
    { "name": "status", "type": "VARCHAR(50)", "nullable": false, "default": "'pending'" },
    { "name": "processed_at", "type": "TIMESTAMP", "nullable": true },
    { "name": "created_at", "type": "TIMESTAMP", "nullable": false, "default": "NOW()" }
  ],
  "primary_key": ["id"],
  "foreign_keys": [
    { "column": "user_id", "references": "users.id" }
  ],
  "indexes": ["user_id", "(status, created_at)"]
}
```

### Step 6: API Contracts

Define REST endpoints (or GraphQL types):

```json
{
  "endpoint": "POST /api/v1/documents/process",
  "method": "POST",
  "description": "Upload and queue a document for processing",
  "request_schema": {
    "file": "multipart/form-data, max 100MB",
    "options": {
      "auto_rotate": "boolean (default: true)",
      "extract_text": "boolean (default: true)",
      "repair_forms": "boolean (default: true)"
    }
  },
  "response_schema": {
    "job_id": "UUID",
    "status": "pending | processing | complete | error",
    "estimated_completion_seconds": "integer"
  },
  "authentication": "Bearer token (JWT)",
  "rate_limits": "100 requests/hour per user, 10 concurrent uploads"
}
```

Include 5–10 key endpoints minimum (list, get, create, update, delete patterns).

### Step 7: Deployment Architecture

How will this run in production?

```
┌─────────────────────────────────────────────┐
│         Production Environment              │
├─────────────────────────────────────────────┤
│  Region: us-east-1                          │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ Vercel (Edge + Serverless)           │   │
│  │ - Auto-scales 0 → 1000 instances    │   │
│  │ - 99.95% uptime SLA                  │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ Railway Backend (Container)          │   │
│  │ - 2 instances (active + standby)     │   │
│  │ - Auto-restart on crash              │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ Neon DB (Managed PostgreSQL)         │   │
│  │ - Daily backup (7-day retention)    │   │
│  │ - Read-only replicas (future)       │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ Sentry + PostHog                    │   │
│  │ - Error tracking, analytics          │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Step 8: Security Considerations

- **Authentication**: JWT with refresh tokens (or OAuth2)
- **Authorization**: Role-based access control (RBAC) — user levels, team roles
- **Data protection**: TLS in transit, encryption at rest (for sensitive fields)
- **Rate limiting**: Per-user, per-IP
- **Input validation**: On frontend + backend
- **Dependency scanning**: Snyk in CI/CD
- **Secrets management**: Environment variables (never in code)
- **GDPR**: User data export, deletion via API

### Step 9: Scalability Plan

- **Expected load at launch**: 100 DAU
- **Expected load in 12 months**: 10k DAU (goal from Stage 3)
- **Bottleneck analysis**: DB write capacity, file storage, API latency
- **Vertical scaling**: Increase instance size (cheap, limited)
- **Horizontal scaling**: Add instances, load balancing (needs architecture changes)
- **Performance targets**: API p95 latency < 200ms, DB query < 100ms, homepage load < 2s

### Step 10: Development Phases

Break MVP into 3–5 phases over timeline_estimate_weeks:

```json
{
  "phase": 1,
  "name": "Core MVP",
  "duration_weeks": 2,
  "deliverables": [
    "Backend API scaffolding + DB schema",
    "User auth + JWT tokens",
    "File upload endpoint"
  ],
  "success_criteria": [
    "All tests passing",
    "Deployed to staging",
    "API documented with OpenAPI"
  ],
  "dependencies": []
}
```

Typical breakdown:
- **Phase 1** (2w): Backend infrastructure + auth
- **Phase 2** (2w): Core features (P0)
- **Phase 3** (2w): Frontend + integration
- **Phase 4** (1–2w): Testing + refinement
- **Phase 5** (1w): Deployment + monitoring

---

## Output Format

### `stage5.json` (Agent Judgment)

```json
{
  "architecture_pattern": "monolith | microservices | serverless | websocket",
  "architecture_rationale": "...",
  "tech_stack": {
    "frontend": { "framework": "Next.js 15", "ui_library": "shadcn/ui", ... },
    "backend": { "language": "Node.js", "framework": "Fastify", ... },
    "database": { "primary": "PostgreSQL", "cache": "Redis", ... },
    "infrastructure": { "hosting": "Vercel + Railway", ... }
  },
  "system_design": [ { "component": "Auth Service", "description": "...", "technologies": [...] } ],
  "database_schema": { "tables": [...] },
  "api_contracts": [ { "endpoint": "POST /api/v1/...", ... } ],
  "deployment_architecture": { "environments": [...], "monitoring": [...] },
  "security_considerations": { ... },
  "scalability_plan": { ... },
  "development_phases": [ { "phase": 1, ... } ],
  "estimated_effort_hours": 320
}
```

### `5_tech_spec.json` (Final)

Merged from `stage5.json` by `build_tech_spec.py`.

### `5_tech_spec.md` (Human Readable)

Formatted Markdown with ASCII/Mermaid diagrams.

---

## Quality Checklist

Before submitting:

- [ ] Architecture pattern chosen with clear rationale
- [ ] Tech stack choices justified (why this over alternatives?)
- [ ] System design diagram is clear and complete
- [ ] Database schema is normalized and indexed appropriately
- [ ] API contracts are complete (≥5 endpoints, full request/response)
- [ ] Deployment architecture matches team ops capabilities
- [ ] Security checklist complete (auth, encryption, secrets, compliance)
- [ ] Scalability plan addresses expected growth (100 → 10k DAU)
- [ ] Development phases are realistic and sequenced
- [ ] Effort hours match Stage 4 feature estimates
- [ ] Dependency graph is clear (phase 1 → phase 2, etc.)

---

## Decision Point ②

Before Stage 6 (coding):
1. Do developers understand the architecture?
2. Is tech stack suitable for timeline?
3. Are database/API designs sound?
4. Can ops support the deployment model?

**Decision**: PROCEED → Stage 6 · REVISE → back to Step 2 · CANCEL → feedback pool

---

## Helper

- `python3 helpers/build_tech_spec.py <pid>` — Merges `stage5.json` + `4_prd.json` → `5_tech_spec.json`
- `python3 helpers/init_codebase.py <pid> --tech-stack <stack>` — Scaffolds Git repo skeleton
- `python3 helpers/digest.py runs/<pid>/5_tech_spec.json` — Renders diagrams to Markdown

---

## References

- PRD schema: [`contracts/prd.schema.json`](../../../contracts/prd.schema.json)
- Tech spec schema: [`contracts/tech_spec.schema.json`](../../../contracts/tech_spec.schema.json)
- Example: `runs/pipe_2026-06-15_001/5_tech_spec.md` (goal: populate soon)
