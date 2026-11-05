import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import io
import base64
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, g)
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from image_assets import image_data

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
if os.getenv('USE_FAKE_MONGO'):
    from mongofake import FakeMongoClient as MongoClient
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client['fittrack']

if not os.getenv('USE_FAKE_MONGO'):
    try:
        client.admin.command('ping')
    except Exception as exc:
        print('\n' + '=' * 70)
        print('  COULD NOT CONNECT TO MONGODB')
        print('=' * 70)
        print('  MONGO_URI is configured; connection details are hidden.')
        print(f'  Error: {exc}')
        print()
        print('  Fix this by opening the .env file in this folder and checking')
        print('  that MONGO_URI is set correctly. See START_HERE.md for steps.')
        print('=' * 70 + '\n')
        raise SystemExit(1)

users_col      = db['users']
workouts_col   = db['workouts']
meals_col      = db['meals']
water_col      = db['water']
progress_col   = db['progress']

users_col.create_index('email', unique=True)
workouts_col.create_index([('user_id', 1), ('date', -1)])
meals_col.create_index([('user_id', 1), ('date', -1)])
water_col.create_index([('user_id', 1), ('date', -1)])
progress_col.create_index([('user_id', 1), ('date', -1)])

CHART_STYLE = {
    'figure.facecolor': '#1C1D1A',
    'axes.facecolor':   '#1C1D1A',
    'axes.edgecolor':   '#2A2B27',
    'axes.labelcolor':  '#9A9B96',
    'xtick.color':      '#9A9B96',
    'ytick.color':      '#9A9B96',
    'grid.color':       '#2A2B27',
    'text.color':       '#F0EDDF',
    'lines.color':      '#C8F53A',
    'patch.facecolor':  '#C8F53A',
}

def apply_chart_style():
    for k, v in CHART_STYLE.items():
        plt.rcParams[k] = v
    plt.rcParams['font.family'] = 'DejaVu Sans'


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120, facecolor=fig.get_facecolor())
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return data


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.before_request
def load_user():
    g.current_user = None
    g.now = datetime.now()
    if 'user_id' in session:
        try:
            user = users_col.find_one({'_id': ObjectId(session['user_id'])})
        except Exception:
            user = None
        if user:
            g.current_user = user
        else:
            session.clear()


@app.context_processor
def inject_globals():
    return dict(current_user=g.current_user, now=g.now, image_data=image_data)


def calc_bmi_bmr_tdee(age, gender, height_cm, weight_kg, activity_level, goal):
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
    if bmi < 18.5:
        bmi_cat = 'Underweight'
    elif bmi < 25:
        bmi_cat = 'Normal weight'
    elif bmi < 30:
        bmi_cat = 'Overweight'
    else:
        bmi_cat = 'Obese'

    if gender == 'male':
        bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age + 5)
    else:
        bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age - 161)

    activity_mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'extra': 1.9}
    tdee = round(bmr * activity_mult.get(activity_level, 1.2))

    goal_offset = {'lose_fat': -500, 'maintain': 0, 'build_muscle': 300, 'improve_fitness': 0}
    recommended = tdee + goal_offset.get(goal, 0)

    return dict(bmi=bmi, bmi_cat=bmi_cat, bmr=bmr, tdee=tdee,
                recommended_calories=recommended, goal=goal)


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        f = request.form
        name  = f.get('name', '').strip()
        email = f.get('email', '').strip().lower()
        pwd   = f.get('password', '')

        if not name or not email or not pwd:
            return render_template('register.html', error='Please fill in all required fields.')
        if len(pwd) < 8:
            return render_template('register.html', error='Password must be at least 8 characters.')
        if users_col.find_one({'email': email}):
            return render_template('register.html', error='An account with that email already exists.')

        user_doc = {
            'name': name,
            'email': email,
            'password': generate_password_hash(pwd),
            'age': int(f.get('age') or 0) or None,
            'gender': f.get('gender') or None,
            'height': float(f.get('height') or 0) or None,
            'weight': float(f.get('weight') or 0) or None,
            'goal': f.get('goal') or None,
            'activity_level': f.get('activity_level') or None,
            'calorie_target': None,
            'water_goal_ml': 3000,
            'created_at': datetime.utcnow(),
        }
        result = users_col.insert_one(user_doc)
        session['user_id'] = str(result.inserted_id)
        flash('Account created. Welcome to FitTrack!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pwd   = request.form.get('password', '')
        user  = users_col.find_one({'email': email})
        if user and check_password_hash(user['password'], pwd):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Incorrect email or password.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    uid = ObjectId(session['user_id'])
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    today_meals = list(meals_col.find({'user_id': uid, 'date': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today + timedelta(days=1), datetime.min.time())}}))
    today_calories = sum(m.get('calories', 0) for m in today_meals)

    workouts_this_week = workouts_col.count_documents({'user_id': uid, 'date': {'$gte': datetime.combine(week_start, datetime.min.time())}})
    recent_workouts = list(workouts_col.find({'user_id': uid}).sort('date', -1).limit(5))

    water_today = list(water_col.find({'user_id': uid, 'date': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today + timedelta(days=1), datetime.min.time())}}))
    water_today_ml = sum(e.get('amount_ml', 0) for e in water_today)

    streak = _calc_streak(uid)
    weekly_chart = _weekly_calorie_chart(uid)

    has_any_data = bool(today_meals or recent_workouts or water_today)

    return render_template('dashboard.html',
        today_calories=today_calories,
        calorie_target=g.current_user.get('calorie_target'),
        workouts_this_week=workouts_this_week,
        recent_workouts=recent_workouts,
        today_meals=today_meals,
        water_today_ml=water_today_ml,
        water_goal_ml=g.current_user.get('water_goal_ml', 3000),
        streak_days=streak,
        weekly_chart=weekly_chart,
        has_any_data=has_any_data,
    )


def _calc_streak(uid):
    today = date.today()
    streak = 0
    check = today
    for _ in range(365):
        dt = datetime.combine(check, datetime.min.time())
        dt_end = datetime.combine(check + timedelta(days=1), datetime.min.time())
        has_log = (meals_col.count_documents({'user_id': uid, 'date': {'$gte': dt, '$lt': dt_end}}) or
                   workouts_col.count_documents({'user_id': uid, 'date': {'$gte': dt, '$lt': dt_end}}))
        if not has_log:
            break
        streak += 1
        check -= timedelta(days=1)
    return streak


def _weekly_calorie_chart(uid):
    apply_chart_style()
    today = date.today()
    labels, values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        dt = datetime.combine(d, datetime.min.time())
        dt_end = datetime.combine(d + timedelta(days=1), datetime.min.time())
        meals = list(meals_col.find({'user_id': uid, 'date': {'$gte': dt, '$lt': dt_end}}))
        labels.append(d.strftime('%a'))
        values.append(sum(m.get('calories', 0) for m in meals))

    if not any(values):
        return None

    fig, ax = plt.subplots(figsize=(7, 2.8))
    bars = ax.bar(labels, values, color='#C8F53A', alpha=.85, width=.6, zorder=2)
    target = g.current_user.get('calorie_target')
    if target:
        ax.axhline(y=target, color='#9A9B96', linewidth=1, linestyle='--', alpha=.6, zorder=1)
    ax.set_ylabel('kcal', fontsize=10)
    ax.tick_params(axis='both', labelsize=10)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


@app.route('/workout')
@login_required
def workout():
    uid = ObjectId(session['user_id'])
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    workouts = list(workouts_col.find({'user_id': uid}).sort('date', -1))
    workouts_this_week = sum(1 for w in workouts if w.get('date') and w['date'].date() >= week_start)
    last = workouts[0].get('date').strftime('%b %d, %Y') if workouts and workouts[0].get('date') else None

    volume_chart = _workout_volume_chart(uid)
    muscle_chart = _muscle_group_chart(uid)

    return render_template('workout.html',
        workouts=workouts,
        workouts_this_week=workouts_this_week,
        total_entries=len(workouts),
        last_workout_date=last,
        volume_chart=volume_chart,
        muscle_chart=muscle_chart,
    )


@app.route('/workout/log', methods=['POST'])
@login_required
def log_workout():
    uid = ObjectId(session['user_id'])
    f = request.form
    name = f.get('exercise_name', '').strip()
    if not name:
        flash('Exercise name is required.', 'error')
        return redirect(url_for('workout'))

    date_str = f.get('date')
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
    except ValueError:
        entry_date = datetime.utcnow()

    doc = {
        'user_id': uid,
        'exercise_name': name,
        'muscle_group': f.get('muscle_group') or None,
        'sets': int(f.get('sets')) if f.get('sets') else None,
        'reps': int(f.get('reps')) if f.get('reps') else None,
        'weight_kg': float(f.get('weight_kg')) if f.get('weight_kg') else None,
        'duration_min': int(f.get('duration_min')) if f.get('duration_min') else None,
        'notes': f.get('notes', '').strip() or None,
        'date': entry_date,
    }
    workouts_col.insert_one(doc)
    flash(f'{name} logged.', 'success')
    return redirect(url_for('workout'))


@app.route('/workout/delete/<workout_id>', methods=['POST'])
@login_required
def delete_workout(workout_id):
    uid = ObjectId(session['user_id'])
    try:
        workouts_col.delete_one({'_id': ObjectId(workout_id), 'user_id': uid})
        flash('Entry removed.', 'success')
    except Exception:
        flash('Invalid entry.', 'error')
    return redirect(url_for('workout'))


def _workout_volume_chart(uid):
    apply_chart_style()
    today = date.today()
    labels, values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        dt = datetime.combine(d, datetime.min.time())
        dt_end = datetime.combine(d + timedelta(days=1), datetime.min.time())
        entries = list(workouts_col.find({'user_id': uid, 'date': {'$gte': dt, '$lt': dt_end}}))
        vol = sum((e.get('sets', 0) or 0) * (e.get('reps', 0) or 0) * (e.get('weight_kg', 0) or 0) for e in entries)
        labels.append(d.strftime('%a'))
        values.append(round(vol))

    if not any(values):
        return None

    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    ax.bar(labels, values, color='#C8F53A', alpha=.85, width=.6, zorder=2)
    ax.set_ylabel('kg·reps', fontsize=9)
    ax.tick_params(labelsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


def _muscle_group_chart(uid):
    apply_chart_style()
    week_start = date.today() - timedelta(days=date.today().weekday())
    entries = list(workouts_col.find({'user_id': ObjectId(session['user_id']), 'date': {'$gte': datetime.combine(week_start, datetime.min.time())}}))
    counts = {}
    for e in entries:
        mg = e.get('muscle_group') or 'Other'
        counts[mg] = counts.get(mg, 0) + 1
    if not counts:
        return None
    labels = list(counts.keys())
    vals   = list(counts.values())
    colors = ['#C8F53A','#8FB52A','#F0A030','#E85C4A','#9A9B96','#3E4039','#2A2B27']
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    ax.barh(labels, vals, color=[colors[i % len(colors)] for i in range(len(labels))], zorder=2)
    ax.set_xlabel('Sets', fontsize=9)
    ax.tick_params(labelsize=9)
    ax.grid(axis='x', zorder=0)
    ax.spines[['top', 'right', 'bottom']].set_visible(False)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


@app.route('/nutrition')
@login_required
def nutrition():
    uid = ObjectId(session['user_id'])
    today = date.today()
    dt_today = datetime.combine(today, datetime.min.time())
    dt_tomorrow = datetime.combine(today + timedelta(days=1), datetime.min.time())

    today_meals = list(meals_col.find({'user_id': uid, 'date': {'$gte': dt_today, '$lt': dt_tomorrow}}).sort('date', 1))
    all_meals   = list(meals_col.find({'user_id': uid}).sort('date', -1).limit(60))

    today_calories = sum(m.get('calories', 0) for m in today_meals)
    today_protein  = round(sum(m.get('protein_g', 0) or 0 for m in today_meals), 1)
    today_carbs    = round(sum(m.get('carbs_g', 0) or 0 for m in today_meals), 1)
    today_fat      = round(sum(m.get('fat_g', 0) or 0 for m in today_meals), 1)

    macro_chart = _macro_chart(uid)

    return render_template('nutrition.html',
        today_meals=today_meals,
        all_meals=all_meals,
        today_calories=today_calories,
        today_protein=today_protein,
        today_carbs=today_carbs,
        today_fat=today_fat,
        calorie_target=g.current_user.get('calorie_target'),
        macro_chart=macro_chart,
    )


@app.route('/nutrition/log', methods=['POST'])
@login_required
def log_meal():
    uid = ObjectId(session['user_id'])
    f = request.form
    name = f.get('food_name', '').strip()
    if not name:
        flash('Food name is required.', 'error')
        return redirect(url_for('nutrition'))
    try:
        cals = int(f.get('calories') or 0)
    except ValueError:
        cals = 0

    date_str = f.get('date')
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
    except ValueError:
        entry_date = datetime.utcnow()

    doc = {
        'user_id': uid,
        'food_name': name,
        'category': f.get('category') or 'Meal',
        'calories': cals,
        'protein_g': float(f.get('protein_g') or 0) or 0,
        'carbs_g': float(f.get('carbs_g') or 0) or 0,
        'fat_g': float(f.get('fat_g') or 0) or 0,
        'date': entry_date,
    }
    meals_col.insert_one(doc)
    flash(f'{name} logged.', 'success')
    return redirect(url_for('nutrition'))


@app.route('/nutrition/delete/<meal_id>', methods=['POST'])
@login_required
def delete_meal(meal_id):
    uid = ObjectId(session['user_id'])
    try:
        meals_col.delete_one({'_id': ObjectId(meal_id), 'user_id': uid})
        flash('Meal removed.', 'success')
    except Exception:
        flash('Invalid entry.', 'error')
    return redirect(url_for('nutrition'))


def _macro_chart(uid):
    apply_chart_style()
    today = date.today()
    labels, cals = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        dt = datetime.combine(d, datetime.min.time())
        meals = list(meals_col.find({'user_id': uid, 'date': {'$gte': dt, '$lt': datetime.combine(d + timedelta(days=1), datetime.min.time())}}))
        labels.append(d.strftime('%a'))
        cals.append(sum(m.get('calories', 0) for m in meals))
    if not any(cals):
        return None
    fig, ax = plt.subplots(figsize=(5, 2.4))
    ax.plot(labels, cals, color='#C8F53A', linewidth=2, marker='o', markersize=5, zorder=2)
    ax.fill_between(labels, cals, alpha=.12, color='#C8F53A')
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(labelsize=9)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


@app.route('/water')
@login_required
def water():
    uid = ObjectId(session['user_id'])
    today = date.today()
    dt_today = datetime.combine(today, datetime.min.time())
    dt_tomorrow = datetime.combine(today + timedelta(days=1), datetime.min.time())

    today_entries = list(water_col.find({'user_id': uid, 'date': {'$gte': dt_today, '$lt': dt_tomorrow}}).sort('logged_at', 1))
    water_today_ml = sum(e.get('amount_ml', 0) for e in today_entries)
    water_goal_ml  = g.current_user.get('water_goal_ml', 3000)
    weekly_chart   = _water_chart(uid)

    return render_template('water.html',
        today_entries=today_entries,
        water_today_ml=water_today_ml,
        water_goal_ml=water_goal_ml,
        today_date=today.isoformat(),
        weekly_water_chart=weekly_chart,
    )


@app.route('/water/log', methods=['POST'])
@login_required
def log_water():
    uid = ObjectId(session['user_id'])
    f = request.form
    try:
        amount = int(f.get('amount_ml') or 0)
    except ValueError:
        amount = 0
    if amount <= 0:
        flash('Enter a valid amount.', 'error')
        return redirect(url_for('water'))

    date_str = f.get('date')
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
    except ValueError:
        entry_date = datetime.utcnow()

    doc = {
        'user_id': uid,
        'amount_ml': amount,
        'date': entry_date,
        'logged_at': datetime.utcnow(),
    }
    water_col.insert_one(doc)
    flash(f'{amount} ml logged.', 'success')
    return redirect(url_for('water'))


@app.route('/water/goal', methods=['POST'])
@login_required
def update_water_goal():
    uid = ObjectId(session['user_id'])
    try:
        goal = int(request.form.get('water_goal_ml') or 3000)
    except ValueError:
        goal = 3000
    users_col.update_one({'_id': uid}, {'$set': {'water_goal_ml': goal}})
    flash('Water goal updated.', 'success')
    return redirect(url_for('water'))


@app.route('/water/delete/<entry_id>', methods=['POST'])
@login_required
def delete_water(entry_id):
    uid = ObjectId(session['user_id'])
    try:
        water_col.delete_one({'_id': ObjectId(entry_id), 'user_id': uid})
        flash('Entry removed.', 'success')
    except Exception:
        flash('Invalid entry.', 'error')
    return redirect(url_for('water'))


def _water_chart(uid):
    apply_chart_style()
    today = date.today()
    labels, vals = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        dt = datetime.combine(d, datetime.min.time())
        entries = list(water_col.find({'user_id': uid, 'date': {'$gte': dt, '$lt': datetime.combine(d + timedelta(days=1), datetime.min.time())}}))
        labels.append(d.strftime('%a'))
        vals.append(sum(e.get('amount_ml', 0) for e in entries))
    if not any(vals):
        return None
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.bar(labels, vals, color='#C8F53A', alpha=.7, width=.6, zorder=2)
    goal = g.current_user.get('water_goal_ml', 3000)
    ax.axhline(y=goal, color='#9A9B96', linewidth=1, linestyle='--', alpha=.6, zorder=1)
    ax.set_ylabel('ml', fontsize=9)
    ax.tick_params(labelsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


@app.route('/progress')
@login_required
def progress():
    uid = ObjectId(session['user_id'])
    entries = list(progress_col.find({'user_id': uid}).sort('date', -1))
    latest      = entries[0] if entries else None
    first_entry = entries[-1] if entries else None

    weight_delta = None
    if latest and first_entry and latest.get('weight_kg') and first_entry.get('weight_kg'):
        weight_delta = round(latest['weight_kg'] - first_entry['weight_kg'], 1)

    weight_chart = _weight_chart(uid) if entries else None

    return render_template('progress.html',
        entries=entries,
        latest=latest,
        first_entry=first_entry,
        weight_delta=weight_delta,
        total_entries=len(entries),
        weight_chart=weight_chart,
        goal=g.current_user.get('goal'),
    )


@app.route('/progress/log', methods=['POST'])
@login_required
def log_progress():
    uid = ObjectId(session['user_id'])
    f = request.form
    date_str = f.get('date')
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
    except ValueError:
        entry_date = datetime.utcnow()

    doc = {
        'user_id': uid,
        'date': entry_date,
        'weight_kg':  float(f.get('weight_kg')) if f.get('weight_kg') else None,
        'chest_cm':   float(f.get('chest_cm')) if f.get('chest_cm') else None,
        'waist_cm':   float(f.get('waist_cm')) if f.get('waist_cm') else None,
        'hips_cm':    float(f.get('hips_cm')) if f.get('hips_cm') else None,
        'arms_cm':    float(f.get('arms_cm')) if f.get('arms_cm') else None,
        'notes':      f.get('notes', '').strip() or None,
    }
    progress_col.insert_one(doc)
    flash('Progress entry saved.', 'success')
    return redirect(url_for('progress'))


@app.route('/progress/delete/<entry_id>', methods=['POST'])
@login_required
def delete_progress(entry_id):
    uid = ObjectId(session['user_id'])
    try:
        progress_col.delete_one({'_id': ObjectId(entry_id), 'user_id': uid})
        flash('Entry removed.', 'success')
    except Exception:
        flash('Invalid entry.', 'error')
    return redirect(url_for('progress'))


def _weight_chart(uid):
    apply_chart_style()
    entries = list(progress_col.find({'user_id': uid, 'weight_kg': {'$ne': None}}).sort('date', 1).limit(60))
    if len(entries) < 2:
        return None
    dates  = [e['date'] for e in entries]
    weights = [e['weight_kg'] for e in entries]
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.plot(dates, weights, color='#C8F53A', linewidth=2, marker='o', markersize=4, zorder=2)
    ax.fill_between(dates, weights, min(weights) - 1, alpha=.1, color='#C8F53A')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('kg', fontsize=9)
    ax.tick_params(axis='y', labelsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


@app.route('/calculator', methods=['GET', 'POST'])
@login_required
def calculator():
    results = None
    form_data = {}
    if request.method == 'POST':
        f = request.form
        try:
            age    = int(f.get('age') or 0)
            height = float(f.get('height') or 0)
            weight = float(f.get('weight') or 0)
        except ValueError:
            flash('Please enter valid numbers.', 'error')
            return render_template('calculator.html', results=None)

        gender   = f.get('gender', 'male')
        activity = f.get('activity_level', 'sedentary')
        goal     = f.get('goal', 'maintain')

        if age and height and weight:
            results = calc_bmi_bmr_tdee(age, gender, height, weight, activity, goal)
        else:
            flash('Age, height, and weight are required.', 'error')

        form_data = {'form_age': age, 'form_gender': gender, 'form_height': height,
                     'form_weight': weight, 'form_activity': activity, 'form_goal': goal}

    return render_template('calculator.html', results=results, **form_data)


@app.route('/calculator/apply', methods=['POST'])
@login_required
def apply_calorie_target():
    uid = ObjectId(session['user_id'])
    try:
        target = int(request.form.get('calorie_target') or 0)
    except ValueError:
        target = 0
    if target:
        users_col.update_one({'_id': uid}, {'$set': {'calorie_target': target}})
        flash(f'Calorie target set to {target} kcal/day.', 'success')
    return redirect(url_for('calculator'))


@app.route('/reports')
@login_required
def reports():
    uid    = ObjectId(session['user_id'])
    try:
        period = int(request.args.get('period', 7))
    except (ValueError, TypeError):
        period = 7
    if period not in (7, 30, 90):
        period = 7
    start  = datetime.combine(date.today() - timedelta(days=period), datetime.min.time())

    calorie_chart = _period_calorie_chart(uid, start, period)
    weight_chart  = _period_weight_chart(uid, start)
    workout_chart = _period_workout_chart(uid, start, period)
    water_chart   = _period_water_chart(uid, start, period)

    meals    = list(meals_col.find({'user_id': uid, 'date': {'$gte': start}}))
    workouts = list(workouts_col.find({'user_id': uid, 'date': {'$gte': start}}))
    water    = list(water_col.find({'user_id': uid, 'date': {'$gte': start}}))
    prog     = list(progress_col.find({'user_id': uid, 'date': {'$gte': start}}).sort('date', 1))

    avg_cal   = round(sum(m.get('calories', 0) for m in meals) / period) if meals else None
    avg_water = round(sum(e.get('amount_ml', 0) for e in water) / period) if water else None
    wt_delta  = None
    if len(prog) >= 2 and prog[0].get('weight_kg') and prog[-1].get('weight_kg'):
        wt_delta = round(prog[-1]['weight_kg'] - prog[0]['weight_kg'], 1)

    summary = dict(avg_calories=avg_cal, workout_count=len(workouts),
                   avg_water=avg_water, weight_delta=wt_delta)

    return render_template('reports.html',
        period=period,
        calorie_chart=calorie_chart,
        weight_chart=weight_chart,
        workout_chart=workout_chart,
        water_chart=water_chart,
        summary=summary,
    )


def _period_calorie_chart(uid, start, period):
    apply_chart_style()
    today  = date.today()
    labels, vals = [], []
    step = max(1, period // 14)
    d = (date.today() - timedelta(days=period-1))
    while d <= today:
        dt = datetime.combine(d, datetime.min.time())
        meals = list(meals_col.find({'user_id': uid, 'date': {'$gte': dt, '$lt': datetime.combine(d + timedelta(days=1), datetime.min.time())}}))
        labels.append(d.strftime('%b %d'))
        vals.append(sum(m.get('calories', 0) for m in meals))
        d += timedelta(days=1)
    if not any(vals):
        return None
    fig, ax = plt.subplots(figsize=(7, 2.8))
    x = range(len(labels))
    ax.fill_between(x, vals, alpha=.15, color='#C8F53A')
    ax.plot(x, vals, color='#C8F53A', linewidth=1.5, zorder=2)
    visible = max(1, len(labels) // 7)
    ax.set_xticks(list(range(0, len(labels), visible)))
    ax.set_xticklabels(labels[::visible], rotation=30, ha='right', fontsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='y', labelsize=9)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


def _period_weight_chart(uid, start):
    apply_chart_style()
    entries = list(progress_col.find({'user_id': uid, 'date': {'$gte': start}, 'weight_kg': {'$ne': None}}).sort('date', 1))
    if len(entries) < 2:
        return None
    dates   = [e['date'] for e in entries]
    weights = [e['weight_kg'] for e in entries]
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.plot(dates, weights, color='#C8F53A', linewidth=2, marker='o', markersize=4, zorder=2)
    ax.fill_between(dates, weights, min(weights) - .5, alpha=.1, color='#C8F53A')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('kg', fontsize=9)
    ax.tick_params(axis='y', labelsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


def _period_workout_chart(uid, start, period):
    apply_chart_style()
    today  = date.today()
    labels, vals = [], []
    d = date.today() - timedelta(days=period-1)
    while d <= today:
        dt = datetime.combine(d, datetime.min.time())
        count = workouts_col.count_documents({'user_id': uid, 'date': {'$gte': dt, '$lt': datetime.combine(d + timedelta(days=1), datetime.min.time())}})
        labels.append(d.strftime('%b %d'))
        vals.append(count)
        d += timedelta(days=1)
    if not any(vals):
        return None
    fig, ax = plt.subplots(figsize=(7, 2.6))
    x = range(len(labels))
    ax.bar(x, vals, color='#C8F53A', alpha=.85, width=.6, zorder=2)
    visible = max(1, len(labels) // 7)
    ax.set_xticks(list(range(0, len(labels), visible)))
    ax.set_xticklabels(labels[::visible], rotation=30, ha='right', fontsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='y', labelsize=9)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


def _period_water_chart(uid, start, period):
    apply_chart_style()
    today = date.today()
    labels, vals = [], []
    d = date.today() - timedelta(days=period-1)
    while d <= today:
        dt = datetime.combine(d, datetime.min.time())
        entries = list(water_col.find({'user_id': uid, 'date': {'$gte': dt, '$lt': datetime.combine(d + timedelta(days=1), datetime.min.time())}}))
        labels.append(d.strftime('%b %d'))
        vals.append(sum(e.get('amount_ml', 0) for e in entries))
        d += timedelta(days=1)
    if not any(vals):
        return None
    fig, ax = plt.subplots(figsize=(7, 2.6))
    x = range(len(labels))
    ax.bar(x, vals, color='#C8F53A', alpha=.7, width=.6, zorder=2)
    goal = g.current_user.get('water_goal_ml', 3000)
    ax.axhline(y=goal, color='#9A9B96', linewidth=1, linestyle='--', alpha=.6)
    visible = max(1, len(labels) // 7)
    ax.set_xticks(list(range(0, len(labels), visible)))
    ax.set_xticklabels(labels[::visible], rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('ml', fontsize=9)
    ax.grid(axis='y', zorder=0)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(axis='y', labelsize=9)
    fig.tight_layout(pad=.5)
    return fig_to_b64(fig)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    uid = ObjectId(session['user_id'])
    if request.method == 'POST':
        f = request.form
        new_email = f.get('email', '').strip().lower() or g.current_user.get('email')
        if new_email != g.current_user.get('email'):
            existing = users_col.find_one({'email': new_email, '_id': {'$ne': uid}})
            if existing:
                flash('That email is already in use.', 'error')
                return redirect(url_for('profile_page'))
        update = {
            'name':           f.get('name', '').strip() or g.current_user.get('name'),
            'email':          new_email,
            'age':            int(f.get('age')) if f.get('age') else g.current_user.get('age'),
            'gender':         f.get('gender') or g.current_user.get('gender'),
            'height':         float(f.get('height')) if f.get('height') else g.current_user.get('height'),
            'weight':         float(f.get('weight')) if f.get('weight') else g.current_user.get('weight'),
            'goal':           f.get('goal') or g.current_user.get('goal'),
            'activity_level': f.get('activity_level') or g.current_user.get('activity_level'),
        }
        new_pwd = f.get('new_password', '').strip()
        if new_pwd and len(new_pwd) >= 8:
            update['password'] = generate_password_hash(new_pwd)
        users_col.update_one({'_id': uid}, {'$set': update})
        flash('Profile updated.', 'success')
        return redirect(url_for('profile_page'))
    return render_template('profile.html')


@app.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    uid = ObjectId(session['user_id'])
    workouts_col.delete_many({'user_id': uid})
    meals_col.delete_many({'user_id': uid})
    water_col.delete_many({'user_id': uid})
    progress_col.delete_many({'user_id': uid})
    users_col.delete_one({'_id': uid})
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('404.html'), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
