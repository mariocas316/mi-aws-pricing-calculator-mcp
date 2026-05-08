#!/usr/bin/env python3
"""
Reconciliación de VMs Azure: Vincula datos de inventario con costos
y genera resumen de conciliación.
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import re

# Rutas
INVENTORY_FILE = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
COST_DIR = Path("archivostcoonnet/CostManagement")
VM_MAPPING_FILE = Path("vm-azure-aws-mapping.json")

def extract_environment_from_vm_name(vm_name):
    """Intenta extraer el ambiente del nombre de la VM"""
    vm_lower = vm_name.lower()
    
    if 'prod' in vm_lower:
        return 'Prod'
    elif 'dev' in vm_lower or 'development' in vm_lower:
        return 'Dev'
    elif 'qa' in vm_lower or 'test' in vm_lower:
        return 'QA'
    elif 'central' in vm_lower or 'hub' in vm_lower:
        return 'CentralHub'
    elif 'staging' in vm_lower or 'stage' in vm_lower:
        return 'QA'
    else:
        return 'Unknown'


def read_and_analyze_costs():
    """Lee todos los archivos de costos y analiza estructura"""
    print("💰 Analizando archivos de costos...\n")
    
    cost_summary = {}
    cost_files = list(COST_DIR.glob("*.xlsx"))
    
    for cost_file in cost_files:
        if "logicapps" in cost_file.name.lower():
            continue  # Saltar archivos no-VM
        
        env_name = cost_file.stem.replace("CostManagement_Onnet-", "").split("_2026")[0]
        print(f"📄 {cost_file.name}")
        
        try:
            df = pd.read_excel(cost_file)
            print(f"   Columnas: {list(df.columns)[:5]}...")
            print(f"   Registros: {len(df)}")
            
            # Buscar columnas relevantes
            cost_col = None
            resource_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'cost' in col_lower or 'charge' in col_lower or 'amount' in col_lower:
                    cost_col = col
                if 'resource' in col_lower or 'name' in col_lower or 'service' in col_lower:
                    resource_col = col
            
            if cost_col and resource_col:
                # Sumar costos por recurso
                total_cost = df[cost_col].sum() if cost_col in df.columns else 0
                print(f"   Costo total: ${total_cost:,.2f}")
                
                # Buscar costos de VMs
                vm_costs = df[df[resource_col].str.contains('vm|virtual', na=False, case=False)]
                print(f"   Registros de VM encontrados: {len(vm_costs)}")
                if len(vm_costs) > 0:
                    print(f"   Costo de VMs: ${vm_costs[cost_col].sum():,.2f}")
            
            cost_summary[env_name] = {
                'file': cost_file.name,
                'data': df,
                'columns': list(df.columns)
            }
            print()
        
        except Exception as e:
            print(f"   ⚠️  Error: {e}\n")
    
    return cost_summary


def load_vm_mapping():
    """Carga el mapeo de VMs generado anteriormente"""
    if VM_MAPPING_FILE.exists():
        with open(VM_MAPPING_FILE, 'r', encoding='utf-8') as f:
            vms = json.load(f)
        print(f"✅ Cargadas {len(vms)} VMs del mapeo")
        return vms
    else:
        print(f"❌ Archivo {VM_MAPPING_FILE} no encontrado")
        return []


def reconcile_vm_costs(vms, cost_data):
    """Reconcilia VMs con costos por ambiente"""
    print("\n" + "="*100)
    print("RECONCILIACIÓN DE VMs Y COSTOS")
    print("="*100 + "\n")
    
    reconciliation = []
    
    for vm in vms:
        env = extract_environment_from_vm_name(vm['name'])
        vm_info = {
            'name': vm['name'],
            'azure_size': vm['azure_size'],
            'vcpu': vm['vcpu'],
            'memory_gb': vm['memory_gb'],
            'estimated_env': env,
            'disk_gb': vm.get('total_disk_gb', 0),
            'aws_equivalent': vm['aws_equivalent'],
            'cost_found': False,
            'actual_cost': 0,
        }
        reconciliation.append(vm_info)
    
    # Resumen por ambiente
    print("📊 RESUMEN POR AMBIENTE\n")
    env_summary = defaultdict(lambda: {'vms': 0, 'total_vcpu': 0, 'total_ram': 0, 'cost': 0})
    
    for vm_info in reconciliation:
        env = vm_info['estimated_env']
        env_summary[env]['vms'] += 1
        env_summary[env]['total_vcpu'] += vm_info['vcpu'] or 0
        env_summary[env]['total_ram'] += vm_info['memory_gb'] or 0
    
    for env in sorted(env_summary.keys()):
        summary = env_summary[env]
        print(f"{env}:")
        print(f"   VMs: {summary['vms']}")
        print(f"   vCPUs totales: {summary['total_vcpu']}")
        print(f"   RAM total: {summary['total_ram']} GB")
        print()
    
    # Distribuir por familia Azure
    print("📦 DISTRIBUCIÓN POR FAMILIA AZURE\n")
    family_dist = defaultdict(list)
    for vm_info in reconciliation:
        family = vm_info['azure_size'].split('_')[1] if '_' in vm_info['azure_size'] else 'Unknown'
        family_dist[family].append(vm_info)
    
    for family in sorted(family_dist.keys())[:15]:
        vms_in_family = family_dist[family]
        total_vcpu = sum(vm['vcpu'] or 0 for vm in vms_in_family)
        total_ram = sum(vm['memory_gb'] or 0 for vm in vms_in_family)
        print(f"Standard_{family}: {len(vms_in_family)} VMs (vCPU: {total_vcpu}, RAM: {total_ram} GB)")
    
    # Salvar reconciliación
    output_file = Path("vm-reconciliation-report.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_vms': len(reconciliation),
            'environment_summary': {k: dict(v) for k, v in env_summary.items()},
            'vm_details': reconciliation
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Reconciliación guardada en: {output_file}")
    
    return reconciliation, env_summary


def generate_cost_estimation():
    """Genera estimación de costos basada en equivalentes AWS"""
    print("\n" + "="*100)
    print("ESTIMACIÓN DE COSTOS AWS BASADA EN EQUIVALENTES")
    print("="*100 + "\n")
    
    # Precios aproximados mensuales (OnDemand US East 2)
    aws_prices = {
        't3.small': 7.50,
        't3.medium': 15.00,
        't3.large': 30.00,
        't3.xlarge': 60.00,
        't3.2xlarge': 120.00,
        'c6i.large': 50.00,
        'c6i.xlarge': 100.00,
        'c6i.2xlarge': 200.00,
        'm6i.large': 75.00,
        'm6i.xlarge': 150.00,
        'm6i.2xlarge': 300.00,
        'm6i.4xlarge': 600.00,
        'm6i.8xlarge': 1200.00,
        'r6i.large': 100.00,
        'r6i.xlarge': 200.00,
        'r6i.2xlarge': 400.00,
        'r6i.4xlarge': 800.00,
    }
    
    vms = load_vm_mapping()
    
    print("💵 ESTIMACIÓN DE COSTOS MENSUALES (OnDemand)\n")
    
    total_cost = 0
    aws_dist = defaultdict(lambda: {'count': 0, 'cost': 0})
    
    for vm in vms:
        aws_equiv = vm['aws_equivalent']
        monthly_price = aws_prices.get(aws_equiv, 75.00)  # Default fallback
        total_cost += monthly_price
        aws_dist[aws_equiv]['count'] += 1
        aws_dist[aws_equiv]['cost'] += monthly_price
    
    print(f"{'Instancia AWS':<18} {'Cantidad':<10} {'$/mes c/u':<15} {'Total/mes':<15}")
    print("-" * 60)
    
    for instance in sorted(aws_dist.keys(), key=lambda x: aws_dist[x]['cost'], reverse=True):
        dist = aws_dist[instance]
        price_each = aws_prices.get(instance, 75.00)
        print(f"{instance:<18} {dist['count']:<10} ${price_each:<14.2f} ${dist['cost']:<14.2f}")
    
    print("-" * 60)
    print(f"{'TOTAL':<18} {sum(d['count'] for d in aws_dist.values()):<10} {'':<15} ${total_cost:<14.2f}")
    
    # Estimación anual
    annual_cost = total_cost * 12
    print(f"\nEstimación anual: ${annual_cost:,.2f}")
    print(f"Con descuento 1 año reservado (30%): ${annual_cost * 0.70:,.2f}")
    print(f"Con descuento 3 años reservado (50%): ${annual_cost * 0.50:,.2f}")
    
    return total_cost, aws_dist


def create_detailed_cost_report():
    """Crea un reporte detallado de costos por VM"""
    print("\n" + "="*100)
    print("REPORTE DETALLADO: VMs Y ESTIMACIÓN DE COSTOS")
    print("="*100 + "\n")
    
    aws_prices = {
        't3.small': 7.50, 't3.medium': 15.00, 't3.large': 30.00,
        't3.xlarge': 60.00, 't3.2xlarge': 120.00,
        'c6i.large': 50.00, 'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00,
        'm6i.large': 75.00, 'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00,
        'm6i.4xlarge': 600.00, 'm6i.8xlarge': 1200.00,
        'r6i.large': 100.00, 'r6i.xlarge': 200.00, 'r6i.2xlarge': 400.00,
        'r6i.4xlarge': 800.00,
    }
    
    vms = load_vm_mapping()
    
    print(f"{'Nombre VM':<30} {'Tamaño Azure':<20} {'AWS Equiv':<15} {'$/mes':<10} {'Amb.':<8}")
    print("-" * 85)
    
    total = 0
    for vm in vms[:50]:  # Top 50
        price = aws_prices.get(vm['aws_equivalent'], 75.00)
        env = extract_environment_from_vm_name(vm['name'])
        total += price
        vm_name = str(vm['name'])[:30]
        azure_size = str(vm['azure_size'])[:20]
        aws_equiv = vm['aws_equivalent'][:15]
        print(f"{vm_name:<30} {azure_size:<20} {aws_equiv:<15} ${price:<9.2f} {env:<8}")
    
    print(f"\n... y {len(vms) - 50} VMs más" if len(vms) > 50 else "")
    
    return total


def main():
    print("🚀 Iniciando reconciliación de costos\n")
    
    # 1. Analizar archivos de costos
    cost_data = read_and_analyze_costs()
    
    # 2. Cargar mapeo de VMs
    vms = load_vm_mapping()
    
    # 3. Reconciliar
    reconciliation, env_summary = reconcile_vm_costs(vms, cost_data)
    
    # 4. Estimación de costos AWS
    monthly_cost, aws_dist = generate_cost_estimation()
    
    # 5. Reporte detallado
    create_detailed_cost_report()
    
    print("\n✨ Reconciliación completada")


if __name__ == "__main__":
    main()
