#!/bin/sh
# Backup the database URL in the environment and the MEDIA_ROOT directory.
# Does not contain passwords. Exits non-zero if the required variables are missing.

set -eu

if [ -z "${DATABASE_URL:-}" ] || [ -z "${MEDIA_ROOT:-}" ]; then
  echo "Set DATABASE_URL and MEDIA_ROOT before running this script." >&2
  exit 1
fi

dest="${BACKUP_DIR:-$HOME/backups/scholarship}"
mkdir -p "$dest"
stamp=$(date +%Y%m%d-%H%M)
parent=$(dirname "$MEDIA_ROOT")
base=$(basename "$MEDIA_ROOT")

case "$DATABASE_URL" in
  postgres://*|postgresql://*)
    pg_dump --format=custom --no-owner --file="$dest/db-$stamp.dump" --dbname="$DATABASE_URL"
    ;;
  mysql://*)
    echo "MySQL backups need mysqldump with host, user, and database flags. See docs/BACKUP.md." >&2
    exit 1
    ;;
  *)
    echo "Unsupported DATABASE_URL scheme." >&2
    exit 1
    ;;
esac

tar -C "$parent" -czf "$dest/media-$stamp.tar.gz" "$base"
echo "Wrote $dest/db-$stamp.dump and $dest/media-$stamp.tar.gz"
