#!/bin/sh
set -eu

DUMP_PATH="${DUMP_PATH:-/dumps/firulais-mysql-dump.sql}"

mysqldump \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --user="${DB_USER}" \
  --password="${DB_PASSWORD}" \
  --ssl=0 \
  --single-transaction \
  --skip-lock-tables \
  "${DB_NAME}" \
  > "${DUMP_PATH}"

echo "Backup MySQL creado en ${DUMP_PATH}"
