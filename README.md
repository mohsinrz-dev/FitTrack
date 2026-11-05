# FitTrack — Gym & Diet Management System

**B.Tech 3rd Semester Project — AI & ML Department**
RVS College of Engineering and Technology, Jamshedpur

## Team

| Name | Role |
|---|---|
| Prasanjeet Khan | Developer |
| Md Faizan | Developer |
| Nazish | Developer |
| Mohit | Developer |

## Overview

FitTrack is a web-based gym and diet management system that lets users log workouts, track nutrition and macros, monitor water intake, record body measurements, calculate BMI/BMR/TDEE, and view progress through Matplotlib-generated charts — all within a single integrated dashboard.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| Database | MongoDB or included in-memory demo mock |
| Database Driver | PyMongo |
| Charts | Matplotlib |
| Icons | Phosphor Icons (CDN) |
| Fonts | Google Fonts (Montserrat, Inter) |
| Animations | GSAP + ScrollTrigger (CDN) |

## Features

- User registration and login with hashed passwords
- Dashboard with daily calorie summary, workout count, water intake, and streak
- Workout logger with sets, reps, weight, muscle groups, and volume charts
- Diet tracker with per-meal macros (protein, carbs, fat) and calorie trends
- Hydration tracker with quick-add buttons, custom amounts, and daily goals
- Body progress tracker with weight, chest, waist, hips, and arms measurements
- BMI, BMR, and TDEE calculator (Mifflin-St Jeor formula)
- Reports page with 7-day, 30-day, and 90-day period charts
- Profile editor with password change and account deletion
- Server-side Matplotlib charts rendered as inline base64 PNGs
- Dark-themed responsive UI with GSAP scroll animations
- Secure session-based authentication with HttpOnly cookies

## Prerequisites

- Node.js 18 or later and npm
- Python 3.10 or later (the backend runs on Flask)

## Quick Demo (No MongoDB Required)

From the project folder, run:

```sh
npm install
npm run dev
```

`npm install` creates a local Python virtual environment, copies `.env.example`
to `.env`, and installs the requirements from `requirements.txt`. The app uses
the included in-memory demo database by default. Open
[http://localhost:5000](http://localhost:5000) and create an account. Demo data
is temporary and is cleared when the app stops.
To run without npm, use `python app.py` after installing `requirements.txt`.

The MongoDB setup below is only needed if you want persistent data.

## Setup Instructions (Windows)

### 1. Clone or extract the project

```powershell
cd C:\path\to\your\projects
# Extract fittrack.zip or clone the repository
```

### 2. Create a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update the values:

```powershell
copy .env.example .env
```

Edit `.env`:

```
SECRET_KEY=your-random-secret-key-here
MONGO_URI=mongodb://localhost:27017/
```

For MongoDB Atlas, use your connection string:

```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### 5. Start MongoDB

If using a local MongoDB installation:

```powershell
mongod
```

Or start the MongoDB service:

```powershell
net start MongoDB
```

### 6. Run the application

```powershell
python app.py
```

Open your browser to [http://localhost:5000](http://localhost:5000).

## Setup Instructions (Linux / macOS)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python app.py
```

## Running Tests

The test runner enables the in-memory fake database; MongoDB is not required.

```powershell
python -m pytest tests/ -v
```

Or with unittest directly:

```powershell
python -m unittest tests.test_fittrack -v
```

## Project Structure

```
fittrack/
├── app.py                  Flask application (routes, models, charts)
├── requirements.txt        Python dependencies
├── .env.example            Environment variable template
├── README.md               This file
├── DESIGN.md               Visual design system reference
├── FRONTEND.md             Frontend integration specification
├── static/
│   ├── css/
│   │   ├── system.css      Design tokens and base component styles
│   │   ├── app.css         Dashboard and app layout styles
│   │   ├── landing.css     Landing page styles
│   │   └── nav.css         Navigation and sidebar styles
│   ├── js/
│   │   ├── main.js         App-wide JS (nav toggle, toast, GSAP)
│   │   └── landing.js      Landing page animations
│   └── img/
│       └── favicon.svg     Site favicon
├── templates/
│   ├── base.html           Root template (fonts, icons, GSAP, toasts)
│   ├── app_base.html       Authenticated layout (sidebar, nav)
│   ├── index.html          Landing page
│   ├── login.html          Login page
│   ├── register.html       Registration page
│   ├── dashboard.html      Main dashboard
│   ├── workout.html        Workout tracker
│   ├── nutrition.html      Diet tracker
│   ├── water.html          Hydration tracker
│   ├── progress.html       Body progress tracker
│   ├── calculator.html     BMI/BMR/TDEE calculator
│   ├── reports.html        Period-based reports
│   ├── profile.html        User profile editor
│   └── 404.html            Error page
└── tests/
    └── test_fittrack.py    Test suite
```

## API / Route Reference

| Method | Route | Auth | Description |
|---|---|---|---|
| GET | `/` | No | Landing page (redirects to dashboard if logged in) |
| GET, POST | `/register` | No | User registration |
| GET, POST | `/login` | No | User login |
| GET | `/logout` | No | Session logout |
| GET | `/dashboard` | Yes | Main dashboard |
| GET | `/workout` | Yes | Workout list and charts |
| POST | `/workout/log` | Yes | Log a workout entry |
| POST | `/workout/delete/<id>` | Yes | Delete a workout entry |
| GET | `/nutrition` | Yes | Nutrition tracker |
| POST | `/nutrition/log` | Yes | Log a meal |
| POST | `/nutrition/delete/<id>` | Yes | Delete a meal |
| GET | `/water` | Yes | Hydration tracker |
| POST | `/water/log` | Yes | Log water intake |
| POST | `/water/goal` | Yes | Update daily water goal |
| POST | `/water/delete/<id>` | Yes | Delete a water entry |
| GET | `/progress` | Yes | Body progress tracker |
| POST | `/progress/log` | Yes | Log a body measurement |
| POST | `/progress/delete/<id>` | Yes | Delete a progress entry |
| GET, POST | `/calculator` | Yes | BMI/BMR/TDEE calculator |
| POST | `/calculator/apply` | Yes | Apply calorie target to profile |
| GET | `/reports` | Yes | Period reports (7/30/90 days) |
| GET, POST | `/profile` | Yes | Profile editor |
| POST | `/account/delete` | Yes | Delete account and all data |

## MongoDB Collections

| Collection | Key Fields |
|---|---|
| `users` | name, email, password (hashed), age, gender, height, weight, goal, activity_level, calorie_target, water_goal_ml |
| `workouts` | user_id, exercise_name, muscle_group, sets, reps, weight_kg, duration_min, date |
| `meals` | user_id, food_name, category, calories, protein_g, carbs_g, fat_g, date |
| `water` | user_id, amount_ml, date, logged_at |
| `progress` | user_id, weight_kg, chest_cm, waist_cm, hips_cm, arms_cm, notes, date |

Indexes are created automatically on application startup:
- `users.email` (unique)
- `{workouts,meals,water,progress}.(user_id, date)` (compound)

## Calculation Formulas

**BMI** = weight(kg) / (height(m))²

**BMR (Mifflin-St Jeor)**:
- Male: 10 × weight + 6.25 × height − 5 × age + 5
- Female: 10 × weight + 6.25 × height − 5 × age − 161

**TDEE** = BMR × activity multiplier
- Sedentary: 1.2 | Light: 1.375 | Moderate: 1.55 | Active: 1.725 | Extra: 1.9

**Calorie adjustment**: Lose fat (−500 kcal) | Maintain (0) | Build muscle (+300 kcal)

> These are estimates based on standard formulas. They are not medical advice. Consult a healthcare professional before making significant dietary changes.

## Known Limitations

- No CSRF token protection (acceptable for a local college project; add Flask-WTF for production)
- No email verification or password reset
- No rate limiting on login attempts
- Chart generation is synchronous and may be slow with very large datasets
- No image/photo upload for progress tracking
- External CDN dependencies (Google Fonts, Phosphor Icons, GSAP) require internet access
- No data export functionality

## Deployment Notes

- Change `SECRET_KEY` to a strong random value
- Set `debug=False` in production
- Use HTTPS in production for secure cookies
- Consider adding `SESSION_COOKIE_SECURE = True` when serving over HTTPS
- Do not commit `.env` files to version control

## License

College project — not for commercial distribution.
