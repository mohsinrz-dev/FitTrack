# FitTrack — Frontend Integration Guide

## Running the project

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Make sure MongoDB is running locally (default: port 27017)
# Or set the MONGO_URI environment variable:
# export MONGO_URI="mongodb://localhost:27017/"

# 3. Set a secret key (required for sessions)
# export SECRET_KEY="your-random-secret-key"

# 4. Run Flask
python app.py
# → http://localhost:5000
```

---

## File structure

```
fittrack/
├── app.py                    Flask application + all routes + chart generation
├── image_assets.py           Verified Unsplash image registry (responsive URLs, credits)
├── CREDITS.md                Full licensing/verification record for every sourced photo
├── requirements.txt
├── DESIGN.md                 Visual design system reference (light-cinematic theme)
├── FRONTEND.md               This file
├── static/
│   ├── css/
│   │   ├── system.css        Design tokens (light theme), buttons, forms, cards, modals, toasts
│   │   ├── nav.css           Top nav, sidebar, mobile drawer, app layout
│   │   ├── landing.css       Hero, pinned story section, features grid, footer
│   │   └── app.css           Dashboard, workout, nutrition, water, progress UI
│   ├── js/
│   │   ├── main.js           Nav scroll, hamburger toggle, toast utility, data-driven counters/bars
│   │   └── landing.js        GSAP hero entrance, pinned scroll-story, 3D tilt, reveals
│   └── img/
│       └── favicon.svg
└── templates/
    ├── base.html             Root HTML shell, flash messages, GSAP CDN
    ├── app_base.html         Authenticated layout: nav + sidebar + app content slot
    ├── index.html            Public landing page
    ├── login.html            Login form
    ├── register.html         Registration form
    ├── dashboard.html        Summary dashboard
    ├── workout.html          Workout tracker + log modal
    ├── nutrition.html        Diet tracker + meal modal
    ├── water.html            Hydration tracker
    ├── progress.html         Body progress log + weight chart
    ├── calculator.html       BMI / BMR / TDEE calculator
    ├── reports.html          Period-based charts (7 / 30 / 90 days)
    ├── profile.html          Profile editor + account deletion
    └── 404.html              Error page
```

---

## Flask route contract

| Method | Route | Template | Auth |
|--------|-------|----------|------|
| GET | `/` | `index.html` | — |
| GET/POST | `/register` | `register.html` | — |
| GET/POST | `/login` | `login.html` | — |
| GET | `/logout` | redirect | ✓ |
| GET | `/dashboard` | `dashboard.html` | ✓ |
| GET | `/workout` | `workout.html` | ✓ |
| POST | `/workout/log` | redirect | ✓ |
| POST | `/workout/delete/<id>` | redirect | ✓ |
| GET | `/nutrition` | `nutrition.html` | ✓ |
| POST | `/nutrition/log` | redirect | ✓ |
| POST | `/nutrition/delete/<id>` | redirect | ✓ |
| GET | `/water` | `water.html` | ✓ |
| POST | `/water/log` | redirect | ✓ |
| POST | `/water/goal` | redirect | ✓ |
| POST | `/water/delete/<id>` | redirect | ✓ |
| GET | `/progress` | `progress.html` | ✓ |
| POST | `/progress/log` | redirect | ✓ |
| POST | `/progress/delete/<id>` | redirect | ✓ |
| GET/POST | `/calculator` | `calculator.html` | ✓ |
| POST | `/calculator/apply` | redirect | ✓ |
| GET | `/reports?period=7|30|90` | `reports.html` | ✓ |
| GET/POST | `/profile` | `profile.html` | ✓ |
| POST | `/account/delete` | redirect | ✓ |

---

## Template variables

### `dashboard.html`
| Variable | Type | Description |
|----------|------|-------------|
| `today_calories` | int | Calories logged today |
| `calorie_target` | int\|None | User's calorie target |
| `workouts_this_week` | int | Workouts logged this week |
| `recent_workouts` | list | Up to 5 recent workout docs |
| `today_meals` | list | Today's meal docs |
| `water_today_ml` | int | Today's water total |
| `water_goal_ml` | int | User's daily water goal |
| `streak_days` | int | Consecutive logging days |
| `weekly_chart` | str\|None | Base64 PNG calorie chart |
| `has_any_data` | bool | Whether to show empty state |

### `workout.html`
| Variable | Type | Description |
|----------|------|-------------|
| `workouts` | list | All workout docs, newest first |
| `workouts_this_week` | int | Workouts this week |
| `total_entries` | int | Total exercises logged |
| `last_workout_date` | str\|None | Formatted last workout date |
| `volume_chart` | str\|None | Base64 PNG weekly volume bar chart |
| `muscle_chart` | str\|None | Base64 PNG muscle group horizontal bar |

### `nutrition.html`
| Variable | Type | Description |
|----------|------|-------------|
| `today_meals` | list | Today's meals |
| `all_meals` | list | Last 60 meals |
| `today_calories` | int | Calories today |
| `today_protein` | float | Protein today (g) |
| `today_carbs` | float | Carbs today (g) |
| `today_fat` | float | Fat today (g) |
| `calorie_target` | int\|None | User's calorie target |
| `macro_chart` | str\|None | Base64 PNG 7-day calorie line |

### `water.html`
| Variable | Type | Description |
|----------|------|-------------|
| `today_entries` | list | Today's water log entries |
| `water_today_ml` | int | Total ml today |
| `water_goal_ml` | int | Daily goal |
| `today_date` | str | ISO date string (YYYY-MM-DD) |
| `weekly_water_chart` | str\|None | Base64 PNG bar chart |

### `calculator.html`
| Variable | Type | Description |
|----------|------|-------------|
| `results` | dict\|None | `{bmi, bmi_cat, bmr, tdee, recommended_calories, goal}` |
| `form_*` | various | Repopulated form values |

### `reports.html`
| Variable | Type | Description |
|----------|------|-------------|
| `period` | int | 7, 30, or 90 |
| `calorie_chart` | str\|None | Base64 PNG |
| `weight_chart` | str\|None | Base64 PNG |
| `workout_chart` | str\|None | Base64 PNG |
| `water_chart` | str\|None | Base64 PNG |
| `summary` | dict | `{avg_calories, workout_count, avg_water, weight_delta}` |

---

## MongoDB collections

| Collection | Key fields |
|------------|------------|
| `users` | `name, email, password (hashed), age, gender, height, weight, goal, activity_level, calorie_target, water_goal_ml` |
| `workouts` | `user_id, exercise_name, muscle_group, sets, reps, weight_kg, duration_min, notes, date` |
| `meals` | `user_id, food_name, category, calories, protein_g, carbs_g, fat_g, date` |
| `water` | `user_id, amount_ml, date, logged_at` |
| `progress` | `user_id, weight_kg, chest_cm, waist_cm, hips_cm, arms_cm, notes, date` |

---

## External dependencies (CDN — no install)
- Google Fonts: Montserrat + Inter
- Phosphor Icons 2.1.1
- GSAP 3.12.5 + ScrollTrigger (loaded on every page via `base.html`; `landing.js` only runs its animations when the hero/story elements it targets are present, i.e. on `index.html`)
- Photography: Unsplash CDN (`images.unsplash.com`), see `CREDITS.md` for the full licensing record

## What to verify after running
1. Register → redirects to dashboard showing empty state
2. Log a workout → appears in table, delete works
3. Log a meal → calories appear in dashboard stat card; stat values count up from 0
4. Log water → fill animation updates correctly; amount counts up from 0
5. Calculator → submitting with valid stats shows BMI gauge + calorie targets (gauge needle clamps correctly at both extremes)
6. Reports page → charts render when data exists, empty states when not
7. Landing page → hero reveals on load, scrolling into "How it works" pins the image column and crossfades between the four section photos as you scroll past each text block
8. Mobile (< 1024px) → hamburger opens drawer, sidebar hides, pinned story section falls back to a static stacked layout (no pin/crossfade — this is intentional, not a bug)
9. With OS "reduce motion" enabled → all animations should skip straight to their end state; counters and progress bars should show final values immediately

## Testing performed vs. not performed (read this before assuming coverage)
This project was built and validated in a sandboxed environment with **no outbound
network access** and **no MongoDB instance**, so the following is an accurate account
of what was actually checked, not a blanket "it's tested":

**Actually executed and passing:**
- `python3 -m ast` syntax check on `app.py` and `image_assets.py`
- `image_assets.image_data()` called for all 7 registry keys and asserted to return valid Unsplash CDN URLs + non-empty srcsets
- Every template in `templates/` parsed with Jinja2 (`Environment.get_template`)
- Every template **fully rendered** with realistic mock context data (including edge cases: empty dashboard, no progress entries, calculator before/after submission across the full BMI range 14–45) — this caught and fixed a real bug (BMI gauge needle used an invalid `|min|max(0)` filter chain that threw `TypeError` whenever results were present; fixed to `[[x, 0]|max, 100]|min`)
- `node --check` on both JS files (valid syntax)
- CSS brace-balance check on all four stylesheets
- Full-project grep sweep confirming no leftover dark-theme hex values, no dead `--c-lime-dim` variable references, no unverified image URLs

**Not possible in this environment, so not claimed:**
- Running `python app.py` itself (requires `pymongo`, which has no network path to install here) or the existing `tests/test_fittrack.py` suite (requires a live MongoDB)
- Any actual browser rendering: whether the GSAP pin/crossfade looks right, whether the hero image crops well at various widths, real mobile device testing, Lighthouse/performance numbers
- Visual confirmation of the Figma screenshot (Figma's asset host isn't fetchable from here either)

**If you want that last mile covered:** run `pip install -r requirements.txt && python app.py` locally and click through the checklist above — the Jinja/Python-level testing here gives strong confidence the app won't crash, but only a browser can confirm the animations *feel* right.
