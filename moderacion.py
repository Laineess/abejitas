# -*- coding: utf-8 -*-
"""Moderación de mensajes basada en la librería spanlp.

Sustituye al diccionario manual anterior. spanlp trae su propio corpus de
groserías por país (21 países hispanohablantes), así que aquí solo se
configura y se normaliza el texto de entrada para atrapar evasiones
(acentos, may/min, puntuación intercalada, "leet speak" y erratas).

API pública (la que consume app.py):
    buscar_groseria(texto) -> str | None   palabra detectada o None
    es_limpio(texto)       -> bool
"""

import unicodedata

from better_profanity import profanity  # 4ª capa: palabrotas en inglés

profanity.load_censor_words()

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
    "patarajad", "mugros", "zarrapastros", "escori",
    # inglés
    "fuck", "fuk", "fck", "fucc", "shit", "bitch", "asshole", "ashole",
    "motherfuck", "mothafuck", "cunt", "nigg", "fagg", "whore", "slut",
    "retard", "dumbass", "jackass", "douche", "wank", "twat", "pussy",
    "bastard", "dickhead",
]

# --------------------------------------------------------------------- config

# Todos los países hispanohablantes que soporta spanlp.
_PAISES = list(Country)

# Términos frecuentes que el corpus de spanlp no trae y conviene añadir.
# (Es una lista MÍNIMA, no el diccionario gigante anterior.)
_INCLUIR = [
    "no mames", "conchetumare", "conchesumadre", "csm", "ctm", "qliao",
    "hijueputa", "malparido", "verga", "pendejada",
]

# Palabras que spanlp podría marcar y aquí queremos permitir (falsos
# positivos). Vacío por ahora; agregar aquí si aparece alguno.
_EXCLUIR = []

# Detector principal. distance_metric=Jaccard atrapa erratas leves
# ("pvta" ~ "puta") sin necesidad de listarlas.
_detector = Palabrota(
    countries=_PAISES,
    include=_INCLUIR,
    exclude=_EXCLUIR,
    distance_metric=JaccardIndex(threshold=0.8),
)

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


def _normalizar(texto: str) -> str:
    texto = texto.lower().translate(_MAPA_LEET)
    # Quitar acentos (á -> a) pero conservar la ñ
    texto = texto.replace("ñ", "\x00")
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


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
            frase_d = _contiene_frase(
                variante, [_normalizar(f) for f in _FRASES_DENIGRANTES])
            if frase_d:
                return f"discurso de odio ({g.group(1)} + {frase_d})"
    # 4ª capa: better-profanity sobre el texto ya normalizado (sin acentos ni
    # leet), así atrapa las evasiones que el resto del pipeline ya desarmó.
    normal = _normalizar(texto)
    if profanity.contains_profanity(normal):
        return "profanity"
    return None


def es_limpio(texto: str) -> bool:
    return buscar_groseria(texto) is None
