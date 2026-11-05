import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
os.environ['USE_FAKE_MONGO'] = '1'
os.environ['SECRET_KEY'] = 'test-secret-key'

from app import app, db, client, users_col, workouts_col, meals_col, water_col, progress_col, calc_bmi_bmr_tdee
from werkzeug.security import generate_password_hash
from bson import ObjectId
from datetime import datetime, date, timedelta


TEST_DB_NAME = 'fittrack_test'


class FitTrackTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        global db, users_col, workouts_col, meals_col, water_col, progress_col
        import app as app_module
        app_module.db = client[TEST_DB_NAME]
        app_module.users_col = app_module.db['users']
        app_module.workouts_col = app_module.db['workouts']
        app_module.meals_col = app_module.db['meals']
        app_module.water_col = app_module.db['water']
        app_module.progress_col = app_module.db['progress']
        db = app_module.db
        users_col = app_module.users_col
        workouts_col = app_module.workouts_col
        meals_col = app_module.meals_col
        water_col = app_module.water_col
        progress_col = app_module.progress_col

    def setUp(self):
        self.client = app.test_client()
        db.users.drop()
        db.workouts.drop()
        db.meals.drop()
        db.water.drop()
        db.progress.drop()

    @classmethod
    def tearDownClass(cls):
        client.drop_database(TEST_DB_NAME)

    def _register(self, name='Test User', email='test@example.com', password='password123', age='25', gender='male', height='175', weight='70', goal='maintain', activity_level='moderate'):
        return self.client.post('/register', data=dict(
            name=name, email=email, password=password,
            age=age, gender=gender, height=height, weight=weight,
            goal=goal, activity_level=activity_level
        ), follow_redirects=True)

    def _login(self, email='test@example.com', password='password123'):
        return self.client.post('/login', data=dict(
            email=email, password=password
        ), follow_redirects=True)

    def _logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_register_success(self):
        rv = self._register()
        self.assertEqual(rv.status_code, 200)
        user = users_col.find_one({'email': 'test@example.com'})
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], 'Test User')

    def test_register_duplicate_email(self):
        self._register()
        self._logout()
        rv = self.client.post('/register', data=dict(
            name='Another', email='test@example.com', password='password123',
            age='25', gender='male', height='175', weight='70',
            goal='maintain', activity_level='moderate'
        ), follow_redirects=True)
        self.assertIn(b'already exists', rv.data)

    def test_register_short_password(self):
        rv = self.client.post('/register', data=dict(
            name='Test', email='short@example.com', password='short',
            age='25', gender='male', height='175', weight='70',
            goal='maintain', activity_level='moderate'
        ), follow_redirects=True)
        self.assertIn(b'at least 8 characters', rv.data)

    def test_register_missing_fields(self):
        rv = self.client.post('/register', data=dict(
            name='', email='', password=''
        ), follow_redirects=True)
        self.assertIn(b'fill in all', rv.data)

    def test_login_success(self):
        self._register()
        self._logout()
        rv = self._login()
        self.assertEqual(rv.status_code, 200)

    def test_login_wrong_password(self):
        self._register()
        self._logout()
        rv = self._login(password='wrongpassword')
        self.assertIn(b'Incorrect', rv.data)

    def test_login_nonexistent_email(self):
        rv = self._login(email='nobody@example.com')
        self.assertIn(b'Incorrect', rv.data)

    def test_logout_clears_session(self):
        self._register()
        rv = self._logout()
        self.assertEqual(rv.status_code, 200)
        rv = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_dashboard(self):
        rv = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_workout(self):
        rv = self.client.get('/workout', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_nutrition(self):
        rv = self.client.get('/nutrition', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_water(self):
        rv = self.client.get('/water', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_progress(self):
        rv = self.client.get('/progress', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_calculator(self):
        rv = self.client.get('/calculator', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_reports(self):
        rv = self.client.get('/reports', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_access_control_profile(self):
        rv = self.client.get('/profile', follow_redirects=True)
        self.assertIn(b'Log in', rv.data)

    def test_password_hashing(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        self.assertNotEqual(user['password'], 'password123')
        self.assertTrue(user['password'].startswith('scrypt:') or user['password'].startswith('pbkdf2:'))

    def test_log_workout(self):
        self._register()
        today = date.today().isoformat()
        rv = self.client.post('/workout/log', data=dict(
            exercise_name='Bench Press', muscle_group='Chest',
            sets='3', reps='10', weight_kg='60',
            duration_min='45', date=today, notes='Good session'
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(workouts_col.count_documents({}), 1)
        w = workouts_col.find_one({})
        self.assertEqual(w['exercise_name'], 'Bench Press')
        self.assertEqual(w['sets'], 3)

    def test_delete_workout(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        wid = workouts_col.insert_one({
            'user_id': user['_id'], 'exercise_name': 'Squat',
            'sets': 3, 'reps': 10, 'weight_kg': 80, 'date': datetime.utcnow()
        }).inserted_id
        rv = self.client.post(f'/workout/delete/{wid}', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(workouts_col.count_documents({}), 0)

    def test_log_meal(self):
        self._register()
        today = date.today().isoformat()
        rv = self.client.post('/nutrition/log', data=dict(
            food_name='Chicken Breast', category='Lunch',
            calories='350', protein_g='40', carbs_g='0', fat_g='8', date=today
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(meals_col.count_documents({}), 1)
        m = meals_col.find_one({})
        self.assertEqual(m['food_name'], 'Chicken Breast')
        self.assertEqual(m['calories'], 350)

    def test_delete_meal(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        mid = meals_col.insert_one({
            'user_id': user['_id'], 'food_name': 'Rice',
            'calories': 200, 'date': datetime.utcnow()
        }).inserted_id
        rv = self.client.post(f'/nutrition/delete/{mid}', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(meals_col.count_documents({}), 0)

    def test_log_water(self):
        self._register()
        today = date.today().isoformat()
        rv = self.client.post('/water/log', data=dict(
            amount_ml='500', date=today
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(water_col.count_documents({}), 1)

    def test_log_water_invalid(self):
        self._register()
        rv = self.client.post('/water/log', data=dict(
            amount_ml='0'
        ), follow_redirects=True)
        self.assertEqual(water_col.count_documents({}), 0)

    def test_delete_water(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        wid = water_col.insert_one({
            'user_id': user['_id'], 'amount_ml': 500,
            'date': datetime.utcnow(), 'logged_at': datetime.utcnow()
        }).inserted_id
        rv = self.client.post(f'/water/delete/{wid}', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(water_col.count_documents({}), 0)

    def test_update_water_goal(self):
        self._register()
        rv = self.client.post('/water/goal', data=dict(
            water_goal_ml='4000'
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        user = users_col.find_one({'email': 'test@example.com'})
        self.assertEqual(user['water_goal_ml'], 4000)

    def test_log_progress(self):
        self._register()
        today = date.today().isoformat()
        rv = self.client.post('/progress/log', data=dict(
            date=today, weight_kg='75', chest_cm='95',
            waist_cm='80', hips_cm='90', arms_cm='35', notes='Feeling good'
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(progress_col.count_documents({}), 1)

    def test_delete_progress(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        pid = progress_col.insert_one({
            'user_id': user['_id'], 'weight_kg': 75, 'date': datetime.utcnow()
        }).inserted_id
        rv = self.client.post(f'/progress/delete/{pid}', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(progress_col.count_documents({}), 0)

    def test_bmi_calculation(self):
        result = calc_bmi_bmr_tdee(25, 'male', 175, 70, 'moderate', 'maintain')
        self.assertAlmostEqual(result['bmi'], 22.9, places=1)
        self.assertEqual(result['bmi_cat'], 'Normal weight')

    def test_bmr_male(self):
        result = calc_bmi_bmr_tdee(25, 'male', 175, 70, 'sedentary', 'maintain')
        expected_bmr = round(10 * 70 + 6.25 * 175 - 5 * 25 + 5)
        self.assertEqual(result['bmr'], expected_bmr)

    def test_bmr_female(self):
        result = calc_bmi_bmr_tdee(25, 'female', 165, 60, 'sedentary', 'maintain')
        expected_bmr = round(10 * 60 + 6.25 * 165 - 5 * 25 - 161)
        self.assertEqual(result['bmr'], expected_bmr)

    def test_tdee_sedentary(self):
        result = calc_bmi_bmr_tdee(25, 'male', 175, 70, 'sedentary', 'maintain')
        self.assertEqual(result['tdee'], round(result['bmr'] * 1.2))

    def test_calorie_target_lose_fat(self):
        result = calc_bmi_bmr_tdee(25, 'male', 175, 70, 'moderate', 'lose_fat')
        self.assertEqual(result['recommended_calories'], result['tdee'] - 500)

    def test_calorie_target_build_muscle(self):
        result = calc_bmi_bmr_tdee(25, 'male', 175, 70, 'moderate', 'build_muscle')
        self.assertEqual(result['recommended_calories'], result['tdee'] + 300)

    def test_bmi_categories(self):
        underweight = calc_bmi_bmr_tdee(25, 'male', 175, 50, 'sedentary', 'maintain')
        self.assertEqual(underweight['bmi_cat'], 'Underweight')
        normal = calc_bmi_bmr_tdee(25, 'male', 175, 70, 'sedentary', 'maintain')
        self.assertEqual(normal['bmi_cat'], 'Normal weight')
        overweight = calc_bmi_bmr_tdee(25, 'male', 175, 85, 'sedentary', 'maintain')
        self.assertEqual(overweight['bmi_cat'], 'Overweight')
        obese = calc_bmi_bmr_tdee(25, 'male', 175, 110, 'sedentary', 'maintain')
        self.assertEqual(obese['bmi_cat'], 'Obese')

    def test_calculator_page(self):
        self._register()
        rv = self.client.post('/calculator', data=dict(
            age='25', gender='male', height='175', weight='70',
            activity_level='moderate', goal='maintain'
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'BMI', rv.data)
        self.assertIn(b'BMR', rv.data)

    def test_apply_calorie_target(self):
        self._register()
        rv = self.client.post('/calculator/apply', data=dict(
            calorie_target='2200'
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        user = users_col.find_one({'email': 'test@example.com'})
        self.assertEqual(user['calorie_target'], 2200)

    def test_data_isolation(self):
        self._register(name='User One', email='one@example.com')
        user1 = users_col.find_one({'email': 'one@example.com'})
        workouts_col.insert_one({
            'user_id': user1['_id'], 'exercise_name': 'User1 Workout',
            'sets': 3, 'reps': 10, 'date': datetime.utcnow()
        })
        self._logout()
        self._register(name='User Two', email='two@example.com')
        rv = self.client.get('/workout')
        self.assertNotIn(b'User1 Workout', rv.data)

    def test_delete_workout_invalid_id(self):
        self._register()
        rv = self.client.post('/workout/delete/invalid-id', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

    def test_delete_meal_invalid_id(self):
        self._register()
        rv = self.client.post('/nutrition/delete/invalid-id', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

    def test_empty_dashboard(self):
        self._register()
        rv = self.client.get('/dashboard')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Your dashboard is ready', rv.data)

    def test_empty_workout_page(self):
        self._register()
        rv = self.client.get('/workout')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'No exercises logged', rv.data)

    def test_empty_nutrition_page(self):
        self._register()
        rv = self.client.get('/nutrition')
        self.assertEqual(rv.status_code, 200)

    def test_empty_progress_page(self):
        self._register()
        rv = self.client.get('/progress')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Nothing tracked yet', rv.data)

    def test_water_totals(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        today = datetime.combine(date.today(), datetime.min.time())
        water_col.insert_many([
            {'user_id': user['_id'], 'amount_ml': 250, 'date': today, 'logged_at': datetime.utcnow()},
            {'user_id': user['_id'], 'amount_ml': 500, 'date': today, 'logged_at': datetime.utcnow()},
            {'user_id': user['_id'], 'amount_ml': 330, 'date': today, 'logged_at': datetime.utcnow()},
        ])
        rv = self.client.get('/water')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'1080', rv.data)

    def test_reports_valid_periods(self):
        self._register()
        for period in [7, 30, 90]:
            rv = self.client.get(f'/reports?period={period}')
            self.assertEqual(rv.status_code, 200)

    def test_reports_invalid_period(self):
        self._register()
        rv = self.client.get('/reports?period=abc')
        self.assertEqual(rv.status_code, 200)
        rv = self.client.get('/reports?period=0')
        self.assertEqual(rv.status_code, 200)

    def test_workout_no_name(self):
        self._register()
        rv = self.client.post('/workout/log', data=dict(
            exercise_name='', sets='3', reps='10'
        ), follow_redirects=True)
        self.assertEqual(workouts_col.count_documents({}), 0)

    def test_meal_no_name(self):
        self._register()
        rv = self.client.post('/nutrition/log', data=dict(
            food_name='', calories='100'
        ), follow_redirects=True)
        self.assertEqual(meals_col.count_documents({}), 0)

    def test_profile_update(self):
        self._register()
        rv = self.client.post('/profile', data=dict(
            name='Updated Name', email='test@example.com',
            age='30', gender='male', height='180', weight='75',
            goal='build_muscle', activity_level='active'
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        user = users_col.find_one({'email': 'test@example.com'})
        self.assertEqual(user['name'], 'Updated Name')
        self.assertEqual(user['age'], 30)

    def test_delete_account(self):
        self._register()
        user = users_col.find_one({'email': 'test@example.com'})
        workouts_col.insert_one({'user_id': user['_id'], 'exercise_name': 'Test', 'date': datetime.utcnow()})
        meals_col.insert_one({'user_id': user['_id'], 'food_name': 'Test', 'calories': 100, 'date': datetime.utcnow()})
        rv = self.client.post('/account/delete', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIsNone(users_col.find_one({'email': 'test@example.com'}))
        self.assertEqual(workouts_col.count_documents({}), 0)
        self.assertEqual(meals_col.count_documents({}), 0)

    def test_404_page(self):
        rv = self.client.get('/nonexistent-page')
        self.assertEqual(rv.status_code, 404)

    def test_index_redirects_when_logged_in(self):
        self._register()
        rv = self.client.get('/', follow_redirects=False)
        self.assertEqual(rv.status_code, 302)
        self.assertIn('/dashboard', rv.headers['Location'])

    def test_landing_page(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'FitTrack', rv.data)


if __name__ == '__main__':
    unittest.main()
