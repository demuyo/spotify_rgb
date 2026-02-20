# config.py
"""
Configuração do Spotify RGB Sync

🎨 CORES:
   As cores de cada banda são derivadas da cor da CAPA DO ÁLBUM.
   Cada banda desloca o HUE pra ter cor distinta.

🎸🎹🥁 BANDAS:
   PERCUSSION (🥁): Graves/Kick    → 20-200Hz   → Bumbo, kick, tom
   BASS       (🎸): Médios/Melodia → 200-4kHz   → Guitarra, voz, synth  
   MELODY     (🎹): Agudos/Hi-hat  → 4k-16kHz   → Pratos, hi-hat, brilho

📊 LED_SKIP:
   Se você tem LEDs invisíveis (ex: backplate da placa mãe),
   use LED_SKIP_START pra ignorá-los.
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
# Credenciais do Spotify Developer Dashboard
# https://developer.spotify.com/dashboard

SPOTIFY_CLIENT_ID     = os.environ["SPOTIPY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = os.environ["SPOTIPY_CLIENT_SECRET"]
SPOTIFY_REDIRECT_URI  = os.environ["SPOTIPY_REDIRECT_URI"]
SPOTIFY_SCOPE         = "user-read-currently-playing"

# ══════════════════════════════════════════════════════════════════════════════
# SPOTIFY POLLING RATE (segundos)
# ══════════════════════════════════════════════════════════════════════════════
# Controla com que frequência verificamos a música atual

POLL_INTERVAL     = 4.0   # Intervalo normal de verificação
POLL_ENDING       = 1.5   # Quando faltam 15s pra acabar
POLL_ENDING_SOON  = 0.5   # Quando faltam 5s pra acabar
POLL_AFTER_CHANGE = 2.0   # Logo após trocar de música
POLL_IDLE         = 15.0  # Quando pausado/sem música

# ══════════════════════════════════════════════════════════════════════════════
# OPENRGB
# ══════════════════════════════════════════════════════════════════════════════
# Conexão com o servidor OpenRGB (deve estar rodando)

OPENRGB_HOST = "127.0.0.1"  # IP do servidor OpenRGB
OPENRGB_PORT = 6742         # Porta do SDK (padrão: 6742)
OPENRGB_NAME = "SpotifySync"  # Nome do cliente

# ══════════════════════════════════════════════════════════════════════════════
# LED CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
# Configuração de quais LEDs usar

# ── IGNORAR LEDs INVISÍVEIS ──
# Use isso se você tem LEDs que não consegue ver (ex: backplate da placa mãe)
#
# Exemplo: Se os primeiros 5 LEDs são do backplate:
#   LED_SKIP_START = 5
#   LED_SKIP_END = 0
#
# Os LEDs pulados ficam APAGADOS, as zonas usam só os VISÍVEIS

LED_SKIP_START = 5   # 🔢 Quantos LEDs PULAR no INÍCIO (0 = nenhum)
LED_SKIP_END   = 0   # 🔢 Quantos LEDs PULAR no FIM (0 = nenhum)

# Total de LEDs a usar (None = calcula: total - skip_start - skip_end)
LED_COUNT = None

# Devices específicos (None = usa todos)
# Exemplo: SELECTED_DEVICES = [0, 2, 3]  → usa só esses
SELECTED_DEVICES = None

# ══════════════════════════════════════════════════════════════════════════════
# COR PADRÃO
# ══════════════════════════════════════════════════════════════════════════════
# Cor usada quando não há música tocando ou capa de álbum

DEFAULT_COLOR = (100, 0, 200)  # RGB (roxo)

# ══════════════════════════════════════════════════════════════════════════════
# AUDIO REACTIVE
# ══════════════════════════════════════════════════════════════════════════════

REACTIVE_MODE = True  # True = reage ao áudio | False = só cor estática

# Modo do LED:
#   "breathing" → Efeito visual reativo ao áudio
#   "quantized" → Poucos níveis de brilho (menos suave)
#   "static"    → Sem reação ao áudio
LED_MODE = "breathing"

# Estilo do hit (quando não usa efeito visual):
#   "brightness"   → Só aumenta brilho no beat
#   "color_shift"  → Muda cor pro branco no beat
#   "both"         → Brilho + cor juntos
HIT_STYLE = "both"

# ══════════════════════════════════════════════════════════════════════════════
# VISUAL EFFECT
# ══════════════════════════════════════════════════════════════════════════════
# Escolha o efeito visual principal

# Opções:
#   "bands"     → 🎸🎹🥁 Cada instrumento com sua COR! (recomendado)
#   "chase"     → Onda que corre pelos LEDs
#   "frequency" → Frequência → posição (graves esquerda, agudos direita)
#   "hybrid"    → Frequency + Chase combinados

VISUAL_EFFECT = "bands"

# ══════════════════════════════════════════════════════════════════════════════
# DETECÇÃO DE ÁUDIO
# ══════════════════════════════════════════════════════════════════════════════
# Como detectar beats e transientes

# Modos:
#   "drums" → Detecta kick/snare via aubio
#   "peaks" → Detecta picos de energia
#   "both"  → Combina os dois métodos (mais sensível)

DETECTION_MODE = "peaks"

# ══════════════════════════════════════════════════════════════════════════════
# BRILHO
# ══════════════════════════════════════════════════════════════════════════════
# Controle de brilho em diferentes situações

BRIGHTNESS_FLOOR = 0.20  # 🔆 Brilho MÍNIMO (nunca fica mais escuro que isso)
BRIGHTNESS_BASE  = 0.65  # 🔆 Brilho normal (proporcional ao volume)
BRIGHTNESS_KICK  = 0.85  # 🔆 Brilho no kick
BRIGHTNESS_SNARE = 1.00  # 🔆 Brilho no snare (máximo)
BRIGHTNESS_PEAK  = 0.92  # 🔆 Brilho em picos de energia

# ══════════════════════════════════════════════════════════════════════════════
# COLOR SHIFT
# ══════════════════════════════════════════════════════════════════════════════
# Quanto a cor clareia em direção ao BRANCO nos beats
# 0.0 = sem mudança | 1.0 = fica branco

COLOR_SHIFT_KICK  = 0.15  # 🎨 Shift no kick (sutil)
COLOR_SHIFT_SNARE = 0.40  # 🎨 Shift no snare (forte)
COLOR_SHIFT_PEAK  = 0.30  # 🎨 Shift em picos

# ══════════════════════════════════════════════════════════════════════════════
# SENSIBILIDADE
# ══════════════════════════════════════════════════════════════════════════════
# Quão sensível é a detecção de beats

# Presets disponíveis: "low", "medium", "high", "ultra", "custom"
SENSITIVITY       = "medium"  # Sensibilidade pra kick/snare
PEAKS_SENSITIVITY = "medium"  # Sensibilidade pra picos

# Valores customizados (só usados se SENSITIVITY = "custom")
CUSTOM_KICK_THRESHOLD   = 0.45
CUSTOM_SNARE_THRESHOLD  = 0.35
CUSTOM_KICK_MIN_ENERGY  = 0.006
CUSTOM_SNARE_MIN_ENERGY = 0.004
CUSTOM_KICK_MINIOI      = 0.06   # Intervalo mínimo entre kicks (segundos)
CUSTOM_SNARE_MINIOI     = 0.04   # Intervalo mínimo entre snares

# Timing
PEAK_HOLD_TIME    = 0.12  # Quanto tempo o "peak" fica ativo
PEAK_MIN_INTERVAL = 0.04  # Intervalo mínimo entre peaks
HIT_HOLD_TIME     = 0.18  # Quanto tempo o hit visual dura

# ══════════════════════════════════════════════════════════════════════════════
# CHASE EFFECT 🌊
# ══════════════════════════════════════════════════════════════════════════════
# Configuração do efeito de onda que corre pelos LEDs

CHASE_ENABLED        = True   # Habilita o chase (se VISUAL_EFFECT = "chase")
CHASE_SPEED_MAX      = 0.8    # 🚀 Velocidade máxima (LEDs por frame)
CHASE_TAIL_LENGTH    = 4      # 🌊 Tamanho da cauda da onda (LEDs)
CHASE_BRIGHTNESS_MIN = 0.10   # 🔆 Brilho da onda quando volume = 0%
CHASE_BRIGHTNESS_MAX = 0.50   # 🔆 Brilho da onda quando volume = 100%
CHASE_BEAT_FLASH     = 0.50   # ⚡ Intensidade do flash no beat
CHASE_FLASH_DECAY    = 0.85   # 📉 Velocidade que o flash some (0.9 = lento)
CHASE_BG_BRIGHTNESS  = 0.15   # 🔆 Brilho de fundo (sempre aceso)

# ══════════════════════════════════════════════════════════════════════════════
# FREQUENCY EFFECT 📊
# ══════════════════════════════════════════════════════════════════════════════
# Configuração do efeito que divide LEDs por frequência

# Smoothing (suavização)
FREQ_SMOOTHING_ATTACK = 0.38  # ⬆️ Velocidade de SUBIDA (maior = mais rápido)
FREQ_SMOOTHING_DECAY  = 0.12  # ⬇️ Velocidade de DESCIDA (menor = mais suave)

# Beat
FREQ_BEAT_AMOUNT = 0.25  # ⚡ Quanto o beat adiciona de brilho
FREQ_BEAT_DECAY  = 0.92  # 📉 Velocidade que o beat some

# Brilho e cor
FREQ_BG_BRIGHTNESS = 0.12  # 🔆 Brilho de fundo
FREQ_BASS_MULT     = 0.70  # 🎨 Multiplicador de cor dos graves (mais escuro)
FREQ_HIGH_SHIFT    = 0.25  # 🎨 Shift pro branco nos agudos

# Visual
FREQ_COLOR_LERP  = 0.35  # 🎬 Interpolação entre frames (maior = mais abrupto)
FREQ_ZONE_BLEND  = 0.08  # 🎬 Transição entre zonas

# ══════════════════════════════════════════════════════════════════════════════
# HYBRID EFFECT 🌊📊
# ══════════════════════════════════════════════════════════════════════════════
# Frequency como base + Chase por cima

HYBRID_CHASE_INTENSITY = 0.6    # 🌊 Visibilidade da onda (0.0-1.0)
HYBRID_CHASE_SPEED     = 0.5    # 🚀 Velocidade da onda
HYBRID_CHASE_TAIL      = 5      # 🌊 Tamanho da cauda
HYBRID_CHASE_MODE      = "blend"  # "add" = soma brilho | "blend" = mistura

# ══════════════════════════════════════════════════════════════════════════════
# BAND EFFECT 🎸🎹🥁
# ══════════════════════════════════════════════════════════════════════════════
# O EFEITO PRINCIPAL! Divide LEDs por instrumento, cada um com sua cor.
#
# COMO FUNCIONA:
#   1. Pega a cor dominante da CAPA DO ÁLBUM
#   2. Gera 3 cores derivadas (variando o HUE)
#   3. Cada zona reage à sua faixa de frequência
#
# BANDAS DE FREQUÊNCIA:
#   🥁 PERCUSSION: 20-200Hz    → Kick, bumbo, tom baixo
#   🎸 BASS:       200-4000Hz  → Baixo, guitarra, voz, synth
#   🎹 MELODY:     4000-16kHz  → Hi-hat, pratos, brilho, shimmer

# ── DISTRIBUIÇÃO DOS LEDs ─────────────────────────────────────────────────────
# Proporção de cada zona (deve somar ~1.0)
# Os LEDs são divididos na ordem: PERCUSSION → BASS → MELODY

BAND_ZONE_PERCUSSION = 0.36  # 🥁 36% dos LEDs (graves/kick)
BAND_ZONE_BASS       = 0.32  # 🎸 32% dos LEDs (médios/melodia)
BAND_ZONE_MELODY     = 0.32  # 🎹 32% dos LEDs (agudos/hi-hat)

# ── CORES: OFFSET DE HUE ──────────────────────────────────────────────────────
# Quanto deslocar a cor em relação à cor do álbum
#
# Valores:
#   0.0   = Mesma cor do álbum
#   0.1   = Levemente diferente
#   0.33  = Cor complementar
#   -0.25 = Direção oposta no círculo cromático
#
# Exemplo com álbum ROXO (hue ~0.75):
#   PERCUSSION -0.15 → Mais pro AZUL
#   BASS        0.00 → ROXO (original)
#   MELODY     +0.15 → Mais pro VERMELHO/ROSA

BAND_HUE_PERCUSSION =  0.00  # 🥁 Desloca pra azul/ciano
BAND_HUE_BASS       =  0.00  # 🎸 Cor ORIGINAL do álbum
BAND_HUE_MELODY     =  0.  # 🎹 Desloca pra vermelho/rosa

# ── SATURAÇÃO ─────────────────────────────────────────────────────────────────
# Quão vívida/forte é a cor (0.0 = cinza, 1.0 = máximo)

BAND_SAT_PERCUSSION = 1.00  # 🥁 Saturação máxima
BAND_SAT_BASS       = 1.00  # 🎸 Saturação máxima
BAND_SAT_MELODY     = 1.00  # 🎹 Saturação máxima

# ── SMOOTHING (SUAVIZAÇÃO) ────────────────────────────────────────────────────
# Controla quão suave são as transições de intensidade
#
# ATTACK: Quão rápido SOBE quando o som aumenta
# DECAY:  Quão rápido DESCE quando o som diminui
#
# Valores maiores = mais rápido/abrupto
# Valores menores = mais lento/suave

BAND_SMOOTHING_ATTACK = 0.25  # ⬆️ Subida (0.1=lento, 0.5=rápido)
BAND_SMOOTHING_DECAY  = 0.06  # ⬇️ Descida (0.03=suave, 0.15=rápido)

# ── BEAT (FLASH NO RITMO) ─────────────────────────────────────────────────────
# Configuração do flash que acontece nos beats

BAND_BEAT_ATTACK      = 0.50  # ⚡ Quão rápido o beat aparece
BAND_BEAT_DECAY       = 0.90  # 📉 Quão devagar some (0.95=lento, 0.8=rápido)
BAND_BEAT_FLASH       = 0.50  # 🔆 Quanto brilho adiciona (0.0-1.0)
BAND_BEAT_COLOR_SHIFT = 0.25  # 🎨 Quanto clareia no beat (0.0-1.0)

# ── VISUAL ────────────────────────────────────────────────────────────────────
# Configurações visuais gerais

BAND_BG_BRIGHTNESS     = 0.08  # 🔆 Brilho mínimo de fundo (sempre aceso)
BAND_INTERNAL_GRADIENT = 0.20  # 🎬 Gradiente DENTRO da zona (centro mais brilhante)
BAND_COLOR_LERP        = 0.18  # 🎬 Interpolação entre frames (suavização)
BAND_ZONE_BLEND_WIDTH  = 1     # 🎬 LEDs de transição entre zonas (0=corte seco)

# ══════════════════════════════════════════════════════════════════════════════
# QUANTIZED (modo alternativo)
# ══════════════════════════════════════════════════════════════════════════════
# Modo com poucos níveis de brilho (menos suave, mais "digital")

QUANTIZED_UPDATE_INTERVAL = 0.30  # Segundos entre atualizações
QUANTIZED_LEVELS = 5              # Número de níveis de brilho


# ══════════════════════════════════════════════════════════════════════════════
# 📚 GUIA RÁPIDO DE AJUSTES
# ══════════════════════════════════════════════════════════════════════════════
#
# 🎨 CORES MUITO PARECIDAS?
#    Aumente a diferença de HUE:
#    BAND_HUE_PERCUSSION = -0.25
#    BAND_HUE_MELODY     =  0.25
#
# ⚡ MUITO EPILÉPTICO?
#    Diminua o smoothing attack e aumente o decay:
#    BAND_SMOOTHING_ATTACK = 0.15
#    BAND_SMOOTHING_DECAY  = 0.04
#
# 😴 MUITO LENTO/MOLE?
#    Aumente o attack:
#    BAND_SMOOTHING_ATTACK = 0.40
#
# 🥁 NÃO VÊ PERCUSSÃO?
#    - Verifique se LED_SKIP_START está certo
#    - Aumente BAND_ZONE_PERCUSSION pra 0.40
#    - Teste com música com bateria forte
#
# 🔆 MUITO ESCURO?
#    Aumente BAND_BG_BRIGHTNESS = 0.15
#    Aumente BRIGHTNESS_FLOOR = 0.25
#
# 🔆 MUITO CLARO?
#    Diminua BAND_BG_BRIGHTNESS = 0.05
#    Diminua BRIGHTNESS_FLOOR = 0.10
#
# ══════════════════════════════════════════════════════════════════════════════