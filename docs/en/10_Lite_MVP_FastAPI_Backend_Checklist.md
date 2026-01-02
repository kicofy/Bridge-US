# Lite MVP (initial version): What the FastAPI backend needs

> Goal: ship a minimal, usable version in **1–2 weeks**. It must include **baseline content**, **human review**, and **AI Q&A grounded in reviewed content**. Everything else is deferred.

## Lite MVP — only these features

### 1) Content browsing (public)

- show published content (only `approved`)
- filter: city/section (start with 2 dimensions)
- seed a small set of “human-curated starter guides” so the platform is useful on day one
- multilingual: UI and content support EN/ZH; default EN (`en`), switch to ZH (`zh`)

**Sections (`section`)**: fixed enum (en code + localized label)

- `first_week` (First week / 落地第一周)
- `housing_move_in` (Housing & move-in / 找房与入住)
- `food_groceries` (Food & groceries / 食物与超市)
- `transportation` (Transportation / 交通出行)
- `life_admin` (Life admin / 办事与生活)
- `safety_scams` (Safety & scams / 安全与诈骗)

### 2) Submissions (login optional, but recommended)

- for the first version, you can skip post types and treat everything as one “Post”
- author chooses `section` and fills `title` + `content`
- state: `draft` → `pending_review`

> Important: `section` is “where it appears in navigation.”  
> Post “types” (guide vs scam case) can be added later for templates and display.

### 3) Human review (most critical)

- moderation queue: list pending submissions
- actions: approve / reject (optional “needs info” later)
- only `approved` is publicly visible

### 4) AI Q&A (first version)

- one endpoint: user question → AI answer
- **hard constraint**: AI answers must be grounded in reviewed content and return citations (post IDs/titles)
- no multi-turn memory or personalization in the first version
- multilingual: question in EN/ZH; answer in user language; citations prefer matching language version if available

### 5) AI pre-screen moderation (red-line blocking)

- run at submission time:
  - privacy leaks (phone/email/IDs/unit numbers)
  - obvious scam/lead-gen (transfer prompts, contact bait, non-official links)
- output: `allow / needs_review / block` + triggering reasons

### 6) (Optional) Reporting

- one-click report
- admin can view report list (full workflow can come later)

## Lite MVP — explicitly NOT in scope

- reactions/bookmarks/points
- comments and DMs
- volunteer ticket system
- human collaborative translation workflows (AI translation is separate)
- advanced search and reranking
- housing marketplace matchmaking

## Minimal tables (MVP)

- `users` (optional if you allow anonymous reads/Q&A)
- `posts` (status/city/section/source_lang/title/content/created_at/updated_at)
- `moderation_reviews` (or a simpler audit in `posts`)
- `ai_answer_logs`
- `ai_moderation_results`
- (optional) `reports`
- (optional) `post_translations` for AI translation

## Minimal API (example)

- Content:
  - `GET /posts` (public; only `approved`; query: `city`, `section`)
  - `GET /posts/{id}` (public)
  - `POST /posts` (submit; login or internal)
- Moderation:
  - `GET /moderation/queue` (moderator/admin)
  - `POST /moderation/reviews/{post_id}` (approve/reject)
- AI:
  - `POST /ai/ask`
- (Optional) Reports:
  - `POST /reports`


