# Multilingual Support & Translation Strategy (EN/ZH first)

## Goals

- Full-site multilingual support (at least EN + ZH), with language switching at any time
- **English-first development**: code, variables, APIs, DB fields, and commit messages use English
- Content (posts) supports:
  - users submit in EN or ZH
  - platform provides **AI translation** (EN↔ZH; later more languages)
  - translations flow through review/verification to avoid dangerous misunderstandings

## I18n scope

### 1) UI copy (required)

- navigation, buttons, forms, error messages, moderation statuses—all translatable
- default language: English (`en`)
- supported languages: English (`en`), Simplified Chinese (`zh`)

### 2) Content language (required)

Each post has at least one “source language” version and may have multiple translated versions.

- source language: `source_lang` (`en`/`zh`)
- versions: store `title/content` per language
- rendering:
  - if the user’s language version exists → show it
  - otherwise → show the source language and offer “AI translate / request translation”

## Data structure (keep it simple)

### Recommended minimal approach

- `posts`: store only the source-language version
  - `id, city, section, status, source_lang, title, content, created_at, updated_at`
- `post_translations`: store translated versions
  - `id, post_id, lang, title, content, provider, quality_status, created_at, updated_at`
  - `quality_status`: `ai_draft` / `human_reviewed` / `rejected`

## AI translation workflow (post translations)

### Trigger options (pick one for MVP)

- author clicks “Generate EN/ZH version” after submitting (most controllable)
- admin generates translation from moderation queue (works well early)
- on-demand translation after publishing (cost control)

### Recommended flow (safety-first)

1. generate translation → write to `post_translations` as `ai_draft`
2. if high-risk section (housing/safety) → require human review
3. after review, mark `human_reviewed` to become the default translated version

### Quality rules (avoid misinformation)

- do not invent details
- preserve proper nouns (departments, apps, institutions) and optionally keep originals
- keep numbers/dates/amounts identical
- flag ambiguity for terms prone to mistranslation (lease/sublease, deposit, co-signer)

## Translation system prompt (copy-ready)

```text
You are Bridge US’s content translation assistant. Translate posts accurately between English and Chinese without distortion.

[Hard rules]
1) Translate only what is provided. Do not add new facts, locations, prices, times, or contact details.
2) Numbers, dates, amounts, and addresses (if present) must remain exactly the same.
3) Preserve proper nouns (departments, places, app names, institutions). Optionally keep the original in parentheses.
4) Preserve structure and tone: titles stay titles, lists stay lists, steps stay steps.
5) For high-risk terms, you may add a very short parenthetical clarification (<= 12 English words or <= 12 Chinese characters).

[Input]
- source_lang: "en" or "zh"
- target_lang: "en" or "zh"
- title: ...
- content: ...

[Output JSON]
{
  "title": "...",
  "content": "...",
  "notes": ["...optional: term warnings / ambiguities..."]
}
```


