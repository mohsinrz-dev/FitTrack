# FitTrack — Visual Design System (Light Cinematic)

## Philosophy
Bright, refined, athletic — a premium training journal rendered in warm daylight,
not a dark neon dashboard. One deliberate visual moment per section; real
photography carries the energy, not decoration.

This replaces the project's original dark theme. Tokens below are kept in sync
with the Figma variable collection "FitTrack / Color" in
[FitTrack — Light Cinematic Design System](https://www.figma.com/design/zoKsjndql0isQRYF5mslGT).

## Color Tokens

| Token              | Hex       | Role                                       |
|--------------------|-----------|---------------------------------------------|
| `--c-base`         | `#F7F5F0` | Page background — warm off-white            |
| `--c-surface`      | `#EFEBE2` | Soft grey surface (alternating sections)     |
| `--c-surface-2`    | `#E4DFD3` | Deeper surface (progress tracks, macro bars) |
| `--c-text`         | `#211F1C` | Primary text — charcoal                      |
| `--c-sub`          | `#6B6660` | Secondary text, labels, captions             |
| `--c-lime`         | `#AEEA00` | Primary accent — CTAs, highlights            |
| `--c-lime-deep`    | `#7FA800` | Accent on light backgrounds, chart lines, links (passes text-contrast where `--c-lime` doesn't) |
| `--c-white`        | `#FFFFFF` | Cards, form fields                           |
| `--c-border`       | `#DAD4C6` | Dividers, outlines                           |
| `--c-muted`        | `#B9B2A2` | Disabled, placeholder                        |
| `--c-danger`       | `#C4432E` | Error, destructive action                    |
| `--c-warn`         | `#B5790B` | Warning                                      |

**Why two limes?** The PDF's reference lime (`#B6FF00`-ish) fails WCAG contrast as
text or small UI on a light background. `--c-lime` stays for large filled surfaces
(buttons, badges) where contrast comes from the dark text on top of it;
`--c-lime-deep` is used wherever lime appears *as* text or a thin line (links,
chart strokes, active nav state).

## Typography

**Display — Montserrat (600/700/800)**
Bold, geometric, editorial. Hero headline, section headings, stat values.

**Interface — Inter (300–600)**
Body copy, labels, form fields, navigation.

(Previously Barlow Condensed + Inter in the dark-theme version — swapped to
Montserrat per the PDF's "Montserrat/Poppins Bold" direction.)

## Spacing / Radius / Shadow / Motion
Unchanged from the original system — 4px spacing scale, `--r-sm/md/lg/pill`
radii, `--shadow-subtle/card/lift`, `--ease-out` cubic-bezier. See
`static/css/system.css` for exact values.

## Photography
Five section photographs sourced from Unsplash (verified free-license — see
`CREDITS.md` for the full record with source URLs). Delivered responsively via
Unsplash's CDN with `srcset`, lazy-loading below the fold, and a soft gradient
fallback (`.photo-frame`) shown while loading or if a request fails.

## 3D depth
Restrained CSS only — no WebGL. `.tilt-scene` / `.tilt-card` give the hero image
a subtle pointer-driven tilt (desktop only, `prefers-reduced-motion` disables
it); photo frames use `box-shadow` elevation rather than literal rotation to
read as "lifted" rather than gimmicky.

## Motion system
GSAP 3.12.5 + ScrollTrigger (CDN, version pinned — matches what the project
already had installed). See `static/js/landing.js`:
- Hero entrance timeline (staggered eyebrow → heading → copy → CTA → visual → stats)
- Generic `.reveal` scroll-triggered fade/rise, used across every section
- Pinned storytelling block (`#story-pin`): sticky image column crossfades
  between four photographs as four text blocks scroll past — genuine
  `ScrollTrigger` pin pattern, not a fake effect, disabled below 1024px width
  in favor of a static stacked layout
- Pointer-driven 3D tilt on the hero image (desktop + fine pointer only)
- Page-transition fade on internal navigation

`static/js/main.js` additionally animates progress bars and stat counters
**from the real server-rendered value** (0 → actual number) when they scroll
into view — never invented data, just an animated reveal of what Flask already
rendered. Falls back to the final value instantly under `prefers-reduced-motion`.

## Component inventory
Unchanged from the dark-theme version — `btn`, `form-*`, `card`, `badge`,
`stat-card`, `nav` / `sidebar`, `modal`, `toast`, `progress-ring`,
`chart-wrapper`, `empty-state`, `skeleton`. All retokenized to the light
palette; no structural changes.

## Icons
Phosphor Icons (CDN, weight: regular).
