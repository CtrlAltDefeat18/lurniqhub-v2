# LurniqHub

LurniqHub is a maritime-focused Flask learning platform for rural South
African learners. The current MVP provides account access, a seeded course
catalogue, lesson progress, browser-based simulations, learner rankings and
maritime career opportunities.

The application uses a local SQLite database, so it needs no database server
or external backend service. It is designed for eventual offline-first use,
but the current MVP does not yet include a service worker, IndexedDB
synchronisation or a local caching layer.

## Stack

- Flask 3.0
- SQLite through Python's built-in `sqlite3` module, using WAL mode
- Jinja templates
- Werkzeug password hashing and Flask signed-cookie sessions
- Tailwind CSS, Alpine.js and GSAP loaded from CDNs
- Gunicorn for production-style serving

## Run locally

From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python src/app.py
```

Open <http://127.0.0.1:8080>. The default database is created at
`data/lurniqhub.db` on first import and persists between restarts. The first
registered account is marked as an administrator, although no administrator
routes are currently implemented.

For production-style serving:

```bash
gunicorn --chdir src app:app
```

## Configuration

Set environment variables before starting the application:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Development-only key | Flask session signing; set a real value in production |
| `DATABASE_PATH` | `data/lurniqhub.db` | SQLite database location |
| `HOST` | `127.0.0.1` | Bind address for `python src/app.py` |
| `PORT` | `8080` | Bind port for `python src/app.py` |
| `FLASK_DEBUG` | Disabled | Set to `1` for the direct development server |

Example:

```bash
SECRET_KEY='replace-with-a-random-value' \
DATABASE_PATH='/path/to/lurniqhub.db' \
python src/app.py
```

Course content is defined in `src/seed_data.py` and inserted into the
database when the dashboard, course catalogue or course-detail route first
needs it. Existing course rows are not overwritten automatically.

## Main routes

- `/` — redirect to the dashboard or login
- `/register`, `/login`, `/logout` — account lifecycle
- `/dashboard` — learner progress and ranking summary
- `/courses` and `/courses/<slug>` — course catalogue and details
- `/courses/<slug>/module/...` — lessons and completion
- `/courses/<slug>/simulation` — interactive helm simulation
- `/leaderboard`, `/profile`, `/opportunities` — learner views
- `/health` — public SQLite connectivity check

## Test it

```bash
python test_smoke.py
```

The smoke test uses a temporary database and exercises registration, login,
protected pages, enrolment, lesson completion, simulation scoring, rewards,
rank promotion and the health endpoint.

## Repository guide

- `src/app.py` — Flask application, routes, database schema and reward logic
- `src/seed_data.py` — curriculum, simulations, ranks and opportunities
- `src/templates/` — Jinja pages
- `src/static/js/` — page utilities and simulation engine
- `docs/architecture.md` — implemented architecture and known limitations
- `docs/vision_mission.md` — product purpose and pilot goals
- `AGENTS.md` — contributor and engineering guidelines

The project documentation in `docs/` describes the intended product direction;
`docs/architecture.md` describes the behaviour currently implemented.
