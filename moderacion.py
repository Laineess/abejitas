"""Filtro de groserías y discurso de odio para los mensajes de los alumnos.

Tres capas de detección sobre texto normalizado (minúsculas, sin acentos,
sin leet-speak como p3ndejo/k4g4d4, sin letras repetidas, sin separadores
tipo p.u.t.o):

1. RAICES  — coinciden por PREFIJO: "pito" atrapa "pitochico", "pitorrear";
             "pendej" atrapa "pendejada", "pendejisimo", etc.
2. EXACTAS y FRASES — palabras con riesgo de falso positivo (se exigen
             límites de palabra) y frases completas ("hijo de puta",
             "muerte a", "kill yourself").
3. ODIO    — co-ocurrencia: mención de un grupo protegido (judíos, gays,
             mujeres, indígenas...) junto a una expresión denigrante
             (roban, plaga, viven a costa, deberían morir...). Atrapa
             discurso de odio que no usa ninguna grosería.

Nota: ningún filtro léxico es perfecto al 100 %; esta configuración
prefiere BLOQUEAR DE MÁS (algún falso positivo raro) antes que dejar
pasar una ofensa.
"""

import re
import unicodedata

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

# ----------------------------------------------------------------- capa 2
# Palabras exactas (límite de palabra + plural/diminutivo), para términos
# que como prefijo darían falsos positivos ("menso" vs "mensaje",
# "teta" vs "tétanos", "ass" vs "assembly").
EXACTAS = [
    "menso", "mensa", "naco", "naca", "zorra", "perra", "golfa",
    "teta", "chichi", "pene", "semen", "vagina", "verija", "chocho",
    "culito", "tortillera", "sudaca", "nazi", "hitler", "feminazi",
    "pedorro", "pedorra", "cornudo", "cornuda", "prosti",
    "dick", "cock", "ass", "arse", "fag", "hoe", "tit", "tits",
    "bullshit", "boobs", "wtf", "stfu", "kys", "hdp", "ptm", "ctm",
    "csm", "alv", "vlv", "mms", "nmms", "gtfo", "milf", "simp",
]

# Frases completas (subcadena sobre el texto normalizado).
FRASES = [
    "hijo de puta", "hija de puta", "hijo de tu", "hija de tu",
    "chinga tu madre", "chingada madre", "puta madre", "madre que te",
    "a la verga", "vales verga", "vete a la verga", "me la pelas",
    "me la mamas", "come mierda", "concha de tu madre", "conchetumare",
    "la concha de", "no mames", "no manches guey", "que te den",
    "muerte a", "maten a", "matenlos", "hay que matar", "voy a matar",
    "te voy a matar", "te voy a violar", "te voy a partir",
    "ojala te mueras", "ojala se mueran", "deberias morir",
    "deberian morir", "kill yourself", "go kill", "eat shit",
    "fuck you", "fuck off", "son of a bitch", "piece of shit",
    "suck my", "blow me", "muerto de hambre", "muertos de hambre",
]

# ----------------------------------------------------------------- capa 3
# Discurso de odio por co-ocurrencia: GRUPO protegido + expresión
# DENIGRANTE en el mismo mensaje.
GRUPOS = [
    "judio", "judia", "negro", "negra", "gay", "gei", "geis",
    "lesbiana", "homosexual", "bisexual", "trans", "transexual",
    "travesti", "musulman", "islamico", "cristiano", "catolico",
    "mormon", "ateo", "indigena", "indio", "india", "chino", "china",
    "japones", "coreano", "arabe", "gringo", "gringa", "latino",
    "latina", "moreno", "morena", "migrante", "inmigrante",
    "extranjero", "extranjera", "mujer", "hombre", "niña", "niño",
    "anciano", "anciana", "viejo", "vieja", "discapacitado",
    "discapacitada", "autista", "gordo", "gorda", "flaco", "flaca",
    "enano", "enana", "pobre", "rico", "otaku", "friki",
]

DENIGRANTES = [
    "odio", "odia", "odian", "asco", "asquer", "roba", "roban",
    "ladron", "ladrones", "rata", "ratas", "plaga", "parasit",
    "basura", "lacra", "inferior", "apesta", "apestos", "maldit",
    "matar", "matarl", "matenl", "extermin", "desaparec", "invasor",
    "ilegal", "delincuent", "criminal", "terrorist", "violador",
    "sucio", "sucia", "cochino", "cochina", "estorba", "sobra",
    "no sirven", "no sirve", "no deberia", "no merecen", "no merece",
    "a costa", "viven de", "vive de", "culpa de", "fuera de aqui",
    "fuera del pais", "no son personas", "no es persona", "esclavo",
    "quemar", "colgar", "fusilar", "deportar", "inutil",
]

_MAPA_LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s", "!": "i", "+": "t",
})

# Sustituciones fonéticas para evasiones: k4g4d4 -> cagada, pvta -> puta
_MAPA_FONETICO = str.maketrans({"k": "c", "q": "c", "v": "u", "z": "s"})

# Sufijos para las EXACTAS (plurales, diminutivos, aumentativos)
_SUFIJOS = (r"(?:s|es|a|o|as|os|ita|ito|itas|itos|illa|illo|illas|illos"
            r"|ote|ota|otes|otas|ada|adas|ado|ados|azo|aza|azos|azas"
            r"|on|ona|ones|onas|udo|uda|udos|udas|ero|era|eros|eras"
            r"|isimo|isima|isimos|isimas|zote|zotes)?")


def _normalizar(texto: str) -> str:
    texto = texto.lower().translate(_MAPA_LEET)
    # Quitar acentos (á -> a) pero conservar la ñ
    texto = texto.replace("ñ", "\x00")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.replace("\x00", "ñ")
    # Todo lo que no sea letra/número se vuelve espacio (p.u.t.o -> p u t o)
    texto = re.sub(r"[^a-z0-9ñ]+", " ", texto)
    return texto.strip()


def _variantes(texto: str):
    """Genera variantes del texto para atrapar evasiones."""
    normal = _normalizar(texto)
    base = [
        normal,
        # Letras repetidas colapsadas: "puuuuto" -> "puto"
        re.sub(r"(.)\1+", r"\1", normal),
        # Espacios eliminados: "p u t o" -> "puto"
        normal.replace(" ", ""),
    ]
    for v in base:
        yield v
        yield v.translate(_MAPA_FONETICO)


def _formas(palabra: str):
    """Forma normalizada + forma fonética de una entrada del diccionario."""
    norm = _normalizar(palabra)
    formas = {norm, norm.translate(_MAPA_FONETICO)}
    return [f for f in formas if f]


def _regex_alternativas(palabras, sufijo=""):
    alternativas = sorted({f for p in palabras for f in _formas(p)},
                          key=len, reverse=True)
    cuerpo = "|".join(re.escape(a) for a in alternativas)
    return re.compile(r"(?:^|\s)(" + cuerpo + r")" + sufijo + r"(?=\s|$)")


# Raíces: prefijo + cualquier terminación ("pito" -> "pitochico")
_RE_RAICES = _regex_alternativas(RAICES, sufijo=r"\w*")
# Exactas: palabra completa + sufijo común ("teta" -> "tetas", no "tétanos")
_RE_EXACTAS = _regex_alternativas(EXACTAS, sufijo=_SUFIJOS)
# Grupos y denigrantes: prefijo (cubre plurales y conjugaciones)
_RE_GRUPOS = _regex_alternativas(GRUPOS, sufijo=r"\w*")
_RE_DENIGRANTES = _regex_alternativas(
    [d for d in DENIGRANTES if " " not in d], sufijo=r"\w*")
_FRASES_DENIGRANTES = [d for d in DENIGRANTES if " " in d]

_FRASES_NORM = sorted({f for fr in FRASES for f in _formas(fr)},
                      key=len, reverse=True)


def _contiene_frase(variante: str, frases) -> str | None:
    con_margen = f" {variante} "
    for frase in frases:
        if f" {frase} " in con_margen or frase.replace(" ", "") == variante:
            return frase
    return None


def buscar_groseria(texto: str):
    """Devuelve la palabra/frase prohibida encontrada, o None si es limpio."""
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
    return None


def es_limpio(texto: str) -> bool:
    return buscar_groseria(texto) is None
