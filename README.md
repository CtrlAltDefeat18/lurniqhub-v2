# LurniqHub v2

Maritime-focused EdTech platform for rural youth. Offline-first by design:
runs entirely on a local SQLite file with no external database server, so it
works on a Raspberry Pi, a locked-down public machine, or anywhere Python runs.

## Stack
- Flask (web framework)
- SQLite via Python's built-in `sqlite3` — no server, no network, no setup
- Werkzeug password hashing, signed-cookie sessions

## Run it
```bash
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000. The database file `lurniqhub.db` is created
automatically on first run and persists between restarts. The first account
registered becomes the admin.

To run for production-style serving:
```bash
gunicorn app:app
```

## Notes
- Move the database elsewhere with: `DATABASE_PATH=/path/to/lurniqhub.db`
- Set a real secret in production: `SECRET_KEY=...`
- Course content lives in `seed_data.py` and is seeded into the DB on first request.

## Test it
```bash
python test_smoke.py
```
Runs a full register/login/enrol/lesson/simulation journey against a throwaway database and prints a pass/fail summary. Reuse it to demo to anyone or before you ship a change.
