#!/usr/bin/env python3
"""
Análisis y clasificación de VMs Unknown: Identificar ambiente correcto
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# Cargar datos
VM_MAPPING = Path("vm-azure-aws-mapping.json")
INVENTORY_FILE = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")

def get_resource_group(vm_name):
    """Intenta obtener el grupo de recursos del inventario"""
    df_vms = pd.read_excel(INVENTORY_FILE, sheet_name='Virtual Machines')
    
    rg_map = {}
    for idx, row in df_vms.iterrows():
        vm_name_inv = row['VM Name']
        rg = row['Resource Group']
        rg_map[vm_name_inv] = rg
    
    return rg_map.get(vm_name, 'Unknown')


def classify_unknown_vms():
    """Clasifica las VMs Unknown basándose en múltiples criterios"""
    print("="*120)
    print("CLASIFICACIÓN DE VMs UNKNOWN - Identificar Ambiente Correcto")
    print("="*120 + "\n")
    
    # Cargar VMs
    with open(VM_MAPPING, 'r', encoding='utf-8') as f:
        vms = json.load(f)
    
    # Leer inventario para obtener grupos de recursos
    df_vms = pd.read_excel(INVENTORY_FILE, sheet_name='Virtual Machines')
    
    # Crear mapa de VM Name -> Resource Group
    rg_map = {}
    for idx, row in df_vms.iterrows():
        vm_name_inv = row['VM Name']
        rg = row['Resource Group']
        rg_map[vm_name_inv] = rg
    
    # Filtrar Unknown
    unknown_vms = [vm for vm in vms if vm['name'].lower() not in 'prod,dev,qa,central,hub']
    
    print(f"📌 VMs a clasificar: {len(unknown_vms)}\n")
    
    # Criterios de clasificación
    prod_keywords = ['prod', 'prd', 'production', 'pr-', 'p-', 'live', 'customer']
    dev_keywords = ['dev', 'development', 'dev-', 'd-', 'staging', 'stage', 'test', 'testing']
    qa_keywords = ['qa', 'qat', 'test', 'validation', 'qa-', 'q-']
    central_keywords = ['central', 'hub', 'infra', 'shared', 'management']
    
    # Clasificación mejorada
    def improved_classify(vm_name, rg):
        """Clasifica con múltiples criterios"""
        vm_lower = vm_name.lower()
        rg_lower = str(rg).lower() if rg else ''
        combined = f"{vm_lower} {rg_lower}"
        
        # Verificar cada palabra clave
        for keyword in prod_keywords:
            if keyword in combined:
                return 'Prod', keyword
        
        for keyword in dev_keywords:
            if keyword in combined:
                return 'Dev', keyword
        
        for keyword in qa_keywords:
            if keyword in combined:
                return 'QA', keyword
        
        for keyword in central_keywords:
            if keyword in combined:
                return 'CentralHub', keyword
        
        # Intentar clasificar por UUID (si es UUID, probablemente sea VBA o temporal)
        import re
        if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}', vm_name.lower()):
            return 'Dev', 'UUID pattern (likely VBA/temporary)'
        
        return 'Unclassified', 'no pattern'
    
    classifications = []
    
    print(f"{'Nombre':<45} {'RG':<40} {'Clasificación':<15} {'Criterio':<30}")
    print("-" * 130)
    
    for vm in unknown_vms:
        rg = rg_map.get(vm['name'], 'Unknown')
        env, criterion = improved_classify(vm['name'], rg)
        
        classifications.append({
            'name': vm['name'],
            'azure_size': vm['azure_size'],
            'vcpu': vm['vcpu'],
            'memory_gb': vm['memory_gb'],
            'aws_equivalent': vm['aws_equivalent'],
            'resource_group': rg,
            'classified_as': env,
            'criterion': criterion,
        })
        
        rg_display = str(rg)[:40]
        print(f"{vm['name'][:45]:<45} {rg_display:<40} {env:<15} {criterion:<30}")
    
    # Resumen de clasificación
    print("\n\n📊 RESUMEN DE CLASIFICACIÓN\n")
    
    classification_summary = defaultdict(list)
    for c in classifications:
        classification_summary[c['classified_as']].append(c)
    
    for env in sorted(classification_summary.keys()):
        vms_in_env = classification_summary[env]
        total_vcpu = sum(vm['vcpu'] or 0 for vm in vms_in_env)
        total_ram = sum(vm['memory_gb'] or 0 for vm in vms_in_env)
        
        aws_prices = {
            't3.large': 30.00, 't3.xlarge': 60.00, 't3.2xlarge': 120.00,
            'c6i.large': 50.00, 'c6i.2xlarge': 200.00,
            'm6i.4xlarge': 600.00, 'm6i.8xlarge': 1200.00,
        }
        
        cost = sum(aws_prices.get(vm['aws_equivalent'], 75.00) for vm in vms_in_env)
        
        print(f"{env}:")
        print(f"  Máquinas: {len(vms_in_env)}")
        print(f"  vCPUs: {total_vcpu}")
        print(f"  RAM: {total_ram} GB")
        print(f"  Costo/mes: ${cost:,.2f}")
        print()
    
    # Detalle de máquinas más caras por nueva clasificación
    print("\n" + "="*120)
    print("🖥️  VMs MÁS CARAS POR NUEVA CLASIFICACIÓN\n")
    
    aws_prices = {
        't3.small': 7.50, 't3.medium': 15.00, 't3.large': 30.00,
        't3.xlarge': 60.00, 't3.2xlarge': 120.00,
        'c6i.large': 50.00, 'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00,
        'm6i.large': 75.00, 'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00,
        'm6i.4xlarge': 600.00, 'm6i.8xlarge': 1200.00,
    }
    
    for env in sorted(classification_summary.keys()):
        vms_in_env = classification_summary[env]
        
        # Ordenar por costo
        vms_sorted = sorted(vms_in_env, 
                           key=lambda x: aws_prices.get(x['aws_equivalent'], 75.00), 
                           reverse=True)
        
        if vms_sorted:
            print(f"\n{env}:")
            print(f"{'Nombre':<40} {'Azure Size':<20} {'AWS':<15} {'$/mes':<10}")
            print("-" * 85)
            
            for vm in vms_sorted[:5]:
                price = aws_prices.get(vm['aws_equivalent'], 75.00)
                print(f"{vm['name'][:40]:<40} {vm['azure_size'][:20]:<20} "
                      f"{vm['aws_equivalent'][:15]:<15} ${price:<9.2f}")
    
    # Exportar clasificación
    output_file = Path("vm-unknown-classified.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'classifications': classifications,
            'summary': {
                env: {
                    'count': len(vms_in_env),
                    'total_vcpu': sum(vm['vcpu'] or 0 for vm in vms_in_env),
                    'total_ram': sum(vm['memory_gb'] or 0 for vm in vms_in_env),
                }
                for env, vms_in_env in classification_summary.items()
            }
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Clasificación guardada en: {output_file}")
    
    # Sugerencias
    print("\n\n" + "="*120)
    print("💡 SUGERENCIAS PARA CLASIFICACIÓN MANUAL\n")
    
    unclassified = classification_summary.get('Unclassified', [])
    if unclassified:
        print("Máquinas que requieren clasificación manual:")
        for vm in unclassified:
            print(f"  - {vm['name']} (RG: {vm['resource_group']})")
    
    print("\n" + "="*120)


if __name__ == "__main__":
    classify_unknown_vms()
