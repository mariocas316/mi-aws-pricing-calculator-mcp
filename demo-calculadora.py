#!/usr/bin/env python3
"""
Demostración automática de la calculadora
"""

import json
from pathlib import Path

# Cargar datos
with open('vm-costs-azure-aws-mapping.json', 'r') as f:
    data = json.load(f)

vms = data.get('vms', [])

# Extraer por ambiente
envs = {'Prod': [], 'Dev': [], 'QA': [], 'CentralHub': [], 'Unknown': []}
for vm in vms:
    name = vm.get('name', '').lower()
    if 'prod' in name:
        envs['Prod'].append(vm)
    elif 'dev' in name:
        envs['Dev'].append(vm)
    elif 'qa' in name:
        envs['QA'].append(vm)
    elif 'central' in name or 'centralhub' in name:
        envs['CentralHub'].append(vm)
    else:
        envs['Unknown'].append(vm)

print('\n' + '='*100)
print('🧮 CALCULADORA AWS - MIGRACIÓN DESDE AZURE')
print('='*100)
print()

# Resumen general
print('📊 RESUMEN GENERAL')
print('─'*100)
print()

total_vms = len(vms)
total_azure = data.get('total_azure_annual', 0)
total_aws = data.get('total_aws_annual', 0)

for env_name, env_vms in envs.items():
    if not env_vms:
        continue
    
    env_azure = sum(vm.get('azure_cost_total', 0) for vm in env_vms)
    env_aws = sum(vm.get('aws_cost_annual', 0) for vm in env_vms)
    env_savings = env_azure - env_aws
    env_savings_pct = (env_savings / env_azure * 100) if env_azure > 0 else 0
    
    print(f'🏢 {env_name:15} | VMs: {len(env_vms):3} | Azure: ${env_azure:>11,.2f}/año | AWS: ${env_aws:>11,.2f}/año | Ahorro: ${env_savings:>11,.2f} ({env_savings_pct:>6.1f}%)')

print()
print('─'*100)
print(f'📈 TOTALES           | VMs: {total_vms:3} | Azure: ${total_azure:>11,.2f}/año | AWS: ${total_aws:>11,.2f}/año')
print('─'*100)

# Recursos
print()
print('💾 RECURSOS CONSUMIDOS:')
total_vcpu = sum(vm.get('vcpu', 0) for vm in vms)
total_ram = sum(vm.get('memory_gb', 0) for vm in vms)
print(f'   vCPUs totales: {total_vcpu}')
print(f'   RAM total:    {total_ram:,.0f} GB ({total_ram/1024:.1f} TB)')
print()

# Distribución de instancias
print('📦 DISTRIBUCIÓN DE INSTANCIAS AWS:')
instance_dist = {}
for vm in vms:
    instance = vm.get('aws_equivalent', 'Unknown')
    instance_dist[instance] = instance_dist.get(instance, 0) + 1

for instance in sorted(instance_dist.keys()):
    count = instance_dist[instance]
    pct = count / total_vms * 100
    print(f'   {instance:15} x {count:2} ({pct:>5.1f}%)')

print()
print()

# Análisis por ambiente detallado
print('='*100)
print('🌍 ANÁLISIS DETALLADO POR AMBIENTE')
print('='*100)

for env_name, env_vms in envs.items():
    if not env_vms:
        continue
    
    print(f'\n📍 {env_name.upper()}')
    print('─'*100)
    print(f'   Total VMs: {len(env_vms)}')
    
    env_azure = sum(vm.get('azure_cost_total', 0) for vm in env_vms)
    env_aws = sum(vm.get('aws_cost_annual', 0) for vm in env_vms)
    env_savings = env_azure - env_aws
    
    print(f'   Costo Azure:    ${env_azure:>12,.2f}/año (${env_azure/12:>10,.2f}/mes)')
    print(f'   Costo AWS:      ${env_aws:>12,.2f}/año (${env_aws/12:>10,.2f}/mes)')
    print(f'   Potencial:      ${env_savings:>12,.2f}/año')
    
    if env_azure > 0:
        savings_pct = (env_savings / env_azure * 100)
        print(f'   Ahorro (%):     {savings_pct:>12.1f}%')
    
    # Top 3
    top_vms = sorted(env_vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:3]
    print(f'\n   Top 3 VMs más costosas:')
    for i, vm in enumerate(top_vms, 1):
        name = vm.get('name', 'Unknown')[:45]
        azure_cost = vm.get('azure_cost_total', 0)
        aws_instance = vm.get('aws_equivalent', '')
        print(f'      {i}. {name:45} | Azure: ${azure_cost:>8,.0f} → {aws_instance}')

print()
print()

# Escenarios de pricing
print('='*100)
print('📈 ESCENARIOS DE PRICING')
print('='*100)
print()

strategies = [
    ('OnDemand', 1.0),
    ('1yr Savings Plan (30%)', 0.70),
    ('3yr Savings Plan (50%)', 0.50),
    ('Spot Instances (Best)', 0.30),
]

print(f'{"Estrategia":<30} | {"Costo Anual":>15} | {"Costo Mensual":>15} | {"vs Azure":>15} | {"Ahorro %":>8}')
print('─'*100)

for strategy, discount in strategies:
    cost = total_aws * discount
    monthly = cost / 12
    savings = total_azure - cost
    savings_pct = (savings / total_azure * 100) if total_azure > 0 else 0
    
    status = '✅' if savings > 0 else '❌'
    print(f'{status} {strategy:<28} | ${cost:>14,.2f} | ${monthly:>14,.2f} | ${savings:>14,.2f} | {savings_pct:>7.1f}%')

print()
print()

# Top 10 VMs
print('='*100)
print('🎯 TOP 10 VMs MÁS COSTOSAS EN AZURE')
print('='*100)
print()

sorted_vms = sorted(vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:10]

print(f'{"#":<3} | {"Nombre":<40} | {"Azure":<12} | {"AWS Equiv":<15} | {"Ahorro":<12}')
print('─'*100)

for i, vm in enumerate(sorted_vms, 1):
    name = vm.get('name', 'Unknown')[:40]
    azure_cost = vm.get('azure_cost_total', 0)
    aws_equivalent = vm.get('aws_equivalent', '')[:15]
    aws_cost = vm.get('aws_cost_annual', 0)
    savings = azure_cost - aws_cost
    
    print(f'{i:<3} | {name:<40} | ${azure_cost:>10,.0f} | {aws_equivalent:<15} | ${savings:>10,.0f}')

print()
print('='*100)
print()
