# Image Credits & Licensing Record

Every photograph used in FitTrack was individually verified against its live Unsplash
photo page before being added to the project. Each page was confirmed to show
**"Free to use under the Unsplash License"** — not Unsplash+, which is a separate paid
and more restricted tier. No image in this project required a paid license or
subscription.

Attribution is not required by the Unsplash License, but is included here and in the
UI (a small credit chip appears on hover/visible over each photo) because it's good
practice and keeps this record auditable.

| Section | Photographer | Unsplash Photo ID | Source page (verified) |
|---|---|---|---|
| Hero | Morrow Solutions | `photo-1656774950529-44a6153521ee` | https://unsplash.com/photos/a-man-lifting-weights-9W9BDUG7u9E |
| Workout | Victor Freitas | `photo-1517838277536-f5f99be501cd` | https://unsplash.com/photos/man-holding-black-barbell-hOuJYX2K5DA |
| Nutrition | Sergio Mena Ferreira | `photo-1768326119231-bf064c1b8fdf` | https://unsplash.com/photos/a-colorful-poke-bowl-with-tuna-avocado-and-edamame-ounjBTyK6VY |
| Hydration | Andrew R | `photo-1616556425595-93db848a50c7` | https://unsplash.com/photos/water-pouring-on-clear-drinking-glass-BhspCN17HT8 |
| Progress | joe mcferrin | `photo-1686247167200-d74f0f24b5be` | https://unsplash.com/photos/a-man-lifting-a-barbell-in-a-park-s6znUip3Mro |
| Login page panel | Victor Freitas | `photo-1517838277536-f5f99be501cd` | (same as Workout, reused) |
| Register page panel | Morrow Solutions | `photo-1656774950529-44a6153521ee` | (same as Hero, reused) |

## How images are served

This sandbox has no outbound network access, so binaries could not be downloaded and
re-hosted as local static files — `curl` to `images.unsplash.com` fails DNS resolution
here (verified directly, not assumed). Images are instead served directly from
Unsplash's own CDN (`images.unsplash.com`), which is imgix-backed: the `w=`, `q=`, and
`auto=format` URL parameters perform genuine on-the-fly resizing, compression, and
format negotiation (serving WebP/AVIF to supporting browsers). A `srcset` with five
widths (480/800/1200/1600/2000px) is generated for every image so each `<picture>`
loads an appropriately-sized file per viewport — see `image_assets.py`.

**If you later deploy somewhere with outbound network access:** download each photo at
its suggested filename below, drop it into `static/img/`, and update `image_assets.py`'s
`IMAGES` dict to point `src`/`srcset` at `/static/img/<filename>` instead of the
Unsplash CDN. No template changes are needed — they all read through `image_data()`.

| Key | Suggested local filename |
|---|---|
| hero | `hero-athlete-lifting.jpg` |
| workout | `workout-barbell-grip.jpg` |
| nutrition | `nutrition-poke-bowl.jpg` |
| hydration | `hydration-water-splash.jpg` |
| progress | `progress-outdoor-training.jpg` |

## Figma design reference

The visual direction (color tokens, typography pairing, hero and section
composition) was planned in Figma before implementation:
**[FitTrack — Light Cinematic Design System](https://www.figma.com/design/zoKsjndql0isQRYF5mslGT)**

No Figma AI credits were spent — the design system, wireframes, and layout
specifications were built using free Figma Plugin API operations (variables, frames,
text, auto-layout) only. Photography was sourced from Unsplash per the table above,
not generated.
