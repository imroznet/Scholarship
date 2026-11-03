# cPanel deployment

This application is a Django project with a Passenger entry point at the repository root (`passenger_wsgi.py`). It does not need root access, Docker, or a running Node.js server.

These steps were checked against the project settings and the local test run on Python 3.12. They were not executed on a live cPanel account. Replace every placeholder. Do not commit the real `.env` file.

## 1. Python version

Use a cPanel “Setup Python App” version that Django 5.2 supports: 3.10, 3.11, 3.12, or 3.13. This codebase was tested on Python 3.12.3 with Django 5.2.

If the host only offers an older Python, do not force this release onto it. Django 5.2 will refuse to start.

## 2. Virtual environment

In cPanel, create the Python application and let it create the virtual environment. A typical layout is:

```text
/home/USERNAME/scholarship/          application root (this project)
/home/USERNAME/virtualenv/scholarship/   virtual environment created by cPanel
/home/USERNAME/public_html/          document root, not the place for source or .env
```

The application root must be the directory that contains `manage.py` and `passenger_wsgi.py`. Keep that directory outside `public_html` when the host allows it. Point the domain’s document root at `public_html`, and point the Python app at the project directory.

## 3. Install dependencies

From the virtual environment cPanel created:

```bash
source /home/USERNAME/virtualenv/scholarship/bin/activate
cd /home/USERNAME/scholarship
pip install -r requirements.txt
```

`requirements.txt` includes Django, Pillow, openpyxl, ReportLab, psycopg, PyMySQL, WhiteNoise, uharfbuzz, and freetype-py. The Bangla certificate renderer needs the last two plus the fonts already in `static/fonts/`.

## 4. Environment variables

Copy `.env.example` to `.env` in the application root, outside `public_html`. Set at least:

```text
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=a unique random string of at least 40 characters
DEBUG=False
ALLOWED_HOSTS=scholarship.example.com
CSRF_TRUSTED_ORIGINS=https://scholarship.example.com
DATABASE_URL=postgresql://DBUSER:DBPASSWORD@localhost:5432/DBNAME
TIME_ZONE=Asia/Dhaka
MEDIA_ROOT=/home/USERNAME/private/scholarship-media
LOG_DIR=/home/USERNAME/logs/scholarship
DJANGO_SECURE_SSL=True
DJANGO_BEHIND_PROXY=True
```

`SECRET_KEY` must not start with `dev-`. Generate it on the server, for example with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

For MySQL or MariaDB use:

```text
DATABASE_URL=mysql://DBUSER:DBPASSWORD@localhost:3306/DBNAME
```

PyMySQL is loaded automatically for `mysql://` URLs. The connection uses `utf8mb4`.

Optional bootstrap of the first super admin, used once:

```text
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=choose-a-long-password
BOOTSTRAP_ADMIN_EMAIL=office@example.com
```

Remove those three variables after the user exists.

## 5. Database

Prefer the host’s PostgreSQL database if it is offered. Otherwise use MySQL/MariaDB. The Django models use portable fields. Production settings reject SQLite.

Create an empty database and a user that can use only that database. Note the host, port, database name, user, and password from cPanel and put them in `DATABASE_URL`.

If the cPanel account has neither PostgreSQL nor MySQL, host the database on a managed service and put that hostname in `DATABASE_URL`. The application does not embed a database server.

On MySQL, conditional “only one active row” indexes are not created. The session and schedule services still keep a single active row by locking and updating inside a transaction. Use InnoDB, which is the default on current MySQL and MariaDB.

## 6. Migrations

```bash
python manage.py migrate
python manage.py bootstrap_scholarship
```

`migrate` creates every table, including the custom user table. Run it before creating users. `bootstrap_scholarship` inserts the two categories and the 2026 session only when they are absent.

If `CACHE_BACKEND=db` (the production default), create the cache table once:

```bash
python manage.py createcachetable
```

## 7. Static files

The compiled stylesheet is already in `static/css/app.css`. On the server:

```bash
python manage.py collectstatic --noinput
```

WhiteNoise serves those files. Do not run a Node.js build on the server. If you change Tailwind classes in a future release, compile `static/css/app.css` before uploading.

## 8. Passenger WSGI

In the Python application screen:

- Application root: the project directory
- Application startup file: `passenger_wsgi.py`
- Application entry point: `application`

`passenger_wsgi.py` adds the project to `sys.path` and defaults `DJANGO_SETTINGS_MODULE` to `config.settings.production`. An environment variable set in cPanel overrides that default.

Restart the application after code or environment changes. Use cPanel’s Restart button or `touch tmp/restart.txt` inside the application root.

## 9. Media uploads

Set `MEDIA_ROOT` to a directory outside `public_html`, for example `/home/USERNAME/private/scholarship-media`. Create it before uploading.

Do not alias `/media/` to that directory in Apache. Student photos and notice attachments must not be directly downloadable. The application serves public logos and published winner photos through its own views.

## 10. File permissions

The application user must be able to read the project and write to `MEDIA_ROOT` and `LOG_DIR`. A typical setup:

```bash
mkdir -p /home/USERNAME/private/scholarship-media /home/USERNAME/logs/scholarship
chmod 750 /home/USERNAME/private /home/USERNAME/private/scholarship-media
```

Do not make media or `.env` world-readable (`chmod 777` is not appropriate). Source files can stay readable by the user and not writable by the web server except for the media and log directories.

## 11. HTTPS and allowed hosts

Enable the cPanel AutoSSL or Let’s Encrypt certificate for the domain. Set `DJANGO_SECURE_SSL=True` so session cookies, the CSRF cookie, and the HTTPS redirect are secure. `DJANGO_BEHIND_PROXY=True` trusts `X-Forwarded-Proto` from the host proxy.

`ALLOWED_HOSTS` must list the real domain names, not `*`. `CSRF_TRUSTED_ORIGINS` must include the `https://` origin. The production module also sets HSTS for one year. Set `HSTS_SECONDS=0` only while you are still confirming that HTTPS works, then set it back.

## 12. Error logging

Production logs to the console and to a rotating file at `$LOG_DIR/django.log` (5 MB, 5 backups). cPanel’s “Errors” and the Passenger log are the other places to look when the app will not start. A failed settings check raises `ImproperlyConfigured` before serving traffic. That usually means `SECRET_KEY`, `ALLOWED_HOSTS`, or `DATABASE_URL` is missing or still points at SQLite.

## 13. Database backup

See [BACKUP.md](BACKUP.md). Schedule the dump from cPanel cron as the account user. Keep dumps outside `public_html` and outside git.

## 14. Restoration

See [BACKUP.md](BACKUP.md). Restore the database first, then the media directory, then run `python manage.py migrate` in case the code is newer than the dump.

## 15. Production smoke tests

After restart, from a machine that can reach the site:

1. `GET /` returns the Bangla homepage and the session name from the database, not a server error.
2. `GET /application-process/` states that online registration is not accepted, and the page has no registration form.
3. `GET /accounts/login/` shows the login form.
4. A super admin can open `/dashboard/` and `/dashboard/branding/`.
5. An operator can open `/dashboard/students/` and receives 403 on `/dashboard/branding/`.
6. `GET /robots.txt` disallows `/dashboard/`, `/accounts/`, `/django-admin/`, and `/media/`.
7. A direct request for a student photo path under `/media/` is not served by the web server.
8. Uploading a student photo, searching that student, and printing the profile work while logged in.
9. A winner does not appear on `/winners/` until a super admin publishes that winner.
10. `python manage.py check --deploy` reports no unexpected issues for the production settings.

Record the result of those checks for the hosting account. This repository’s test run does not replace that live check.
