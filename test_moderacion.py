# Check del filtro de mensajes:  python test_moderacion.py
from moderacion import buscar_groseria, es_limpio, solo_texto

# --- solo_texto: quita emojis/símbolos, conserva texto real ---
assert solo_texto("hola \U0001F41D mundo") == "hola mundo"
assert solo_texto("\U0001F44D\U0001F525") == ""          # solo emojis -> vacío
assert solo_texto("te quiero ❤️") == "te quiero"  # emoji + selector variación
assert solo_texto("¡Qué? niño ñoño") == "¡Qué? niño ñoño"  # acentos/signos/ñ intactos
assert solo_texto("a  b   c") == "a b c"                  # espacios colapsados

# --- limpio no se bloquea ---
for ok in ["hola abejita bonita", "me encanta AWS", "saludos UAEMex",
           "the cloud is great", "que buena expo"]:
    assert es_limpio(ok), f"falso positivo: {ok!r}"

# --- groserías del filtro español/anti-evasión ---
for mal in ["pendejo", "p3nd3jo", "p u t o", "no mames", "hijo de puta"]:
    assert buscar_groseria(mal), f"no detectó: {mal!r}"

# --- 4ª capa (better-profanity): cobertura que el filtro previo no tenía ---
for mal in ["you are a jerk", "what a prick", "arsehole", "tosser"]:
    assert buscar_groseria(mal), f"better-profanity no detectó: {mal!r}"

print("ok — solo_texto, limpios, groserías y 4ª capa")
