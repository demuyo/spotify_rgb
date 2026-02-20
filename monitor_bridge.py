# monitor_bridge.py
"""
Bridge de dados entre o engine (main.py) e a GUI.
Singleton thread-safe para compartilhar estado em tempo real.
"""

import threading
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

RGB = Tuple[int, int, int]


@dataclass
class MonitorData:
    """Dados expostos pro monitor da GUI."""
    
    # ── Track Info ──
    track: str = ""
    is_playing: bool = False
    
    # ── Band Levels (0-1) ──
    percussion: float = 0.0
    bass: float = 0.0
    melody: float = 0.0
    
    # ── Band Colors ──
    color_percussion: RGB = (255, 100, 100)
    color_bass: RGB = (100, 100, 255)
    color_melody: RGB = (100, 255, 100)
    
    # ── LED State ──
    led_colors: List[RGB] = field(default_factory=list)
    led_count: int = 0
    
    # ── Audio Info ──
    volume: float = 0.0
    beat_intensity: float = 0.0
    state: str = "idle"  # idle/kick/snare/peak
    agc_gain: float = 1.0
    
    # ── Performance ──
    fps: float = 0.0
    last_update: float = 0.0


class MonitorBridge:
    """
    Singleton thread-safe para compartilhar dados do engine com a GUI.
    
    Uso no main.py:
        from monitor_bridge import monitor
        monitor.update(track="Artist - Song", bass=0.5, ...)
    
    Uso na GUI:
        from monitor_bridge import monitor
        data = monitor.get_data()
    """
    
    _instance: Optional['MonitorBridge'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        """Inicialização (chamada só uma vez)."""
        self._data = MonitorData()
        self._data_lock = threading.Lock()
        self._update_count = 0
        self._fps_time = time.monotonic()
        self._fps_count = 0
    
    def update(
        self,
        track: Optional[str] = None,
        is_playing: Optional[bool] = None,
        percussion: Optional[float] = None,
        bass: Optional[float] = None,
        melody: Optional[float] = None,
        color_percussion: Optional[RGB] = None,
        color_bass: Optional[RGB] = None,
        color_melody: Optional[RGB] = None,
        led_colors: Optional[List[RGB]] = None,
        volume: Optional[float] = None,
        beat_intensity: Optional[float] = None,
        state: Optional[str] = None,
        agc_gain: Optional[float] = None,
    ):
        """
        Atualiza dados do monitor.
        Só atualiza os campos passados (não-None).
        """
        with self._data_lock:
            if track is not None:
                self._data.track = track
            if is_playing is not None:
                self._data.is_playing = is_playing
            if percussion is not None:
                self._data.percussion = percussion
            if bass is not None:
                self._data.bass = bass
            if melody is not None:
                self._data.melody = melody
            if color_percussion is not None:
                self._data.color_percussion = color_percussion
            if color_bass is not None:
                self._data.color_bass = color_bass
            if color_melody is not None:
                self._data.color_melody = color_melody
            if led_colors is not None:
                self._data.led_colors = list(led_colors)
                self._data.led_count = len(led_colors)
            if volume is not None:
                self._data.volume = volume
            if beat_intensity is not None:
                self._data.beat_intensity = beat_intensity
            if state is not None:
                self._data.state = state
            if agc_gain is not None:
                self._data.agc_gain = agc_gain
            
            # FPS tracking
            self._update_count += 1
            now = time.monotonic()
            elapsed = now - self._fps_time
            if elapsed >= 1.0:
                self._data.fps = self._fps_count / elapsed
                self._fps_count = 0
                self._fps_time = now
            self._fps_count += 1
            
            self._data.last_update = now
    
    def get_data(self) -> Dict:
        """
        Retorna dados formatados pro TabMonitor.
        
        Returns:
            Dict compatível com o formato esperado pelo tab_monitor.py
        """
        with self._data_lock:
            return {
                'track': self._data.track,
                'is_playing': self._data.is_playing,
                'bands': {
                    'percussion': self._data.percussion,
                    'bass': self._data.bass,
                    'melody': self._data.melody,
                },
                'band_colors': {
                    'percussion': self._data.color_percussion,
                    'bass': self._data.color_bass,
                    'melody': self._data.color_melody,
                },
                'led_colors': list(self._data.led_colors),
                'led_count': self._data.led_count,
                'volume': self._data.volume,
                'beat_intensity': self._data.beat_intensity,
                'state': self._data.state,
                'agc_gain': self._data.agc_gain,
                'fps': self._data.fps,
            }
    
    def get_monitor_data(self) -> Dict:
        """Alias pra compatibilidade com app_ref.get_monitor_data()."""
        return self.get_data()


# ══════════════════════════════════════════════════
# SINGLETON GLOBAL
# ══════════════════════════════════════════════════

monitor = MonitorBridge()