# Production

```bash
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
gunicorn backend.wsgi
```

```bash
cd frontend
npm run build
node .output/server/index.mjs
```

Put a reverse proxy with HTTPS (for example Caddy or Nginx) in front of both. `check --deploy` reports an error as long as `EMAIL_HOST` is not set, because confirmation mails would otherwise only appear in the terminal.

Settings come from environment variables. The backend reads them in `backend/settings.py` (for example `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=0` in production); the frontend lists its variables in `frontend/.env.example`.

## Regular jobs

Run these regularly (cron or task scheduler):

```bash
python manage.py backup_db            # keeps the 14 most recent backups
python manage.py cleanup_unverified   # removes accounts unconfirmed after 3 days
python manage.py flushexpiredtokens   # removes expired entries from the JWT blocklist
```

## Before going live

- The legal pages (imprint, privacy, terms) are templates, not legal advice. Fill in the operator details and have them reviewed.
- Cloudflare Turnstile and real SMTP delivery were only tested with mocks or a local test server.
- The renewal grace period (10 seconds) and the shared renewal live in the memory of one Nuxt process. With several Nuxt instances behind a load balancer, use sticky sessions or accept that a parallel request may be asked to log in again.
