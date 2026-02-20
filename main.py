# main.py
"""
Spotify ↔ OpenRGB - Versão Otimizada
- Auto-start silencioso
- GUI lazy-load
- Mínimo consumo de recursos
"""

import logging
import signal
import sys
import os
import time
import threading
from typing import Optional, Tuple, List, Dict

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ══════════════════════════════════════════════════════════
# LOGGING OTIMIZADO (menos verbose em produção)
# ══════════════════════════════════════════════════════════

_debug_mode = "--debug" in sys.argv
log_level = logging.DEBUG if _debug_mode else logging.WARNING  # WARNING em produção!

logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("spotify_rgb.log", encoding="utf-8"),
    ] if not _debug_mode else [
        logging.StreamHandler(),
        logging.FileHandler("spotify_rgb.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("SpotifyRGB")

# ══════════════════════════════════════════════════════════
# IMPORTS (só o necessário)
# ══════════════════════════════════════════════════════════

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config
from spotify_module import create_spotify_client, get_current_track
from color_module import get_dominant_color, adjust_brightness, clear_cache
from openrgb_module import OpenRGBController
from audio_spotify_only import AudioReactiveSpotifyOnly as AudioReactive

# ══════════════════════════════════════════════════════════
# GLOBAL STATE (mínimo)
# ══════════════════════════════════════════════════════════

_running = True
_standby_mode = False
_current_album_url: Optional[str] = None
_current_track_id: Optional[str] = None
_current_color: Tuple[int, int, int] = config.DEFAULT_COLOR
_last_music_color: Tuple[int, int, int] = config.DEFAULT_COLOR
_current_track_name: str = ""
_is_playing: bool = False

RGB = Tuple[int, int, int]


def signal_handler(sig, frame):
    global _running
    _running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ══════════════════════════════════════════════════════════
# HELPERS OTIMIZADOS
# ══════════════════════════════════════════════════════════

def _smart_sleep(seconds: float):
    """Sleep interruptível."""
    end = time.monotonic() + seconds
    while _running and time.monotonic() < end:
        time.sleep(min(0.5, end - time.monotonic()))


def _calc_poll(prog, dur, last_change):
    """Calcula intervalo de polling dinâmico."""
    if dur <= 0:
        return config.POLL_INTERVAL
    rem = (dur - prog) / 1000.0
    since = time.monotonic() - last_change
    if rem <= 5:
        return config.POLL_ENDING_SOON
    if rem <= 15:
        return config.POLL_ENDING
    if since < 30:
        return config.POLL_AFTER_CHANGE
    return config.POLL_INTERVAL


# ══════════════════════════════════════════════════════════
# LED HELPERS
# ══════════════════════════════════════════════════════════

def get_led_config(rgb: OpenRGBController) -> Tuple[int, List[Dict]]:
    """Retorna (total_leds_usáveis, devices_info)."""
    devices = rgb.get_active_devices()
    real_total = sum(d["leds"] for d in devices)
    
    skip_start = getattr(config, 'LED_SKIP_START', 0)
    skip_end = getattr(config, 'LED_SKIP_END', 0)
    usable_total = real_total - skip_start - skip_end
    
    configured = getattr(config, 'LED_COUNT', None)
    
    if configured is None or configured <= 0:
        return usable_total, devices
    
    return configured, devices


def map_virtual_to_real(
    virtual_colors: List[RGB],
    virtual_count: int,
    devices: List[Dict]
) -> List[List[RGB]]:
    """
    Mapeia cores virtuais para LEDs reais.
    
    CORRIGIDO: Usa global_offset de cada device pra calcular corretamente.
    """
    # Calcula total REAL de LEDs
    real_total = sum(d["leds"] for d in devices)
    
    skip_start = getattr(config, 'LED_SKIP_START', 0)
    skip_end = getattr(config, 'LED_SKIP_END', 0)
    
    # Cria array completo (começa tudo preto)
    full_colors = [(0, 0, 0)] * real_total
    
    # Região usável
    usable_start = skip_start
    usable_end = real_total - skip_end
    usable_count = usable_end - usable_start
    
    if usable_count <= 0:
        logger.warning(f"Nenhum LED usável! total={real_total}, skip_start={skip_start}, skip_end={skip_end}")
        return [[c for c in [(0, 0, 0)] * d["leds"]] for d in devices]
    
    # Mapeia cores virtuais pra região usável
    for i in range(usable_count):
        # Posição no array de cores virtuais
        if virtual_count > 1:
            virtual_pos = (i / (usable_count - 1)) * (virtual_count - 1)
        else:
            virtual_pos = 0
        
        # Interpolação
        idx_low = int(virtual_pos)
        idx_high = min(idx_low + 1, virtual_count - 1)
        frac = virtual_pos - idx_low
        
        c1 = virtual_colors[idx_low]
        c2 = virtual_colors[idx_high]
        
        r = int(c1[0] + (c2[0] - c1[0]) * frac)
        g = int(c1[1] + (c2[1] - c1[1]) * frac)
        b = int(c1[2] + (c2[2] - c1[2]) * frac)
        
        # Posição REAL (global)
        real_idx = usable_start + i
        if 0 <= real_idx < real_total:
            full_colors[real_idx] = (r, g, b)
    
    # ══════════════════════════════════════════════
    # DISTRIBUI PROS DEVICES
    # ══════════════════════════════════════════════
    result = []
    
    # Usa global_offset se disponível, senão calcula
    offset = 0
    for dev in devices:
        dev_offset = dev.get('global_offset', offset)
        dev_leds = dev["leds"]
        
        # Pega as cores pra este device
        dev_colors = full_colors[dev_offset:dev_offset + dev_leds]
        
        # Garante que tem a quantidade certa
        if len(dev_colors) < dev_leds:
            dev_colors = list(dev_colors) + [(0, 0, 0)] * (dev_leds - len(dev_colors))
        
        result.append(dev_colors)
        offset += dev_leds
    
    return result


# ══════════════════════════════════════════════════════════
# SPOTIFY THREAD (OTIMIZADA)
# ══════════════════════════════════════════════════════════

def _spotify_thread(sp, rgb, rgb_ok):
    """Thread que monitora o Spotify."""
    global _running, _current_track_id, _current_color, _last_music_color
    global _current_album_url, _standby_mode, _current_track_name, _is_playing

    last_change = time.monotonic()
    last_prog = -1
    last_poll = time.monotonic()

    while _running:
        try:
            now = time.monotonic()
            elapsed = now - last_poll
            last_poll = now

            track = get_current_track(sp)

            if track is None or not track.is_playing:
                if _current_track_id is not None:
                    _current_track_id = None
                    last_prog = -1
                
                _standby_mode = True
                _is_playing = False
                
                # Sleep longo quando idle (economia de recursos)
                _smart_sleep(config.POLL_IDLE)
                continue

            _standby_mode = False
            _is_playing = True

            changed = track.track_id != _current_track_id

            if changed:
                _current_track_id = track.track_id
                last_change = now
                last_prog = track.progress_ms

                clear_cache()
                new_color = get_dominant_color(track.album_art)
                _current_album_url = track.album_art

                base = adjust_brightness(new_color, config.BRIGHTNESS_BASE)
                if rgb_ok:
                    rgb.set_all_leds(*base, log=False)

                _current_color = new_color
                _last_music_color = new_color
                _current_track_name = f"{track.artist} - {track.name}"
                
                if _debug_mode:
                    logger.info(f"🎵 {_current_track_name}")

            else:
                last_prog = track.progress_ms

            _smart_sleep(_calc_poll(track.progress_ms, track.duration_ms, last_change))

        except Exception as e:
            if _debug_mode:
                logger.error(f"Spotify: {e}")
            _smart_sleep(config.POLL_INTERVAL * 2)


# ══════════════════════════════════════════════════════════
# EFEITOS (imports lazy)
# ══════════════════════════════════════════════════════════

_effect_cache = {}

def _get_effect(effect_type: str, rgb: OpenRGBController):
    """Lazy load de efeitos."""
    global _effect_cache
    
    if effect_type in _effect_cache:
        return _effect_cache[effect_type]
    
    if effect_type == "bands":
        from band_module import BandVisualizer
        
        class BandEffect:
            def __init__(self, rgb):
                self.rgb = rgb
                self.total_leds, self.devices = get_led_config(rgb)
                self.viz = BandVisualizer(self.total_leds)
                self._last_color = None
                self._last_url = None
                self._band_colors = {}
            
            def update(self, base_color, audio, album_url=None):
                if base_color != self._last_color or album_url != self._last_url:
                    colors = self.viz.set_base_color(base_color, album_url)
                    self._last_color = base_color
                    self._last_url = album_url
                    if colors and len(colors) >= 3:
                        self._band_colors = {
                            'percussion': colors[0],
                            'bass': colors[1],
                            'melody': colors[2],
                        }
                
                virtual_colors = self.viz.generate(
                    bass=audio.bass,
                    melody=audio.melody,
                    percussion=audio.percussion,
                    beat_intensity=audio.beat_intensity,
                    volume=audio.volume_normalized,
                    state=audio.state,
                )
                
                real_colors = map_virtual_to_real(virtual_colors, self.total_leds, self.devices)
                for dev, colors in zip(self.devices, real_colors):
                    self.rgb.set_device_leds(dev["index"], colors)
        
        effect = BandEffect(rgb)
        _effect_cache[effect_type] = effect
        return effect
    
    # Fallback: efeito simples
    return None


# ══════════════════════════════════════════════════════════
# STANDBY BREATHING (OTIMIZADO)
# ══════════════════════════════════════════════════════════

class StandbyBreathing:
    """Breathing suave quando pausado."""
    
    def __init__(self, rgb: OpenRGBController):
        self.rgb = rgb
        self.total_leds, self.devices = get_led_config(rgb)
        self.phase = 0.0
        self._last_colors = None
    
    def update(self, base_color: RGB):
        import math
        
        speed = getattr(config, 'STANDBY_BREATHING_SPEED', 0.025)
        min_b = getattr(config, 'STANDBY_BRIGHTNESS_MIN', 0.15)
        max_b = getattr(config, 'STANDBY_BRIGHTNESS_MAX', 0.40)
        
        self.phase += speed
        if self.phase > math.pi * 2:
            self.phase -= math.pi * 2
        
        wave = (math.sin(self.phase) + 1) / 2
        brightness = min_b + (wave * (max_b - min_b))
        
        r = min(255, int(base_color[0] * brightness))
        g = min(255, int(base_color[1] * brightness))
        b = min(255, int(base_color[2] * brightness))
        
        color = (r, g, b)
        
        # Só atualiza se mudou (economia)
        if color == self._last_colors:
            return
        self._last_colors = color
        
        virtual_colors = [color] * self.total_leds
        real_colors = map_virtual_to_real(virtual_colors, self.total_leds, self.devices)
        
        for dev, colors in zip(self.devices, real_colors):
            self.rgb.set_device_leds(dev["index"], colors)


# ══════════════════════════════════════════════════════════
# REACTIVE LOOP (OTIMIZADO)
# ══════════════════════════════════════════════════════════

def _reactive_loop(audio: AudioReactive, rgb: OpenRGBController):
    """Loop principal otimizado."""
    global _running, _current_album_url, _standby_mode

    effect_type = getattr(config, 'VISUAL_EFFECT', 'bands')
    effect = _get_effect(effect_type, rgb)
    standby_effect = StandbyBreathing(rgb)
    
    rgb.set_mode("direct")
    
    # Timers pra reduzir updates
    last_update = 0
    min_interval = 0.012  # ~83 FPS máximo (na prática menos)
    
    # Intervalo maior quando standby
    standby_interval = 0.030  # ~33 FPS no standby (suficiente pra breathing)

    while _running:
        now = time.monotonic()
        
        # ── STANDBY MODE ──
        if _standby_mode:
            if now - last_update < standby_interval:
                time.sleep(0.005)
                continue
            
            standby_effect.update(_last_music_color)
            last_update = now
            time.sleep(standby_interval)
            continue
        
        # ── ACTIVE MODE ──
        if now - last_update < min_interval:
            time.sleep(0.002)
            continue
        
        if effect:
            effect.update(_last_music_color, audio, _current_album_url)
        
        last_update = now
        time.sleep(min_interval)


# ══════════════════════════════════════════════════════════
# MAIN LOOP (OTIMIZADO)
# ══════════════════════════════════════════════════════════

def main_loop():
    """Loop principal."""
    global _running, _current_color, _last_music_color

    if _debug_mode:
        logger.info("=" * 50)
        logger.info("  🎵 Spotify RGB Sync (Optimized)")
        logger.info("=" * 50)

    # ── Spotify ──
    sp = None
    for i in range(3):  # Menos tentativas
        try:
            sp = create_spotify_client()
            break
        except Exception as e:
            if _debug_mode:
                logger.warning(f"Spotify {i+1}/3: {e}")
            _smart_sleep(5)
    
    if not sp:
        logger.error("Spotify falhou")
        return

    # ── OpenRGB ──
    rgb = OpenRGBController()
    rgb_ok = rgb.connect(retries=3, delay=3.0)

    if rgb_ok:
        rgb.set_mode("direct")
        rgb.set_all_leds(*adjust_brightness(_current_color, config.BRIGHTNESS_FLOOR))

    # ── Audio ──
    audio = None
    if rgb_ok and config.REACTIVE_MODE:
        audio = AudioReactive(hold_time=config.HIT_HOLD_TIME)
        if audio.start():
            if _debug_mode:
                logger.info("✅ Audio reactive ON")
        else:
            audio = None

    if audio:
        # Spotify em thread separada
        threading.Thread(
            target=_spotify_thread, 
            args=(sp, rgb, rgb_ok), 
            daemon=True
        ).start()

        _reactive_loop(audio, rgb)
    else:
        _spotify_thread(sp, rgb, rgb_ok)

    # ── Cleanup ──
    if audio:
        audio.stop()
    if rgb_ok:
        idle = adjust_brightness(_last_music_color, config.BRIGHTNESS_FLOOR)
        rgb.set_all_leds(*idle)
        time.sleep(0.1)
        rgb.disconnect()


# ══════════════════════════════════════════════════════════
# STATUS CALLBACK (para tray)
# ══════════════════════════════════════════════════════════

def get_status() -> dict:
    """Retorna status atual pra o tray."""
    return {
        'track': _current_track_name,
        'is_playing': _is_playing,
        'color': _current_color,
    }


def quit_app():
    """Encerra o app."""
    global _running
    _running = False


# ══════════════════════════════════════════════════════════
# ENTRY POINTS
# ══════════════════════════════════════════════════════════

def run_headless():
    """Roda sem interface (mais leve)."""
    main_loop()


def run_with_tray():
    """Roda com tray icon minimalista."""
    from tray_minimal import MinimalTray
    
    # Inicia o core em thread
    core_thread = threading.Thread(target=main_loop, daemon=True)
    core_thread.start()
    
    # Cria tray
    tray = MinimalTray(
        on_quit_callback=quit_app,
        get_status_callback=get_status
    )
    
    # Roda tray (bloqueia)
    tray.run()


def main():
    """Entry point principal."""
    import argparse
    parser = argparse.ArgumentParser(description="Spotify RGB Sync")
    parser.add_argument("--debug", action="store_true", help="Modo debug (verbose)")
    parser.add_argument("--headless", action="store_true", help="Sem tray (terminal)")
    parser.add_argument("--gui", action="store_true", help="Abre GUI direto")
    args = parser.parse_args()
    
    global _debug_mode
    _debug_mode = args.debug
    
    if args.headless:
        run_headless()
    elif args.gui:
        # Abre GUI direto (pra debug)
        run_with_tray()
    else:
        # Padrão: tray minimalista
        run_with_tray()


if __name__ == "__main__":
    main()