from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import logging
from datetime import datetime
from functools import wraps

from seed_data import (
    SEED_COURSES, OPPORTUNITIES, RANKS,
    NM_ENROLL, NM_LESSON, NM_DAILY_LOGIN, NM_COURSE_COMPLETE,
    rank_for_miles,
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/lurniqhub')
client = MongoClient(MONGO_URI)
db = client.lurniqhub

users       = db.users
courses     = db.courses
enrollments = db.enrollments
user_stats  = db.user_stats

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def _wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return _wrap


def _get_stats(user_id: str) -> dict:
    s = user_stats.find_one({'user_id': user_id}) or {}
    return {
        'nautical_miles':        s.get('nautical_miles', 0),
        'rank_name':             s.get('rank_name', 'Deckhand'),
        'rank_level':            s.get('rank_level', 1),
        'streak_days':           s.get('streak_days', 0),
        'total_logins':          s.get('total_logins', 0),
        'courses_enrolled':      s.get('courses_enrolled', 0),
        'lessons_completed':     s.get('lessons_completed', []),
        'simulations_completed': s.get('simulations_completed', []),
    }


def _award_nm(user_id: str, amount: int, reason: str = '') -> int:
    user_stats.update_one(
        {'user_id': user_id},
        {'$inc': {'nautical_miles': amount}},
        upsert=True,
    )
    doc = user_stats.find_one({'user_id': user_id}) or {}
    nm = doc.get('nautical_miles', 0)
    rank, _, _ = rank_for_miles(nm)
    user_stats.update_one(
        {'user_id': user_id},
        {'$set': {'rank_name': rank['name'], 'rank_level': rank['level']}},
    )
    if reason:
        log.info('NM +%d to %s (%s) — total %d NM', amount, user_id, reason, nm)
    return nm


def _seed_if_needed():
    for c in SEED_COURSES:
        if not courses.find_one({'slug': c['slug']}):
            doc = {k: v for k, v in c.items()}
            doc['is_active'] = True
            doc['created_at'] = datetime.utcnow()
            courses.insert_one(doc)
    courses.create_index('slug', unique=True, background=True)
    users.create_index('username', unique=True, background=True)
    user_stats.create_index('user_id', unique=True, background=True)
    enrollments.create_index(
        [('user_id', 1), ('course_slug', 1)], unique=True, background=True
    )


@app.context_processor
def _inject_nav_nm():
    if 'user_id' in session:
        s = user_stats.find_one({'user_id': session['user_id']}) or {}
        return {'nav_nm': s.get('nautical_miles', 0)}
    return {'nav_nm': None}


@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if len(username) < 3:
                flash('Username must be at least 3 characters.', 'danger')
                return redirect(url_for('register'))
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('register'))
            if users.find_one({'username': username}):
                flash('That username is already taken — try another.', 'danger')
                return redirect(url_for('register'))

            is_first = users.count_documents({}) == 0
            oid = users.insert_one({
                'username': username,
                'password': generate_password_hash(password),
                'created_at': datetime.utcnow(),
                'is_admin': is_first,
            }).inserted_id

            uid = str(oid)
            user_stats.insert_one({
                'user_id': uid,
                'nautical_miles': 0,
                'rank_name': 'Deckhand',
                'rank_level': 1,
                'total_logins': 0,
                'streak_days': 0,
                'courses_enrolled': 0,
                'lessons_completed': [],
                'simulations_completed': [],
            })

            flash('Account created — welcome aboard! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception:
            log.exception('Registration error')
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = users.find_one({'username': username})

            if not user or not check_password_hash(user['password'], password):
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))

            uid = str(user['_id'])
            session['user_id']  = uid
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)

            now  = datetime.utcnow()
            stat = user_stats.find_one({'user_id': uid}) or {}
            last = stat.get('last_login')
            streak = stat.get('streak_days', 0)
            if last:
                days_since = (now.date() - last.date()).days
                if days_since == 1:
                    streak += 1
                elif days_since > 1:
                    streak = 1
            else:
                streak = 1

            user_stats.update_one(
                {'user_id': uid},
                {'$inc': {'total_logins': 1},
                 '$set': {'last_login': now, 'streak_days': streak}},
                upsert=True,
            )
            _award_nm(uid, NM_DAILY_LOGIN, 'daily login')

            flash(f'Welcome back, {username}! ⚓', 'success')
            return redirect(url_for('dashboard'))

        except Exception:
            log.exception('Login error')
            flash('Something went wrong. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out. Fair winds!', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    _seed_if_needed()
    uid = session['user_id']
    stats = _get_stats(uid)
    nm = stats['nautical_miles']
    rank, next_rank, rank_pct = rank_for_miles(nm)

    enrolled_docs = []
    for enr in enrollments.find({'user_id': uid}):
        slug = enr['course_slug']
        c = courses.find_one({'slug': slug})
        if not c:
            continue
        lesson_count = sum(len(m['lessons']) for m in c.get('modules', []))
        done = len([l for l in stats['lessons_completed'] if l.startswith(slug + '/')])
        progress = int(100 * done / lesson_count) if lesson_count else 0
        enrolled_docs.append({
            'slug':         slug,
            'title':        c['title'],
            'tagline':      c.get('tagline', ''),
            'category':     c.get('category', ''),
            'grade_level':  c.get('grade_level', ''),
            'icon':         c.get('icon', 'school'),
            'theme':        c.get('theme', {'from': '#1976D2', 'to': '#006994'}),
            'progress':     progress,
            'lesson_count': lesson_count,
            'done':         done,
        })

    lb_raw = list(user_stats.find().sort('nautical_miles', DESCENDING).limit(10))
    leaderboard = []
    current_user_rank = None
    for i, entry in enumerate(lb_raw, 1):
        try:
            u = users.find_one({'_id': ObjectId(entry['user_id'])})
        except Exception:
            u = None
        uname = u['username'] if u else 'Unknown'
        r, _, _ = rank_for_miles(entry.get('nautical_miles', 0))
        leaderboard.append({
            'rank_pos':       i,
            'username':       uname,
            'nautical_miles': entry.get('nautical_miles', 0),
            'rank_name':      r['name'],
            'rank_level':     r['level'],
            'is_current':     entry['user_id'] == uid,
        })
        if entry['user_id'] == uid:
            current_user_rank = i

    return render_template(
        'dashboard.html',
        stats=stats, nm=nm, rank=rank, next_rank=next_rank, rank_pct=rank_pct,
        enrolled_courses=enrolled_docs, leaderboard=leaderboard,
        current_user_rank=current_user_rank,
    )


@app.route('/courses')
@login_required
def courses_catalog():
    _seed_if_needed()
    uid = session['user_id']
    enrolled_slugs = {e['course_slug'] for e in enrollments.find({'user_id': uid})}
    stats = _get_stats(uid)
    catalog = []
    for c in courses.find({'is_active': True}):
        slug = c['slug']
        lesson_count = sum(len(m['lessons']) for m in c.get('modules', []))
        done = len([l for l in stats['lessons_completed'] if l.startswith(slug + '/')])
        progress = int(100 * done / lesson_count) if lesson_count else 0
        catalog.append({
            'slug':           slug,
            'title':          c['title'],
            'tagline':        c.get('tagline', ''),
            'category':       c.get('category', ''),
            'grade_level':    c.get('grade_level', ''),
            'difficulty':     c.get('difficulty', 'Beginner'),
            'icon':           c.get('icon', 'school'),
            'theme':          c.get('theme', {'from': '#1976D2', 'to': '#006994'}),
            'lesson_count':   lesson_count,
            'module_count':   len(c.get('modules', [])),
            'has_simulation': bool(c.get('simulation')),
            'is_enrolled':    slug in enrolled_slugs,
            'progress':       progress,
            'done':           done,
        })
    categories = sorted({c['category'] for c in catalog})
    return render_template('courses.html', catalog=catalog, categories=categories)


@app.route('/courses/<slug>')
@login_required
def course_detail(slug):
    _seed_if_needed()
    uid = session['user_id']
    c = courses.find_one({'slug': slug})
    if not c:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses_catalog'))

    is_enrolled = bool(enrollments.find_one({'user_id': uid, 'course_slug': slug}))
    stats = _get_stats(uid)
    completed_ids = set(stats['lessons_completed'])

    modules_out = []
    total_lessons = 0
    for m in c.get('modules', []):
        lessons_out = []
        for l in m['lessons']:
            total_lessons += 1
            full_id = f"{slug}/{m['id']}/{l['id']}"
            lessons_out.append({**l, 'full_id': full_id, 'done': full_id in completed_ids})
        modules_out.append({**m, 'lessons': lessons_out})

    done_count = len([l for l in completed_ids if l.startswith(slug + '/')])
    sim_done = slug in stats.get('simulations_completed', [])

    return render_template(
        'course_detail.html',
        course=c, modules=modules_out, is_enrolled=is_enrolled,
        total_lessons=total_lessons, done_count=done_count, sim_done=sim_done,
    )


@app.route('/courses/<slug>/enroll', methods=['POST'])
@login_required
def enroll_course(slug):
    uid = session['user_id']
    c = courses.find_one({'slug': slug})
    if not c:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses_catalog'))

    if not enrollments.find_one({'user_id': uid, 'course_slug': slug}):
        enrollments.insert_one({
            'user_id':     uid,
            'course_slug': slug,
            'enrolled_at': datetime.utcnow(),
        })
        user_stats.update_one(
            {'user_id': uid},
            {'$inc': {'courses_enrolled': 1}},
            upsert=True,
        )
        _award_nm(uid, NM_ENROLL, f'enrolled {slug}')
        flash(f'Enrolled in {c["title"]}! +{NM_ENROLL} NM awarded.', 'success')
    else:
        flash('Already enrolled in this course.', 'info')

    return redirect(url_for('course_detail', slug=slug))


@app.route('/courses/<slug>/module/<mod_id>/lesson/<lesson_id>')
@login_required
def lesson(slug, mod_id, lesson_id):
    uid = session['user_id']
    c = courses.find_one({'slug': slug})
    if not c:
        return redirect(url_for('courses_catalog'))
    if not enrollments.find_one({'user_id': uid, 'course_slug': slug}):
        flash('Enrol in this course first.', 'warning')
        return redirect(url_for('course_detail', slug=slug))

    module = next((m for m in c['modules'] if m['id'] == mod_id), None)
    if not module:
        return redirect(url_for('course_detail', slug=slug))
    lesson_doc = next((l for l in module['lessons'] if l['id'] == lesson_id), None)
    if not lesson_doc:
        return redirect(url_for('course_detail', slug=slug))

    stats = _get_stats(uid)
    full_id = f'{slug}/{mod_id}/{lesson_id}'
    is_done = full_id in stats['lessons_completed']

    flat = [(m['id'], l['id']) for m in c['modules'] for l in m['lessons']]
    idx = next((i for i, (m, l) in enumerate(flat) if m == mod_id and l == lesson_id), 0)
    prev_l = flat[idx - 1] if idx > 0 else None
    next_l = flat[idx + 1] if idx < len(flat) - 1 else None

    return render_template(
        'lesson.html',
        course=c, module=module, lesson=lesson_doc, full_id=full_id,
        is_done=is_done, prev_lesson=prev_l, next_lesson=next_l,
        nm_reward=NM_LESSON, lesson_index=idx + 1, total_lessons=len(flat),
    )


@app.route('/courses/<slug>/module/<mod_id>/lesson/<lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(slug, mod_id, lesson_id):
    uid = session['user_id']
    full_id = f'{slug}/{mod_id}/{lesson_id}'
    stats = _get_stats(uid)

    if full_id in stats['lessons_completed']:
        return jsonify({'awarded': 0, 'already_done': True, 'ok': True})

    user_stats.update_one(
        {'user_id': uid},
        {'$addToSet': {'lessons_completed': full_id}},
        upsert=True,
    )
    new_total = _award_nm(uid, NM_LESSON, f'lesson {full_id}')

    bonus = 0
    c = courses.find_one({'slug': slug})
    if c:
        lesson_count = sum(len(m['lessons']) for m in c.get('modules', []))
        stats2 = _get_stats(uid)
        done = len([l for l in stats2['lessons_completed'] if l.startswith(slug + '/')])
        if done >= lesson_count:
            bonus = NM_COURSE_COMPLETE
            _award_nm(uid, bonus, f'course complete {slug}')
            new_total += bonus

    rank, _, _ = rank_for_miles(new_total)
    return jsonify({
        'ok': True, 'awarded': NM_LESSON, 'bonus': bonus,
        'total_nm': new_total, 'rank': rank['name'],
    })


@app.route('/courses/<slug>/simulation')
@login_required
def simulation(slug):
    uid = session['user_id']
    c = courses.find_one({'slug': slug})
    if not c or not c.get('simulation'):
        flash('No simulation for this course.', 'info')
        return redirect(url_for('course_detail', slug=slug))
    if not enrollments.find_one({'user_id': uid, 'course_slug': slug}):
        flash('Enrol in this course first.', 'warning')
        return redirect(url_for('course_detail', slug=slug))

    stats = _get_stats(uid)
    sim = c['simulation']
    sim_done = slug in stats.get('simulations_completed', [])
    sim_config_json = json.dumps(sim['config'])

    return render_template(
        'simulation.html',
        course=c, sim=sim, sim_done=sim_done, sim_config_json=sim_config_json,
        max_nm=sim.get('max_nm', 60), pass_score=sim.get('pass_score', 60),
    )


@app.route('/courses/<slug>/simulation/submit', methods=['POST'])
@login_required
def submit_simulation(slug):
    uid = session['user_id']
    data = request.get_json(silent=True) or {}
    score = max(0, min(100, int(data.get('score', 0))))

    c = courses.find_one({'slug': slug})
    if not c or not c.get('simulation'):
        return jsonify({'ok': False, 'error': 'not found'})

    sim = c['simulation']
    pass_score = sim.get('pass_score', 60)
    max_nm = sim.get('max_nm', 60)
    passed = score >= pass_score

    stats = _get_stats(uid)
    already = slug in stats.get('simulations_completed', [])
    awarded = 0

    if passed and not already:
        awarded = int(max_nm * score / 100)
        _award_nm(uid, awarded, f'sim {slug} score {score}')
        user_stats.update_one(
            {'user_id': uid},
            {'$addToSet': {'simulations_completed': slug}},
            upsert=True,
        )

    return jsonify({
        'ok': True, 'passed': passed, 'score': score,
        'awarded': awarded, 'pass_score': pass_score, 'already_done': already,
    })


@app.route('/leaderboard')
@login_required
def leaderboard():
    uid = session['user_id']
    lb_raw = list(user_stats.find().sort('nautical_miles', DESCENDING).limit(50))
    board = []
    current_user_rank = None
    for i, entry in enumerate(lb_raw, 1):
        try:
            u = users.find_one({'_id': ObjectId(entry['user_id'])})
        except Exception:
            u = None
        uname = u['username'] if u else 'Unknown'
        r, _, _ = rank_for_miles(entry.get('nautical_miles', 0))
        board.append({
            'rank_pos':         i,
            'username':         uname,
            'nautical_miles':   entry.get('nautical_miles', 0),
            'rank_name':        r['name'],
            'rank_level':       r['level'],
            'courses_enrolled': entry.get('courses_enrolled', 0),
            'streak_days':      entry.get('streak_days', 0),
            'is_current':       entry['user_id'] == uid,
        })
        if entry['user_id'] == uid:
            current_user_rank = i

    return render_template('leaderboard.html', board=board, current_user_rank=current_user_rank)


@app.route('/opportunities')
@login_required
def opportunities():
    return render_template('opportunities.html', sections=OPPORTUNITIES)


@app.route('/profile')
@login_required
def profile():
    uid = session['user_id']
    stats = _get_stats(uid)
    nm = stats['nautical_miles']
    rank, next_rank, rank_pct = rank_for_miles(nm)
    enrolled = list(enrollments.find({'user_id': uid}))
    enrolled_slugs = [e['course_slug'] for e in enrolled]

    return render_template(
        'profile.html',
        stats=stats, nm=nm, rank=rank, next_rank=next_rank, rank_pct=rank_pct,
        enrolled_slugs=enrolled_slugs, all_ranks=RANKS,
    )


@app.route('/health')
def health():
    try:
        client.server_info()
        db_ok = 'connected'
    except Exception:
        db_ok = 'error'
    return {'status': 'ok', 'db': db_ok}, 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
