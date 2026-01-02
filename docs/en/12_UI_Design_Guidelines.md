# UI Design Guidelines (Modern / Minimal / Premium)

> Goal: ship a UI that “looks like a product, not homework”: restrained, spacious, high contrast, clear hierarchy, and lightweight motion.  
> English-first copy (UI can switch EN/ZH). Avoid noisy decoration and heavy shadows.

## 1) Visual keywords

- **Modern**: clean grid, consistent spacing, subtle glass/blur used sparingly
- **Minimal**: fewer lines and borders; structure comes from whitespace + hierarchy
- **Premium**: refined typography, soft gradients, polished hover/focus states

## 2) Color system (dark-first, easy to extend to light mode)

- Background: near-black with a slight blue tint
- Surface: dark cards with low-contrast 1px borders
- Accent: one saturated blue as the primary accent (buttons/links)
- Text: near-white primary, muted secondary gray-blue

Suggested tokens:

- `--bg-0` / `--bg-1`
- `--surface-0` / `--surface-1`
- `--border`
- `--text-0` / `--text-1`
- `--accent` / `--accent-2`
- `--shadow`

## 3) Typography

- Prefer system UI fonts (Windows/Apple/Android); optionally add Inter later
- Heading scale:
  - H1: 32–40px (page title)
  - H2: 18–22px (card/module title)
  - Meta: 12–13px (tags/time/language)
- Body:
  - line height ~1.6
  - max reading width ~72ch

## 4) Layout

- Container width: `max-width: 1100px`
- Section spacing: ~24px
- Card radius: 14–18px
- Prefer “card lists” over tables

## 5) Components (must be consistent in MVP)

- **Topbar**: translucent + blur; no jump on scroll
- **Buttons**:
  - Primary: accent filled
  - Secondary: surface + border
  - Ghost: transparent with hover background
- **Cards**:
  - surface + border + subtle shadow
  - hover: slightly stronger border + gentle lift
- **Section cards**:
  - title + optional short description
  - icons optional (avoid emojis by default)
- **Feed / post cards** (social-style):
  - avatar, author, meta, title preview, and action row

## 6) Page structure (current pages)

### Home (`/`)
- recommended feed (latest approved for MVP)

### Sections (`/sections`)
- grid of all sections
- click through to `/sections/<code>`

### Section posts (`/sections/<code>`)
- section header
- feed list (same card pattern as home)

### Post detail (`/posts/<id>`)
- title + meta
- readable content layout
- meta includes author, section, city, language (and status if not approved)

## 7) Usability (required)

- visible focus styles (keyboard accessible)
- comfortable hit targets (>= 40px)
- contrast near WCAG AA


