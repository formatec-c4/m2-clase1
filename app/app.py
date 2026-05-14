import os
from datetime import date, datetime, time, timedelta

import pymysql
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


def db_config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "database": os.environ.get("DB_NAME", "firulais"),
        "user": os.environ.get("DB_USER", "firulais"),
        "password": os.environ.get("DB_PASSWORD", "firulais"),
        "cursorclass": pymysql.cursors.DictCursor,
    }


def get_connection():
    return pymysql.connect(**db_config())


def serialize_value(value):
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return value


def serialize_turno(turno):
    return {key: serialize_value(value) for key, value in dict(turno).items()}


def fetch_turnos():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, mascota, duenio, fecha, hora, motivo, created_at
                FROM turnos
                ORDER BY fecha, hora, id;
                """
            )
            return [serialize_turno(row) for row in cur.fetchall()]


def fetch_turno(turno_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, mascota, duenio, fecha, hora, motivo, created_at
                FROM turnos
                WHERE id = %s;
                """,
                (turno_id,),
            )
            row = cur.fetchone()

    if row is None:
        return None

    return serialize_turno(row)


def validate_turno(data):
    required_fields = ["mascota", "duenio", "fecha", "hora"]
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return {"error": "Faltan campos obligatorios", "campos": missing_fields}

    return None


@app.get("/")
def index():
    try:
        turnos = fetch_turnos()
        db_error = None
    except Exception as exc:
        turnos = []
        db_error = str(exc)

    return render_template("index.html", turnos=turnos, db_error=db_error)


@app.get("/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as exc:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(exc)}), 503


@app.get("/api/turnos")
def listar_turnos():
    return jsonify(fetch_turnos())


@app.post("/api/turnos")
def crear_turno():
    data = request.get_json(silent=True) or {}
    validation_error = validate_turno(data)

    if validation_error:
        return jsonify(validation_error), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO turnos (mascota, duenio, fecha, hora, motivo)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    data["mascota"],
                    data["duenio"],
                    data["fecha"],
                    data["hora"],
                    data.get("motivo"),
                ),
            )
            turno_id = cur.lastrowid
        conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, mascota, duenio, fecha, hora, motivo, created_at
                FROM turnos
                WHERE id = %s;
                """,
                (turno_id,),
            )
            turno = serialize_turno(cur.fetchone())

    return jsonify(turno), 201


@app.put("/api/turnos/<int:turno_id>")
def actualizar_turno(turno_id):
    data = request.get_json(silent=True) or {}
    validation_error = validate_turno(data)

    if validation_error:
        return jsonify(validation_error), 400

    if fetch_turno(turno_id) is None:
        return jsonify({"error": "Turno no encontrado"}), 404

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE turnos
                SET mascota = %s,
                    duenio = %s,
                    fecha = %s,
                    hora = %s,
                    motivo = %s
                WHERE id = %s;
                """,
                (
                    data["mascota"],
                    data["duenio"],
                    data["fecha"],
                    data["hora"],
                    data.get("motivo"),
                    turno_id,
                ),
            )

        conn.commit()

    return jsonify(fetch_turno(turno_id))


@app.delete("/api/turnos/<int:turno_id>")
def eliminar_turno(turno_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM turnos WHERE id = %s;", (turno_id,))

            if cur.rowcount == 0:
                return jsonify({"error": "Turno no encontrado"}), 404

        conn.commit()

    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
