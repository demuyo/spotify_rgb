# main.py
"""
Spotify RGB Sync — Versão Otimizada
- Lazy imports
- FPS limitado configurável  
- Menos uso de memória
"""

import sys
import os
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict

# Diretório do app
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent
os.chdir(APP_DIR)

# ══════════════════════════════════════════════════════════
# LOGGING (mínimo em produção)
# ══════════════════════════════════════════════════════════

_debug = "--debug" in sys.argv

logging.basicConfig(
    level=logging.DEBUG if _debug else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler() if _debug else logging.NullHandler(),
        logging.FileHandler(APP_DIR / "spotify_rgb.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("SpotifyRGB")

# ══════════════════════════════════════════════════════════
# IMPORTS ESSENCIAIS (lazy imports pra GUI depois)
# ══════════════════════════════════════════════════════════

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config

# ══════════════════════════════════════════════════════════
# ESTADO GLOBAL (usando __slots__ pra economia de memória)
# ══════════════════════════════════════════════════════════

class AppState:
    __slots__ = (
        'running', 'standby', 'track_id', 'track_name', 'album_url',
        'color', 'last_color', 'is_playing'
    )
    
    def __init__(self):
        self.running = True
        self.standby = False
        self.track_id = None
        self.track_name = ""
        self.album_url = None
        self.color = config.DEFAULT_COLOR
        self.last_color = config.DEFAULT_COLOR
        self.is_playing = False

state = AppState()

RGB = Tuple[int, int, int]


def signal_handler(sig, frame):
    state.running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

def smart_sleep(seconds: float):
    end = time.monotonic() + seconds
    while state.running and time.monotonic() < end:
        time.sleep(min(0.3, end - time.monotonic()))


def get_status() -> dict:
    return {
        'track': state.track_name,
        'is_playing': state.is_playing,
        'color': state.color,
    }


def quit_app():
    state.running = False


# ══════════════════════════════════════════════════════════
# LED HELPERS (otimizado)
# ══════════════════════════════════════════════════════════

def get_led_config(rgb) -> Tuple[int, List[Dict]]:
    devices = rgb.get_active_devices()
    total = sum(d["leds"] for d in devices)
    skip_s = getattr(config, 'LED_SKIP_START', 0)
    skip_e = getattr(config, 'LED_SKIP_END', 0)
    usable = total - skip_s - skip_e
    configured = getattr(config, 'LED_COUNT', None)
    return (configured if configured and configured > 0 else usable), devices


def map_colors(colors: List[RGB], count: int, devices: List[Dict]) -> List[List[RGB]]:
    """Mapeia cores virtuais pra LEDs reais (versão otimizada)."""
    total = sum(d["leds"] for d in devices)
    skip_s = getattr(config, 'LED_SKIP_START', 0)
    skip_e = getattr(config, 'LED_SKIP_END', 0)
    
    full = [(0, 0, 0)] * total
    usable = total - skip_s - skip_e
    
    if usable <= 0 or not colors:
        return [[full[0]] * d["leds"] for d in devices]
    
    n_colors = len(colors)
    for i in range(usable):
        pos = (i / max(1, usable - 1)) * max(1, n_colors - 1) if n_colors > 1 else 0
        idx = int(pos)
        frac = pos - idx
        c1 = colors[min(idx, n_colors - 1)]
        c2 = colors[min(idx + 1, n_colors - 1)]
        
        full[skip_s + i] = (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )
    
    result = []
    offset = 0
    for d in devices:
        n = d["leds"]
        result.append(full[offset:offset + n])
        offset += n
    return result


# ══════════════════════════════════════════════════════════
# ENGINE
# ══════════════════════════════════════════════════════════

def run_engine():
    """Engine principal (roda em thread)."""
    # Lazy imports
    from spotify_module import create_spotify_client, get_current_track
    from color_module import get_dominant_color, adjust_brightness, clear_cache
    from openrgb_module import OpenRGBController
    
    if _debug:
        logger.info("🎵 Engine iniciando...")
    
    # Spotify
    sp = None
    for i in range(3):
        try:
            sp = create_spotify_client()
            break
        except Exception as e:
            if _debug:
                logger.warning(f"Spotify {i+1}/3: {e}")
            smart_sleep(3)
    
    if not sp:
        logger.error("Spotify falhou")
        return
    
    # OpenRGB
    rgb = OpenRGBController()
    rgb_ok = rgb.connect(retries=2, delay=2.0)
    
    if not rgb_ok:
        logger.warning("OpenRGB não conectado")
    
    # Audio
    audio = None
    effect = None
    standby_effect = None
    
    if rgb_ok and config.REACTIVE_MODE:
        from audio_spotify_only import AudioReactiveSpotifyOnly
        audio = AudioReactiveSpotifyOnly(hold_time=config.HIT_HOLD_TIME)
        if audio.start():
            if _debug:
                logger.info("✅ Audio ON")
            
            # Cria efeitos
            from band_module import BandVisualizer
            
            led_count, devices = get_led_config(rgb)
            viz = BandVisualizer(led_count)
            
            class Effect:
                __slots__ = ('viz', 'devices', 'led_count', 'last_color', 'last_url', 'colors')
                def __init__(self):
                    self.viz = viz
                    self.devices = devices
                    self.led_count = led_count
                    self.last_color = None
                    self.last_url = None
                    self.colors = {}
            
            effect = Effect()
            
            # Standby
            class Standby:
                __slots__ = ('phase', 'devices', 'led_count')
                def __init__(self):
                    self.phase = 0.0
                    self.devices = devices
                    self.led_count = led_count
            
            standby_effect = Standby()
        else:
            audio = None
    
    if rgb_ok:
        rgb.set_mode("direct")
    
    # Monitor bridge
    try:
        from monitor_bridge import monitor
        has_monitor = True
    except ImportError:
        has_monitor = False
        monitor = None
    
    # ═══════════════════════════════════════════════════
    # LOOP PRINCIPAL
    # ═══════════════════════════════════════════════════
    
    last_poll = 0
    last_frame = 0
    fps = getattr(config, 'MAX_FPS', 60)
    fps_standby = getattr(config, 'STANDBY_FPS', 15)
    
    while state.running:
        now = time.monotonic()
        
        # ── Polling Spotify ──
        if now - last_poll > (config.POLL_IDLE if state.standby else config.POLL_INTERVAL):
            last_poll = now
            
            try:
                track = get_current_track(sp)
                
                if track is None or not track.is_playing:
                    state.standby = True
                    state.is_playing = False
                else:
                    state.standby = False
                    state.is_playing = True
                    
                    if track.track_id != state.track_id:
                        state.track_id = track.track_id
                        state.track_name = f"{track.artist} - {track.name}"
                        state.album_url = track.album_art
                        
                        clear_cache()
                        state.color = get_dominant_color(track.album_art)
                        state.last_color = state.color
                        
                        if has_monitor:
                            monitor.update(track=state.track_name, is_playing=True)
                        
                        if _debug:
                            logger.info(f"🎵 {state.track_name}")
            except Exception as e:
                if _debug:
                    logger.error(f"Poll: {e}")
        
        # ── FPS Control ──
        target_fps = fps_standby if state.standby else fps
        frame_time = 1.0 / target_fps
        
        if now - last_frame < frame_time:
            time.sleep(0.001)
            continue
        
        last_frame = now
        
        # ── Render ──
        if not rgb_ok:
            continue
        
        if state.standby:
            # Breathing
            if standby_effect:
                import math
                speed = getattr(config, 'STANDBY_BREATHING_SPEED', 0.025)
                min_b = getattr(config, 'STANDBY_BRIGHTNESS_MIN', 0.15)
                max_b = getattr(config, 'STANDBY_BRIGHTNESS_MAX', 0.40)
                
                standby_effect.phase += speed
                if standby_effect.phase > 6.283:
                    standby_effect.phase -= 6.283
                
                wave = (math.sin(standby_effect.phase) + 1) / 2
                b = min_b + wave * (max_b - min_b)
                
                c = state.last_color
                color = (min(255, int(c[0] * b)), min(255, int(c[1] * b)), min(255, int(c[2] * b)))
                
                colors = [color] * standby_effect.led_count
                mapped = map_colors(colors, standby_effect.led_count, standby_effect.devices)
                
                for dev, cols in zip(standby_effect.devices, mapped):
                    rgb.set_device_leds(dev["index"], cols)
                
                if has_monitor:
                    flat = [c for cols in mapped for c in cols]
                    monitor.update(is_playing=False, led_colors=flat, bass=0, melody=0, percussion=0)
        
        elif effect and audio:
            # Atualiza cores se mudou
            if state.color != effect.last_color or state.album_url != effect.last_url:
                cols = effect.viz.set_base_color(state.color, state.album_url)
                effect.last_color = state.color
                effect.last_url = state.album_url
                if cols and len(cols) >= 3:
                    effect.colors = {'percussion': cols[0], 'bass': cols[1], 'melody': cols[2]}
            
            # Gera frame
            virtual = effect.viz.generate(
                bass=audio.bass,
                melody=audio.melody,
                percussion=audio.percussion,
                beat_intensity=audio.beat_intensity,
                volume=audio.volume_normalized,
                state=audio.state,
            )
            
            mapped = map_colors(virtual, effect.led_count, effect.devices)
            
            for dev, cols in zip(effect.devices, mapped):
                rgb.set_device_leds(dev["index"], cols)
            
            if has_monitor:
                flat = [c for cols in mapped for c in cols]
                monitor.update(
                    percussion=audio.percussion,
                    bass=audio.bass,
                    melody=audio.melody,
                    color_percussion=effect.colors.get('percussion', (255, 100, 100)),
                    color_bass=effect.colors.get('bass', (100, 100, 255)),
                    color_melody=effect.colors.get('melody', (100, 255, 100)),
                    led_colors=flat,
                    volume=audio.volume_normalized,
                    beat_intensity=audio.beat_intensity,
                    state=audio.state,
                    agc_gain=getattr(audio, 'agc_gain', 1.0),
                    is_playing=True,
                )
    
    # Cleanup
    if audio:
        audio.stop()
    if rgb_ok:
        c = adjust_brightness(state.last_color, config.BRIGHTNESS_FLOOR)
        rgb.set_all_leds(*c)
        rgb.disconnect()


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    
    global _debug
    _debug = args.debug
    
    if args.headless:
        run_engine()
        return
    
    # ═══════════════════════════════════════════════════
    # GUI + TRAY (Qt)
    # ═══════════════════════════════════════════════════
    
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
    from PyQt6.QtCore import Qt, QTimer
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Spotify RGB Sync")
    
    gui_window = None
    
    # ── Ícone ──
    def make_icon():
        px = QPixmap(48, 48)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = state.color or (100, 0, 200)
        p.setBrush(QColor(*c))
        p.setPen(QPen(QColor(0, 0, 0), 2))
        p.drawRoundedRect(2, 2, 44, 44, 6, 6)
        p.setBrush(QColor(0, 255, 0) if state.is_playing else QColor(80, 80, 80))
        p.drawEllipse(32, 32, 12, 12)
        p.end()
        return QIcon(px)
    
    # ── Menu ──
    def open_gui():
        nonlocal gui_window
        try:
            from gui.main_window import MainWindow
            if gui_window is None:
                gui_window = MainWindow(app_ref=None)
            gui_window.show()
            gui_window.raise_()
            gui_window.activateWindow()
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Falha ao abrir GUI:\n\n{e}")
    
    def show_log():
        import subprocess
        log = APP_DIR / "spotify_rgb.log"
        if log.exists():
            subprocess.Popen(["notepad.exe", str(log)])
    
    def do_quit():
        quit_app()
        app.quit()
    
    tray = QSystemTrayIcon()
    tray.setIcon(make_icon())
    tray.setToolTip("Spotify RGB Sync")
    
    menu = QMenu()
    menu.addAction("🎵 Spotify RGB Sync").setEnabled(False)
    menu.addSeparator()
    
    status_act = menu.addAction("⏸ Pausado")
    status_act.setEnabled(False)
    
    track_act = menu.addAction("♪ ---")
    track_act.setEnabled(False)
    
    menu.addSeparator()
    menu.addAction("⚙️ Configurações", open_gui)
    menu.addAction("📄 Ver Log", show_log)
    menu.addSeparator()
    menu.addAction("❌ Sair", do_quit)
    
    tray.setContextMenu(menu)
    tray.show()
    
    # ── Update Timer ──
    def update():
        tray.setIcon(make_icon())
        status_act.setText("▶ Tocando" if state.is_playing else "⏸ Pausado")
        t = state.track_name or "---"
        track_act.setText(f"♪ {t[:35]}..." if len(t) > 35 else f"♪ {t}")
    
    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(2000)
    
    # ── Engine Thread ──
    threading.Thread(target=run_engine, daemon=True).start()
    
    if _debug:
        logger.info("✅ App rodando")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()