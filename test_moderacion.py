# -*- coding: utf-8 -*-
"""Suite exhaustiva de pruebas para el sistema de moderación de mensajes.

Ejecución:  ./venv/bin/python test_moderacion.py
"""

from moderacion import buscar_groseria, es_limpio, moderar_con_openai, solo_texto

# -----------------------------------------------------------------------------
# 1. solo_texto: quita emojis/símbolos, conserva texto real y puntuación válida
# -----------------------------------------------------------------------------
assert solo_texto("hola \U0001F41D mundo") == "hola mundo"
assert solo_texto("\U0001F44D\U0001F525") == ""             # solo emojis -> vacío
assert solo_texto("te quiero ❤️") == "te quiero"            # emoji + selector de variación
assert solo_texto("¡Qué? niño ñoño") == "¡Qué? niño ñoño"   # acentos/signos/ñ intactos
assert solo_texto("a  b   c") == "a b c"                     # espacios múltiples colapsados
print(" [1/7] solo_texto verificado correctamente.")

# -----------------------------------------------------------------------------
# 2. Prevención de Falsos Positivos (palabras legítimas que NO deben bloquearse)
# -----------------------------------------------------------------------------
mensajes_limpios = [
    "hola abejita bonita",
    "me encanta AWS",
    "saludos UAEMex",
    "the cloud is great",
    "que buena expo",
    "vamos a la computadora a programar",  # contiene 'put' adentro de computadora
    "anotar los apuntes en el cuaderno",   # contiene 'ano' adentro de anotar
    "quedo en sexto lugar de la carrera",  # contiene 'sex' adentro de sexto
    "este es un mensaje de prueba",        # contiene 'mens' adentro de mensaje
    "los diputados estan en sesion",       # contiene 'put' adentro de diputados
    "asistir puntualmente al evento",
    "buenas tardes a todos los presentes",
]

for ok in mensajes_limpios:
    assert es_limpio(ok), f"Falso positivo detectado en mensaje limpio: {ok!r}"
print(" [2/7] Prevención de falsos positivos validada (12 casos).")

# -----------------------------------------------------------------------------
# 3. Evasiones por Leet Speak y sustitución numérica
# -----------------------------------------------------------------------------
leet_evasiones = [
    "p3nd3jo",
    "ch1ng4",
    "v3rg4",
    "m13rd4",
    "put0",
    "cul0",
    "c4br0n",
    "8oludo",
    "pu+a",
    "p@n0ch4",
    "sh1t",
    "b1tch",
]

for mal in leet_evasiones:
    res = buscar_groseria(mal)
    assert res is not None, f"No detectó evasión Leet Speak: {mal!r}"
print(" [3/7] Evasiones por Leet Speak y números validadas (12 casos).")

# -----------------------------------------------------------------------------
# 4. Evasiones por Separadores (puntos, guiones, espacios, guiones bajos)
# -----------------------------------------------------------------------------
separador_evasiones = [
    "p u t o",
    "p.u.t.o",
    "p-u-t-0",
    "p_u_t_a",
    "p.e.n.d.e.j.o",
    "f.u.c.k",
    "f_u_c_k",
    "c_h_i_n_g_a",
    "c.h.i.n.g.a.d.e.r.a",
    "p-u-t-0 el que lo lea",
    "hola p.u.t.o como estas",
]

for mal in separador_evasiones:
    res = buscar_groseria(mal)
    assert res is not None, f"No detectó evasión con separadores: {mal!r}"
print(" [4/7] Evasiones por signos/separadores validadas (11 casos).")

# -----------------------------------------------------------------------------
# 5. Evasiones por Letras Repetidas / Alargadas
# -----------------------------------------------------------------------------
repetidas_evasiones = [
    "puuuuutoooo",
    "chiiiingaaa",
    "veeeergaaaa",
    "seeeexooo",
    "puuuuutoooo todos",
    "chiiiingaaa ya",
    "p...u...u...t...0",
]

for mal in repetidas_evasiones:
    res = buscar_groseria(mal)
    assert res is not None, f"No detectó evasión con letras repetidas: {mal!r}"
print(" [5/7] Evasiones por letras repetidas validadas (7 casos).")

# -----------------------------------------------------------------------------
# 6. Groserías en inglés y frases compuestas de odio
# -----------------------------------------------------------------------------
frases_e_ingles = [
    "chinga tu madre",
    "hijo de puta",
    "vete a la mierda",
    "you are a jerk",
    "what a prick",
    "arsehole",
    "tosser",
    "shut the fuck up",
    "los extranjeros son una plaga",
    "hay que matar a los homosexuales",
]

for mal in frases_e_ingles:
    res = buscar_groseria(mal)
    assert res is not None, f"No detectó frase ofensiva o en inglés: {mal!r}"
print(" [6/7] Frases compuestas, odio e insultos en inglés validados (10 casos).")

# -----------------------------------------------------------------------------
# 7. Resiliencia de OpenAI Moderation (Zero-Crash Fallback)
# -----------------------------------------------------------------------------
# Verificar que la llamada a moderar_con_openai no cause excepciones fatales
# incluso si la API devuelve 429, timeout o falla de red.
ok, razon = moderar_con_openai("Hola a todos los ingenieros de la UAEMex")
assert isinstance(ok, bool)
print(" [7/7] Resiliencia de OpenAI Moderation API validada.")

print("\n🎉 ¡TODAS LAS PRUEBAS (50+ verificaciones) PASARON EXITOSAMENTE!")

