# audio_reactive.py
"""
Captura áudio do sistema e detecta kick/snare via aubio.
Sensibilidade configurável via config.py.

Dependências: pip install pyaudiowpatch aubio numpy
"""

import logging
import threading
import time
from typing import Optional

import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

import config

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════
# PRESETS DE SENSIBILIDADE
# ══════════════════════════════════════════════════

SENSITIVITY_PRESETS = {
    "low": {
        "kick_threshold": 1.0,
        "snare_threshold": 0.9,
        "kick_min_energy": 0.020,
        "snare_min_energy": 0.015,
        "kick_minioi": 0.15,
        "snare_minioi": 0.12,
    },
    "medium": {
        "kick_threshold": 0.7,
        "snare_threshold": 0.6,
        "kick_min_energy": 0.012,
        "snare_min_energy": 0.008,
        "kick_minioi": 0.10,
        "snare_minioi": 0.08,
    },
    "high": {
        "kick_threshold": 0.45,
        "snare_threshold": 0.35,
        "kick_min_energy": 0.006,
        "snare_min_energy": 0.004,
        "kick_minioi": 0.06,
        "snare_minioi": 0.04,
    },
    "custom": {
        "kick_threshold": config.CUSTOM_KICK_THRESHOLD,
        "snare_threshold": config.CUSTOM_SNARE_THRESHOLD,
        "kick_min_energy": config.CUSTOM_KICK_MIN_ENERGY,
        "snare_min_energy": config.CUSTOM_SNARE_MIN_ENERGY,
        "kick_minioi": config.CUSTOM_KICK_MINIOI,
        "snare_minioi": config.CUSTOM_SNARE_MINIOI,
    },
}


def _get_sensitivity():
    """Pega preset de sensibilidade do config."""
    preset = config.SENSITIVITY.lower()
    if preset in SENSITIVITY_PRESETS:
        return SENSITIVITY_PRESETS[preset]
    logger.warning(f"Sensibilidade '{preset}' desconhecida, usando 'medium'")
    return SENSITIVITY_PRESETS["medium"]


def _find_loopback():
    try:
        import pyaudiowpatch as pyaudio
    except ImportError:
        logger.error("pyaudiowpatch não instalado")
        return None

    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev.get("isLoopbackDevice", False):
            logger.info(f"Loopback: [{i}] {dev['name']}")
            p.terminate()
            return {
                "index": i,
                "name": dev["name"],
                "rate": int(dev["defaultSampleRate"]),
                "channels": min(dev["maxInputChannels"], 2),
            }

    p.terminate()
    return None


class AudioReactive:

    def __init__(self, hold_time: float = 0.25):
        self._state = "idle"
        self._volume = 0.0
        self._hold_time = hold_time
        self._last_hit_time = 0.0
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    @property
    def state(self) -> str:
        with self._lock:
            if self._state != "idle":
                if time.perf_counter() - self._last_hit_time > self._hold_time:
                    self._state = "idle"
            return self._state

    @property
    def volume(self) -> float:
        with self._lock:
            return self._volume

    @property
    def is_running(self) -> bool:
        return self._running

    def _processing_loop(self, dev_info: dict):
        try:
            import pyaudiowpatch as pyaudio
            import aubio
        except ImportError as e:
            logger.error(f"Dependência: {e}")
            self._running = False
            return

        # Pega sensibilidade
        sens = _get_sensitivity()

        logger.info(f"Sensibilidade: {config.SENSITIVITY}")
        logger.info(f"  Kick:  threshold={sens['kick_threshold']}, "
                     f"min_energy={sens['kick_min_energy']}, "
                     f"minioi={sens['kick_minioi']}s")
        logger.info(f"  Snare: threshold={sens['snare_threshold']}, "
                     f"min_energy={sens['snare_min_energy']}, "
                     f"minioi={sens['snare_minioi']}s")

        p = pyaudio.PyAudio()
        sample_rate = dev_info["rate"]
        channels = dev_info["channels"]

        WIN_SIZE = 1024
        HOP_SIZE = 512

        stream = p.open(
            format=pyaudio.paFloat32,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=dev_info["index"],
            frames_per_buffer=HOP_SIZE,
        )

        # Configura aubio com sensibilidade
        kick_onset = aubio.onset("energy", WIN_SIZE, HOP_SIZE, sample_rate)
        kick_onset.set_threshold(sens["kick_threshold"])
        kick_onset.set_minioi_s(sens["kick_minioi"])

        snare_onset = aubio.onset("hfc", WIN_SIZE, HOP_SIZE, sample_rate)
        snare_onset.set_threshold(sens["snare_threshold"])
        snare_onset.set_minioi_s(sens["snare_minioi"])

        KICK_MIN_ENERGY = sens["kick_min_energy"]
        SNARE_MIN_ENERGY = sens["snare_min_energy"]
        SILENCE_THRESHOLD = 0.003

        freqs = np.fft.rfftfreq(HOP_SIZE, 1.0 / sample_rate)
        kick_mask = (freqs >= 40) & (freqs <= 150)
        snare_mask = (freqs >= 200) & (freqs <= 2000)

        volume_smooth = 0.0

        logger.info(f"Audio reativo ON: {dev_info['name']} @ {sample_rate}Hz")

        try:
            while self._running:
                try:
                    data = stream.read(HOP_SIZE, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.01)
                    continue

                audio = np.frombuffer(data, dtype=np.float32).copy()

                if channels == 2:
                    audio = audio.reshape(-1, 2).mean(axis=1).astype(np.float32)

                if len(audio) != HOP_SIZE:
                    continue

                rms = float(np.sqrt(np.mean(audio ** 2)))
                is_silence = rms < SILENCE_THRESHOLD

                volume_raw = 0.0 if is_silence else min(1.0, rms / 0.12)
                volume_smooth += (volume_raw - volume_smooth) * 0.1

                with self._lock:
                    self._volume = volume_smooth

                if is_silence:
                    continue

                fft = np.fft.rfft(audio)
                fft_mag = np.abs(fft)

                kick_energy = float(np.mean(fft_mag[kick_mask]))
                snare_energy = float(np.mean(fft_mag[snare_mask]))

                kick_fft = np.zeros_like(fft)
                kick_fft[kick_mask] = fft[kick_mask]
                kick_audio = np.fft.irfft(kick_fft, HOP_SIZE).astype(np.float32)

                snare_fft = np.zeros_like(fft)
                snare_fft[snare_mask] = fft[snare_mask]
                snare_audio = np.fft.irfft(snare_fft, HOP_SIZE).astype(np.float32)

                now = time.perf_counter()

                if snare_onset(snare_audio) and snare_energy >= SNARE_MIN_ENERGY:
                    with self._lock:
                        self._state = "snare"
                        self._last_hit_time = now

                elif kick_onset(kick_audio) and kick_energy >= KICK_MIN_ENERGY:
                    with self._lock:
                        if self._state != "snare" or now - self._last_hit_time > self._hold_time:
                            self._state = "kick"
                            self._last_hit_time = now

        except Exception as e:
            logger.error(f"Erro no audio loop: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            self._running = False

    def start(self) -> bool:
        if self._running:
            return True

        dev_info = _find_loopback()
        if dev_info is None:
            logger.error("Loopback não encontrado.")
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._processing_loop,
            args=(dev_info,),
            daemon=True,
        )
        self._thread.start()
        time.sleep(0.3)
        return self._running

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        with self._lock:
            self._state = "idle"
            self._volume = 0.0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print(f"\n  🥁 Teste Audio Reactive")
    print(f"  Sensibilidade: {config.SENSITIVITY}")
    print(f"  Ctrl+C pra sair\n")

    ar = AudioReactive(hold_time=config.HIT_HOLD_TIME)
    if not ar.start():
        print("  ❌ Falhou")
        exit(1)

    kick_count = 0
    snare_count = 0
    prev_state = "idle"

    try:
        while True:
            s = ar.state
            v = ar.volume

            if s != prev_state:
                if s == "kick":
                    kick_count += 1
                elif s == "snare":
                    snare_count += 1
                prev_state = s

            bar_len = int(v * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)

            hit = ""
            if s == "snare":
                hit = " ◀◀ SNARE!"
            elif s == "kick":
                hit = " ◀ kick"

            print(
                f"\r  [{bar}] {s:6} K:{kick_count:3} S:{snare_count:3}{hit:15}",
                end="", flush=True,
            )
            time.sleep(0.015)

    except KeyboardInterrupt:
        print(f"\n\n  Total: {kick_count} kicks, {snare_count} snares")

    ar.stop()
    print("  ✅ Done!")