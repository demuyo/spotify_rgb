# color_module.py
"""
Extrai cores predominantes da capa do álbum.
REGRA: Usa APENAS cores que existem na imagem, nunca inventa.

Suporta múltiplas estratégias de seleção e atribuição,
configuráveis via config.py / GUI.
"""

import logging
import colorsys
import math
from io import BytesIO
from itertools import combinations
from typing import Tuple, List, Dict, Optional
from collections import Counter

import requests
from PIL import Image

import config

logger = logging.getLogger(__name__)

RGB = Tuple[int, int, int]
HSV = Tuple[float, float, float]

_color_cache: Dict[str, RGB] = {}
_multi_color_cache: Dict[str, Dict] = {}
_session = requests.Session()


# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════

def _download_image(url: str) -> Image.Image:
    """Baixa imagem e redimensiona."""
    response = _session.get(url, timeout=10)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize((80, 80), Image.Resampling.LANCZOS)
    return img


def _rgb_to_hsv(r: int, g: int, b: int) -> HSV:
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def _hsv_to_rgb(h: float, s: float, v: float) -> RGB:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


def _get_luminance(r: int, g: int, b: int) -> float:
    """Luminância percebida (0-1)."""
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _get_saturation(r: int, g: int, b: int) -> float:
    _, s, _ = _rgb_to_hsv(r, g, b)
    return s


def _color_distance(c1: RGB, c2: RGB) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def _is_similar(c1: RGB, c2: RGB, threshold: float = 40) -> bool:
    return _color_distance(c1, c2) < threshold


def _get_hue(r: int, g: int, b: int) -> float:
    h, _, _ = _rgb_to_hsv(r, g, b)
    return h


def _hue_distance(c1: RGB, c2: RGB) -> float:
    """Distância circular de hue (0-0.5)."""
    h1 = _get_hue(*c1)
    h2 = _get_hue(*c2)
    diff = abs(h1 - h2)
    return min(diff, 1.0 - diff)


# ══════════════════════════════════════════════════
# EXTRAÇÃO DE CORES
# ══════════════════════════════════════════════════

def _extract_colors(img: Image.Image) -> List[Tuple[RGB, int]]:
    """
    Extrai cores da imagem usando quantização.
    Retorna lista de (cor, contagem) ordenada por frequência.
    """
    quantized = img.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    pixels = list(quantized.getdata())
    counts = Counter(pixels)

    colors = []
    for idx, pixel_count in counts.most_common(16):
        if idx < 16 and palette:
            i = idx * 3
            r, g, b = palette[i], palette[i + 1], palette[i + 2]
            colors.append(((r, g, b), pixel_count))

    return colors


def _merge_similar_colors(
    colors: List[Tuple[RGB, int]], threshold: float = 35
) -> List[Tuple[RGB, int]]:
    """Agrupa cores similares, mantendo a mais saturada do grupo."""
    if not colors:
        return []

    merged = []

    for color, count in colors:
        found = False
        for i, (existing, existing_count) in enumerate(merged):
            if _is_similar(color, existing, threshold):
                if _get_saturation(*color) > _get_saturation(*existing):
                    merged[i] = (color, existing_count + count)
                else:
                    merged[i] = (existing, existing_count + count)
                found = True
                break

        if not found:
            merged.append((color, count))

    merged.sort(key=lambda x: x[1], reverse=True)
    return merged


# ══════════════════════════════════════════════════
# BOOST DE SATURAÇÃO
# ══════════════════════════════════════════════════

def _boost_color(color: RGB, album_avg_sat: float) -> RGB:
    """
    Aumenta saturação da cor pra ficar visível em LED.
    
    Usa COLOR_MIN_SATURATION como piso.
    NÃO muda o hue! Só saturação e value.
    """
    r, g, b = color
    h, s, v = _rgb_to_hsv(r, g, b)

    # Praticamente cinza → não tem como salvar
    if s < 0.05:
        return color

    # ── Piso de saturação (configurável) ──
    min_sat = getattr(config, 'COLOR_MIN_SATURATION', 0.45)
    s = max(s, min_sat)

    # ── Boost adicional pra saturações ainda baixas ──
    if s < 0.40:
        s = min(0.92, s * 2.2)
    elif s < 0.65:
        s = min(0.95, s * 1.6)
    # Se já é saturada (≥0.65), deixa como está

    # ── Ajusta value pra não ficar invisível nem lavado ──
    if v < 0.30:
        v = 0.42
    elif v > 0.95:
        v = 0.88

    return _hsv_to_rgb(h, s, v)


# ══════════════════════════════════════════════════
# UTILITÁRIOS DE SELEÇÃO
# ══════════════════════════════════════════════════

def _fill_remaining(selected: List[RGB], target: int = 3) -> List[RGB]:
    """Preenche até 'target' cores, criando variações se necessário."""
    while len(selected) < target:
        if selected:
            base = selected[0]
            h, s, v = _rgb_to_hsv(*base)
            offset = len(selected) * 0.25
            if len(selected) % 2 == 1:
                new_v = max(0.25, v - offset)
            else:
                new_v = min(0.95, v + offset)
            selected.append(_hsv_to_rgb(h, s, new_v))
        else:
            selected.append(config.DEFAULT_COLOR)
    return selected[:target]


def _separate_chromatic(
    colors: List[Tuple[RGB, int]], min_sat: float = 0.10
) -> tuple:
    """Separa cores cromáticas (com cor) das acromáticas (cinza)."""
    chromatic = []
    achromatic = []

    for color, count in colors:
        sat = _get_saturation(*color)
        lum = _get_luminance(*color)

        if sat > min_sat:
            chromatic.append((color, count, sat))
        elif sat > 0.06 and 0.15 < lum < 0.85:
            chromatic.append((color, count, sat))
        else:
            achromatic.append((color, count))

    return chromatic, achromatic


def _pick_distinct(
    candidates: list,
    avg_sat: float,
    threshold: float = 50,
    max_colors: int = 3,
) -> List[RGB]:
    """
    Pega até max_colors cores distintas dos candidatos.
    Candidatos: lista de (color, count, sat) ou (color, count).
    """
    selected = []

    for item in candidates:
        color = item[0]
        boosted = _boost_color(color, avg_sat)

        if not any(_is_similar(boosted, s, threshold=threshold) for s in selected):
            selected.append(boosted)
            if len(selected) >= max_colors:
                break

    return selected


# ══════════════════════════════════════════════════
# ESTRATÉGIAS DE SELEÇÃO DE CORES
# ══════════════════════════════════════════════════

def _select_balanced(
    colors: List[Tuple[RGB, int]], avg_sat: float
) -> List[RGB]:
    """
    Estratégia EQUILIBRADA (comportamento original).
    Score = frequência * 0.60 + saturação * 0.40
    
    Bom pra álbuns com paleta definida.
    Pode produzir cores lavadas se o álbum for pastel.
    """
    if not colors:
        return [config.DEFAULT_COLOR] * 3

    chromatic, achromatic = _separate_chromatic(colors, min_sat=0.12)

    if chromatic:
        max_count = max(c[1] for c in chromatic)
        chromatic.sort(
            key=lambda x: (x[1] / max_count) * 0.6 + x[2] * 0.4,
            reverse=True,
        )

    selected = _pick_distinct(chromatic, avg_sat, threshold=50)

    # Fallback: acromáticas
    if len(selected) < 3 and achromatic:
        for color, count in achromatic:
            if not any(_is_similar(color, s, threshold=50) for s in selected):
                selected.append(color)
                if len(selected) >= 3:
                    break

    return _fill_remaining(selected)


def _select_vibrant(
    colors: List[Tuple[RGB, int]], avg_sat: float
) -> List[RGB]:
    """
    Estratégia VIBRANTE.
    Score = frequência * 0.25 + saturação * 0.75
    
    Prioriza cores vivas. Ideal pra LEDs.
    As cores mais saturadas da capa dominam.
    """
    if not colors:
        return [config.DEFAULT_COLOR] * 3

    chromatic, achromatic = _separate_chromatic(colors, min_sat=0.08)

    if chromatic:
        max_count = max(c[1] for c in chromatic)
        chromatic.sort(
            key=lambda x: (x[1] / max_count) * 0.25 + x[2] * 0.75,
            reverse=True,
        )

    selected = _pick_distinct(chromatic, avg_sat, threshold=50)

    if len(selected) < 3 and achromatic:
        for color, count in achromatic:
            if not any(_is_similar(color, s, threshold=50) for s in selected):
                selected.append(color)
                if len(selected) >= 3:
                    break

    return _fill_remaining(selected)


def _select_max_saturation(
    colors: List[Tuple[RGB, int]], avg_sat: float
) -> List[RGB]:
    """
    Estratégia MÁXIMA SATURAÇÃO.
    Ordena puramente por saturação, ignora frequência.
    
    Pega as cores mais vivas do álbum, mesmo que sejam raras.
    Pode ignorar a "identidade visual" do álbum.
    """
    if not colors:
        return [config.DEFAULT_COLOR] * 3

    # Ordena TUDO por saturação (não separa chromatic/achromatic)
    by_sat = sorted(colors, key=lambda x: _get_saturation(*x[0]), reverse=True)

    # Filtra só cromáticas
    chromatic = [
        (c, cnt, _get_saturation(*c))
        for c, cnt in by_sat
        if _get_saturation(*c) > 0.06
    ]

    selected = _pick_distinct(chromatic, avg_sat, threshold=55)
    return _fill_remaining(selected)


def _select_contrast(
    colors: List[Tuple[RGB, int]], avg_sat: float
) -> List[RGB]:
    """
    Estratégia MÁXIMO CONTRASTE.
    Encontra a combinação de 3 cores com maior distância visual.
    
    Garante que as 3 bandas sejam BEM diferentes entre si.
    Usa brute-force (C(12,3) = 220 combinações, super rápido).
    """
    if not colors:
        return [config.DEFAULT_COLOR] * 3

    # Prepara candidatas: boost todas as cromáticas
    candidates = []
    for color, count in colors:
        if _get_saturation(*color) > 0.06:
            boosted = _boost_color(color, avg_sat)
            candidates.append(boosted)

    # Fallback: inclui acromáticas
    if len(candidates) < 3:
        for color, count in colors:
            if color not in candidates:
                candidates.append(color)

    if len(candidates) < 3:
        return _fill_remaining(candidates)

    # Limita a 12 candidatas pra performance
    candidates = candidates[:12]

    best_score = -1
    best_triplet = candidates[:3]

    for triplet in combinations(range(len(candidates)), 3):
        c1, c2, c3 = [candidates[i] for i in triplet]

        # Distância total (RGB euclidiana)
        dist = (
            _color_distance(c1, c2)
            + _color_distance(c2, c3)
            + _color_distance(c1, c3)
        )

        # Pondera pela saturação média (prefere triplets coloridos)
        avg_s = (
            _get_saturation(*c1) + _get_saturation(*c2) + _get_saturation(*c3)
        ) / 3
        score = dist * (0.4 + avg_s * 0.6)

        if score > best_score:
            best_score = score
            best_triplet = [c1, c2, c3]

    return list(best_triplet)


def _select_adaptive(
    colors: List[Tuple[RGB, int]], avg_sat: float
) -> List[RGB]:
    """
    Estratégia ADAPTATIVA.
    Escolhe automaticamente baseado no perfil do álbum:
    
    - Álbum colorido (sat > 0.45) → balanced (já tá bom)
    - Álbum pastel (0.20-0.45) → vibrant (puxa saturação)
    - Álbum desaturado (< 0.20) → max_saturation (busca qualquer cor)
    """
    if avg_sat > 0.45:
        logger.debug(f"Adaptive → balanced (avg_sat={avg_sat:.2f})")
        return _select_balanced(colors, avg_sat)
    elif avg_sat > 0.20:
        logger.debug(f"Adaptive → vibrant (avg_sat={avg_sat:.2f})")
        return _select_vibrant(colors, avg_sat)
    else:
        logger.debug(f"Adaptive → max_saturation (avg_sat={avg_sat:.2f})")
        return _select_max_saturation(colors, avg_sat)


# ── Mapa de estratégias ──
SELECTION_STRATEGIES = {
    "balanced": _select_balanced,
    "vibrant": _select_vibrant,
    "max_saturation": _select_max_saturation,
    "contrast": _select_contrast,
    "adaptive": _select_adaptive,
}


# ══════════════════════════════════════════════════
# SELEÇÃO: DISPATCHER
# ══════════════════════════════════════════════════

def _select_top_3_colors(colors: List[Tuple[RGB, int]], avg_sat: float) -> List[RGB]:
    """
    Dispatcher: chama a estratégia configurada em COLOR_SELECTION_STRATEGY.
    """
    strategy_name = getattr(config, 'COLOR_SELECTION_STRATEGY', 'vibrant').lower()
    strategy_func = SELECTION_STRATEGIES.get(strategy_name, _select_vibrant)

    logger.debug(f"Color selection strategy: {strategy_name}")
    result = strategy_func(colors, avg_sat)

    return result


# ══════════════════════════════════════════════════
# DISTINÇÃO ENTRE CORES
# ══════════════════════════════════════════════════

def _ensure_distinct(colors: List[RGB], min_distance: float = 40) -> List[RGB]:
    """
    Garante que as cores são visualmente distintas.
    Se duas são muito parecidas, ajusta o value da segunda.
    """
    if len(colors) < 2:
        return colors

    result = [colors[0]]

    for color in colors[1:]:
        is_distinct = True
        for existing in result:
            if _color_distance(color, existing) < min_distance:
                is_distinct = False
                h, s, v = _rgb_to_hsv(*color)
                _, _, ev = _rgb_to_hsv(*existing)

                if ev > 0.6:
                    v = max(0.3, v - 0.3)
                else:
                    v = min(0.9, v + 0.3)

                adjusted = _hsv_to_rgb(h, s, v)

                if _color_distance(adjusted, existing) >= min_distance:
                    result.append(adjusted)
                    is_distinct = True
                break

        if is_distinct and color not in result:
            result.append(color)

    return result


# ══════════════════════════════════════════════════
# MODOS DE ATRIBUIÇÃO ÀS BANDAS
# ══════════════════════════════════════════════════

def _assign_luminance(colors: List[RGB]) -> Dict[str, RGB]:
    """
    Atribuição por LUMINÂNCIA (comportamento original).
    
    bass       = mais ESCURA
    melody     = MÉDIA
    percussion = mais CLARA
    
    Problema: bass escura fica invisível em LEDs.
    """
    sorted_by_lum = sorted(colors, key=lambda c: _get_luminance(*c))
    return {
        "bass": sorted_by_lum[0],
        "melody": sorted_by_lum[1],
        "percussion": sorted_by_lum[2],
    }


def _assign_vibrant_bass(colors: List[RGB]) -> Dict[str, RGB]:
    """
    Bass recebe a cor mais SATURADA (visível mesmo quando escuro).
    Percussion recebe a mais clara das restantes.
    Melody fica com o que sobra.
    
    Lógica: o bass não tem beat flash, então precisa de uma cor
    que "grite" por conta própria. Percussion já recebe flash
    dos beats, não precisa da cor mais forte.
    """
    sorted_by_sat = sorted(
        colors, key=lambda c: _get_saturation(*c), reverse=True
    )

    bass = sorted_by_sat[0]
    remaining = sorted_by_sat[1:]

    # Das restantes, a mais clara vai pra percussion
    remaining_by_lum = sorted(
        remaining, key=lambda c: _get_luminance(*c), reverse=True
    )

    return {
        "bass": bass,
        "percussion": remaining_by_lum[0],
        "melody": remaining_by_lum[1] if len(remaining_by_lum) > 1 else remaining_by_lum[0],
    }


def _assign_even(colors: List[RGB]) -> Dict[str, RGB]:
    """
    EQUALIZA brilho de todas as bandas.
    Todas ficam com value ~0.65 e saturação ≥0.55.
    
    O resultado é que nenhuma banda domina por causa da cor —
    a diferença visual vem 100% da intensidade do áudio.
    """
    equalized = []
    for c in colors:
        h, s, v = _rgb_to_hsv(*c)
        v = max(0.55, min(0.75, v))  # Clamp pra faixa visível
        s = max(0.55, s)  # Garante saturação
        equalized.append(_hsv_to_rgb(h, s, v))

    # Mantém ordenação por luminância pra consistência
    sorted_by_lum = sorted(equalized, key=lambda c: _get_luminance(*c))
    return {
        "bass": sorted_by_lum[0],
        "melody": sorted_by_lum[1],
        "percussion": sorted_by_lum[2],
    }


def _assign_inverted(colors: List[RGB]) -> Dict[str, RGB]:
    """
    INVERTIDO: oposto da luminância.
    
    bass       = mais CLARA (sempre visível)
    melody     = MÉDIA
    percussion = mais ESCURA (beats criam flash dramático do escuro)
    
    Efeito dramático: percussão pisca do escuro → claro.
    """
    sorted_by_lum = sorted(
        colors, key=lambda c: _get_luminance(*c), reverse=True
    )
    return {
        "bass": sorted_by_lum[0],        # Mais clara
        "melody": sorted_by_lum[1],      # Média
        "percussion": sorted_by_lum[2],  # Mais escura
    }


# ── Mapa de modos ──
ASSIGNMENT_MODES = {
    "luminance": _assign_luminance,
    "vibrant_bass": _assign_vibrant_bass,
    "even": _assign_even,
    "inverted": _assign_inverted,
}


# ══════════════════════════════════════════════════
# ATRIBUIÇÃO: DISPATCHER
# ══════════════════════════════════════════════════

def _assign_to_bands(colors: List[RGB]) -> Dict[str, RGB]:
    """
    Dispatcher: chama o modo configurado em COLOR_ASSIGNMENT_MODE.
    """
    if len(colors) < 3:
        colors = colors + [config.DEFAULT_COLOR] * (3 - len(colors))

    mode_name = getattr(config, 'COLOR_ASSIGNMENT_MODE', 'vibrant_bass').lower()
    mode_func = ASSIGNMENT_MODES.get(mode_name, _assign_vibrant_bass)

    result = mode_func(colors)

    logger.info(
        f"Band colors ({mode_name}): "
        f"🥁 perc={result['percussion']} "
        f"(S={_get_saturation(*result['percussion']):.2f} "
        f"L={_get_luminance(*result['percussion']):.2f}) | "
        f"🎹 mel={result['melody']} "
        f"(S={_get_saturation(*result['melody']):.2f} "
        f"L={_get_luminance(*result['melody']):.2f}) | "
        f"🎸 bass={result['bass']} "
        f"(S={_get_saturation(*result['bass']):.2f} "
        f"L={_get_luminance(*result['bass']):.2f})"
    )

    return result


# ══════════════════════════════════════════════════
# API PRINCIPAL
# ══════════════════════════════════════════════════

def get_album_colors(url: str) -> Dict:
    """Extrai info de cores do álbum."""
    if url in _multi_color_cache:
        return _multi_color_cache[url]

    try:
        img = _download_image(url)
        raw_colors = _extract_colors(img)
        colors = _merge_similar_colors(raw_colors)

        total = sum(c for _, c in colors) or 1
        avg_lum = sum(_get_luminance(*c) * cnt / total for c, cnt in colors)
        avg_sat = sum(_get_saturation(*c) * cnt / total for c, cnt in colors)

        result = {
            "colors": colors,
            "dominant": colors[0][0] if colors else config.DEFAULT_COLOR,
            "avg_luminance": avg_lum,
            "avg_saturation": avg_sat,
        }

        _multi_color_cache[url] = result
        return result

    except Exception as e:
        logger.error(f"Erro ao extrair cores: {e}")
        return {
            "colors": [(config.DEFAULT_COLOR, 1)],
            "dominant": config.DEFAULT_COLOR,
            "avg_luminance": 0.5,
            "avg_saturation": 0.5,
        }


def generate_band_colors_from_album(url: str) -> Dict[str, RGB]:
    """
    Gera as 3 cores para as bandas baseado na capa.

    Usa COLOR_SELECTION_STRATEGY pra escolher as 3 cores.
    Usa COLOR_ASSIGNMENT_MODE pra distribuir entre as bandas.

    Returns:
        {"percussion": RGB, "bass": RGB, "melody": RGB}
    """
    album_data = get_album_colors(url)
    colors = album_data["colors"]

    strategy = getattr(config, 'COLOR_SELECTION_STRATEGY', 'vibrant')
    mode = getattr(config, 'COLOR_ASSIGNMENT_MODE', 'vibrant_bass')

    logger.debug(
        f"Generating band colors: strategy={strategy}, mode={mode}, "
        f"album_sat={album_data['avg_saturation']:.2f}"
    )
    logger.debug(f"Raw colors: {[(c, cnt) for c, cnt in colors[:5]]}")

    # 1. Seleciona as 3 melhores (via estratégia)
    top_3 = _select_top_3_colors(colors, album_data["avg_saturation"])
    logger.debug(f"Top 3 selected ({strategy}): {top_3}")

    # 2. Garante que são distintas
    distinct = _ensure_distinct(top_3, min_distance=40)

    # 3. Atribui às bandas (via modo)
    result = _assign_to_bands(distinct)

    return result


# ══════════════════════════════════════════════════
# FUNÇÕES LEGADAS (compatibilidade)
# ══════════════════════════════════════════════════

def get_dominant_color(url: str) -> RGB:
    """Retorna a cor dominante da capa."""
    if url in _color_cache:
        return _color_cache[url]
    try:
        album_data = get_album_colors(url)
        dominant = album_data["dominant"]
        boosted = _boost_color(dominant, album_data["avg_saturation"])
        _color_cache[url] = boosted
        return boosted
    except Exception as e:
        logger.error(f"Erro: {e}")
        return config.DEFAULT_COLOR


def adjust_brightness(color: RGB, brightness: float) -> RGB:
    """Ajusta brilho mantendo H e S."""
    r, g, b = color
    h, s, _ = _rgb_to_hsv(r, g, b)
    v_new = max(0.0, min(1.0, brightness))
    return _hsv_to_rgb(h, s, v_new)


def _color_shift(color: RGB, shift: float) -> RGB:
    """Shift em direção ao branco."""
    r, g, b = color
    return (
        min(255, int(r + (255 - r) * shift)),
        min(255, int(g + (255 - g) * shift)),
        min(255, int(b + (255 - b) * shift)),
    )


def get_volume_color(color: RGB, volume: float) -> RGB:
    brightness = config.BRIGHTNESS_FLOOR + (
        volume * (config.BRIGHTNESS_BASE - config.BRIGHTNESS_FLOOR)
    )
    return adjust_brightness(color, brightness)


def get_hit_color(color: RGB, hit_type: str, volume: float) -> RGB:
    style = config.HIT_STYLE

    if hit_type == "snare":
        bright_mult = config.BRIGHTNESS_SNARE
        shift_amt = config.COLOR_SHIFT_SNARE
    elif hit_type == "kick":
        bright_mult = config.BRIGHTNESS_KICK
        shift_amt = config.COLOR_SHIFT_KICK
    elif hit_type == "peak":
        bright_mult = config.BRIGHTNESS_PEAK
        shift_amt = config.COLOR_SHIFT_PEAK
    else:
        return get_volume_color(color, volume)

    brightness = config.BRIGHTNESS_FLOOR + (
        volume * (bright_mult - config.BRIGHTNESS_FLOOR)
    )

    if style == "brightness":
        return adjust_brightness(color, brightness)
    elif style in ("color_shift", "both"):
        base = adjust_brightness(color, brightness)
        shift_scaled = shift_amt * volume
        return _color_shift(base, shift_scaled)

    return adjust_brightness(color, brightness)


def get_quantized_levels(color: RGB) -> List[RGB]:
    n = config.QUANTIZED_LEVELS
    min_b = config.BRIGHTNESS_FLOOR
    max_b = 1.0

    levels = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.5
        brightness = min_b + t * (max_b - min_b)
        levels.append(adjust_brightness(color, brightness))

    return levels


def clear_cache():
    _color_cache.clear()
    _multi_color_cache.clear()


# ══════════════════════════════════════════════════
# DEBUG / TESTE
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://i.scdn.co/image/ab67616d0000b273edf5b257be1d6593e81bb45f"

    print(f"\n🎨 Teste de Extração de Cores")
    print(f"{'=' * 60}")
    print(f"URL: {url}\n")

    # Extrai
    album_data = get_album_colors(url)

    print(f"📊 Estatísticas do álbum:")
    print(f"   Luminância média: {album_data['avg_luminance']:.2f}")
    print(f"   Saturação média:  {album_data['avg_saturation']:.2f}")

    print(f"\n🎨 Top 5 cores extraídas (raw):")
    for i, (color, count) in enumerate(album_data['colors'][:5]):
        h, s, v = _rgb_to_hsv(*color)
        lum = _get_luminance(*color)
        print(f"   {i+1}. RGB{color}")
        print(f"      H={h:.2f} S={s:.2f} V={v:.2f} L={lum:.2f} ({count} px)")

    # ── Testa todas as estratégias ──
    print(f"\n{'=' * 60}")
    print(f"🔬 COMPARAÇÃO DE ESTRATÉGIAS")
    print(f"{'=' * 60}")

    avg_sat = album_data["avg_saturation"]
    colors = album_data["colors"]

    for strat_name, strat_func in SELECTION_STRATEGIES.items():
        top_3 = strat_func(colors, avg_sat)
        print(f"\n  📌 Seleção: {strat_name}")
        for i, c in enumerate(top_3):
            h, s, v = _rgb_to_hsv(*c)
            print(f"     {i+1}. RGB{c}  S={s:.2f} V={v:.2f}")

    # ── Testa todos os modos de atribuição ──
    print(f"\n{'=' * 60}")
    print(f"🎯 COMPARAÇÃO DE ATRIBUIÇÃO")
    print(f"{'=' * 60}")

    # Usa vibrant pra ter cores boas
    top_3 = _select_vibrant(colors, avg_sat)
    distinct = _ensure_distinct(top_3)

    for mode_name, mode_func in ASSIGNMENT_MODES.items():
        result = mode_func(distinct)
        print(f"\n  📌 Atribuição: {mode_name}")
        for band in ["percussion", "bass", "melody"]:
            c = result[band]
            s = _get_saturation(*c)
            l = _get_luminance(*c)
            emoji = {"percussion": "🥁", "bass": "🎸", "melody": "🎹"}[band]
            print(f"     {emoji} {band:11s}: RGB{c}  S={s:.2f} L={l:.2f}")

    # ── Teste com config atual ──
    print(f"\n{'=' * 60}")
    print(f"✅ CONFIG ATUAL")
    print(f"   Seleção:    {getattr(config, 'COLOR_SELECTION_STRATEGY', 'vibrant')}")
    print(f"   Atribuição: {getattr(config, 'COLOR_ASSIGNMENT_MODE', 'vibrant_bass')}")
    print(f"   Min Sat:    {getattr(config, 'COLOR_MIN_SATURATION', 0.45)}")
    print(f"{'=' * 60}")

    band_colors = generate_band_colors_from_album(url)
    for band in ["percussion", "bass", "melody"]:
        c = band_colors[band]
        h, s, v = _rgb_to_hsv(*c)
        emoji = {"percussion": "🥁", "bass": "🎸", "melody": "🎹"}[band]
        print(f"   {emoji} {band:11s}: RGB{c}  H={h:.2f} S={s:.2f} V={v:.2f}")

    print(f"\n{'=' * 60}")
    print("✅ Done!")