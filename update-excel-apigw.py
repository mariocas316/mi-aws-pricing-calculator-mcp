#!/usr/bin/env python3
"""
Calcula costos de API Gateway para 80M llamadas mensuales
Y actualiza Excel con los costos
"""
import pandas as pd
from pathlib import Path

# Precios AWS API Gateway (precio actual aproximado)
# https://aws.amazon.com/api-gateway/pricing/
# $3.50 por millón de solicitudes (tier 1: primeros 333 millones)

API_CALLS_MONTHLY = 80_000_000  # 80 millones
API_COST_PER_MILLION = 3.50

# Data Transfer aproximada
DATA_TRANSFER_GB = 100
DATA_TRANSFER_COST_PER_GB = 0.09

# CloudWatch Logs
LOGS_GB = 50
LOGS_COST_PER_GB = 0.50

# Calcular costos
print("=" * 80)
print("ANÁLISIS DE COSTOS - API GATEWAY (80M llamadas/mes)")
print("=" * 80)

# Desglose
api_calls_millions = API_CALLS_MONTHLY / 1_000_000
api_cost_monthly = (api_calls_millions * API_COST_PER_MILLION)
data_transfer_cost_monthly = DATA_TRANSFER_GB * DATA_TRANSFER_COST_PER_GB
logs_cost_monthly = LOGS_GB * LOGS_COST_PER_GB
total_monthly_ondemand = api_cost_monthly + data_transfer_cost_monthly + logs_cost_monthly

print(f"\n💰 COSTOS MENSUALES (On-Demand):")
print(f"   • API Calls ({api_calls_millions}M × ${API_COST_PER_MILLION}/M):  ${api_cost_monthly:,.2f}")
print(f"   • Data Transfer ({DATA_TRANSFER_GB}GB × ${DATA_TRANSFER_COST_PER_GB}/GB):    ${data_transfer_cost_monthly:,.2f}")
print(f"   • CloudWatch Logs ({LOGS_GB}GB × ${LOGS_COST_PER_GB}/GB):   ${logs_cost_monthly:,.2f}")
print(f"   {'─' * 50}")
print(f"   • TOTAL On-Demand:                 ${total_monthly_ondemand:,.2f}")

# Savings Plans (aproximados)
# SP 1yr típicamente da ~25% descuento en compute/API
# SP 3yr típicamente da ~45% descuento en compute/API
sp1yr_discount = 0.25
sp3yr_discount = 0.45

cost_sp1yr_monthly = total_monthly_ondemand * (1 - sp1yr_discount)
cost_sp3yr_monthly = total_monthly_ondemand * (1 - sp3yr_discount)

print(f"\n📊 ESCENARIOS CON SAVINGS PLANS:")
print(f"   • SP 1yr (25% desc):              ${cost_sp1yr_monthly:,.2f}/mes")
print(f"   • SP 3yr (45% desc):              ${cost_sp3yr_monthly:,.2f}/mes")

# Anuales
annual_ondemand = total_monthly_ondemand * 12
annual_sp1yr = cost_sp1yr_monthly * 12
annual_sp3yr = cost_sp3yr_monthly * 12

print(f"\n📈 COSTOS ANUALES:")
print(f"   • On-Demand:                      ${annual_ondemand:,.2f}")
print(f"   • SP 1yr:                         ${annual_sp1yr:,.2f}")
print(f"   • SP 3yr:                         ${annual_sp3yr:,.2f}")

# Guardar en Excel
excel_file = Path('archivostcoonet/TCO_Migracion_Azure_AWS_OnNet_v2.xlsx')

print(f"\n📝 Actualizando Excel: {excel_file}")

# Leer archivo
df = pd.read_excel(excel_file, sheet_name='1. Resumen Ejecutivo TCO')

# Encontrar fila para APIM (probablemente sea la siguiente a AKS)
# AKS está en fila 8 (índice 7 porque pandas cuenta desde 0)
# APIM debería estar en fila 9 (índice 8)

# Primero, verificar si existe ya una fila para APIM
# Si no, la crearemos

print("\nBuscando fila para APIM en Excel...")

# Buscar "APIM" o "API Management" en la columna A
apim_row = None
for idx, val in enumerate(df.iloc[:, 0]):
    if val and 'APIM' in str(val).upper():
        apim_row = idx
        print(f"✓ Fila {idx + 2} (Excel row {idx + 1}): {val}")
        break

if apim_row is None:
    # Crear nueva fila después de AKS (asumiendo que está en row 8, índice 7)
    apim_row = 8  # Esto será la fila 9 en Excel
    print(f"\nℹ️  No encontrada - Creando nueva fila en posición {apim_row + 2} (Excel row {apim_row + 1})")
    
    # Insertar nueva fila
    new_row = pd.DataFrame([[None] * len(df.columns)], columns=df.columns)
    df = pd.concat([df.iloc[:apim_row+1], new_row, df.iloc[apim_row+1:]]).reset_index(drop=True)

# Actualizar valores en la fila APIM
print(f"\n✏️  Actualizando fila {apim_row + 2} (Excel row {apim_row + 1}):")

# Columnas (ajustar según estructura real)
# Basado en el código anterior, sabemos:
# Col A: Servicio Azure
# Col B: Servicio AWS
# Col C: Estrategia
# Col D: Azure Mensual
# Col E: Azure Anual
# Col F: AWS On-Demand Mensual
# Col G: AWS SP 1yr Mensual
# Col H: AWS SP 3yr Mensual
# Col I: Ahorro Mensual
# Col J: Ahorro %
# Col K: Ahorro Anual

# Llenar datos
if apim_row < len(df):
    # Información básica
    df.iloc[apim_row, 0] = 'APIM (11 instancias, 80M llamadas/mes)'
    df.iloc[apim_row, 1] = 'Amazon API Gateway'
    df.iloc[apim_row, 2] = 'Replatform'
    
    print(f"  • Col A: APIM (11 instancias, 80M llamadas/mes)")
    print(f"  • Col B: Amazon API Gateway")
    print(f"  • Col C: Replatform")
    
    # Costos Azure (aproximar basado en info disponible)
    # APIM Developer = ~$40-50/mes
    # APIM Basic = ~$100/mes
    # APIM Premium = ~$300-400/mes
    # 8 Dev + 1 Basic + 2 Premium ≈ (8*50) + 100 + (2*350) = 1100/mes aprox
    azure_monthly = 1100
    azure_annual = azure_monthly * 12
    
    df.iloc[apim_row, 3] = azure_monthly  # Col D
    df.iloc[apim_row, 4] = azure_annual   # Col E
    
    print(f"  • Col D (Azure Monthly): ${azure_monthly:,.2f}")
    print(f"  • Col E (Azure Annual): ${azure_annual:,.2f}")
    
    # Costos AWS
    df.iloc[apim_row, 5] = round(total_monthly_ondemand, 2)     # Col F: On-Demand
    df.iloc[apim_row, 6] = round(cost_sp1yr_monthly, 2)         # Col G: SP 1yr
    df.iloc[apim_row, 7] = round(cost_sp3yr_monthly, 2)         # Col H: SP 3yr
    
    print(f"  • Col F (AWS On-Demand): ${total_monthly_ondemand:,.2f}")
    print(f"  • Col G (AWS SP 1yr): ${cost_sp1yr_monthly:,.2f}")
    print(f"  • Col H (AWS SP 3yr): ${cost_sp3yr_monthly:,.2f}")
    
    # Ahorros (respecto a On-Demand AWS)
    ahorro_mensual = total_monthly_ondemand - cost_sp3yr_monthly
    ahorro_porcentaje = (ahorro_mensual / total_monthly_ondemand) * 100 if total_monthly_ondemand > 0 else 0
    ahorro_anual = ahorro_mensual * 12
    
    df.iloc[apim_row, 8] = round(ahorro_mensual, 2)      # Col I: Ahorro Mensual
    df.iloc[apim_row, 9] = round(ahorro_porcentaje / 100, 6)  # Col J: Ahorro %
    df.iloc[apim_row, 10] = round(ahorro_anual, 2)       # Col K: Ahorro Anual
    
    print(f"  • Col I (Ahorro Mensual SP3yr): ${ahorro_mensual:,.2f}")
    print(f"  • Col J (Ahorro %): {ahorro_porcentaje:.1f}%")
    print(f"  • Col K (Ahorro Anual): ${ahorro_anual:,.2f}")
    
    # URLs de calculadora (a llenar manualmente después)
    # Col N, O, P para las URLs
    print(f"\n⚠️  URLs de calculadora (para rellenar manualmente):")
    print(f"  • Fila {apim_row + 2}, Col N (On-Demand): https://calculator.aws/#/estimate?id=17a2b57f568036aee836395e441cd6849d45177a")
    print(f"  • Fila {apim_row + 2}, Col O (SP 1yr): https://calculator.aws/#/estimate?id=1963f6eb5befc2b1ec267ab873d93a41a22dcb47")
    print(f"  • Fila {apim_row + 2}, Col P (SP 3yr): https://calculator.aws/#/estimate?id=8373dd6d9be6d6ec0a78ef690239be8ae99d43d7")

# Guardar
try:
    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='1. Resumen Ejecutivo TCO', index=False)
    print(f"\n✅ Excel actualizado exitosamente")
except Exception as e:
    print(f"\n⚠️  Error actualizando Excel con escritor mode='a': {e}")
    print("Intentando con método alternativo...")
    df.to_excel(excel_file, sheet_name='1. Resumen Ejecutivo TCO', index=False)
    print(f"✅ Excel actualizado exitosamente (alternativa)")

print("\n" + "=" * 80)
print("RESUMEN FINAL - APIM → API GATEWAY")
print("=" * 80)
print(f"Instancias: 11 APIM")
print(f"Llamadas: 80 millones mensuales")
print(f"Costos AWS:")
print(f"  • On-Demand:  ${total_monthly_ondemand:>8,.2f}/mes  (${annual_ondemand:>12,.2f}/año)")
print(f"  • SP 1yr:     ${cost_sp1yr_monthly:>8,.2f}/mes  (${annual_sp1yr:>12,.2f}/año)")
print(f"  • SP 3yr:     ${cost_sp3yr_monthly:>8,.2f}/mes  (${annual_sp3yr:>12,.2f}/año) ← RECOMENDADO")
print("=" * 80)
