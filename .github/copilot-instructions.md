# Copilot Instructions for PerformanceLens

- PerformanceLens is a local-first Flask app with an optional native wrapper via `pywebview`.
- Backend logic is centralized in `src/app/routes.py`; this file handles routing, session enforcement, file uploads, DB initialization, and most API payloads.
- Entry points:
  - `src/run.py` starts the Flask dev server.
  - `desktop.py` launches the same app inside a native desktop window.
  - `./run-desktop.sh` launches the desktop wrapper and requires `venv/bin/python`.
- Session/auth flow is enforced by `@bp.before_request` in `src/app/routes.py`.
  - Allowed unauthenticated routes: `/`, `/unlock`, `/api/onboarding/complete`, `/api/unlock`, `/api/logout`, `/api/results/upload`.
  - Onboarding stores `user_id`, `user_name`, and `pin_unlocked` in Flask session; most pages require PIN unlock.
- The app uses SQLite on disk. Override the DB path with `PERFORMANCELENS_DB_PATH`; default is `performance.db` in the repo root.
- Runtime config is controlled via environment variables listed in `README.md` and `env.example`.
  - `PERFORMANCELENS_SECRET_KEY` is required for shared/package builds.
  - `PERFORMANCELENS_DEBUG`, `PERFORMANCELENS_HOST`, and `PERFORMANCELENS_PORT` control dev server behavior.
- Study planner logic lives in `src/app/study_schedule.py`.
  - Preserve public helpers like `normalize_availability_payload`, `build_plan`, and `pack_blocks` when changing schedule generation.
- File upload parsing is implemented in `src/app/routes.py` with support for `.csv`, `.xlsx`, `.xls`, `.pdf`, and `.docx`.
- Templates are in `src/app/templates/`; key pages include `home.jinja`, `unlock.jinja`, `dashboard.jinja`, `input.jinja`, `analysis.jinja`, `recommendations.jinja`, `study.jinja`, and `settings.jinja`.
- Static assets are in `src/app/static/`; vendor JS/CSS such as Chart.js lives in `src/app/static/vendor/`.
- Developer workflow:
  - `cd src`
  - `python -m venv ../venv`
  - `source ../venv/bin/activate`
  - `pip install -r ../requirements.txt`
  - `python run.py`
- Testing:
  - `pytest`
  - `tests/conftest.py` sets `PERFORMANCELENS_DB_PATH` to a temporary test DB and `PERFORMANCELENS_SECRET_KEY` for isolation.
- Important project conventions:
  - No separate service layer; routes and helpers coexist in `src/app/routes.py`.
  - DB migrations are applied automatically in `routes.init_db()`.
  - `pytest.ini` adds `src` to the import path so tests can import `app` directly.

Please review and tell me whether you want me to add a route flow diagram for PIN unlock, onboarding, or desktop wrapper behavior.
