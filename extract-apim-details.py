#!/usr/bin/env python3
"""
Lee los detalles completos de APIM de la hoja APIM
"""
import pandas as pd
from pathlib import Path

inventory_file = Path('inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx')

# Leer la hoja APIM
df_apim = pd.read_excel(inventory_file, sheet_name='APIM', dtype=str)

print("=" * 100)
print("INSTANCIAS DE API MANAGEMENT (APIM) - INVENTARIO ARI")
print("=" * 100)

# Mostrar todas las columnas disponibles
print(f"\nColumnas disponibles: {list(df_apim.columns)}\n")

# Mostrar todas las filas
print(f"Total de instancias: {len(df_apim)}\n")

for idx, row in df_apim.iterrows():
    print(f"\n{'='*80}")
    print(f"Instancia #{idx + 1}")
    print(f"{'='*80}")
    for col in df_apim.columns:
        val = row[col]
        if pd.notna(val):
            print(f"  {col}: {val}")

print("\n" + "=" * 100)
print("RESUMEN POR AMBIENTE")
print("=" * 100)

# Crear resumen
dev_instances = []
qa_instances = []
prod_instances = []
dr_instances = []

for idx, row in df_apim.iterrows():
    name = str(row['Name']).lower() if 'Name' in df_apim.columns else ""
    
    if 'dev' in name:
        dev_instances.append(row['Name'])
    elif 'qa' in name:
        qa_instances.append(row['Name'])
    elif 'dr' in name:
        dr_instances.append(row['Name'])
    elif 'prod' in name:
        prod_instances.append(row['Name'])

print(f"\n🔵 DESARROLLO (DEV): {len(dev_instances)} instancias")
for inst in dev_instances:
    print(f"   • {inst}")

print(f"\n🟠 QA: {len(qa_instances)} instancias")
for inst in qa_instances:
    print(f"   • {inst}")

print(f"\n🔴 PRODUCCIÓN (PROD): {len(prod_instances)} instancias")
for inst in prod_instances:
    print(f"   • {inst}")

print(f"\n🟣 DISASTER RECOVERY (DR): {len(dr_instances)} instancias")
for inst in dr_instances:
    print(f"   • {inst}")

print(f"\n📊 TOTAL: {len(dev_instances) + len(qa_instances) + len(prod_instances) + len(dr_instances)} instancias")
print("\n" + "=" * 100)
