# config_manager.py
"""
Gerenciador de configuração com hot-reload.
Permite alterar config em runtime sem reiniciar o programa.
"""

import threading
import time
import copy
from typing import Any, Callable, Dict, List, Optional


class ConfigManager:
    """
    Singleton que gerencia todas as configurações.
    Permite leitura/escrita thread-safe e notifica listeners quando algo muda.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._values: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._listeners: List[Callable] = []
        self._category_listeners: Dict[str, List[Callable]] = {}
        self._rw_lock = threading.RLock()
        self._dirty = False
        self._categories: Dict[str, List[str]] = {}

        self._load_from_config_module()

    def _load_from_config_module(self):
        """Carrega todos os valores do config.py atual."""
        import config

        skip = {
            "os", "Path", "ENV_PATH", "load_env",
            "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET",
            "SPOTIFY_REDIRECT_URI",
        }

        categories = {
            "general": [
                "REACTIVE_MODE", "LED_MODE", "HIT_STYLE",
                "VISUAL_EFFECT", "DETECTION_MODE", "DEFAULT_COLOR",
            ],
            "leds": [
                "LED_SKIP_START", "LED_SKIP_END", "LED_COUNT", "SELECTED_DEVICES",
            ],
            "openrgb": [
                "OPENRGB_HOST", "OPENRGB_PORT", "OPENRGB_NAME",
            ],
            "spotify": [
                "SPOTIFY_SCOPE",
                "POLL_INTERVAL", "POLL_ENDING", "POLL_ENDING_SOON",
                "POLL_AFTER_CHANGE", "POLL_IDLE",
            ],
            "brightness": [
                "BRIGHTNESS_FLOOR", "BRIGHTNESS_BASE",
                "BRIGHTNESS_KICK", "BRIGHTNESS_SNARE", "BRIGHTNESS_PEAK",
                "BRIGHTNESS_MAP",
            ],
            "color_shift": [
                "COLOR_SHIFT_KICK", "COLOR_SHIFT_SNARE", "COLOR_SHIFT_PEAK",
            ],
            "sensitivity": [
                "SENSITIVITY", "PEAKS_SENSITIVITY",
                "CUSTOM_KICK_THRESHOLD", "CUSTOM_SNARE_THRESHOLD",
                "CUSTOM_KICK_MIN_ENERGY", "CUSTOM_SNARE_MIN_ENERGY",
                "CUSTOM_KICK_MINIOI", "CUSTOM_SNARE_MINIOI",
                "PEAK_HOLD_TIME", "PEAK_MIN_INTERVAL", "HIT_HOLD_TIME",
            ],
            "bands": [
                "BAND_ZONE_PERCUSSION", "BAND_ZONE_BASS", "BAND_ZONE_MELODY",
                "BAND_COLOR_SCHEME",
                "BAND_HUE_PERCUSSION", "BAND_HUE_BASS", "BAND_HUE_MELODY",
                "BAND_SAT_PERCUSSION", "BAND_SAT_BASS", "BAND_SAT_MELODY",
                "BAND_SMOOTHING_ATTACK", "BAND_SMOOTHING_DECAY",
                "BAND_BEAT_ATTACK", "BAND_BEAT_DECAY",
                "BAND_BEAT_FLASH", "BAND_BEAT_COLOR_SHIFT",
                "BAND_BG_BRIGHTNESS", "BAND_INTERNAL_GRADIENT",
                "BAND_COLOR_LERP", "BAND_ZONE_BLEND_WIDTH",
                "BAND_BOOST_PERCUSSION", "BAND_BOOST_BASS", "BAND_BOOST_MELODY",
                "BAND_EXPANSION_PERCUSSION", "BAND_EXPANSION_BASS", "BAND_EXPANSION_MELODY",
                "BAND_FLOOR_PERCUSSION", "BAND_FLOOR_BASS", "BAND_FLOOR_MELODY",
                "BAND_CEILING_PERCUSSION", "BAND_CEILING_BASS", "BAND_CEILING_MELODY",
                "BAND_ATTACK", "BAND_DECAY",
                "BAND_RESPONSE_CURVE",
                "BAND_COMPRESSION_ENABLED", "BAND_COMPRESSION_THRESHOLD",
                "BAND_COMPRESSION_RATIO",
            ],
            "chase": [
                "CHASE_ENABLED", "CHASE_SPEED_MAX", "CHASE_TAIL_LENGTH",
                "CHASE_BRIGHTNESS_MIN", "CHASE_BRIGHTNESS_MAX",
                "CHASE_BEAT_FLASH", "CHASE_FLASH_DECAY", "CHASE_BG_BRIGHTNESS",
            ],
            "frequency": [
                "FREQ_SMOOTHING_ATTACK", "FREQ_SMOOTHING_DECAY",
                "FREQ_BEAT_AMOUNT", "FREQ_BEAT_DECAY",
                "FREQ_BG_BRIGHTNESS", "FREQ_BASS_MULT",
                "FREQ_HIGH_SHIFT", "FREQ_COLOR_LERP", "FREQ_ZONE_BLEND",
            ],
            "hybrid": [
                "HYBRID_CHASE_INTENSITY", "HYBRID_CHASE_SPEED",
                "HYBRID_CHASE_TAIL", "HYBRID_CHASE_MODE",
            ],
            "standby": [
                "STANDBY_BRIGHTNESS_MIN", "STANDBY_BRIGHTNESS_MAX",
                "STANDBY_BREATHING_SPEED",
            ],
            "quantized": [
                "QUANTIZED_UPDATE_INTERVAL", "QUANTIZED_LEVELS",
            ],
        }

        with self._rw_lock:
            for attr_name in dir(config):
                if attr_name.startswith("_") or attr_name in skip:
                    continue
                val = getattr(config, attr_name)
                if callable(val) and not isinstance(val, (list, tuple, dict)):
                    continue
                self._values[attr_name] = copy.deepcopy(val)
                self._defaults[attr_name] = copy.deepcopy(val)

            self._categories = categories

            # Mapear cada key à sua categoria
            self._key_to_category: Dict[str, str] = {}
            for cat, keys in categories.items():
                for k in keys:
                    self._key_to_category[k] = cat

    def get(self, key: str, default=None) -> Any:
        with self._rw_lock:
            return copy.deepcopy(self._values.get(key, default))

    def set(self, key: str, value: Any, notify: bool = True):
        with self._rw_lock:
            old = self._values.get(key)
            self._values[key] = value
            self._dirty = True

        if notify and old != value:
            cat = self._key_to_category.get(key, "unknown")
            self._notify(key, value, cat)

    def set_many(self, updates: Dict[str, Any], notify: bool = True):
        changed = {}
        with self._rw_lock:
            for key, value in updates.items():
                old = self._values.get(key)
                if old != value:
                    self._values[key] = value
                    changed[key] = value
            if changed:
                self._dirty = True

        if notify and changed:
            cats = set()
            for k in changed:
                cats.add(self._key_to_category.get(k, "unknown"))
            for k, v in changed.items():
                cat = self._key_to_category.get(k, "unknown")
                self._notify(k, v, cat)

    def reset(self, key: str):
        if key in self._defaults:
            self.set(key, copy.deepcopy(self._defaults[key]))

    def reset_category(self, category: str):
        keys = self._categories.get(category, [])
        updates = {}
        for k in keys:
            if k in self._defaults:
                updates[k] = copy.deepcopy(self._defaults[k])
        if updates:
            self.set_many(updates)

    def reset_all(self):
        with self._rw_lock:
            self._values = copy.deepcopy(self._defaults)
            self._dirty = True
        self._notify_all()

    def get_category_keys(self, category: str) -> List[str]:
        return list(self._categories.get(category, []))

    def get_categories(self) -> List[str]:
        return list(self._categories.keys())

    def is_dirty(self) -> bool:
        return self._dirty

    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def add_category_listener(self, category: str, callback: Callable):
        if category not in self._category_listeners:
            self._category_listeners[category] = []
        self._category_listeners[category].append(callback)

    def _notify(self, key: str, value: Any, category: str):
        for cb in self._listeners:
            try:
                cb(key, value, category)
            except Exception as e:
                print(f"[ConfigManager] Listener error: {e}")

        for cb in self._category_listeners.get(category, []):
            try:
                cb(key, value)
            except Exception as e:
                print(f"[ConfigManager] Category listener error: {e}")

    def _notify_all(self):
        for key, value in self._values.items():
            cat = self._key_to_category.get(key, "unknown")
            self._notify(key, value, cat)

    def apply_to_config_module(self):
        """Escreve os valores atuais de volta no módulo config importado."""
        import config
        with self._rw_lock:
            for key, value in self._values.items():
                if hasattr(config, key):
                    setattr(config, key, copy.deepcopy(value))
            self._dirty = False

    def save_to_file(self, filepath: str = None):
        """Salva as configurações atuais no arquivo config.py."""
        if filepath is None:
            from pathlib import Path
            filepath = str(Path(__file__).parent / "config.py")

        with self._rw_lock:
            values = copy.deepcopy(self._values)
            defaults = copy.deepcopy(self._defaults)

        lines = []
        lines.append('# config.py')
        lines.append('"""')
        lines.append('Configuração do Spotify RGB Sync')
        lines.append('Auto-gerado pela GUI')
        lines.append('"""')
        lines.append('')
        lines.append('import os')
        lines.append('from pathlib import Path')
        lines.append('')
        lines.append('ENV_PATH = Path(__file__).parent / ".env"')
        lines.append('')
        lines.append('def load_env():')
        lines.append('    if ENV_PATH.exists():')
        lines.append('        with open(ENV_PATH) as f:')
        lines.append('            for line in f:')
        lines.append('                line = line.strip()')
        lines.append('                if line and not line.startswith("#") and "=" in line:')
        lines.append('                    key, value = line.split("=", 1)')
        lines.append('                    os.environ.setdefault(key.strip(), value.strip())')
        lines.append('')
        lines.append('load_env()')
        lines.append('')

        # Credenciais Spotify (sempre do .env)
        lines.append('# ' + '═' * 78)
        lines.append('# SPOTIFY API')
        lines.append('# ' + '═' * 78)
        lines.append('')
        lines.append('SPOTIFY_CLIENT_ID     = os.environ["SPOTIPY_CLIENT_ID"]')
        lines.append('SPOTIFY_CLIENT_SECRET = os.environ["SPOTIPY_CLIENT_SECRET"]')
        lines.append('SPOTIFY_REDIRECT_URI  = os.environ["SPOTIPY_REDIRECT_URI"]')

        # Gerar seções
        section_order = [
            ("SPOTIFY POLLING RATE", "spotify"),
            ("OPENRGB", "openrgb"),
            ("LED CONFIGURATION", "leds"),
            ("COR PADRÃO", "general"),
            ("AUDIO REACTIVE", "general"),
            ("VISUAL EFFECT", "general"),
            ("DETECÇÃO", "general"),
            ("BRILHO", "brightness"),
            ("COLOR SHIFT", "color_shift"),
            ("SENSIBILIDADE", "sensitivity"),
            ("CHASE EFFECT", "chase"),
            ("FREQUENCY EFFECT", "frequency"),
            ("HYBRID EFFECT", "hybrid"),
            ("BAND EFFECT", "bands"),
            ("BOOST E DINÂMICA", "bands"),
            ("MAPEAMENTO DE BRILHO", "brightness"),
            ("STANDBY MODE", "standby"),
            ("QUANTIZED", "quantized"),
        ]

        written = set()

        for section_name, category in section_order:
            keys = self._categories.get(category, [])
            unwritten = [k for k in keys if k not in written and k in values]
            if not unwritten:
                continue

            lines.append('')
            lines.append('# ' + '═' * 78)
            lines.append(f'# {section_name}')
            lines.append('# ' + '═' * 78)
            lines.append('')

            for k in unwritten:
                v = values[k]
                lines.append(f'{k} = {repr(v)}')
                written.add(k)

        # Keys restantes
        remaining = [k for k in values if k not in written]
        if remaining:
            lines.append('')
            lines.append('# ' + '═' * 78)
            lines.append('# OUTROS')
            lines.append('# ' + '═' * 78)
            lines.append('')
            for k in remaining:
                lines.append(f'{k} = {repr(values[k])}')

        lines.append('')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def export_preset(self, name: str, filepath: str = None):
        """Exporta configuração atual como preset JSON."""
        import json
        from pathlib import Path

        if filepath is None:
            presets_dir = Path(__file__).parent / "presets"
            presets_dir.mkdir(exist_ok=True)
            filepath = str(presets_dir / f"{name}.json")

        with self._rw_lock:
            data = {
                "name": name,
                "timestamp": time.time(),
                "values": copy.deepcopy(self._values),
            }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def import_preset(self, filepath: str):
        """Importa preset JSON."""
        import json

        with open(filepath, 'r') as f:
            data = json.load(f)

        values = data.get("values", {})

        # Converter tipos especiais de volta
        for k, v in values.items():
            if k == "BRIGHTNESS_MAP" and isinstance(v, list):
                values[k] = [tuple(pair) for pair in v]
            elif k == "DEFAULT_COLOR" and isinstance(v, list):
                values[k] = tuple(v)

        self.set_many(values)
        self.apply_to_config_module()