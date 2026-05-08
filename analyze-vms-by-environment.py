#!/usr/bin/env python3
"""
Análisis detallado de VMs por ambiente: Costos, cantidad y características
"""

import json
from pathlib import Path
from collections import defaultdict

# Cargar datos
VM_MAPPING = Path("vm-azure-aws-mapping.json")

def extract_environment(vm_name):
    """Extrae el ambiente del nombre de VM"""
    vm_lower = vm_name.lower()
    
    if 'prod' in vm_lower:
        return 'Prod'
    elif 'dev' in vm_lower or 'development' in vm_lower:
        return 'Dev'
    elif 'qa' in vm_lower or 'test' in vm_lower or 'stage' in vm_lower:
        return 'QA'
    elif 'central' in vm_lower or 'hub' in vm_lower:
        return 'CentralHub'
    else:
        return 'Unknown'


def analyze_vms_by_environment():
    """Analiza VMs discriminadas por ambiente"""
    print("="*120)
    print("ANÁLISIS DETALLADO: VMs POR AMBIENTE (Excluyendo AKS Workers)")
    print("="*120 + "\n")
    
    # Cargar mapeo de VMs
    with open(VM_MAPPING, 'r', encoding='utf-8') as f:
        vms = json.load(f)
    
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
    
    # Agrupar por ambiente
    env_vms = defaultdict(list)
    
    for vm in vms:
        env = extract_environment(vm['name'])
        env_vms[env].append(vm)
    
    # Resumen por ambiente
    print("📊 RESUMEN GENERAL POR AMBIENTE\n")
    
    env_summary = {}
    total_vms = 0
    total_cost_monthly = 0
    
    for env in sorted(env_vms.keys()):
        vms_list = env_vms[env]
        total_vms += len(vms_list)
        
        # Calcular totales
        env_vcpu = sum(vm['vcpu'] or 0 for vm in vms_list)
        env_ram = sum(vm['memory_gb'] or 0 for vm in vms_list)
        env_disk = sum(vm.get('total_disk_gb', 0) for vm in vms_list)
        env_cost = sum(aws_prices.get(vm['aws_equivalent'], 75.00) for vm in vms_list)
        
        total_cost_monthly += env_cost
        
        env_summary[env] = {
            'vms': len(vms_list),
            'vcpu': env_vcpu,
            'ram': env_ram,
            'disk': env_disk,
            'cost_monthly': env_cost,
            'cost_annual': env_cost * 12,
        }
        
        print(f"{env}:")
        print(f"  Máquinas:         {len(vms_list):>4}")
        print(f"  vCPUs totales:    {env_vcpu:>4}")
        print(f"  RAM total:        {env_ram:>7.1f} GB")
        print(f"  Almacenamiento:   {env_disk:>9.0f} GB")
        print(f"  Costo mensual:    ${env_cost:>10,.2f}")
        print(f"  Costo anual:      ${env_cost * 12:>10,.2f}")
        print()
    
    # Totales
    print("="*60)
    print(f"TOTAL:")
    print(f"  Máquinas:         {total_vms:>4}")
    total_vcpu = sum(s['vcpu'] for s in env_summary.values())
    total_ram = sum(s['ram'] for s in env_summary.values())
    total_disk = sum(s['disk'] for s in env_summary.values())
    print(f"  vCPUs totales:    {total_vcpu:>4}")
    print(f"  RAM total:        {total_ram:>7.1f} GB")
    print(f"  Almacenamiento:   {total_disk:>9.0f} GB")
    print(f"  Costo mensual:    ${total_cost_monthly:>10,.2f}")
    print(f"  Costo anual:      ${total_cost_monthly * 12:>10,.2f}")
    print("="*60)
    
    # Desglose por tipo de instancia por ambiente
    print("\n\n📦 DISTRIBUCIÓN POR TIPO DE INSTANCIA Y AMBIENTE\n")
    
    for env in sorted(env_vms.keys()):
        print(f"\n{env}:")
        print("-" * 100)
        
        vms_list = env_vms[env]
        instance_dist = defaultdict(list)
        
        for vm in vms_list:
            instance_dist[vm['aws_equivalent']].append(vm)
        
        print(f"{'Instancia AWS':<18} {'Cantidad':<10} {'vCPU':<8} {'RAM (GB)':<12} {'$/mes c/u':<15} {'Total/mes':<15}")
        print("-" * 100)
        
        for instance in sorted(instance_dist.keys(), key=lambda x: len(instance_dist[x]), reverse=True):
            vms_in_instance = instance_dist[instance]
            count = len(vms_in_instance)
            total_vcpu = sum(vm['vcpu'] or 0 for vm in vms_in_instance)
            total_ram = sum(vm['memory_gb'] or 0 for vm in vms_in_instance)
            price = aws_prices.get(instance, 75.00)
            total_price = price * count
            
            print(f"{instance:<18} {count:<10} {total_vcpu:<8} {total_ram:<12.1f} ${price:<14.2f} ${total_price:<14.2f}")
        
        print()
    
    # Detalle de VMs por ambiente (Top 15 por costo)
    print("\n" + "="*120)
    print("🖥️  MÁQUINAS VIRTUALES MÁS CARAS POR AMBIENTE\n")
    
    for env in sorted(env_vms.keys()):
        vms_list = env_vms[env]
        
        # Ordenar por costo
        vms_sorted = sorted(vms_list, 
                           key=lambda x: aws_prices.get(x['aws_equivalent'], 75.00), 
                           reverse=True)
        
        print(f"\n{env}: Top 10 máquinas más caras")
        print("-" * 120)
        print(f"{'Nombre':<35} {'Azure Size':<20} {'vCPU':<6} {'RAM GB':<8} {'AWS Equiv':<18} {'$/mes':<12}")
        print("-" * 120)
        
        for vm in vms_sorted[:10]:
            price = aws_prices.get(vm['aws_equivalent'], 75.00)
            vm_name = str(vm['name'])[:35]
            azure_size = str(vm['azure_size'])[:20]
            aws_equiv = vm['aws_equivalent'][:18]
            
            print(f"{vm_name:<35} {azure_size:<20} {vm['vcpu'] or '-':<6} "
                  f"{vm['memory_gb'] or '-':<8} {aws_equiv:<18} ${price:<11.2f}")
    
    # Comparativo de costos con reservaciones
    print("\n\n" + "="*120)
    print("💰 ESTIMACIÓN CON DIFERENTES OPCIONES DE PAGO\n")
    
    print(f"{'Ambiente':<20} {'OnDemand/mes':<18} {'OnDemand/año':<18} {'1 Año Reservado':<20} {'3 Años Reservado':<20}")
    print("-" * 96)
    
    for env in sorted(env_vms.keys()):
        cost_monthly = env_summary[env]['cost_monthly']
        cost_annual = cost_monthly * 12
        cost_1yr = cost_annual * 0.70
        cost_3yr = cost_annual * 0.50
        
        print(f"{env:<20} ${cost_monthly:<17,.2f} ${cost_annual:<17,.2f} ${cost_1yr:<19,.2f} ${cost_3yr:<19,.2f}")
    
    print("-" * 96)
    total_monthly = total_cost_monthly
    total_annual = total_monthly * 12
    total_1yr = total_annual * 0.70
    total_3yr = total_annual * 0.50
    
    print(f"{'TOTAL':<20} ${total_monthly:<17,.2f} ${total_annual:<17,.2f} ${total_1yr:<19,.2f} ${total_3yr:<19,.2f}")
    
    # Exportar datos a JSON
    output_file = Path("vm-analysis-by-environment.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': env_summary,
            'total': {
                'vms': total_vms,
                'vcpu': total_vcpu,
                'ram': total_ram,
                'disk_gb': total_disk,
                'monthly_cost': total_cost_monthly,
                'annual_cost': total_annual,
                'annual_1yr_reserved': total_1yr,
                'annual_3yr_reserved': total_3yr,
            },
            'vms_by_env': {
                env: [
                    {
                        'name': vm['name'],
                        'azure_size': vm['azure_size'],
                        'vcpu': vm['vcpu'],
                        'memory_gb': vm['memory_gb'],
                        'aws_equivalent': vm['aws_equivalent'],
                        'monthly_cost': aws_prices.get(vm['aws_equivalent'], 75.00),
                    }
                    for vm in env_vms[env]
                ]
                for env in env_summary.keys()
            }
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Análisis guardado en: {output_file}")


if __name__ == "__main__":
    analyze_vms_by_environment()
