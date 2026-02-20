# chase_explorer.py
"""
Explora os LEDs individuais de cada dispositivo.
Descobre quais suportam controle por zona/LED.
"""

import time
import logging

from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

import config

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    print("\n" + "=" * 60)
    print("  🔬 CHASE EXPLORER - Investigando LEDs individuais")
    print("=" * 60)
    
    client = OpenRGBClient(
        address=config.OPENRGB_HOST,
        port=config.OPENRGB_PORT,
        name="ChaseExplorer",
    )
    
    print(f"\n  ✅ Conectado! {len(client.devices)} dispositivo(s)\n")
    
    for i, dev in enumerate(client.devices):
        print(f"  ═══ [{i}] {dev.name} ═══")
        print(f"      Tipo: {dev.type}")
        print(f"      LEDs: {len(dev.leds)}")
        
        # Lista LEDs individuais
        if dev.leds:
            print(f"      LED names:")
            for j, led in enumerate(dev.leds):
                print(f"        [{j}] {led.name}")
        
        # Lista zonas
        if dev.zones:
            print(f"      Zones:")
            for j, zone in enumerate(dev.zones):
                print(f"        [{j}] {zone.name} ({len(zone.leds)} LEDs)")
        
        # Modos
        print(f"      Modos:")
        for j, mode in enumerate(dev.modes):
            active = " ◀ ATUAL" if j == dev.active_mode else ""
            print(f"        [{j}] {mode.name}{active}")
        
        print()
    
    # ═══ TESTE CHASE ═══
    
    print("  Qual dispositivo testar? (número)")
    dev_idx = int(input("  > "))
    dev = client.devices[dev_idx]
    
    print(f"\n  Testando: {dev.name} ({len(dev.leds)} LEDs)")
    
    # Coloca em modo Direct
    for j, mode in enumerate(dev.modes):
        if mode.name.lower() in ("direct", "static"):
            dev.set_mode(j)
            break
    
    # ═══ TESTE 1: Acende cada LED individualmente ═══
    
    print("\n  [1] Acendendo cada LED individualmente...")
    print("      Observe quais LEDs existem e onde ficam.")
    input("      ENTER pra começar...")
    
    # Apaga tudo
    dev.set_color(RGBColor(0, 0, 0))
    time.sleep(0.5)
    
    for j in range(len(dev.leds)):
        # Cria array de cores - tudo apagado exceto o LED atual
        colors = [RGBColor(0, 0, 0)] * len(dev.leds)
        colors[j] = RGBColor(255, 0, 0)  # Vermelho
        
        try:
            dev.set_colors(colors)
            print(f"\r      LED [{j}] {dev.leds[j].name}    ", end="", flush=True)
            time.sleep(0.3)
        except Exception as e:
            print(f"\r      LED [{j}] ERRO: {e}    ", end="", flush=True)
            time.sleep(0.1)
    
    print("\n")
    
    # ═══ TESTE 2: Chase effect ═══
    
    print("  [2] Chase effect (onda percorrendo os LEDs)")
    input("      ENTER pra começar...")
    
    BASE = RGBColor(30, 0, 60)     # Roxo escuro (fundo)
    CHASE = RGBColor(255, 50, 255)  # Rosa brilhante (onda)
    TAIL_LEN = 3                    # Comprimento da cauda
    
    n_leds = len(dev.leds)
    
    try:
        for _round in range(3):  # 3 voltas
            for pos in range(n_leds):
                colors = [BASE] * n_leds
                
                # Onda com cauda
                for t in range(TAIL_LEN):
                    idx = (pos - t) % n_leds
                    # Fade na cauda
                    fade = 1.0 - (t / TAIL_LEN)
                    r = int(CHASE.red * fade + BASE.red * (1 - fade))
                    g = int(CHASE.green * fade + BASE.green * (1 - fade))
                    b = int(CHASE.blue * fade + BASE.blue * (1 - fade))
                    colors[idx] = RGBColor(r, g, b)
                
                dev.set_colors(colors)
                time.sleep(0.06)
    
    except Exception as e:
        print(f"      Chase FALHOU: {e}")
        print(f"      Esse dispositivo pode não suportar set_colors individual.")
    
    print()
    
    # ═══ TESTE 3: Pulse dos LEDs (simula beat) ═══
    
    print("  [3] Pulse (todos pulsam juntos)")
    input("      ENTER pra começar...")
    
    try:
        for _beat in range(8):
            # Flash
            dev.set_color(RGBColor(255, 100, 255))
            time.sleep(0.08)
            
            # Volta
            dev.set_color(RGBColor(40, 0, 80))
            time.sleep(0.4)
    
    except Exception as e:
        print(f"      Pulse FALHOU: {e}")
    
    print()
    
    # ═══ TESTE 4: Chase reagindo a "beat" simulado ═══
    
    print("  [4] Chase + beat (onda acelera no beat)")
    input("      ENTER pra começar...")
    
    try:
        pos = 0
        speed = 0.08
        
        for frame in range(200):
            colors = [BASE] * n_leds
            
            for t in range(TAIL_LEN):
                idx = (pos - t) % n_leds
                fade = 1.0 - (t / TAIL_LEN)
                r = int(CHASE.red * fade + BASE.red * (1 - fade))
                g = int(CHASE.green * fade + BASE.green * (1 - fade))
                b = int(CHASE.blue * fade + BASE.blue * (1 - fade))
                colors[idx] = RGBColor(r, g, b)
            
            dev.set_colors(colors)
            
            # Simula beat a cada 30 frames
            if frame % 30 == 0:
                speed = 0.02  # Acelera
                CHASE = RGBColor(255, 200, 255)  # Mais brilhante
            else:
                speed = min(speed + 0.002, 0.08)  # Desacelera
                CHASE = RGBColor(255, 50, 255)
            
            pos = (pos + 1) % n_leds
            time.sleep(speed)
    
    except Exception as e:
        print(f"      Chase+beat FALHOU: {e}")
    
    # Limpa
    dev.set_color(RGBColor(100, 0, 200))
    
    print("\n  Resultados:")
    print("    [1] LEDs individuais funcionaram?")
    print("    [2] Chase funcionou?")
    print("    [3] Pulse funcionou?")
    print("    [4] Chase + beat funcionou?")
    
    resp = input("\n  Quais funcionaram? (ex: '1234' ou '13'): ").strip()
    
    print(f"\n  Testes que funcionaram: {resp}")
    
    if "2" in resp or "4" in resp:
        print("  ✅ Chase é possível nesse dispositivo!")
        print(f"     {n_leds} LEDs disponíveis pra animação.")
    elif "1" in resp:
        print("  ⚠️ LEDs individuais funcionam mas chase não.")
        print("     Pode ser que o dispositivo é lento demais pra animação.")
    else:
        print("  ❌ LEDs individuais não funcionam.")
        print("     Esse dispositivo não suporta chase.")
    
    client.disconnect()
    print("\n  Done!")


if __name__ == "__main__":
    main()