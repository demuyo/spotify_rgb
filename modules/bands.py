# debug_zone_resize.py
"""
Diagnostica e corrige zonas com LEDs faltando.
Foco: watercooler com 1/4 dos LEDs apagados no Direct mode.
"""

import sys
import time

try:
    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor
except ImportError:
    print("pip install openrgb-python")
    sys.exit(1)


def main():
    print()
    print("=" * 60)
    print("  🌀 FIX: LEDs APAGADOS NO WATERCOOLER")
    print("=" * 60)
    print()
    
    client = OpenRGBClient('127.0.0.1', 6742, name='ZoneFix')
    devices = client.devices
    
    # ══════════════════════════════════════════════
    # PASSO 1: Encontra devices ARGB
    # ══════════════════════════════════════════════
    
    print("📦 DEVICES DETECTADOS:")
    print()
    
    argb_candidates = []
    
    for i, dev in enumerate(devices):
        dev_leds = len(dev.leds)
        print(f"  [{i}] {dev.name} → {dev_leds} LEDs")
        
        # Mostra zonas
        for z, zone in enumerate(dev.zones):
            zone_leds = len(zone.leds) if hasattr(zone, 'leds') else zone.leds_count
            
            # Tenta pegar min/max
            zone_min = getattr(zone, 'leds_min', '?')
            zone_max = getattr(zone, 'leds_max', '?')
            
            resizable = "RESIZABLE" if getattr(zone, 'type', None) == 2 or zone_max != '?' else ""
            
            print(f"       Zona {z}: '{zone.name}' → {zone_leds} LEDs "
                  f"(min={zone_min}, max={zone_max}) {resizable}")
        
        # Detecta se é ARGB/addressable
        name_lower = dev.name.lower()
        if 'addressable' in name_lower or 'argb' in name_lower:
            argb_candidates.append((i, dev))
        
        print()
    
    if not argb_candidates:
        print("⚠️  Nenhum device ARGB encontrado!")
        print("    Seus devices ARGB podem ter outro nome.")
        print()
        try:
            idx = int(input("  Digite o índice do device do watercooler: "))
            if 0 <= idx < len(devices):
                argb_candidates = [(idx, devices[idx])]
        except:
            pass
    
    if not argb_candidates:
        print("Nenhum device selecionado. Saindo.")
        return
    
    # ══════════════════════════════════════════════
    # PASSO 2: Identifica o problema
    # ══════════════════════════════════════════════
    
    print()
    print("=" * 60)
    print("  PASSO 1: IDENTIFICAR O PROBLEMA")
    print("=" * 60)
    print()
    
    for dev_idx, dev in argb_candidates:
        print(f"📦 [{dev_idx}] {dev.name}")
        print(f"   LEDs totais (OpenRGB): {len(dev.leds)}")
        print()
        
        # Primeiro: Static (todos acendem)
        print("   🔹 Acendendo em STATIC mode...")
        try:
            modes = [m.name.lower() for m in dev.modes]
            if 'static' in modes:
                static_idx = modes.index('static')
                dev.set_mode(static_idx)
                time.sleep(0.1)
                dev.set_color(RGBColor(255, 255, 255))
                time.sleep(0.5)
        except Exception as e:
            print(f"   Erro no Static: {e}")
        
        static_count = input("   Quantos LEDs acenderam no STATIC? ").strip()
        
        # Agora: Direct
        print("   🔹 Acendendo em DIRECT mode...")
        try:
            dev.set_mode('direct')
            time.sleep(0.1)
            colors = [RGBColor(0, 255, 0)] * len(dev.leds)
            dev.set_colors(colors)
            time.sleep(0.5)
        except Exception as e:
            print(f"   Erro no Direct: {e}")
        
        direct_count = input("   Quantos LEDs acenderam no DIRECT? ").strip()
        
        if static_count.isdigit() and direct_count.isdigit():
            s = int(static_count)
            d = int(direct_count)
            missing = s - d
            
            if missing > 0:
                print()
                print(f"   ⚠️  PROBLEMA CONFIRMADO!")
                print(f"      Static: {s} LEDs")
                print(f"      Direct: {d} LEDs")
                print(f"      Faltam: {missing} LEDs no Direct mode")
                print()
                
                # Calcula
                openrgb_count = len(dev.leds)
                real_count = s
                
                if openrgb_count < real_count:
                    print(f"   🔧 CAUSA: OpenRGB acha que tem {openrgb_count} LEDs,")
                    print(f"             mas o watercooler tem {real_count}!")
                    print(f"             Precisa REDIMENSIONAR a zona pra {real_count}.")
                elif openrgb_count == real_count:
                    print(f"   🔧 CAUSA: OpenRGB sabe que tem {openrgb_count} LEDs,")
                    print(f"             mas o Direct mode só controla {d}.")
                    print(f"             Pode ser limite do controlador ASUS.")
                else:
                    print(f"   🤔 OpenRGB diz {openrgb_count}, Static mostra {s}, Direct mostra {d}")
            elif missing == 0:
                print(f"\n   ✅ Todos os LEDs funcionam em ambos os modos!")
            else:
                print(f"\n   🤔 Mais LEDs no Direct que no Static? Estranho...")
        
        # Apaga
        try:
            dev.set_color(RGBColor(0, 0, 0))
        except:
            pass
    
    # ══════════════════════════════════════════════
    # PASSO 3: Tenta soluções
    # ══════════════════════════════════════════════
    
    print()
    print("=" * 60)
    print("  PASSO 2: TENTANDO SOLUÇÕES")
    print("=" * 60)
    print()
    print("  1. Resize de zona (OpenRGB)")
    print("  2. Teste com mais LEDs no Direct")
    print("  3. Teste zona por zona")
    print("  4. Teste: Static primeiro, depois Direct")
    print("  5. Teste: Enviar cores em partes")
    print("  6. Ver instruções manuais")
    print("  0. Sair")
    
    while True:
        print()
        try:
            choice = input("  Escolha: ").strip()
        except KeyboardInterrupt:
            break
        
        if choice == '0':
            break
        elif choice == '1':
            try_resize(client, devices, argb_candidates)
        elif choice == '2':
            try_more_leds(devices, argb_candidates)
        elif choice == '3':
            try_zone_by_zone(devices, argb_candidates)
        elif choice == '4':
            try_static_then_direct(devices, argb_candidates)
        elif choice == '5':
            try_partial_update(devices, argb_candidates)
        elif choice == '6':
            show_manual_instructions()
    
    print("\n👋 Fim!")


def try_resize(client, devices, argb_candidates):
    """Tenta redimensionar a zona via API."""
    print()
    print("  🔧 RESIZE DE ZONA")
    print()
    
    for dev_idx, dev in argb_candidates:
        print(f"  Device [{dev_idx}] {dev.name}")
        
        for z, zone in enumerate(dev.zones):
            zone_leds = len(zone.leds) if hasattr(zone, 'leds') else zone.leds_count
            zone_max = getattr(zone, 'leds_max', None)
            zone_min = getattr(zone, 'leds_min', None)
            
            print(f"     Zona {z}: '{zone.name}' → {zone_leds} LEDs")
            
            if zone_max is not None:
                print(f"        Máximo permitido: {zone_max}")
            
            # Tenta resize
            new_size = input(f"     Novo tamanho? (Enter = manter {zone_leds}): ").strip()
            
            if new_size.isdigit():
                new_size = int(new_size)
                
                try:
                    # Método 1: resize via zone
                    if hasattr(zone, 'resize'):
                        zone.resize(new_size)
                        print(f"     ✅ Zona redimensionada pra {new_size}!")
                    
                    # Método 2: resize via client
                    elif hasattr(client, 'resize_zone'):
                        client.resize_zone(dev_idx, z, new_size)
                        print(f"     ✅ Zona redimensionada pra {new_size}!")
                    
                    else:
                        print(f"     ❌ API de resize não disponível")
                        print(f"        Faça manualmente no OpenRGB!")
                    
                    # Recarrega device
                    time.sleep(0.5)
                    try:
                        client.update()
                    except:
                        pass
                    
                except Exception as e:
                    print(f"     ❌ Erro no resize: {e}")
                    print(f"        Tente fazer manualmente no OpenRGB")
    
    # Testa se funcionou
    print()
    test = input("  Testar Direct mode agora? (s/n): ").strip().lower()
    if test == 's':
        for dev_idx, dev in argb_candidates:
            try:
                dev.set_mode('direct')
                time.sleep(0.1)
                colors = [RGBColor(0, 255, 255)] * len(dev.leds)
                dev.set_colors(colors)
                print(f"  [{dev_idx}] {dev.name}: CIANO ({len(dev.leds)} LEDs)")
            except Exception as e:
                print(f"  [{dev_idx}] Erro: {e}")
        
        input("\n  Todos os LEDs acenderam? [Enter]")
        
        for _, dev in argb_candidates:
            try:
                dev.set_color(RGBColor(0, 0, 0))
            except:
                pass


def try_more_leds(devices, argb_candidates):
    """Tenta enviar mais LEDs do que o OpenRGB detectou."""
    print()
    print("  🔧 TESTE: ENVIAR MAIS LEDS")
    print()
    
    for dev_idx, dev in argb_candidates:
        current = len(dev.leds)
        print(f"  Device [{dev_idx}] {dev.name}: {current} LEDs detectados")
        
        new_count = input(f"  Quantos LEDs enviar? (ex: {current + 12}): ").strip()
        
        if new_count.isdigit():
            n = int(new_count)
            
            try:
                dev.set_mode('direct')
                time.sleep(0.1)
                
                colors = [RGBColor(255, 0, 255)] * n  # Magenta
                
                try:
                    dev.set_colors(colors)
                    print(f"  Enviado {n} LEDs em MAGENTA")
                except Exception as e:
                    print(f"  Erro com {n} LEDs: {e}")
                    print(f"  Tentando truncar pra {current}...")
                    dev.set_colors(colors[:current])
                
            except Exception as e:
                print(f"  Erro: {e}")
        
        resp = input("  Mais LEDs acenderam? (s/n): ").strip().lower()
        if resp == 's':
            print(f"  ✅ Funcionou! Use LED_COUNT ou resize pra {n}")
        
        try:
            dev.set_color(RGBColor(0, 0, 0))
        except:
            pass


def try_zone_by_zone(devices, argb_candidates):
    """Tenta controlar cada zona separadamente."""
    print()
    print("  🔧 TESTE: ZONA POR ZONA")
    print("  Acende cada zona em cor diferente")
    print()
    
    zone_colors = [
        (RGBColor(255, 0, 0), "VERMELHO"),
        (RGBColor(0, 255, 0), "VERDE"),
        (RGBColor(0, 0, 255), "AZUL"),
        (RGBColor(255, 255, 0), "AMARELO"),
        (RGBColor(255, 0, 255), "MAGENTA"),
        (RGBColor(0, 255, 255), "CIANO"),
    ]
    
    for dev_idx, dev in argb_candidates:
        print(f"  📦 [{dev_idx}] {dev.name}")
        
        try:
            dev.set_mode('direct')
            time.sleep(0.1)
        except:
            pass
        
        # Primeiro: apaga tudo
        try:
            dev.set_color(RGBColor(0, 0, 0))
        except:
            pass
        
        time.sleep(0.3)
        
        # Acende zona por zona
        all_colors = [RGBColor(0, 0, 0)] * len(dev.leds)
        offset = 0
        
        for z, zone in enumerate(dev.zones):
            zone_leds = len(zone.leds) if hasattr(zone, 'leds') else zone.leds_count
            color, name = zone_colors[z % len(zone_colors)]
            
            for i in range(zone_leds):
                if offset + i < len(all_colors):
                    all_colors[offset + i] = color
            
            print(f"     Zona {z}: '{zone.name}' → {zone_leds} LEDs = {name}")
            
            offset += zone_leds
        
        try:
            dev.set_colors(all_colors)
        except Exception as e:
            print(f"     Erro: {e}")
        
        print()
        print("     Qual zona tem LEDs APAGADOS?")
        problem_zone = input("     (Número da zona, ou Enter se todas OK): ").strip()
        
        if problem_zone.isdigit():
            pz = int(problem_zone)
            if pz < len(dev.zones):
                zone = dev.zones[pz]
                zone_leds = len(zone.leds) if hasattr(zone, 'leds') else zone.leds_count
                print(f"\n     ⚠️  Zona {pz} '{zone.name}' com problema!")
                print(f"         LEDs configurados: {zone_leds}")
                print(f"         Provavelmente precisa de mais LEDs!")
                
                qtd = input(f"         Quantos LEDs DEVERIA ter? ").strip()
                if qtd.isdigit():
                    print(f"\n     📋 SOLUÇÃO:")
                    print(f"         No OpenRGB:")
                    print(f"         1. Clique no device '{dev.name}'")
                    print(f"         2. Ache a zona '{zone.name}'")
                    print(f"         3. Mude o tamanho de {zone_leds} pra {qtd}")
                    print(f"         4. Clique 'Resize Zone'")
                    print(f"         5. Salve o perfil")
        
        # Apaga
        try:
            dev.set_color(RGBColor(0, 0, 0))
        except:
            pass
        
        print()


def try_static_then_direct(devices, argb_candidates):
    """Workaround: usa Static pra "acordar" os LEDs, depois Direct."""
    print()
    print("  🔧 WORKAROUND: STATIC → DIRECT")
    print("  Acende via Static primeiro, depois muda pra Direct")
    print()
    
    for dev_idx, dev in argb_candidates:
        print(f"  [{dev_idx}] {dev.name}")
        
        try:
            # Passo 1: Static branco
            modes = [m.name.lower() for m in dev.modes]
            if 'static' in modes:
                static_idx = modes.index('static')
                dev.set_mode(static_idx)
                time.sleep(0.1)
                dev.set_color(RGBColor(50, 50, 50))  # Branco baixo
                time.sleep(0.5)
                print("     1. Static aplicado (branco fraco)")
            
            # Passo 2: Direct com cores
            dev.set_mode('direct')
            time.sleep(0.2)
            
            colors = [RGBColor(0, 255, 0)] * len(dev.leds)
            dev.set_colors(colors)
            print("     2. Direct aplicado (verde)")
            
        except Exception as e:
            print(f"     Erro: {e}")
    
    resp = input("\n  Todos os LEDs ficaram VERDES? (s/n): ").strip().lower()
    
    if resp == 's':
        print("  ✅ WORKAROUND FUNCIONA!")
        print("  Vou implementar isso no openrgb_module.py")
    else:
        print("  ❌ Não funcionou")
    
    for _, dev in argb_candidates:
        try:
            dev.set_color(RGBColor(0, 0, 0))
        except:
            pass


def try_partial_update(devices, argb_candidates):
    """Tenta atualizar LEDs em partes menores."""
    print()
    print("  🔧 TESTE: UPDATE PARCIAL")
    print("  Envia cores em blocos pequenos")
    print()
    
    for dev_idx, dev in argb_candidates:
        total = len(dev.leds)
        print(f"  [{dev_idx}] {dev.name}: {total} LEDs")
        
        try:
            dev.set_mode('direct')
            time.sleep(0.1)
        except:
            pass
        
        # Acende em blocos de 5
        block_size = 5
        
        for start in range(0, total, block_size):
            end = min(start + block_size, total)
            
            colors = [RGBColor(0, 0, 0)] * total
            for i in range(start, end):
                colors[i] = RGBColor(255, 100, 0)  # Laranja
            
            try:
                dev.set_colors(colors)
            except:
                pass
            
            print(f"\r     LEDs {start}-{end-1} em LARANJA", end="", flush=True)
            time.sleep(0.3)
        
        print()
        
        # Agora tenta tudo junto
        print(f"     Agora todos juntos...")
        
        try:
            colors = [RGBColor(0, 255, 255)] * total  # Ciano
            dev.set_colors(colors)
        except Exception as e:
            print(f"     Erro: {e}")
        
        resp = input("     Todos acenderam? (s/n): ").strip().lower()
        
        for _, dev in argb_candidates:
            try:
                dev.set_color(RGBColor(0, 0, 0))
            except:
                pass


def show_manual_instructions():
    """Mostra instruções pra fix manual no OpenRGB."""
    print()
    print("=" * 60)
    print("  📋 INSTRUÇÕES MANUAIS - FIX NO OPENRGB")
    print("=" * 60)
    print()
    print("  MÉTODO 1: RESIZE DE ZONA")
    print("  ─────────────────────────")
    print("  1. Abra o OpenRGB")
    print("  2. Clique no device do watercooler")
    print("     (provavelmente 'Aura Addressable X')")
    print("  3. Na aba 'LEDs', veja quantos LEDs tem")
    print("  4. Na aba 'Device Info' ou 'Zones':")
    print("     - Encontre a zona que tem poucos LEDs")
    print("     - Mude o número pra quantidade REAL")
    print("     - Clique 'Resize Zone'")
    print("  5. Salve o perfil")
    print()
    print("  MÉTODO 2: OPENRGB SETTINGS")
    print("  ───────────────────────────")
    print("  1. OpenRGB → Settings → ASUS")
    print("  2. Procure por 'ARGB Header' ou 'Addressable'")
    print("  3. Aumente o número de LEDs configurado")
    print("  4. Reinicie o OpenRGB")
    print()
    print("  MÉTODO 3: OPENRGB.JSON")
    print("  ───────────────────────")
    print("  1. Feche o OpenRGB")
    print("  2. Abra o arquivo:")
    print("     %APPDATA%\\OpenRGB\\OpenRGB.json")
    print("     OU a pasta onde o OpenRGB está instalado")
    print("  3. Procure por 'Addressable' no JSON")
    print("  4. Mude 'leds_count' pra o valor correto")
    print("  5. Salve e reabra o OpenRGB")
    print()
    print("  DICA: COMO SABER QUANTOS LEDs TEM?")
    print("  ────────────────────────────────────")
    print("  RiseMode 240mm geralmente tem:")
    print("    - 2 ventoinhas de 120mm")
    print("    - Cada ventoinha: 12-18 LEDs ARGB")
    print("    - Bomba/bloco: 0-12 LEDs")
    print("    - Total provável: 24-48 LEDs")
    print()
    print("  Se no Static acendem X LEDs, configure")
    print("  as zonas pra somar X no total.")
    print()
    input("  [Enter para continuar]")


if __name__ == "__main__":
    main()