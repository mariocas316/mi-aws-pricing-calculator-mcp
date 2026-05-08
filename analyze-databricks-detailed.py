#!/usr/bin/env python3
"""
Script mejorado para análisis detallado de costos de Databricks
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

COSTMGMT_DIR = "archivostcoonnet/CostManagement"
OUTPUT_DIR = "databricks-analysis"

def analyze_databricks_detailed():
    """Análisis detallado de Databricks por ambiente, tipo de computación y costo"""
    
    print("=" * 100)
    print("ANÁLISIS DETALLADO DE DATABRICKS - AZURE")
    print("=" * 100)
    
    all_records = []
    env_stats = {}
    
    # Procesar cada archivo de Cost Management
    for filename in sorted(os.listdir(COSTMGMT_DIR)):
        if not filename.endswith('.xlsx'):
            continue
        
        filepath = os.path.join(COSTMGMT_DIR, filename)
        
        # Extraer nombre del ambiente
        parts = filename.replace('CostManagement_Onnet-', '').replace('_2026', '').split('_')[0]
        env_name = parts if parts else filename
        
        print(f"\n📊 Procesando: {filename}")
        
        try:
            xls = pd.ExcelFile(filepath)
            sheet_name = xls.sheet_names[0] if xls.sheet_names else None
            
            if not sheet_name:
                continue
            
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            # Búsqueda más exhaustiva de Databricks
            for col in df.columns:
                if col.lower() in ['servicename', 'resourcetype', 'meter', 'tags']:
                    mask = df[col].astype(str).str.contains('databricks', case=False, na=False)
                    if mask.any():
                        databricks_rows = df[mask].copy()
                        
                        # Extraer costo (buscar columna de costo)
                        cost_col = next((c for c in df.columns if 'cost' in c.lower() and 'usd' in c.lower()), None)
                        if cost_col is None:
                            cost_col = next((c for c in df.columns if 'cost' in c.lower()), None)
                        
                        if cost_col:
                            total_cost = databricks_rows[cost_col].sum()
                            count = len(databricks_rows)
                            
                            print(f"  ✓ {count} registros encontrados - Costo: ${total_cost:.2f}")
                            
                            # Agregar información del ambiente
                            databricks_rows['Environment_Folder'] = env_name
                            databricks_rows['Cost_Column'] = cost_col
                            
                            all_records.append(databricks_rows)
                            
                            if env_name not in env_stats:
                                env_stats[env_name] = {
                                    'total_cost': 0,
                                    'record_count': 0,
                                    'by_meter': {},
                                    'by_resource': {}
                                }
                            
                            env_stats[env_name]['total_cost'] += total_cost
                            env_stats[env_name]['record_count'] += count
                            
                            # Agrupar por tipo de medidor
                            if 'Meter' in databricks_rows.columns:
                                for idx, row in databricks_rows.iterrows():
                                    meter = row['Meter']
                                    meter_cost = row[cost_col] if cost_col else 0
                                    
                                    if meter not in env_stats[env_name]['by_meter']:
                                        env_stats[env_name]['by_meter'][meter] = 0
                                    env_stats[env_name]['by_meter'][meter] += meter_cost
                            
                            # Agrupar por recurso
                            if 'ResourceId' in databricks_rows.columns:
                                for idx, row in databricks_rows.iterrows():
                                    resource = row.get('ResourceGroupName', row.get('ResourceId', 'Unknown'))
                                    resource_cost = row[cost_col] if cost_col else 0
                                    
                                    if resource not in env_stats[env_name]['by_resource']:
                                        env_stats[env_name]['by_resource'][resource] = 0
                                    env_stats[env_name]['by_resource'][resource] += resource_cost
                        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    return all_records, env_stats

def generate_detailed_report(all_records, env_stats):
    """Genera reporte detallado"""
    
    print("\n" + "=" * 100)
    print("RESUMEN POR AMBIENTE")
    print("=" * 100)
    
    total_cost_all = 0
    total_records_all = 0
    
    for env, stats in sorted(env_stats.items()):
        print(f"\n🔵 AMBIENTE: {env.upper()}")
        print(f"   Costo Total: ${stats['total_cost']:,.2f}")
        print(f"   Total de Registros: {stats['record_count']}")
        
        total_cost_all += stats['total_cost']
        total_records_all += stats['record_count']
        
        # Desglose por tipo de métrica (Meter)
        if stats['by_meter']:
            print(f"\n   📈 Desglose por Tipo de Computación:")
            for meter, cost in sorted(stats['by_meter'].items(), key=lambda x: x[1], reverse=True):
                pct = (cost / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
                print(f"      • {meter}: ${cost:,.2f} ({pct:.1f}%)")
        
        # Desglose por recurso (Resource Group)
        if stats['by_resource']:
            print(f"\n   🏢 Desglose por Grupo de Recursos:")
            for resource, cost in sorted(stats['by_resource'].items(), key=lambda x: x[1], reverse=True):
                pct = (cost / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
                print(f"      • {resource}: ${cost:,.2f} ({pct:.1f}%)")
    
    print("\n" + "=" * 100)
    print(f"💰 COSTO TOTAL DE DATABRICKS: ${total_cost_all:,.2f}")
    print(f"📋 TOTAL DE REGISTROS: {total_records_all}")
    print("=" * 100)
    
    # Guardar datos consolidados
    if all_records:
        consolidated = pd.concat(all_records, ignore_index=True)
        csv_path = os.path.join(OUTPUT_DIR, "databricks-detallado-completo.csv")
        consolidated.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"\n✓ Archivo completo guardado: {csv_path}")
    
    # Guardar resumen JSON
    json_path = os.path.join(OUTPUT_DIR, "databricks-resumen-detallado.json")
    summary_json = {
        'fecha_extraccion': datetime.now().isoformat(),
        'costo_total': total_cost_all,
        'total_registros': total_records_all,
        'por_ambiente': {}
    }
    
    for env, stats in env_stats.items():
        summary_json['por_ambiente'][env] = {
            'costo_total': stats['total_cost'],
            'registros': stats['record_count'],
            'por_tipo': dict(sorted(stats['by_meter'].items(), key=lambda x: x[1], reverse=True)),
            'por_recurso': dict(sorted(stats['by_resource'].items(), key=lambda x: x[1], reverse=True))
        }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_json, f, indent=2, ensure_ascii=False, default=str)
    print(f"✓ Resumen JSON guardado: {json_path}")

def main():
    print("\n🔍 Iniciando análisis de Databricks...\n")
    
    all_records, env_stats = analyze_databricks_detailed()
    
    if env_stats:
        generate_detailed_report(all_records, env_stats)
        print("\n✅ Análisis completado")
    else:
        print("\n⚠️  No se encontraron registros de Databricks")

if __name__ == "__main__":
    main()
