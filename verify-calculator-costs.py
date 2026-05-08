#!/usr/bin/env python3
import requests
import json

# URLs de los 3 estimados
urls = {
    'On-Demand': 'https://calculator.aws/#/estimate?id=b85917e49169b0323353e144b2365f7505e02edf',
    'SP 1yr': 'https://calculator.aws/#/estimate?id=3212057dc73dacbe78827859f33ad41ea4a53e91',
    'SP 3yr': 'https://calculator.aws/#/estimate?id=62d931b4d78ff55624c6524b6651be2cf599b0b7'
}

# URLs CloudFront para obtener JSON (extraer ID)
cf_base = 'https://d3knqfixx3sbls.cloudfront.net/'
ids = {
    'On-Demand': 'b85917e49169b0323353e144b2365f7505e02edf',
    'SP 1yr': '3212057dc73dacbe78827859f33ad41ea4a53e91',
    'SP 3yr': '62d931b4d78ff55624c6524b6651be2cf599b0b7'
}

# Valores esperados del TCO (del Excel)
expected = {
    'On-Demand': {'monthly': 52923, 'annual': 635076},
    'SP 1yr': {'monthly': 44984, 'annual': 539808},
    'SP 3yr': {'monthly': 36369, 'annual': 436428}
}

print("=" * 80)
print("VERIFICACIÓN DE COSTOS EN CALCULADORAS AWS")
print("=" * 80)

for scenario, estimate_id in ids.items():
    print(f"\n📊 Escenario: {scenario}")
    print(f"   URL: {urls[scenario]}")
    print(f"   ID: {estimate_id}")
    
    try:
        # Intenta obtener el JSON desde CloudFront
        cf_url = cf_base + estimate_id
        print(f"   Descargando desde: {cf_url}")
        
        response = requests.get(cf_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Calcular totales
            total_monthly = 0
            total_upfront = 0
            
            if 'groups' in data:
                for group_name, group_data in data['groups'].items():
                    if 'groupSubtotal' in group_data:
                        total_monthly += group_data['groupSubtotal'].get('monthly', 0)
                        total_upfront += group_data['groupSubtotal'].get('upfront', 0)
            
            total_annual = (total_monthly * 12) + total_upfront
            
            print(f"\n   💰 Valores Reales:")
            print(f"      Mensual:  ${total_monthly:,.2f}")
            print(f"      Inicial:  ${total_upfront:,.2f}")
            print(f"      Anual:    ${total_annual:,.2f}")
            
            print(f"\n   ✓ Valores Esperados (TCO):")
            print(f"      Mensual:  ${expected[scenario]['monthly']:,.2f}")
            print(f"      Anual:    ${expected[scenario]['annual']:,.2f}")
            
            # Comparar
            monthly_diff = total_monthly - expected[scenario]['monthly']
            annual_diff = total_annual - expected[scenario]['annual']
            monthly_pct = (monthly_diff / expected[scenario]['monthly'] * 100) if expected[scenario]['monthly'] != 0 else 0
            
            print(f"\n   📈 Diferencia:")
            print(f"      Mensual:  ${monthly_diff:+,.2f} ({monthly_pct:+.1f}%)")
            print(f"      Anual:    ${annual_diff:+,.2f}")
            
            if abs(monthly_diff) < 100:
                print(f"   ✅ COINCIDE (diferencia < $100)")
            elif abs(monthly_diff) < 1000:
                print(f"   ⚠️  CERCANO (diferencia < $1,000)")
            else:
                print(f"   ❌ DISCREPANCIA SIGNIFICATIVA (diferencia > $1,000)")
                
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  No se pudo conectar: {str(e)}")
        print(f"   💡 Nota: AWS no sirve JSON directamente. Necesitas abrir la URL en navegador")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("NOTAS:")
print("- AWS Calculator calcula precios en el navegador (JavaScript)")
print("- Los valores mostrados son cálculos locales sin actualización del servidor")
print("- Para ver valores reales, abre cada URL en navegador y captura la pantalla")
print("=" * 80)
