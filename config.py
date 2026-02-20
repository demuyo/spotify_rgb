# config.py
"""
Configuração do Spotify RGB Sync
Auto-gerado pela GUI
"""

import os
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

def load_env():
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

# ══════════════════════════════════════════════════════════════════════════════
# SPOTIFY API
# ══════════════════════════════════════════════════════════════════════════════

SPOTIFY_CLIENT_ID     = os.environ["SPOTIPY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIPY_CLIENT_SECRET"]
SPOTIFY_REDIRECT_URI  = os.environ["SPOTIPY_REDIRECT_URI"]

# ══════════════════════════════════════════════════════════════════════════════
# SPOTIFY POLLING RATE
# ══════════════════════════════════════════════════════════════════════════════

SPOTIFY_SCOPE = 'user-read-currently-playing'
POLL_INTERVAL = 4.0
POLL_ENDING = 1.5
POLL_ENDING_SOON = 0.5
POLL_AFTER_CHANGE = 2.0
POLL_IDLE = 5.0

# ══════════════════════════════════════════════════════════════════════════════
# OPENRGB
# ══════════════════════════════════════════════════════════════════════════════

OPENRGB_HOST = '127.0.0.1'
OPENRGB_PORT = 6742
OPENRGB_NAME = 'SpotifySync'

# ══════════════════════════════════════════════════════════════════════════════
# LED CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

LED_SKIP_START = 5
LED_SKIP_END = 0
LED_COUNT = None
SELECTED_DEVICES = None

# ══════════════════════════════════════════════════════════════════════════════
# COR PADRÃO
# ══════════════════════════════════════════════════════════════════════════════

REACTIVE_MODE = True
LED_MODE = 'breathing'
HIT_STYLE = 'both'
VISUAL_EFFECT = 'bands'
DETECTION_MODE = 'peaks'
DEFAULT_COLOR = (100, 0, 200)

# ══════════════════════════════════════════════════════════════════════════════
# BRILHO
# ══════════════════════════════════════════════════════════════════════════════

BRIGHTNESS_FLOOR = 0.1
BRIGHTNESS_BASE = 0.25
BRIGHTNESS_KICK = 0.85
BRIGHTNESS_SNARE = 1.0
BRIGHTNESS_PEAK = 0.92
BRIGHTNESS_MAP = [(0.02, 0.01), (0.15, 0.02), (0.3, 0.08), (0.5, 0.25), (0.7, 0.5), (0.85, 0.75), (1.0, 1.0)]

# ══════════════════════════════════════════════════════════════════════════════
# COLOR SHIFT
# ══════════════════════════════════════════════════════════════════════════════

COLOR_SHIFT_KICK = 0.15
COLOR_SHIFT_SNARE = 0.4
COLOR_SHIFT_PEAK = 0.35

# ══════════════════════════════════════════════════════════════════════════════
# SENSIBILIDADE
# ══════════════════════════════════════════════════════════════════════════════

SENSITIVITY = 'medium'
PEAKS_SENSITIVITY = 'medium'
CUSTOM_KICK_THRESHOLD = 0.45
CUSTOM_SNARE_THRESHOLD = 0.35
CUSTOM_KICK_MIN_ENERGY = 0.006
CUSTOM_SNARE_MIN_ENERGY = 0.004
CUSTOM_KICK_MINIOI = 0.06
CUSTOM_SNARE_MINIOI = 0.04
PEAK_HOLD_TIME = 0.12
PEAK_MIN_INTERVAL = 0.04
HIT_HOLD_TIME = 0.18

# ══════════════════════════════════════════════════════════════════════════════
# CHASE EFFECT
# ══════════════════════════════════════════════════════════════════════════════

CHASE_ENABLED = True
CHASE_SPEED_MAX = 0.8
CHASE_TAIL_LENGTH = 4
CHASE_BRIGHTNESS_MIN = 0.1
CHASE_BRIGHTNESS_MAX = 0.5
CHASE_BEAT_FLASH = 0.5
CHASE_FLASH_DECAY = 0.85
CHASE_BG_BRIGHTNESS = 0.15

# ══════════════════════════════════════════════════════════════════════════════
# FREQUENCY EFFECT
# ══════════════════════════════════════════════════════════════════════════════

FREQ_SMOOTHING_ATTACK = 0.38
FREQ_SMOOTHING_DECAY = 0.12
FREQ_BEAT_AMOUNT = 0.25
FREQ_BEAT_DECAY = 0.92
FREQ_BG_BRIGHTNESS = 0.12
FREQ_BASS_MULT = 0.5
FREQ_HIGH_SHIFT = 0.25
FREQ_COLOR_LERP = 0.35
FREQ_ZONE_BLEND = 0.08

# ══════════════════════════════════════════════════════════════════════════════
# HYBRID EFFECT
# ══════════════════════════════════════════════════════════════════════════════

HYBRID_CHASE_INTENSITY = 0.6
HYBRID_CHASE_SPEED = 0.5
HYBRID_CHASE_TAIL = 5
HYBRID_CHASE_MODE = 'blend'

# ══════════════════════════════════════════════════════════════════════════════
# BAND EFFECT
# ══════════════════════════════════════════════════════════════════════════════

BAND_ZONE_PERCUSSION = 0.33
BAND_ZONE_BASS = 0.33
BAND_ZONE_MELODY = 0.33
BAND_COLOR_SCHEME = 'album_colors'
BAND_HUE_PERCUSSION = 0.0
BAND_HUE_BASS = 0.0
BAND_HUE_MELODY = 0.0
BAND_SAT_PERCUSSION = 1.0
BAND_SAT_BASS = 1.0
BAND_SAT_MELODY = 1.0
BAND_SMOOTHING_ATTACK = 0.56
BAND_SMOOTHING_DECAY = 0.12
BAND_BEAT_ATTACK = 0.5
BAND_BEAT_DECAY = 0.09
BAND_BEAT_FLASH = 0.6
BAND_BEAT_COLOR_SHIFT = 0.0
BAND_BG_BRIGHTNESS = 0.08
BAND_INTERNAL_GRADIENT = 0.03
BAND_COLOR_LERP = 0.4
BAND_ZONE_BLEND_WIDTH = 2
BAND_BOOST_PERCUSSION = 1.4
BAND_BOOST_BASS = 1.2
BAND_BOOST_MELODY = 1.7
BAND_EXPANSION_PERCUSSION = 1.2000000000000002
BAND_EXPANSION_BASS = 1.0
BAND_EXPANSION_MELODY = 1.4
BAND_FLOOR_PERCUSSION = 0.1
BAND_FLOOR_BASS = 0.1
BAND_FLOOR_MELODY = 0.1
BAND_CEILING_PERCUSSION = 1.3
BAND_CEILING_BASS = 1.4
BAND_CEILING_MELODY = 1.3
BAND_ATTACK = 0.45
BAND_DECAY = 0.08
BAND_RESPONSE_CURVE = 'linear'
BAND_COMPRESSION_ENABLED = True
BAND_COMPRESSION_THRESHOLD = 0.7
BAND_COMPRESSION_RATIO = 1.0

# ══════════════════════════════════════════════════════════════════════════════
# STANDBY MODE
# ══════════════════════════════════════════════════════════════════════════════

STANDBY_BRIGHTNESS_MIN = 0.15
STANDBY_BRIGHTNESS_MAX = 0.4
STANDBY_BREATHING_SPEED = 0.025

# ══════════════════════════════════════════════════════════════════════════════
# QUANTIZED
# ══════════════════════════════════════════════════════════════════════════════

QUANTIZED_UPDATE_INTERVAL = 0.3
QUANTIZED_LEVELS = 5

# ══════════════════════════════════════════════════════════════════════════════
# OUTROS
# ══════════════════════════════════════════════════════════════════════════════

BAND_FREQ_BASS_MAX = 400
BAND_FREQ_BASS_MIN = 200
BAND_FREQ_MELODY_MAX = 16000
BAND_FREQ_MELODY_MIN = 6000
BAND_FREQ_PERCUSSION_MAX = 200
BAND_FREQ_PERCUSSION_MIN = 20
COLOR_ASSIGNMENT_MODE = 'vibrant_bass'
COLOR_MIN_SATURATION = 0.8
COLOR_SELECTION_STRATEGY = 'contrast'

# ══════════════════════════════════════════════════════════════════════════════
# AGC (Automatic Gain Control) — Normalização adaptativa
# ══════════════════════════════════════════════════════════════════════════════

# Habilita AGC (normalização adaptativa ao volume)
AGC_ENABLED = True

# Ganho máximo quando volume está baixo (1.0 = sem boost, 4.0 = 4x)
AGC_MAX_GAIN = 3.5

# Ganho mínimo quando volume está alto (evita saturar)
AGC_MIN_GAIN = 0.8

# Velocidade de adaptação do ganho (0.01 = lento, 0.1 = rápido)
AGC_ATTACK = 0.03
AGC_RELEASE = 0.01

# Volume alvo (o AGC tenta manter a energia média nesse nível)
AGC_TARGET = 0.35

# ══════════════════════════════════════════════════════════════════════════════
# COMPRESSOR DE DINÂMICA — Suaviza diferença entre baixo/alto
# ══════════════════════════════════════════════════════════════════════════════

# Threshold do compressor (0.0-1.0, valores abaixo não são comprimidos)
COMPRESSOR_THRESHOLD = 0.25

# Ratio (2.0 = 2:1, 4.0 = 4:1, quanto maior mais comprime)
COMPRESSOR_RATIO = 2.5

# Knee (suavidade da transição, 0.0 = hard knee, 0.3 = soft)
COMPRESSOR_KNEE = 0.15

# Makeup gain automático (compensa a redução de volume)
COMPRESSOR_MAKEUP = 1.4

# ══════════════════════════════════════════════════════════════════════════════
# SMOOTHING ADAPTATIVO — Decay mais lento em volume baixo
# ══════════════════════════════════════════════════════════════════════════════

# Habilita smoothing adaptativo
ADAPTIVE_SMOOTHING = True

# Multiplicador de decay em volume baixo (2.0 = decay 2x mais lento)
SMOOTHING_LOW_VOL_MULT = 2.5

# Limiar de "volume baixo" (0.0-1.0)
SMOOTHING_LOW_VOL_THRESH = 0.35

# ══════════════════════════════════════════════════════════════════════════════
# FLOOR DINÂMICO — Brilho mínimo sobe quando volume está baixo
# ══════════════════════════════════════════════════════════════════════════════

# Habilita floor dinâmico
DYNAMIC_FLOOR_ENABLED = True

# Floor máximo quando volume está muito baixo
DYNAMIC_FLOOR_MAX = 0.15

# Volume abaixo do qual o floor começa a subir
DYNAMIC_FLOOR_THRESH = 0.30