"""
Centralized registry of externally-sourced photography used across FitTrack.

Every entry here was verified directly against its Unsplash photo page before
being added — each confirms "Free to use under the Unsplash License" (not
Unsplash+, which is a paid/restricted tier). See CREDITS.md for the full
verification record (photographer, publish date, source URL).

Images are served from Unsplash's own CDN (images.unsplash.com), which is an
imgix-backed service: appending ``w=``, ``q=``, and ``auto=format`` parameters
performs genuine on-the-fly resizing, compression, and format negotiation
(serving WebP/AVIF to supporting browsers). This sandbox has no outbound
network access to download and re-host binaries locally (verified: DNS
resolution to images.unsplash.com fails from the build environment), so this
is the real optimization path available here rather than static local files.
If you deploy this project somewhere with outbound network access, you can
swap these for locally-hosted, pre-optimized files using the same filenames
suggested below without changing any template markup — just point SRC_BASE
entries at /static/img/<filename> instead.
"""

UNSPLASH_BASE = "https://images.unsplash.com/{photo_id}"

IMAGES = {
    "hero": {
        "photo_id": "photo-1656774950529-44a6153521ee",
        "photographer": "Morrow Solutions",
        "photographer_url": "https://unsplash.com/@morrowsolutions",
        "source_url": "https://unsplash.com/photos/a-man-lifting-weights-9W9BDUG7u9E",
        "alt": "Athlete lifting weights in a modern gym, caught mid-lift under natural studio light",
        "suggested_filename": "hero-athlete-lifting.jpg",
        "focal": "center",
    },
    "workout": {
        "photo_id": "photo-1517838277536-f5f99be501cd",
        "photographer": "Victor Freitas",
        "photographer_url": "https://unsplash.com/@victorfreitas",
        "source_url": "https://unsplash.com/photos/man-holding-black-barbell-hOuJYX2K5DA",
        "alt": "Close-up of an athlete's hand gripping a barbell during strength training",
        "suggested_filename": "workout-barbell-grip.jpg",
        "focal": "center",
    },
    "nutrition": {
        "photo_id": "photo-1768326119231-bf064c1b8fdf",
        "photographer": "Sergio Mena Ferreira",
        "photographer_url": "https://unsplash.com/@sergiomenamx",
        "source_url": "https://unsplash.com/photos/a-colorful-poke-bowl-with-tuna-avocado-and-edamame-ounjBTyK6VY",
        "alt": "Overhead view of a fresh tuna poke bowl with avocado and edamame",
        "suggested_filename": "nutrition-poke-bowl.jpg",
        "focal": "center",
    },
    "hydration": {
        "photo_id": "photo-1616556425595-93db848a50c7",
        "photographer": "Andrew R",
        "photographer_url": "https://unsplash.com/@mouldy_coffee",
        "source_url": "https://unsplash.com/photos/water-pouring-on-clear-drinking-glass-BhspCN17HT8",
        "alt": "Water pouring into a clear glass, caught mid-splash",
        "suggested_filename": "hydration-water-splash.jpg",
        "focal": "center",
    },
    "progress": {
        "photo_id": "photo-1686247167200-d74f0f24b5be",
        "photographer": "joe mcferrin",
        "photographer_url": "https://unsplash.com/@runnersathletics",
        "source_url": "https://unsplash.com/photos/a-man-lifting-a-barbell-in-a-park-s6znUip3Mro",
        "alt": "Athlete deadlifting outdoors, training consistently outside the gym",
        "suggested_filename": "progress-outdoor-training.jpg",
        "focal": "center",
    },
    "login_panel": {
        "photo_id": "photo-1517838277536-f5f99be501cd",
        "photographer": "Victor Freitas",
        "photographer_url": "https://unsplash.com/@victorfreitas",
        "source_url": "https://unsplash.com/photos/man-holding-black-barbell-hOuJYX2K5DA",
        "alt": "Athlete gripping a barbell, side panel imagery for the login page",
        "suggested_filename": "workout-barbell-grip.jpg",
        "focal": "center",
    },
    "register_panel": {
        "photo_id": "photo-1656774950529-44a6153521ee",
        "photographer": "Morrow Solutions",
        "photographer_url": "https://unsplash.com/@morrowsolutions",
        "source_url": "https://unsplash.com/photos/a-man-lifting-weights-9W9BDUG7u9E",
        "alt": "Athlete lifting weights, side panel imagery for the registration page",
        "suggested_filename": "hero-athlete-lifting.jpg",
        "focal": "center",
    },
}


def _url(photo_id: str, w: int, q: int = 75) -> str:
    return (
        f"{UNSPLASH_BASE.format(photo_id=photo_id)}"
        f"?w={w}&q={q}&auto=format&fit=crop&crop=entropy"
    )


def image_data(key: str) -> dict:
    """Return everything a template needs to render a responsive <img> for `key`."""
    entry = IMAGES[key]
    photo_id = entry["photo_id"]
    widths = [480, 800, 1200, 1600, 2000]
    srcset = ", ".join(f"{_url(photo_id, w)} {w}w" for w in widths)
    return {
        "src": _url(photo_id, 1200),
        "srcset": srcset,
        "alt": entry["alt"],
        "credit_name": entry["photographer"],
        "credit_url": entry["photographer_url"],
        "source_url": entry["source_url"],
    }
