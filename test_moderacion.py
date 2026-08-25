# Check del filtro de mensajes:  python test_moderacion.py
import moderacion
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


# --- Detoxify: umbral y salida sin descargar el modelo real ---
class ModeloDetoxifyFalso:
    def __init__(self, toxicidad):
        self.toxicidad = toxicidad

    def predict(self, texto):
        return {"toxicity": self.toxicidad}


moderacion._detoxify_model = ModeloDetoxifyFalso(0.9)
assert buscar_groseria("comentario contextual") == (
    "detoxify (toxicidad >= 0.65)"
)
moderacion._detoxify_model = ModeloDetoxifyFalso(0.2)
assert es_limpio("comentario contextual"), "falso positivo de Detoxify"

# --- ampliación del diccionario: "gei" y nuevas raíces (naco, menso, sidos) ---
for mal in ["gei", "geis", "eres un gei", "naco", "que naco eres",
            "menso", "no seas menso", "sidos", "eres un sidoso"]:
    assert buscar_groseria(mal), f"no detectó (ampliación): {mal!r}"

# "gei" es palabra EXACTA, no raíz: no debe atrapar palabras que empiezan igual
for ok in ["geiser en Islandia", "geisha japonesa"]:
    assert es_limpio(ok), f"falso positivo por 'gei': {ok!r}"

print("ok — solo_texto, limpios, groserías, 4ª capa y ampliación del diccionario")
