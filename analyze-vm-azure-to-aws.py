#!/usr/bin/env python3
"""
Análisis de VMs en Azure: Extrae máquinas activas, identifica características,
busca homólogos en AWS y reconcilia costos.
"""

import openpyxl
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import re

# Rutas
INVENTORY_FILE = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
COST_DIR = Path("archivostcoonnet/CostManagement")

# Mapeo de familias de VMs Azure a AWS (basado en características similares)
AZURE_TO_AWS_FAMILY_MAP = {
    'Standard_B': 'burstable (t3/t4)',           # B-series -> t3/t4
    'Standard_D': 'general-purpose (m6i/m7i)',  # D-series -> m6i/m7i
    'Standard_E': 'memory-optimized (r6i/r7i)', # E-series -> r6i/r7i
    'Standard_F': 'compute-optimized (c6i/c7i)',# F-series -> c6i/c7i
    'Standard_G': 'memory-optimized (r6i/r7i)', # G-series -> r6i/r7i
    'Standard_L': 'storage-optimized (i3)',      # L-series -> i3
    'Standard_M': 'memory-optimized (x2)',       # M-series -> x2
    'Standard_N': 'gpu (g4/g5)',                 # N-series -> GPU instances
}

# Mapeo de vCPU Azure a instancias AWS típicas
VCPU_TO_AWS_INSTANCE = {
    1: 't3.small',      # 1 vCPU
    2: 't3.medium',     # 2 vCPU
    4: 't3.large',      # 2 vCPU - pero buscamos 4
    4: 'm6i.large',     # 2 vCPU
    8: 'm6i.xlarge',    # 4 vCPU
    16: 'm6i.2xlarge',  # 8 vCPU
    32: 'm6i.4xlarge',  # 16 vCPU
    64: 'm6i.8xlarge',  # 32 vCPU
}

def read_azure_inventory():
    """Lee el archivo de inventario de Azure y extrae información de VMs"""
    print("📂 Leyendo inventario de Azure...")
    
    # Leer todas las hojas del Excel
    xls = pd.ExcelFile(INVENTORY_FILE)
    print(f"   Total hojas: {len(xls.sheet_names)}")
    
    # Buscar hoja de VMs/máquinas virtuales
    vm_sheet = "Virtual Machines"
    if vm_sheet not in xls.sheet_names:
        # Buscar alternativa
        for sheet in xls.sheet_names:
            if 'vm' in sheet.lower() or 'virtual' in sheet.lower() or 'máquina' in sheet.lower():
                vm_sheet = sheet
                break
    
    print(f"   Usando hoja: {vm_sheet}")
    df = pd.read_excel(INVENTORY_FILE, sheet_name=vm_sheet)
    
    print(f"   Columnas encontradas: {len(df.columns)}")
    print(f"   Total de registros: {len(df)}")
    
    return df, xls.sheet_names


def extract_active_vms(df):
    """Extrae VMs activas y sus características"""
    print("\n🔍 Extrayendo VMs activas...")
    
    # Columnas esperadas en Virtual Machines
    resource_col = "VM Name"
    vm_size_col = "VM Size"
    status_col = "Power State"
    vcpu_col = "vCPUs"
    memory_col = "RAM (GiB)"
    os_disk_col = "OS Disk Size (GB)"
    data_disk_col = "Data Disk Size (GB)"
    
    # Filtrar VMs activas (PowerState = VM running)
    if status_col in df.columns:
        active_vms = df[df[status_col].str.lower().str.contains('running|allocated', na=False, regex=True)]
        print(f"   VMs activas encontradas: {len(active_vms)}")
        print(f"   Estados encontrados: {df[status_col].unique()[:5]}")
    else:
        active_vms = df
        print(f"   No se encontró columna de estado, usando todos: {len(active_vms)}")
    
    # Mostrar ejemplos
    print("\n   Primeras 5 VMs activas:")
    for idx, row in active_vms.head().iterrows():
        name = row[resource_col] if resource_col in row else "N/A"
        size = row[vm_size_col] if vm_size_col in row else "N/A"
        status = row[status_col] if status_col in row else "N/A"
        vcpu = row[vcpu_col] if vcpu_col in row else "N/A"
        memory = row[memory_col] if memory_col in row else "N/A"
        print(f"   - {name}: {size} ({vcpu} vCPU, {memory} GB RAM, {status})")
    
    return active_vms, resource_col, vm_size_col, status_col, vcpu_col, memory_col, os_disk_col, data_disk_col


def extract_vm_characteristics(vms_df, resource_col, vm_size_col, vcpu_col, memory_col, os_disk_col, data_disk_col):
    """Extrae características de VMs (vCPU, RAM, disco)"""
    print("\n📊 Extrayendo características de VMs...")
    
    vm_characteristics = []
    
    for idx, row in vms_df.iterrows():
        vm_name = row[resource_col] if resource_col in row else "Unknown"
        vm_size = row[vm_size_col] if vm_size_col in row else "Unknown"
        vcpu = row[vcpu_col] if vcpu_col in row and pd.notna(row[vcpu_col]) else None
        memory_gb = row[memory_col] if memory_col in row and pd.notna(row[memory_col]) else None
        os_disk = row[os_disk_col] if os_disk_col in row and pd.notna(row[os_disk_col]) else None
        data_disk = row[data_disk_col] if data_disk_col in row and pd.notna(row[data_disk_col]) else None
        
        # Convertir a números si es necesario
        try:
            vcpu = int(vcpu) if vcpu else None
        except:
            vcpu = None
        
        try:
            memory_gb = float(memory_gb) if memory_gb else None
        except:
            memory_gb = None
        
        try:
            os_disk = float(os_disk) if os_disk else None
        except:
            os_disk = None
        
        try:
            data_disk = float(data_disk) if data_disk else None
        except:
            data_disk = None
        
        vm_characteristics.append({
            'name': vm_name,
            'azure_size': vm_size,
            'vcpu': vcpu,
            'memory_gb': memory_gb,
            'os_disk_gb': os_disk,
            'data_disk_gb': data_disk,
            'total_disk_gb': (os_disk or 0) + (data_disk or 0),
            'aws_equivalent': find_aws_equivalent(vcpu, memory_gb),
        })
    
    return vm_characteristics


def parse_azure_vm_size(size_str):
    """Parsea el tamaño de VM de Azure para extraer vCPU y memoria"""
    # Ejemplos: Standard_D2s_v3, Standard_B2s, Standard_E4_v3
    
    vcpu_map = {
        'b1s': (1, 1), 'b1ms': (1, 2), 'b2s': (2, 4), 'b2ms': (2, 8),
        'b4ms': (4, 16), 'b8ms': (8, 32),
        'd1': (1, 3.5), 'd2': (2, 7), 'd3': (4, 14), 'd4': (8, 28),
        'd2s': (2, 7), 'd4s': (4, 14),
        'e2': (2, 16), 'e4': (4, 32), 'e8': (8, 64), 'e16': (16, 128),
        'e2s': (2, 16), 'e4s': (4, 32), 'e8s': (8, 64), 'e16s': (16, 128),
        'f1': (1, 2), 'f2': (2, 4), 'f4': (4, 8), 'f8': (8, 16),
    }
    
    size_lower = size_str.lower().replace('standard_', '')
    
    for key, (vcpu, mem) in vcpu_map.items():
        if size_lower.startswith(key):
            return vcpu, mem
    
    return None, None


def find_aws_equivalent(vcpu, memory_gb):
    """Encuentra el equivalente en AWS basado en vCPU y memoria"""
    if not vcpu:
        return "Unknown"
    
    # Instancias AWS comunes (vCPU, memoria)
    aws_instances = {
        't3.micro': (1, 1),
        't3.small': (1, 2),
        't3.medium': (1, 4),
        't3.large': (2, 8),
        't3.xlarge': (4, 16),
        't3.2xlarge': (8, 32),
        'm6i.large': (2, 8),
        'm6i.xlarge': (4, 16),
        'm6i.2xlarge': (8, 32),
        'm6i.4xlarge': (16, 64),
        'm6i.8xlarge': (32, 128),
        'c6i.large': (2, 4),
        'c6i.xlarge': (4, 8),
        'c6i.2xlarge': (8, 16),
        'r6i.large': (2, 16),
        'r6i.xlarge': (4, 32),
        'r6i.2xlarge': (8, 64),
        'r6i.4xlarge': (16, 128),
    }
    
    best_match = None
    min_diff = float('inf')
    
    for instance, (aws_vcpu, aws_mem) in aws_instances.items():
        # Buscar mejor match considerando vCPU y memoria
        if aws_vcpu >= vcpu:  # Preferir >= que <
            diff = (aws_vcpu - vcpu) + abs(aws_mem - (memory_gb or 0)) * 0.5
            if diff < min_diff:
                min_diff = diff
                best_match = instance
    
    return best_match or "t3.large"  # Default


def read_cost_files():
    """Lee todos los archivos de costos de CostManagement"""
    print("\n💰 Leyendo archivos de costos...")
    
    cost_data = {}
    cost_files = list(COST_DIR.glob("*.xlsx"))
    
    for cost_file in cost_files:
        env_name = cost_file.stem.replace("CostManagement_Onnet-", "").replace("_2026", "")
        print(f"   {cost_file.name}")
        
        try:
            df = pd.read_excel(cost_file)
            cost_data[env_name] = {
                'file': cost_file.name,
                'records': len(df),
                'columns': list(df.columns),
                'data': df
            }
        except Exception as e:
            print(f"   ⚠️  Error leyendo {cost_file.name}: {e}")
    
    return cost_data


def generate_report(active_vms, vm_chars, cost_data):
    """Genera un reporte completo"""
    print("\n" + "="*100)
    print("REPORTE DE ANÁLISIS: MÁQUINAS VIRTUALES AZURE vs AWS")
    print("="*100)
    
    print(f"\n📈 RESUMEN")
    print(f"   Total de VMs activas en Azure: {len(active_vms)}")
    print(f"   Características extraídas: {len(vm_chars)}")
    print(f"   Ambientes con costos: {list(cost_data.keys())}")
    
    print(f"\n🖥️  CARACTERÍSTICAS DE VMs (Top 30)")
    print(f"{'Nombre':<25} {'Azure Size':<18} {'vCPU':<6} {'RAM GB':<10} {'Disco GB':<12} {'AWS Equiv':<18}")
    print("-" * 100)
    
    for vm in vm_chars[:30]:
        disk_total = vm['total_disk_gb'] or 0
        print(f"{str(vm['name'])[:25]:<25} {str(vm['azure_size'])[:18]:<18} {str(vm['vcpu'] or '-'):<6} "
              f"{str(vm['memory_gb'] or '-'):<10} {str(disk_total):<12} {vm['aws_equivalent']:<18}")
    
    # Estadísticas
    print(f"\n📊 ESTADÍSTICAS")
    
    vcpu_dist = defaultdict(int)
    memory_dist = defaultdict(int)
    azure_size_dist = defaultdict(int)
    
    for vm in vm_chars:
        if vm['vcpu']:
            vcpu_dist[vm['vcpu']] += 1
        if vm['memory_gb']:
            # Agrupar memoria en rangos
            mem_range = int(vm['memory_gb'] / 8) * 8  # Redondear a 8
            memory_dist[mem_range] += 1
        if vm['azure_size'] != 'Unknown':
            azure_size_dist[vm['azure_size']] += 1
    
    print(f"\n   Distribución por vCPU:")
    for vcpu in sorted(vcpu_dist.keys()):
        print(f"      {vcpu} vCPU: {vcpu_dist[vcpu]} VMs")
    
    print(f"\n   Distribución por Familia Azure (Top 10):")
    for size, count in sorted(azure_size_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      {size}: {count} VMs")
    
    print(f"\n   Equivalentes AWS más comunes:")
    aws_equiv_dist = defaultdict(int)
    for vm in vm_chars:
        aws_equiv_dist[vm['aws_equivalent']] += 1
    for aws_type, count in sorted(aws_equiv_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      {aws_type}: {count} VMs")
    
    # Salvar JSON con detalles
    output_json = Path("vm-azure-aws-mapping.json")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(vm_chars, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ Detalles guardados en: {output_json}")
    
    return vm_chars


def main():
    print("🚀 Iniciando análisis de VMs Azure -> AWS\n")
    
    # 1. Leer inventario de Azure
    try:
        df, _ = read_azure_inventory()
        active_vms, resource_col, vm_size_col, status_col, vcpu_col, memory_col, os_disk_col, data_disk_col = extract_active_vms(df)
    except Exception as e:
        print(f"❌ Error leyendo inventario: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Extraer características
    try:
        vm_chars = extract_vm_characteristics(active_vms, resource_col, vm_size_col, vcpu_col, memory_col, os_disk_col, data_disk_col)
    except Exception as e:
        print(f"❌ Error extrayendo características: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Leer costos
    try:
        cost_data = read_cost_files()
    except Exception as e:
        print(f"❌ Error leyendo costos: {e}")
        cost_data = {}
    
    # 4. Generar reporte
    generate_report(active_vms, vm_chars, cost_data)
    
    print("\n✨ Análisis completado")


if __name__ == "__main__":
    main()
