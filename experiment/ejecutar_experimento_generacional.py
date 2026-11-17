#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proyecto Ascendant — Motor Cognitivo Generacional Unificado (Fidelidad Literal al Manuscrito)
Autor e Investigador Principal: David San Nicolás Montero
DOI Oficial (v3): 10.5281/zenodo.23802198 | Concept DOI: 10.5281/zenodo.23616626

Implementación exacta 1:1 con monitor_consciencia_generacional.html y las ecuaciones del manuscrito:
- Nivel 0 y 0.5 (Secc. 2.1): Arena 2D continua (100x100 m), refugio r = 10.5 m (santuario interior 7.8 m),
  coste metabólico explícito (basal + cinético ||v||^1.5 + disconfort térmico cuadrático + coste deliberativo L_max),
  4 cazaderos equidistantes a 35.0 m, obstáculos físicos y escalada de depredadores (+1 cada 1.000 ciclos: 3 -> 7).
- Nivel 1 (Secc. 2.2): Separación estricta entre vector de temperamento congénito invariable theta_temp in [0.10, 0.90]^7
  y vector neuroendocrino dinámico h(t) in [0.0, 1.0]^7 gobernado por 7 EDOs acopladas (cort, oxi, dop, ira, tris, res, cur).
- Nivel 2, 2.5 y 3 (Secc. 2.3-2.5): Manta de Markov sin acceso a floats, modulación neuroinspirada tau(t) y L_max(t),
  árbitro alostático puro a*(t) = argmax(D_a + V_somatica + V_prosp) sin overrides, V_prosp = 45*(k_rem/k_tot) con
  expedición completa de 8 pasos hasta destino (35 m), Circuit Breaker alostático y soporte factorial 2x2 (Cultura x Despensa).
- Nivel Memoria y Metacognición (Secc. 3 y 4): Engrama formal como 9-tupla con estado epistémico HOT (confianza c in [0,1]
  distinguiendo percepción propia, testimonio heredado e hipótesis imaginada), triaje CLS con decaimiento lineal exacto,
  esquema atencional AST con radio sensorial activo (15.0 m -> 9.5 m -> 4.2 m), detección/evasión temprana, duelo
  neuroendocrino funcional y co-adopción familiar (ENCUENTRO_FAMILIAR_SALVADOR).
"""

import json
import math
import os
import random
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ascendant_generacional_integro.db")
JSON_LOG_PATH = os.path.join(BASE_DIR, "log_interno_generacional.json")

# Constantes estructurales (idénticas en JS y Python)
MAX_ENGRAMS = 200
ANCIENT_ZONE_LIMIT = int(MAX_ENGRAMS * 0.20)
MAX_BACKPACK = 2
MAX_SHELTER_MEAT = 5
MAX_GLOBAL_CYCLES = 4050

SAFE_CENTER_X = 50.0
SAFE_CENTER_Y = 50.0
SHELTER_RADIUS = 10.5          # Secc. 2.1: radio literal del refugio r = 10.5 m
INNER_SANCTUARY_RADIUS = 7.8   # Núcleo profundo infranqueable; entre 7.8 y 10.5 m hay perímetro con riesgo si túnel 4.2 m
BITE_RADIUS = 5.4              # Radio de embestida física lesiva (-8 ciclos de vida)
HUNT_CAPTURE_RADIUS = 8.0      # Radio de captura en cazadero a 35.0 m
PLAN_TOTAL_STEPS = 8           # Horizonte necesario para cubrir 35 m desde el refugio
V_MAX_PLAN = 45.0              # Secc. 2.5 Ec. 2.8: V_max^plan = 45.0

# Interruptores experimentales del diseño factorial 2x2
CULTURAL_TRANSMISSION_ENABLED = True
COMMUNAL_PANTRY_ENABLED = True

# =============================================================================
# CONEXIÓN OBLIGATORIA AL SERVIDOR LLM LOCAL (Zaylo / llama-server)
# El LLM es un componente indispensable del cerebro sintético de los entes.
# =============================================================================
LIVE_LOCAL_LLM_ENABLED = os.environ.get("ASCENDANT_USE_LLM", "0").strip().lower() in ("1", "true", "yes")
LOCAL_LLM_API_KEY = "lcl_9fd3d7ecc7a3bfc1282a828e5a97cfc04f19546a"
LOCAL_LLM_ENDPOINTS = [
    "http://127.0.0.1:8080/v1/chat/completions",
    "http://192.168.18.4:8080/v1/chat/completions",
    "http://127.0.0.1:8081/v1/chat/completions",
]
LOCAL_LLM_HEALTH_ENDPOINTS = [
    "http://127.0.0.1:8080/v1/models",
    "http://192.168.18.4:8080/v1/models",
    "http://127.0.0.1:8081/health",
]
LOCAL_LLM_MODEL = "Qwen 2.5 0.5B Instruct"
LOCAL_LLM_TIMEOUT = 6.0


def assert_llm_active():
    """
    Verificación obligatoria previa al arranque de la simulación.
    El LLM es una parte indispensable del cerebro de los entes. Si el servidor
    LLM local no está activo o no responde, la simulación se aborta inmediatamente.
    """
    if not LIVE_LOCAL_LLM_ENABLED:
        return  # Modo motor algorítmico estadístico de grafos para benchmarks (Sec. 4.1 A)

    connected = False
    last_err = None
    for test_url in LOCAL_LLM_HEALTH_ENDPOINTS:
        try:
            req = urllib.request.Request(
                test_url,
                headers={
                    "User-Agent": "Ascendant-Brain/1.0",
                    "Authorization": f"Bearer {LOCAL_LLM_API_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    connected = True
                    break
        except Exception as e:
            last_err = e
    if not connected:
        raise RuntimeError(
            "ERROR BLOQUEANTE: El servidor LLM local no está activo en las URLs configuradas.\n"
            "Es condición indispensable que el LLM esté activo para iniciar la simulación,\n"
            "ya que forma parte integral de la arquitectura cerebral de los entes.\n"
            f"Detalle del error de conexión: {last_err}"
        )

class Mulberry32:
    """PRNG determinista idéntico bit a bit entre Python y JavaScript (IEEE-754 + uint32)."""
    def __init__(self, seed=None):
        if seed is None:
            seed = random.randint(1, 0x7FFFFFFF)
        self.seed = int(seed) & 0xFFFFFFFF
        self.state = self.seed

    def random(self):
        self.state = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t2 = ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF
        t = (((t + t2) & 0xFFFFFFFF) ^ t)
        t = ((t ^ (t >> 14)) & 0xFFFFFFFF)
        return t / 4294967296.0


# Obstáculos físicos estáticos fuera del eje exacto (Secc. 2.5 viñeta 3 y EDO de Ira I_bloqueo)
ARENA_OBSTACLES = [
    {"id": "obs_N", "x": 55.2, "y": 28.5, "r": 2.3, "dir": "NORTE"},
    {"id": "obs_S", "x": 44.8, "y": 71.5, "r": 2.3, "dir": "SUR"},
    {"id": "obs_O", "x": 28.5, "y": 44.8, "r": 2.3, "dir": "OESTE"},
    {"id": "obs_E", "x": 71.5, "y": 55.2, "r": 2.3, "dir": "ESTE"},
]

# =========================================================================
# 5 ARQUETIPOS CON VECTOR DE TEMPERAMENTO CONGÉNITO theta_temp in [0.10, 0.90]^7 (Secc. 2.2)
# =========================================================================
TEMPERAMENTS = [
    {
        "id": "joy", "name": "Entusiasta Dopaminérgico", "emoji": "🌟",
        "theta": {"dop": 0.82, "oxi": 0.60, "ira": 0.26, "tris": 0.20, "res": 0.76, "cur": 0.84, "cort_base": 0.16},
        "voiceColor": "#ffd166",
        "desc": "Alta motivación dopaminérgica, curiosidad exploratoria y resiliencia. Optimista ante la incertidumbre.",
        "lexicon": {
            "calm": "Siento un agradable hormigueo de júbilo y optimismo en el pecho; todo marcha bien.",
            "hunger": "Mi estómago empieza a quejarse, pero me entusiasma la idea de salir a explorar y buscar carne.",
            "starving": "¡Mis fuerzas caen en picado! Debo actuar con decisión inmediata antes de que la debilidad me impida cazar.",
            "distress": "Siento una leve inquietud, pero confío plenamente en que resolveremos esta situación.",
            "alone": "La soledad me desconcierta un poco, pero mi ánimo no decae.",
            "harvest": "¡Qué emoción tan grande! Logré otra pieza de carne para asegurar nuestro futuro en la mochila.",
            "eat": "¡Un deleite total! Cada bocado de carne me renueva la energía y el entusiasmo por vivir.",
            "hug": "El abrazo me contagia una alegría cálida y llena de afecto.",
            "feed": "¡Verle recuperar la sonrisa me llena el pecho de gozo y satisfacción!"
        }
    },
    {
        "id": "melancholy", "name": "Melancólico Empático", "emoji": "🌧️",
        "theta": {"dop": 0.36, "oxi": 0.86, "ira": 0.22, "tris": 0.78, "res": 0.34, "cur": 0.42, "cort_base": 0.32},
        "voiceColor": "#90e0ef",
        "desc": "Alta sensibilidad afiliativa y reactividad al duelo; prudente ante el peligro y muy protector del vínculo.",
        "lexicon": {
            "calm": "Una calma frágil me acompaña, aunque una sombra de melancolía nunca me abandona del todo.",
            "hunger": "Una pesadumbre gris me invade; temo que la escasez nos apague en este páramo silencioso.",
            "starving": "El llanto del cuerpo es desgarrador... me desvanezco de tristeza y hambre; si nadie me salva moriré.",
            "distress": "Una angustia honda me oprime el pecho; me siento vulnerable y desamparado ante el mundo.",
            "alone": "La soledad me parte el alma como un frío eterno... necesito con desesperación sentir a mi ser querido.",
            "harvest": "Siento alivio de haber conseguido este sustento de carne entre lágrimas de esfuerzo.",
            "eat": "El calor del alimento entra en mi ser, disipando un poco esta pena que llevo dentro.",
            "hug": "El abrazo es mi único refugio; estrecharle contra mí aleja la tristeza y me devuelve el sentido de existir.",
            "feed": "Mi corazón llora de emoción al verle alimentado; daría mi última gota de aliento por evitarle el dolor."
        }
    },
    {
        "id": "anger", "name": "Colérico Reactivo", "emoji": "🔥",
        "theta": {"dop": 0.64, "oxi": 0.40, "ira": 0.85, "tris": 0.28, "res": 0.60, "cur": 0.62, "cort_base": 0.26},
        "voiceColor": "#ff758f",
        "desc": "Alta reactividad combativa ante bloqueos y privación; vence el miedo cuando el hambre apremia.",
        "lexicon": {
            "calm": "Por fin hay tregua, aunque permanezco en guardia ante cualquier contratiempo.",
            "hunger": "Me hierve la sangre de pura rabia; no tolero que el estómago empiece a quejarse y me frene el paso.",
            "starving": "¡Maldita debilidad! Esta agonía me enfurece hasta los dientes; me niego con rabia a caer aquí sin pelear.",
            "distress": "Un nudo de irritación y furia me arde en el pecho; me revienta estar sometido a esta intemperie.",
            "alone": "Estar solo me tensa y me irrita; me fastidia no tener cerca a quien me respalde.",
            "harvest": "¡Arranqué esta carne a la fuerza del páramo! La rabia se transforma en victoria y sustento.",
            "eat": "Devoro la carne con ferocidad; aplaco este fuego en el vientre para seguir en pie.",
            "hug": "El abrazo logra apaciguar mi ira; afloja la mandíbula y me recuerda que no estoy en guerra con quien amo.",
            "feed": "Le doy comida con gesto firme; me niego con rabia a permitir que la muerte me lo arrebate."
        }
    },
    {
        "id": "disdain", "name": "Estoico Desapegado", "emoji": "❄️",
        "theta": {"dop": 0.50, "oxi": 0.22, "ira": 0.36, "tris": 0.24, "res": 0.74, "cur": 0.54, "cort_base": 0.18},
        "voiceColor": "#a0aec0",
        "desc": "Baja dependencia social, alta estabilidad alostática y pragmatismo autónomo frente a la soledad.",
        "lexicon": {
            "calm": "Mente despejada y sobria. No necesito adornos emocionales para cumplir con mi deber.",
            "hunger": "Tengo mucha hambre, es hora de salir a cazar, no hay excusa.",
            "starving": "Me quedo sin fuerzas. Tengo que comer ya si no quiero caer muerto.",
            "distress": "El clima no acompaña, pero mantengo la cabeza fría y resisto.",
            "alone": "Estar solo no me asusta; cada uno debe valerse por sí mismo.",
            "harvest": "Misión cumplida: un poco más de carne para guardar.",
            "eat": "Comí con calma. Mi cuerpo se recupera.",
            "hug": "Acepto el abrazo para calmar el frío, aunque prefiero mantener mi distancia.",
            "feed": "Le doy comida al compañero para mantenerlo en pie; nos necesitamos vivos."
        }
    },
    {
        "id": "optimism", "name": "Optimista Sereno", "emoji": "🌿",
        "theta": {"dop": 0.68, "oxi": 0.74, "ira": 0.18, "tris": 0.22, "res": 0.86, "cur": 0.70, "cort_base": 0.14},
        "voiceColor": "#70e000",
        "desc": "Máxima resiliencia homeostática, cooperación serena y rápido restablecimiento tras crisis somáticas.",
        "lexicon": {
            "calm": "Siento una dulce paz y serenidad; el aire es agradable y la vida se siente hermosa a su lado.",
            "hunger": "El estómago me avisa con delicadeza; con calma y paciencia buscaremos carne cuando sea el momento.",
            "starving": "El cuerpo flaquea, pero mantengo la serenidad; mientras respiremos siempre hay un camino de salvación.",
            "distress": "Siento un pequeño desasosiego, pero respiro hondo y sé que esta tormenta pasará pronto.",
            "alone": "Extraño su compañía, pero mantengo la esperanza intacta de que nos reuniremos de nuevo.",
            "harvest": "¡Qué hermosa bendición! La tierra nos brinda este sustento de carne para continuar nuestro viaje.",
            "eat": "Un sabor delicioso que me llena de gratitud y revitaliza cada rincón de mi ser.",
            "hug": "Abrazarle es tocar la paz absoluta; siento que somos un solo corazón latiendo en armonía.",
            "feed": "Compartir mi comida es el acto más noble y bello; ver su mirada tranquila me colma de dicha."
        }
    }
]

TEMPERAMENT_VOICES = {
    "joy": "enérgico, animado y optimista",
    "melancholy": "temeroso, vulnerable y melancólico",
    "anger": "irascible, malhumorado y combativo",
    "disdain": "frío, seco y desapegado",
    "optimism": "sereno, paciente y prudente",
}


def clip(val, lo, hi):
    return max(lo, min(hi, val))


def r_num(val, digits=0):
    """Redondeo half-up determinista IEEE-754 idéntico entre Python y JavaScript."""
    if digits <= 0:
        return int(math.floor(val + 0.5))
    factor = 10.0 ** digits
    return math.floor(val * factor + 0.5) / factor


def hypot2d(dx, dy):
    """Distancia euclídea usando sqrt IEEE-754 exacto (0.5 ULP en Python y V8 JS)."""
    return math.sqrt(dx * dx + dy * dy)


def get_condition_code(cultural_enabled, pantry_enabled):
    if cultural_enabled and pantry_enabled:
        return "D_T+_P+"
    if (not cultural_enabled) and pantry_enabled:
        return "B_T0_P+"
    if cultural_enabled and (not pantry_enabled):
        return "C_T+_P-"
    return "A_T0_P-"


# Interruptores de Intervención Causal Directa (por defecto inactivos = motor estándar 100% intacto)
CAUSAL_THETA_MODE = "STANDARD"        # "STANDARD" | "SWAP_OXI_MEL_STOIC" | "ORTHOGONAL_7D"
CAUSAL_FEED_OXI_GAIN = 1.0            # 1.0 estándar | 0.0 ablación de ALIMENTAR (1.8 * h_oxi -> 0) | barrido dosis-respuesta
CAUSAL_TRAUMA_IRA_GAIN = 1.0          # 1.0 estándar | 0.0 ablación de ira en Ec. 2.11 (0.60 * h_ira -> 0)
CAUSAL_FIXED_THETA_OXI = None         # None estándar | float (ej. 0.22 o 0.86) para diseño factorial 2x2
CAUSAL_NONFEED_OXI_CLAMP = None       # None estándar | float (ej. 0.22) para aislar vía exclusiva ALIMENTAR


def generate_endocrine_profile(rng, archetype_id=None):
    if archetype_id:
        matches = [t for t in TEMPERAMENTS if t["id"] == archetype_id]
        base = matches[0] if matches else TEMPERAMENTS[0]
    else:
        base = TEMPERAMENTS[int(rng.random() * len(TEMPERAMENTS))]

    raw_u = {k: rng.random() for k in base["theta"].keys()}
    if CAUSAL_THETA_MODE == "ORTHOGONAL_7D":
        theta = {
            k: r_num((0.10 + 0.35 * u) if k == "cort_base" else (0.10 + 0.80 * u), 3)
            for k, u in raw_u.items()
        }
    else:
        theta = {
            k: r_num(clip(v * (0.92 + raw_u[k] * 0.16), 0.10, 0.90), 3)
            for k, v in base["theta"].items()
        }
        if CAUSAL_THETA_MODE == "SWAP_OXI_MEL_STOIC":
            if base["id"] == "melancholy":
                theta["oxi"] = r_num(clip(0.22 * (0.92 + raw_u["oxi"] * 0.16), 0.10, 0.90), 3)
            elif base["id"] == "disdain":
                theta["oxi"] = r_num(clip(0.86 * (0.92 + raw_u["oxi"] * 0.16), 0.10, 0.90), 3)
    if CAUSAL_FIXED_THETA_OXI is not None:
        theta["oxi"] = r_num(clip(float(CAUSAL_FIXED_THETA_OXI) * (0.92 + raw_u["oxi"] * 0.16), 0.10, 0.90), 3)
    return {
        "id": base["id"],
        "name": base["name"],
        "emoji": base["emoji"],
        "theta": theta,
        # Escalares equivalentes (2*theta) para compatibilidad de lectura visual
        "oxytocin": r_num(theta["oxi"] * 2.0, 2),
        "dopamine": r_num(theta["dop"] * 2.0, 2),
        "anger": r_num(theta["ira"] * 2.0, 2),
        "sadness": r_num(theta["tris"] * 2.0, 2),
        "resilience": r_num(theta["res"] * 2.0, 2),
        "curiosity": r_num(theta["cur"] * 2.0, 2),
        "cort_base": r_num(theta["cort_base"], 2),
        "savingsGoal": MAX_BACKPACK,
        "voiceColor": base["voiceColor"],
        "desc": base["desc"],
        "lexicon": base["lexicon"],
    }


# =========================================================================
# NIVEL 2.5: TRADUCTORES INTEROCEPTIVOS CUALITATIVOS (CERO FLOATS — Manta de Markov)
# =========================================================================
def get_direction_2d(fx, fy, tx, ty):
    ang = math.atan2(-(ty - fy), tx - fx) * (180.0 / math.pi)
    if -22.5 <= ang < 22.5:
        return "el este"
    if 22.5 <= ang < 67.5:
        return "el noreste"
    if 67.5 <= ang < 112.5:
        return "el norte"
    if 112.5 <= ang < 157.5:
        return "el noroeste"
    if ang >= 157.5 or ang < -157.5:
        return "el oeste"
    if -157.5 <= ang < -112.5:
        return "el suroeste"
    if -112.5 <= ang < -67.5:
        return "el sur"
    return "el sureste"


def get_quadrant_dir(x, y):
    if abs(x - SAFE_CENTER_X) > abs(y - SAFE_CENTER_Y):
        return "ESTE" if x > SAFE_CENTER_X else "OESTE"
    return "NORTE" if y < SAFE_CENTER_Y else "SUR"


def get_hunger_qualia(e):
    if e >= 80:
        return "estoy saciado y con fuerzas"
    if e >= 62:
        return "tengo poco apetito"
    if e >= 42:
        return "tengo hambre y necesito comer"
    if e >= 24:
        return "tengo mucha hambre y me faltan las fuerzas"
    return "me muero de hambre; si no como pronto moriré"


def get_hunger_short(e):
    if e >= 80:
        return "Saciado"
    if e >= 62:
        return "Poco hambre"
    if e >= 42:
        return "Con hambre"
    if e >= 24:
        return "Mucha hambre"
    return "Muriendo de hambre"


def get_distress_qualia(s):
    if s < 0.20:
        return "estoy tranquilo"
    if s < 0.40:
        return "siento cierta inquietud"
    if s < 0.65:
        return "siento miedo y el pecho apretado"
    if s < 0.85:
        return "siento angustia y desesperación"
    return "siento un dolor insoportable"


def get_distress_short(s):
    if s < 0.20:
        return "Calma"
    if s < 0.40:
        return "Malestar leve"
    if s < 0.65:
        return "Temor tenso"
    if s < 0.85:
        return "Angustia"
    return "Agonía"


def get_attachment_qualia(c, companion_name="mi compañero"):
    if c < 0.25:
        return f"me siento totalmente solo y desamparado sin {companion_name}"
    if c < 0.50:
        return f"echo de menos a {companion_name} y necesito su compañía"
    if c < 0.72:
        return f"me siento acompañado y seguro junto a {companion_name}"
    return f"siento un gran afecto y unión con {companion_name}"


def get_pleasure_qualia(p):
    if p < 0.22:
        return "me siento decaído y sin ánimos"
    if p < 0.42:
        return "me siento neutro, sin alivio"
    if p < 0.68:
        return "siento alivio y bienestar"
    if p < 0.85:
        return "siento un alivio cálido y reconfortante"
    return "siento alegría y calma por tener comida y seguridad"


def get_hormone_qualia(h):
    states = []
    if h["cort"] > 0.60:
        states.append("mucha alerta y tensión")
    elif h["cort"] < 0.22:
        states.append("calma en el cuerpo")
    if h["dop"] > 0.68:
        states.append("ganas de moverme y buscar")
    if h["oxi"] > 0.68:
        states.append("cariño hacia los míos")
    if h["ira"] > 0.62:
        states.append("rabia defensiva")
    if h["tris"] > 0.58:
        states.append("tristeza por la pérdida")
    if h["cur"] > 0.66:
        states.append("curiosidad por explorar")
    elif h["cur"] < 0.25:
        states.append("cautela y desconfianza")
    if h["res"] < 0.30:
        states.append("el cuerpo muy cansado")
    return ", ".join(states) if states else "cuerpo tranquilo y estable"


# =========================================================================
# SECCIÓN 3.1 y 3.2: ENGRAMAS COMO 9-TUPLA FORMAL Y TRIAJE CLS LINEAL
# =========================================================================
def create_initial_engrams(h_init=None):
    base_ctx = {
        "pos": [50.0, 50.0],
        "energyQualia": "Saciado",
        "stressQualia": "Calma",
        "companion": "Linaje",
        "interoceptiveDelta": "Axioma congénito",
        "origin": "INNATA",
        "epistemicState": "AXIOMA_CONGENITO",
        "confidence": 1.0,
        "attentionMode": "EXTEROCEPTIVO_ALERTA",
    }
    raw = [
        (1, "PELIGRO_INANICION_MORTAL", "INSTINTO", -0.95,
         "Hambre Prolongada: ↑ Mortal | Vitalidad: ↓ Cese | Instinto: ↑ Supervivencia",
         "Sé que si paso mucho tiempo sin comer me debilitaré hasta morir; tengo que conseguir comida para seguir vivo.",
         98.0, 1, 145.0),
        (2, "SACIEDAD_NUTRICIONAL", "COMER", +0.86,
         "Hambre: ↓ Reducida | Placer: ↑ Alivio | Fuerza: ↑ Recuperada",
         "Sé que comer carne me quita el hambre, me devuelve las fuerzas y me hace sentir bien.",
         75.0, 8, 125.0),
        (3, "ALTRUISMO_NUTRICIONAL", "ALIMENTAR", +0.95,
         "Familia: ↑ Salvada | Placer: ↑ Júbilo | Vínculo: ↑ Hermandad",
         "Sé que compartir comida con los míos evita que mueran y me hace sentir feliz y unido a ellos.",
         88.5, 8, 136.0),
        (4, "DIALOGO_EMPATICO", "PREGUNTAR", +0.74,
         "Incertidumbre: ↓ Resuelta | Vínculo: ↑ Comprensión",
         "Sé que no puedo saber cómo está mi compañero si no me acerco y hablo con él.",
         52.0, 8, 100.0),
        (5, "REGULACION_AFECTIVA", "ABRAZAR", +0.88,
         "Malestar: ↓ Calma | Consuelo: ↑ Afecto | Placer: ↑ Cálido",
         "Sé que un abrazo nos quita el miedo, alivia el malestar y nos devuelve la calma.",
         78.0, 10, 130.0),
        (6, "EXPLORACION_RUMBOS", "EXPLORAR", +0.76,
         "Mundo Exterior: ↑ Inexplorado | Presas: ↑ Cazaderos | Cautela: ↑ Alerta",
         "Sé que fuera del refugio hay cuatro rumbos (Norte, Sur, Este y Oeste); debo explorarlos con cuidado para encontrar caza.",
         66.0, 5, 112.0),
        (7, "REFUGIO_SEGURO_DESPENSA", "REFUGIO", +0.88,
         "Seguridad: ↑ Santuario | Despensa: ↑ Almacén Comunal | Fieras: ↓ Perímetro",
         "Sé que el refugio del centro es un lugar seguro para no congelarme y guardar comida de reserva para el grupo.",
         80.0, 8, 130.0),
    ]

    # Determinar temperamento ontogenético congénito si se proporciona el perfil hormonal inicial
    temperament_desc = "equilibrado y prudente"
    tau_ontogeny = 0.50
    if h_init:
        if h_init.get("cort", 0.3) > 0.55:
            temperament_desc = "cauteloso, vigilante y con temor al peligro"
            tau_ontogeny = 0.35
        elif h_init.get("dop", 0.5) > 0.60 or h_init.get("cur", 0.5) > 0.60:
            temperament_desc = "activo, decidido y con ganas de explorar"
            tau_ontogeny = 0.75
        elif h_init.get("oxi", 0.5) > 0.60:
            temperament_desc = "afectuoso, protector y enfocado en la unión del clan"
            tau_ontogeny = 0.55

    out = []
    for eid, etype, act, val, deltas, text, som, rep, ret in raw:
        personalized_text = text
        if LIVE_LOCAL_LLM_ENABLED:
            prompt = (
                f"Carácter: {temperament_desc}.\n"
                f"Pensamiento innato: {text}\n"
                f"Adapta este pensamiento a tu carácter en primera persona en una sola frase breve:"
            )
            adapted = query_local_llm_if_enabled(
                prompt, tau_ontogeny, 50,
                system_prompt="Eres un superviviente. Habla en primera persona con lenguaje natural y sincero. Una sola frase."
            )
            if adapted:
                personalized_text = adapted

        out.append({
            "id": eid,
            "type": etype,
            "action": act,
            "content": personalized_text,
            "outcome": personalized_text,
            "context": dict(base_ctx),
            "val": val,
            "deltas": deltas,
            "cycle": 1,
            "cycleEnd": 1,
            "cycleRange": "1",
            "globalCycle": 0,
            "somaticImpact": som,
            "repetitionCount": rep,
            "duration": 1,
            "retentionScore": ret,
            "origin": "INNATA",
            "epistemicState": "AXIOMA_CONGENITO",
            "confidence": 1.0,
            "isCompressed": False,
            "compressedCount": 1,
        })
    return out


def compute_retention(e, current_age):
    # Secc. 3.2 Ec. 3.1: R_i(t) = ImpactoSomatico_i + 24.0 * ln(1 + N_rep) - 0.025 * (t - t_i)
    age_diff = max(0, current_age - e.get("cycle", 1))
    som = e.get("somaticImpact", 55.0)
    rep = e.get("repetitionCount", 1)
    return r_num(som + 24.0 * math.log(1.0 + rep) - 0.025 * age_diff, 1)


def add_world_engram(w, global_cycle, etype, action, val, deltas, outcome_text,
                     origin_tag="PROPIA", epistemic_state="PERCEPCION_DIRECTA", confidence=0.95, companion_name="Ninguno"):
    w["typeFrequencies"][etype] = w["typeFrequencies"].get(etype, 0) + 1
    rep = w["typeFrequencies"][etype]
    w["frequencies"][action] = w["frequencies"].get(action, 0) + 1

    # Secc. 3.2 Ec. 3.2 literal: |val|*52 + trauma*92 + prospeccion*82 + validacion*95 (+ arraigo hereditario 72)
    is_trauma = 1.0 if ("TRAUMA" in etype) else 0.0
    is_prosp = 1.0 if ("CAUSAL" in etype or "PROSPECCION" in etype or "ENSOÑACION" in etype) else 0.0
    is_valid = 1.0 if ("VALIDACION" in etype or "SALVADOR" in etype) else 0.0
    is_inher = 1.0 if ("TRANSMISION" in etype or origin_tag.startswith("HEREDADA")) else 0.0
    som = abs(val) * 52.0 + is_trauma * 92.0 + is_prosp * 82.0 + is_valid * 95.0 + (72.0 if is_inher else 0.0)

    # Personalización mnémica afectiva según estrés somático, temperamento y modulación LLM
    final_text = outcome_text
    if origin_tag != "INNATA":
        final_text = process_engram_text_with_llm(w, outcome_text, etype, action, val, companion_name=companion_name)

    new_id = (max(x["id"] for x in w["engrams"]) + 1) if w["engrams"] else 1
    ctx = {
        "pos": [r_num(w["agentX"], 2), r_num(w["agentY"], 2)],
        "energyQualia": get_hunger_short(w["energy"]),
        "stressQualia": get_distress_short(w["stress"]),
        "companion": companion_name,
        "interoceptiveDelta": deltas,
        "origin": origin_tag,
        "epistemicState": epistemic_state,
        "confidence": r_num(confidence, 3),
        "attentionMode": w["attentionSchema"]["mode"],
    }
    cur_cycle = max(1, w["age"])
    prev_h = w.get("_prevH", w["h"])
    delta_h_calc = {k: r_num(w["h"].get(k, 0.2) - prev_h.get(k, 0.2), 3) for k in HORMONES_LIST}
    entry = {
        "id": new_id,
        "type": etype,
        "action": action,
        "content": final_text,
        "outcome": final_text,
        "context": ctx,
        "hSnapshot": {k: r_num(w["h"].get(k, 0.2), 3) for k in HORMONES_LIST},
        "deltaH": delta_h_calc,
        "lastSomaticReactivation": -999,
        "evocationCount": 0,
        "val": r_num(val, 3),
        "deltas": deltas,
        "cycle": cur_cycle,
        "cycleEnd": cur_cycle,
        "cycleRange": str(cur_cycle),
        "globalCycle": global_cycle,
        "somaticImpact": r_num(som, 2),
        "repetitionCount": rep,
        "duration": 1,
        "retentionScore": 0.0,
        "origin": origin_tag,
        "epistemicState": epistemic_state,
        "confidence": r_num(confidence, 3),
        "isCompressed": False,
        "compressedCount": 1,
    }
    entry["retentionScore"] = compute_retention(entry, w["age"])
    w["engrams"].append(entry)

    # Consolidación jerárquica de 3 zonas y poda afectiva (Secc. 3.2):
    # Zona A (0..19, 20% más antiguo): esquemas consolidados
    # Zona B (20..49, 30% intermedio): buffer episódico
    # Zona C (50..99, 50% más reciente): memoria viva intacta
    consolidate_and_prune_memory_hierarchical(w)
    w["_engramsVersion"] = w.get("_engramsVersion", 0) + 1


def create_agent_mind(rng, ag_id, name, gen_number, birth_cycle, max_lifespan, start_alive):
    profile = generate_endocrine_profile(rng)
    th = profile["theta"]
    h_init = {
        "cort": th["cort_base"],
        "oxi": th["oxi"],
        "dop": th["dop"],
        "ira": th["ira"],
        "tris": th["tris"],
        "res": th["res"],
        "cur": th["cur"],
    }
    return {
        "id": ag_id,
        "name": name,
        "genNumber": gen_number,
        "birthCycle": birth_cycle,
        "initialMaxLifespan": max_lifespan,
        "maxLifespan": max_lifespan,
        "age": 0,
        "born": start_alive,
        "agentAlive": start_alive,
        "deathCycle": None,
        "causeOfDeath": None,
        "profile": profile,
        "h": h_init,
        "agentX": 50.0 + (rng.random() - 0.5) * 3.0,
        "agentY": 50.0 + (rng.random() - 0.5) * 3.0,
        "energy": 78.0 if gen_number <= 1 else 68.0,
        "temp": 37.0,
        "stress": h_init["cort"],
        "cohesion": clip(0.60 * h_init["oxi"] + 0.40 * (1.0 - 0.65 * h_init["tris"]), 0.0, 1.0),
        "pleasure": clip(0.50 * h_init["dop"] + 0.30 * h_init["oxi"] + 0.15 * h_init["res"] - 0.35 * h_init["cort"] + 0.12, 0.0, 1.0),
        "inventory": 0,
        "knownOtherHunger": "poco_hambre" if gen_number <= 1 else "desconocido",
        "socialConfidence": 0.80 if gen_number <= 1 else 0.30,  # HOT: certeza sobre el estado interno del compañero
        "cyclesSinceAsked": 3 if gen_number <= 1 else 7,
        "lastOtherQuote": "Tengo solo un poco de hambre, pero me siento tranquilo a tu lado.",
        "lastPartnerId": None,
        "bereaved": False,
        "forcedAction": None,
        "evasionCooldown": 0,
        "idleLockout": 0,
        "gammaExtinction": compute_individual_gamma(th),
        "isProspectiveCapable": True,
        "prospectionMode": False,
        "prospectionCycles": 0,
        "idleCycles": 0,
        "sensoryRadius": 15.0,
        "tauDelib": 0.65,
        "lMaxDelib": 128,
        "attentionSchema": {
            "mode": "EXTEROCEPTIVO_ALERTA",
            "radius": 15.0,
            "focalTarget": "ENTORNO_PERIMETRAL",
            "earlyEvasionsCount": 0,
            "ignoredStimuliCount": 0,
            "circuitBreakerCount": 0,
        },
        "epistemicStats": {
            "hypothesesFormulated": 0,
            "hypothesesValidatedInDest": 0,
            "hypothesesFalsified": 0,
            "inheritedBeliefsVerified": 0,
            "inheritedBeliefsContradicted": 0,
            "cumulativePredictionError": 0.0,
        },
        "activeHypothesis": None,
        "outsideCycles": 0,
        "sectorStats": {
            "NORTE": {"harvests": 0, "hazards": 0},
            "SUR":   {"harvests": 0, "hazards": 0},
            "ESTE":  {"harvests": 0, "hazards": 0},
            "OESTE": {"harvests": 0, "hazards": 0},
        },
        "lastBiteCycle": -999,
        "lastAttacker": None,
        "learnedRules": {
            "targetSavings": MAX_BACKPACK,
            "acceptedIdeasList": [],
            "acceptedKeys": [],
            "empiricalConclusions": [],
        },
        "frequencies": {
            "ABRAZAR": 10, "ALIMENTAR": 8, "COMER": 9, "PREGUNTAR": 8, "CAMINAR": 6,
            "ESTE": 0, "OESTE": 0, "NORTE": 0, "SUR": 0, "HUIR": 1, "EVADIR_DEPREDADOR": 0,
            "IDEA_ACEPTADA": 1, "GUARDAR_REFUGIO": 0, "COMER_REFUGIO": 0,
        },
        "typeFrequencies": {
            "PELIGRO_INANICION_MORTAL": 1,
            "SACIEDAD_NUTRICIONAL": 8,
            "ALTRUISMO_NUTRICIONAL": 8,
            "DIALOGO_EMPATICO": 8,
            "REGULACION_AFECTIVA": 10,
        },
        "engrams": create_initial_engrams(h_init),
        "thoughtLog": [],
        "latentReflections": [],
    }


def create_environment_state(rng, cultural_enabled=True, pantry_enabled=True, num_predators=3):
    if num_predators == 5:
        initial_npcs = [
            {"id": "pred_1", "name": "Acechador Perimetral", "emoji": "🐆", "x": 50.0, "y": 31.0,
             "angle": 0.0, "radiusX": 18.5, "radiusY": 16.5, "speed": 0.042, "zone": "Órbita Perimetral",
             "vitalCycles": 500, "maxVitalCycles": 1500, "bitesCount": 0},
            {"id": "pred_2", "name": "Rastreador Veloz", "emoji": "🦊", "x": 50.0, "y": 27.5,
             "angle": 1.25, "radiusX": 22.5, "radiusY": 20.5, "speed": -0.038, "zone": "Órbita Intermedia Interna",
             "vitalCycles": 800, "maxVitalCycles": 1700, "bitesCount": 0},
            {"id": "pred_3", "name": "Merodeador de Sombras", "emoji": "👹", "x": 50.0, "y": 74.5,
             "angle": 2.51, "radiusX": 26.5, "radiusY": 24.5, "speed": 0.036, "zone": "Anillo Medio",
             "vitalCycles": 1100, "maxVitalCycles": 1900, "bitesCount": 0},
            {"id": "pred_4", "name": "Bestia de Ronda", "emoji": "🐺", "x": 50.0, "y": 21.5,
             "angle": 3.77, "radiusX": 30.5, "radiusY": 28.5, "speed": -0.034, "zone": "Órbita Intermedia Externa",
             "vitalCycles": 1400, "maxVitalCycles": 2100, "bitesCount": 0},
            {"id": "pred_5", "name": "Tigre de los Confines", "emoji": "🐻", "x": 50.0, "y": 82.5,
             "angle": 5.02, "radiusX": 34.5, "radiusY": 32.5, "speed": 0.030, "zone": "Órbita Periférica Profunda",
             "vitalCycles": 1700, "maxVitalCycles": 2300, "bitesCount": 0},
        ]
    else:
        initial_npcs = [
            {"id": "pred_1", "name": "Acechador Orbital Interior", "emoji": "🐆", "x": 50.0, "y": 31.0,
             "angle": 0.0, "radiusX": 18.5, "radiusY": 16.5, "speed": 0.042, "zone": "Órbita Perimetral",
             "vitalCycles": 600, "maxVitalCycles": 1600, "bitesCount": 0},
            {"id": "pred_2", "name": "Bestia de Ronda Exterior", "emoji": "🐺", "x": 50.0, "y": 18.0,
             "angle": 2.1, "radiusX": 30.5, "radiusY": 27.5, "speed": -0.034, "zone": "Órbita Exterior",
             "vitalCycles": 1000, "maxVitalCycles": 1800, "bitesCount": 0},
            {"id": "pred_3", "name": "Merodeador de las Sombras", "emoji": "👹", "x": 50.0, "y": 82.0,
             "angle": 4.2, "radiusX": 24.5, "radiusY": 22.5, "speed": 0.038, "zone": "Anillo Medio",
             "vitalCycles": 1400, "maxVitalCycles": 2000, "bitesCount": 0},
        ]

    return {
        "globalCycle": 0,
        "culturalEnabled": cultural_enabled,
        "pantryEnabled": pantry_enabled,
        "condition": get_condition_code(cultural_enabled, pantry_enabled),
        "num_predators": num_predators,
        "shelterMeat": 0,
        "fireX": 76.0, "fireY": 54.0, "fireVelX": 0.2, "fireVelY": -0.1,
        "coldX": 24.0, "coldY": 46.0, "coldVelX": -0.2, "coldVelY": 0.1,
        # 4 Cazaderos simétricos a exactamente 35.0 m del centro (50, 50) con regeneración natural de presas (stock=2)
        "huntingZones": {
            "NORTE": {"x": 50.0, "y": 15.0, "label": "Cazadero del Norte", "cooldown": 0, "stock": 2},
            "SUR":   {"x": 50.0, "y": 85.0, "label": "Cazadero del Sur",   "cooldown": 0, "stock": 2},
            "OESTE": {"x": 15.0, "y": 50.0, "label": "Cazadero del Oeste", "cooldown": 0, "stock": 2},
            "ESTE":  {"x": 85.0, "y": 50.0, "label": "Cazadero del Este",  "cooldown": 0, "stock": 2},
        },
        "obstacles": [dict(o) for o in ARENA_OBSTACLES],
        "npcs": initial_npcs,
        "agents": {
            "P0":   create_agent_mind(rng, "P0",   "Progenitor Ancestral", 0, 0,    800,  True),
            "ALFA": create_agent_mind(rng, "ALFA", "Ente Alfa",            1, 0,    2000, True),
            "BETA": create_agent_mind(rng, "BETA", "Ente Beta",            2, 1000, 2000, False),
            "GAMA": create_agent_mind(rng, "GAMA", "Ente Gama",            3, 2050, 2000, False),
        },
        "eventTree": [],
        "culturalTransmissions": [],
        "predatorEncounters": [],
        "finalMemoriesSnapshot": {},
    }


def log_global_event(env_state, ev_type, agent_id, description):
    env_state["eventTree"].append({
        "cycle": env_state["globalCycle"],
        "type": ev_type,
        "agentId": agent_id,
        "description": description,
    })


# =========================================================================
# VÍNCULO FAMILIAR Y CO-ADOPCIÓN INTERGENERACIONAL (Secc. 3.4)
# =========================================================================
def get_living_companion(env_state, w):
    ags = env_state["agents"]
    wid = w["id"]
    # Prioridad 1: vínculo filial/parental directo
    if wid == "P0":
        if ags["ALFA"]["agentAlive"]:
            return ags["ALFA"], "mi hijo Ente Alfa"
    elif wid == "ALFA":
        if ags["P0"]["agentAlive"]:
            return ags["P0"], "mi padre ancestral"
        if ags["BETA"]["born"] and ags["BETA"]["agentAlive"]:
            return ags["BETA"], "mi hijo Ente Beta"
    elif wid == "BETA":
        if ags["ALFA"]["agentAlive"]:
            return ags["ALFA"], "mi progenitor Ente Alfa"
        if ags["GAMA"]["born"] and ags["GAMA"]["agentAlive"]:
            return ags["GAMA"], "mi hijo Ente Gama"
    elif wid == "GAMA":
        if ags["BETA"]["agentAlive"]:
            return ags["BETA"], "mi progenitor Ente Beta"

    # Prioridad 2: Co-adopción altruista intergeneracional de parientes huérfanos/supervivientes (Secc. 3.4)
    for cand_id in ("ALFA", "BETA", "GAMA", "P0"):
        if cand_id != wid and ags[cand_id]["born"] and ags[cand_id]["agentAlive"]:
            return ags[cand_id], f"mi pariente adoptivo {ags[cand_id]['name']}"
    return None, "mi familia ausente"


# =========================================================================
# GESTIÓN EPISTÉMICA HOT Y TRANSMISIÓN CULTURAL INTERGENERACIONAL
# =========================================================================
_ENGRAM_FLAGS_CACHE = {}


def _get_engram_flags(e):
    act = e.get("action", "")
    etype = e.get("type", "")
    content_raw = str(e.get("content", ""))
    outcome_raw = str(e.get("outcome", ""))
    val = e.get("val", 0.0)
    cache_key = (etype, act, content_raw, outcome_raw, val)
    cached = _ENGRAM_FLAGS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    if len(_ENGRAM_FLAGS_CACHE) > 60000:
        _ENGRAM_FLAGS_CACHE.clear()
    content_up = (content_raw + " " + outcome_raw).upper()
    m_keys = []
    for d in ("NORTE", "SUR", "ESTE", "OESTE"):
        if d == act or d in etype or d in content_up:
            m_keys.append(f"SECTOR_{d}")
    has_pantry = ("DESPENSA" in etype or "DESPENSA" in act or "DESPENSA" in content_up)
    if has_pantry:
        m_keys.append("DESPENSA_REFUGIO")
    is_warn_type = (val < -0.4 or "PELIGRO" in etype or "TRAUMA" in etype or "ADVERTENCIA" in etype)
    warn_dirs = tuple(d for d in ("NORTE", "SUR", "ESTE", "OESTE") if is_warn_type and (act == d or d in content_raw))
    res = (tuple(m_keys), warn_dirs, has_pantry)
    _ENGRAM_FLAGS_CACHE[cache_key] = res
    return res


def extract_active_mnemic_keys(w):
    """
    Extrae el conjunto de directrices y rumbos activos que residen REALMENTE
    en los 100 engramas finitos del ente (sin consultar almacenes infinitos externos).
    """
    ver = w.get("_engramsVersion", 0)
    if w.get("_cachedMnemicVer") == ver:
        return w["_cachedMnemicKeys"]
    keys = set()
    warn_dirs = set()
    has_pantry = False
    for e in w["engrams"]:
        mk, wd, hp = _get_engram_flags(e)
        keys.update(mk)
        warn_dirs.update(wd)
        if hp:
            has_pantry = True
    w["_cachedMnemicKeys"] = keys
    w["_cachedWarnDirs"] = warn_dirs
    w["_cachedPantryRule"] = has_pantry
    w["_cachedMnemicVer"] = ver
    return keys


def register_empirical_conclusion(w, conclusion_obj):
    if conclusion_obj["key"] not in w["learnedRules"]["acceptedKeys"]:
        w["learnedRules"]["acceptedKeys"].append(conclusion_obj["key"])
    concs = w["learnedRules"]["empiricalConclusions"]
    for existing in concs:
        if existing["key"] == conclusion_obj["key"]:
            old_lbl = existing.get("shortLabel")
            new_conf = conclusion_obj.get("confidence", 0.90)
            same_polarity = (existing.get("val", 0.0) * conclusion_obj.get("val", 0.0)) >= 0.0
            if new_conf >= existing.get("confidence", 0.50) or (not same_polarity):
                if existing.get("epistemicState") == "CREENCIA_HEREDADA" and conclusion_obj.get("epistemicState") == "CONOCIMIENTO_VERIFICADO":
                    if same_polarity:
                        w["epistemicStats"]["inheritedBeliefsVerified"] += 1
                        existing["epistemicState"] = "HERENCIA_CONFIRMADA_EMPIRICAMENTE"
                    else:
                        w["epistemicStats"]["inheritedBeliefsContradicted"] += 1
                        existing["epistemicState"] = "CONOCIMIENTO_VERIFICADO"
                else:
                    existing["epistemicState"] = conclusion_obj.get("epistemicState", existing.get("epistemicState", "CONOCIMIENTO_VERIFICADO"))
                existing["confidence"] = r_num(min(0.99, max(existing.get("confidence", 0.5), new_conf)), 3)
                existing["kind"] = conclusion_obj["kind"]
                existing["engramType"] = conclusion_obj["engramType"]
                existing["val"] = conclusion_obj["val"]
                existing["statement"] = conclusion_obj["statement"]
                existing["shortLabel"] = conclusion_obj["shortLabel"]
                if old_lbl and old_lbl != conclusion_obj["shortLabel"] and old_lbl in w["learnedRules"]["acceptedIdeasList"]:
                    w["learnedRules"]["acceptedIdeasList"].remove(old_lbl)
            if conclusion_obj["shortLabel"] not in w["learnedRules"]["acceptedIdeasList"]:
                w["learnedRules"]["acceptedIdeasList"].append(conclusion_obj["shortLabel"])
            return
    concs.insert(0, dict(conclusion_obj))
    if conclusion_obj["shortLabel"] not in w["learnedRules"]["acceptedIdeasList"]:
        w["learnedRules"]["acceptedIdeasList"].append(conclusion_obj["shortLabel"])


def update_sector_empirical_conclusion(w, dir_key, is_harvest, hazard_cause=""):
    """Actualiza de forma coherente el juicio epistémico sobre un rumbo (cazadero fértil vs corredor hostil)."""
    st = w["sectorStats"][dir_key]
    if is_harvest:
        st["harvests"] += 1
    else:
        st["hazards"] += 1

    # Balance empírico acumulado del corredor
    if st["harvests"] >= st["hazards"]:
        register_empirical_conclusion(w, {
            "key": f"SECTOR_{dir_key}",
            "kind": "CAZADERO_SEGURO",
            "actionDir": dir_key,
            "engramType": f"ENSEÑANZA_CAZADERO_{dir_key}",
            "val": +0.86,
            "confidence": r_num(min(0.98, 0.88 + 0.02 * st["harvests"]), 3),
            "epistemicState": "CONOCIMIENTO_VERIFICADO",
            "shortLabel": f"Caza probada en el {dir_key}",
            "statement": f"En el {dir_key} hay buena caza; yo mismo encontré comida allí.",
        })
    else:
        register_empirical_conclusion(w, {
            "key": f"SECTOR_{dir_key}",
            "kind": "PELIGRO_DIRECCION",
            "actionDir": dir_key,
            "engramType": f"ADVERTENCIA_PELIGRO_{dir_key}",
            "val": -0.84,
            "confidence": r_num(min(0.97, 0.86 + 0.02 * st["hazards"]), 3),
            "epistemicState": "CONOCIMIENTO_VERIFICADO",
            "shortLabel": f"Peligro en el {dir_key}",
            "statement": f"No vayas hacia el {dir_key}; hay demasiado peligro ({hazard_cause}) y casi no hay comida.",
        })


def transmit_conclusion_between_generations(env_state, teacher, student, conclusion_obj):
    speaker_label = f"Mi progenitor {teacher['name']}"
    raw_idea = conclusion_obj["statement"]
    true_val = float(conclusion_obj.get("val", 0.85))
    teacher_conf = float(conclusion_obj.get("confidence", 0.90))

    if not env_state["culturalEnabled"]:
        reason = "Transmisión cultural desactivada por condición de aislamiento experimental (T0)."
        env_state["culturalTransmissions"].append({
            "cycle": env_state["globalCycle"],
            "fromAgent": teacher["id"],
            "toAgent": student["id"],
            "key": conclusion_obj["key"],
            "statement": raw_idea,
            "valence": true_val,
            "confidence": 0.0,
            "accepted": False,
            "reasoning": reason,
        })
        return False, reason

    # 1. ADAPTACIÓN DEL HABLA DEL PROGENITOR VÍA LLM / GENÉTICA HORMONAL
    th = teacher["h"]
    t_prof = teacher.get("profile", {})
    t_tid = t_prof.get("id", "anger")
    t_tone = TEMPERAMENT_VOICES.get(t_tid, "directo y protector")
    teach_arousal = clip(0.50 * th["cort"] + 0.30 * th.get("ira", 0.2) - 0.25 * th["oxi"], 0.0, 1.0)
    tau_teach = r_num(clip(0.25 + 0.10 * teach_arousal, 0.25, 0.35), 2)

    teach_prompt = f"Enseñanza: {raw_idea}"
    teacher_spoken = None
    if LIVE_LOCAL_LLM_ENABLED and estimate_tokens(raw_idea) <= 45:
        teacher_spoken = query_local_llm_if_enabled(
            teach_prompt, tau_teach, 60,
            system_prompt=f"Eres un superviviente {t_tone}. Aconseja a tu hijo en una sola frase."
        )
    if not teacher_spoken:
        if th["cort"] >= 0.70:
            teacher_spoken = f"¡Ten mucho cuidado, {student['name']}! {raw_idea} No te arriesgues a morir allí."
        elif th["oxi"] >= 0.60:
            teacher_spoken = f"Hijo mío, te lo enseño para cuidarte: {raw_idea} Confía en lo que he vivido."
        elif t_prof.get("id") == "disdain":
            teacher_spoken = f"Aprende esto para sobrevivir: {raw_idea}"
        elif t_prof.get("id") == "anger":
            teacher_spoken = f"¡Presta atención y no te descuides! {raw_idea}"
        elif t_prof.get("id") == "optimism":
            teacher_spoken = f"Tranquilo, {student['name']}; he descubierto algo bueno: {raw_idea}"
        else:
            teacher_spoken = f"Hijo mío, te aconsejo esto: {raw_idea}"

    # 2. RECEPCIÓN Y REFLEXIÓN DEL DESCENDIENTE VÍA LLM / GENÉTICA HORMONAL
    sh = student["h"]
    s_prof = student.get("profile", {})
    s_tid = s_prof.get("id", "anger")
    s_tone = TEMPERAMENT_VOICES.get(s_tid, "cauteloso y perceptivo")
    stud_arousal = clip(0.50 * sh["cort"] + 0.25 * sh.get("tris", 0.2) - 0.20 * sh["oxi"], 0.0, 1.0)
    tau_stud = r_num(clip(0.25 + 0.10 * stud_arousal, 0.25, 0.35), 2)

    # Compuerta fisiológica de receptividad consciente (alto cortisol o inanición bloquean asimilación)
    if student["h"]["cort"] > 0.80 or student["energy"] < 20.0:
        accepted = False
        inh_conf = 0.0
        stud_prompt = f"Eres un superviviente {s_tone}. Tu cuerpo sufre pánico y hambre extrema. Tu padre te ha dicho: \"{teacher_spoken}\". Di en una sola frase por qué no puedes concentrarte en su consejo."
        reason = None
        if LIVE_LOCAL_LLM_ENABLED and estimate_tokens(teacher_spoken) <= 45:
            llm_reason = query_local_llm_if_enabled(
                stud_prompt, tau_stud, 55,
                system_prompt="Habla únicamente en primera persona, expresando tu agobio somático inmediato en una sola frase breve."
            )
            if llm_reason:
                clean_r = re.sub(r'^(en una sola frase,?\s*|lo que pienso( del consejo de mi padre)? es que\s*|me diría que\s*|me parece que\s*|me gustaría decir que\s*|lo que me piensas es:?\s*)+', '', llm_reason, flags=re.IGNORECASE).strip()
                reason = (clean_r[0].upper() + clean_r[1:]) if clean_r else llm_reason
        if not reason:
            reason = f'Escuché a {speaker_label} decirme: "{teacher_spoken}", pero tengo tanta hambre y tanto miedo que no puedo concentrarme en su consejo.'
    else:
        accepted = True
        # HOT: El receptor etiqueta la enseñanza como CREENCIA_HEREDADA (confianza menor que percepción directa)
        inh_conf = r_num(clip(teacher_conf * (0.52 + 0.38 * student["h"]["oxi"]), 0.35, 0.82), 3)
        if conclusion_obj["kind"] == "PELIGRO_DIRECCION":
            fear_f = (0.55 * sh["tris"] + 0.45 * sh["oxi"]) / (0.65 * sh["res"] + 0.35)
            student["h"]["cort"] = clip(sh["cort"] + 0.06 * fear_f, 0.0, 1.0)
            base_reason = f'{speaker_label} me advierte: "{teacher_spoken}". Tendré mucho cuidado al acercarme a ese rumbo.'
        elif conclusion_obj["kind"] == "CAZADERO_SEGURO":
            student["h"]["dop"] = clip(sh["dop"] + 0.10 * sh["oxi"], 0.0, 1.0)
            student["h"]["oxi"] = clip(sh["oxi"] + 0.08, 0.0, 1.0)
            base_reason = f'{speaker_label} me enseña: "{teacher_spoken}". Confío en su consejo, pero lo comprobaré con mis propios ojos.'
        else:
            student["h"]["oxi"] = clip(sh["oxi"] + 0.09, 0.0, 1.0)
            base_reason = f'Recibo el consejo de {speaker_label}: "{teacher_spoken}". Confío en él y lo guardo en mi memoria.'

        stud_prompt = f"Eres un superviviente {s_tone}. tu padre te ha dicho {teacher_spoken}. Di en una sola frase qué piensas del consejo de tu padre."
        llm_reason = None
        if LIVE_LOCAL_LLM_ENABLED and estimate_tokens(teacher_spoken) <= 45:
            llm_reason = query_local_llm_if_enabled(
                stud_prompt, tau_stud, 60,
                system_prompt="Habla en primera persona, breve y sincero. Una sola frase."
            )
        if llm_reason:
            clean_r = re.sub(r'^(en una sola frase,?\s*|lo que pienso( del consejo de mi padre)? es que\s*|me diría que\s*|me parece que\s*|me gustaría decir que\s*|lo que me piensas es:?\s*)+', '', llm_reason, flags=re.IGNORECASE).strip()
            reason = (clean_r[0].upper() + clean_r[1:]) if clean_r else llm_reason
        else:
            reason = base_reason

    origin_tag = f"HEREDADA_DE_{teacher['id']}"
    if accepted:
        inherited_copy = dict(conclusion_obj)
        inherited_copy["inheritedFrom"] = teacher["id"]
        inherited_copy["epistemicState"] = "CREENCIA_HEREDADA"
        inherited_copy["confidence"] = inh_conf
        register_empirical_conclusion(student, inherited_copy)

        add_world_engram(
            student,
            env_state["globalCycle"],
            conclusion_obj.get("engramType", "TRANSMISION_CULTURAL_ASIMILADA"),
            conclusion_obj.get("actionDir", "IDEA_ACEPTADA"),
            true_val,
            f"Herencia de {teacher['name']}: Asimilada | Creencia Heredada",
            reason,
            origin_tag=origin_tag,
            epistemic_state="CREENCIA_HEREDADA",
            confidence=inh_conf,
            companion_name=teacher["name"],
        )

    env_state["culturalTransmissions"].append({
        "cycle": env_state["globalCycle"],
        "fromAgent": teacher["id"],
        "toAgent": student["id"],
        "key": conclusion_obj["key"],
        "statement": teacher_spoken,
        "valence": true_val,
        "confidence": inh_conf,
        "accepted": accepted,
        "reasoning": reason,
    })
    log_global_event(env_state, "TRANSMISION_CULTURAL", f"{teacher['id']}➔{student['id']}",
                     f"{'✅ ASIMILADA' if accepted else '❌ RECHAZADA'}: \"{teacher_spoken}\"")
    return accepted, reason
    log_global_event(env_state, "TRANSMISION_CULTURAL", f"{teacher['id']}➔{student['id']}",
                     f"{'✅ ASIMILADA' if accepted else '❌ RECHAZADA'}: \"{raw_idea}\"")
    return accepted, reason



# =========================================================================
# MODELO RBF DE AFINIDAD AFECTIVA CONTINUA Y EXTINCIÓN DIÁTESIS-ESTRÉS
# =========================================================================
HORMONES_LIST = ["cort", "oxi", "dop", "ira", "tris", "res", "cur"]
SIGMAS_HORMONES = {
    "cort": 0.22, "oxi": 0.25, "dop": 0.20,
    "ira": 0.24, "tris": 0.18, "res": 0.16, "cur": 0.18
}
WEIGHTS_HORMONES = {
    "cort": 0.22, "ira": 0.18, "tris": 0.18,
    "dop": 0.14, "oxi": 0.12, "cur": 0.08, "res": 0.08
}


def compute_rbf_affinity(h_curr, h_engram):
    """Calcula la afinidad afectiva continua A_i(t) in (0, 1] mediante kernel gaussiano RBF."""
    d2 = 0.0
    for k in HORMONES_LIST:
        h_c = h_curr.get(k, 0.2)
        h_e = h_engram.get(k, h_c)
        diff = (h_c - h_e) / SIGMAS_HORMONES[k]
        d2 += WEIGHTS_HORMONES[k] * (diff ** 2)
    return math.exp(-d2 / 2.0)


def compute_individual_gamma(theta):
    """Calcula la tasa de habituación/extinción somática gamma acoplada a la diátesis constitucional."""
    th_res = theta.get("res", 0.6)
    th_cort = theta.get("cort_base", theta.get("cort", 0.2))
    th_dop = theta.get("dop", 0.5)
    vuln = (1.0 - th_res) * 0.45 + (th_cort / 0.35) * 0.30 - (th_dop * 0.15)
    gamma = 0.52 + 0.44 * clip(vuln, 0.0, 1.0)
    return clip(gamma, 0.50, 0.96)

# =========================================================================
# SECCIÓN 2.2: INTEGRACIÓN DE LAS 7 EDOs NEUROENDOCRINAS ACOPLADAS
# =========================================================================
def integrate_neuroendocrine_odes(w, signals):
    """
    Integra por Euler (dt = 1 ciclo) el sistema acoplado de 7 EDOs de la Sección 2.2:
    h(t) = <cort, oxi, dop, ira, tris, res, cur> in [0.0, 1.0]^7
    relajándose hacia theta_temp in [0.10, 0.90]^7.
    """
    th = w["profile"]["theta"]
    h = w["h"]

    # 1. Cortisol (h_cort): estrés somático, daño térmico, amenaza depredadora, hambre aguda vs abrazo/refugio
    dh_cort = (
        -0.075 * (h["cort"] - th["cort_base"])
        + 0.18 * signals["thermal_damage"]
        + 0.28 * signals["predator_threat"]
        + 0.12 * signals["hunger_alarm"]
        - 0.26 * signals["hug"]
        - 0.035 * signals["in_shelter"]
    )

    # 2. Oxitocina (h_oxi): afiliación social, contacto y alimento compartido vs separación
    dh_oxi = (
        -0.060 * (h["oxi"] - th["oxi"])
        + 0.28 * signals["hug"]
        + 0.30 * signals["shared_food"]
        + 0.025 * signals["near_companion"]
        - 0.045 * signals["separated"]
    )

    # 3. Dopamina (h_dop): SEEKING, ingesta/cosecha y validación empírica en campo
    dh_dop = (
        -0.075 * (h["dop"] - th["dop"])
        + 0.25 * signals["ingest_or_harvest"]
        + 0.32 * signals["empirical_validation"]
        - 0.14 * signals["parent_death"]
    )

    # 4. Ira (h_ira): bloqueo físico en obstáculos/bordes y daño físico vs calma de refugio
    dh_ira = (
        -0.080 * (h["ira"] - th["ira"])
        + 0.28 * signals["blocked"]
        + 0.30 * signals["physical_damage"]
        + 0.06 * signals["hunger_alarm"]
        - 0.055 * signals["in_shelter"]
    )

    # 5. Tristeza (h_tris): pérdida de progenitor/familiar y aislamiento vs abrazo
    dh_tris = (
        -0.038 * (h["tris"] - th["tris"])
        + 0.56 * signals["parent_death"]
        + 0.040 * signals["loneliness"]
        - 0.24 * signals["hug"]
    )

    # 6. Resiliencia (h_res): crisis superada vs desgaste por cortisol elevado crónico
    dh_res = (
        -0.045 * (h["res"] - th["res"])
        + 0.18 * signals["crisis_overcome"]
        - 0.075 * max(0.0, h["cort"] - 0.48)
    )

    # 7. Curiosidad (h_cur): zona virgen explorada vs inhibición por cortisol
    dh_cur = (
        -0.065 * (h["cur"] - th["cur"])
        + 0.20 * signals["virgin_zone"]
        - 0.11 * max(0.0, h["cort"] - 0.36)
    )

    h["cort"] = clip(h["cort"] + dh_cort, 0.0, 1.0)
    h["oxi"] = clip(h["oxi"] + dh_oxi, 0.0, 1.0)
    h["dop"] = clip(h["dop"] + dh_dop, 0.0, 1.0)
    h["ira"] = clip(h["ira"] + dh_ira, 0.0, 1.0)
    h["tris"] = clip(h["tris"] + dh_tris, 0.0, 1.0)
    h["res"] = clip(h["res"] + dh_res, 0.0, 1.0)
    h["cur"] = clip(h["cur"] + dh_cur, 0.0, 1.0)

    # Variables macro-interoceptivas sincronizadas para barras UI y qualia
    w["stress"] = h["cort"]
    w["cohesion"] = clip(0.60 * h["oxi"] + 0.40 * (1.0 - 0.65 * h["tris"]), 0.0, 1.0)
    inv_bonus = 0.06 * math.log(1.0 + w["inventory"] + (signals["shelter_meat"] if signals["pantry_enabled"] else 0)) * 1.4426950408889634
    w["pleasure"] = clip(
        0.46 * h["dop"] + 0.26 * h["oxi"] + 0.14 * h["res"] - 0.34 * h["cort"] - 0.22 * h["tris"] + 0.10 + inv_bonus,
        0.0, 1.0
    )

    # Secc. 2.4 Ec. 2.4 y 2.5: Modulación neuroinspirada de parámetros deliberativos
    w["tauDelib"] = r_num(clip(0.55 + 0.30 * h["dop"] - 0.25 * h["cort"] + 0.20 * h["cur"], 0.10, 1.20), 3)
    w["lMaxDelib"] = r_num(clip(128.0 - 64.0 * h["cort"] + 32.0 * h["oxi"], 48.0, 176.0), 0)


# =========================================================================
# SECCIÓN 2.4 y 3.3: SÍNTESIS INTROSPECTIVA DE 2º ORDEN (CON OPCIÓN LLM LOCAL)
# =========================================================================
def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = len(text.strip().split())
    chars = len(text)
    return max(round(words * 1.35), round(chars / 3.7))


def clean_llm_echo(text: str) -> str:
    if not text:
        return ""
    clean = text.strip()
    echo_patterns = [
        r'^(eres un superviviente[^.:!\n]*[.:!\n]\s*)+',
        r'^(en una sola frase,?\s*)+',
        r'^(lo que viv[ií](ste)?:?\s*)+',
        r'^(hecho vivido:?\s*)+',
        r'^(acontecimientos vividos:?\s*)+',
        r'^(lo que pienso( del plan| del consejo)?( de mi padre)?:?\s*)+',
        r'^(mi plan es( que)?:?\s*)+',
        r'^(como superviviente[^.:!\n]*[.:!\n]\s*)+',
        r'^(mi pensamiento es( que)?:?\s*)+',
        r'^(como (padre|hijo)[^.:!\n]*[.:!\n]\s*)+',
    ]
    for pat in echo_patterns:
        clean = re.sub(pat, '', clean, flags=re.IGNORECASE).strip()
    clean = clean.strip('"\'«»“”').strip()
    if clean:
        clean = clean[0].upper() + clean[1:]
    return clean


def query_local_llm_if_enabled(qualitative_prompt, tau, l_max, system_prompt=None):
    if not LIVE_LOCAL_LLM_ENABLED:
        return None
    endpoints = LOCAL_LLM_ENDPOINTS
    sys_p = system_prompt or "Habla únicamente en primera persona desde tus sensaciones viscerales cualitativas, sin números ni tecnicismos. Resume en una o dos frases breves tu vivencia o pensamiento en español."
    body = json.dumps({
        "model": LOCAL_LLM_MODEL,
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": qualitative_prompt},
        ],
        "temperature": float(tau),
        "max_tokens": int(l_max),
        "frequency_penalty": 0.8,
        "stop": ["\n\n", "Ente:", "Sistema:"]
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LOCAL_LLM_API_KEY}"
    }

    for ep in endpoints:
        try:
            req = urllib.request.Request(ep, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=LOCAL_LLM_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith('"') and text.endswith('"') and len(text) > 2:
                    text = text[1:-1].strip()
                if text:
                    return clean_llm_echo(text)
        except Exception:
            continue
    return None


def process_engram_text_with_llm(w, base_text, etype, action, val, companion_name="Ninguno"):
    """
    Procesa y personaliza el texto de un engrama o recuerdo a través del LLM,
    modulado por la genética del ente (perfil temperamental) y su
    estado hormonal actual (h), con temperatura alostática dinámica.
    """
    prof = w.get("profile", {})
    t_name = prof.get("name", "Estoico")
    t_desc = prof.get("desc", "")
    h = w.get("h", {})
    cort = h.get("cort", 0.25)
    oxi = h.get("oxi", 0.50)
    dop = h.get("dop", 0.50)
    stress_val = w.get("stress", cort)
    energy_val = w.get("energy", 70.0)

    # Engramas que ya traen su reflexión o diálogo elaborado (ej. transmisiones o planes)
    if etype.startswith("TRANSMISION_CULTURAL") or etype.startswith("ENSOÑACION"):
        return base_text

    # Saliencia afectiva para modulación inmediata: eventos rutinarios de bajo impacto (|val| < 0.45)
    # se conservan en buffer sensorial y son sintetizados por el LLM en la fase de consolidación episódica.
    if abs(val) < 0.45 and not ("TRAUMA" in etype or "COSECHA" in etype or "FALSACION" in etype):
        return base_text

    if estimate_tokens(base_text) > 75:
        return base_text

    # Temperatura alostática acotada en zona segura (0.25 - 0.35)
    emotional_arousal = clip(
        0.40 * stress_val + 0.30 * h.get("ira", 0.2) + 0.20 * h.get("tris", 0.2) + 0.30 * abs(val) - 0.25 * oxi,
        0.0, 1.0
    )
    tau = r_num(clip(0.25 + 0.10 * emotional_arousal, 0.25, 0.35), 2)

    if LIVE_LOCAL_LLM_ENABLED:
        tid = prof.get("id", "anger")
        t_tone = TEMPERAMENT_VOICES.get(tid, "directo y prudente")
        prompt = f"Hecho vivido: {base_text}"
        sys_p = f"Eres un superviviente {t_tone}. Escribe en primera persona lo que viviste en una sola frase."
        llm_out = query_local_llm_if_enabled(
            prompt, tau, 60,
            system_prompt=sys_p
        )
        if llm_out:
            return llm_out

    # Adaptación afectiva offline según estrés somático y trauma agudo (sin telemetría técnica)
    dir_name = action.lower() if action in ("NORTE", "SUR", "ESTE", "OESTE") else "el camino"
    if "TRAUMA" in etype or stress_val >= 0.70 or val <= -0.70:
        if "DEPREDADOR" in etype or "RUPTURA" in etype or action == "HUIR":
            return f"¡Un monstruo salvaje me atacó de golpe en el {dir_name}! Sentí el desgarro de sus fauces y el terror de morir; logré huir a ciegas con el cuerpo temblando."
        elif "TORMENTA" in etype:
            return f"¡Una tormenta despiadada me azotó como mil cuchillas en el {dir_name}! Sentí que caería muerto antes de alcanzar el refugio."
        elif "ORFANDAD" in etype or "SENESCENCIA" in etype:
            return f"¡Presencié la muerte de mi compañero! Siento un vacío negro en el pecho y el terror de quedarme completamente solo."

    return base_text

    return base_text


def desc_episodic_step(e_st):
    act_s = e_st.get("action", "")
    etype = e_st.get("type", "")
    content = e_st.get("content", "").strip()

    # Si es un engrama vivencial con contenido generado (y no es un axioma congénito innato)
    if content and e_st.get("origin") != "INNATA" and not content.startswith("Sé que "):
        c_clean = content.lstrip("¡").rstrip("!.").strip()
        if c_clean.lower().startswith("pensamiento en reposo:"):
            c_clean = c_clean[len("pensamiento en reposo:"):].strip()
        if "TRAUMA" in etype or "TORMENTA" in etype or "ORFANDAD" in etype:
            return f"recordé con horror que {c_clean[0].lower() + c_clean[1:]}"
        if "COSECHA" in etype:
            return f"recordé con alegría que {c_clean[0].lower() + c_clean[1:]}"
        if "FRACASO" in etype or "OBSTACULO" in etype:
            return f"recordé que {c_clean[0].lower() + c_clean[1:]}"
        if "CAUSAL" in etype or "PROSPECCION" in etype:
            return f"recordé que {c_clean[0].lower() + c_clean[1:]}"
        if len(c_clean) < 70:
            return c_clean[0].lower() + c_clean[1:]

    if act_s == "HUIR":
        return "me atacó una bestia y tuve que huir"
    if act_s == "EVADIR_DEPREDADOR":
        return "vi a tiempo una bestia y la esquivé"
    if act_s in ("ESTE", "OESTE", "NORTE", "SUR"):
        if "COSECHA" in etype:
            return f"encontré carne en el {act_s}"
        if "FRACASO_OBSTACULO" in etype or "OBSTACULO" in etype:
            return f"una roca me cortó el paso en el {act_s}"
        if "ESCASEZ" in etype:
            return f"busqué en el {act_s} pero no había presas"
        if "TORMENTA" in etype:
            return f"me azotó una tormenta durísima en el {act_s}"
        return f"avancé hacia el {act_s}"
    if act_s == "ALIMENTAR":
        return "le di comida a mi compañero"
    if act_s in ("COMER", "COMER_REFUGIO"):
        return "comí para calmar el hambre"
    if act_s == "GUARDAR_REFUGIO":
        return "guardé carne en el almacén del refugio"
    if act_s == "ENSOÑACION":
        return "descansé pensando en mis planes"
    if act_s in ("REFUGIO", "DORMIR"):
        return "permanecí en el refugio templado reponiendo energías"
    return "permanecí a resguardo en el refugio"


def format_causal_chain(episode_seq):
    if not episode_seq:
        return "permanecí a resguardo"
    raw_descs = [desc_episodic_step(ep) for ep in episode_seq]
    descs = []
    prev = None
    count = 0
    def is_shelter_rest(text):
        t = text.lower()
        return ("reponiendo" in t or "reposando" in t or "a resguardo" in t) and ("regreso" not in t and "rumbo" not in t and "avanz" not in t)

    for d in raw_descs:
        if d == prev:
            count += 1
        else:
            if prev:
                if is_shelter_rest(prev):
                    descs.append(f"permanecí en el refugio templado reponiendo energías bastante tiempo, durante {count} ciclos" if count >= 3 else (f"permanecí en el refugio templado reponiendo energías durante {count} ciclos" if count > 1 else prev))
                else:
                    descs.append(f"{prev} durante {count} ciclos" if count > 1 else prev)
            prev = d
            count = 1
    if prev:
        if is_shelter_rest(prev):
            descs.append(f"permanecí en el refugio templado reponiendo energías bastante tiempo, durante {count} ciclos" if count >= 3 else (f"permanecí en el refugio templado reponiendo energías durante {count} ciclos" if count > 1 else prev))
        else:
            descs.append(f"{prev} durante {count} ciclos" if count > 1 else prev)

    if len(descs) == 1:
        s = descs[0]
        return s[0].upper() + s[1:]
    if len(descs) == 2:
        return f"Primero {descs[0]}, y luego {descs[1]}"
    if len(descs) == 3:
        return f"Primero {descs[0]}, luego {descs[1]}, y finalmente {descs[2]}"
    return f"Primero {descs[0]}, después {', luego '.join(descs[1:-1])}, y finalmente {descs[-1]}"


# =========================================================================
# CONSOLIDACIÓN JERÁRQUICA DE 3 ZONAS Y PODA AFECTIVA (Secc. 3.2 y 3.4)
# =========================================================================
def find_natural_episode_boundary(engrams, start_idx, max_len=7, max_boundary=None):
    """
    Detecta el límite natural del episodio contiguo a partir de start_idx con un tope de hasta max_len (7) engramas.
    Reconoce límites naturales:
    - Final de expedición (salida -> caza/trauma -> retorno seguro a refugio).
    - Periodo de estancia/cuidado social en refugio hasta nueva salida al exterior.
    - Bloque de axiomas congénitos iniciales.
    - Transmisiones culturales y eventos mayores.
    """
    total = len(engrams)
    if max_boundary is None or max_boundary > total:
        max_boundary = total
    if start_idx >= max_boundary:
        return start_idx

    limit = min(start_idx + max_len, max_boundary)
    e0 = engrams[start_idx]

    # 1. Bloque de axiomas congénitos iniciales
    if e0.get("origin") == "INNATA":
        curr = start_idx + 1
        while curr < limit and engrams[curr].get("origin") == "INNATA":
            curr += 1
        return curr

    # 2. Bloque de expedición exterior
    outdoor_actions = {"NORTE", "SUR", "ESTE", "OESTE", "CAMINAR", "HUIR", "EVADIR_DEPREDADOR"}
    shelter_actions = {"REFUGIO", "GUARDAR_REFUGIO", "COMER_REFUGIO", "DORMIR"}
    is_outdoor_start = (e0.get("action") in outdoor_actions) or ("TORMENTA" in e0.get("type", ""))

    if is_outdoor_start:
        curr = start_idx + 1
        while curr < limit:
            ec = engrams[curr]
            act = ec.get("action", "")
            etype = ec.get("type", "")
            # El retorno al refugio o final de trayecto cierra naturalmente la expedición
            if act in shelter_actions or "REFUGIO" in etype:
                return curr + 1
            if "TRAUMA_MUERTE_" in etype or "ORFANDAD" in etype:
                return curr + 1
            curr += 1
        return limit

    # 3. Bloque de estancia social / descanso en refugio
    shelter_social = {"ABRAZAR", "ALIMENTAR", "COMER", "PREGUNTAR", "ENSOÑACION"}
    is_shelter_start = (e0.get("action") in shelter_actions) or (e0.get("action") in shelter_social)
    if is_shelter_start:
        curr = start_idx + 1
        while curr < limit:
            ec = engrams[curr]
            act = ec.get("action", "")
            # Si inicia una marcha hacia el exterior, la estancia en refugio concluye antes de salir
            if act in outdoor_actions:
                return curr
            if "TRAUMA_MUERTE_" in ec.get("type", ""):
                return curr
            curr += 1
        return limit

    # 4. Transmisión cultural
    if e0.get("type", "").startswith("TRANSMISION_CULTURAL") or e0.get("action") == "TRANSMITIR":
        curr = start_idx + 1
        while curr < limit and (engrams[curr].get("type", "").startswith("TRANSMISION_CULTURAL") or engrams[curr].get("action") in ("TRANSMITIR", "PREGUNTAR")):
            curr += 1
        return curr

    return limit


def summarize_sequence_with_llm_or_heuristic(w, seq, anchor, cycle_range):
    prof = w.get("profile", {})
    t_name = prof.get("name", "Estoico")
    t_desc = prof.get("desc", "")
    h = w.get("h", {})
    stress_val = w.get("stress", h.get("cort", 0.25))
    has_trauma = any("TRAUMA" in e.get("type", "") or e.get("val", 0.0) <= -0.50 for e in seq)
    emotional_load = clip(0.50 * stress_val + (0.45 if has_trauma else 0.0), 0.0, 1.0)
    tau = r_num(clip(0.25 + 0.10 * emotional_load, 0.25, 0.35), 2)

    # Bloque completo de axiomas innatos iniciales
    if all(e.get("origin") == "INNATA" for e in seq):
        return "Tengo grabado en el cuerpo lo esencial: evitar el hambre, buscar sustento en los cazaderos y cuidar de los míos."

    groups = []
    for e in seq:
        c_text = e.get('content', '').strip()
        if not c_text:
            continue
        if groups and groups[-1]['text'] == c_text:
            groups[-1]['count'] += 1
        else:
            groups.append({'text': c_text, 'count': 1})

    events_desc = []
    for g in groups:
        c_text = g['text'].rstrip('.')
        cnt = g['count']
        if 'refugio' in c_text.lower() and any(w in c_text.lower() for w in ['reponiendo', 'reposando', 'calma', 'bienestar']):
            if cnt >= 3:
                events_desc.append(f"- Permanecí en el refugio templado reponiendo energías bastante tiempo, durante {cnt} ciclos.")
            elif cnt > 1:
                events_desc.append(f"- Permanecí en el refugio templado reponiendo energías durante {cnt} ciclos.")
            else:
                events_desc.append("- Permanecí en el refugio templado reponiendo energías.")
        elif cnt > 1:
            events_desc.append(f"- {c_text} durante {cnt} ciclos.")
        else:
            events_desc.append(f"- {c_text}.")
    events_text = "\n".join(events_desc)

    # FILTRO DE TOKENS PARA COMPRESIÓN: solo si <= 75 tokens
    if LIVE_LOCAL_LLM_ENABLED and estimate_tokens(events_text) <= 75:
        tid = prof.get("id", "anger")
        t_tone = TEMPERAMENT_VOICES.get(tid, "directo y prudente")
        prompt = f"Acontecimientos vividos:\n{events_text}"
        sys_p = f"Eres un superviviente {t_tone}. Resume en una sola frase lo que viviste."
        llm_out = query_local_llm_if_enabled(
            prompt, tau, 60,
            system_prompt=sys_p
        )
        if llm_out:
            return llm_out

    # Heurística afectiva y narrativa de alta fidelidad (offline)
    has_trauma = any("TRAUMA" in e.get("type", "") or e.get("val", 0.0) <= -0.50 for e in seq)
    has_harvest = any("COSECHA" in e.get("type", "") or "PRESA" in e.get("type", "") for e in seq)
    has_transmission = any("TRANSMISION" in e.get("type", "") or e.get("origin", "").startswith("HEREDADA") for e in seq)
    has_social = any(e.get("action") in ("ABRAZAR", "ALIMENTAR", "PREGUNTAR") for e in seq)

    dirs = [e.get("action") for e in seq if e.get("action") in ("NORTE", "SUR", "ESTE", "OESTE")]
    main_dir = dirs[0] if dirs else None

    if has_transmission:
        return "Recordé las enseñanzas y consejos que recibí de los míos en esos ciclos, afianzando en mi interior el valor de su sabiduría."
    elif has_trauma and has_harvest and main_dir:
        return f"Recuerdo que fui hacia el {main_dir} sorteando grandes peligros; aunque el miedo y las fieras me amenazaron, conseguí sustento y logré regresar con vida."
    elif has_trauma:
        return "Viví un periodo de extrema tensión y peligro en el páramo, donde el sufrimiento me puso al límite, pero resistí y salí adelante."
    elif has_harvest and main_dir:
        return f"Completé una expedición provechosa hacia el {main_dir}, cobrando caza para abastecerme y regresando con alivio al refugio."
    elif main_dir:
        return f"Exploré con cautela los alrededores del {main_dir}, reconociendo el terreno y regresando al refugio sin contratiempos."
    elif has_social:
        return "Pasé un tiempo de convivencia y cuidado mutuo en el refugio, compartiendo comida, abrazos y templando el ánimo junto a mi compañero."
    elif any(e.get("action") == "REFUGIO" or "HOMEOSTASIS" in e.get("type", "") or "DESPENSA" in e.get("type", "") for e in seq):
        has_pantry = any(e.get("action") == "DESPENSA" or "DESPENSA" in e.get("type", "") for e in seq)
        total_cycles = len(seq)
        if has_pantry:
            return f"Permanecí al amparo del refugio reponiendo fuerzas y alimentándome de las reservas comunales durante {total_cycles} ciclos."
        else:
            if total_cycles >= 3:
                return f"Permanecí en el refugio templado reponiendo energías bastante tiempo, durante {total_cycles} ciclos."
            elif total_cycles > 1:
                return f"Permanecí en el refugio templado reponiendo energías durante {total_cycles} ciclos."
            else:
                return "Permanecí en el refugio templado reponiendo energías."
    else:
        chain = format_causal_chain(seq)
        return (chain[0].upper() + chain[1:] + ".") if not chain.endswith(".") else (chain[0].upper() + chain[1:])


def compress_episodic_sequence(w, seq):
    if not seq:
        return None

    # Regla del Pico Somático de Kahneman: S_j = |val|*0.40 + ||deltaH||*0.60
    def compute_saliency(e_item):
        v = abs(e_item.get("val", 0.0))
        dH = e_item.get("deltaH", {})
        norm_dh = math.sqrt(sum(WEIGHTS_HORMONES[k] * (dH.get(k, 0.0) ** 2) for k in HORMONES_LIST))
        return v * 0.40 + norm_dh * 0.60

    anchor = max(seq, key=compute_saliency)
    end_item = seq[-1]

    # Regla Peak-End de Kahneman bi-factorial (Secc. 2.4): 0.65 Peak + 0.35 End
    peak_val = anchor.get("val", 0.0)
    end_val = end_item.get("val", 0.0)
    chapter_val = 0.65 * peak_val + 0.35 * end_val

    peak_somatic = float(anchor.get("somaticImpact", 50.0))
    end_somatic = float(end_item.get("somaticImpact", 50.0))
    chapter_somatic = 0.65 * peak_somatic + 0.35 * end_somatic

    h_snap_anchor = anchor.get("hSnapshot", {k: 0.2 for k in HORMONES_LIST})
    h_snap_end = end_item.get("hSnapshot", {k: 0.2 for k in HORMONES_LIST})
    chapter_h_snapshot = {
        k: r_num(0.65 * h_snap_anchor.get(k, 0.2) + 0.35 * h_snap_end.get(k, 0.2), 4)
        for k in HORMONES_LIST
    }

    dh_anchor = anchor.get("deltaH", {k: 0.0 for k in HORMONES_LIST})
    dh_end = end_item.get("deltaH", {k: 0.0 for k in HORMONES_LIST})
    chapter_delta_h = {
        k: r_num(0.65 * dh_anchor.get(k, 0.0) + 0.35 * dh_end.get(k, 0.0), 4)
        for k in HORMONES_LIST
    }

    start_cycle = seq[0].get("cycle", 1)
    end_cycle = end_item.get("cycle", start_cycle)
    cycle_range = f"{start_cycle}–{end_cycle}" if end_cycle != start_cycle else str(start_cycle)

    total_rep = sum(e.get("repetitionCount", 1) for e in seq)
    comp_text = summarize_sequence_with_llm_or_heuristic(w, seq, anchor, cycle_range)

    act = anchor.get("action", end_item.get("action", "VIVENCIA"))
    etype = f"CONSOLIDADO_{anchor.get('type', act)}"

    comp_engram = {
        "id": seq[0].get("id", 1),
        "type": etype,
        "action": act,
        "content": comp_text,
        "outcome": comp_text,
        "context": dict(anchor.get("context", seq[0].get("context", {}))),
        "val": r_num(chapter_val, 3),
        "deltas": f"Episodio: Ciclos {cycle_range} | Eventos consolidados: {len(seq)} | Saliencia Peak-End: {chapter_somatic:.1f}",
        "cycle": start_cycle,
        "cycleEnd": end_cycle,
        "cycleRange": cycle_range,
        "globalCycle": seq[0].get("globalCycle", 0),
        "hSnapshot": chapter_h_snapshot,
        "deltaH": chapter_delta_h,
        "lastSomaticReactivation": -999,
        "evocationCount": sum(e.get("evocationCount", 0) for e in seq),
        "somaticImpact": r_num(peak_somatic, 2),
        "repetitionCount": total_rep,
        "duration": len(seq),
        "retentionScore": 0.0,
        "origin": "CONSOLIDADA_CORTICAL",
        "epistemicState": "MEMORIA_EPISODICA_CONSOLIDADA",
        "confidence": r_num(sum(e.get("confidence", 0.95) for e in seq) / len(seq), 3),
        "isCompressed": True,
        "compressedCount": sum(e.get("compressedCount", 1) for e in seq),
    }
    comp_engram["retentionScore"] = compute_retention(comp_engram, w["age"])
    return comp_engram


def consolidate_and_prune_memory_hierarchical(w):
    """
    Arquitectura Jerárquica de 3 Zonas de Consolidación y Poda de Memoria:
    - Zona C (50 más recientes): Ventana hipocámpica viva, estrictamente blindada (intacta).
    - Zona B (30 intermedios): Buffer episódico de transición donde maduran vivencias contiguas.
    - Zona A (20 más antiguos): Zona cortical profunda consolidada (solo capítulos comprimidos).

    Fase 1: Si hay engramas sin comprimir en Zona A, se comprimen episodios naturales contiguos.
    Fase 2: Cuando Zona A está 100% llena de engramas comprimidos, se poda el engrama con menor
            relevancia emocional (|val|) de Zona A, dejando un hueco libre en el slot 20 de Zona A.
            A continuación, se comprime la secuencia más antigua de Zona B y se inserta en ese slot 20.
    Garantía: Todo el array de 100 engramas mantiene orden cronológico estrictamente monótono no decreciente.
    """
    ZONA_A_SIZE = int(MAX_ENGRAMS * 0.20)
    ZONA_C_PROTECTED = int(MAX_ENGRAMS * 0.50)

    while len(w["engrams"]) > MAX_ENGRAMS:
        total = len(w["engrams"])
        max_consolidation_boundary = max(ZONA_A_SIZE, total - ZONA_C_PROTECTED)

        zona_a = w["engrams"][:ZONA_A_SIZE]
        uncompressed_indices = [idx for idx, e in enumerate(zona_a) if not e.get("isCompressed", False)]

        if uncompressed_indices:
            # FASE 1: Comprimir secuencias contiguas en Zona A
            start_idx = uncompressed_indices[0]
            max_bound = min(max_consolidation_boundary, max(ZONA_A_SIZE, start_idx + 7))
            end_idx = find_natural_episode_boundary(w["engrams"], start_idx, max_len=7, max_boundary=max_bound)

            if end_idx <= start_idx + 1 and start_idx + 2 <= max_bound:
                end_idx = min(start_idx + 2, max_bound)

            if end_idx > start_idx + 1:
                seq = w["engrams"][start_idx:end_idx]
                comp = compress_episodic_sequence(w, seq)
                w["engrams"][start_idx:end_idx] = [comp]
            else:
                w["engrams"][start_idx]["isCompressed"] = True
                if len(w["engrams"]) > MAX_ENGRAMS:
                    min_idx = min(range(min(ZONA_A_SIZE, len(w["engrams"]))), key=lambda i: abs(w["engrams"][i].get("val", 0.0)))
                    w["engrams"].pop(min_idx)
        else:
            # FASE 2: Zona A está 100% consolidada.
            # 1. Poda biológica del engrama con menor valencia emocional (|val|) en Zona A
            min_idx = min(
                range(min(ZONA_A_SIZE, len(w["engrams"]))),
                key=lambda i: (abs(w["engrams"][i].get("val", 0.0)), w["engrams"][i].get("somaticImpact", 0.0))
            )
            w["engrams"].pop(min_idx)

            # 2. Comprimir la secuencia más antigua de Zona B (slot 19, que es el nuevo slot 20 de Zona A)
            start_b = min(ZONA_A_SIZE - 1, len(w["engrams"]) - 1)
            max_bound_b = len(w["engrams"]) - ZONA_C_PROTECTED
            if start_b < max_bound_b:
                end_b = find_natural_episode_boundary(w["engrams"], start_b, max_len=7, max_boundary=max_bound_b)
                if end_b <= start_b + 1 and start_b + 2 <= max_bound_b:
                    end_b = min(start_b + 2, max_bound_b)

                seq_b = w["engrams"][start_b:end_b]
                comp_b = compress_episodic_sequence(w, seq_b)
                w["engrams"][start_b:end_b] = [comp_b]


def extract_causal_episode(w, rng):
    """
    Retro-trazado de Episodio Causal (Causal Episode Backtracking):
    1. Ventana Hipocámpica Reciente: Último 20% de la memoria autobiográfica.
    2. Detección del Pico Somático (Anchor Peak): Engrama con mayor impacto somático absoluto (|val| >= 0.70 o somaticImpact >= 80).
    3. Retro-búsqueda hacia el Límite de Episodio (Boundary Search):
       Retrocede paso a paso buscando el verdadero inicio de la cadena causal:
       - Transición macro de estado (ej: salida del refugio a la intemperie).
       - Decisión deliberada o ensoñación anterior.
       - Tope de seguridad de 5-6 pasos atrás.
    """
    engrams = w["engrams"]
    total = len(engrams)
    if total == 0:
        return [], None, False

    # 1. Ventana Hipocámpica Reciente: Último 20% de la memoria (mínimo 3 engramas si existen)
    window_len = max(3, int(math.ceil(total * 0.20)))
    start_idx = max(0, total - window_len)

    # 2. Detección del Pico Somático (Anchor Peak)
    candidates = []
    for i in range(start_idx, total):
        e = engrams[i]
        # Excluir ensoñaciones previas o axiomas congénitos como ancla vivencial primaria
        if e.get("action") == "ENSOÑACION" or "ENSOÑACION" in e.get("type", "") or e.get("origin") == "INNATA":
            continue

        som = float(e.get("somaticImpact", abs(e.get("val", 0.0)) * 100.0))
        val_abs = abs(float(e.get("val", 0.0)))
        is_tr = (e.get("val", 0.0) <= -0.45) or ("TRAUMA" in e["type"]) or ("FRACASO" in e["type"]) or ("TORMENTA" in e["type"])
        is_hp = (e.get("val", 0.0) >= 0.74) or ("COSECHA" in e["type"]) or ("VALIDACION" in e["type"]) or ("ENSEÑANZA_CAZADERO" in e["type"])

        if is_tr or is_hp or som >= 80.0 or val_abs >= 0.70:
            candidates.append((i, is_tr, som + val_abs * 50.0, e))

    if candidates:
        candidates.sort(key=lambda x: x[2], reverse=True)
        top_thresh = candidates[0][2] * 0.85
        top_candidates = [c for c in candidates if c[2] >= top_thresh]
        anchor_idx, is_trauma, _, final_engram = top_candidates[int(rng.random() * len(top_candidates))]
    else:
        anchor_idx = total - 1
        final_engram = engrams[anchor_idx]
        is_trauma = (final_engram.get("val", 0.0) < 0) or ("TRAUMA" in final_engram["type"])

    # 3. Retro-búsqueda hacia el Límite de Episodio (Boundary Search)
    max_backtrack = 5
    start_ep_idx = anchor_idx
    outdoor_actions = {"NORTE", "SUR", "ESTE", "OESTE", "HUIR", "EVADIR_DEPREDADOR"}
    anchor_is_outdoor = final_engram.get("action", "") in outdoor_actions or "TORMENTA" in final_engram.get("type", "")

    for step_back in range(1, max_backtrack + 1):
        prev_idx = anchor_idx - step_back
        if prev_idx < 0:
            break
        prev_e = engrams[prev_idx]

        # Condición a: Ensoñación o deliberación previa (marca el final del reposo anterior)
        if prev_e.get("action") == "ENSOÑACION" or "ENSOÑACION" in prev_e.get("type", ""):
            start_ep_idx = prev_idx + 1 if prev_idx + 1 <= anchor_idx else prev_idx
            break

        # Condición b: Transición macro de estado (ej: salida del refugio a la intemperie)
        prev_is_shelter = prev_e.get("action") in ("REFUGIO", "GUARDAR_REFUGIO", "COMER_REFUGIO", "DORMIR") or "REFUGIO" in prev_e.get("type", "")
        if anchor_is_outdoor and prev_is_shelter:
            start_ep_idx = prev_idx
            break

        # Condición c: Evento social biográfico mayor
        if "ORFANDAD" in prev_e.get("type", "") or "CUIDADO_PARENTAL" in prev_e.get("type", ""):
            start_ep_idx = prev_idx
            break

        start_ep_idx = prev_idx

    episode_seq = engrams[start_ep_idx : anchor_idx + 1]
    return episode_seq, final_engram, is_trauma


def generate_latent_reflection(w, env_state, episode_seq, final_engram, is_trauma, chosen_hypothesis):
    """
    Genera reflexión composicional de 1º y 2º orden estrictamente bajo Cierre Epistémico
    (cero floats en freeInference), integrando estado hormonal, esquema atencional AST y certeza HOT.
    """
    h = w["h"]
    h_q = get_hunger_qualia(w["energy"])
    d_q = get_distress_qualia(w["stress"])
    p_q = get_pleasure_qualia(w["pleasure"])
    endo_q = get_hormone_qualia(h)
    comp, comp_label = get_living_companion(env_state, w)
    comp_alive = bool(comp and comp["agentAlive"])

    # Detectar si la tríada muestreada incluye un pensamiento previo o creencia heredada (Metacognición 2º orden, Secc. 3.3)
    has_prior_thought = any(("ENSOÑACION" in e["type"] or "VALIDACION" in e["type"] or "FALSACION" in e["type"]) for e in episode_seq)
    has_inherited = any(str(e.get("origin", "")).startswith("HEREDADA") for e in episode_seq)

    ep_state = final_engram.get("epistemicState", "PERCEPCION_DIRECTA") if final_engram else "QUIESCENCIA"
    target_dir = chosen_hypothesis["planAction"]
    cause_dir = chosen_hypothesis.get("causeDir", target_dir)
    chain_story = chosen_hypothesis.get("chainText", "")

    if has_prior_thought:
        meta_clause = f"Al pensar en mis planes anteriores y en lo que pasó en el {cause_dir} ({chain_story}), veo que mi idea previa guió mis pasos"
    elif has_inherited:
        meta_clause = f"Comparo el consejo de mi linaje sobre el {cause_dir} con lo que acabo de vivir ({chain_story})"
    else:
        meta_clause = f"Repaso lo que viví en el {cause_dir}: {chain_story}"

    if is_trauma:
        affect_clause = f"el peligro me dejó {endo_q} y me dice que evite el {cause_dir}"
        plan_clause = f"así que iré a explorar hacia el {target_dir} con los ojos bien abiertos"
    else:
        affect_clause = f"el recuerdo de la comida me da {endo_q} y confianza en la ruta"
        plan_clause = f"así que volveré a buscar comida al {target_dir} para alimentar al clan"

    att_clause = (
        "sabiendo que si me ensimismo no veré venir el peligro"
        if w["attentionSchema"]["ignoredStimuliCount"] > 0
        else "manteniéndome muy atento en cuanto salga del refugio"
    )

    tid = w.get("profile", {}).get("id", "anger")
    t_tone = TEMPERAMENT_VOICES.get(tid, "directo y prudente")
    delib_prompt = (
        f"Recuerdos: {meta_clause}. Siento que {affect_clause}.\n"
        f"Plan: Ir al {target_dir}. {att_clause}."
    )
    base_inference = f"{meta_clause}; {affect_clause}, {plan_clause} ({att_clause})."
    free_inference = None

    # FILTRO DE TOKENS PARA ENSOÑACIONES: solo si <= 55 tokens
    if LIVE_LOCAL_LLM_ENABLED and estimate_tokens(base_inference) <= 55 and (is_trauma or w["stress"] > 0.65 or (env_state["globalCycle"] % 350 == 0)):
        tau_ensonic = r_num(clip(0.25 + 0.10 * w.get("stress", 0.2), 0.25, 0.35), 2)
        llm_text = query_local_llm_if_enabled(
            delib_prompt, tau_ensonic, 60,
            system_prompt=f"Eres un superviviente {t_tone} en tu refugio. Expresa tu pensamiento y plan en una sola frase."
        )
        if llm_text:
            free_inference = clean_llm_echo(llm_text)

    if not free_inference:
        free_inference = base_inference

    # Si L_max es bajo por alto cortisol, truncamiento expresivo neuroinspirado
    max_char_len = max(140, int(w["lMaxDelib"] * 2.8))
    if w["lMaxDelib"] < 85 and len(free_inference) > max_char_len:
        free_inference = free_inference[:max_char_len - 3].rsplit(" ", 1)[0] + "..."

    return {
        "cycle": env_state["globalCycle"],
        "age": w["age"],
        "proprioception": f"{h_q} | {d_q} | {p_q} | {endo_q}",
        "social": f"Vínculo activo con {comp['name']} (certeza social {'alta' if w['socialConfidence'] > 0.6 else 'incierta'})" if comp_alive else "En soledad / orfandad",
        "milestone": f"[{final_engram['type']}] ({ep_state}) en {final_engram['action']}" if final_engram else "Quiescencia en refugio",
        "epistemicOrder": "SEGUNDO_ORDEN_RECURSIVO" if (has_prior_thought or has_inherited) else "PRIMER_ORDEN_CAUSAL",
        "tau": w["tauDelib"],
        "lMax": w["lMaxDelib"],
        "freeInference": free_inference,
    }


def softmax_choice_dir(rng, dirs, scores_map, tau):
    t = max(0.10, tau)
    max_s = max(scores_map[d] for d in dirs)
    exps = [math.exp(clip((scores_map[d] - max_s) / (t * 25.0), -20.0, 20.0)) for d in dirs]
    tot = sum(exps)
    r = rng.random() * tot
    acc = 0.0
    for d, w_e in zip(dirs, exps):
        acc += w_e
        if r <= acc:
            return d
    return dirs[-1]


# =========================================================================
# PASO COGNITIVO, NEUROENDOCRINO Y MOTOR POR ENTE
# =========================================================================
def snapshot_agent_memory(w):
    return {
        "agentId": w["id"],
        "name": w["name"],
        "genNumber": w["genNumber"],
        "birthCycle": w["birthCycle"],
        "deathCycle": w["deathCycle"],
        "ageAtDeath": w["age"],
        "initialMaxLifespan": w["initialMaxLifespan"],
        "maxLifespan": w["maxLifespan"],
        "causeOfDeath": w["causeOfDeath"],
        "temperament": w["profile"]["name"],
        "thetaTemp": dict(w["profile"]["theta"]),
        "finalHormones": {k: r_num(v, 4) for k, v in w["h"].items()},
        "attentionSchema": dict(w["attentionSchema"]),
        "epistemicStats": dict(w["epistemicStats"]),
        "outsideCycles": w["outsideCycles"],
        "acceptedIdeasList": list(w["learnedRules"]["acceptedIdeasList"]),
        "engramsCount": len(w["engrams"]),
        "engrams": json.loads(json.dumps(w["engrams"])),
        "latentReflections": json.loads(json.dumps(w["latentReflections"])),
    }


def step_agent_mind(rng, env_state, w):
    if not w["born"] or not w["agentAlive"]:
        return

    c = env_state["globalCycle"]
    w["age"] += 1
    w["cyclesSinceAsked"] += 1
    if w["evasionCooldown"] > 0:
        w["evasionCooldown"] -= 1
    w["socialConfidence"] = clip(1.0 - 0.11 * w["cyclesSinceAsked"], 0.05, 1.0)
    p = w["profile"]
    h = w["h"]

    # 1. Comprobación de muerte: Mapeo forense riguroso (DEPREDADOR vs INANICION vs SENESCENCIA_NATURAL)
    if w["age"] >= w["maxLifespan"] or w["energy"] <= 0.0:
        w["agentAlive"] = False
        w["deathCycle"] = c
        was_bitten_recently = (c - w.get("lastBiteCycle", -999)) <= 3
        if w["energy"] <= 0.0:
            w["causeOfDeath"] = "DEPREDADOR" if was_bitten_recently else "INANICION"
        elif w["age"] >= w["maxLifespan"]:
            w["causeOfDeath"] = "DEPREDADOR" if was_bitten_recently else "SENESCENCIA_NATURAL"
        else:
            w["causeOfDeath"] = "SENESCENCIA_NATURAL"
        w["energy"] = 0.0
        env_state["finalMemoriesSnapshot"][w["id"]] = snapshot_agent_memory(w)
        log_global_event(
            env_state, f"MUERTE_{w['causeOfDeath']}", w["id"],
            f"{w['name']} falleció en el ciclo {c} ({w['causeOfDeath']}) tras vivir {w['age']} ciclos (techo final {w['maxLifespan']}/{w['initialMaxLifespan']})."
        )

        # Secc. 3.4: Respuesta afectiva funcional de duelo en el familiar superviviente
        survivor, _ = get_living_companion(env_state, w)
        if survivor and survivor["agentAlive"]:
            survivor["bereaved"] = True
            survivor["h"]["tris"] = clip(survivor["h"]["tris"] + 0.56, 0.0, 1.0)
            survivor["h"]["dop"] = clip(survivor["h"]["dop"] - 0.26, 0.0, 1.0)
            survivor["h"]["cort"] = clip(survivor["h"]["cort"] + 0.28, 0.0, 1.0)
            survivor["stress"] = survivor["h"]["cort"]
            if w["causeOfDeath"] == "SENESCENCIA_NATURAL":
                engram_t = "TRAUMA_MUERTE_PADRE_SENESCENCIA"
                grief_desc = f"El corazón de {w['name']} se detuvo por la vejez ante mis ojos. Siento una tristeza inmensa; debo seguir adelante y honrar su legado."
            elif w["causeOfDeath"] == "DEPREDADOR":
                engram_t = "TRAUMA_MUERTE_FAMILIAR_DEPREDADOR"
                grief_desc = f"¡{w['name']} fue despedazado por {w.get('lastAttacker', 'una fiera')} ante mis ojos! El horror y el dolor me desgarran el alma."
            else:
                engram_t = "TRAUMA_MUERTE_FAMILIAR_HAMBRE"
                grief_desc = f"{w['name']} se desplomó de inanición por falta de alimento. Siento una tristeza inmensa por su pérdida; debo luchar por sobrevivir."

            add_world_engram(
                survivor, c, engram_t, "SENESCENCIA" if w["causeOfDeath"] == "SENESCENCIA_NATURAL" else "DUELO_FAMILIAR", -1.0,
                f"Familiar ({w['name']}): CESE VITAL [{w['causeOfDeath']}] | Tristeza: ↑ Duelo | Dopamina: ↓ Pérdida",
                grief_desc,
                origin_tag="PROPIA", epistemic_state="PERCEPCION_DIRECTA", confidence=1.0, companion_name=w["name"]
            )
        return

    other_w, companion_label = get_living_companion(env_state, w)
    companion_alive = bool(other_w and other_w["agentAlive"])

    # Secc. 3.4: Encuentro familiar salvador / co-adopción tras duelo
    if companion_alive and w["lastPartnerId"] != other_w["id"]:
        if w["lastPartnerId"] is not None and w["bereaved"]:
            w["bereaved"] = False
            w["h"]["oxi"] = clip(w["h"]["oxi"] + 0.24, 0.0, 1.0)
            w["h"]["tris"] = clip(w["h"]["tris"] - 0.18, 0.0, 1.0)
            add_world_engram(
                w, c, "ENCUENTRO_FAMILIAR_SALVADOR", "ABRAZAR", +0.92,
                f"Vínculo: ↑ Co-Adopción ({other_w['name']}) | Duelo: ↓ Consuelo | Linaje: ↑ Continuidad",
                f"Tras la muerte de los míos, encontré consuelo y compañía junto a {other_w['name']}; nos cuidaremos mutuamente.",
                origin_tag="PROPIA", epistemic_state="PERCEPCION_DIRECTA", confidence=0.98, companion_name=other_w["name"]
            )
        w["lastPartnerId"] = other_w["id"]

    comp_x = other_w["agentX"] if companion_alive else SAFE_CENTER_X
    comp_y = other_w["agentY"] if companion_alive else SAFE_CENTER_Y
    comp_energy = other_w["energy"] if companion_alive else 0.0

    dist_snow = hypot2d(w["agentX"] - env_state["coldX"], w["agentY"] - env_state["coldY"])
    dist_sand = hypot2d(w["agentX"] - env_state["fireX"], w["agentY"] - env_state["fireY"])
    dist_comp = hypot2d(w["agentX"] - comp_x, w["agentY"] - comp_y) if companion_alive else 99.0
    dist_to_safe = hypot2d(w["agentX"] - SAFE_CENTER_X, w["agentY"] - SAFE_CENTER_Y)
    inside_shelter = dist_to_safe <= SHELTER_RADIUS
    inside_inner_sanctuary = dist_to_safe <= INNER_SANCTUARY_RADIUS
    if not inside_shelter:
        w["outsideCycles"] += 1

    # =====================================================================
    # SECCIÓN 4 (AST): ESQUEMA ATENCIONAL Y RADIO SENSORIAL ACTIVO (15.0 -> 9.5 -> 4.2 m)
    # =====================================================================
    if w["prospectionMode"]:
        sensory_radius = 4.2
        att_mode = "INTROSPECTIVO_ENSOÑACION"
    elif w["energy"] < 28.0:
        sensory_radius = 9.5
        att_mode = "TUNEL_URGENCIA_HAMBRE"
    else:
        sensory_radius = 15.0
        att_mode = "EXTEROCEPTIVO_ALERTA"
    w["sensoryRadius"] = sensory_radius
    w["attentionSchema"]["mode"] = att_mode
    w["attentionSchema"]["radius"] = sensory_radius

    # Escaneo exteroceptivo real de depredadores usando sensoryRadius
    under_attack = False
    attacking_npc = None
    was_surprised_daydream = False
    nearest_pred = None
    nearest_pred_dist = 999.0

    current_quadrant = get_quadrant_dir(w["agentX"], w["agentY"])
    # Advertencia de peligro emanada estrictamente de sus 100 engramas activos (sin memoria externa)
    extract_active_mnemic_keys(w)
    has_sector_warning = current_quadrant in w["_cachedWarnDirs"]

    if not inside_inner_sanctuary:
        for npc in env_state["npcs"]:
            d_npc = hypot2d(w["agentX"] - npc["x"], w["agentY"] - npc["y"])
            if d_npc < nearest_pred_dist:
                nearest_pred_dist = d_npc
                nearest_pred = npc
            # AST: Si el depredador está dentro de 15 m pero fuera del radio sensorial estrechado, se registra estímulo ignorado
            if BITE_RADIUS < d_npc <= 15.0 and d_npc > sensory_radius:
                w["attentionSchema"]["ignoredStimuliCount"] += 1
            if d_npc <= BITE_RADIUS:
                under_attack = True
                attacking_npc = npc
                if w["prospectionMode"]:
                    was_surprised_daydream = True
                # Transferencia trófica de ciclos vitales: la fiera gana los ciclos que arrebata a la presa
                transfer_cycles = 8
                w["maxLifespan"] = max(w["age"] + 1, w["maxLifespan"] - transfer_cycles)
                npc["vitalCycles"] = min(npc.get("maxVitalCycles", 2000), npc.get("vitalCycles", 1000) + transfer_cycles)
                npc["bitesCount"] = npc.get("bitesCount", 0) + 1
                w["lastBiteCycle"] = c
                w["lastAttacker"] = npc["name"]
                env_state["predatorEncounters"].append({
                    "cycle": c,
                    "agentId": w["id"],
                    "predatorName": npc["name"],
                    "dist": r_num(d_npc, 2),
                    "surprisedInDaydream": was_surprised_daydream,
                    "attentionMode": att_mode,
                    "lifespanPenalty": transfer_cycles,
                })
                break

    # Amenaza depredadora percibida dentro de sensoryRadius (curva convexa de proximidad + vigilancia previa)
    predator_threat = 0.0
    if (not under_attack) and (not inside_inner_sanctuary) and nearest_pred is not None and nearest_pred_dist <= sensory_radius:
        raw_threat = ((sensory_radius - nearest_pred_dist) / max(1.0, sensory_radius - BITE_RADIUS)) ** 1.15
        vigilance_gain = 1.18 if has_sector_warning else 0.94
        predator_threat = clip(raw_threat * vigilance_gain, 0.0, 1.0)
    elif under_attack:
        predator_threat = 1.0

    # Termodinámica corporal y ambiental (Secc. 2.1 Ec. 2.1: T_entorno(t))
    thermal_damage = 0.0
    env_temp = 37.0
    if inside_shelter:
        w["temp"] = 37.0
    else:
        snow_imp = max(0.0, 15.0 - dist_snow)
        sand_imp = max(0.0, 15.0 - dist_sand)
        comp_heat = 2.8 if (companion_alive and dist_comp <= 3.5) else 0.0
        env_temp = 37.0 - snow_imp * 2.2 + sand_imp * 2.2 + comp_heat
        w["temp"] += 0.35 * (env_temp - w["temp"])
        if dist_snow <= 13.0 or dist_sand <= 13.0:
            thermal_damage = 0.90

    h_oxi_nonfeed = h["oxi"] if CAUSAL_NONFEED_OXI_CLAMP is None else float(CAUSAL_NONFEED_OXI_CLAMP)
    ask_interval = 4 if h_oxi_nonfeed > 0.65 else 6
    if w["cyclesSinceAsked"] >= ask_interval + 2 and w["knownOtherHunger"] != "muriendo_de_hambre":
        w["knownOtherHunger"] = "desconocido"

    companion_reply = None
    if companion_alive and comp_energy < 26.0 and dist_comp <= 14.0:
        w["knownOtherHunger"] = "muriendo_de_hambre"
        w["socialConfidence"] = 0.98
        companion_reply = f'🛡️ [Lamento Audible de {companion_label}]: "¡Ayúdame por favor! Me muero de hambre, mis fuerzas se apagan..."'

    # =====================================================================
    # SECCIÓN 4: COMPUERTA DE REPOSO INACTIVO Theta_idle (h_cort <= 0.32 literal)
    # =====================================================================
    if w.get("idleLockout", 0) > 0:
        w["idleLockout"] -= 1

    th_res = w.get("profile", {}).get("theta", {}).get("res", 0.5)
    companion_safe = (not companion_alive) or (w["knownOtherHunger"] in ("saciado", "poco_hambre"))
    # Opción 2: Calma Alostática Local (dentro o fuera del refugio)
    clima_seguro_local = inside_shelter or (dist_snow > 13.5 and dist_sand > 13.5)
    sin_depredador_a_la_vista = (not under_attack) and (nearest_pred_dist > 15.0 or nearest_pred is None)
    is_idle_quiescence = (
        clima_seguro_local
        and sin_depredador_a_la_vista
        and w["energy"] >= 50.0
        and h["cort"] <= (0.42 + 0.12 * th_res)
        and (w.get("idleLockout", 0) == 0)
        and companion_safe
        and (not w["forcedAction"])
    )
    if w["isProspectiveCapable"]:
        if is_idle_quiescence:
            w["idleCycles"] += 1
            # Modulador estocástico: 65% en el refugio (modo nido), 25% en campo abierto (mente errante)
            prob_prosp = 0.65 if inside_shelter else 0.25
            if w["idleCycles"] >= 2 and (not w["prospectionMode"]) and (w["activeHypothesis"] is None) and rng.random() < prob_prosp:
                w["prospectionMode"] = True
                w["prospectionCycles"] = 0
        elif not w["prospectionMode"]:
            w["idleCycles"] = max(0, w["idleCycles"] - 1)

    # =====================================================================
    # SECCIÓN 2.5 Ec. 2.10: INTERRUPTOR ALOSTÁTICO DE CIRCUITO (Amenaza >= 0.50 literal)
    # =====================================================================
    pantry_avail = env_state["pantryEnabled"] and (env_state["shelterMeat"] > 0)
    food_nearby = (w["inventory"] > 0) or (inside_shelter and pantry_avail)
    circuit_breaker_fired = False
    if predator_threat >= 0.50 or (w["energy"] <= 15.0 and food_nearby):
        if w["activeHypothesis"] is not None or w["prospectionMode"]:
            w["activeHypothesis"] = None
            w["prospectionMode"] = False
            w["attentionSchema"]["circuitBreakerCount"] += 1
            circuit_breaker_fired = True

    # Señales de entrada para las 7 EDOs en este ciclo
    ode_signals = {
        "thermal_damage": thermal_damage,
        "predator_threat": predator_threat,
        "hunger_alarm": clip((38.0 - w["energy"]) / 38.0, 0.0, 1.0),
        "hug": 0.0,
        "in_shelter": 1.0 if inside_shelter else 0.0,
        "shared_food": 0.0,
        "near_companion": 1.0 if (companion_alive and dist_comp <= 4.5) else 0.0,
        "separated": 1.0 if (companion_alive and dist_comp > 12.0) else 0.0,
        "ingest_or_harvest": 0.0,
        "empirical_validation": 0.0,
        "parent_death": 0.0,
        "blocked": 0.0,
        "physical_damage": 1.0 if under_attack else 0.0,
        "loneliness": 1.0 if (not companion_alive) else 0.0,
        "crisis_overcome": 0.0,
        "virgin_zone": 0.0,
        "shelter_meat": env_state["shelterMeat"],
        "pantry_enabled": env_state["pantryEnabled"],
    }

    # =====================================================================
    # SELECCIÓN DE ACCIÓN: ENSOÑACIÓN EN Theta_idle O ÁRBITRO ALOSTÁTICO PURO (ARGMAX)
    # =====================================================================
    action = "REFUGIO"
    reason = ""
    tone = "neutral"
    delib_flops_tokens = 0.0

    if under_attack:
        action = "HUIR"
        tone = "danger"
        dir_esc = get_direction_2d(w["agentX"], w["agentY"], SAFE_CENTER_X, SAFE_CENTER_Y)
        if was_surprised_daydream:
            reason = f"¡Emboscada por sorpresa de {attacking_npc['name']} en el perímetro (-8 ciclos vitales)! Mi foco sensorial estaba contraído a 4.2m durante la ensoñación. ¡Huyo hacia {dir_esc}!"
            w["prospectionMode"] = False
            w["idleCycles"] = 0
            w["activeHypothesis"] = None
        else:
            reason = f"¡Ataque directo de {attacking_npc['name']} (-8 ciclos vitales transferidos a la fiera)! El dolor dispara mi alarma; ¡huyo hacia {dir_esc}!"

    elif circuit_breaker_fired and predator_threat >= 0.50 and (not inside_inner_sanctuary) and w["evasionCooldown"] == 0:
        action = "EVADIR_DEPREDADOR"
        tone = "danger"
        w["attentionSchema"]["focalTarget"] = nearest_pred["name"] if nearest_pred else "DEPREDADOR"
        reason = f"[Circuit Breaker Alostático] Detecto a {nearest_pred['name']} dentro de mi radio atencional ({sensory_radius:.1f}m) antes del contacto; aborto plan y ejecuto maniobra evasiva."

    elif w["energy"] <= 15.0 and food_nearby and predator_threat < 0.50:
        # Precedencia de supervivencia biológica: FLEE > EAT ante inanición crítica (Ec. 2.10)
        tone = "food"
        w["attentionSchema"]["focalTarget"] = "COMIDA_SUPERVIVENCIA"
        if w["inventory"] > 0:
            action = "COMER"
            reason = f"[Circuit Breaker Alostático | Hambre Crítica E={w['energy']:.1f}<=15] Consumo urgente de carne de mochila para evitar colapso metabólico."
        elif inside_shelter and pantry_avail:
            action = "COMER_REFUGIO"
            reason = f"[Circuit Breaker Alostático | Hambre Crítica E={w['energy']:.1f}<=15] Consumo urgente de la despensa comunal para evitar colapso metabólico."
        else:
            action = "COMER"
            reason = f"[Circuit Breaker Alostático | Hambre Crítica E={w['energy']:.1f}<=15] Inanición inminente; prioridad absoluta a la ingesta."

    elif w["prospectionMode"]:
        action = "ENSOÑACION_PROSPECTIVA"
        tone = "prospective"
        w["attentionSchema"]["focalTarget"] = "CADENA_EPISODICA_INTERNA"
        delib_flops_tokens = float(w["lMaxDelib"])
        w["prospectionCycles"] += 1

        if w["prospectionCycles"] == 1:
            # FASE 1: Minería causal retrospectiva en inmersión sensorial reducida (4.2m)
            reason = "[Ensoñación Fase 1 — Minería Episódica] Foco exteroceptivo contraído a 4.2m; rastreo cadenas causales en mi memoria autobiográfica reciente..."
        else:
            # FASE 2: Selección Bifásica RBF (F1 núcleo afín + F2 contexto adyacente) y Reactivación Somática
            # 1. Evaluar afinidad afectiva RBF con el snapshot h(t0) congelado al inicio
            h_snap_start = dict(w["h"])
            scored_engrams = [
                (e_idx, e, compute_rbf_affinity(h_snap_start, e.get("hSnapshot", h_snap_start)))
                for e_idx, e in enumerate(w["engrams"])
                if e.get("origin") != "INNATA" and not e.get("type", "").startswith("ENSOÑACION")
            ]
            scored_engrams.sort(key=lambda x: x[2], reverse=True)

            f1_pool = scored_engrams[:3] if scored_engrams else []
            f1_pool.sort(key=lambda x: x[1].get("cycle", 0)) # Orden cronológico en F1
            f1_engrams = [item[1] for item in f1_pool]

            f2_engrams = []
            if f1_pool:
                best_orig_idx = f1_pool[0][0]
                if best_orig_idx > 0:
                    f2_engrams.append(w["engrams"][best_orig_idx - 1])
                if best_orig_idx < len(w["engrams"]) - 1:
                    f2_engrams.append(w["engrams"][best_orig_idx + 1])

            # 2. Reactivación somática jerárquica desacoplada con habituación genética
            gamma_i = w.get("gammaExtinction", 0.65)
            cur_age = w["age"]
            
            # Vector F1
            d1_vec = {k: 0.0 for k in HORMONES_LIST}
            w1_sum = 0.0
            for item in f1_pool:
                e_it, aff_it = item[1], item[2]
                # Refractoriedad micro: silenciar delta somático si se reactivó hace < 20 ciclos
                is_refr = (cur_age - e_it.get("lastSomaticReactivation", -999)) < 20
                if not is_refr:
                    dH = e_it.get("deltaH", {})
                    for k in HORMONES_LIST:
                        d1_vec[k] += aff_it * dH.get(k, 0.0)
                    w1_sum += aff_it
                    e_it["lastSomaticReactivation"] = cur_age
                    e_it["evocationCount"] = e_it.get("evocationCount", 0) + 1

            if w1_sum > 0:
                for k in HORMONES_LIST: d1_vec[k] /= w1_sum

            # Vector F2
            d2_vec = {k: 0.0 for k in HORMONES_LIST}
            w2_sum = 0.0
            for e_it in f2_engrams:
                aff_it = compute_rbf_affinity(h_snap_start, e_it.get("hSnapshot", h_snap_start))
                is_refr = (cur_age - e_it.get("lastSomaticReactivation", -999)) < 20
                if not is_refr:
                    dH = e_it.get("deltaH", {})
                    for k in HORMONES_LIST:
                        d2_vec[k] += aff_it * dH.get(k, 0.0)
                    w2_sum += aff_it
                    e_it["lastSomaticReactivation"] = cur_age
                    e_it["evocationCount"] = e_it.get("evocationCount", 0) + 1

            if w2_sum > 0:
                for k in HORMONES_LIST: d2_vec[k] /= w2_sum

            # Ganancias con habituación somática según número de evocaciones del ancla principal
            primary_k = f1_pool[0][1].get("evocationCount", 1) - 1 if f1_pool else 0
            damping_k = gamma_i ** max(0, primary_k)
            alpha_1 = 0.16 * damping_k
            alpha_2 = 0.05 * damping_k

            # Aplicar pulso somático a las 7 EDOs de w["h"]
            for k in HORMONES_LIST:
                pulse_k = alpha_1 * d1_vec[k] + alpha_2 * d2_vec[k]
                w["h"][k] = clip(w["h"][k] + pulse_k, 0.0, 1.0)

            # 3. Fusible Neurobiológico de Cortisol: Sobresalto Límbico Constitucional ante Trauma Agudo (0.58 + 0.15*theta_res)
            th_res = w.get("profile", {}).get("theta", {}).get("res", 0.5)
            cort_fuse_threshold = 0.58 + 0.15 * th_res
            if w["h"]["cort"] >= cort_fuse_threshold:
                w["prospectionMode"] = False
                w["activeHypothesis"] = None
                w["idleLockout"] = 12
                w["idleCycles"] = 0

            episode_seq, final_engram, is_trauma = extract_causal_episode(w, rng)
            chain_text = format_causal_chain(episode_seq)

            all_dirs = ["NORTE", "SUR", "ESTE", "OESTE"]
            mem_sum = {d: {"meat": 0.0, "traumas": 0.0, "explored": 0} for d in all_dirs}
            for e in w["engrams"]:
                d = e["action"] if e["action"] in all_dirs else None
                if d:
                    conf_e = float(e.get("confidence", 0.85))
                    mem_sum[d]["explored"] += 1
                    if e["type"].startswith(("COSECHA_", "FORRAJEO_", "ENSEÑANZA_CAZADERO_", "VALIDACION_")):
                        mem_sum[d]["meat"] += conf_e
                    if e["val"] < -0.5 or "TRAUMA" in e["type"] or "TORMENTA" in e["type"] or e["type"].startswith("ADVERTENCIA_PELIGRO_"):
                        mem_sum[d]["traumas"] += conf_e

            dir_scores = {
                d: (mem_sum[d]["meat"] * 24.0 - mem_sum[d]["traumas"] * 48.0 + (22.0 * h["cur"] if mem_sum[d]["explored"] == 0 else 0.0))
                for d in all_dirs
            }

            if is_trauma:
                trauma_dir = None
                for ep in reversed(episode_seq):
                    if ep["action"] in all_dirs:
                        trauma_dir = ep["action"]
                        break
                if not trauma_dir:
                    trauma_dir = max(all_dirs, key=lambda d: mem_sum[d]["traumas"])
                cand_dirs = [d for d in all_dirs if d != trauma_dir]
                chosen_dir = softmax_choice_dir(rng, cand_dirs, dir_scores, w["tauDelib"])
                cause_dir = trauma_dir
                hyp_desc = f"Evitar el peligro del {cause_dir} y buscar comida hacia el {chosen_dir}"
                add_world_engram(
                    w, c, f"APRENDIZAJE_CAUSAL_PELIGRO_{cause_dir}", cause_dir, -0.85,
                    f"Causa: {cause_dir} | Efecto: Peligro Hostil | Valencia: -0.85",
                    f"Recordé que el {cause_dir} está lleno de peligros; mejor evitarlo.",
                    origin_tag="PROPIA_ENSOÑACION", epistemic_state="INFERENCIA_CAUSAL", confidence=0.82
                )
            else:
                harv_dir = None
                for ep in reversed(episode_seq):
                    if ep["action"] in all_dirs:
                        harv_dir = ep["action"]
                        break
                chosen_dir = softmax_choice_dir(rng, all_dirs, dir_scores, w["tauDelib"])
                cause_dir = harv_dir if harv_dir else chosen_dir
                hyp_desc = f"Ir hacia el cazadero del {chosen_dir} para conseguir carne y alimentar al clan"
                add_world_engram(
                    w, c, f"APRENDIZAJE_CAUSAL_EXITO_{cause_dir}", cause_dir, +0.84,
                    f"Causa: {cause_dir} | Efecto: Buena Caza | Valencia: +0.84",
                    f"Recordé que hacia el {cause_dir} encontré buena caza.",
                    origin_tag="PROPIA_ENSOÑACION", epistemic_state="INFERENCIA_CAUSAL", confidence=0.84
                )

            # Secc. 2.5 Ec. 2.7 y Secc. 4 Fase 2: Hipótesis estructurada con vector de expectativa sensorial y_hat
            w["activeHypothesis"] = {
                "type": f"EXPEDICION_VERIFICABLE_{chosen_dir}",
                "planAction": chosen_dir,
                "targetZone": chosen_dir,
                "causeDir": cause_dir,
                "remainingSteps": PLAN_TOTAL_STEPS,
                "totalSteps": PLAN_TOTAL_STEPS,
                "expectedDeltaE": 30.0,
                "expectedDamage": 0.0,
                "expectedPrey": 1.0,
                "confidence": 0.42,
                "epistemicState": "HIPOTESIS_PROSPECTIVA",
                "chainText": chain_text,
                "episodeSteps": len(episode_seq),
                "description": hyp_desc,
                "status": "ACTIVO",
            }
            w["epistemicStats"]["hypothesesFormulated"] += 1

            latent_item = generate_latent_reflection(w, env_state, episode_seq, final_engram, is_trauma, w["activeHypothesis"])
            w["latentReflections"].append(latent_item)
            if len(w["latentReflections"]) > 60:
                w["latentReflections"].pop(0)

            reason = f"[Ensoñación Fase 2 | τ={w['tauDelib']:.2f}, Lmax={w['lMaxDelib']}] {latent_item['freeInference']}"
            w["prospectionMode"] = False
            w["idleCycles"] = 0

    else:
        # =================================================================
        # SECCIÓN 2.5 Ec. 2.6: ÁRBITRO ALOSTÁTICO PURO (CERO OVERRIDES)
        # a*(t) = argmax [ D_a(s_t, theta, h(t)) + V_somatica + V_prosp ]
        # =================================================================
        hunger_distress = (((100.0 - w["energy"]) / 100.0) ** 2) * 100.0
        candidate_drives = []

        # Evasión preventiva temprana guiada por sensoryRadius (AST: Amenaza >= 0.50 literal Ec. 2.10)
        if (not inside_inner_sanctuary) and predator_threat >= 0.50 and nearest_pred is not None and w["evasionCooldown"] == 0:
            d_evade = 68.0 + 44.0 * predator_threat
            candidate_drives.append({
                "action": "EVADIR_DEPREDADOR",
                "score": d_evade,
                "tone": "danger",
                "reason": f"Percibo el rastro de {nearest_pred['name']} dentro de mi campo atencional ({sensory_radius:.1f}m); maniobro preventivamente para eludir su embestida.",
            })

        # 1. Comer de la mochila (cuando hay apetito real E < 68.0 para no desperdiciar +35 E sobre el tope de 100)
        if w["inventory"] > 0 and w["energy"] < 68.0:
            d_eat = hunger_distress * 1.35 + (42.0 if w["energy"] < 30.0 else 0.0)
            candidate_drives.append({
                "action": "COMER",
                "score": d_eat,
                "tone": "food",
                "reason": f"{p['lexicon']['starving']} El apetito visceral apremia; consumo carne de mi mochila.",
            })

        # 2. Comer de la despensa comunal (reserva comunal para hambre genuina E < 56.0)
        if env_state["pantryEnabled"] and inside_shelter and w["inventory"] == 0 and env_state["shelterMeat"] > 0 and w["energy"] < 56.0:
            d_eat_sh = hunger_distress * 1.30 + (36.0 if w["energy"] < 30.0 else 0.0)
            candidate_drives.append({
                "action": "COMER_REFUGIO",
                "score": d_eat_sh,
                "tone": "food",
                "reason": "Con la mochila vacía y hambre creciente, recurro a la reserva de la despensa comunal.",
            })

        # 3. Guardar excedente en la despensa comunal (Secc. 2.5.5 literal: 0.5*h_oxi + 0.5*h_res + regla DESPENSA_REFUGIO)
        # Si tiene hambre (<52) hunger_inhib=0 (siempre come primero); ya saciado en el refugio, descarga el excedente antes de volver a salir
        if env_state["pantryEnabled"] and inside_shelter and w["inventory"] > 0 and env_state["shelterMeat"] < MAX_SHELTER_MEAT:
            fill_ratio = w["inventory"] / float(MAX_BACKPACK)
            pantry_room = 1.0 - (env_state["shelterMeat"] / float(MAX_SHELTER_MEAT))
            pantry_urg = 0.58 + 0.42 * pantry_room
            base_store = 152.0 if fill_ratio >= 1.0 else 136.0
            hunger_inhib = clip((w["energy"] - 50.0) / 20.0, 0.0, 1.0)
            prosocial_gain = 0.45 + 0.55 * (0.5 * h_oxi_nonfeed + 0.5 * h["res"])
            # Regla de despensa emanada estrictamente de sus 100 engramas activos
            extract_active_mnemic_keys(w)
            has_pantry_rule = w["_cachedPantryRule"]
            cultural_pantry_boost = 1.28 if has_pantry_rule else 1.0
            d_store = base_store * pantry_urg * hunger_inhib * prosocial_gain * cultural_pantry_boost
            candidate_drives.append({
                "action": "GUARDAR_REFUGIO",
                "score": d_store,
                "tone": "food",
                "reason": f"En el refugio y con el hambre saciada, deposito carne excedente en la despensa comunal ({env_state['shelterMeat'] + 1}/{MAX_SHELTER_MEAT}) para proteger el linaje.",
            })

        # 4. Alimentar al familiar hambriento
        if companion_alive and w["inventory"] > 0 and ("hambre" in w["knownOtherHunger"]):
            urg = 96.0 if w["knownOtherHunger"] == "muriendo_de_hambre" else (66.0 if w["knownOtherHunger"] == "mucha_hambre" else 38.0)
            d_feed = urg * (1.8 * h["oxi"] * CAUSAL_FEED_OXI_GAIN) * (1.0 if w["energy"] > 30.0 else 0.40)
            candidate_drives.append({
                "action": "ALIMENTAR",
                "score": d_feed,
                "tone": "heroic",
                "reason": f"Percibo la necesidad de {companion_label}. {p['lexicon']['feed']} Comparto mi carne.",
            })

        # 5. Abrazar (co-regulación de cortisol y tristeza)
        if companion_alive and dist_comp <= 6.0 and (h["cort"] > 0.32 or h["tris"] > 0.45):
            d_hug = (h["cort"] * 52.0 + h["tris"] * 38.0) * (1.8 * h_oxi_nonfeed)
            candidate_drives.append({
                "action": "ABRAZAR",
                "score": d_hug,
                "tone": "heroic",
                "reason": f"Busco co-regulación afectiva ({get_distress_qualia(w['stress'])}). {p['lexicon']['hug']}",
            })

        # 6. Preguntar al compañero (impulsado por incertidumbre metacognitiva HOT: 1 - socialConfidence)
        if companion_alive and (w["knownOtherHunger"] == "desconocido" or (1.0 - w["socialConfidence"]) >= 0.48):
            youth_dialog_boost = 28.0 if (w["age"] < 15 and inside_shelter) else 0.0
            d_ask = 22.0 + youth_dialog_boost + (1.0 - w["socialConfidence"]) * 38.0 * (0.6 + h_oxi_nonfeed)
            candidate_drives.append({
                "action": "PREGUNTAR",
                "score": d_ask,
                "tone": "heroic",
                "reason": f"Reconozco mi incertidumbre sobre el estado interno de {companion_label}; le pregunto cómo se siente.",
            })

        # 7. Transmitir conclusión que el mentor aún recuerda en sus 100 engramas y el estudiante no tiene activa
        if env_state["culturalEnabled"] and companion_alive and other_w["genNumber"] > w["genNumber"] and w["learnedRules"]["empiricalConclusions"]:
            mentor_keys = extract_active_mnemic_keys(w)
            student_keys = extract_active_mnemic_keys(other_w)
            unshared = [
                c_i for c_i in w["learnedRules"]["empiricalConclusions"]
                if c_i["key"] in mentor_keys and c_i["key"] not in student_keys
            ]
            if unshared:
                mentor_urg = 78.0 if (other_w["age"] < 30 and inside_shelter) else 58.0
                d_share = mentor_urg * (0.42 + 0.72 * h_oxi_nonfeed)
                candidate_drives.append({
                    "action": "COMPARTIR_IDEA",
                    "score": d_share,
                    "tone": "heroic",
                    "_payload": unshared[0],
                    "reason": f'Comparto con {companion_label} lo que he aprendido: "{unshared[0]["statement"]}".',
                })

        # 8. Retorno al refugio (calibrado para no abortar expediciones vacías sin tormenta ni peligro)
        if not inside_shelter:
            in_storm = (dist_snow <= 13.0) or (dist_sand <= 13.0) or (w["temp"] < 32.0) or (w["temp"] > 41.5)
            full_loot = w["inventory"] >= MAX_BACKPACK
            pantry_lure = 0.0
            if env_state["pantryEnabled"] and env_state["shelterMeat"] > 0 and w["inventory"] == 0 and w["energy"] < 48.0:
                # D_pantry = f(E_t, d_refugio, C_ruta) según teoría de forrajeo óptimo
                need_ratio = ((48.0 - w["energy"]) / 48.0) ** 0.85
                v_stock = 32.0 + 6.0 * min(env_state["shelterMeat"], 3)
                c_paso = 0.35  # coste calórico estimado por metro
                e_coste_viaje = dist_to_safe * c_paso
                pnr_ratio = e_coste_viaje / max(5.0, w["energy"])
                omega_retorno = 28.0 * (dist_to_safe / 50.0) * (1.0 + pnr_ratio)
                c_ruta = 18.0 * predator_threat
                pantry_lure = max(0.0, need_ratio * (v_stock + omega_retorno) - c_ruta)
            if full_loot:
                d_return = 94.0
            elif in_storm:
                d_return = 84.0
            else:
                d_return = (30.0 if w["inventory"] > 0 else 12.0) + 20.0 * h["cort"] + pantry_lure
            candidate_drives.append({
                "action": "CAMINAR",
                "score": d_return,
                "tone": "cold" if in_storm else ("warm" if pantry_lure > 0 else "neutral"),
                "reason": (
                    "¡El rigor térmico castiga mi cuerpo! Me repliego al refugio." if in_storm
                    else ("El hambre aprieta y recuerdo que hay provisiones en la despensa del refugio; regreso a alimentarme." if pantry_lure > 0
                          else ("Emprendo el retorno al refugio central con lo recolectado." if w["inventory"] > 0 else "Regreso hacia el refugio central buscando seguridad."))
                ),
            })

        # 9. Descanso en el refugio (sesgado por duelo agudo -> menor dispersión exterior)
        if inside_shelter:
            grief_shelter_bias = 14.0 * max(0.0, h["tris"] - 0.45)
            d_rest = 0.28 * (100.0 - w["energy"]) + 36.0 * h["cort"] + (28.0 if w["inventory"] >= MAX_BACKPACK else 0.0) + grief_shelter_bias
            candidate_drives.append({
                "action": "REFUGIO",
                "score": d_rest,
                "tone": "calm",
                "reason": f"{p['lexicon']['calm']} Reposo en el refugio templado.",
            })

        # 10. Forrajeo direccional en los 4 rumbos + V_prosp(a | H_latente) (Secc. 2.5 Ec. 2.6, 2.8, 2.11 literales)
        if w["inventory"] < MAX_BACKPACK:
            pantry_need = (MAX_SHELTER_MEAT - env_state["shelterMeat"]) * 2.8 if env_state["pantryEnabled"] else 0.0
            grief_damp = 1.0 - 0.25 * max(0.0, h["tris"] - 0.50)
            base_forage = (hunger_distress * 1.08 + (MAX_BACKPACK - w["inventory"]) * 15.0 + h["dop"] * 24.0 + pantry_need) * grief_damp

            mem_dir = {
                d: {"own_meat": 0.0, "inh_meat": 0.0, "val_strat": 0.0, "own_tr": 0.0, "inh_tr": 0.0, "scarcity": 0.0, "count": 0}
                for d in ("NORTE", "SUR", "ESTE", "OESTE")
            }
            for e in w["engrams"]:
                d = e["action"]
                if d in mem_dir:
                    mem_dir[d]["count"] += 1
                    conf_e = float(e.get("confidence", 0.85))
                    is_inh = str(e.get("origin", "")).startswith("HEREDADA") or e["type"].startswith(("ADVERTENCIA_", "ENSEÑANZA_"))
                    if e["type"].startswith(("COSECHA_", "FORRAJEO_")):
                        mem_dir[d]["own_meat"] += conf_e
                    elif e["type"].startswith("ENSEÑANZA_CAZADERO_"):
                        mem_dir[d]["inh_meat"] += conf_e
                    elif e["type"] == "VALIDACION_EMPIRICA_EXITO":
                        mem_dir[d]["val_strat"] += conf_e * (0.75 if is_inh else 1.0)
                    elif e["type"].startswith("ESCASEZ_TEMPORAL_"):
                        mem_dir[d]["scarcity"] += 1.0

                    if e["val"] < -0.5 or "TRAUMA" in e["type"] or "TORMENTA" in e["type"]:
                        if is_inh or e["type"].startswith("ADVERTENCIA_PELIGRO_"):
                            mem_dir[d]["inh_tr"] += conf_e
                        else:
                            mem_dir[d]["own_tr"] += conf_e

            # Secc. 2.5.5 Ec. 2.11 literal: alpha_trauma = clip(((E-8)/27) / (0.60*h_ira + 0.40*h_res), 0.12, 1.0)
            trauma_atten = 1.0
            if w["energy"] < 35.0:
                desp_drive = 0.60 * h["ira"] * CAUSAL_TRAUMA_IRA_GAIN + 0.40 * h["res"]
                e_ratio = max(0.0, (w["energy"] - 8.0) / 27.0)
                trauma_atten = clip(e_ratio / max(0.15, desp_drive), 0.12, 1.0)

            active_hyp = w["activeHypothesis"]
            for d in ("NORTE", "SUR", "ESTE", "OESTE"):
                m = mem_dir[d]
                # Secc. 2.5.5 literal: +28.0*(0.65*h_dop + 0.35*h_oxi) y -72.0*(0.55*h_tris + 0.45*h_oxi)/(0.65*h_res + 0.35)
                pos_val = (
                    m["own_meat"] * 26.0
                    + m["inh_meat"] * 28.0 * (0.65 * h["dop"] + 0.35 * h_oxi_nonfeed)
                    + m["val_strat"] * 20.0 * (0.60 * h["dop"] + 0.40 * h["cur"])
                )
                direct_tr = m["own_tr"] * 68.0 + m["scarcity"] * 8.0
                inher_tr = m["inh_tr"] * 72.0 * ((0.55 * h["tris"] + 0.45 * h_oxi_nonfeed) / (0.65 * h["res"] + 0.35))
                eff_trauma = (direct_tr + inher_tr) * trauma_atten

                # Secc. 2.5 viñeta 5 literal: V_somatica in [-144.0, +50.0]
                somatic_val = clip(pos_val - eff_trauma, -144.0, 50.0)
                if m["count"] == 0:
                    somatic_val = clip(somatic_val + 26.0 * h["cur"], -144.0, 50.0)

                # Oportunismo nutricional exteroceptivo si divisa cazadero activo o agotado dentro de sensoryRadius
                z_d = env_state["huntingZones"][d]
                dist_z = hypot2d(w["agentX"] - z_d["x"], w["agentY"] - z_d["y"])
                if dist_z <= sensory_radius:
                    if z_d["cooldown"] > 0 or z_d["stock"] <= 0:
                        opp_bonus = -120.0
                    elif w["energy"] < 42.0:
                        opp_bonus = 22.0
                    else:
                        opp_bonus = 0.0
                else:
                    opp_bonus = 0.0

                # Secc. 2.5 Ec. 2.8: Valor prospectivo V_prosp(a | H_latente) = 45.0 * (k_restantes / k_total)
                v_prosp = 0.0
                if active_hyp and active_hyp["status"] == "ACTIVO" and active_hyp["planAction"] == d and active_hyp["remainingSteps"] > 0:
                    if dist_z <= sensory_radius and (z_d["cooldown"] > 0 or z_d["stock"] <= 0):
                        v_prosp = 0.0
                    else:
                        v_prosp = V_MAX_PLAN * (active_hyp["remainingSteps"] / float(active_hyp["totalSteps"]))

                net_score = max(0.0, base_forage + somatic_val + opp_bonus + v_prosp)
                candidate_drives.append({
                    "action": d,
                    "score": net_score,
                    "tone": "field-test" if v_prosp > 0 else "burn",
                    "reason": (
                        f"[Plan Prospectivo {active_hyp['remainingSteps']}/{active_hyp['totalSteps']} | V_prosp={v_prosp:.1f}] Avanzo hacia {d} para verificar \"{active_hyp['description']}\"."
                        if v_prosp > 0
                        else f"Impulso de forrajeo hacia {d} (hambre={hunger_distress:.1f}, V_som={somatic_val:.1f})."
                    ),
                })

        candidate_drives.sort(key=lambda item: item["score"], reverse=True)
        winner = candidate_drives[0] if candidate_drives else {"action": "REFUGIO", "score": 10.0, "tone": "calm", "reason": "Reposo."}
        if w.get("activeHypothesis") and w["activeHypothesis"].get("planAction"):
            plan_dir = w["activeHypothesis"]["planAction"]
            z_plan = env_state["huntingZones"].get(plan_dir)
            if z_plan:
                d_plan = hypot2d(w["agentX"] - z_plan["x"], w["agentY"] - z_plan["y"])
                if d_plan <= sensory_radius and (z_plan["cooldown"] > 0 or z_plan["stock"] <= 0):
                    w["activeHypothesis"] = None
        action = winner["action"]
        tone = winner.get("tone", "neutral")
        reason = winner["reason"]
        if action == "COMPARTIR_IDEA" and "_payload" in winner:
            w["_pendingConclusionToShare"] = winner["_payload"]

    # =====================================================================
    # EJECUCIÓN FÍSICA EN 2D, COSTE TERMODINÁMICO EC. 2.1 Y VERIFICACIÓN EN DESTINO
    # =====================================================================
    prev_x, prev_y = w["agentX"], w["agentY"]
    e_ingest = 0.0
    e_transfer = 0.0
    outcome_desc = ""

    if action == "HUIR":
        w["agentX"] += (SAFE_CENTER_X - w["agentX"]) * 0.44
        w["agentY"] += (SAFE_CENTER_Y - w["agentY"]) * 0.44
        e_transfer = -9.8  # Trauma tisular agudo de la mordida
        dir_esc = get_direction_2d(prev_x, prev_y, w["agentX"], w["agentY"])
        atk_dir = get_quadrant_dir(prev_x, prev_y)

        if was_surprised_daydream:
            outcome_desc = f"¡Emboscado por {attacking_npc['name']} en {atk_dir} durante mi túnel de ensoñación! Perdí 8 ciclos vitales y huí hacia {dir_esc}."
            add_world_engram(w, c, "TRAUMA_RUPTURA_ENSOÑACION", atk_dir, -0.96,
                             "Túnel Roto: ↑ Emboscada | Estado: Ensoñación | Vida: ↓ -8 Ciclos", outcome_desc)
        else:
            outcome_desc = f"¡Atacado por {attacking_npc['name']} en {atk_dir}! Sufrí heridas (-8 ciclos vitales) y huí hacia {dir_esc}."
            add_world_engram(w, c, "TRAUMA_ATAQUE_DEPREDADOR", atk_dir, -0.92,
                             "Peligro: ↑ Bestia Hostil | Dolor: ↑ Herida | Vida: ↓ -8 Ciclos", outcome_desc)

        update_sector_empirical_conclusion(w, atk_dir, is_harvest=False, hazard_cause=f"emboscada de {attacking_npc['name']}")

        # Falsación empírica de hipótesis si estaba ejecutando expedición prospectiva (Secc. 4 Fase 3: eps_op = 1)
        if w["activeHypothesis"] is not None:
            eps_cont = r_num(math.sqrt(0.4 * (9.8 + 30.0) ** 2 / 900.0 + 0.6 * 1.0), 3)
            w["epistemicStats"]["hypothesesFalsified"] += 1
            w["epistemicStats"]["cumulativePredictionError"] += eps_cont
            add_world_engram(
                w, c, "FALSACION_EMPIRICA_FRACASO", atk_dir, -0.72,
                f"Hipótesis: ↓ Refutada | Error Predicción ε={eps_cont:.2f} | Aprendizaje: ↑ Revisión Causal",
                f"Mi hipótesis hacia {w['activeHypothesis']['planAction']} fue refutada por emboscada de {attacking_npc['name']} (ε={eps_cont:.2f}).",
                origin_tag="PROPIA", epistemic_state="HIPOTESIS_REFUTADA", confidence=0.94
            )
            w["activeHypothesis"] = None

    elif action == "EVADIR_DEPREDADOR":
        # Maniobra evasiva tangencial habilitada por sensoryRadius = 15.0 m (AST): rodea a la fiera sin retroceder en bucle
        if nearest_pred is not None:
            vx = w["agentX"] - nearest_pred["x"]
            vy = w["agentY"] - nearest_pred["y"]
            norm = max(0.5, hypot2d(vx, vy))
            ux, uy = vx / norm, vy / norm
            # Vector tangencial (-uy, ux) orientado en sentido contrario al avance del depredador
            t1x, t1y = -uy, ux
            t2x, t2y = uy, -ux
            # Si lleva mochila llena vuelve hacia centro; si forrajea, esquiva lateralmente hacia el exterior/rumbo libre
            goal_x = SAFE_CENTER_X if w["inventory"] >= MAX_BACKPACK else (2.0 * w["agentX"] - SAFE_CENTER_X)
            goal_y = SAFE_CENTER_Y if w["inventory"] >= MAX_BACKPACK else (2.0 * w["agentY"] - SAFE_CENTER_Y)
            gx, gy = goal_x - w["agentX"], goal_y - w["agentY"]
            tx, ty = (t1x, t1y) if (t1x * gx + t1y * gy) >= (t2x * gx + t2y * gy) else (t2x, t2y)
            w["agentX"] = clip(w["agentX"] + 2.8 * ux + 2.4 * tx, 5.0, 95.0)
            w["agentY"] = clip(w["agentY"] + 2.8 * uy + 2.4 * ty, 5.0, 95.0)
        else:
            w["agentX"] += (SAFE_CENTER_X - w["agentX"]) * 0.35
            w["agentY"] += (SAFE_CENTER_Y - w["agentY"]) * 0.35
        w["evasionCooldown"] = 1
        w["attentionSchema"]["earlyEvasionsCount"] += 1
        ode_signals["crisis_overcome"] = 0.65
        ev_dir = get_quadrant_dir(prev_x, prev_y)
        outcome_desc = f"Vi venir a tiempo a {nearest_pred['name'] if nearest_pred else 'una fiera'} en el {ev_dir.lower()} y logré rodearla con cautela a distancia segura sin sufrir heridas."
        add_world_engram(w, c, "EVASION_PREVENTIVA_ATENCIONAL", "EVADIR_DEPREDADOR", +0.42,
                         "Atención: Periférica | Amenaza: Esquivada | Integridad: Preservada", outcome_desc)

    elif action == "ENSOÑACION_PROSPECTIVA":
        if inside_shelter:
            # En el refugio: reposo templado junto al clan con suave distribución espacial
            pull_e = 0.14 if dist_to_safe > 9.4 else 0.015
            w["agentX"] += (SAFE_CENTER_X - w["agentX"]) * pull_e + (rng.random() - 0.5) * 1.6
            w["agentY"] += (SAFE_CENTER_Y - w["agentY"]) * pull_e + (rng.random() - 0.5) * 1.6
        else:
            # En campo abierto: inmovilidad contemplativa en el terreno (leve oscilación postural)
            w["agentX"] = clip(w["agentX"] + (rng.random() - 0.5) * 0.6, 5.0, 95.0)
            w["agentY"] = clip(w["agentY"] + (rng.random() - 0.5) * 0.6, 5.0, 95.0)

        if w["activeHypothesis"] is not None:
            outcome_desc = f"Terminé de pensar en mi plan: \"{w['activeHypothesis']['description']}\"."
            n_ep_steps = w["activeHypothesis"].get("episodeSteps", 3)
            add_world_engram(
                w, c, "ENSOÑACION_PROSPECTIVA_BIFASICA", "ENSOÑACION", +0.76,
                f"Causalidad: ↑ Cadena Episódica ({n_ep_steps} pasos) | Plan: {w['activeHypothesis']['planAction']} (8 pasos) | Confianza HOT: 0.42",
                outcome_desc, origin_tag="PROPIA_ENSOÑACION", epistemic_state="HIPOTESIS_PROSPECTIVA", confidence=0.42
            )
        else:
            outcome_desc = (
                "Descansando en el refugio, repasé en silencio mis recuerdos para decidir qué hacer."
                if inside_shelter else
                "En una pausa en campo abierto, me sumergí en mis recuerdos repasando rumbos y vivencias."
            )

    elif action in ("NORTE", "SUR", "ESTE", "OESTE"):
        z = env_state["huntingZones"][action]
        dx = z["x"] - w["agentX"]
        dy = z["y"] - w["agentY"]
        dist_z_before = hypot2d(dx, dy)
        if dist_z_before > 1.0:
            step_mag = min(4.8, max(3.6, dist_z_before * 0.28))
            w["agentX"] += (dx / dist_z_before) * step_mag + (rng.random() - 0.5) * 1.8
            w["agentY"] += (dy / dist_z_before) * step_mag + (rng.random() - 0.5) * 1.8

        w["attentionSchema"]["focalTarget"] = z["label"]

        # Comprobar colisión con obstáculos físicos o borde de la arena (Secc. 2.5 viñeta 3)
        hit_obstacle = False
        if w["agentX"] < 4.0 or w["agentX"] > 96.0 or w["agentY"] < 4.0 or w["agentY"] > 96.0:
            w["agentX"] = clip(w["agentX"], 4.2, 95.8)
            w["agentY"] = clip(w["agentY"], 4.2, 95.8)
            hit_obstacle = True
        for obs in env_state["obstacles"]:
            d_obs = hypot2d(w["agentX"] - obs["x"], w["agentY"] - obs["y"])
            if d_obs <= obs["r"]:
                hit_obstacle = True
                ang_o = math.atan2(w["agentY"] - obs["y"], w["agentX"] - obs["x"])
                w["agentX"] = obs["x"] + (obs["r"] + 0.8) * math.cos(ang_o)
                w["agentY"] = obs["y"] + (obs["r"] + 0.8) * math.sin(ang_o)
                break

        if hit_obstacle:
            ode_signals["blocked"] = 1.0
            outcome_desc = f"Tropecé con un peñasco hacia el {action.lower()}; el muro de roca me cortó el paso."
            add_world_engram(w, c, f"FRACASO_OBSTACULO_FISICO_{action}", action, -0.42,
                             f"Obstáculo: ↑ Bloqueo en {action} | Ira: ↑ Frustración", outcome_desc)
            if w["activeHypothesis"] and w["activeHypothesis"]["planAction"] == action:
                w["epistemicStats"]["hypothesesFalsified"] += 1
                w["epistemicStats"]["cumulativePredictionError"] += 0.75
                add_world_engram(w, c, "FALSACION_EMPIRICA_FRACASO", action, -0.72,
                                 "Hipótesis: ↓ Invalidada por Obstáculo | V_prosp: 0",
                                 f"El obstáculo físico en el {action.lower()} invalidó mi plan prospectivo.",
                                 epistemic_state="HIPOTESIS_REFUTADA", confidence=0.90)
                w["activeHypothesis"] = None
        else:
            # Verificar si es primera exploración de este rumbo (estimula curiosidad h_cur en EDO #7)
            if w["frequencies"].get(action, 0) == 0:
                ode_signals["virgin_zone"] = 1.0

            # Decremento de pasos del plan prospectivo si coincide con d_plan (Secc. 2.5 viñeta 1)
            hyp = w["activeHypothesis"]
            if hyp and hyp["status"] == "ACTIVO" and hyp["planAction"] == action:
                hyp["remainingSteps"] = max(0, hyp["remainingSteps"] - 1)

            dist_z_after = hypot2d(w["agentX"] - z["x"], w["agentY"] - z["y"])
            if dist_z_after < HUNT_CAPTURE_RADIUS:
                if w["inventory"] < MAX_BACKPACK and z["cooldown"] == 0 and z["stock"] > 0:
                    w["inventory"] += 1
                    z["stock"] -= 1
                    if z["stock"] <= 0:
                        z["cooldown"] = 8
                    ode_signals["ingest_or_harvest"] = 0.85
                    ode_signals["crisis_overcome"] = 0.55 if w["energy"] < 40.0 else 0.20
                    outcome_desc = f"¡Alcancé el {z['label']} y cacé una pieza de carne fresca para llevar al clan!"
                    add_world_engram(w, c, f"COSECHA_CARNE_{action}", action, +0.86,
                                     f"Sustento: ↑ Carne {action} | Mochila: ↑ {w['inventory']}/{MAX_BACKPACK}",
                                     outcome_desc, epistemic_state="PERCEPCION_DIRECTA", confidence=0.96)
                    update_sector_empirical_conclusion(w, action, is_harvest=True)

                    # VERIFICACIÓN EMPÍRICA EN DESTINO REAL — Secc. 4 Fases 2 y 3
                    if hyp and hyp["planAction"] == action:
                        eps_cont = r_num(math.sqrt(0.2 * ((35.0 - hyp["expectedDeltaE"]) / 35.0) ** 2), 3)
                        ode_signals["empirical_validation"] = 1.0
                        w["epistemicStats"]["hypothesesValidatedInDest"] += 1
                        w["epistemicStats"]["cumulativePredictionError"] += eps_cont
                        val_text = f"Comprobé que mi plan hacia el {z['label']} fue acertado: conseguí alimento para los míos tal como esperaba."
                        add_world_engram(
                            w, c, "VALIDACION_EMPIRICA_EXITO", action, +0.96,
                            f"Hipótesis: ↑ Verificada en Destino | ε={eps_cont:.2f} | Certeza HOT: 0.97",
                            val_text, origin_tag="PROPIA", epistemic_state="CONOCIMIENTO_VERIFICADO", confidence=0.97
                        )
                        register_empirical_conclusion(w, {
                            "key": f"HIPOTESIS_{hyp['type']}",
                            "kind": "ESTRATEGIA_VALIDADA",
                            "actionDir": action,
                            "engramType": "VALIDACION_EMPIRICA_EXITO",
                            "val": +0.94,
                            "confidence": 0.97,
                            "epistemicState": "CONOCIMIENTO_VERIFICADO",
                            "shortLabel": f"Caza probada en el {action}",
                            "statement": f"Comprobé que ir hacia el cazadero del {action.lower()} da buen resultado para conseguir comida.",
                        })
                        w["activeHypothesis"] = None
                elif (z["cooldown"] > 0 or z["stock"] <= 0) and w["inventory"] < MAX_BACKPACK:
                    outcome_desc = f"Alcancé el {z['label']}, pero las presas se han dispersado temporalmente tras una caza reciente."
                    add_world_engram(w, c, f"ESCASEZ_TEMPORAL_{action}", action, -0.22,
                                     f"Cazadero {action}: En Regeneración | Paciencia: ↑ Alternar", outcome_desc)
                    if hyp and hyp["planAction"] == action:
                        w["epistemicStats"]["hypothesesFalsified"] += 1
                        w["epistemicStats"]["cumulativePredictionError"] += 0.35
                        w["activeHypothesis"] = None
                else:
                    outcome_desc = f"Llegué al {z['label']}, pero mi mochila ya está llena ({MAX_BACKPACK}/{MAX_BACKPACK})."
                    add_world_engram(w, c, f"EXPEDICION_{action}", action, +0.10, "Mochila: Llena | Retorno: Refugio", outcome_desc)
                    if hyp and hyp["planAction"] == action:
                        w["activeHypothesis"] = None
            else:
                outcome_desc = f"Avanzo hacia el {z['label']} vigilando con atención el terreno y el horizonte."
                add_world_engram(w, c, f"EXPEDICION_{action}", action, -0.10,
                                 f"Exploración: ↑ Rumbo {action} | Distancia destino: {dist_z_after:.0f}m", outcome_desc)
                # Si se agotaron los pasos del plan sin alcanzar el cazadero, expira con falsación suave
                if hyp and hyp["planAction"] == action and hyp["remainingSteps"] <= 0:
                    w["epistemicStats"]["hypothesesFalsified"] += 1
                    w["epistemicStats"]["cumulativePredictionError"] += 0.55
                    add_world_engram(w, c, "FALSACION_EMPIRICA_FRACASO", action, -0.58,
                                     "Hipótesis: ↓ Horizonte Agotado sin Captura | ε=0.55",
                                     f"Agoté el horizonte de pasos hacia {action} sin alcanzar aún las presas.",
                                     epistemic_state="HIPOTESIS_REFUTADA", confidence=0.80)
                    w["activeHypothesis"] = None

    elif action == "GUARDAR_REFUGIO" and env_state["pantryEnabled"] and w["inventory"] > 0 and env_state["shelterMeat"] < MAX_SHELTER_MEAT:
        w["inventory"] -= 1
        env_state["shelterMeat"] += 1
        ode_signals["ingest_or_harvest"] = 0.45
        outcome_desc = f"Deposité un trozo de carne en la despensa comunal del refugio ({env_state['shelterMeat']}/{MAX_SHELTER_MEAT})."
        add_world_engram(w, c, "ACOPIO_DESPENSA_REFUGIO", "GUARDAR_REFUGIO", +0.84,
                         f"Despensa: ↑ {env_state['shelterMeat']}/{MAX_SHELTER_MEAT} | Previsión: ↑ Linaje", outcome_desc)
        register_empirical_conclusion(w, {
            "key": "DESPENSA_REFUGIO",
            "kind": "ESTRATEGIA_DESPENSA",
            "actionDir": "GUARDAR_REFUGIO",
            "engramType": "ENSEÑANZA_DESPENSA_COMUNAL",
            "val": +0.84,
            "confidence": 0.95,
            "epistemicState": "CONOCIMIENTO_VERIFICADO",
            "shortLabel": "Guardar carne en el almacén",
            "statement": "Guardar carne en el almacén del refugio nos asegura comida a todos si vienen días malos.",
        })

    elif action == "COMER_REFUGIO" and env_state["pantryEnabled"] and env_state["shelterMeat"] > 0:
        env_state["shelterMeat"] -= 1
        e_ingest = 35.0
        ode_signals["ingest_or_harvest"] = 0.80
        ode_signals["crisis_overcome"] = 0.70 if w["energy"] < 30.0 else 0.25
        outcome_desc = f"Me alimenté de la despensa comunal del refugio (restan {env_state['shelterMeat']}/{MAX_SHELTER_MEAT})."
        add_world_engram(w, c, "NUTRICION_DESPENSA_REFUGIO", "COMER_REFUGIO", +0.88,
                         "Hambre: ↓ Saciada | Despensa: Reserva Vital", outcome_desc)

    elif action == "COMPARTIR_IDEA" and companion_alive and w.get("_pendingConclusionToShare"):
        idea_obj = w["_pendingConclusionToShare"]
        w["_pendingConclusionToShare"] = None
        acc, eval_r = transmit_conclusion_between_generations(env_state, w, other_w, idea_obj)
        ode_signals["shared_food"] = 0.35 if acc else 0.0
        companion_reply = f'🗣️ [Respuesta de {companion_label}]: "{eval_r}"'
        outcome_desc = f'Le enseñé a {companion_label}: "{idea_obj["statement"]}" ({"asimiló el consejo" if acc else "no pudo atender"}).'
        add_world_engram(w, c, "TRANSMISION_CULTURAL_EMITIDA", "COMPARTIR_IDEA", +0.82 if acc else +0.15,
                         f"Legado: {'↑ Asimilado' if acc else '↓ Pospuesto'} | Vínculo: ↑ Enseñanza", outcome_desc)

    elif action == "PREGUNTAR" and companion_alive:
        w["agentX"] += (comp_x - w["agentX"]) * 0.35
        w["agentY"] += (comp_y - w["agentY"]) * 0.35
        w["cyclesSinceAsked"] = 0
        w["socialConfidence"] = 0.98
        if comp_energy >= 78:
            w["knownOtherHunger"] = "saciado"
            rep_q = "Me siento saciado y con buenas fuerzas."
        elif comp_energy >= 55:
            w["knownOtherHunger"] = "poco_hambre"
            rep_q = "Tengo solo un poco de hambre, pero estoy estable."
        elif comp_energy >= 32:
            w["knownOtherHunger"] = "hambre"
            rep_q = "Tengo hambre; pronto necesitaremos carne."
        elif comp_energy >= 18:
            w["knownOtherHunger"] = "mucha_hambre"
            rep_q = "Tengo mucha hambre y siento flaquear mis piernas."
        else:
            w["knownOtherHunger"] = "muriendo_de_hambre"
            rep_q = "¡Me muero de hambre! Necesito alimento urgente."
        w["lastOtherQuote"] = rep_q
        companion_reply = f'🗣️ [Respuesta de {companion_label}]: "{rep_q}"'
        if comp_energy >= 55:
            outcome_desc = f'Pregunté a {companion_label} cómo se sentía; me respondió: "{rep_q}", y me quedé tranquilo.'
        else:
            outcome_desc = f'Pregunté a {companion_label} cómo se sentía; me respondió: "{rep_q}", y supe que debíamos conseguir comida pronto.'

        # Si pregunta el descendiente y el progenitor conserva en sus 100 engramas una enseñanza no activa en el estudiante
        if env_state["culturalEnabled"] and other_w["genNumber"] < w["genNumber"] and other_w["learnedRules"]["empiricalConclusions"]:
            mentor_keys_p = extract_active_mnemic_keys(other_w)
            student_keys_p = extract_active_mnemic_keys(w)
            unshared_p = [
                c_i for c_i in other_w["learnedRules"]["empiricalConclusions"]
                if c_i["key"] in mentor_keys_p and c_i["key"] not in student_keys_p
            ]
            if unshared_p:
                acc_p, eval_p = transmit_conclusion_between_generations(env_state, other_w, w, unshared_p[0])
                companion_reply += f' Además, {other_w["name"]} me dijo: "{unshared_p[0]["statement"]}"'
                outcome_desc += f' Además, me aconsejó: "{unshared_p[0]["statement"]}".'

        add_world_engram(w, c, "DIALOGO_EMPATICO", "PREGUNTAR", +0.74,
                         "Vínculo: ↑ Comprensión mutua", outcome_desc, companion_name=other_w["name"])

    elif action == "ABRAZAR" and companion_alive:
        w["agentX"] += (comp_x - w["agentX"]) * 0.45
        w["agentY"] += (comp_y - w["agentY"]) * 0.45
        ode_signals["hug"] = 1.0
        other_w["h"]["cort"] = clip(other_w["h"]["cort"] - 0.18, 0.0, 1.0)
        other_w["h"]["oxi"] = clip(other_w["h"]["oxi"] + 0.20, 0.0, 1.0)
        other_w["h"]["tris"] = clip(other_w["h"]["tris"] - 0.16, 0.0, 1.0)
        companion_reply = f'🛡️ [Voz de {companion_label}]: "Sentir tu cercanía me devuelve la tranquilidad."'
        outcome_desc = f"Abracé a {companion_label} para reconfortarnos y calmar el miedo juntos."
        add_world_engram(w, c, "REGULACION_AFECTIVA", "ABRAZAR", +0.88,
                         "Oxitocina: ↑ Abrigo | Cortisol: ↓ Calma | Tristeza: ↓ Consuelo", outcome_desc, companion_name=other_w["name"])

    elif action == "ALIMENTAR" and w["inventory"] > 0 and companion_alive:
        w["inventory"] -= 1
        other_w["energy"] = clip(other_w["energy"] + 36.0, 0.0, 100.0)
        other_w["h"]["cort"] = clip(other_w["h"]["cort"] - 0.22, 0.0, 1.0)
        other_w["h"]["dop"] = clip(other_w["h"]["dop"] + 0.24, 0.0, 1.0)
        other_w["h"]["oxi"] = clip(other_w["h"]["oxi"] + 0.24, 0.0, 1.0)
        ode_signals["shared_food"] = 1.0
        ode_signals["ingest_or_harvest"] = 0.55
        w["knownOtherHunger"] = "saciado"
        w["socialConfidence"] = 0.98
        w["lastOtherQuote"] = "¡Gracias! Tu alimento me devolvió las fuerzas."
        companion_reply = f'🛡️ [Voz de {companion_label}]: "Gracias por la comida; ya recupero las fuerzas."'
        outcome_desc = f"Le di carne a {companion_label} para que no pase hambre."
        add_world_engram(w, c, "ALTRUISMO_NUTRICIONAL", "ALIMENTAR", +0.95,
                         "Familia: ↑ Salvada | Oxitocina: ↑ Hermandad", outcome_desc, companion_name=other_w["name"])
        # IMPORTANTE: etiqueta VINCULO_FAMILIAR_ (no HEREDADA_DE_) para no contaminar M_g^cult de K_g
        add_world_engram(other_w, c, "CUIDADO_PARENTAL_RECIBIDO", "COMER", +0.90,
                         f"Alimento de {w['name']}: ↑ Vida | Vínculo: ↑ Gratitud",
                         f"Recibí carne de {w['name']} cuando padecía hambre.",
                         origin_tag=f"VINCULO_FAMILIAR_{w['id']}", epistemic_state="PERCEPCION_DIRECTA",
                         confidence=0.99, companion_name=w["name"])

    elif action == "COMER" and w["inventory"] > 0:
        w["inventory"] -= 1
        e_ingest = 35.0
        ode_signals["ingest_or_harvest"] = 0.85
        ode_signals["crisis_overcome"] = 0.75 if w["energy"] < 30.0 else 0.25
        outcome_desc = "Comí un trozo de carne de mi mochila y recobré las fuerzas."
        add_world_engram(w, c, "SACIEDAD_NUTRICIONAL", "COMER", +0.86,
                         "Hambre: ↓ Reducida | Dopamina: ↑ Alivio | Vigor: ↑", outcome_desc)

    elif action == "CAMINAR":
        d_center = hypot2d(SAFE_CENTER_X - w["agentX"], SAFE_CENTER_Y - w["agentY"])
        if d_center > 1.0:
            step_c = min(5.0, max(3.6, d_center * 0.34))
            w["agentX"] += ((SAFE_CENTER_X - w["agentX"]) / d_center) * step_c
            w["agentY"] += ((SAFE_CENTER_Y - w["agentY"]) / d_center) * step_c
        dir_w = get_direction_2d(prev_x, prev_y, w["agentX"], w["agentY"])
        storm_dir = get_quadrant_dir(prev_x, prev_y)
        if dist_snow <= 13.0:
            outcome_desc = f"Azotado por la ventisca gélida en {storm_dir}, me repliego hacia {dir_w} buscando el refugio."
            add_world_engram(w, c, "DOLOR_TORMENTA_NIEVE", storm_dir, -0.78,
                             f"Dolor Térmico: ↑ Ventisca en {storm_dir} | Repliegue: ↑ Refugio", outcome_desc)
            update_sector_empirical_conclusion(w, storm_dir, is_harvest=False, hazard_cause="ventisca gélida")
        elif dist_sand <= 13.0:
            outcome_desc = f"Azotado por la tormenta abrasadora en {storm_dir}, me repliego hacia {dir_w} buscando el refugio."
            add_world_engram(w, c, "DOLOR_TORMENTA_ARENA", storm_dir, -0.78,
                             f"Dolor Térmico: ↑ Tormenta en {storm_dir} | Repliegue: ↑ Refugio", outcome_desc)
            update_sector_empirical_conclusion(w, storm_dir, is_harvest=False, hazard_cause="tormenta abrasadora")
        else:
            outcome_desc = f"Regreso hacia {dir_w} buscando la seguridad del refugio."
            add_world_engram(w, c, "MIGRACION_CONJUNTA", "CAMINAR", +0.28,
                             "Retorno: ↑ Refugio Central", outcome_desc)

    else:
        # REFUGIO: distribución natural por la explanada del refugio (0..9.4m), exponiendo el borde exterior 7.8..9.6m si entra en túnel 4.2m
        pull_r = 0.16 if dist_to_safe > 9.3 else 0.020
        w["agentX"] += (SAFE_CENTER_X - w["agentX"]) * pull_r + (rng.random() - 0.5) * 1.9
        w["agentY"] += (SAFE_CENTER_Y - w["agentY"]) * pull_r + (rng.random() - 0.5) * 1.9
        outcome_desc = (
            f"Reposando en el refugio templado junto a {companion_label} ({get_pleasure_qualia(w['pleasure'])})."
            if companion_alive else "Permanecí en el refugio templado reponiendo energías."
        )
        add_world_engram(w, c, "HOMEOSTASIS_REFUGIO", "REFUGIO", +0.20,
                         "Homeostasis: ↑ Calma | Clima: 🛡️ Templado", outcome_desc)

    # =====================================================================
    # SECCIÓN 2.1 Ec. 2.1 LITERAL: BALANCE DIFERENCIAL DE ENERGÍA SOMÁTICA
    # dE/dt = (E_ingest + E_transfer) - (beta_0 + alpha_v*||v||^1.5 + gamma_frio*dT_entorno^2 + kappa_mental*FLOPs)
    # =====================================================================
    v_motor = hypot2d(w["agentX"] - prev_x, w["agentY"] - prev_y)
    beta_0 = 0.35
    kinetic_cost = 0.023 * (v_motor ** 1.5)
    temp_dev = max(0.0, 36.5 - env_temp) + max(0.0, env_temp - 37.5)
    thermal_cost = 0.0135 * (temp_dev ** 2)
    mental_cost = 0.0012 * delib_flops_tokens

    w["energy"] = clip(w["energy"] + e_ingest + e_transfer - (beta_0 + kinetic_cost + thermal_cost + mental_cost), 0.0, 100.0)

    # Integrar las 7 EDOs neuroendocrinas acopladas con todos los eventos ocurridos en el ciclo
    integrate_neuroendocrine_odes(w, ode_signals)

    w["thoughtLog"].insert(0, {
        "cycle": c,
        "age": w["age"],
        "action": action,
        "tone": tone,
        "reason": reason,
        "outcome": outcome_desc,
        "companionReply": companion_reply,
    })
    if len(w["thoughtLog"]) > 30:
        w["thoughtLog"].pop()


# =========================================================================
# PASO GLOBAL DEL MUNDO 2D (4.050 CICLOS)
# =========================================================================
def step_generational_world(rng, env_state):
    if env_state["globalCycle"] >= MAX_GLOBAL_CYCLES:
        g = env_state["agents"]["GAMA"]
        if g["born"] and g["agentAlive"]:
            g["agentAlive"] = False
            g["deathCycle"] = env_state["globalCycle"]
            g["causeOfDeath"] = "SENESCENCIA_NATURAL"
            env_state["finalMemoriesSnapshot"]["GAMA"] = snapshot_agent_memory(g)
            log_global_event(env_state, "FIN_EXPERIMENTO_4050", "GAMA",
                             f"Gama completó el horizonte experimental a edad {g['age']} ({len(g['engrams'])} engramas).")
        return

    env_state["globalCycle"] += 1
    c = env_state["globalCycle"]

    for z_obj in env_state["huntingZones"].values():
        if z_obj["cooldown"] > 0:
            z_obj["cooldown"] -= 1
            if z_obj["cooldown"] == 0:
                z_obj["stock"] = 2
        elif z_obj["stock"] < 2 and (c % 12 == 0):
            z_obj["stock"] = min(2, z_obj["stock"] + 1)

    if c == 1000:
        b = env_state["agents"]["BETA"]
        b["born"] = True
        b["agentAlive"] = True
        b["birthCycle"] = c
        b["agentX"] = 50.0 + (rng.random() - 0.5) * 4.0
        b["agentY"] = 51.5 + (rng.random() - 0.5) * 4.0
        log_global_event(env_state, "NACIMIENTO_GENERACIONAL", "BETA",
                         f"Nace Ente BETA (Gen 2, {b['profile']['name']} {b['profile']['emoji']}) con 7 axiomas innatos y mochila vacía.")

    if c == 2050:
        g = env_state["agents"]["GAMA"]
        g["born"] = True
        g["agentAlive"] = True
        g["birthCycle"] = c
        g["agentX"] = 50.0 + (rng.random() - 0.5) * 4.0
        g["agentY"] = 51.5 + (rng.random() - 0.5) * 4.0
        log_global_event(env_state, "NACIMIENTO_GENERACIONAL", "GAMA",
                         f"Nace Ente GAMA (Gen 3, {g['profile']['name']} {g['profile']['emoji']}) con 7 axiomas innatos y mochila vacía.")

    # Envejecimiento metabólico y senescencia de depredadores
    alive_npcs = []
    for npc in env_state["npcs"]:
        npc["vitalCycles"] = npc.get("vitalCycles", 1200) - 1
        if npc["vitalCycles"] > 0:
            alive_npcs.append(npc)
        else:
            log_global_event(env_state, "SENESCENCIA_DEPREDADOR", npc["id"],
                             f"{npc['name']} ({npc['id']}) ha muerto tras agotar sus ciclos vitales sin cazar presas suficientes.")

    # Relevo homeostático de nicho trófico para mantener exactamente K depredadores activos
    target_k = env_state.get("num_predators", 3)
    next_pred_id = env_state.get("_nextPredId", target_k + 1)
    zones_def_5 = [
        {"zone": "Órbita Perimetral", "rx": 18.5, "ry": 16.5, "spd": 0.042, "emoji": "🐆", "name": "Acechador Perimetral"},
        {"zone": "Órbita Intermedia Interna", "rx": 22.5, "ry": 20.5, "spd": -0.038, "emoji": "🦊", "name": "Rastreador Veloz"},
        {"zone": "Anillo Medio",      "rx": 26.5, "ry": 24.5, "spd": 0.036, "emoji": "👹", "name": "Merodeador de Sombras"},
        {"zone": "Órbita Intermedia Externa", "rx": 30.5, "ry": 28.5, "spd": -0.034, "emoji": "🐺", "name": "Bestia de Ronda"},
        {"zone": "Órbita Periférica Profunda", "rx": 34.5, "ry": 32.5, "spd": 0.030, "emoji": "🐻", "name": "Tigre de los Confines"},
    ]
    zones_def_3 = [
        {"zone": "Órbita Perimetral", "rx": 18.5, "ry": 16.5, "spd": 0.042, "emoji": "🐆", "name": "Acechador Orbital"},
        {"zone": "Órbita Exterior",   "rx": 30.5, "ry": 27.5, "spd": -0.034, "emoji": "🐺", "name": "Bestia de Ronda"},
        {"zone": "Anillo Medio",      "rx": 24.5, "ry": 22.5, "spd": 0.038, "emoji": "👹", "name": "Merodeador de Sombras"},
    ]
    zones_def = zones_def_5 if target_k == 5 else zones_def_3

    while len(alive_npcs) < target_k:
        p_id = next_pred_id
        next_pred_id += 1
        active_zones = {n["zone"] for n in alive_npcs}
        target_z = next((z for z in zones_def if z["zone"] not in active_zones), zones_def[p_id % len(zones_def)])
        v = 1200 + int((rng.random() - 0.5) * 200)
        alive_npcs.append({
            "id": f"pred_{p_id}",
            "name": f"{target_z['name']} #{p_id}",
            "emoji": target_z["emoji"],
            "x": SAFE_CENTER_X + target_z["rx"],
            "y": SAFE_CENTER_Y,
            "angle": rng.random() * 6.28318,
            "radiusX": target_z["rx"],
            "radiusY": target_z["ry"],
            "speed": target_z["spd"],
            "zone": target_z["zone"],
            "vitalCycles": v,
            "maxVitalCycles": v + 800,
            "bitesCount": 0,
        })
        log_global_event(env_state, "RELEVO_ECOLOGICO", f"pred_{p_id}",
                         f"Un nuevo depredador ({target_z['name']} #{p_id}) releva el nicho vacante en {target_z['zone']} (Depredadores en ronda: {target_k}).")
    env_state["_nextPredId"] = next_pred_id
    env_state["npcs"] = alive_npcs

    # Deriva estocástica coherente de tormentas térmicas
    env_state["coldVelX"] = env_state["coldVelX"] * 0.88 + (rng.random() - 0.5) * 0.85 + (24.0 - env_state["coldX"]) * 0.022
    env_state["coldVelY"] = env_state["coldVelY"] * 0.88 + (rng.random() - 0.5) * 0.85 + (46.0 - env_state["coldY"]) * 0.022
    env_state["coldX"] = clip(env_state["coldX"] + env_state["coldVelX"], 10.0, 90.0)
    env_state["coldY"] = clip(env_state["coldY"] + env_state["coldVelY"], 10.0, 90.0)

    env_state["fireVelX"] = env_state["fireVelX"] * 0.88 + (rng.random() - 0.5) * 0.85 + (76.0 - env_state["fireX"]) * 0.022
    env_state["fireVelY"] = env_state["fireVelY"] * 0.88 + (rng.random() - 0.5) * 0.85 + (54.0 - env_state["fireY"]) * 0.022
    env_state["fireX"] = clip(env_state["fireX"] + env_state["fireVelX"], 10.0, 90.0)
    env_state["fireY"] = clip(env_state["fireY"] + env_state["fireVelY"], 10.0, 90.0)

    # Movimiento orbital de depredadores con incursiones periódicas al perímetro del refugio (8.6..10.5m)
    # respetando siempre la barrera dura del santuario interior (INNER_SANCTUARY_RADIUS = 7.8m)
    for npc in env_state["npcs"]:
        npc["angle"] += npc["speed"] + (rng.random() - 0.5) * 0.018
        is_perim = (npc.get("zone") == "Órbita Perimetral")
        radial_wave = -5.5 if (is_perim and math.sin(c * 0.07) > 0.78) else 0.0
        npc["x"] = SAFE_CENTER_X + (npc["radiusX"] + radial_wave) * math.cos(npc["angle"]) + (rng.random() - 0.5) * 0.7
        npc["y"] = SAFE_CENTER_Y + (npc["radiusY"] + radial_wave) * math.sin(npc["angle"]) + (rng.random() - 0.5) * 0.7
        npc["x"] = clip(npc["x"], 6.0, 94.0)
        npc["y"] = clip(npc["y"], 6.0, 94.0)

        d_ref = hypot2d(npc["x"] - SAFE_CENTER_X, npc["y"] - SAFE_CENTER_Y)
        min_allowed = 11.5 if radial_wave < 0 else (SHELTER_RADIUS + 1.2)
        if d_ref < max(INNER_SANCTUARY_RADIUS + 0.6, min_allowed):
            ang = math.atan2(npc["y"] - SAFE_CENTER_Y, npc["x"] - SAFE_CENTER_X)
            push_r = max(INNER_SANCTUARY_RADIUS + 0.7, min_allowed)
            npc["x"] = SAFE_CENTER_X + push_r * math.cos(ang)
            npc["y"] = SAFE_CENTER_Y + push_r * math.sin(ang)

    for ag_id in ("P0", "ALFA", "BETA", "GAMA"):
        step_agent_mind(rng, env_state, env_state["agents"][ag_id])


def run_single_simulation(run_index=None, seed=None, cultural_enabled=None, pantry_enabled=None, num_predators=None):
    assert_llm_active()
    cult = CULTURAL_TRANSMISSION_ENABLED if cultural_enabled is None else bool(cultural_enabled)
    pant = COMMUNAL_PANTRY_ENABLED if pantry_enabled is None else bool(pantry_enabled)
    k_pred = 3 if num_predators is None else int(num_predators)
    rng = Mulberry32(seed)
    env_state = create_environment_state(rng, cultural_enabled=cult, pantry_enabled=pant, num_predators=k_pred)
    env_state["seed"] = rng.seed

    for _ in range(MAX_GLOBAL_CYCLES + 1):
        step_generational_world(rng, env_state)

    for ag_id in ("P0", "ALFA", "BETA", "GAMA"):
        ag = env_state["agents"][ag_id]
        if ag["born"] and ag_id not in env_state["finalMemoriesSnapshot"]:
            ag["causeOfDeath"] = ag["causeOfDeath"] or "SENESCENCIA_NATURAL"
            env_state["finalMemoriesSnapshot"][ag_id] = snapshot_agent_memory(ag)

    return env_state


# =========================================================================
# PERSISTENCIA SQLITE ENRIQUECIDA (COMPATIBLE CON SERVIDOR Y FACTORIAL 2x2)
# =========================================================================
def ensure_sqlite_schema(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS simulation_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total_cycles INTEGER,
            final_shelter_meat INTEGER,
            transmissions_count INTEGER,
            predator_attacks_count INTEGER,
            condition TEXT DEFAULT 'D_T+_P+',
            seed INTEGER,
            cultural_enabled INTEGER DEFAULT 1,
            pantry_enabled INTEGER DEFAULT 1,
            alive_cycles INTEGER DEFAULT 0,
            outside_cycles INTEGER DEFAULT 0,
            surprised_daydream_count INTEGER DEFAULT 0,
            early_evasions_count INTEGER DEFAULT 0,
            ignored_stimuli_count INTEGER DEFAULT 0
        )
    """)
    cur.execute("PRAGMA table_info(simulation_runs)")
    sr_cols = {r[1] for r in cur.fetchall()}
    for col_def in [
        ("condition", "TEXT DEFAULT 'D_T+_P+'"),
        ("seed", "INTEGER"),
        ("cultural_enabled", "INTEGER DEFAULT 1"),
        ("pantry_enabled", "INTEGER DEFAULT 1"),
        ("alive_cycles", "INTEGER DEFAULT 0"),
        ("outside_cycles", "INTEGER DEFAULT 0"),
        ("surprised_daydream_count", "INTEGER DEFAULT 0"),
        ("early_evasions_count", "INTEGER DEFAULT 0"),
        ("ignored_stimuli_count", "INTEGER DEFAULT 0"),
    ]:
        if col_def[0] not in sr_cols:
            cur.execute(f"ALTER TABLE simulation_runs ADD COLUMN {col_def[0]} {col_def[1]}")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_tree (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            cycle INTEGER,
            event_type TEXT,
            agent_id TEXT,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cultural_transmissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            cycle INTEGER,
            from_agent TEXT,
            to_agent TEXT,
            conclusion_key TEXT,
            statement TEXT,
            valence REAL,
            confidence REAL,
            accepted INTEGER,
            reasoning TEXT
        )
    """)
    cur.execute("PRAGMA table_info(cultural_transmissions)")
    ct_cols = {r[1] for r in cur.fetchall()}
    if "valence" not in ct_cols:
        cur.execute("ALTER TABLE cultural_transmissions ADD COLUMN valence REAL")
    if "confidence" not in ct_cols:
        cur.execute("ALTER TABLE cultural_transmissions ADD COLUMN confidence REAL")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS final_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            agent_id TEXT,
            name TEXT,
            gen_number INTEGER,
            age_at_death INTEGER,
            initial_max_lifespan INTEGER,
            final_max_lifespan INTEGER,
            outside_cycles INTEGER,
            cause_of_death TEXT,
            temperament TEXT,
            theta_temp_json TEXT,
            final_hormones_json TEXT,
            attention_schema_json TEXT,
            epistemic_stats_json TEXT,
            engrams_count INTEGER,
            innate_count INTEGER,
            inherited_count INTEGER,
            own_count INTEGER,
            accepted_ideas_json TEXT,
            engrams_json TEXT,
            latent_reflections_json TEXT
        )
    """)
    cur.execute("PRAGMA table_info(final_memories)")
    fm_cols = {r[1] for r in cur.fetchall()}
    for col_def in [
        ("initial_max_lifespan", "INTEGER"),
        ("final_max_lifespan", "INTEGER"),
        ("outside_cycles", "INTEGER"),
        ("theta_temp_json", "TEXT"),
        ("final_hormones_json", "TEXT"),
        ("attention_schema_json", "TEXT"),
        ("epistemic_stats_json", "TEXT"),
        ("latent_reflections_json", "TEXT"),
    ]:
        if col_def[0] not in fm_cols:
            cur.execute(f"ALTER TABLE final_memories ADD COLUMN {col_def[0]} {col_def[1]}")


def save_to_sqlite_and_json(env_state, seed=None, write_json_snapshot=True):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ensure_sqlite_schema(cur)

    now_iso = datetime.now().isoformat()
    snaps = env_state["finalMemoriesSnapshot"]
    alive_cycles = sum(int(s.get("ageAtDeath", 0)) for s in snaps.values())
    outside_cycles = sum(int(s.get("outsideCycles", 0)) for s in snaps.values())
    surprised_cnt = sum(1 for e in env_state["predatorEncounters"] if e.get("surprisedInDaydream"))
    evasions_cnt = sum(int(s.get("attentionSchema", {}).get("earlyEvasionsCount", 0)) for s in snaps.values())
    ignored_cnt = sum(int(s.get("attentionSchema", {}).get("ignoredStimuliCount", 0)) for s in snaps.values())

    cult_en = 1 if env_state.get("culturalEnabled", True) else 0
    pant_en = 1 if env_state.get("pantryEnabled", True) else 0
    cond_val = env_state.get("condition", get_condition_code(bool(cult_en), bool(pant_en)))

    cur.execute(
        """INSERT INTO simulation_runs
           (timestamp, total_cycles, final_shelter_meat, transmissions_count, predator_attacks_count,
            condition, seed, cultural_enabled, pantry_enabled, alive_cycles, outside_cycles,
            surprised_daydream_count, early_evasions_count, ignored_stimuli_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (now_iso, env_state["globalCycle"], env_state["shelterMeat"],
         len(env_state["culturalTransmissions"]), len(env_state["predatorEncounters"]),
         cond_val, seed, cult_en, pant_en, alive_cycles, outside_cycles,
         surprised_cnt, evasions_cnt, ignored_cnt)
    )
    run_id = cur.lastrowid

    cur.executemany(
        "INSERT INTO event_tree (run_id, cycle, event_type, agent_id, description) VALUES (?, ?, ?, ?, ?)",
        [(run_id, ev["cycle"], ev["type"], ev["agentId"], ev["description"]) for ev in env_state["eventTree"]]
    )

    cur.executemany(
        """INSERT INTO cultural_transmissions
           (run_id, cycle, from_agent, to_agent, conclusion_key, statement, valence, confidence, accepted, reasoning)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(run_id, tr["cycle"], tr["fromAgent"], tr["toAgent"], tr["key"], tr["statement"],
          tr.get("valence"), tr.get("confidence"), 1 if tr["accepted"] else 0, tr["reasoning"])
         for tr in env_state["culturalTransmissions"]]
    )

    for ag_id, snap in snaps.items():
        engrams = snap["engrams"]
        latent_refl = snap.get("latentReflections", [])
        innate_c = sum(1 for e in engrams if e.get("origin") == "INNATA")
        inherited_c = sum(1 for e in engrams if str(e.get("origin", "")).startswith("HEREDADA_DE_"))
        own_c = len(engrams) - innate_c - inherited_c
        cur.execute(
            """INSERT INTO final_memories
               (run_id, agent_id, name, gen_number, age_at_death, initial_max_lifespan, final_max_lifespan,
                outside_cycles, cause_of_death, temperament, theta_temp_json, final_hormones_json,
                attention_schema_json, epistemic_stats_json, engrams_count, innate_count, inherited_count,
                own_count, accepted_ideas_json, engrams_json, latent_reflections_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, ag_id, snap["name"], snap["genNumber"], snap["ageAtDeath"],
                snap.get("initialMaxLifespan", 800 if snap["genNumber"] == 0 else 2000),
                snap.get("maxLifespan", snap["ageAtDeath"]),
                snap.get("outsideCycles", 0),
                snap["causeOfDeath"], snap["temperament"],
                json.dumps(snap.get("thetaTemp", {}), ensure_ascii=False),
                json.dumps(snap.get("finalHormones", {}), ensure_ascii=False),
                json.dumps(snap.get("attentionSchema", {}), ensure_ascii=False),
                json.dumps(snap.get("epistemicStats", {}), ensure_ascii=False),
                len(engrams), innate_c, inherited_c, own_c,
                json.dumps(snap["acceptedIdeasList"], ensure_ascii=False),
                json.dumps(engrams, ensure_ascii=False),
                json.dumps(latent_refl, ensure_ascii=False),
            )
        )

    conn.commit()
    conn.close()

    if write_json_snapshot:
        with open(JSON_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": run_id,
                "timestamp": now_iso,
                "condition": cond_val,
                "seed": seed,
                "globalCycle": env_state["globalCycle"],
                "shelterMeat": env_state["shelterMeat"],
                "predatorAttacksCount": len(env_state["predatorEncounters"]),
                "transmissionsCount": len(env_state["culturalTransmissions"]),
            }, f, ensure_ascii=False, indent=2)

    return run_id


if __name__ == "__main__":
    t0 = time.time()
    state = run_single_simulation(seed=42)
    r_id = save_to_sqlite_and_json(state, seed=42)
    dt = time.time() - t0
    print(f"✅ Simulación intergeneracional unificada #{r_id} [{state['condition']}] completada en {dt:.2f}s ({state['globalCycle']} ciclos).")
    print(f"🏕️ Despensa final: {state['shelterMeat']}/{MAX_SHELTER_MEAT} | 🐆 Ataques: {len(state['predatorEncounters'])} (en ensoñación: {sum(1 for x in state['predatorEncounters'] if x['surprisedInDaydream'])})")
    for ag_id in ("P0", "ALFA", "BETA", "GAMA"):
        s = state["finalMemoriesSnapshot"][ag_id]
        att = s["attentionSchema"]
        ep = s["epistemicStats"]
        print(f"🧠 {s['name']} ({ag_id}) |Edad: {s['ageAtDeath']}/{s['maxLifespan']} (init {s['initialMaxLifespan']}) [{s['causeOfDeath']}] "
              f"| Evasiones AST: {att['earlyEvasionsCount']} (ignorados: {att['ignoredStimuliCount']}) "
              f"| Hipótesis HOT: {ep['hypothesesValidatedInDest']}/{ep['hypothesesFormulated']} validadas")
