import io
import os
import sqlite3
import time

import qrcode
from flask import (Flask, g, jsonify, redirect, render_template, request,
                   send_file, session, url_for)

from moderacion import buscar_groseria

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mensajes.db")

COOLDOWN = 10
MAX_CARACTERES = 100

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")

# Contraseña del panel de admin (cámbiala con la variable de entorno)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "abejas2026")

# Cooldown en memoria: ip -> timestamp del último envío
_ultimo_envio = {}


# ---------------------------------------------------------------- base de datos

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def cerrar_db(_exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            texto  TEXT NOT NULL,
            creado REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );
        INSERT OR IGNORE INTO config (clave, valor) VALUES ('mostrar_mensajes', '1');
    """)
    con.commit()
    con.close()


def mostrar_activado() -> bool:
    fila = get_db().execute(
        "SELECT valor FROM config WHERE clave = 'mostrar_mensajes'").fetchone()
    return fila is not None and fila["valor"] == "1"


def set_mostrar(activado: bool):
    db = get_db()
    db.execute("UPDATE config SET valor = ? WHERE clave = 'mostrar_mensajes'",
               ("1" if activado else "0",))
    db.commit()


def ip_cliente() -> str:
    # Detrás de un proxy/balanceador llega en X-Forwarded-For
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else (request.remote_addr or "?")


# --------------------------------------------------------------------- páginas

@app.route("/")
def pantalla():
    return render_template("display.html")


@app.route("/mensaje")
def pagina_mensaje():
    return render_template("mensaje.html", max_caracteres=MAX_CARACTERES)


@app.route("/qr.png")
def qr_png():
    url = request.url_root.rstrip("/") + url_for("pagina_mensaje")
    img = qrcode.make(url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ------------------------------------------------------------------------- API

@app.route("/api/mensaje", methods=["POST"])
def recibir_mensaje():
    datos = request.get_json(silent=True) or {}
    texto = (datos.get("texto") or "").strip()
    ip = ip_cliente()
    ahora = time.time()

    # Cooldown de 10 segundos por visitante
    transcurrido = ahora - _ultimo_envio.get(ip, 0)
    if transcurrido < COOLDOWN:
        restante = int(COOLDOWN - transcurrido) + 1
        return jsonify(ok=False, error="cooldown", restante=restante,
                       mensaje=f"Espera {restante} s antes de enviar otro mensaje."), 429

    if not texto:
        return jsonify(ok=False, error="vacio",
                       mensaje="Escribe un mensaje antes de enviar."), 400

    if len(texto) > MAX_CARACTERES:
        return jsonify(ok=False, error="longitud",
                       mensaje=f"El mensaje no puede superar {MAX_CARACTERES} caracteres."), 400

    groseria = buscar_groseria(texto)
    if groseria:
        # Cuenta como intento: también consume el cooldown
        _ultimo_envio[ip] = ahora
        app.logger.warning("Mensaje rechazado de %s (palabra: %s)", ip, groseria)
        return jsonify(ok=False, error="groseria",
                       mensaje="⚠️ Tu mensaje contiene lenguaje ofensivo y no será "
                               "mostrado. Recuerda ser respetuoso. 🐝"), 400

    _ultimo_envio[ip] = ahora
    db = get_db()
    db.execute("INSERT INTO mensajes (texto, creado) VALUES (?, ?)", (texto, ahora))
    db.commit()
    return jsonify(ok=True,
                   mensaje="¡Gracias! Una abejita llevará tu mensaje a la pantalla. 🐝"), 201


@app.route("/api/estado")
def estado():
    fila = get_db().execute("SELECT MAX(id) AS ultimo FROM mensajes").fetchone()
    return jsonify(activado=mostrar_activado(), ultimo_id=fila["ultimo"] or 0)


@app.route("/api/nuevos")
def nuevos():
    if not mostrar_activado():
        return jsonify(activado=False, mensajes=[])
    after = request.args.get("after", 0, type=int)
    filas = get_db().execute(
        "SELECT id, texto FROM mensajes WHERE id > ? ORDER BY id LIMIT 10",
        (after,)).fetchall()
    return jsonify(activado=True,
                   mensajes=[{"id": f["id"], "texto": f["texto"]} for f in filas])


# ----------------------------------------------------------------------- admin

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and not session.get("admin"):
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            return render_template("admin.html", autenticado=False,
                                   error="Contraseña incorrecta.")

    if not session.get("admin"):
        return render_template("admin.html", autenticado=False, error=None)

    ultimos = get_db().execute(
        "SELECT id, texto, creado FROM mensajes ORDER BY id DESC LIMIT 20").fetchall()
    return render_template("admin.html", autenticado=True, error=None,
                           activado=mostrar_activado(), mensajes=ultimos)


@app.route("/admin/toggle", methods=["POST"])
def admin_toggle():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    set_mostrar(not mostrar_activado())
    return redirect(url_for("admin"))


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


init_db()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=puerto)
