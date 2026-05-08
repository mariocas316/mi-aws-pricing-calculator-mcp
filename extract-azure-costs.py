#!/usr/bin/env python3
"""
Extractor de costos reales de Azure desde CostManagement Excel files
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

COST_DIR = Path("archivostcoonnet/CostManagement")
VM_MAPPING = Path("vm-azure-aws-mapping.json")

def extract_vm_costs_from_azure():
    """Extrae costos reales de VMs de Azure desde archivos CostManagement"""
    print("💰 Extrayendo costos reales de VMs en Azure...\n")
    
    vm_costs = defaultdict(lambda: {'azure_cost': 0, 'environment': '', 'resource_type': ''})
    env_totals = defaultdict(float)
    
    cost_files = sorted(COST_DIR.glob("*.xlsx"))
    
    for cost_file in cost_files:
        if "logicapps" in cost_file.name.lower():
            continue
        
        # Extraer ambiente del nombre
        if "CentralHub" in cost_file.name:
            env = "CentralHub"
        elif "Dev" in cost_file.name:
            env = "Dev"
        elif "Prod" in cost_file.name:
            env = "Prod"
        elif "QA" in cost_file.name:
            env = "QA"
        else:
            env = "Unknown"
        
        print(f"📄 Leyendo: {cost_file.name}")
        
        df = pd.read_excel(cost_file)
        
        # Filtrar solo VMs
        vm_df = df[df['ResourceType'].str.contains('virtualmachine', na=False, case=False)]
        
        print(f"   VMs encontradas: {len(vm_df)}")
        total_vm_cost = vm_df['CostUSD'].sum()
        print(f"   Costo total de VMs: ${total_vm_cost:,.2f}")
        
        # Agrupar por VM
        for idx, row in vm_df.iterrows():
            resource_id = row['ResourceId']
            
            # Extraer nombre de VM del Resource ID
            if '/virtualmachines/' in resource_id.lower():
                vm_name = resource_id.split('/virtualmachines/')[-1].split('/')[0]
            else:
                vm_name = row.get('Meter', 'Unknown')
            
            cost = row['CostUSD']
            vm_costs[vm_name]['azure_cost'] += cost
            vm_costs[vm_name]['environment'] = env
            vm_costs[vm_name]['resource_type'] = row['ResourceType']
        
        env_totals[env] += total_vm_cost
        print()
    
    return dict(vm_costs), dict(env_totals)


def map_vm_costs_with_mapping():
    """Mapea costos de Azure con el mapeo de VMs a AWS"""
    print("="*120)
    print("MAPEO DE COSTOS: Azure VMs → AWS EC2")
    print("="*120 + "\n")
    
    # Cargar mapeo de VMs
    with open(VM_MAPPING, 'r', encoding='utf-8') as f:
        vms = json.load(f)
    
    # Extraer costos de Azure
    vm_costs, env_totals = extract_vm_costs_from_azure()
    
    # Precios AWS
    aws_prices = {
        't3.small': 7.50, 't3.medium': 15.00, 't3.large': 30.00,
        't3.xlarge': 60.00, 't3.2xlarge': 120.00,
        'c6i.large': 50.00, 'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00,
        'm6i.large': 75.00, 'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00,
        'm6i.4xlarge': 600.00, 'm6i.8xlarge': 1200.00,
        'r6i.large': 100.00, 'r6i.xlarge': 200.00, 'r6i.2xlarge': 400.00,
        'r6i.4xlarge': 800.00,
    }
    
    # Mapear costos
    mapped_vms = []
    total_azure_cost = 0
    total_aws_cost_monthly = 0
    
    for vm in vms:
        # Buscar costo en Azure
        azure_cost_total = vm_costs.get(vm['name'], {}).get('azure_cost', 0)
        total_azure_cost += azure_cost_total
        
        # Calcular costo AWS
        aws_price = aws_prices.get(vm['aws_equivalent'], 75.00)
        total_aws_cost_monthly += aws_price
        
        mapped_vms.append({
            'name': vm['name'],
            'azure_size': vm['azure_size'],
            'aws_equivalent': vm['aws_equivalent'],
            'vcpu': vm['vcpu'],
            'memory_gb': vm['memory_gb'],
            'azure_cost_total': azure_cost_total,
            'aws_cost_monthly': aws_price,
            'aws_cost_annual': aws_price * 12,
            'savings_potential': azure_cost_total - (aws_price * 12),  # Comparación anual
        })
    
    # Resumen por ambiente
    print("\n📊 RESUMEN POR AMBIENTE\n")
    print(f"{'Ambiente':<15} {'Azure Total':<18} {'AWS Monthly':<18} {'AWS Annual':<18} {'Diferencia':<18}")
    print("-" * 90)
    
    env_summary = defaultdict(lambda: {'azure': 0, 'aws_monthly': 0})
    
    for vm in mapped_vms:
        # Aquí asumimos ambiente basado en nombre para agrupar
        env = 'Prod' if 'prod' in vm['name'].lower() else \
              'Dev' if 'dev' in vm['name'].lower() else \
              'QA' if 'qa' in vm['name'].lower() else \
              'CentralHub'
        
        env_summary[env]['azure'] += vm['azure_cost_total']
        env_summary[env]['aws_monthly'] += vm['aws_cost_monthly']
    
    for env in sorted(env_summary.keys()):
        summary = env_summary[env]
        azure_annual = summary['azure']
        aws_annual = summary['aws_monthly'] * 12
        diff = azure_annual - aws_annual
        
        print(f"{env:<15} ${azure_annual:<17,.2f} ${summary['aws_monthly']:<17,.2f} ${aws_annual:<17,.2f} ${diff:<17,.2f}")
    
    print("-" * 90)
    azure_total_annual = total_azure_cost
    aws_total_annual = total_aws_cost_monthly * 12
    diff_total = azure_total_annual - aws_total_annual
    
    print(f"{'TOTAL':<15} ${azure_total_annual:<17,.2f} ${total_aws_cost_monthly:<17,.2f} ${aws_total_annual:<17,.2f} ${diff_total:<17,.2f}")
    
    print("\n\n📈 TOP 10 VMs CON MAYOR DIFERENCIA\n")
    
    # Ordenar por savings potencial
    sorted_vms = sorted(mapped_vms, key=lambda x: x['savings_potential'], reverse=True)
    
    print(f"{'Nombre':<35} {'Azure Costo':<15} {'AWS Annual':<15} {'Ahorro Potencial':<20}")
    print("-" * 85)
    
    for vm in sorted_vms[:10]:
        print(f"{vm['name'][:35]:<35} ${vm['azure_cost_total']:<14,.2f} ${vm['aws_cost_annual']:<14,.2f} ${vm['savings_potential']:<19,.2f}")
    
    # Exportar resultado
    output_file = Path("vm-costs-azure-aws-mapping.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_azure_annual': azure_total_annual,
            'total_aws_monthly': total_aws_cost_monthly,
            'total_aws_annual': aws_total_annual,
            'total_potential_savings': diff_total,
            'savings_percentage': (diff_total / azure_total_annual * 100) if azure_total_annual > 0 else 0,
            'vms': mapped_vms,
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Mapeo guardado en: {output_file}")
    
    return mapped_vms, azure_total_annual, aws_total_annual


if __name__ == "__main__":
    map_vm_costs_with_mapping()
