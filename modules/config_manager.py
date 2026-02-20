# config_manager.py
"""
Gerenciador de configuração com hot-reload.
Permite alterar config em runtime sem reiniciar o programa.
"""

import threading
import time
import copy
import types
from typing import Any, Callable, Dict, List, Optional


def _safe_deepcopy(val):
    """
    Copia um valor de forma segura.
    Se não conseguir, retorna o valor original.
    """
    # Tipos que não podem/não precisam ser copiados
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, types.ModuleType):
        return None  # Ignora módulos
    if callable(val) and not isinstance(val, (list, tuple, dict, type)):
        return None  # Ignora funções
    
    try:
        return copy.deepcopy(val)
    except (TypeError, AttributeError):
        # Se não conseguir copiar, tenta cópia rasa
        try:
            if isinstance(val, dict):
                return dict(val)
            if isinstance(val, list):
                return list(val)
            if isinstance(val, tuple):
                return tuple(val)
            return val
        except:
            return val


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
        self._key_to_category: Dict[str, str] = {}

        self._load_from_config_module()

    def _load_from_config_module(self):
        """Carrega todos os valores do config.py atual."""
        import config

        # Nomes a ignorar (módulos, funções internas, credenciais)
        skip = {
            # Módulos comuns
            "os", "sys", "Path", "pathlib", "logging", "json", "time",
            "threading", "copy", "types", "typing",
            # Funções/variáveis internas
            "ENV_PATH", "load_env", "APP_DIR",
            # Credenciais (ficam no .env)
            "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REDIRECT_URI",
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
            "color_strategy": [
                "COLOR_SELECTION_STRATEGY", "COLOR_ASSIGNMENT_MODE", "COLOR_MIN_SATURATION",
            ],
            "sensitivity": [
                "SENSITIVITY", "PEAKS_SENSITIVITY",
                "CUSTOM_KICK_THRESHOLD", "CUSTOM_SNARE_THRESHOLD",
                "CUSTOM_KICK_MIN_ENERGY", "CUSTOM_SNARE_MIN_ENERGY",
                "CUSTOM_KICK_MINIOI", "CUSTOM_SNARE_MINIOI",
                "PEAK_HOLD_TIME", "PEAK_MIN_INTERVAL", "HIT_HOLD_TIME",
            ],
            "dynamics": [
                "AGC_ENABLED", "AGC_MAX_GAIN", "AGC_MIN_GAIN", "AGC_TARGET",
                "AGC_ATTACK", "AGC_RELEASE",
                "COMPRESSOR_THRESHOLD", "COMPRESSOR_RATIO", "COMPRESSOR_KNEE", "COMPRESSOR_MAKEUP",
                "ADAPTIVE_SMOOTHING", "SMOOTHING_LOW_VOL_MULT", "SMOOTHING_LOW_VOL_THRESH",
                "DYNAMIC_FLOOR_ENABLED", "DYNAMIC_FLOOR_MAX", "DYNAMIC_FLOOR_THRESH",
            ],
            "bands": [
                "BAND_ZONE_PERCUSSION", "BAND_ZONE_BASS", "BAND_ZONE_MELODY",
                "BAND_COLOR_SCHEME",
                "BAND_HUE_PERCUSSION", "BAND_HUE_BASS", "BAND_HUE_MELODY",
                "BAND_SAT_PERCUSSION", "BAND_SAT_BASS", "BAND_SAT_MELODY",
                "BAND_SMOOTHING_ATTACK", "BAND_SMOOTHING_DECAY",
                "BAND_BEAT_ATTACK", "BAND_BEAT_DECAY",
                "BAND_BEAT_FLASH", "BAND_BEAT_COLOR_SHIFT", "BAND_COLOR_SHIFT_MODE",
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
                "BAND_FREQ_BASS_MIN", "BAND_FREQ_BASS_MAX",
                "BAND_FREQ_MELODY_MIN", "BAND_FREQ_MELODY_MAX",
                "BAND_FREQ_PERCUSSION_MIN", "BAND_FREQ_PERCUSSION_MAX",
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
                # Pula atributos internos
                if attr_name.startswith("_"):
                    continue
                
                # Pula nomes conhecidos a ignorar
                if attr_name in skip:
                    continue
                
                # Pega o valor
                try:
                    val = getattr(config, attr_name)
                except Exception:
                    continue
                
                # Pula módulos
                if isinstance(val, types.ModuleType):
                    continue
                
                # Pula funções (exceto se for lista/tuple/dict)
                if callable(val) and not isinstance(val, (list, tuple, dict, type)):
                    continue
                
                # Pula classes
                if isinstance(val, type):
                    continue
                
                # Copia de forma segura
                copied = _safe_deepcopy(val)
                if copied is None and val is not None:
                    # Se não conseguiu copiar e não era None, pula
                    continue
                
                self._values[attr_name] = copied
                self._defaults[attr_name] = _safe_deepcopy(val)

            self._categories = categories

            # Mapear cada key à sua categoria
            for cat, keys in categories.items():
                for k in keys:
                    self._key_to_category[k] = cat

    def get(self, key: str, default=None) -> Any:
        with self._rw_lock:
            val = self._values.get(key, default)
            return _safe_deepcopy(val) if val is not None else default

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
            for k, v in changed.items():
                cat = self._key_to_category.get(k, "unknown")
                self._notify(k, v, cat)

    def reset(self, key: str):
        if key in self._defaults:
            self.set(key, _safe_deepcopy(self._defaults[key]))

    def reset_category(self, category: str):
        keys = self._categories.get(category, [])
        updates = {}
        for k in keys:
            if k in self._defaults:
                updates[k] = _safe_deepcopy(self._defaults[k])
        if updates:
            self.set_many(updates)

    def reset_all(self):
        with self._rw_lock:
            self._values = {}
            for k, v in self._defaults.items():
                self._values[k] = _safe_deepcopy(v)
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
                    try:
                        setattr(config, key, _safe_deepcopy(value))
                    except Exception:
                        pass
            self._dirty = False

    def save_to_file(self, filepath: str = None):
        """Salva as configurações atuais no arquivo config.py."""
        import sys
        from pathlib import Path
        
        if filepath is None:
            if getattr(sys, 'frozen', False):
                filepath = str(Path(sys.executable).parent / "config.py")
            else:
                filepath = str(Path(__file__).parent / "config.py")

        with self._rw_lock:
            values = {}
            for k, v in self._values.items():
                values[k] = _safe_deepcopy(v)

        lines = []
        lines.append('# config.py')
        lines.append('"""')
        lines.append('Configuração do Spotify RGB Sync')
        lines.append('Auto-gerado pela GUI')
        lines.append('"""')
        lines.append('')
        lines.append('import os')
        lines.append('import sys')
        lines.append('from pathlib import Path')
        lines.append('')
        lines.append('# Detecta diretório do executável')
        lines.append("if getattr(sys, 'frozen', False):")
        lines.append('    APP_DIR = Path(sys.executable).parent')
        lines.append('else:')
        lines.append('    APP_DIR = Path(__file__).parent')
        lines.append('')
        lines.append('ENV_PATH = APP_DIR / ".env"')
        lines.append('')
        lines.append('def load_env():')
        lines.append('    if ENV_PATH.exists():')
        lines.append("        with open(ENV_PATH, encoding='utf-8') as f:")
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
        lines.append('SPOTIFY_CLIENT_ID     = os.environ.get("SPOTIPY_CLIENT_ID", "")')
        lines.append('SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET", "")')
        lines.append('SPOTIFY_REDIRECT_URI  = os.environ.get("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")')

        # Gerar seções
        section_order = [
            ("SPOTIFY POLLING RATE", "spotify"),
            ("OPENRGB", "openrgb"),
            ("LED CONFIGURATION", "leds"),
            ("COR PADRÃO", "general"),
            ("BRILHO", "brightness"),
            ("COLOR STRATEGY", "color_strategy"),
            ("COLOR SHIFT", "color_shift"),
            ("SENSIBILIDADE", "sensitivity"),
            ("AGC E DINÂMICA", "dynamics"),
            ("CHASE EFFECT", "chase"),
            ("FREQUENCY EFFECT", "frequency"),
            ("HYBRID EFFECT", "hybrid"),
            ("BAND EFFECT", "bands"),
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
            for k in sorted(remaining):
                lines.append(f'{k} = {repr(values[k])}')

        lines.append('')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def export_preset(self, name: str, filepath: str = None):
        """Exporta configuração atual como preset JSON."""
        import json
        import sys
        from pathlib import Path

        if filepath is None:
            if getattr(sys, 'frozen', False):
                presets_dir = Path(sys.executable).parent / "presets"
            else:
                presets_dir = Path(__file__).parent / "presets"
            presets_dir.mkdir(exist_ok=True)
            filepath = str(presets_dir / f"{name}.json")

        with self._rw_lock:
            data = {
                "name": name,
                "timestamp": time.time(),
                "values": {},
            }
            for k, v in self._values.items():
                data["values"][k] = _safe_deepcopy(v)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def import_preset(self, filepath: str):
        """Importa preset JSON."""
        import json

        with open(filepath, 'r', encoding='utf-8') as f:
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