import os
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# CARREGAMENTO DO .env COM FALLBACK
# ══════════════════════════════════════════════════════════════════════════════

def load_env():
    """Carrega .env do diretório do executável ou script."""
    # Detecta se está rodando como executável PyInstaller
    if getattr(sys, 'frozen', False):
        # Executável: usa diretório do .exe
        app_dir = Path(sys.executable).parent
    else:
        # Script: usa diretório do config.py
        app_dir = Path(__file__).parent
    
    env_path = app_dir / ".env"
    
    if env_path.exists():
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
        return True
    return False

import sys
_env_loaded = load_env()

# ══════════════════════════════════════════════════════════════════════════════
# SPOTIFY API (com defaults vazios se .env não existir)
# ══════════════════════════════════════════════════════════════════════════════

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")

# Validação (só em modo debug)
if __name__ != "__main__" and not _env_loaded:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        "⚠️  Arquivo .env não encontrado!\n"
        "   Crie um arquivo .env na pasta do executável com:\n"
        "   SPOTIPY_CLIENT_ID=seu_id\n"
        "   SPOTIPY_CLIENT_SECRET=seu_secret\n"
        "   SPOTIPY_REDIRECT_URI=http://localhost:8888/callback"
    )

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

CHASE_ENABLED = False
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
BAND_BOOST_PERCUSSION = 1.1
BAND_BOOST_BASS = 0.9
BAND_BOOST_MELODY = 1.5
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
BAND_COMPRESSION_ENABLED = False
BAND_COMPRESSION_THRESHOLD = 0.7
BAND_COMPRESSION_RATIO = 1.0

# ══════════════════════════════════════════════════════════════════════════════
# STANDBY MODE
# ══════════════════════════════════════════════════════════════════════════════

STANDBY_BRIGHTNESS_MIN = 0.15
STANDBY_BRIGHTNESS_MAX = 0.4
STANDBY_BREATHING_SPEED = 0.08

# ══════════════════════════════════════════════════════════════════════════════
# QUANTIZED
# ══════════════════════════════════════════════════════════════════════════════

QUANTIZED_UPDATE_INTERVAL = 0.3
QUANTIZED_LEVELS = 5

# ══════════════════════════════════════════════════════════════════════════════
# OUTROS
# ══════════════════════════════════════════════════════════════════════════════

ADAPTIVE_SMOOTHING = True
AGC_ATTACK = 0.03
AGC_ENABLED = False
AGC_MAX_GAIN = 3.5
AGC_MIN_GAIN = 0.8
AGC_RELEASE = 0.01
AGC_TARGET = 0.35
BAND_FREQ_BASS_MAX = 400
BAND_FREQ_BASS_MIN = 200
BAND_FREQ_MELODY_MAX = 16000
BAND_FREQ_MELODY_MIN = 6000
BAND_FREQ_PERCUSSION_MAX = 200
BAND_FREQ_PERCUSSION_MIN = 20
COLOR_ASSIGNMENT_MODE = 'vibrant_bass'
COLOR_MIN_SATURATION = 0.8
COLOR_SELECTION_STRATEGY = 'contrast'
COMPRESSOR_KNEE = 0.15
COMPRESSOR_MAKEUP = 1.4
COMPRESSOR_RATIO = 2.5
COMPRESSOR_THRESHOLD = 0.25
DYNAMIC_FLOOR_ENABLED = True
DYNAMIC_FLOOR_MAX = 0.15
DYNAMIC_FLOOR_THRESH = 0.3
SMOOTHING_LOW_VOL_MULT = 2.5
SMOOTHING_LOW_VOL_THRESH = 0.35


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════

MAX_FPS = 60           # FPS máximo quando tocando
STANDBY_FPS = 15       # FPS quando pausado
START_MINIMIZED = True # Inicia só no tray