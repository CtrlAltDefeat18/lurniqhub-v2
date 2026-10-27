# Architecture

This describes the behaviour implemented in the current tree; the other
project documents include future MVP goals.

## Layout and runtime

- `src/app.py`: single Flask application, routes, authentication, SQLite helpers and reward logic; no service modules or blueprints.
- `src/seed_data.py`: five course documents with nested modules, lessons, quizzes and simulation configuration; eight ranks, reward constants, opportunity links and pure helpers.
- `src/templates/`: `base.html` plus login, register, dashboard, courses, course_detail, lesson, simulation, leaderboard, profile and opportunities pages.
- `src/static/js/`: `main.js` (counters/progress/animations) and `simulator.js` (Canvas helm simulation). No local CSS or image assets.
- Root: `test_smoke.py`, `requirements.txt`, `runtime.txt`, `Procfile`, `.env.example`, `AGENTS.md`, `README.md`, `lurniqhubMVP_history.md`, `.vscode/` and `docs/`. `scripts/` contains legacy copies of the seed and smoke files; the active entry points are `src/seed_data.py` and the root `test_smoke.py`. `requirements.txt.tmp` is a legacy dependency list.
- No `package.json`, `pyproject.toml`, `tests/` or GitHub Actions workflow is present.

Flask 3.0.0 renders Jinja templates; Werkzeug hashes passwords and Flask signs cookie sessions. SQLite uses WAL with a ten-second connection timeout. Gunicorn 21.2.0 is declared and Python 3.11.7 is pinned. No MongoDB, ORM, frontend bundler or external database server is used.

`base.html` loads Tailwind, Alpine.js, GSAP, Google Fonts and Material Icons from CDNs. Templates contain inline CSS/JavaScript; lesson completion and simulation submission use `fetch`. Quizzes and simulation scoring run in the browser. No service worker or local progress synchronisation exists.

Start from the repository root with `python src/app.py` or `gunicorn --chdir src app:app` (the Procfile command). Importing `app` creates tables; `_seed_if_needed()` is called by dashboard, catalogue and course-detail requests, not at import. It inserts missing course slugs without updating existing content.

| Variable | Actual behaviour |
|---|---|
| `SECRET_KEY` | Defaults to `dev-secret-key`; missing/empty raises only when `FLASK_ENV=production` |
| `FLASK_ENV` | No default; used for that secret-key guard |
| `DATABASE_PATH` | Defaults to repository-root `data/lurniqhub.db`; parent directory is created |
| `HOST`, `PORT` | Direct Python server defaults: `127.0.0.1`, `8080`; not Gunicorn bind settings |
| `FLASK_DEBUG` | Direct Python server enables debug only for `1` |

## Routes

GET routes also support Flask's automatic HEAD/OPTIONS. Protected routes use `login_required`, redirecting anonymous users to login; this also applies to JSON endpoints.

| Methods | Path | Behaviour / access |
|---|---|---|
| GET | `/` | Redirect to dashboard or login |
| GET, POST | `/register`, `/login` | Public forms; signed-in users redirect to dashboard |
| GET | `/logout` | Clears session; no login decorator |
| GET | `/dashboard`, `/courses`, `/courses/<slug>` | Protected progress, catalogue and course detail |
| POST | `/courses/<slug>/enroll` | Protected enrolment and reward |
| GET | `/courses/<slug>/module/<mod_id>/lesson/<lesson_id>` | Protected lesson; requires enrolment |
| POST | `/courses/<slug>/module/<mod_id>/lesson/<lesson_id>/complete` | Protected JSON completion/reward |
| GET | `/courses/<slug>/simulation` | Protected simulation; requires enrolment |
| POST | `/courses/<slug>/simulation/submit` | Protected JSON score/reward |
| GET | `/leaderboard`, `/profile`, `/opportunities` | Protected rankings, progress and static opportunity links |
| GET | `/health` | Public SQLite connectivity check; always HTTP 200, even with `db=error` |
| GET | `/static/<path:filename>` | Flask static-file serving |

The first registered user receives `is_admin`; no admin routes exist. Ranks and nautical-mile rewards already work; they are not deferred features.

## Database

These are the four application tables from `init_db()` (SQLite also maintains `sqlite_sequence`). JSON is stored as TEXT, not separate module/lesson tables. Although connections enable foreign keys, no foreign-key constraints are declared.

```sql
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
```

`users.password` holds a hash. Related `user_id` values are stored as TEXT despite the integer user primary key. Course JSON contains the curriculum and simulation settings; completion arrays hold lesson identifiers and course slugs. There are no profiles, pathways, funding, lesson-view or separate rank tables. Opportunities and rank thresholds come from Python constants.

## Validation and current debt

`python test_smoke.py` imports from `src/`, explicitly initialises/seeds a temporary database, and runs 19 checks through Flask's test client: account flow, protected pages, enrolment, lesson/simulation rewards, persistence, ranks and health. It does not exercise a real Gunicorn process or browser JavaScript. CI, lint/format scripts, scheduled backups and a hosting deployment are not implemented in this tree.

- Startup seeding is request-driven; the smoke test's explicit setup masks that distinction. Seeding uses SELECT then INSERT, which can race between workers.
- Reward endpoints lack enrolment checks; lesson completion also lacks lesson validation. Simulation scores are client-supplied and invalid numeric values can raise errors. Login awards the “daily” reward on every successful login.
- Completion checks, JSON-array updates and rewards span transactions, risking duplicate awards/lost updates under concurrency. No schema migration mechanism or foreign-key constraints exist.
- No CSRF enforcement or login/registration rate limiting; conditional token markup does not provide protection. Logout changes state via GET. No account deletion or consent workflow is implemented.
- CDN assets prevent reliable offline use and add mobile bandwidth cost. Inline scripts/styles and duplicated content in `scripts/` increase maintenance effort. PWA caching/sync remains future scope per AGENTS.md.
- `lurniqhubMVP_history.md` and the files under `scripts/` preserve older MongoDB-era notes and are not active application entry points. The active requirements contain no MongoDB packages; the legacy dependency list remains only in `requirements.txt.tmp`.
- Opportunity data has no enforced verification-date policy. Pathway matching, learner subject/marks profiles and teacher tools described in planning docs are not implemented.
