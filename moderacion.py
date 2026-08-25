# -*- coding: utf-8 -*-
"""Moderación de mensajes en español e inglés.

El texto de entrada se normaliza para atrapar evasiones (acentos, may/min,
"leet speak" y letras separadas) y luego pasa por cuatro capas:

    1. raíces      — palabras que EMPIEZAN por una raíz ofensiva
    2. exactas     — palabras completas (donde el prefijo daría falsos positivos)
    3. frases      — groserías de varias palabras
    4. odio        — grupo protegido + expresión denigrante
    5. profanity   — better-profanity, para el inglés que no cubren las listas

API pública (la que consume app.py):
    buscar_groseria(texto) -> str | None   palabra detectada o None
    es_limpio(texto)       -> bool
    solo_texto(texto)      -> str          sin emojis ni símbolos
"""

import logging
import os
import re
import threading
import unicodedata

from better_profanity import profanity  # 4ª capa: palabrotas en inglés

profanity.load_censor_words()

_logger = logging.getLogger(__name__)
_detoxify_model = None
_detoxify_lock = threading.Lock()
DETOXIFY_UMBRAL = float(os.environ.get("DETOXIFY_UMBRAL", "0.65"))

# ----------------------------------------------------------------- capa 1
# Raíces: se bloquea cualquier palabra que EMPIECE con ellas.
# Elegidas para no chocar con palabras normales (no "verg" porque
# bloquearía "vergüenza"; no "mens" porque bloquearía "mensaje").
RAICES = [
    # español — groserías y sexuales
    "put", "pendej", "ching", "verga", "vergaz", "verguiz", "vrga",
    "mierd", "miard", "cabron", "culer", "culo", "caga", "cago", "cague",
    "mamad", "mamon", "mames", "mamast", "chupam", "chupal",
    "joto", "jotol", "jotit", "maric", "pito", "pija", "pijud",
    "panoch", "polla", "ojete", "nalg", "huevon", "guevon", "webon",
    "wevon", "puñet", "punet", "puñal", "punal", "piruj", "prostitut",
    "ramera", "gilipoll", "bolud", "pelotud", "conchud", "malparid",
    "hijueput", "hijodeput", "gonorre", "marran", "carajo", "joder",
    "jodid", "jodet", "coño", "cojon", "cojud", "carech", "chimb",
    "pichul", "pinch", "wil", "guil", "verguer", "madraz", "madread",
    "madrear", "putiz", "cerd",
    # español — insultos
    "estupid", "imbecil", "idiot", "tarad", "babos", "zopenc",
    "mongol", "retrasad", "subnormal", "machorr", "lenchon", "invertid",
    "patarajad", "mugros", "zarrapastros", "escori", "naco", "menso",
    "sidos",
    # inglés
    "fuck", "fuk", "fck", "fucc", "shit", "bitch", "asshole", "ashole",
    "motherfuck", "mothafuck", "cunt", "nigg", "fagg", "whore", "slut",
    "retard", "dumbass", "jackass", "douche", "wank", "twat", "pussy",
    "bastard", "dickhead",
]

# ----------------------------------------------------------------- capa 2
# Palabras completas: buscarlas por prefijo daría falsos positivos
# ("ano" bloquearía "anotar", "sexo" bloquearía "sexto").
EXACTAS = [
    "sexo", "semen", "pene", "vagina", "teta", "tetas", "chichis",
    "zorra", "zorras", "perra", "perras", "coger", "cojer", "nepe",
    "csm", "ctm", "qliao", "wtf", "stfu",
    "gei", "geis",  # variante fonética de "gay" usada como insulto
]

# ----------------------------------------------------------------- capa 3
# Groserías de varias palabras (las de una sola ya las cubren las raíces).
FRASES = [
    "no mames", "no manches", "hijo de puta", "hija de puta",
    "chinga tu madre", "chinga a tu madre", "vete a la mierda",
    "la concha de tu madre", "conchetumare", "conchesumadre",
    "me vale verga", "puta madre", "hijo de perra", "vete al carajo",
]

# ----------------------------------------------------------------- capa 4
# Discurso de odio: solo se bloquea si aparece un grupo protegido JUNTO a
# una expresión denigrante. Por separado son palabras legítimas.
GRUPOS = [
    "judio", "judia", "gay", "lesbian", "homosexual", "trans", "travesti",
    "indigen", "migrant", "inmigrant", "musulman", "gitan", "sudaca",
    "discapacitad", "negro", "negra", "chino", "china", "boliviano",
    "peruano", "haitiano", "venezolano", "mexicano",
]

DENIGRANTES = [
    "asqueros", "repugnant", "inferior", "subhuman", "infrahuman",
    "plaga", "lacra", "escoria", "apestan", "estorban", "parasit",
]

FRASES_DENIGRANTES = [
    "deberian morir", "no deberian existir", "hay que matar",
    "fuera de mi pais", "no merecen vivir", "muerte a los",
    "son una plaga", "que se mueran",
]

# Sustitución "leet"/fonética para evasiones: put0 -> puto, pv7a -> puta.
_MAPA_LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s", "!": "i", "+": "t",
    "k": "c", "v": "u", "z": "s",
})


# ---------------------------------------------------------------- utilidades

def _asegurar_texto(valor) -> str:
    """Coacciona cualquier entrada a texto Unicode (UTF-8) válido y limpio.

    - Bytes se decodifican como UTF-8 (ignorando lo que no lo sea).
    - Se normaliza a NFC (forma canónica) para que 'é' compuesta y
      precompuesta cuenten igual.
    - Se eliminan caracteres de control no imprimibles.
    """
    if isinstance(valor, bytes):
        valor = valor.decode("utf-8", errors="ignore")
    elif not isinstance(valor, str):
        valor = str(valor)
    valor = unicodedata.normalize("NFC", valor)
    return "".join(c for c in valor if c == "\n" or not unicodedata.category(c).startswith("C"))


def solo_texto(texto: str) -> str:
    """Quita emojis y símbolos: deja letras, números, espacios y puntuación.

    Se rechazan las categorías Unicode de símbolo (S*) y de control/formato
    (C*, incluye ZWJ y selectores de variación de los emojis). Conserva
    acentos, ñ y signos normales (¿ ¡ ? ! , . …).
    """
    limpio = "".join(
        c for c in texto
        if unicodedata.category(c)[0] not in ("S", "C")
        and not 0xFE00 <= ord(c) <= 0xFE0F   # selectores de variación de emoji
        or c in "\t\n"
    )
    return re.sub(r"\s+", " ", limpio).strip()


def _sin_acentos(texto: str) -> str:
    """Quita acentos (á -> a) pero conserva la ñ."""
    texto = texto.replace("ñ", "\x00").replace("Ñ", "\x00")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.replace("\x00", "ñ")


def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con la sustitución leet aplicada."""
    return _sin_acentos(_asegurar_texto(texto).lower()).translate(_MAPA_LEET)


def _variantes(texto: str):
    """Formas normalizadas del texto para atrapar evasiones."""
    base = _sin_acentos(_asegurar_texto(texto).lower())
    leet = base.translate(_MAPA_LEET)
    formas = {
        base,                    # original en minúsculas sin acentos
        leet,                    # con sustitución leet/fonética
        leet.replace(" ", ""),   # "p u t o" -> "puto"
    }
    return [f for f in formas if f.strip()]


def _contiene_frase(texto: str, frases):
    """Devuelve la primera frase de la lista contenida en el texto, o None."""
    for frase in frases:
        if frase and frase in texto:
            return frase
    return None


def _detectar_con_detoxify(texto: str):
    """Devuelve una etiqueta si Detoxify considera tóxico el texto."""
    global _detoxify_model
    if _detoxify_model is None:
        with _detoxify_lock:
            if _detoxify_model is None:
                try:
                    from detoxify import Detoxify
                    _detoxify_model = Detoxify("multilingual", device="cpu")
                except Exception as error:
                    _logger.warning("No se pudo cargar Detoxify: %s", error)
                    _detoxify_model = False
    if not _detoxify_model:
        return None

    try:
        resultado = _detoxify_model.predict(texto)
        if resultado.get("toxicity", 0) >= DETOXIFY_UMBRAL:
            return "detoxify (toxicidad >= %.2f)" % DETOXIFY_UMBRAL
    except Exception as error:
        _logger.warning("Falló la moderación con Detoxify: %s", error)
    return None


# ------------------------------------------------------- expresiones regulares
# Se compilan una sola vez al importar. Las raíces se ordenan de más larga a
# más corta para que el grupo capturado sea la coincidencia más específica.

def _alternancia(palabras):
    return "|".join(re.escape(p) for p in sorted(set(palabras), key=len, reverse=True))


# Raíz al principio de palabra: "put" atrapa "puto", "putazo", "putiza".
_RE_RAICES = re.compile(rf"\b({_alternancia(RAICES)}\w*)", re.UNICODE)
# Palabra completa: no atrapa prefijos.
_RE_EXACTAS = re.compile(rf"\b({_alternancia(EXACTAS)})\b", re.UNICODE)
_RE_GRUPOS = re.compile(rf"\b({_alternancia(GRUPOS)}\w*)", re.UNICODE)
_RE_DENIGRANTES = re.compile(rf"\b({_alternancia(DENIGRANTES)}\w*)", re.UNICODE)

_FRASES_NORM = [_normalizar(f) for f in FRASES]
_FRASES_DENIGRANTES_NORM = [_normalizar(f) for f in FRASES_DENIGRANTES]


# ------------------------------------------------------------- API pública

def buscar_groseria(texto: str):
    """Devuelve la palabra ofensiva detectada, o None si el texto es limpio."""
    for variante in _variantes(texto):
        m = _RE_RAICES.search(variante)
        if m:
            return m.group(1)
        m = _RE_EXACTAS.search(variante)
        if m:
            return m.group(1)
        frase = _contiene_frase(variante, _FRASES_NORM)
        if frase:
            return frase
        # Discurso de odio: grupo protegido + expresión denigrante
        g = _RE_GRUPOS.search(variante)
        if g:
            d = _RE_DENIGRANTES.search(variante)
            if d:
                return f"discurso de odio ({g.group(1)} + {d.group(1)})"
            frase_d = _contiene_frase(variante, _FRASES_DENIGRANTES_NORM)
            if frase_d:
                return f"discurso de odio ({g.group(1)} + {frase_d})"
    # Última capa: better-profanity sobre el texto en minúsculas y sin acentos.
    # No se le pasa la variante leet a propósito: el mapa convierte k -> c, lo
    # que rompería palabras inglesas del corpus ("jerk" -> "jerc").
    if profanity.contains_profanity(_sin_acentos(_asegurar_texto(texto).lower())):
        return "profanity"
    return _detectar_con_detoxify(texto)


def es_limpio(texto: str) -> bool:
    return buscar_groseria(texto) is None
