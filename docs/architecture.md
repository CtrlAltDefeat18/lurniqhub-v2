# Architecture

Status: Draft v0.1, 21/10/2026. This describes the target MVP architecture. Verify each section against the actual repository and correct anything that has drifted.

## Principles

- Smallest thing that works. One Flask app, one SQLite database, no build step for the backend.
- Runs on a single small server. No external services unless essential.
- Light pages for low-end phones and patchy connections.
- Everything checkable by an automated smoke test on every push to `main`.

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Flask, Gunicorn | Single app, routes grouped by feature |
| Database | SQLite in WAL mode | JSON columns for array fields. One file, backed up on a schedule |
| Frontend | Jinja templates, Tailwind, Alpine.js, GSAP | No bundler |
| Hosting | DigitalOcean (small droplet or App Platform) | Decide before the November deploy |
| CI | GitHub Actions | Lint, format check, smoke test on push to `main` |

## Repository layout

```
.
├── src/
│   ├── app.py            # Flask app and routes
│   ├── templates/        # Jinja templates
│   ├── static/           # css, js, images
│   └── ...               # service modules (dashboard, news, profile)
├── tests/ or test_smoke.py
├── docs/                 # this folder
├── .github/workflows/ci.yml
├── requirements.txt
├── package.json          # lint and format tooling only
├── pyproject.toml        # ruff configuration
├── AGENTS.md
└── README.md
```

`app.py` lives in `src/`, next to `templates/` and `static/`. Flask resolves template and static folders relative to the module, so these two work by default. Paths that depend on the working directory (the database file, imports between modules, the start command) must be set explicitly.

## Configuration

All configuration comes from environment variables. Nothing secret is committed.

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Session signing | None. The app must refuse to start in production without it |
| `DATABASE_PATH` | SQLite file location | A `data/` folder outside `src/` |
| `FLASK_ENV` | Environment name | `production` |

## Data model (MVP)

- `users`: id, username, password hash, created_at, is_admin
- `profiles`: user_id, grade, school, subjects (JSON), province, town. Add fields only when a feature needs them
- `courses`, `modules`, `topics`: curriculum structure and lesson content
- `enrolments`: user_id, course_id, enrolled_at
- `lesson_views`: user_id, topic_id, first_viewed_at
- `pathways`, `programmes`, `funding_opportunities`: each row has `source_url` and `last_verified` (DD/MM/YYYY). No row is shown without them

Deferred: ranks and points tables, academic results, photo upload, email tokens.

## Security and privacy

- Passwords hashed with Werkzeug's `generate_password_hash`.
- Real CSRF protection on every state-changing form. A token in the session that is never checked is not protection.
- Rate limit login and registration.
- Do not collect the 13-digit ID number in the MVP. Most users are minors and the feature does not need it.
- POPIA: collect only what a feature needs, give a privacy notice, obtain parent or guardian consent for learners under 18, and keep a way to delete an account.
- Never store learner data in GitHub or send it to AI tools.
- Keep `.env` and `*.db` out of git.

## Start command

Because `app.py` is inside `src/`, either of these works. Pick one and use it everywhere (README, CI, server):

```
gunicorn --chdir src app:app
```

or make `src` a package and run `gunicorn src.app:app`, changing imports to `from src.module import ...` or relative imports.

The first is simpler and keeps existing imports unchanged.

## Testing and CI

- `test_smoke.py` starts the app with a temporary database and checks that key routes respond: register, login, dashboard, courses.
- Each new route gets a smoke check.
- GitHub Actions runs `ruff check`, `ruff format --check`, ESLint, Prettier check and the smoke test on every push to `main` and on pull requests.

## Known technical debt

- Tailwind via the CDN script is for development. Before the pilot, generate a compiled CSS file with the Tailwind standalone CLI in CI and serve that, which is smaller and faster on mobile.
- Google Fonts and the Material Icons font add requests and weight. Self-host or subset later.
- `requirements.txt` may still list MongoDB-era packages. Remove anything the code no longer imports.
- Inline JavaScript in templates is not linted. Move it to files under `static/js/`.

## Deferred

Offline-first and Raspberry Pi deployment, email, photo upload, teacher dashboard, ranking system. Revisit after the first pilot, once real constraints are known.
