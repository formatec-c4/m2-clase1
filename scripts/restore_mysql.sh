#!/bin/sh
set -eu

DUMP_PATH="${DUMP_PATH:-/dumps/firulais-mysql-dump.sql}"

sed 's/utf8mb4_uca1400_ai_ci/utf8mb4_0900_ai_ci/g' "${DUMP_PATH}" | mysql \
  --host="${DB_HOST}" \
  --port="${DB_PORT}" \
  --user="${DB_USER}" \
  --password="${DB_PASSWORD}" \
  --ssl=0 \
  "${DB_NAME}"

echo "Backup MySQL restaurado desde ${DUMP_PATH}"
