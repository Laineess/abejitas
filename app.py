# -*- coding: utf-8 -*-
"""AWS Students Builder — muro de mensajes en vivo.

Sin base de datos: los mensajes aprobados NO se guardan, se transmiten en
tiempo real a la(s) pantalla(s) por WebSocket (flask-sock). Solo se conserva
en memoria un búfer de los más recientes (se pierde al reiniciar), suficiente
para el panel de admin. El texto llega y sale siempre como Unicode/UTF-8.
"""

import io
import json
import os
import queue
import threading
import time
from collections import deque

import qrcode
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from flask_sock import Sock

from moderacion import buscar_groseria

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COOLDOWN = 10
MAX_CARACTERES = 100
MAX_RECIENTES = 50   # cuántos mensajes recientes se guardan en memoria

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
# jsonify sin escapar acentos/emojis (respuesta UTF-8 legible)
app.json.ensure_ascii = False
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
sock = Sock(app)

# Contraseña del panel de admin (cámbiala con la variable de entorno)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "abejas2026")

# ------------------------------------------------------------- estado en memoria
_lock = threading.Lock()
_mensajes = deque(maxlen=MAX_RECIENTES)   # recientes: {"id": int, "texto": str}
_siguiente_id = 1
_mostrar = True                            # ¿se muestran los mensajes en pantalla?
_clientes = set()                          # colas de las pantallas conectadas por WS
_ultimo_envio = {}                         # cooldown: ip -> timestamp del último envío


def ip_cliente() -> str:
    # Detrás de un proxy/balanceador llega en X-Forwarded-For
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else (request.remote_addr or "?")


def _difundir(evento: dict):
    """Envía un evento JSON-serializable a todas las pantallas conectadas."""
    with _lock:
        clientes = list(_clientes)
    for cola in clientes:
        try:
            cola.put(evento)
        except Exception:
            pass


# --------------------------------------------------------------- WebSocket

@sock.route("/ws")
def ws_pantalla(ws):
    """Canal de solo salida: la pantalla recibe estado y mensajes nuevos."""
    cola = queue.SimpleQueue()

    with _lock:
        _clientes.add(cola)
        estado_inicial = {"tipo": "estado", "activado": _mostrar}

    ws.send(json.dumps(estado_inicial))
    try:
        while True:
            try:
                evento = cola.get(timeout=25)
            except queue.Empty:
                evento = {"tipo": "ping"}     # latido para detectar desconexión
            ws.send(json.dumps(evento))
    except Exception:
        pass                                  # cliente cerró la conexión
    finally:
        with _lock:
            _clientes.discard(cola)


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

    # Cooldown por visitante
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
        _ultimo_envio[ip] = ahora            # el intento también consume cooldown
        app.logger.warning("Mensaje rechazado de %s (palabra: %s)", ip, groseria)
        return jsonify(ok=False, error="groseria",
                       mensaje="⚠️ Tu mensaje contiene lenguaje ofensivo y no será "
                               "mostrado. Recuerda ser respetuoso. 🐝"), 400

    _ultimo_envio[ip] = ahora
    global _siguiente_id
    with _lock:
        msg = {"id": _siguiente_id, "texto": texto}
        _siguiente_id += 1
        _mensajes.append(msg)
        mostrar = _mostrar

    if mostrar:
        _difundir({"tipo": "mensaje", "id": msg["id"], "texto": texto})

    return jsonify(ok=True,
                   mensaje="¡Gracias! Una abejita llevará tu mensaje a la pantalla. 🐝"), 201


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
        activado = _mostrar
    return render_template("admin.html", autenticado=True, error=None,
                           activado=activado, mensajes=recientes)


@app.route("/admin/toggle", methods=["POST"])
def admin_toggle():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    global _mostrar
    with _lock:
        _mostrar = not _mostrar
        activado = _mostrar
    _difundir({"tipo": "estado", "activado": activado})
    return redirect(url_for("admin"))


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    # threaded=True: atiende WebSockets y HTTP a la vez con el servidor de dev
    app.run(host="0.0.0.0", port=puerto, threaded=True)
