# Backup and restoration

Keep backups of the database and of `MEDIA_ROOT`. The database holds students, results, and branding text. The media directory holds photos, logos, signatures, seals, and notice attachments. One without the other is an incomplete restore.

Do not put dumps, `.env`, or media files in git. Store them outside `public_html`.

The commands below use placeholders. Run them as the hosting account user. They were not executed against a production server from this repository.

## What to copy

- Database named in `DATABASE_URL`
- The directory named by `MEDIA_ROOT`
- A copy of `.env`, stored separately from the database dump because it contains the secret key and the database password

The application source can be recovered from git. Uploaded files and the database cannot.

## PostgreSQL

```bash
mkdir -p "$HOME/backups/scholarship"
stamp=$(date +%Y%m%d-%H%M)
pg_dump --format=custom --no-owner --file="$HOME/backups/scholarship/db-$stamp.dump" \
  --dbname="$DATABASE_URL"
tar -C "$(dirname "$MEDIA_ROOT")" -czf "$HOME/backups/scholarship/media-$stamp.tar.gz" \
  "$(basename "$MEDIA_ROOT")"
```

`DATABASE_URL` must already be in the environment, in the same form Django uses (`postgresql://USER:PASSWORD@HOST:PORT/NAME`). If the host’s `pg_dump` does not accept a URL, pass `-h`, `-p`, `-U`, and the database name instead, and keep the password in a `pgpass` file with mode `600`.

Restore into an empty database:

```bash
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" \
  "$HOME/backups/scholarship/db-YYYYMMDD-HHMM.dump"
tar -C "$(dirname "$MEDIA_ROOT")" -xzf "$HOME/backups/scholarship/media-YYYYMMDD-HHMM.tar.gz"
cd /home/USERNAME/scholarship
python manage.py migrate
```

`--clean` drops objects before recreating them. Use it only on the database you intend to replace.

## MySQL or MariaDB

```bash
mkdir -p "$HOME/backups/scholarship"
stamp=$(date +%Y%m%d-%H%M)
mysqldump --single-transaction --default-character-set=utf8mb4 \
  -h localhost -u DBUSER -p DBNAME > "$HOME/backups/scholarship/db-$stamp.sql"
tar -C "$(dirname "$MEDIA_ROOT")" -czf "$HOME/backups/scholarship/media-$stamp.tar.gz" \
  "$(basename "$MEDIA_ROOT")"
```

`--single-transaction` needs InnoDB, which this project expects. The dump is UTF-8 so Bangla text survives.

Restore:

```bash
mysql --default-character-set=utf8mb4 -h localhost -u DBUSER -p DBNAME \
  < "$HOME/backups/scholarship/db-YYYYMMDD-HHMM.sql"
tar -C "$(dirname "$MEDIA_ROOT")" -xzf "$HOME/backups/scholarship/media-YYYYMMDD-HHMM.tar.gz"
cd /home/USERNAME/scholarship
python manage.py migrate
```

## Schedule

A daily cron entry is enough for the expected size of this system. `scripts/backup.sh` reads `DATABASE_URL` and `MEDIA_ROOT` from the environment and supports a PostgreSQL URL. For MySQL, use the `mysqldump` command above.

```text
15 2 * * * DATABASE_URL='postgresql://...' MEDIA_ROOT='/home/USERNAME/private/scholarship-media' /home/USERNAME/scholarship/scripts/backup.sh >> /home/USERNAME/logs/scholarship/backup.log 2>&1
```

Keep at least 14 daily copies, and copy them off the same disk when the host provides another location. Delete old dumps from the server so they do not fill the account.

Test a restore on a spare database before you need it. A dump that has never been restored is an unverified dump.

## After a restore

1. Confirm `DATABASE_URL` and `MEDIA_ROOT` point at the restored data.
2. Run `python manage.py migrate`.
3. Restart the Passenger application.
4. Log in as a super admin, open a known student, and confirm the photo loads.
5. Open `/` and confirm the active session’s name and logos.
6. Confirm unpublished winners are still absent from `/winners/`.

Student IDs and certificate numbers continue from `StudentSequence`. Do not reset that table during a restore, or new registrations could reuse IDs that already appear on printed profiles.
