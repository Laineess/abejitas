# -*- coding: utf-8 -*-
"""AWS Students Builder — muro de mensajes en vivo.

Sin base de datos: los mensajes aprobados NO se guardan, se transmiten en
tiempo real a la(s) pantalla(s) por WebSocket (flask-socketio). Solo se
conserva en memoria un búfer de los más recientes (se pierde al reiniciar),
suficiente para el panel de admin. El texto llega y sale siempre como
Unicode/UTF-8.
"""

import io
import os
import socket
import threading
import time
from collections import deque

import qrcode
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from flask_socketio import SocketIO

from moderacion import buscar_groseria, solo_texto

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COOLDOWN = 10
MAX_CARACTERES = 100
MAX_RECIENTES = 50   # cuántos mensajes recientes se guardan en memoria

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
# jsonify sin escapar acentos/emojis (respuesta UTF-8 legible)
app.json.ensure_ascii = False
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")

# async_mode="threading": sin eventlet/gevent, corre sobre el mismo servidor.
# Suficiente para una pantalla; para muchos clientes tocaría un worker async.
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# Contraseña del panel de admin (cámbiala con la variable de entorno)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "abejas2026")

# ------------------------------------------------------------- estado en memoria
# Flags on/off del panel. Whitelist: solo estas claves se pueden alternar.
FLAGS = {"mostrar_mensajes", "audio"}

_lock = threading.Lock()
_mensajes = deque(maxlen=MAX_RECIENTES)   # recientes: {"id": int, "texto": str}
_siguiente_id = 1
_flags = {"mostrar_mensajes": True, "audio": True}
_ultimo_envio = {}                         # cooldown: ip -> timestamp del último envío


def ip_cliente() -> str:
    # Detrás de un proxy/balanceador llega en X-Forwarded-For
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else (request.remote_addr or "?")


def flag(clave: str) -> bool:
    with _lock:
        return _flags.get(clave, False)


def set_flag(clave: str, activado: bool):
    with _lock:
        _flags[clave] = bool(activado)


def guardar_mensaje(texto: str) -> dict:
    """Registra el mensaje en el búfer en memoria y devuelve {'id', 'texto'}."""
    global _siguiente_id
    with _lock:
        mensaje = {"id": _siguiente_id, "texto": texto}
        _siguiente_id += 1
        _mensajes.append(mensaje)
    return mensaje


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
    # Solo texto: se descartan emojis y símbolos antes de todo lo demás
    texto = solo_texto((datos.get("texto") or ""))
    ip = ip_cliente()
    ahora = time.time()

    # Cooldown por visitante
    transcurrido = ahora - _ultimo_envio.get(ip, 0)
    if transcurrido < COOLDOWN:
        restante = int(COOLDOWN - transcurrido) + 1
        return jsonify(ok=False, error="cooldown", restante=restante,
                       mensaje=f"Espera {restante} s antes de enviar otro mensaje."), 429

    if not texto:
        return jsonify(ok=False, error="vacio",
                       mensaje="Escribe un mensaje de texto (sin solo emojis)."), 400

    if len(texto) > MAX_CARACTERES:
        return jsonify(ok=False, error="longitud",
                       mensaje=f"El mensaje no puede superar {MAX_CARACTERES} caracteres."), 400

    groseria = buscar_groseria(texto)
    if groseria:
        _ultimo_envio[ip] = ahora            # el intento también consume cooldown
        app.logger.warning("Mensaje rechazado de %s (palabra: %s)", ip, groseria)
        return jsonify(ok=False, error="groseria",
                       mensaje="⚠️ Tu mensaje contiene lenguaje ofensivo y no será "
                               "mostrado. Recuerda ser respetuoso. 🐝"), 400

    _ultimo_envio[ip] = ahora
    mensaje = guardar_mensaje(texto)
    # Empuja el mensaje a la pantalla en tiempo real (solo si está activada)
    if flag("mostrar_mensajes"):
        socketio.emit("mensaje", mensaje)
    return jsonify(ok=True,
                   mensaje="¡Gracias! Una abejita llevará tu mensaje a la pantalla. 🐝"), 201


@app.route("/api/estado")
def estado():
    with _lock:
        ultimo_id = _mensajes[-1]["id"] if _mensajes else 0
    return jsonify(activado=flag("mostrar_mensajes"), audio=flag("audio"),
                   ultimo_id=ultimo_id)


@app.route("/api/nuevos")
def nuevos():
    """Respaldo por polling para pantallas sin WebSocket."""
    if not flag("mostrar_mensajes"):
        return jsonify(activado=False, audio=flag("audio"), mensajes=[])
    after = request.args.get("after", 0, type=int)
    with _lock:
        nuevos = [m for m in _mensajes if m["id"] > after][:10]
    return jsonify(activado=True, audio=flag("audio"), mensajes=nuevos)


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

    with _lock:
        recientes = list(_mensajes)[-20:][::-1]
    return render_template("admin.html", autenticado=True, error=None,
                           activado=flag("mostrar_mensajes"),
                           audio=flag("audio"), mensajes=recientes)


@app.route("/admin/toggle/<clave>", methods=["POST"])
def admin_toggle(clave):
    if not session.get("admin"):
        return redirect(url_for("admin"))
    if clave in FLAGS:
        set_flag(clave, not flag(clave))
        # Empuja el nuevo estado a la pantalla al instante (mensajes / audio)
        socketio.emit("config", {"activado": flag("mostrar_mensajes"),
                                  "audio": flag("audio")})
    return redirect(url_for("admin"))


@app.route("/admin/prueba", methods=["POST"])
def admin_prueba():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    # Inyecta N mensajes de golpe para ver varias abejas hablando a la vez.
    # No se guardan en la DB (son de prueba): solo se empujan por socket.
    n = max(1, min(12, request.form.get("cantidad", 6, type=int)))
    for i in range(1, n + 1):
        socketio.emit("mensaje", {"id": -i, "texto": f"Mensaje de prueba {i}"})
    return redirect(url_for("admin"))


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    # 8000 y no 8080: ese puerto lo suelen ocupar Tomcat, XAMPP o Jenkins.
    # Para usar otro:  PORT=5050 python app.py
    puerto = int(os.environ.get("PORT", 8000))

    # Se comprueba el puerto antes de arrancar: si está ocupado, Werkzeug
    # imprime un error del sistema poco claro y sale, así que lo avisamos aquí.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as prueba:
        try:
            prueba.bind(("0.0.0.0", puerto))
        except OSError as err:
            print(f"\nNo se pudo abrir el puerto {puerto}: {err}\n"
                  f"Otro programa lo está usando. Arranca en otro puerto con:\n"
                  f"    $env:PORT={puerto + 1}; python app.py   (PowerShell)\n"
                  f"    PORT={puerto + 1} python app.py         (bash)\n")
            raise SystemExit(1)

    # allow_unsafe_werkzeug: usamos el server de Werkzeug a propósito (expo,
    # una pantalla). Para producción real, un worker async + gunicorn.
    socketio.run(app, host="0.0.0.0", port=puerto,
                 allow_unsafe_werkzeug=True)
