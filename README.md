# PerformanceLens (NYSH)

Local-first Flask app for school results, dashboards, recommendations, and a study planner. Data lives in **SQLite** on disk—there is no cloud account.

## Quick start

### Web App
```bash
cd src
python -m venv ../venv
source ../venv/bin/activate   # Windows: ..\venv\Scripts\activate
pip install -r ../requirements.txt
python run.py
```

Open **http://127.0.0.1:5000** (or the host/port you set). Complete onboarding once, then enter your **PIN** each time you open the app.

### Desktop App
```bash
# Option 1: Use the launcher script (recommended)
./run-desktop.sh

# Option 2: Manual activation
source venv/bin/activate  # On Windows: venv\Scripts\activate
python desktop.py
```

This opens PerformanceLens in a native desktop window using pywebview.

## Configuration (environment variables)

| Variable | Purpose |
|----------|---------|
| `PERFORMANCELENS_SECRET_KEY` | Flask session signing. Set a long random string for any shared or packaged build. |
| `PERFORMANCELENS_DB_PATH` | Full path to the SQLite file. Default: `performance.db` beside the project root when running from this repo. |
| `PERFORMANCELENS_DEBUG` | `true` / `false` for Flask debug (default `true` in `run.py`). |
| `PERFORMANCELENS_HOST` | Bind address (default `127.0.0.1`). |
| `PERFORMANCELENS_PORT` | Port (default `5000`). |

See `env.example` for a template.

## Desktop shell (Tauri or Electron)

Typical setup:

1. **Start this Flask app** from your native wrapper (same machine), listening on `127.0.0.1` with `PERFORMANCELENS_DEBUG=false` for release builds.
2. **Point the webview** at `http://127.0.0.1:5000` (or use a fixed port you control).
3. Set **`PERFORMANCELENS_DB_PATH`** to a file inside the user data directory (e.g. `%APPDATA%`, `~/Library/Application Support`, or XDG config) so grades survive app updates.
4. Set a strong **`PERFORMANCELENS_SECRET_KEY`** per install (or derive once and store alongside the DB).

Use **Settings → Download backup** before migrations or uninstall. Restoring from JSON is not automated; the backup is for archival and future import tooling.

## PerformanceLens Deployment Guide

## Session Management & Security

### PIN System
- **Secure Implementation**: PINs are stored using Werkzeug's scrypt hashing
- **Session Flow**: User ID + PIN unlock required for protected pages
- **Production Safe**: Dev session endpoint disabled in production

### Session Persistence
- **Secure Cookies**: HttpOnly, SameSite=Lax, Secure in production
- **Session Lifetime**: 24 hours with automatic expiration
- **Data Protection**: All user data stored in SQLite database

## Environment Setup

1. Copy `.env.example` to `.env`
2. Set `FLASK_ENV=production` for deployment
3. Set `PERFORMANCELENS_SECRET_KEY` to a secure random string
4. Optionally set database path: `PERFORMANCELENS_DB_PATH`

## User Data Preservation

**No Data Loss on Browser Close**:
- Sessions persist across browser restarts (24-hour lifetime)
- All grades, schedules, and preferences stored in database
- Only session cookies expire - not user data

**Migration Safety**:
- Database schema includes migration functions
- Backward compatibility maintained
- No breaking changes in current version

## Deployment Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export PERFORMANCELENS_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Run application
python src/run.py
```

## Security Checklist

- [ ] Set strong SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Set FLASK_ENV=production
- [ ] Backup database regularly
- [ ] Monitor application logs

## Troubleshooting

**If users can't access data**:
1. Check session cookie is being set
2. Verify database file permissions
3. Check FLASK_ENV setting
4. Clear browser cookies and re-login

**Data Backup**:
```bash
# Export all user data
curl -b cookies.txt http://localhost:5000/api/export/json > backup.json
```

## Tests

```bash
pip install -r ../requirements.txt
pytest
```

(`pytest.ini` adds `src` to the Python path.)

## Data & privacy

- **Backup**: Settings → Download backup (JSON). You can also copy the `.db` file while the app is stopped.
- **Reset**: Settings → erase results and planner data (PIN + confirmation). Your profile and PIN remain unless you sign out and onboard again.

## Charts

Dashboard **Performance over time** uses an inline SVG; **Analysis** uses Chart.js. Tick labels are sized for readability on laptop screens and in embedded webviews.

## Features

- Grade tracking and analysis
- Subject performance trends
- Study schedule generation
- Personalized recommendations
- Enhanced UI with consistent button system
- Time management suggestions
- Study technique recommendations
