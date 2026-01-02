# Technical Architecture Recommendations (MVP-ready)

## Goals

- Support the minimal closed loop: **content + moderation + AI Q&A + anti-spam/anti-scam**
- Scale to multiple cities/campuses, multiple languages, and volunteer workflows
- Safety and privacy by default

## Suggested stack (replaceable)

### Frontend

- Next.js (React + TypeScript)
- UI: Tailwind CSS (or Chakra/MUI)
- i18n: next-intl (or i18next)

### Backend (choose one based on team strengths)

- Node.js: NestJS (or Express/Fastify)
- Python: FastAPI

### Data & search

- Primary DB: PostgreSQL
- Search: Postgres full-text (MVP) → OpenSearch/Elastic later
- Vector retrieval: pgvector (MVP is enough)
- Cache/queue: Redis (rate limits, moderation queue, async jobs)

### Files & media

- Object storage: S3-compatible
- Safety handling: EXIF stripping; optional image redaction (phone/address/face)

## Service split (MVP)

- Web app (SSR/ISR)
- API service (auth, content, moderation, volunteers)
- AI service (merged into API or separated)
  - RAG: retrieve + rerank + generate
  - Moderation: rules + model tags
- Worker (async jobs)
  - embeddings/ingestion
  - queue processing
  - staleness reminders / update tasks

## Roles & permissions

- user: read, ask, submit
- contributor: higher posting limits, help update content
- volunteer: verification/translation/support tickets
- moderator: review, ban, handle appeals
- admin: system configuration and permissions

## Core data model (overview)

- User: role, language, school/city, trust score
- Post: guides/experiences/scam cases
  - minimum suggested fields:
    - `type`: guide / experience / scam
    - `section`: First week / Housing & move-in / Food & groceries / Transportation / Life admin / Safety & scams
    - `city` (optional `state`, `school`)
    - `title`, `content`
    - `status`: draft / pending / approved / rejected
- Verification: review records (status, evidence, reviewer, timestamps)
- Helpfulness: helpful feedback
- Report: reports and outcomes
- VolunteerTicket: volunteer assignments
- AiAnswerLog: Q&A logs (citations, model version, risk flags)
- ModerationResult: AI pre-screen results (internal)

## Non-functional requirements (design early)

- Security: rate limits, anti-bot, link policy, redaction, audit logs
- Privacy: minimal collection, default anonymity, deletion requests and retention policy
- Observability: errors, slow queries, queue backlog, moderation hit rates
- Operability: staleness, update incentives, report loop, moderation SLA


