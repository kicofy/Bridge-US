# Developing Plan (Flask full-stack, Lite MVP)

> Framework & entry point: **Flask**, with **`app.py`** as the project entry.  
> Goal: deliver the Lite MVP core loop: **browse content / submit posts / human review / AI Q&A / AI pre-screen moderation (red-line blocking)**.  
> Extra constraint: **site-wide bilingual support** (at least `en`/`zh`) and **English-first development** (code/APIs/DB fields/copy written in English by default).

---

## 0. Minimal constraints (align first)

### Multilingual (I18n) baseline

- UI must support `en`/`zh`, default `en`
- Users can switch language at any time (recommended: `/set-lang/<lang>` or `?lang=...`)
- Posts support bilingual content:
  - `source_lang`: author submission language (`en`/`zh`)
  - optional `post_translations`: AI translation versions (`ai_draft` → `human_reviewed`)

### Lite MVP sections (`section`)

- First week
- Housing & move-in
- Food & groceries
- Transportation
- Life admin
- Safety & scams

### Lite MVP minimal status (`status`)

- `draft`: draft (author-visible)
- `pending_review`: pending review (admin-visible)
- `approved`: published (public)
- `rejected`: rejected (author-visible)

---

## 1. Project structure (keep it minimal)

> You required `app.py` as entry point. This split keeps things maintainable without getting complex.

```
/
  app.py
  requirements.txt
  instance/
    app.db                  # SQLite for the initial version
  templates/
    base.html
    index.html              # content list
    post_detail.html
    submit.html             # submission form
    admin_login.html
    admin_queue.html        # moderation queue
    ai_chat.html            # AI Q&A page
  static/
    app.css
    app.js                  # optional: AI Q&A frontend calls
  services/
    ai.py                   # AI Q&A (placeholder, replaceable)
    moderation_ai.py        # AI pre-screen moderation (red-line blocking)
    translate_ai.py         # optional: AI translation (EN↔ZH)
  db.py                     # database init/connection
  translations/             # Flask-Babel language packs (generated later)
```

---

## 2. Step-by-step development plan

### Step 1 — Bootstrap the project (half day)

**Goal**: run the Flask server locally and render a homepage.

- Deliverables:
  - `requirements.txt` (at least: Flask + Flask-Babel)
  - `app.py` (Flask app + `/` route)
  - `templates/base.html`, `templates/index.html`
- Acceptance:
  - visiting `/` shows a page
  - default language is `en`, can switch to `zh`

---

### Step 2 — SQLite database + `posts` table (half day)

**Goal**: create the minimal DB tables to store posts.

- Table `posts` (minimal fields):
  - `id` (int)
  - `title` (text)
  - `content` (text)
  - `city` (text, nullable)
  - `section` (text, must be one of the section enum values)
  - `status` (text: draft/pending_review/approved/rejected)
  - `source_lang` (text: en/zh, default en)
  - `created_at`, `updated_at`
- (Optional but recommended) Table `post_translations` (for AI translation):
  - `id`, `post_id`
  - `lang` (en/zh)
  - `title`, `content`
  - `provider` (e.g., openai/other)
  - `quality_status` (ai_draft/human_reviewed/rejected)
  - `created_at`, `updated_at`
- Deliverables:
  - `db.py`: init DB + create tables
  - `app.py`: ensure tables exist on startup
- Acceptance:
  - after inserting one `approved` post manually, it shows on the homepage

---

### Step 3 — Content browsing (city + section filtering) (1 day)

**Maps to Lite MVP #1**

**Goal**: browse content without login; show only `approved`; filter by `city` and `section`.

- Pages:
  - `GET /`: list page (query: `city`, `section`)
  - `GET /posts/<id>`: detail page
- Deliverables:
  - `templates/index.html`: city input/dropdown, section dropdown, list rendering
  - `templates/post_detail.html`
- Acceptance:
  - `/` shows only approved posts
  - switching `city/section` filters works

---

### Step 4 — Submission (only section + title + content) (1 day)

**Maps to Lite MVP #2**

**Goal**: user submission writes a post as `pending_review` (not publicly visible yet).

- Pages/APIs:
  - `GET /submit`: submission form
  - `POST /submit`: write into posts with status `pending_review`
- Deliverables:
  - `templates/submit.html`
  - validation: section must be valid; title/content required
- Acceptance:
  - after submit, the post does not appear on home feed (because it’s not approved)

---

### Step 5 — Admin login + review queue (1 day)

**Maps to Lite MVP #3**

**Goal**: admin can review pending posts and approve/reject.

- Simplest admin approach (initial version):
  - use env var `ADMIN_PASSWORD` (no complex user system)
  - session login
- Pages/APIs:
  - `GET /admin/login`, `POST /admin/login`
  - `GET /admin/queue`: list only `pending_review`
  - `POST /admin/review/<id>`: approve or reject (optional reason)
- Deliverables:
  - `templates/admin_login.html`
  - `templates/admin_queue.html`
- Acceptance:
  - approved posts appear on home immediately
  - rejected posts do not appear publicly (author status UI can be added later)

---

### Step 6 — AI Q&A (MVP: cite reviewed content only) (1–2 days)

**Maps to Lite MVP #4**

**Goal**: provide an AI Q&A page + API; answers must reference only approved content.

- Backend:
  - `GET /ai`: Q&A page
  - `POST /api/ai/ask`: input `question` → output `{answer, quotes:[{post_id,title}]}`
- Minimal strategy (simple but usable):
  - retrieval: keyword match over `approved` posts (first version)
  - generation:
    - template-based answer summarizing quotes, or
    - connect an LLM later, but must return quotes
  - multilingual:
    - Chinese question → Chinese answer; English question → English answer (or follow UI language)
    - citations prefer same-language version if `post_translations` exists
- Deliverables:
  - `services/ai.py`
  - `templates/ai_chat.html`
  - `static/app.js` (optional, fetch the API)
- Acceptance:
  - each answer returns at least one citation (or clearly says “no reviewed content found” and suggests submitting content)

---

### Step 7 — AI pre-screen moderation (red-line blocking) (1 day)

**Maps to Lite MVP #5**

**Goal**: auto-scan submissions for privacy leaks and obvious scam/lead-gen signals; return allow/needs_review/block.

- Trigger:
  - run `services/moderation_ai.py` during `POST /submit`
- Rules (start with deterministic rules):
  - privacy patterns (phone/email/ID) → `needs_review` (or `block`)
  - scam/lead-gen keywords (transfer/deposit bait, WhatsApp/WeChat/Telegram) → `needs_review`
  - non-official external links (http/https) → `needs_review`
- Behavior:
  - `block`: reject submission and tell the user what to remove
  - `needs_review`: allow submission but highlight risks in admin queue
  - `allow`: normal submission flow
- Deliverables:
  - `services/moderation_ai.py`
  - optional: add `ai_flag`/`ai_reason` fields (or log only for first version)
- Acceptance:
  - content containing phone/contact bait is flagged and clearly surfaced

---

### Step 8 — (Optional) AI post translation (EN↔ZH) (1 day)

**Goal**: generate a translated version and store it in `post_translations` as `ai_draft`.

- Trigger (choose one):
  - admin clicks “Generate translation” in review queue
  - or author clicks “Generate EN/ZH version” after submission
- Constraints:
  - translation must not add facts or change numbers/amounts
  - high-risk sections (housing/safety) should require human review before `human_reviewed`
- Acceptance:
  - post detail page shows translation when user language version exists

---

## 3. Minimum launch checklist (actually deployable)

- `.env` (or env vars)
  - `FLASK_SECRET_KEY`
  - `ADMIN_PASSWORD`
- Deployment (keep simple)
  - gunicorn/uwsgi + Nginx (Linux)
  - or managed hosting first
- Basic security
  - admin routes require login
  - CSRF protection for POST endpoints (can be later, but recommended ASAP)

---

## 4. Later iterations (explicitly deferred)

- full user system (registration/login + “my posts” status page)
- helpful/bookmark/report loop
- comments
- true vector retrieval (pgvector) and stronger RAG
- volunteer ticket system


