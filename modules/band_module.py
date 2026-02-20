# band_module.py
"""
🎸🎹🥁 Visualizador por bandas de instrumento.

Suporta múltiplos esquemas de cores:
  - album_colors: Usa as 3 cores mais predominantes da capa
  - triadic, analogous, etc: Deriva cores a partir da dominante
"""

import colorsys
import logging
from typing import List, Tuple, Optional, Dict

import config

logger = logging.getLogger(__name__)

RGB = Tuple[int, int, int]


# band_module.py (adicionar no topo, depois dos imports)

def map_intensity_to_brightness(intensity: float) -> float:
    """
    Mapeia intensidade do áudio (0-1) pra brilho do LED (0-1).
    Usa a curva definida em BRIGHTNESS_MAP do config.
    
    Interpola linearmente entre os pontos definidos.
    """
    # Pega o mapa do config
    brightness_map = getattr(config, 'BRIGHTNESS_MAP', [
        (0.0, 0.001),
        (0.5, 0.30),
        (1.0, 1.00),
    ])
    
    # Garante que tá ordenado
    brightness_map = sorted(brightness_map, key=lambda x: x[0])
    
    # Clamp
    intensity = max(0.0, min(1.0, intensity))
    
    # Se só tem 1 ponto, retorna ele
    if len(brightness_map) == 1:
        return brightness_map[0][1]
    
    # Encontra os dois pontos pra interpolar
    for i in range(len(brightness_map) - 1):
        x0, y0 = brightness_map[i]
        x1, y1 = brightness_map[i + 1]
        
        if x0 <= intensity <= x1:
            # Interpolação linear
            if x1 == x0:
                return y0
            t = (intensity - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    
    # Se passou de todos, retorna o último
    return brightness_map[-1][1]


def render_zone(count: int, band_color: RGB, intensity: float,
                beat: float, zone_name: str) -> List[RGB]:
    """
    Renderiza os LEDs de uma zona.
    
    Color shift agora é mais interessante:
    - Pode ir pro branco (flash)
    - Pode ir pro complementar (mais colorido)
    - Pode aumentar saturação (mais vibrante)
    """
    import colorsys
    
    beat_amount = getattr(config, 'BAND_BEAT_FLASH', 0.50)
    beat_shift = getattr(config, 'BAND_BEAT_COLOR_SHIFT', 0.25)
    gradient = getattr(config, 'BAND_INTERNAL_GRADIENT', 0.20)
    
    # Pega o modo de color shift
    shift_mode = getattr(config, 'BAND_COLOR_SHIFT_MODE', 'white')
    # Opções: 'white', 'saturate', 'complement', 'warm', 'cool'

    colors = []

    for i in range(count):
        # ── Gradiente interno ──
        if count > 1:
            center_dist = abs((i / (count - 1)) - 0.5) * 2.0
        else:
            center_dist = 0.0
        grad_factor = 1.0 - (center_dist * gradient)

        # ── Mapeamento de intensidade → brilho ──
        effective_intensity = intensity * grad_factor
        bright = map_intensity_to_brightness(effective_intensity)

        # ── Beat adiciona flash ──
        bright = min(1.0, bright + beat * beat_amount)

        # ── Cor base com brilho ──
        r = int(band_color[0] * bright)
        g = int(band_color[1] * bright)
        b = int(band_color[2] * bright)

        # ══════════════════════════════════════════════════
        # COLOR SHIFT NO BEAT
        # ══════════════════════════════════════════════════
        if beat > 0.01 and beat_shift > 0.01:
            shift = beat * beat_shift
            
            if shift_mode == 'white':
                # Shift pro branco (original)
                r = min(255, int(r + (255 - r) * shift))
                g = min(255, int(g + (255 - g) * shift))
                b = min(255, int(b + (255 - b) * shift))
            
            elif shift_mode == 'saturate':
                # Aumenta saturação (mais vibrante)
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                s = min(1.0, s + shift * 0.5)
                v = min(1.0, v + shift * 0.3)
                r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
                r, g, b = int(r2 * 255), int(g2 * 255), int(b2 * 255)
            
            elif shift_mode == 'complement':
                # Shift pro complementar (mais dramático)
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                h_comp = (h + 0.5) % 1.0
                # Interpola entre original e complementar
                h_new = h + (h_comp - h) * shift * 0.3
                v = min(1.0, v + shift * 0.2)
                r2, g2, b2 = colorsys.hsv_to_rgb(h_new % 1.0, s, v)
                r, g, b = int(r2 * 255), int(g2 * 255), int(b2 * 255)
            
            elif shift_mode == 'warm':
                # Shift pro amarelo/laranja
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                target_h = 0.08  # Laranja
                h_new = h + (target_h - h) * shift * 0.4
                v = min(1.0, v + shift * 0.2)
                r2, g2, b2 = colorsys.hsv_to_rgb(h_new % 1.0, s, v)
                r, g, b = int(r2 * 255), int(g2 * 255), int(b2 * 255)
            
            elif shift_mode == 'cool':
                # Shift pro ciano/azul
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                target_h = 0.55  # Ciano
                h_new = h + (target_h - h) * shift * 0.4
                v = min(1.0, v + shift * 0.2)
                r2, g2, b2 = colorsys.hsv_to_rgb(h_new % 1.0, s, v)
                r, g, b = int(r2 * 255), int(g2 * 255), int(b2 * 255)

        colors.append((min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))))

    return colors

# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════

def _hsv_to_rgb(h: float, s: float, v: float) -> RGB:
    """Converte HSV (0-1) pra RGB (0-255)."""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, min(1.0, max(0.0, s)), min(1.0, max(0.0, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


def _rgb_to_hsv(color: RGB) -> Tuple[float, float, float]:
    """Converte RGB (0-255) pra HSV (0-1)."""
    return colorsys.rgb_to_hsv(color[0] / 255, color[1] / 255, color[2] / 255)


# ══════════════════════════════════════════════════
# ESQUEMAS DE CORES DERIVADOS
# ══════════════════════════════════════════════════

def _scheme_triadic(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """3 cores igualmente espaçadas (120° cada)."""
    return {
        "percussion": (h, s, v),
        "bass":       ((h + 0.333) % 1.0, s, v),
        "melody":     ((h + 0.666) % 1.0, s, v),
    }


def _scheme_analogous(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """Cores vizinhas (±30°)."""
    return {
        "percussion": ((h - 0.083) % 1.0, s, v),
        "bass":       (h, s, v),
        "melody":     ((h + 0.083) % 1.0, s, v),
    }


def _scheme_complement(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """Base + complementar + vizinha."""
    return {
        "percussion": (h, s, v),
        "bass":       ((h + 0.5) % 1.0, s, v),
        "melody":     ((h + 0.5 + 0.083) % 1.0, s, v),
    }


def _scheme_split(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """Split-complementary."""
    return {
        "percussion": (h, s, v),
        "bass":       ((h + 0.416) % 1.0, s, v),
        "melody":     ((h + 0.583) % 1.0, s, v),
    }


def _scheme_monochrome(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """Mesma matiz, brilhos diferentes."""
    return {
        "percussion": (h, s * 0.7, v * 0.6),
        "bass":       (h, s, v),
        "melody":     (h, s * 0.6, min(1.0, v * 1.3)),
    }


def _scheme_warm_cool(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """Base + quente + fria."""
    return {
        "percussion": (0.05, s, v),    # Vermelho-laranja
        "bass":       (h, s, v),        # Original
        "melody":     (0.55, s, v),     # Ciano-azul
    }


def _scheme_custom(h: float, s: float, v: float) -> Dict[str, Tuple[float, float, float]]:
    """Usa offsets definidos no config."""
    perc_offset = getattr(config, 'BAND_HUE_PERCUSSION', -0.15)
    bass_offset = getattr(config, 'BAND_HUE_BASS', 0.0)
    mel_offset  = getattr(config, 'BAND_HUE_MELODY', 0.15)
    
    perc_sat = getattr(config, 'BAND_SAT_PERCUSSION', 1.0)
    bass_sat = getattr(config, 'BAND_SAT_BASS', 1.0)
    mel_sat  = getattr(config, 'BAND_SAT_MELODY', 1.0)
    
    return {
        "percussion": ((h + perc_offset) % 1.0, s * perc_sat, v),
        "bass":       ((h + bass_offset) % 1.0, s * bass_sat, v),
        "melody":     ((h + mel_offset) % 1.0, s * mel_sat, v),
    }


# Mapa de esquemas derivados (baseados em HUE)
DERIVED_SCHEMES = {
    "triadic":     _scheme_triadic,
    "analogous":   _scheme_analogous,
    "complement":  _scheme_complement,
    "split":       _scheme_split,
    "monochrome":  _scheme_monochrome,
    "warm_cool":   _scheme_warm_cool,
    "custom":      _scheme_custom,
}


# ══════════════════════════════════════════════════
# GERAÇÃO DE CORES
# ══════════════════════════════════════════════════

def generate_band_colors(base_color: RGB, album_url: Optional[str] = None) -> Dict[str, RGB]:
    """
    Gera 3 cores para as bandas.
    
    Se BAND_COLOR_SCHEME = "album_colors" e album_url fornecido:
      → Usa as 3 cores mais predominantes da capa
    
    Senão:
      → Deriva cores a partir da base usando o scheme escolhido
    
    Returns:
        {"percussion": RGB, "bass": RGB, "melody": RGB}
    """
    scheme_name = getattr(config, 'BAND_COLOR_SCHEME', 'triadic').lower()
    
    # ── ALBUM COLORS: Usa cores reais da capa ──
    if scheme_name == "album_colors" and album_url:
        from color_module import generate_band_colors_from_album
        return generate_band_colors_from_album(album_url)
    
    # ── ESQUEMAS DERIVADOS: Usa HUE da cor base ──
    h, s, v = _rgb_to_hsv(base_color)
    
    # Garante saturação e valor mínimos
    s = max(0.6, s)
    v = max(0.5, v)
    
    # Pega função do scheme
    scheme_func = DERIVED_SCHEMES.get(scheme_name, _scheme_triadic)
    
    # Gera HSV pra cada banda
    hsv_colors = scheme_func(h, s, v)
    
    # Converte pra RGB
    rgb_colors = {
        band: _hsv_to_rgb(*hsv)
        for band, hsv in hsv_colors.items()
    }
    
    logger.debug(
        f"Band colors ({scheme_name}): "
        f"🥁{rgb_colors['percussion']} "
        f"🎸{rgb_colors['bass']} "
        f"🎹{rgb_colors['melody']}"
    )
    
    return rgb_colors


# ══════════════════════════════════════════════════
# DISTRIBUIÇÃO DE LEDs
# ══════════════════════════════════════════════════

def compute_zone_layout(total_leds: int) -> Dict[str, Dict[str, int]]:
    """Calcula quantos LEDs cada zona ocupa."""
    p_pct = getattr(config, 'BAND_ZONE_PERCUSSION', 0.33)
    b_pct = getattr(config, 'BAND_ZONE_BASS', 0.34)
    m_pct = getattr(config, 'BAND_ZONE_MELODY', 0.33)

    # Normaliza
    total_pct = p_pct + b_pct + m_pct
    p_pct /= total_pct
    b_pct /= total_pct
    m_pct /= total_pct

    # Distribui
    perc_count = max(1, round(total_leds * p_pct))
    bass_count = max(1, round(total_leds * b_pct))
    mel_count  = max(1, total_leds - perc_count - bass_count)

    return {
        "percussion": {"start": 0, "end": perc_count, "count": perc_count},
        "bass":       {"start": perc_count, "end": perc_count + bass_count, "count": bass_count},
        "melody":     {"start": perc_count + bass_count, "end": total_leds, "count": mel_count},
    }


# ══════════════════════════════════════════════════
# SMOOTHING
# ══════════════════════════════════════════════════

class BandSmoother:
    """Smoothing assimétrico por banda."""

    def __init__(self):
        self.percussion = 0.0
        self.bass = 0.0
        self.melody = 0.0
        self.beat = 0.0

        self._attack = getattr(config, 'BAND_SMOOTHING_ATTACK', 0.25)
        self._decay  = getattr(config, 'BAND_SMOOTHING_DECAY', 0.06)
        self._beat_attack = getattr(config, 'BAND_BEAT_ATTACK', 0.5)
        self._beat_decay  = getattr(config, 'BAND_BEAT_DECAY', 0.90)

    def update(self, raw_perc: float, raw_bass: float,
               raw_melody: float, raw_beat: float):
        self.percussion = self._smooth(self.percussion, raw_perc)
        self.bass       = self._smooth(self.bass, raw_bass)
        self.melody     = self._smooth(self.melody, raw_melody)

        if raw_beat > self.beat:
            self.beat += (raw_beat - self.beat) * self._beat_attack
        else:
            self.beat *= self._beat_decay
            if self.beat < 0.01:
                self.beat = 0.0

    def _smooth(self, current: float, target: float) -> float:
        rate = self._attack if target > current else self._decay
        return current + (target - current) * rate




# ══════════════════════════════════════════════════
# TRANSIÇÃO ENTRE ZONAS
# ══════════════════════════════════════════════════

def blend_zone_borders(colors: List[RGB], layout: Dict, total_leds: int) -> List[RGB]:
    """Suaviza as bordas entre zonas."""
    blend_width = getattr(config, 'BAND_ZONE_BLEND_WIDTH', 2)

    if blend_width <= 0 or total_leds < 6:
        return colors

    result = list(colors)
    border1 = layout["percussion"]["end"]
    border2 = layout["bass"]["end"]

    for border in [border1, border2]:
        for offset in range(-blend_width, blend_width + 1):
            idx = border + offset
            if idx < 0 or idx >= total_leds:
                continue

            left = max(0, idx - 1)
            right = min(total_leds - 1, idx + 1)
            dist = abs(offset) / (blend_width + 1)
            mix = max(0.0, 1.0 - dist) * 0.5

            cl = result[left]
            cr = result[right]

            blended = (
                int(result[idx][0] * (1 - mix) + (cl[0] + cr[0]) / 2 * mix),
                int(result[idx][1] * (1 - mix) + (cl[1] + cr[1]) / 2 * mix),
                int(result[idx][2] * (1 - mix) + (cl[2] + cr[2]) / 2 * mix),
            )
            result[idx] = blended

    return result


# ══════════════════════════════════════════════════
# VISUALIZADOR PRINCIPAL
# ══════════════════════════════════════════════════

class BandVisualizer:
    """Orquestrador principal das bandas visuais."""

    def __init__(self, total_leds: int):
        self.total_leds = total_leds
        self.layout = compute_zone_layout(total_leds)
        self.smoother = BandSmoother()

        # Cores padrão
        self.band_colors = {
            "percussion": (200, 50, 50),
            "bass":       (100, 0, 200),
            "melody":     (50, 150, 255),
        }

        # URL do álbum atual (pra album_colors)
        self._album_url: Optional[str] = None

        self._prev_colors: List[RGB] = [(0, 0, 0)] * total_leds
        self._lerp_rate = getattr(config, 'BAND_COLOR_LERP', 0.12)

        scheme = getattr(config, 'BAND_COLOR_SCHEME', 'triadic')
        
        logger.info(
            f"BandVisualizer: {total_leds} LEDs | Scheme: {scheme}\n"
            f"  🥁 Percussion: {self.layout['percussion']['count']} LEDs "
            f"(idx {self.layout['percussion']['start']}-{self.layout['percussion']['end']-1})\n"
            f"  🎸 Bass:       {self.layout['bass']['count']} LEDs "
            f"(idx {self.layout['bass']['start']}-{self.layout['bass']['end']-1})\n"
            f"  🎹 Melody:     {self.layout['melody']['count']} LEDs "
            f"(idx {self.layout['melody']['start']}-{self.layout['melody']['end']-1})"
        )

    def set_base_color(self, base_color: RGB, album_url: Optional[str] = None) -> List[RGB]:
        """
        Recalcula cores das bandas.
        
        Returns:
            Lista [perc_color, bass_color, melody_color] pra GUI
        """
        self._album_url = album_url
        self.band_colors = generate_band_colors(base_color, album_url)
        
        scheme = getattr(config, 'BAND_COLOR_SCHEME', 'triadic')
        logger.info(
            f"Band colors ({scheme}): "
            f"🥁{self.band_colors['percussion']} "
            f"🎸{self.band_colors['bass']} "
            f"🎹{self.band_colors['melody']}"
        )
        
        # Retorna lista pra GUI
        return [
            self.band_colors['percussion'],
            self.band_colors['bass'],
            self.band_colors['melody'],
        ]

    # band_module.py (substituir o método generate da classe BandVisualizer)

    def generate(
        self,
        bass: float,
        melody: float,
        percussion: float,
        beat_intensity: float,
        volume: float,
        state: str,
    ) -> List[RGB]:
        """
        Gera lista de cores pra todos os LEDs.
        
        CADA BANDA TEM SEU PRÓPRIO BRILHO baseado na sua intensidade.
        Se bass=0.1, zona do baixo fica ESCURA.
        Se percussion=0.9, zona da percussão fica CLARA.
        """
        # ══════════════════════════════════════════════
        # BEAT POR ZONA
        # ══════════════════════════════════════════════
        # Kick afeta mais percussão, snare afeta mais melodia
        if state == "kick":
            beat_perc = beat_intensity * 1.0
            beat_bass = beat_intensity * 0.6
            beat_mel  = beat_intensity * 0.3
        elif state == "snare":
            beat_perc = beat_intensity * 0.5
            beat_bass = beat_intensity * 0.4
            beat_mel  = beat_intensity * 1.0
        elif state == "peak":
            beat_perc = beat_intensity * 0.6
            beat_bass = beat_intensity * 0.5
            beat_mel  = beat_intensity * 0.8
        else:
            beat_perc = 0.0
            beat_bass = 0.0
            beat_mel  = 0.0

        # ══════════════════════════════════════════════
        # SMOOTHING
        # ══════════════════════════════════════════════
        self.smoother.update(percussion, bass, melody, beat_intensity)
        
        # VALORES SUAVIZADOS: estes são 0.0-1.0
        # Quando a banda tá baixa, o valor é BAIXO
        # Quando a banda tá alta, o valor é ALTO
        s_perc = self.smoother.percussion
        s_bass = self.smoother.bass
        s_mel  = self.smoother.melody

        # ══════════════════════════════════════════════
        # RENDERIZA CADA ZONA COM SUA INTENSIDADE
        # ══════════════════════════════════════════════
        # s_perc BAIXO → zona percussão ESCURA
        # s_bass BAIXO → zona baixo ESCURA
        # s_mel  BAIXO → zona melodia ESCURA
        
        perc_leds = render_zone(
            self.layout["percussion"]["count"],
            self.band_colors["percussion"],
            s_perc,          # ← INTENSIDADE DA PERCUSSÃO
            beat_perc,
            "percussion"
        )
        bass_leds = render_zone(
            self.layout["bass"]["count"],
            self.band_colors["bass"],
            s_bass,          # ← INTENSIDADE DO BAIXO
            beat_bass,
            "bass"
        )
        mel_leds = render_zone(
            self.layout["melody"]["count"],
            self.band_colors["melody"],
            s_mel,           # ← INTENSIDADE DA MELODIA
            beat_mel,
            "melody"
        )

        # ══════════════════════════════════════════════
        # JUNTA E SUAVIZA
        # ══════════════════════════════════════════════
        raw = perc_leds + bass_leds + mel_leds

        # Blend nas fronteiras
        raw = blend_zone_borders(raw, self.layout, self.total_leds)

        # Lerp com frame anterior (suavização visual)
        final = []
        for i, target in enumerate(raw):
            prev = self._prev_colors[i]
            lerped = (
                int(prev[0] + (target[0] - prev[0]) * self._lerp_rate),
                int(prev[1] + (target[1] - prev[1]) * self._lerp_rate),
                int(prev[2] + (target[2] - prev[2]) * self._lerp_rate),
            )
            self._prev_colors[i] = lerped
            final.append(lerped)

        return final


# ══════════════════════════════════════════════════
# TESTE STANDALONE
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    print("\n🎸🎹🥁 Teste do BandVisualizer\n")
    
    test_color = (150, 0, 255)  # Roxo
    
    print(f"Cor base: RGB{test_color}\n")
    print("Esquemas derivados:\n")
    
    for scheme in DERIVED_SCHEMES.keys():
        original = getattr(config, 'BAND_COLOR_SCHEME', 'triadic')
        config.BAND_COLOR_SCHEME = scheme
        
        colors = generate_band_colors(test_color)
        
        print(f"  {scheme:12s}: "
              f"🥁{colors['percussion']} "
              f"🎸{colors['bass']} "
              f"🎹{colors['melody']}")
        
        config.BAND_COLOR_SCHEME = original
    
    print("\n✅ Done!")