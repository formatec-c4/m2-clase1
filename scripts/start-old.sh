#!/bin/sh
set -eu

mkdir -p /run/mysqld /var/lib/mysql
chown -R mysql:mysql /run/mysqld /var/lib/mysql

if [ ! -d /var/lib/mysql/mysql ]; then
  mariadb-install-db --user=mysql --datadir=/var/lib/mysql > /dev/null
fi

mariadbd --user=mysql --bind-address=127.0.0.1 --datadir=/var/lib/mysql &
MYSQL_PID="$!"

until mysqladmin --protocol=SOCKET ping --silent; do
  sleep 1
done

mysql --protocol=SOCKET <<SQL
CREATE DATABASE IF NOT EXISTS ${DB_NAME};
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

mysql --protocol=SOCKET "${DB_NAME}" < /app/db/init.sql

/usr/bin/python3 app/app.py &
APP_PID="$!"

trap 'kill "$APP_PID" "$MYSQL_PID"' INT TERM
wait "$APP_PID"
