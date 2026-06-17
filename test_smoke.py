"""
LurniqHub smoke test — run this any time to prove the app works end to end.

    python test_smoke.py

It uses a TEMPORARY database (test_smoke.db), so it never touches your real
lurniqhub.db. Safe to run in front of a friend, collaborator, or examiner.
Exits 0 and prints "ALL CHECKS PASSED" if everything is healthy.
"""
import os
import sys
import tempfile

# Point the app at a throwaway DB BEFORE importing it (app.py builds the DB on import).
_TEST_DB = os.path.join(tempfile.gettempdir(), 'lurniqhub_smoke_test.db')
for ext in ('', '-wal', '-shm'):
    try: os.remove(_TEST_DB + ext)
    except OSError: pass
os.environ['DATABASE_PATH'] = _TEST_DB

import app as appmod  # noqa: E402

PASS, FAIL = 0, 0

def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  \u2713 {label}")
    else:
        FAIL += 1
        print(f"  \u2717 {label}   <-- FAILED")

def main():
    appmod.init_db()
    appmod._seed_if_needed()

    courses = appmod.active_courses()
    check(f"course catalogue seeded ({len(courses)} courses)", len(courses) > 0)

    course = courses[0]
    slug = course['slug']
    mod = course['modules'][0]
    les = mod['lessons'][0]
    sim_course = next((c for c in courses if c.get('simulation')), None)

    app = appmod.app
    app.config['TESTING'] = True
    cl = app.test_client()

    # --- account lifecycle ---
    r = cl.post('/register', data={'username': 'smoke_user', 'password': 'secret123'})
    check("register new account", r.status_code == 302 and '/login' in r.headers.get('Location', ''))

    r = cl.post('/register', data={'username': 'smoke_user', 'password': 'secret123'})
    check("duplicate username rejected", r.status_code == 302 and '/register' in r.headers.get('Location', ''))

    r = cl.post('/login', data={'username': 'smoke_user', 'password': 'WRONG'})
    check("wrong password rejected", '/login' in r.headers.get('Location', ''))

    r = cl.post('/login', data={'username': 'smoke_user', 'password': 'secret123'})
    check("login succeeds", r.status_code == 302 and '/dashboard' in r.headers.get('Location', ''))

    # --- pages load ---
    for page in ('/dashboard', '/courses', f'/courses/{slug}', '/leaderboard', '/profile', '/opportunities'):
        r = cl.get(page)
        check(f"page loads: {page}", r.status_code == 200)

    # --- the nautical-mile economy ---
    r = cl.post(f'/courses/{slug}/enroll')
    check("enrol in a course", r.status_code == 302)

    r = cl.post(f'/courses/{slug}/module/{mod["id"]}/lesson/{les["id"]}/complete')
    j = r.get_json()
    check(f"completing a lesson awards {appmod.NM_LESSON} NM", j.get('awarded') == appmod.NM_LESSON)

    r = cl.post(f'/courses/{slug}/module/{mod["id"]}/lesson/{les["id"]}/complete')
    check("repeating a lesson awards 0 (no double-dipping)", r.get_json().get('already_done') is True)

    if sim_course:
        s = sim_course['slug']
        cl.post(f'/courses/{s}/enroll')
        r = cl.post(f'/courses/{s}/simulation/submit', json={'score': 85})
        j = r.get_json()
        check("simulation pass awards NM", j.get('passed') and j.get('awarded', 0) > 0)
        r = cl.post(f'/courses/{s}/simulation/submit', json={'score': 85})
        check("repeating a passed simulation awards 0", r.get_json().get('already_done') is True)

    # --- persistence: re-read straight from the DB, as a fresh process would ---
    stats = appmod._get_stats('1')
    check("stats persisted to disk", stats['nautical_miles'] > 0)
    check("rank promoted past Deckhand", stats['rank_level'] >= 2)

    # --- health ---
    r = cl.get('/health')
    check("health endpoint reports DB connected", r.get_json().get('db') == 'connected')

    print()
    print(f"  {PASS} passed, {FAIL} failed")
    # tidy up the throwaway DB
    for ext in ('', '-wal', '-shm'):
        try: os.remove(_TEST_DB + ext)
        except OSError: pass

    if FAIL == 0:
        print("\n  \u2693 ALL CHECKS PASSED — LurniqHub is seaworthy.\n")
        return 0
    print("\n  Some checks failed. See the lines marked FAILED above.\n")
    return 1

if __name__ == '__main__':
    sys.exit(main())
