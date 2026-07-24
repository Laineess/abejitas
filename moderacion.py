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

from spanlp.palabrota import Palabrota
from spanlp.domain.countries import Country
from spanlp.domain.strategies import JaccardIndex

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


def _sin_acentos(texto: str) -> str:
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
        if _detector.contains_palabrota(variante):
            # Intentar identificar la palabra concreta para el log.
            for token in variante.split():
                if _detector.contains_palabrota(token):
                    return token
            return "lenguaje ofensivo"
    return None


def es_limpio(texto: str) -> bool:
    return buscar_groseria(texto) is None
