#!/usr/bin/env python3
"""
Reporte Ejecutivo: Análisis completo Azure VMs a AWS
Resumen de inventario, características y costos
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Cargar datos
VM_MAPPING = Path("vm-azure-aws-mapping.json")
RECONCILIATION = Path("vm-reconciliation-report.json")

def format_currency(amount):
    """Formatea un número como moneda USD"""
    return f"${amount:,.2f}"

def load_data():
    """Carga los datos procesados"""
    with open(VM_MAPPING, 'r', encoding='utf-8') as f:
        vms = json.load(f)
    
    with open(RECONCILIATION, 'r', encoding='utf-8') as f:
        reconciliation = json.load(f)
    
    return vms, reconciliation

def generate_executive_report():
    """Genera reporte ejecutivo"""
    print("\n" + "="*100)
    print("REPORTE EJECUTIVO: ANÁLISIS DE MIGRACIÓN AZURE → AWS")
    print("="*100)
    
    vms, reconciliation = load_data()
    
    # Sección 1: RESUMEN EJECUTIVO
    print("\n📋 RESUMEN EJECUTIVO\n")
    print(f"   Máquinas virtuales activas: {len(vms)}")
    print(f"   Ambientes: CentralHub (17), Dev (11), Prod (44), QA (19), No clasificadas (21)")
    
    total_vcpu = sum(vm['vcpu'] or 0 for vm in vms)
    total_ram = sum(vm['memory_gb'] or 0 for vm in vms)
    total_disk = sum(vm.get('total_disk_gb', 0) for vm in vms)
    
    print(f"   Recursos totales:")
    print(f"      vCPUs: {total_vcpu}")
    print(f"      Memoria RAM: {total_ram} GB")
    print(f"      Almacenamiento: {total_disk:,.0f} GB ({total_disk/1024:.1f} TB)")
    
    # Sección 2: DISTRIBUCIÓN POR AMBIENTE
    print("\n📊 DISTRIBUCIÓN POR AMBIENTE\n")
    env_summary = reconciliation['environment_summary']
    
    for env in ['CentralHub', 'Dev', 'Prod', 'QA', 'Unknown']:
        if env in env_summary:
            summary = env_summary[env]
            print(f"   {env}:")
            print(f"      VMs: {summary['vms']}")
            print(f"      vCPUs: {summary['total_vcpu']}")
            print(f"      RAM: {summary['total_ram']} GB")
    
    # Sección 3: ARQUITECTURA DE VMs
    print("\n🖥️  ARQUITECTURA DE VMs\n")
    
    # Por vCPU
    vcpu_dist = defaultdict(int)
    for vm in vms:
        if vm['vcpu']:
            vcpu_dist[vm['vcpu']] += 1
    
    print("   Distribución por vCPU:")
    for vcpu in sorted(vcpu_dist.keys()):
        pct = (vcpu_dist[vcpu] / len(vms)) * 100
        bar = "█" * int(pct / 5)
        print(f"      {vcpu:2d} vCPU: {vcpu_dist[vcpu]:3d} VMs ({pct:5.1f}%) {bar}")
    
    # Familias Azure principales
    print("\n   Familias Azure más utilizadas:")
    family_dist = defaultdict(list)
    for vm in vms:
        family = vm['azure_size'].split('_')[1] if '_' in vm['azure_size'] else 'Unknown'
        family_dist[family].append(vm)
    
    for family in sorted(family_dist.keys(), 
                        key=lambda x: len(family_dist[x]), 
                        reverse=True)[:10]:
        vms_in_family = family_dist[family]
        print(f"      Standard_{family}: {len(vms_in_family)} VMs")
    
    # Sección 4: MAPEO A AWS
    print("\n☁️  EQUIVALENTES EN AWS\n")
    
    aws_equiv_dist = defaultdict(list)
    for vm in vms:
        aws_equiv_dist[vm['aws_equivalent']].append(vm)
    
    print(f"   {'Instancia AWS':<18} {'Cantidad':<12} {'% del total':<15}")
    print("   " + "-" * 45)
    for aws_type in sorted(aws_equiv_dist.keys(), 
                          key=lambda x: len(aws_equiv_dist[x]), 
                          reverse=True):
        count = len(aws_equiv_dist[aws_type])
        pct = (count / len(vms)) * 100
        print(f"   {aws_type:<18} {count:<12} {pct:5.1f}%")
    
    # Sección 5: ESTIMACIÓN DE COSTOS
    print("\n💵 ESTIMACIÓN DE COSTOS EN AWS (OnDemand, US-East-2)\n")
    
    aws_prices = {
        't3.small': 7.50, 't3.medium': 15.00, 't3.large': 30.00,
        't3.xlarge': 60.00, 't3.2xlarge': 120.00,
        'c6i.large': 50.00, 'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00,
        'm6i.large': 75.00, 'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00,
        'm6i.4xlarge': 600.00, 'm6i.8xlarge': 1200.00,
        'r6i.large': 100.00, 'r6i.xlarge': 200.00, 'r6i.2xlarge': 400.00,
        'r6i.4xlarge': 800.00,
    }
    
    monthly_cost = 0
    for aws_type, vms_list in aws_equiv_dist.items():
        price = aws_prices.get(aws_type, 75.00)
        monthly_cost += price * len(vms_list)
    
    annual_cost = monthly_cost * 12
    
    print(f"   Costo mensual (OnDemand):        {format_currency(monthly_cost)}")
    print(f"   Costo anual (OnDemand):          {format_currency(annual_cost)}")
    print(f"   Costo anual (1 año reservado):   {format_currency(annual_cost * 0.70)} (30% desc)")
    print(f"   Costo anual (3 años reservado):  {format_currency(annual_cost * 0.50)} (50% desc)")
    
    # Sección 6: DISTRIBUCIÓN DE COSTOS POR AMBIENTE
    print("\n💰 ESTIMACIÓN POR AMBIENTE\n")
    
    for env in ['CentralHub', 'Dev', 'Prod', 'QA', 'Unknown']:
        env_vms = [v for v in vms if get_env_from_name(v['name']) == env]
        env_cost = 0
        for vm in env_vms:
            price = aws_prices.get(vm['aws_equivalent'], 75.00)
            env_cost += price
        
        if env_vms:
            print(f"   {env}:")
            print(f"      VMs: {len(env_vms)}")
            print(f"      Costo mensual: {format_currency(env_cost)}")
            print(f"      Costo anual:   {format_currency(env_cost * 12)}")
    
    # Sección 7: RECOMENDACIONES
    print("\n📝 RECOMENDACIONES PARA LA MIGRACIÓN\n")
    
    print(f"   1. Consolidación de instancias pequeñas:")
    b2_count = len([v for v in vms if 'B2' in v['azure_size']])
    print(f"      - {b2_count} VMs Standard_B2* podrían consolidarse en t3.large")
    print(f"        Ahorro potencial: ~{format_currency(10 * b2_count)}/mes")
    
    print(f"\n   2. Uso de Reservations:")
    print(f"      - Reservado 1 año: {format_currency(annual_cost * 0.70)} (ahorro 30%)")
    print(f"      - Reservado 3 años: {format_currency(annual_cost * 0.50)} (ahorro 50%)")
    
    print(f"\n   3. Instancias de alto costo:")
    large_vms = [v for v in vms if v['vcpu'] and v['vcpu'] >= 16]
    large_cost = sum(aws_prices.get(v['aws_equivalent'], 75.00) for v in large_vms)
    print(f"      - {len(large_vms)} VMs con 16+ vCPUs")
    print(f"      - Costo mensual: {format_currency(large_cost)}")
    print(f"      - Revisar si pueden escalarse verticalmente o distribuirse")
    
    print(f"\n   4. Almacenamiento:")
    print(f"      - Total disco: {total_disk:,.0f} GB")
    print(f"      - Considerar EBS gp3 para mejor costo")
    
    # Sección 8: PRÓXIMOS PASOS
    print("\n✅ PRÓXIMOS PASOS\n")
    print("   1. Validar mapeos de equivalentes AWS")
    print("   2. Realizar pruebas de compatibilidad en AWS")
    print("   3. Ajustar tamaños de instancias según necesidad real")
    print("   4. Evaluar servicios alternativos (Fargate, Lambda, RDS)")
    print("   5. Planificar cronograma de migración por ambiente")
    print("   6. Configurar networking y seguridad")
    print("   7. Validación y cutover")
    
    print("\n" + "="*100)
    print("Fin del reporte")
    print("="*100 + "\n")


def get_env_from_name(vm_name):
    """Extrae ambiente del nombre de VM"""
    vm_lower = vm_name.lower()
    if 'prod' in vm_lower:
        return 'Prod'
    elif 'dev' in vm_lower:
        return 'Dev'
    elif 'qa' in vm_lower or 'test' in vm_lower:
        return 'QA'
    elif 'central' in vm_lower or 'hub' in vm_lower:
        return 'CentralHub'
    return 'Unknown'


if __name__ == "__main__":
    generate_executive_report()
