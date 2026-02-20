# audio_spotify_only.py
"""
Captura áudio do Spotify.
Expõe 3 bandas configuráveis + beat + volume.

Bandas:
  🎸 bass       → Graves   (config.BAND_BASS_FREQ)
  🎹 melody     → Médios   (config.BAND_MELODY_FREQ)
  🥁 percussion → Agudos   (config.BAND_PERCUSSION_FREQ)

Inclui:
  - AGC (Automatic Gain Control)
  - Compressor de dinâmica
  - Smoothing adaptativo
  - Floor dinâmico
"""

import time
import threading
import numpy as np
from typing import Optional, Tuple
from collections import deque
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

import config

logger = logging.getLogger(__name__)

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    raise ImportError("pip install pyaudiowpatch")

try:
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    from comtypes import CoInitialize, CoUninitialize
except ImportError:
    raise ImportError("pip install pycaw comtypes")

try:
    import aubio
except ImportError:
    raise ImportError("pip install aubio")


DRUMS_PRESETS = {
    "low":    {"kt": 1.0,  "st": 0.9,  "km": 0.15, "sm": 0.12},
    "medium": {"kt": 0.7,  "st": 0.6,  "km": 0.10, "sm": 0.08},
    "high":   {"kt": 0.45, "st": 0.35, "km": 0.06, "sm": 0.04},
    "ultra":  {"kt": 0.30, "st": 0.25, "km": 0.04, "sm": 0.03},
    "custom": {
        "kt": config.CUSTOM_KICK_THRESHOLD,
        "st": config.CUSTOM_SNARE_THRESHOLD,
        "km": config.CUSTOM_KICK_MINIOI,
        "sm": config.CUSTOM_SNARE_MINIOI,
    },
}

PEAKS_PRESETS = {
    "low":    {"ot": 0.8,  "tr": 2.5},
    "medium": {"ot": 0.5,  "tr": 2.0},
    "high":   {"ot": 0.35, "tr": 1.5},
    "ultra":  {"ot": 0.25, "tr": 1.2},
}


class SpotifyAudioCapture:
    def __init__(self):
        self._meter = None
        self._ok = False

    def init(self) -> bool:
        try:
            CoInitialize()
            for s in AudioUtilities.GetAllSessions():
                if s.Process and "spotify" in s.Process.name().lower():
                    self._meter = s._ctl.QueryInterface(IAudioMeterInformation)
                    self._ok = True
                    logger.info(f"Spotify meter OK (PID={s.Process.pid})")
                    return True
            return False
        except Exception:
            return False

    def peak(self) -> float:
        if not self._ok:
            return 0.0
        try:
            return self._meter.GetPeakValue()
        except Exception:
            self._ok = False
            return 0.0

    def cleanup(self):
        try:
            CoUninitialize()
        except Exception:
            pass


def _find_loopback():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        d = p.get_device_info_by_index(i)
        if d.get("isLoopbackDevice", False):
            r = {"index": i, "name": d["name"],
                 "rate": int(d["defaultSampleRate"]),
                 "channels": min(d["maxInputChannels"], 2)}
            p.terminate()
            return r
    p.terminate()
    return None


# ══════════════════════════════════════════════════════════════════════════════
# AGC (Automatic Gain Control)
# ══════════════════════════════════════════════════════════════════════════════

class AGC:
    """
    Automatic Gain Control.
    
    Ajusta ganho dinamicamente pra manter energia média no nível alvo.
    Em volume baixo: aumenta ganho (até AGC_MAX_GAIN).
    Em volume alto: diminui ganho (até AGC_MIN_GAIN).
    """
    
    def __init__(self):
        self.gain = 1.0
        self.enabled = getattr(config, 'AGC_ENABLED', True)
        self.max_gain = getattr(config, 'AGC_MAX_GAIN', 3.5)
        self.min_gain = getattr(config, 'AGC_MIN_GAIN', 0.8)
        self.attack = getattr(config, 'AGC_ATTACK', 0.03)
        self.release = getattr(config, 'AGC_RELEASE', 0.01)
        self.target = getattr(config, 'AGC_TARGET', 0.35)
        
        # Histórico pra suavizar
        self._energy_hist = deque(maxlen=100)
    
    def process(self, energy: float) -> float:
        """
        Aplica AGC à energia.
        
        Args:
            energy: Energia bruta (0.0-1.0+)
        
        Returns:
            Energia com ganho aplicado
        """
        if not self.enabled:
            return energy
        
        # Acumula histórico
        self._energy_hist.append(energy)
        
        # Calcula energia média recente
        if len(self._energy_hist) < 10:
            return energy
        
        avg_energy = np.mean(self._energy_hist)
        
        # Calcula ganho ideal pra atingir o target
        if avg_energy > 0.001:
            ideal_gain = self.target / avg_energy
        else:
            ideal_gain = self.max_gain
        
        # Clamp
        ideal_gain = max(self.min_gain, min(self.max_gain, ideal_gain))
        
        # Suaviza transição (attack/release assimétrico)
        if ideal_gain > self.gain:
            # Aumentando ganho (volume caiu) → mais lento
            self.gain += (ideal_gain - self.gain) * self.release
        else:
            # Diminuindo ganho (volume subiu) → mais rápido
            self.gain += (ideal_gain - self.gain) * self.attack
        
        # Aplica ganho
        return energy * self.gain
    
    def get_gain(self) -> float:
        """Retorna ganho atual (pra debug/GUI)."""
        return self.gain


# ══════════════════════════════════════════════════════════════════════════════
# COMPRESSOR DE DINÂMICA
# ══════════════════════════════════════════════════════════════════════════════

class DynamicsCompressor:
    """
    Compressor de dinâmica com soft knee.
    
    Reduz a diferença entre sons baixos e altos.
    Essencial pra volume baixo não ficar "binário" (0 ou 100).
    """
    
    def __init__(self):
        self.threshold = getattr(config, 'COMPRESSOR_THRESHOLD', 0.25)
        self.ratio = getattr(config, 'COMPRESSOR_RATIO', 2.5)
        self.knee = getattr(config, 'COMPRESSOR_KNEE', 0.15)
        self.makeup = getattr(config, 'COMPRESSOR_MAKEUP', 1.4)
        self.enabled = getattr(config, 'BAND_COMPRESSION_ENABLED', True)
    
    def process(self, value: float) -> float:
        """
        Aplica compressão.
        
        Args:
            value: Valor de entrada (0.0-1.0+)
        
        Returns:
            Valor comprimido
        """
        if not self.enabled or value <= 0:
            return value
        
        # ── Soft Knee ──
        # Região de transição suave em torno do threshold
        knee_start = self.threshold - self.knee
        knee_end = self.threshold + self.knee
        
        if value < knee_start:
            # Abaixo do knee: sem compressão
            compressed = value
        
        elif value > knee_end:
            # Acima do knee: compressão total
            excess = value - self.threshold
            compressed = self.threshold + (excess / self.ratio)
        
        else:
            # Dentro do knee: transição suave (interpolação quadrática)
            # Quanto mais perto do threshold, mais compressão
            knee_range = knee_end - knee_start
            knee_pos = (value - knee_start) / knee_range  # 0-1 dentro do knee
            
            # Ratio efetivo: interpola de 1.0 (sem compressão) até ratio
            effective_ratio = 1.0 + (self.ratio - 1.0) * (knee_pos ** 2)
            
            excess = value - knee_start
            compressed = knee_start + (excess / effective_ratio)
        
        # ── Makeup Gain ──
        # Compensa a redução de volume
        result = compressed * self.makeup
        
        return min(1.0, result)


# ══════════════════════════════════════════════════════════════════════════════
# SMOOTHING ADAPTATIVO
# ══════════════════════════════════════════════════════════════════════════════

class AdaptiveSmoother:
    """
    Smoother com decay adaptativo ao volume.
    
    Em volume baixo: decay mais lento (segura o brilho).
    Em volume alto: decay normal (responsivo).
    """
    
    def __init__(self, attack: float = 0.45, decay: float = 0.08):
        self.base_attack = attack
        self.base_decay = decay
        self.value = 0.0
        
        self.adaptive = getattr(config, 'ADAPTIVE_SMOOTHING', True)
        self.low_vol_mult = getattr(config, 'SMOOTHING_LOW_VOL_MULT', 2.5)
        self.low_vol_thresh = getattr(config, 'SMOOTHING_LOW_VOL_THRESH', 0.35)
    
    def update(self, target: float, volume: float = 1.0) -> float:
        """
        Atualiza valor suavizado.
        
        Args:
            target: Valor alvo
            volume: Volume atual (0-1) pra adaptar decay
        
        Returns:
            Valor suavizado
        """
        # Calcula decay adaptativo
        if self.adaptive and volume < self.low_vol_thresh:
            # Volume baixo → decay mais lento
            # Quanto menor o volume, mais lento
            vol_factor = volume / self.low_vol_thresh  # 0-1
            decay_mult = 1.0 + (self.low_vol_mult - 1.0) * (1.0 - vol_factor)
            decay = self.base_decay / decay_mult
        else:
            decay = self.base_decay
        
        # Aplica smoothing assimétrico
        if target > self.value:
            self.value += (target - self.value) * self.base_attack
        else:
            self.value += (target - self.value) * decay
        
        return self.value
    
    def reset(self):
        self.value = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# FLOOR DINÂMICO
# ══════════════════════════════════════════════════════════════════════════════

class DynamicFloor:
    """
    Floor dinâmico baseado no volume.
    
    Quando volume está baixo, o floor sobe.
    Evita LEDs completamente apagados.
    """
    
    def __init__(self):
        self.enabled = getattr(config, 'DYNAMIC_FLOOR_ENABLED', True)
        self.max_floor = getattr(config, 'DYNAMIC_FLOOR_MAX', 0.15)
        self.thresh = getattr(config, 'DYNAMIC_FLOOR_THRESH', 0.30)
        self._current_floor = 0.0
    
    def get_floor(self, volume: float) -> float:
        """
        Calcula floor dinâmico baseado no volume.
        
        Args:
            volume: Volume atual (0-1)
        
        Returns:
            Floor a ser aplicado (0.0 - max_floor)
        """
        if not self.enabled:
            return 0.0
        
        if volume >= self.thresh:
            target_floor = 0.0
        else:
            # Quanto menor o volume, maior o floor
            # Interpolação linear
            vol_factor = volume / self.thresh  # 0-1
            target_floor = self.max_floor * (1.0 - vol_factor)
        
        # Suaviza transição
        self._current_floor += (target_floor - self._current_floor) * 0.1
        
        return self._current_floor
    
    def apply(self, value: float, volume: float) -> float:
        """
        Aplica floor dinâmico ao valor.
        
        Args:
            value: Valor da banda (0-1)
            volume: Volume atual (0-1)
        
        Returns:
            Valor com floor aplicado
        """
        floor = self.get_floor(volume)
        
        if value < floor:
            # Abaixo do floor: levanta suavemente
            # Não sobe direto pro floor, usa blend
            return floor * 0.7 + value * 0.3
        
        return value


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class AudioReactiveSpotifyOnly:
    """
    Captura áudio do Spotify e expõe métricas reativas.

    Properties:
      .state              → "idle"/"kick"/"snare"/"peak"
      .volume_normalized  → 0-1 volume geral
      .energy             → 0-1 energia suavizada
      .spectral_flux      → 0-1 mudança espectral
      .beat_intensity     → 0-1 força do beat (decai)
      .bass               → 0-1 🎸 graves
      .melody             → 0-1 🎹 médios
      .percussion         → 0-1 🥁 agudos
      .mid                → alias de melody
      .high               → alias de percussion
      .agc_gain           → ganho atual do AGC (debug)
    """

    def __init__(self, hold_time=0.18):
        self._state = "idle"
        self._intensity = 0.0
        self._volume = 0.0
        self._vnorm = 0.0
        self._energy = 0.0
        self._spectral_flux = 0.0
        self._beat_intensity = 0.0

        # ── Bandas por instrumento ──
        self._bass = 0.0
        self._melody = 0.0
        self._percussion = 0.0

        self._hold_time = hold_time
        self._peak_hold = config.PEAK_HOLD_TIME
        self._last_hit = 0.0
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._spotify = SpotifyAudioCapture()
        self._mode = config.DETECTION_MODE.lower()
        
        # ── Processadores (Coisa 2) ──
        self._agc = AGC()
        self._compressor = DynamicsCompressor()
        self._dynamic_floor = DynamicFloor()
        
        # Smoothers adaptativos (um por banda)
        sm_attack = getattr(config, 'BAND_ATTACK', 0.45)
        sm_decay = getattr(config, 'BAND_DECAY', 0.08)
        self._smoother_perc = AdaptiveSmoother(sm_attack, sm_decay)
        self._smoother_bass = AdaptiveSmoother(sm_attack, sm_decay)
        self._smoother_mel = AdaptiveSmoother(sm_attack, sm_decay)

    # ─────────────────────────────────────────────
    # PROPERTIES
    # ─────────────────────────────────────────────

    @property
    def state(self) -> str:
        with self._lock:
            if self._state != "idle":
                h = self._peak_hold if self._state == "peak" else self._hold_time
                if time.perf_counter() - self._last_hit > h:
                    self._state = "idle"
            return self._state

    @property
    def intensity(self) -> float:
        with self._lock:
            return self._intensity

    @property
    def volume_normalized(self) -> float:
        with self._lock:
            return self._vnorm

    @property
    def energy(self) -> float:
        with self._lock:
            return self._energy

    @property
    def spectral_flux(self) -> float:
        with self._lock:
            return self._spectral_flux

    @property
    def is_beat(self) -> bool:
        with self._lock:
            return self._state in ("kick", "snare")

    @property
    def beat_intensity(self) -> float:
        with self._lock:
            return self._beat_intensity

    @property
    def bass(self) -> float:
        """🎸 Energia graves (BAND_BASS_FREQ)."""
        with self._lock:
            return self._bass

    @property
    def melody(self) -> float:
        """🎹 Energia médios (BAND_MELODY_FREQ)."""
        with self._lock:
            return self._melody

    @property
    def percussion(self) -> float:
        """🥁 Energia agudos (BAND_PERCUSSION_FREQ)."""
        with self._lock:
            return self._percussion

    @property
    def mid(self) -> float:
        """Alias de melody (backward compat)."""
        return self.melody

    @property
    def high(self) -> float:
        """Alias de percussion (backward compat)."""
        return self.percussion

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def agc_gain(self) -> float:
        """Ganho atual do AGC (pra debug/GUI)."""
        return self._agc.get_gain()

    # ─────────────────────────────────────────────
    # AUDIO LOOP
    # ─────────────────────────────────────────────

    def _loop(self, dev):
        spotify_ok = self._spotify.init()

        p = pyaudio.PyAudio()
        sr = dev["rate"]
        ch = dev["channels"]
        WIN, HOP = 1024, 512

        stream = p.open(
            format=pyaudio.paFloat32, channels=ch, rate=sr,
            input=True, input_device_index=dev["index"],
            frames_per_buffer=HOP,
        )

        # ══════════════════════════════════════════════════
        # DRUMS DETECTION (aubio)
        # ══════════════════════════════════════════════════
        ds = DRUMS_PRESETS.get(config.SENSITIVITY.lower(), DRUMS_PRESETS["high"])
        kick_o = aubio.onset("energy", WIN, HOP, sr)
        kick_o.set_threshold(ds["kt"])
        kick_o.set_minioi_s(ds["km"])
        snare_o = aubio.onset("hfc", WIN, HOP, sr)
        snare_o.set_threshold(ds["st"])
        snare_o.set_minioi_s(ds["sm"])

        freqs = np.fft.rfftfreq(HOP, 1.0 / sr)
        kick_det_mask = (freqs >= 40) & (freqs <= 150)
        snare_det_mask = (freqs >= 200) & (freqs <= 2000)
        kick_hist = deque(maxlen=50)
        snare_hist = deque(maxlen=50)

        # ══════════════════════════════════════════════════
        # 🎯 MÁSCARAS DE INSTRUMENTO (WEIGHTED)
        # ══════════════════════════════════════════════════
        n_bins = len(freqs)
        w_perc = np.zeros(n_bins, dtype=np.float32)
        w_bass = np.zeros(n_bins, dtype=np.float32)
        w_mel  = np.zeros(n_bins, dtype=np.float32)

        for i, f in enumerate(freqs):
            # 🥁 PERCUSSÃO
            if 40 <= f < 60:      w_perc[i] += 0.5
            elif 60 <= f <= 100:  w_perc[i] += 1.0
            elif 100 < f <= 200:  w_perc[i] += 0.4
            if 150 <= f <= 300:   w_perc[i] += 0.6
            if 2000 <= f <= 4000: w_perc[i] += 0.9
            if 5000 <= f <= 10000: w_perc[i] += 1.0
            if 10000 < f <= 14000: w_perc[i] += 0.4

            # 🎸 BAIXO
            if 40 <= f < 60:      w_bass[i] += 0.3
            if 60 <= f <= 100:    w_bass[i] += 0.5
            if 100 < f <= 250:    w_bass[i] += 1.0
            if 250 < f <= 500:    w_bass[i] += 0.5
            if 500 < f <= 1000:   w_bass[i] += 0.2

            # 🎹 MELODIA
            if 200 <= f <= 500:    w_mel[i] += 0.3
            if 500 < f <= 1000:    w_mel[i] += 0.6
            if 1000 < f <= 2000:   w_mel[i] += 0.9
            if 2000 < f <= 4000:   w_mel[i] += 1.0
            if 4000 < f <= 6000:   w_mel[i] += 0.7
            if 6000 < f <= 8000:   w_mel[i] += 0.5
            if 8000 < f <= 10000:  w_mel[i] += 0.3

        # ── SUBTRAI SOBREPOSIÇÃO ──
        for i, f in enumerate(freqs):
            if 60 <= f <= 100:
                w_bass[i] *= 0.3
            if 150 <= f <= 300:
                w_bass[i] *= 0.4
            if 2000 <= f <= 4000:
                w_mel[i] *= 0.5

        # Normaliza
        w_perc_sum = np.sum(w_perc) + 0.001
        w_bass_sum = np.sum(w_bass) + 0.001
        w_mel_sum  = np.sum(w_mel)  + 0.001
        w_perc_n = w_perc / w_perc_sum
        w_bass_n = w_bass / w_bass_sum
        w_mel_n  = w_mel  / w_mel_sum

        # ══════════════════════════════════════════════════
        # CONFIGURAÇÕES
        # ══════════════════════════════════════════════════
        boost_perc = getattr(config, 'BAND_BOOST_PERCUSSION', 1.0)
        boost_bass = getattr(config, 'BAND_BOOST_BASS', 2.0)
        boost_mel  = getattr(config, 'BAND_BOOST_MELODY', 1.8)

        exp_perc = getattr(config, 'BAND_EXPANSION_PERCUSSION', 1.8)
        exp_bass = getattr(config, 'BAND_EXPANSION_BASS', 2.0)
        exp_mel  = getattr(config, 'BAND_EXPANSION_MELODY', 1.8)

        floor_perc = getattr(config, 'BAND_FLOOR_PERCUSSION', 0.02)
        floor_bass = getattr(config, 'BAND_FLOOR_BASS', 0.02)
        floor_mel  = getattr(config, 'BAND_FLOOR_MELODY', 0.02)

        ceil_perc = getattr(config, 'BAND_CEILING_PERCUSSION', 1.3)
        ceil_bass = getattr(config, 'BAND_CEILING_BASS', 1.4)
        ceil_mel  = getattr(config, 'BAND_CEILING_MELODY', 1.3)

        response_curve = getattr(config, 'BAND_RESPONSE_CURVE', 'exponential')

        # ══════════════════════════════════════════════════
        # FUNÇÕES DE PROCESSAMENTO
        # ══════════════════════════════════════════════════
        def apply_curve(val, curve_type):
            val = max(0.0, min(1.0, val))
            if curve_type == "exponential":
                return val ** 0.6
            elif curve_type == "logarithmic":
                return float(np.log1p(val * 9) / np.log(10)) if val > 0 else 0.0
            elif curve_type == "scurve":
                return val * val * (3 - 2 * val)
            return val

        def apply_expansion(val, expansion, floor_val, ceil_val):
            if expansion != 1.0 and expansion > 0:
                expanded = val ** (1.0 / expansion)
            else:
                expanded = val
            if expanded < floor_val:
                expanded = floor_val * (expanded / max(0.001, floor_val))
            return min(ceil_val, expanded)

        # ══════════════════════════════════════════════════
        # NORMALIZAÇÃO GLOBAL
        # ══════════════════════════════════════════════════
        global_energy_hist = deque(maxlen=200)
        noise_floor = 0.008

        # ══════════════════════════════════════════════════
        # PEAKS DETECTION
        # ══════════════════════════════════════════════════
        ps = PEAKS_PRESETS.get(config.PEAKS_SENSITIVITY.lower(), PEAKS_PRESETS["high"])
        peak_o = aubio.onset("default", WIN, HOP, sr)
        peak_o.set_threshold(ps["ot"])
        peak_o.set_minioi_s(config.PEAK_MIN_INTERVAL)
        peak_o2 = aubio.onset("complex", WIN, HOP, sr)
        peak_o2.set_threshold(ps["ot"] * 1.2)
        peak_o2.set_minioi_s(config.PEAK_MIN_INTERVAL)
        peak_ehist = deque(maxlen=40)
        peak_last_e = 0.0

        # ══════════════════════════════════════════════════
        # VOLUME / ENERGY
        # ══════════════════════════════════════════════════
        rms_hist = deque(maxlen=200)
        vol_smooth = 0.0
        vnorm_smooth = 0.0
        energy_smooth = 0.0
        last_spectrum = None
        flux_smooth = 0.0
        beat_intensity = 0.0

        # ══════════════════════════════════════════════════
        # LOG
        # ══════════════════════════════════════════════════
        agc_status = "ON" if self._agc.enabled else "OFF"
        comp_status = "ON" if self._compressor.enabled else "OFF"
        adapt_status = "ON" if getattr(config, 'ADAPTIVE_SMOOTHING', True) else "OFF"
        floor_status = "ON" if self._dynamic_floor.enabled else "OFF"
        
        logger.info(
            f"Audio ON: {dev['name']} | mode={self._mode}\n"
            f"  🥁 Percussion: boost={boost_perc:.1f} exp={exp_perc:.1f}\n"
            f"  🎸 Bass:       boost={boost_bass:.1f} exp={exp_bass:.1f}\n"
            f"  🎹 Melody:     boost={boost_mel:.1f} exp={exp_mel:.1f}\n"
            f"  Curve: {response_curve}\n"
            f"  === LOW VOLUME FIXES ===\n"
            f"  AGC: {agc_status} (max_gain={self._agc.max_gain:.1f})\n"
            f"  Compressor: {comp_status} (thresh={self._compressor.threshold:.2f} ratio={self._compressor.ratio:.1f})\n"
            f"  Adaptive Smoothing: {adapt_status}\n"
            f"  Dynamic Floor: {floor_status} (max={self._dynamic_floor.max_floor:.2f})"
        )

        # ══════════════════════════════════════════════════
        # MAIN LOOP
        # ══════════════════════════════════════════════════
        try:
            while self._running:
                try:
                    data = stream.read(HOP, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.01)
                    continue

                # Filtra silêncio do Spotify
                if spotify_ok and self._spotify.peak() < 0.01:
                    with self._lock:
                        self._volume = 0.0
                        self._vnorm = 0.0
                        self._energy *= 0.90
                        self._spectral_flux *= 0.85
                        self._beat_intensity *= 0.80
                        self._bass *= 0.85
                        self._melody *= 0.85
                        self._percussion *= 0.85
                    continue

                audio = np.frombuffer(data, dtype=np.float32).copy()
                if ch == 2:
                    audio = audio.reshape(-1, 2).mean(axis=1).astype(np.float32)
                if len(audio) != HOP:
                    continue

                rms = float(np.sqrt(np.mean(audio ** 2)))
                rms_hist.append(rms)
                rms_max = max(rms_hist) if rms_hist else rms

                if rms < 0.003:
                    with self._lock:
                        self._volume *= 0.85
                        self._vnorm *= 0.85
                        self._energy *= 0.90
                        self._spectral_flux *= 0.85
                        self._beat_intensity *= 0.80
                        self._bass *= 0.85
                        self._melody *= 0.85
                        self._percussion *= 0.85
                    continue

                # ══ VOLUME ══
                vol_raw = min(1.0, rms / 0.10)
                vol_smooth += (vol_raw - vol_smooth) * 0.30

                vnorm_raw = min(1.0, rms / rms_max) if rms_max > 0.001 else 0.0
                vnorm_smooth += (vnorm_raw - vnorm_smooth) * 0.35

                # ══ ENERGY ══
                energy_raw = min(1.0, rms / 0.07)
                energy_smooth += (energy_raw - energy_smooth) * 0.20

                # ══ FFT ══
                spectrum = np.abs(np.fft.rfft(audio))

                # ══ SPECTRAL FLUX ══
                if last_spectrum is not None and len(spectrum) == len(last_spectrum):
                    diff = spectrum - last_spectrum
                    flux_raw = float(np.sum(np.maximum(0, diff)))
                    spec_max = float(np.max(spectrum)) + 0.001
                    flux_raw = min(1.0, flux_raw / (spec_max * 8))
                else:
                    flux_raw = 0.0
                last_spectrum = spectrum.copy()
                flux_smooth += (flux_raw - flux_smooth) * 0.25

                # ══════════════════════════════════════════
                # 🎯 ENERGIA POR BANDA (weighted RMS)
                # ══════════════════════════════════════════
                spec_sq = spectrum ** 2

                perc_raw = float(np.sqrt(np.sum(spec_sq * w_perc_n)))
                bass_raw = float(np.sqrt(np.sum(spec_sq * w_bass_n)))
                mel_raw  = float(np.sqrt(np.sum(spec_sq * w_mel_n)))

                # ══════════════════════════════════════════
                # 🔑 AGC — NORMALIZAÇÃO ADAPTATIVA
                # ══════════════════════════════════════════
                # Aplica AGC à energia máxima das bandas
                max_band = max(perc_raw, bass_raw, mel_raw, 0.001)
                global_energy_hist.append(max_band)

                # Calcula referência global
                if len(global_energy_hist) > 30:
                    global_ref = float(np.percentile(list(global_energy_hist), 90)) + 0.001
                else:
                    global_ref = max(global_energy_hist) + 0.001

                # AGC ajusta a referência baseado no volume
                agc_adjusted_ref = global_ref / max(0.3, self._agc.gain)
                
                # Atualiza AGC com energia atual
                self._agc.process(energy_smooth)

                # Normaliza TODAS pelo MESMO denominador (ajustado pelo AGC)
                perc_norm = perc_raw / agc_adjusted_ref
                bass_norm = bass_raw / agc_adjusted_ref
                mel_norm  = mel_raw  / agc_adjusted_ref

                # ── Aplica noise floor ──
                if perc_raw < noise_floor:
                    perc_norm = 0.0
                if bass_raw < noise_floor:
                    bass_norm = 0.0
                if mel_raw < noise_floor:
                    mel_norm = 0.0

                # Clamp
                perc_norm = min(1.0, perc_norm)
                bass_norm = min(1.0, bass_norm)
                mel_norm  = min(1.0, mel_norm)

                # ══ PIPELINE ══
                # 1. Curva de resposta
                perc_curved = apply_curve(perc_norm, response_curve)
                bass_curved = apply_curve(bass_norm, response_curve)
                mel_curved  = apply_curve(mel_norm,  response_curve)

                # 2. Boost
                perc_boosted = perc_curved * boost_perc
                bass_boosted = bass_curved * boost_bass
                mel_boosted  = mel_curved  * boost_mel

                # 3. Expansão
                perc_expanded = apply_expansion(perc_boosted, exp_perc, floor_perc, ceil_perc)
                bass_expanded = apply_expansion(bass_boosted, exp_bass, floor_bass, ceil_bass)
                mel_expanded  = apply_expansion(mel_boosted,  exp_mel,  floor_mel,  ceil_mel)

                # ══════════════════════════════════════════
                # 🔑 COMPRESSOR DE DINÂMICA
                # ══════════════════════════════════════════
                perc_compressed = self._compressor.process(perc_expanded)
                bass_compressed = self._compressor.process(bass_expanded)
                mel_compressed  = self._compressor.process(mel_expanded)

                # Clamp final
                perc_final = min(1.0, perc_compressed)
                bass_final = min(1.0, bass_compressed)
                mel_final  = min(1.0, mel_compressed)

                # ══════════════════════════════════════════
                # 🔑 SMOOTHING ADAPTATIVO
                # ══════════════════════════════════════════
                # Passa o volume pra adaptar o decay
                perc_sm = self._smoother_perc.update(perc_final, vnorm_smooth)
                bass_sm = self._smoother_bass.update(bass_final, vnorm_smooth)
                mel_sm  = self._smoother_mel.update(mel_final, vnorm_smooth)

                # ══════════════════════════════════════════
                # 🔑 FLOOR DINÂMICO
                # ══════════════════════════════════════════
                perc_floored = self._dynamic_floor.apply(perc_sm, vnorm_smooth)
                bass_floored = self._dynamic_floor.apply(bass_sm, vnorm_smooth)
                mel_floored  = self._dynamic_floor.apply(mel_sm, vnorm_smooth)

                # ══ ONSET DETECTION ══
                if rms_max > 0.001:
                    audio_n = np.clip(audio / (rms_max * 2), -1, 1).astype(np.float32)
                else:
                    audio_n = audio

                now = time.perf_counter()
                det = None
                det_i = 0.0

                # ══ PEAKS ══
                if self._mode in ("peaks", "both"):
                    e = float(np.sqrt(np.mean(audio_n ** 2)))
                    peak_ehist.append(e)
                    avg_e = np.mean(peak_ehist)
                    max_e = max(peak_ehist)
                    trans = abs(e - peak_last_e)
                    peak_last_e = e

                    if e > 0.02:
                        hit = (
                            bool(peak_o(audio_n))
                            or bool(peak_o2(audio_n))
                            or (avg_e > 0.01 and e / avg_e > 1.4)
                            or (avg_e > 0.01 and trans > avg_e * ps["tr"])
                        )
                        if hit:
                            det = "peak"
                            det_i = max(0.4, min(1.0, e / max_e)) if max_e > 0.01 else 0.5

                # ══ DRUMS ══
                if self._mode in ("drums", "both"):
                    fft_complex = np.fft.rfft(audio_n)
                    mag = np.abs(fft_complex)

                    ke = float(np.mean(mag[kick_det_mask]))
                    se = float(np.mean(mag[snare_det_mask]))
                    kick_hist.append(ke)
                    snare_hist.append(se)

                    kf = np.zeros_like(fft_complex)
                    kf[kick_det_mask] = fft_complex[kick_det_mask]
                    ka = np.fft.irfft(kf, HOP).astype(np.float32)

                    sf = np.zeros_like(fft_complex)
                    sf[snare_det_mask] = fft_complex[snare_det_mask]
                    sa = np.fft.irfft(sf, HOP).astype(np.float32)

                    km = max(kick_hist) if kick_hist else ke
                    sm = max(snare_hist) if snare_hist else se

                    kick = bool(kick_o(ka)) and ke > km * 0.15
                    snare = bool(snare_o(sa)) and se > sm * 0.10

                    if snare:
                        det = "snare"
                        det_i = 1.0
                    elif kick and det != "snare":
                        if det_i < 0.8:
                            det = "kick"
                            det_i = max(det_i, 0.7)

                # ══ BEAT DECAY ══
                if det in ("kick", "snare"):
                    beat_intensity = det_i
                else:
                    beat_intensity *= config.CHASE_FLASH_DECAY
                    if beat_intensity < 0.02:
                        beat_intensity = 0.0

                # ══ APLICA TUDO ══
                with self._lock:
                    self._volume = vol_smooth
                    self._vnorm = vnorm_smooth
                    self._energy = energy_smooth
                    self._spectral_flux = flux_smooth
                    self._beat_intensity = beat_intensity
                    self._bass = bass_floored
                    self._melody = mel_floored
                    self._percussion = perc_floored

                    if det:
                        if det == "snare":
                            self._state = "snare"
                            self._intensity = 1.0
                        elif det == "kick" and self._state != "snare":
                            self._state = "kick"
                            self._intensity = max(self._intensity, 0.7)
                        elif det == "peak" and self._state not in ("snare", "kick"):
                            self._state = "peak"
                            self._intensity = max(self._intensity, det_i)
                        self._last_hit = now

        except Exception as e:
            logger.error(f"Erro: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            self._spotify.cleanup()
            self._running = False

    def start(self) -> bool:
        if self._running:
            return True
        d = _find_loopback()
        if not d:
            return False
        self._running = True
        self._thread = threading.Thread(target=self._loop, args=(d,), daemon=True)
        self._thread.start()
        time.sleep(0.5)
        return self._running

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)


# ══════════════════════════════════════════════════
# TESTE STANDALONE
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\n  🎸🎹🥁 Teste Audio Bands (com AGC/Compressor)")
    print(f"  AGC: {'ON' if getattr(config, 'AGC_ENABLED', True) else 'OFF'}")
    print(f"  Compressor: {'ON' if getattr(config, 'BAND_COMPRESSION_ENABLED', True) else 'OFF'}")
    print(f"  Adaptive Smoothing: {'ON' if getattr(config, 'ADAPTIVE_SMOOTHING', True) else 'OFF'}")
    print(f"  Dynamic Floor: {'ON' if getattr(config, 'DYNAMIC_FLOOR_ENABLED', True) else 'OFF'}")
    print(f"  Ctrl+C pra sair\n")

    ar = AudioReactiveSpotifyOnly(hold_time=config.HIT_HOLD_TIME)
    if not ar.start():
        exit(1)

    kicks = snares = 0
    prev = "idle"

    try:
        while True:
            s  = ar.state
            v  = ar.volume_normalized
            ba = ar.bass
            me = ar.melody
            pe = ar.percussion
            bi = ar.beat_intensity
            gain = ar.agc_gain

            if s != prev:
                if s == "kick": kicks += 1
                elif s == "snare": snares += 1
                prev = s

            bar_v  = "█" * int(v * 10)  + "░" * (10 - int(v * 10))
            bar_ba = "█" * int(ba * 8)  + "░" * (8 - int(ba * 8))
            bar_me = "█" * int(me * 8)  + "░" * (8 - int(me * 8))
            bar_pe = "█" * int(pe * 8)  + "░" * (8 - int(pe * 8))
            bar_bi = "█" * int(bi * 6)  + "░" * (6 - int(bi * 6))

            hit = {"snare": "SNARE!", "kick": "kick", "peak": "PEAK"}.get(s, "")

            print(
                f"\r  V[{bar_v}] 🎸[{bar_ba}] 🎹[{bar_me}] 🥁[{bar_pe}] "
                f"Beat[{bar_bi}] AGC:{gain:.1f}x K:{kicks} S:{snares} {hit:8}",
                end="", flush=True,
            )
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\n\n  Total: {kicks} kicks, {snares} snares")

    ar.stop()
    print("  ✅ Done!")