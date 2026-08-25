# -*- coding: utf-8 -*-
"""AWS Students Builder — muro de mensajes en vivo.

Sin base de datos: los mensajes aprobados NO se guardan, se transmiten en
tiempo real a la(s) pantalla(s) por WebSocket (flask-socketio). Solo se
conserva en memoria un búfer de los más recientes (se pierde al reiniciar),
suficiente para el panel de admin. El texto llega y sale siempre como
Unicode/UTF-8.
"""

import io
import json
import os
import socket
import threading
import time
from collections import deque

import qrcode
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_file, session, url_for)
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

from moderacion import buscar_groseria, solo_texto

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

# --------------------------------------------------------- ponentes (persistidos)
PONENTES_FILE = os.path.join(BASE_DIR, "ponentes.json")


def _cargar_ponentes() -> tuple[list, int | None]:
    """Lee la lista de ponentes y el índice activo desde el JSON."""
    try:
        with open(PONENTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("ponentes", []), data.get("activo")
    except (FileNotFoundError, json.JSONDecodeError):
        return [], None


def _guardar_ponentes(ponentes: list, activo: int | None):
    """Persiste la lista de ponentes y el índice activo al JSON."""
    with open(PONENTES_FILE, "w", encoding="utf-8") as f:
        json.dump({"ponentes": ponentes, "activo": activo},
                  f, ensure_ascii=False, indent=2)


_ponentes, _ponente_activo = _cargar_ponentes()


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


@app.route("/presentacion")
def presentacion():
    return render_template("presentacion.html")


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


@app.route("/api/ponente-activo")
def ponente_activo():
    """Devuelve el ponente que se está mostrando en /presentacion."""
    with _lock:
        if _ponente_activo is not None and _ponente_activo < len(_ponentes):
            return jsonify(ponente=_ponentes[_ponente_activo])
    return jsonify(ponente=None)


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
                           audio=flag("audio"), mensajes=recientes,
                           ponentes=_ponentes,
                           ponente_activo=_ponente_activo)


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


# --------------------------------------------------------- admin: ponentes

def _emitir_ponente():
    """Empuja el ponente activo (o None) a /presentacion vía Socket.IO."""
    with _lock:
        if _ponente_activo is not None and _ponente_activo < len(_ponentes):
            socketio.emit("ponente", _ponentes[_ponente_activo])
        else:
            socketio.emit("ponente", None)


@app.route("/admin/ponentes", methods=["POST"])
def admin_agregar_ponente():
    global _ponentes, _ponente_activo
    if not session.get("admin"):
        return redirect(url_for("admin"))
    ponente = {
        "nombre":    (request.form.get("nombre") or "").strip(),
        "rol":       (request.form.get("rol") or "").strip(),
        "tema":      (request.form.get("tema") or "").strip(),
        "instagram": (request.form.get("instagram") or "").strip().lstrip("@"),
        "linkedin":  (request.form.get("linkedin") or "").strip(),
        "carrusel_texto": (request.form.get("carrusel_texto") or "").strip(),
        "imagenes": []
    }
    if ponente["nombre"]:
        archivos = request.files.getlist("imagenes")
        archivos_validos = [f for f in archivos if f.filename]
        if 3 <= len(archivos_validos) <= 5:
            for f in archivos_validos:
                filename = f"{int(time.time())}_{secure_filename(f.filename)}"
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                ponente["imagenes"].append(url_for("static", filename=f"uploads/{filename}"))
        with _lock:
            _ponentes.append(ponente)
            _guardar_ponentes(_ponentes, _ponente_activo)
    return redirect(url_for("admin"))


@app.route("/admin/ponentes/<int:idx>/activar", methods=["POST"])
def admin_activar_ponente(idx):
    global _ponente_activo
    if not session.get("admin"):
        return redirect(url_for("admin"))
    with _lock:
        if 0 <= idx < len(_ponentes):
            _ponente_activo = idx
            _guardar_ponentes(_ponentes, _ponente_activo)
    _emitir_ponente()
    return redirect(url_for("admin"))


@app.route("/admin/ponentes/<int:idx>/eliminar", methods=["POST"])
def admin_eliminar_ponente(idx):
    global _ponentes, _ponente_activo
    if not session.get("admin"):
        return redirect(url_for("admin"))
    with _lock:
        if 0 <= idx < len(_ponentes):
            _ponentes.pop(idx)
            # Ajustar el índice activo tras la eliminación
            if _ponente_activo is not None:
                if idx == _ponente_activo:
                    _ponente_activo = None
                elif idx < _ponente_activo:
                    _ponente_activo -= 1
            _guardar_ponentes(_ponentes, _ponente_activo)
    _emitir_ponente()
    return redirect(url_for("admin"))


@app.route("/admin/ponentes/limpiar", methods=["POST"])
def admin_limpiar_ponente():
    global _ponente_activo
    if not session.get("admin"):
        return redirect(url_for("admin"))
    with _lock:
        _ponente_activo = None
        _guardar_ponentes(_ponentes, _ponente_activo)
    _emitir_ponente()
    return redirect(url_for("admin"))


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    # 8000 y no 8080: ese puerto lo suelen ocupar Tomcat, XAMPP o Jenkins.
    # Para usar otro:  PORT=5050 python app.py
    puerto = int(os.environ.get("PORT", 8000))

    # allow_unsafe_werkzeug: usamos el server de Werkzeug a propósito (expo,
    # una pantalla). Para producción real, un worker async + gunicorn.
    # use_reloader: detecta cambios en .py y templates y reinicia solo.
    socketio.run(app, host="0.0.0.0", port=puerto,
                 debug=True, use_reloader=True,
                 allow_unsafe_werkzeug=True)
