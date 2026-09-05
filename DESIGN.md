# DESIGN.md — Chemical Physics Roadmap

The design spec for the roadmap site (`templates/` + `static/style.css` → `site/`).
Derived from the site's existing stylesheet, which itself extends Jonas's blog aesthetic.
Read this before changing anything visual; update it when the look genuinely moves on.

---

## Visual Theme

**Warm paper, not software.** This is a personal academic record, not a SaaS dashboard.
The character comes from a warm off-white ground, a serif for anything that carries
authority (page titles, the site title, note titles), and thin rules instead of boxes and
shadows. There are no cards with drop shadows, no gradients, no full-bleed colour blocks.
Density is the point — this is a document you scan for status, so information sits close
together and colour is reserved for meaning.

**Night mode keeps that character.** The dark theme is a warm charcoal (`#1A1816`), never
a blue-black. The same paper feeling, lit differently. Accents lighten as they move onto
the dark ground; the palette is not simply inverted.

---

## Colour Palette

Every colour is a CSS custom property. **A literal colour inside a rule is a bug** — it
will not survive the theme switch. Add new colours to *both* token blocks.

That means named keywords too, not just hex. `background: white` on `.stat-card` and
`.card` is exactly how the stat boxes stayed glaring white the first time night mode
shipped; grepping for `#` alone will not catch it. Search for `white`, `black`, `rgb(`
and `hsl(` as well — and note that `white-space:` is a false positive.

### Ground and text

| Token | Day | Night | Used for |
|---|---|---|---|
| `--bg` | `#F5F1EB` | `#1A1816` | Page ground |
| `--ink` | `#2C2A26` | `#E8E3DA` | Body text, headings |
| `--muted` | `#6B6660` | `#9B948A` | Secondary text, nav, labels, meta |
| `--rule` | `#D9D2C7` | `#35312B` | Hairlines, table borders, dividers |
| `--accent` | `#CC785C` | `#E0916F` | Links, active nav, progress fill |
| `--accent-dk` | `#A85B40` | `#F0AC8C` | Hover / emphasis on accent |
| `--accent-rgb` | `204, 120, 92` | `224, 145, 111` | The accent as raw channels, for `rgba()` washes |
| `--surface` | `#FFFFFF` | `#221F1C` | Raised panels — stat cards, project/internship cards |

### Status colours — paired foreground and background

Each pair is a badge: text on its own tinted ground. Never use the foreground on `--bg`
directly at small sizes.

| Token pair | Day fg / bg | Night fg / bg | Meaning |
|---|---|---|---|
| `--green` / `--green-bg` | `#2D6A4F` / `#E8F4EC` | `#7FD1A6` / `#1B2E24` | completed, accepted, offered |
| `--amber` / `--amber-bg` | `#8B5000` / `#FFF3E0` | `#E0A458` / `#33260F` | in-progress, active, interviewing |
| `--purple` / `--purple-bg` | `#6B46C1` / `#F5F0FF` | `#B79CF0` / `#262038` | ideation, drafting, paused |
| `--blue` / `--blue-bg` | `#1565C0` / `#E3F2FD` | `#7FB5E8` / `#16283A` | contacted, submitted |
| `--red` / `--red-bg` | `#991B1B` / `#FEE2E2` | `#EFA0A0` / `#3A1E1E` | rejected, urgent deadline |
| `--muted` / `--neutral-bg` | `#6B6660` / `#F0F0F0` | `#9B948A` / `#2A2724` | planned, identified, cold, waived |

### Contrast

Verified against WCAG AA (4.5:1 for body text). Night mode: ink 13.9:1, muted 5.9:1,
accent 7.1:1, every badge pair between 4.9:1 and 7.9:1. Day mode: ink 12.7:1, muted 5.1:1.

**Known exception:** `--accent` in day mode is 2.9:1 on `--bg`. It is inherited from the
existing design and is used only for nav links and the active state, never for body copy.
If accent text ever becomes load-bearing at small sizes, darken it toward `--accent-dk`.

---

## Typography

| Token | Stack | Used for |
|---|---|---|
| `--serif` | Charter, Iowan Old Style, Source Serif, Georgia | Site title, page titles, note titles |
| `--sans` | system-ui stack (`-apple-system`, Segoe UI, Helvetica Neue) | Everything else |
| `--mono` | `ui-monospace`, SF Mono, Menlo, Consolas | Course codes, code blocks, confirmation numbers |

- Body: 15px / 1.6, `--sans`
- Page title: 30px, `--serif`, 600, `-0.015em`
- Site title: 20px, `--serif`, 600
- Nav, subtitles, meta: 13px, `--muted`
- Section labels: uppercase, letter-spaced, `--muted`
- Badges: 11px, uppercase, letter-spaced

Serif carries identity, sans carries data. Do not set tables or badges in the serif.

---

## Components

- **`.mission`** — the quote block on the dashboard. Bare text, no label. One quote, one
  attribution.
- **`.badge-*`** — status pills. One class per status string in the build vocabulary; the
  class name is derived from the status, so a new status needs a new pair here.
- **`.stat-card` / `.stat-grid`** — dashboard counters on `--surface`. Big number in
  `--accent`, uppercase label in `--muted`. In night mode `--surface` sits only a hair
  above `--bg` (1.08:1) — a panel should read as a gentle lift, never as a bright block.
- **`.data-table`** — the workhorse. Hairline rules only, no zebra striping; hover is a
  4% accent wash via `rgba(var(--accent-rgb), 0.04)`.
- **`.progress-row`** — label, track, fill. Fill is `--accent`, turning `--green` at 100%.
- **`.timeline`** — the eight-semester degree strip, horizontally scrollable.
- **`.code-block`** — inverted terminal block. Swaps `--ink` and `--bg` rather than naming
  its own colours, so it stays legible in both themes.
- **`.theme-toggle`** — day/night switch, last item in the nav. Moon glyph when a click
  would take you to night, sun when it would take you back to day.

---

## Layout

- Content column: `--content-width` 900px, centred, 24px side padding (`.wrap`).
- Header: site title left, nav right, baseline-aligned, hairline underneath, 40px below.
- Sections stack with a `.section-label` above each.
- Footer: hairline above, 12px muted text.
- Wide content (tables, the timeline) scrolls inside its own container — the page body
  never scrolls sideways.

---

## Theming Mechanics

Three states, and the order matters:

1. **Bare `:root`** holds the complete light palette. This is the base; every token is
   defined here.
2. **`@media (prefers-color-scheme: dark)` wrapping `:root:not([data-theme="light"])`**
   redefines *only token values* for viewers whose OS asks for dark — unless they have
   explicitly chosen day mode on this site.
3. **`:root[data-theme="dark"]`** redefines the same values again so the in-page toggle
   wins in both directions.

A small script in `<head>` applies the stored choice before first paint, so a night-mode
viewer never sees a flash of light. No stored choice means no attribute, which leaves the
OS preference in charge — and the page keeps following the OS until the viewer clicks.
The choice is per-browser (`localStorage`), wrapped in try/catch so private windows and
blocked site data degrade to the OS preference instead of erroring.

---

## Do

- Put every new colour in **both** token blocks.
- Use the status token *pairs* for anything that signals state.
- Use `rgba(var(--accent-rgb), …)` for accent washes.
- Keep rules hairline and backgrounds flat.
- Check both themes before calling a visual change done.

## Don't

- Don't write a literal hex or `rgb()` inside a rule.
- Don't define a colour only inside the dark blocks — the light value must exist on bare
  `:root` or it is undefined by default.
- Don't add shadows, gradients, or rounded card chrome; this site is paper and rules.
- Don't set data in the serif, or headings in the mono.
- Don't edit `site/` — it is build output. Change `templates/` or `static/style.css` and
  run `python3 tools/build.py`.

---

## Agent Prompt Guide

When asked for a visual change here:

1. Read this file, then `static/style.css`'s token blocks.
2. Decide whether the change is a **token** change (a colour everywhere) or a **rule**
   change (one component). Prefer tokens.
3. If you introduce a colour, add it to the day block *and* the night block, then verify
   contrast against both grounds at 4.5:1 for anything text-sized.
4. Rebuild with `python3 tools/build.py`, preview with `python3 tools/serve.py`, and look
   at the page in **both** themes.
5. Update this file if the change alters the system rather than applying it.
