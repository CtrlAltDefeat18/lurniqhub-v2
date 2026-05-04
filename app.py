from flask import Flask, render_template, session, redirect, url_for, request, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from functools import wraps

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# MongoDB Connection
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/lurniqhub')
client = MongoClient(MONGO_URI)
db = client.lurniqhub

# Collections
users = db.users
courses = db.courses
enrollments = db.enrollments
user_stats = db.user_stats

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if len(username) < 3:
            flash('Username must be at least 3 characters', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect(url_for('register'))
        
        # Check if username exists
        if users.find_one({'username': username}):
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
        
        # Create user
        user_id = users.insert_one({
            'username': username,
            'password': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'is_admin': users.count_documents({}) == 0  # First user is admin
        }).inserted_id
        
        # Create initial stats
        user_stats.insert_one({
            'user_id': str(user_id),
            'nautical_miles': 0,
            'rank_name': 'Deckhand',
            'rank_level': 1,
            'total_logins': 0,
            'streak_days': 0,
            'courses_enrolled': 0
        })
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            
            # Update login stats
            user_stats.update_one(
                {'user_id': str(user['_id'])},
                {'$inc': {'total_logins': 1}}
            )
            
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials', 'danger')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

# ============================================================================
# DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    # Get user stats
    stats = user_stats.find_one({'user_id': user_id}) or {
        'nautical_miles': 0,
        'rank_name': 'Deckhand',
        'rank_level': 1,
        'streak_days': 0,
        'courses_enrolled': 0
    }
    
    # Get enrolled courses
    enrolled = list(enrollments.find({'user_id': user_id}))
    enrolled_courses = []
    for e in enrolled:
        course = courses.find_one({'_id': e['course_id']})
        if course:
            enrolled_courses.append({
                **course,
                'progress': e.get('progress', 0)
            })
    
    # Global leaderboard
    leaderboard = list(user_stats.find().sort('nautical_miles', -1).limit(10))
    for entry in leaderboard:
        user = users.find_one({'_id': entry['user_id']})
        entry['username'] = user['username'] if user else 'Unknown'
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         enrolled_courses=enrolled_courses,
                         leaderboard=leaderboard)

# ============================================================================
# COURSES
# ============================================================================

@app.route('/courses')
@login_required
def courses_catalog():
    all_courses = list(courses.find({'is_active': True}))
    return render_template('courses.html', courses=all_courses)

@app.route('/courses/<course_id>/enroll')
@login_required
def enroll_course(course_id):
    user_id = session['user_id']
    
    # Check if already enrolled
    if enrollments.find_one({'user_id': user_id, 'course_id': course_id}):
        flash('Already enrolled in this course', 'info')
    else:
        enrollments.insert_one({
            'user_id': user_id,
            'course_id': course_id,
            'enrolled_at': datetime.utcnow(),
            'progress': 0
        })
        user_stats.update_one(
            {'user_id': user_id},
            {'$inc': {'courses_enrolled': 1}}
        )
        flash('Successfully enrolled!', 'success')
    
    return redirect(url_for('courses_catalog'))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health')
def health():
    return {'status': 'ok', 'db': 'connected' if client.server_info() else 'disconnected'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
