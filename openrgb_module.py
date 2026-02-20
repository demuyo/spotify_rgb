# openrgb_module.py
"""
Controle de LEDs RGB via OpenRGB.
Suporta breathing, direct, e CHASE EFFECT.
"""

import logging
import time
from typing import Tuple, Optional, List

from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType

import config

logger = logging.getLogger(__name__)

RGB = Tuple[int, int, int]

DEVICE_TYPE_NAMES = {
    DeviceType.MOTHERBOARD: "Placa-mãe",
    DeviceType.DRAM: "RAM",
    DeviceType.GPU: "GPU",
    DeviceType.COOLER: "Cooler",
    DeviceType.LEDSTRIP: "Fita LED",
    DeviceType.KEYBOARD: "Teclado",
    DeviceType.MOUSE: "Mouse",
    DeviceType.MOUSEMAT: "Mousepad",
    DeviceType.HEADSET: "Headset",
    DeviceType.SPEAKER: "Caixa de Som",
    DeviceType.LIGHT: "Luz",
    DeviceType.UNKNOWN: "Desconhecido",
}

BGR_DEVICES = ["ASUS", "TUF", "ROG", "AURA", "Skyloong", "GK104"]
EXCLUDED_DEVICES = ["Skyloong", "GK104"]  # Teclado e mouse não funcionam


class OpenRGBController:

    __slots__ = (
        "client", "devices", "_connected", "excluded_devices",
        "bgr_devices", "_current_mode", "_device_led_counts",
    )

    def __init__(self):
        self.client: Optional[OpenRGBClient] = None
        self.devices: List = []
        self._connected = False
        self.excluded_devices: List[str] = EXCLUDED_DEVICES.copy()
        self.bgr_devices: List[str] = BGR_DEVICES.copy()
        self._current_mode: str = "direct"
        self._device_led_counts: dict = {}

    def connect(self, retries: int = 3, delay: float = 2.0) -> bool:
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"OpenRGB {config.OPENRGB_HOST}:{config.OPENRGB_PORT} ({attempt}/{retries})...")
                self.client = OpenRGBClient(
                    address=config.OPENRGB_HOST,
                    port=config.OPENRGB_PORT,
                    name=config.OPENRGB_NAME,
                )
                self.devices = self.client.devices
                self._connected = True
                
                # Mapeia LEDs por dispositivo
                for i, dev in enumerate(self.devices):
                    self._device_led_counts[i] = len(dev.leds)
                
                logger.info(f"Conectado! {len(self.devices)} dispositivo(s).")
                self._log_devices()
                return True
            except ConnectionRefusedError:
                logger.warning("Conexão recusada.")
            except Exception as e:
                logger.warning(f"Erro: {e}")
            if attempt < retries:
                time.sleep(delay)
        self._connected = False
        return False

    def _log_devices(self):
        for i, dev in enumerate(self.devices):
            dt = DEVICE_TYPE_NAMES.get(dev.type, str(dev.type))
            bgr = " [BGR]" if self._is_bgr(dev.name) else ""
            excl = " [EXCLUDED]" if self._is_excluded(dev.name) else ""
            logger.info(f"  [{i}] {dev.name} | {dt} | {len(dev.leds)} LEDs{bgr}{excl}")

    def _is_bgr(self, name: str) -> bool:
        return any(p.upper() in name.upper() for p in self.bgr_devices)

    def _is_excluded(self, name: str) -> bool:
        return any(p.upper() in name.upper() for p in self.excluded_devices)

    def _color(self, r, g, b, name) -> RGBColor:
        if self._is_bgr(name):
            return RGBColor(r, g, b)
        return RGBColor(b, g, r)

    def _ensure_direct(self, dev):
        try:
            for i, m in enumerate(dev.modes):
                if m.name.lower() in ("direct", "static", "custom"):
                    dev.set_mode(i)
                    return
            dev.set_mode(0)
        except Exception:
            pass

    def set_mode(self, mode: str) -> bool:
        if not self._connected:
            return False
        for dev in self.devices:
            if self._is_excluded(dev.name):
                continue
            if mode == "breathing":
                found = False
                for i, m in enumerate(dev.modes):
                    if "breath" in m.name.lower():
                        dev.set_mode(i)
                        found = True
                        break
                if not found:
                    self._ensure_direct(dev)
            else:
                self._ensure_direct(dev)
        self._current_mode = mode
        logger.info(f"LED mode: {mode}")
        return True

    def set_all_leds(self, r: int, g: int, b: int, log: bool = True) -> bool:
        if not self._connected:
            return self._reconnect(r, g, b)
        try:
            for dev in self.devices:
                if self._is_excluded(dev.name):
                    continue
                try:
                    dev.set_color(self._color(r, g, b, dev.name))
                except Exception as e:
                    logger.debug(f"Erro {dev.name}: {e}")
            if log:
                logger.info(f"LEDs → RGB({r},{g},{b})")
            return True
        except (ConnectionResetError, BrokenPipeError, OSError):
            self._connected = False
            return self._reconnect(r, g, b)

    def set_device_leds(self, dev_index: int, colors: List[RGB]) -> bool:
        """
        Define LEDs individuais num dispositivo.
        colors: lista de (r,g,b) pra cada LED.
        """
        if not self._connected or dev_index >= len(self.devices):
            return False
        try:
            dev = self.devices[dev_index]
            if self._is_excluded(dev.name):
                return False
            rgb_colors = [self._color(r, g, b, dev.name) for r, g, b in colors]
            dev.set_colors(rgb_colors)
            return True
        except Exception as e:
            logger.debug(f"set_device_leds erro: {e}")
            return False

    def get_led_count(self, dev_index: int) -> int:
        """Retorna quantidade de LEDs de um dispositivo."""
        return self._device_led_counts.get(dev_index, 0)

    def get_active_devices(self) -> List[dict]:
        """Retorna dispositivos ativos (não excluídos)."""
        result = []
        for i, dev in enumerate(self.devices):
            if not self._is_excluded(dev.name):
                result.append({
                    "index": i,
                    "name": dev.name,
                    "type": DEVICE_TYPE_NAMES.get(dev.type, str(dev.type)),
                    "leds": len(dev.leds),
                })
        return result

    def _reconnect(self, r, g, b) -> bool:
        if self.connect(retries=2, delay=1.0):
            if self._current_mode:
                self.set_mode(self._current_mode)
            return self.set_all_leds(r, g, b)
        return False

    def disconnect(self):
        if self._current_mode == "breathing":
            self.set_mode("direct")
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected