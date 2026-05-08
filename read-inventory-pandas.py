#!/usr/bin/env python3
"""
Lee Excel con mejor manejo de errores
Busca recursos de tipo APIM (API Management)
"""
import sys
from pathlib import Path

# Intentar con pandas (más robusto)
try:
    import pandas as pd
    
    inventory_file = Path('inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx')
    
    print("=" * 80)
    print("LEYENDO INVENTARIO CON PANDAS")
    print("=" * 80)
    
    # Leer todas las hojas
    xl_file = pd.ExcelFile(inventory_file)
    
    print(f"\nHojas encontradas: {xl_file.sheet_names}\n")
    
    # Buscar APIM en cada hoja
    for sheet_name in xl_file.sheet_names:
        print(f"📋 Hoja: {sheet_name}")
        df = pd.read_excel(inventory_file, sheet_name=sheet_name, dtype=str)
        
        # Buscar en todas las columnas por APIM/apiManagement
        for idx, row in df.iterrows():
            for col in df.columns:
                if row[col] and 'apim' in str(row[col]).lower():
                    print(f"   Fila {idx}: {col} = {row[col]}")
                elif row[col] and 'api management' in str(row[col]).lower():
                    print(f"   Fila {idx}: {col} = {row[col]}")
                    # Mostrar toda la fila
                    print(f"     Datos completos: {dict(row[:10])}")
    
    print("\n" + "=" * 80)
    print("BÚSQUEDA COMPLETADA")
    print("=" * 80)
    
except ImportError:
    print("❌ pandas no está instalado")
    print("Usando método alternativo con Excel COM...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Intenta especificar los datos manualmente")
