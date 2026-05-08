#!/usr/bin/env python3
"""
Script para extraer y analizar costos de Databricks desde archivos de Azure Cost Management
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

# Rutas de archivos de Cost Management
COSTMGMT_DIR = "archivostcoonnet/CostManagement"
OUTPUT_DIR = "databricks-analysis"

# Crear directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_databricks_data():
    """Extrae datos de Databricks de todos los archivos de Cost Management"""
    
    all_databricks = []
    summary_by_env = {}
    
    print("=" * 80)
    print("EXTRACCIÓN DE COSTOS DE DATABRICKS - AZURE")
    print("=" * 80)
    
    # Procesar cada archivo de Cost Management
    for filename in sorted(os.listdir(COSTMGMT_DIR)):
        if not filename.endswith('.xlsx'):
            continue
            
        filepath = os.path.join(COSTMGMT_DIR, filename)
        print(f"\n📄 Procesando: {filename}")
        
        try:
            # Intentar leer con diferentes nombres de hojas
            xls = pd.ExcelFile(filepath)
            print(f"   Hojas disponibles: {xls.sheet_names}")
            
            # Buscar la hoja principal de costos (usualmente "ActualCost" o similar)
            sheet_name = None
            for name in xls.sheet_names:
                if 'cost' in name.lower() or 'actual' in name.lower():
                    sheet_name = name
                    break
            
            if sheet_name is None and len(xls.sheet_names) > 0:
                sheet_name = xls.sheet_names[0]
            
            if sheet_name is None:
                print(f"   ⚠️  No se encontraron hojas válidas")
                continue
            
            print(f"   Usando hoja: {sheet_name}")
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            # Mostrar columnas disponibles
            print(f"   Columnas: {list(df.columns)[:5]}...")
            
            # Buscar filas de Databricks (buscar en columnas de ServiceName, ResourceType, etc.)
            databricks_rows = []
            
            # Búsqueda flexible en todos los datos
            for col in df.columns:
                if col.lower() in ['servicename', 'meter', 'resourcetype', 'resource', 'category', 'subcategory']:
                    mask = df[col].astype(str).str.contains('databricks', case=False, na=False)
                    if mask.any():
                        databricks_rows.append(df[mask].copy())
                        print(f"   ✓ Encontrados {mask.sum()} registros de Databricks en columna '{col}'")
            
            if databricks_rows:
                env_name = filename.split('_')[1].split('-')[0] if '_' in filename else 'Unknown'
                env_databricks = pd.concat(databricks_rows, ignore_index=True)
                
                # Agregar identificador de ambiente
                env_databricks['Environment'] = env_name
                all_databricks.append(env_databricks)
                
                # Resumen por ambiente
                try:
                    cost_col = next((c for c in df.columns if 'cost' in c.lower() and 'usd' in c.lower()), None)
                    if cost_col and cost_col in env_databricks.columns:
                        total_cost = env_databricks[cost_col].sum()
                        summary_by_env[env_name] = {
                            'total_cost': total_cost,
                            'record_count': len(env_databricks),
                            'unique_resources': env_databricks.iloc[:, 0].nunique() if len(env_databricks) > 0 else 0
                        }
                except:
                    pass
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    if not all_databricks:
        print("\n⚠️  No se encontraron registros de Databricks en los archivos")
        return None, None
    
    # Consolidar todos los datos
    consolidated = pd.concat(all_databricks, ignore_index=True)
    
    return consolidated, summary_by_env

def generate_report(databricks_df, summary):
    """Genera reporte de costos de Databricks"""
    
    print("\n" + "=" * 80)
    print("RESUMEN DE DATABRICKS POR AMBIENTE")
    print("=" * 80)
    
    if summary:
        for env, data in summary.items():
            print(f"\n📊 Ambiente: {env}")
            print(f"   Costo Total: ${data['total_cost']:.2f}")
            print(f"   Registros: {data['record_count']}")
            print(f"   Recursos únicos: {data['unique_resources']}")
    
    # Guardar CSV con datos completos
    csv_path = os.path.join(OUTPUT_DIR, "databricks-costos-detallados.csv")
    databricks_df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"\n✓ Datos detallados guardados en: {csv_path}")
    
    # Guardar resumen JSON
    json_path = os.path.join(OUTPUT_DIR, "databricks-resumen.json")
    summary_data = {
        'fecha_extraccion': datetime.now().isoformat(),
        'resumen_por_ambiente': summary,
        'total_registros': len(databricks_df),
        'columnas_disponibles': list(databricks_df.columns)
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"✓ Resumen guardado en: {json_path}")
    
    # Mostrar primeras filas
    print("\n" + "=" * 80)
    print("PRIMEROS REGISTROS")
    print("=" * 80)
    print(databricks_df.head(10).to_string())
    
    return csv_path, json_path

def main():
    print("\n🔍 Extrayendo datos de Databricks...")
    
    databricks_df, summary = extract_databricks_data()
    
    if databricks_df is not None:
        generate_report(databricks_df, summary)
        print("\n✅ Extracción completada")
    else:
        print("\n❌ No se encontraron datos de Databricks")

if __name__ == "__main__":
    main()
