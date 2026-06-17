from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import sqlite3
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

# ---------------------------------------------------------------------------
# Database — local SQLite file. No server, no network, survives restarts.
# Override location with DATABASE_PATH if you want the file elsewhere.
# ---------------------------------------------------------------------------
DB_PATH = os.getenv('DATABASE_PATH',
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lurniqhub.db'))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')   # better concurrency + speed
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def init_db():
    with get_conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            is_admin    INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS courses (
            slug        TEXT PRIMARY KEY,
            data        TEXT NOT NULL,             -- full course doc as JSON
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            user_id     TEXT NOT NULL,
            course_slug TEXT NOT NULL,
            enrolled_at TEXT NOT NULL,
            PRIMARY KEY (user_id, course_slug)
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id               TEXT PRIMARY KEY,
            nautical_miles        INTEGER NOT NULL DEFAULT 0,
            rank_name             TEXT NOT NULL DEFAULT 'Deckhand',
            rank_level            INTEGER NOT NULL DEFAULT 1,
            total_logins          INTEGER NOT NULL DEFAULT 0,
            streak_days           INTEGER NOT NULL DEFAULT 0,
            courses_enrolled      INTEGER NOT NULL DEFAULT 0,
            lessons_completed     TEXT NOT NULL DEFAULT '[]',   -- JSON array
            simulations_completed TEXT NOT NULL DEFAULT '[]',   -- JSON array
            last_login            TEXT
        );
        ''')


# ---------------------------------------------------------------------------
# Data-access helpers  (replace the old Mongo collection calls)
# ---------------------------------------------------------------------------
def find_user_by_username(username):
    with get_conn() as c:
        return c.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()


def find_user_by_id(uid):
    with get_conn() as c:
        return c.execute('SELECT * FROM users WHERE id = ?', (int(uid),)).fetchone()


def count_users():
    with get_conn() as c:
        return c.execute('SELECT COUNT(*) AS n FROM users').fetchone()['n']


def create_user(username, password_hash, is_admin):
    with get_conn() as c:
        cur = c.execute(
            'INSERT INTO users (username, password, created_at, is_admin) VALUES (?, ?, ?, ?)',
            (username, password_hash, datetime.utcnow().isoformat(), 1 if is_admin else 0),
        )
        return str(cur.lastrowid)


def ensure_stats_row(uid):
    with get_conn() as c:
        c.execute('INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)', (uid,))


def _get_stats(uid):
    with get_conn() as c:
        s = c.execute('SELECT * FROM user_stats WHERE user_id = ?', (uid,)).fetchone()
    if not s:
        return {
            'nautical_miles': 0, 'rank_name': 'Deckhand', 'rank_level': 1,
            'streak_days': 0, 'total_logins': 0, 'courses_enrolled': 0,
            'lessons_completed': [], 'simulations_completed': [],
        }
    return {
        'nautical_miles':        s['nautical_miles'],
        'rank_name':             s['rank_name'],
        'rank_level':            s['rank_level'],
        'streak_days':           s['streak_days'],
        'total_logins':          s['total_logins'],
        'courses_enrolled':      s['courses_enrolled'],
        'lessons_completed':     json.loads(s['lessons_completed'] or '[]'),
        'simulations_completed': json.loads(s['simulations_completed'] or '[]'),
    }


def _award_nm(uid, amount, reason=''):
    ensure_stats_row(uid)
    with get_conn() as c:
        c.execute('UPDATE user_stats SET nautical_miles = nautical_miles + ? WHERE user_id = ?',
                  (amount, uid))
        nm = c.execute('SELECT nautical_miles FROM user_stats WHERE user_id = ?',
                       (uid,)).fetchone()['nautical_miles']
        rank, _, _ = rank_for_miles(nm)
        c.execute('UPDATE user_stats SET rank_name = ?, rank_level = ? WHERE user_id = ?',
                  (rank['name'], rank['level'], uid))
    if reason:
        log.info('NM +%d to %s (%s) — total %d NM', amount, uid, reason, nm)
    return nm


def _add_to_array(uid, column, value):
    """Emulate Mongo $addToSet on a JSON-array column."""
    ensure_stats_row(uid)
    with get_conn() as c:
        row = c.execute(f'SELECT {column} FROM user_stats WHERE user_id = ?', (uid,)).fetchone()
        arr = json.loads(row[column] or '[]')
        if value not in arr:
            arr.append(value)
            c.execute(f'UPDATE user_stats SET {column} = ? WHERE user_id = ?',
                      (json.dumps(arr), uid))


def _seed_if_needed():
    with get_conn() as c:
        for course in SEED_COURSES:
            exists = c.execute('SELECT 1 FROM courses WHERE slug = ?',
                               (course['slug'],)).fetchone()
            if not exists:
                c.execute(
                    'INSERT INTO courses (slug, data, is_active, created_at) VALUES (?, ?, 1, ?)',
                    (course['slug'], json.dumps(course), datetime.utcnow().isoformat()),
                )


def course_by_slug(slug):
    with get_conn() as c:
        row = c.execute('SELECT data FROM courses WHERE slug = ?', (slug,)).fetchone()
    return json.loads(row['data']) if row else None


def active_courses():
    with get_conn() as c:
        rows = c.execute('SELECT data FROM courses WHERE is_active = 1').fetchall()
    return [json.loads(r['data']) for r in rows]


def enrollment_exists(uid, slug):
    with get_conn() as c:
        return c.execute('SELECT 1 FROM enrollments WHERE user_id = ? AND course_slug = ?',
                         (uid, slug)).fetchone() is not None


def list_enrollment_slugs(uid):
    with get_conn() as c:
        rows = c.execute('SELECT course_slug FROM enrollments WHERE user_id = ?', (uid,)).fetchall()
    return [r['course_slug'] for r in rows]


def add_enrollment(uid, slug):
    with get_conn() as c:
        c.execute('INSERT OR IGNORE INTO enrollments (user_id, course_slug, enrolled_at) VALUES (?, ?, ?)',
                  (uid, slug, datetime.utcnow().isoformat()))
        c.execute('UPDATE user_stats SET courses_enrolled = courses_enrolled + 1 WHERE user_id = ?',
                  (uid,))


def record_login(uid, now, streak):
    ensure_stats_row(uid)
    with get_conn() as c:
        c.execute(
            'UPDATE user_stats SET total_logins = total_logins + 1, last_login = ?, streak_days = ? '
            'WHERE user_id = ?',
            (now.isoformat(), streak, uid),
        )


def leaderboard_rows(limit):
    with get_conn() as c:
        return c.execute(
            'SELECT s.*, u.username FROM user_stats s '
            'LEFT JOIN users u ON u.id = CAST(s.user_id AS INTEGER) '
            'ORDER BY s.nautical_miles DESC LIMIT ?', (limit,)
        ).fetchall()


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def _wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return _wrap


@app.context_processor
def _inject_nav_nm():
    if 'user_id' in session:
        s = _get_stats(session['user_id'])
        return {'nav_nm': s['nautical_miles']}
    return {'nav_nm': None}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
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
            if find_user_by_username(username):
                flash('That username is already taken — try another.', 'danger')
                return redirect(url_for('register'))

            is_first = count_users() == 0
            uid = create_user(username, generate_password_hash(password), is_first)
            ensure_stats_row(uid)

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
            user = find_user_by_username(username)

            if not user or not check_password_hash(user['password'], password):
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))

            uid = str(user['id'])
            session['user_id']  = uid
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])

            now = datetime.utcnow()
            stats_row = _get_stats(uid)
            last_iso = None
            with get_conn() as c:
                r = c.execute('SELECT last_login FROM user_stats WHERE user_id = ?', (uid,)).fetchone()
                if r:
                    last_iso = r['last_login']

            streak = stats_row['streak_days']
            if last_iso:
                last = datetime.fromisoformat(last_iso)
                days_since = (now.date() - last.date()).days
                if days_since == 1:
                    streak += 1
                elif days_since > 1:
                    streak = 1
            else:
                streak = 1

            record_login(uid, now, streak)
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
    for slug in list_enrollment_slugs(uid):
        c = course_by_slug(slug)
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

    lb_raw = leaderboard_rows(10)
    leaderboard = []
    current_user_rank = None
    for i, entry in enumerate(lb_raw, 1):
        uname = entry['username'] if entry['username'] else 'Unknown'
        r, _, _ = rank_for_miles(entry['nautical_miles'] or 0)
        leaderboard.append({
            'rank_pos':       i,
            'username':       uname,
            'nautical_miles': entry['nautical_miles'] or 0,
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
    enrolled_slugs = set(list_enrollment_slugs(uid))
    stats = _get_stats(uid)
    catalog = []
    for c in active_courses():
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
    c = course_by_slug(slug)
    if not c:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses_catalog'))

    is_enrolled = enrollment_exists(uid, slug)
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
    c = course_by_slug(slug)
    if not c:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses_catalog'))

    if not enrollment_exists(uid, slug):
        add_enrollment(uid, slug)
        _award_nm(uid, NM_ENROLL, f'enrolled {slug}')
        flash(f'Enrolled in {c["title"]}! +{NM_ENROLL} NM awarded.', 'success')
    else:
        flash('Already enrolled in this course.', 'info')

    return redirect(url_for('course_detail', slug=slug))


@app.route('/courses/<slug>/module/<mod_id>/lesson/<lesson_id>')
@login_required
def lesson(slug, mod_id, lesson_id):
    uid = session['user_id']
    c = course_by_slug(slug)
    if not c:
        return redirect(url_for('courses_catalog'))
    if not enrollment_exists(uid, slug):
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

    _add_to_array(uid, 'lessons_completed', full_id)
    new_total = _award_nm(uid, NM_LESSON, f'lesson {full_id}')

    bonus = 0
    c = course_by_slug(slug)
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
    c = course_by_slug(slug)
    if not c or not c.get('simulation'):
        flash('No simulation for this course.', 'info')
        return redirect(url_for('course_detail', slug=slug))
    if not enrollment_exists(uid, slug):
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

    c = course_by_slug(slug)
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
        _add_to_array(uid, 'simulations_completed', slug)

    return jsonify({
        'ok': True, 'passed': passed, 'score': score,
        'awarded': awarded, 'pass_score': pass_score, 'already_done': already,
    })


@app.route('/leaderboard')
@login_required
def leaderboard():
    uid = session['user_id']
    lb_raw = leaderboard_rows(50)
    board = []
    current_user_rank = None
    for i, entry in enumerate(lb_raw, 1):
        uname = entry['username'] if entry['username'] else 'Unknown'
        r, _, _ = rank_for_miles(entry['nautical_miles'] or 0)
        board.append({
            'rank_pos':         i,
            'username':         uname,
            'nautical_miles':   entry['nautical_miles'] or 0,
            'rank_name':        r['name'],
            'rank_level':       r['level'],
            'courses_enrolled': entry['courses_enrolled'] or 0,
            'streak_days':      entry['streak_days'] or 0,
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
    enrolled_slugs = list_enrollment_slugs(uid)

    return render_template(
        'profile.html',
        stats=stats, nm=nm, rank=rank, next_rank=next_rank, rank_pct=rank_pct,
        enrolled_slugs=enrolled_slugs, all_ranks=RANKS,
    )


@app.route('/health')
def health():
    try:
        with get_conn() as c:
            c.execute('SELECT 1')
        db_ok = 'connected'
    except Exception:
        db_ok = 'error'
    return {'status': 'ok', 'db': db_ok}, 200


# Initialise the database as soon as the app is imported (works under
# gunicorn too, where __main__ never runs).
init_db()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))