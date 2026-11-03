# Country Group Scholarship Management System

Bangla scholarship administration for an initial capacity of about 100–500 students. Staff enter applications. The public site only shows scholarship information, the schedule, notices, and winners that an administrator has explicitly published.

The scholarship name, sponsor, and logos are stored per session. They are not hardcoded in templates.

## Stack

- Python 3.12 (Django 5.2 also supports 3.10–3.13)
- Django 5.2 LTS
- Django templates, Tailwind CSS, HTMX, Alpine.js
- PostgreSQL in production, MySQL as a portable alternative
- SQLite only for local development and automated tests

There is no Node.js process to keep running. Tailwind is compiled into `static/css/app.css` before deployment.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py bootstrap_scholarship
python manage.py createsuperuser
python manage.py runserver
```

`bootstrap_scholarship` creates the categories সাধারণ and মাদ্রাসা, and the 2026 session, only when those records are missing. It does not create a password. To create the first super admin from the environment instead of the prompt, set `BOOTSTRAP_ADMIN_USERNAME` and `BOOTSTRAP_ADMIN_PASSWORD` before running the command.

Open `/` for the public site and `/accounts/login/` for the dashboard.

## Tests

```bash
python manage.py test tests
```

The suite covers authentication and roles, branding, institutes and classes, student IDs (including a concurrent registration), verification, schedules, results and winner publication, the public site, certificates, and Excel/CSV exports. Production settings are imported in a subprocess and must reject SQLite.

## Roles

| Role | Access |
| --- | --- |
| `SUPER_ADMIN` | Full dashboard, including branding, sessions, results, winners, certificates, users, and audit logs |
| `DATA_ENTRY_OPERATOR` | Add and edit active students, print profiles, and export a reduced student report |

Authorization is enforced on the server. Operators receive HTTP 403 on super-admin views.

## Main addresses

Public: `/`, `/about/`, `/application-process/`, `/schedule/`, `/notices/`, `/winners/`, `/contact/`

Dashboard: `/dashboard/`, `/dashboard/branding/`, `/dashboard/sessions/`, `/dashboard/students/`, `/dashboard/institutes/`, `/dashboard/academics/classes/`, `/dashboard/academics/registration/`, `/dashboard/verification/`, `/dashboard/schedules/`, `/dashboard/examinations/`, `/dashboard/results/`, `/dashboard/winners/`, `/dashboard/notices/`, `/dashboard/reports/`, `/dashboard/users/`, `/dashboard/audit/`, `/dashboard/settings/`

There is no public student registration form.

## Engineering decisions

- The active scholarship session supplies public branding. Each session keeps its own identity, sponsor, and logos.
- Resetting branding restores the names in `apps/branding/defaults.py`. If student or certificate numbers have already been issued, the short name that formed those numbers is kept.
- Student IDs look like `CGS26-0001`. The prefix is the session short name plus the session code, stored on `StudentSequence`. The counter increments inside a database transaction and rolls back if registration fails. PostgreSQL and MySQL lock the sequence row. SQLite uses `UPDATE ... RETURNING`, which its writer lock serializes. A failed save retries on a lock or unique-constraint error.
- The student’s category is copied from the institute at registration. Later edits to the institute do not rewrite old students.
- Parent name and mobile are required unless a super admin turns that off in settings. Address fields are required. A shared parent phone produces a warning and does not block registration.
- Schedule stages do not advance by themselves, and results are not published by themselves. Winner publication is a separate action. Unpublished winners stay off the public site.
- Student photos and notice files are stored under `private/` and are not served from `/media/`. Public logos and published winner photos use dedicated views.
- SVG uploads are rejected. PNG, JPEG, and WebP are checked with Pillow, resized, and stored under generated names.
- Certificate Bangla is drawn with HarfBuzz and FreeType into images because ReportLab does not shape Bengali. Student IDs, certificate numbers, and other ASCII values stay as PDF text. The certificate reads the branding of its own session.
- Spreadsheet cells that start with `=`, `+`, `-`, `@`, tab, or carriage return are prefixed with an apostrophe. Operator exports omit date of birth, parent details, village, post office, session, and the registering user.
- Login failures are counted in the database (5 failures in 15 minutes by default).
- Times are stored timezone-aware. The application timezone is `Asia/Dhaka`.
- On MySQL, Django does not create partial unique indexes. The application still clears every other active session or schedule stage inside a transaction before activating one.

## Production

Use `DJANGO_SETTINGS_MODULE=config.settings.production`. That module refuses `DEBUG=True`, a short secret, a wildcard host list, and a SQLite `DATABASE_URL`.

Deployment steps for cPanel and Passenger are in [docs/CPANEL.md](docs/CPANEL.md). Backup and restore steps are in [docs/BACKUP.md](docs/BACKUP.md).

This repository does not contain hosting passwords, and pushing the code does not by itself deploy it.
