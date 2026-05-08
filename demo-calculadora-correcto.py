#!/usr/bin/env python3
"""
Reporte Automático - CORREGIDO
Precios de Azure son MENSUALES
"""

import json

# Cargar datos
with open('vm-costs-azure-aws-mapping.json', 'r') as f:
    data = json.load(f)

vms = data.get('vms', [])

# CORRECCIÓN: Azure costs son mensuales
total_azure_monthly = data.get('total_azure_annual', 0)
total_azure_annual = total_azure_monthly * 12
total_aws_annual = data.get('total_aws_annual', 0)

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
print('🧮 CALCULADORA AWS - MIGRACIÓN DESDE AZURE (CORREGIDA)')
print('='*100)
print()

# Resumen general
print('📊 RESUMEN GENERAL')
print('─'*100)
print()

total_vms = len(vms)

for env_name, env_vms in envs.items():
    if not env_vms:
        continue
    
    env_azure_monthly = sum(vm.get('azure_cost_total', 0) for vm in env_vms)
    env_azure_annual = env_azure_monthly * 12
    env_aws = sum(vm.get('aws_cost_annual', 0) for vm in env_vms)
    env_savings = env_azure_annual - env_aws
    env_savings_pct = (env_savings / env_azure_annual * 100) if env_azure_annual > 0 else 0
    
    status = '✅' if env_savings > 0 else '❌'
    print(f'{status} {env_name:15} | VMs: {len(env_vms):3} | Azure: ${env_azure_annual:>11,.0f}/año | AWS: ${env_aws:>11,.0f}/año | {"Ahorro" if env_savings > 0 else "Extra"}: ${abs(env_savings):>11,.0f} ({abs(env_savings_pct):>6.1f}%)')

print()
print('─'*100)

total_savings = total_azure_annual - total_aws_annual
total_savings_pct = (total_savings / total_azure_annual * 100)
status = '✅' if total_savings > 0 else '❌'

print(f'{status} TOTALES           | VMs: {total_vms:3} | Azure: ${total_azure_annual:>11,.0f}/año | AWS: ${total_aws_annual:>11,.0f}/año | {"Ahorro" if total_savings > 0 else "Extra"}: ${abs(total_savings):>11,.0f} ({abs(total_savings_pct):>6.1f}%)')
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
    
    env_azure_monthly = sum(vm.get('azure_cost_total', 0) for vm in env_vms)
    env_azure_annual = env_azure_monthly * 12
    env_aws = sum(vm.get('aws_cost_annual', 0) for vm in env_vms)
    env_savings = env_azure_annual - env_aws
    
    print(f'   Costo Azure:    ${env_azure_annual:>12,.0f}/año (${env_azure_monthly:>10,.0f}/mes)')
    print(f'   Costo AWS:      ${env_aws:>12,.0f}/año (${env_aws/12:>10,.0f}/mes)')
    
    if env_azure_annual > 0:
        savings_pct = (env_savings / env_azure_annual * 100)
        if env_savings > 0:
            print(f'   Ahorro:         ${env_savings:>12,.0f}/año ({savings_pct:>6.1f}%)')
            print(f'   Status:         ✅ AWS es más barato')
        else:
            print(f'   Costo Extra:    ${abs(env_savings):>12,.0f}/año ({abs(savings_pct):>6.1f}%)')
            print(f'   Status:         ❌ Azure es más barato')
    
    # Top 3
    top_vms = sorted(env_vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:3]
    print(f'\n   Top 3 VMs más costosas:')
    for i, vm in enumerate(top_vms, 1):
        name = vm.get('name', 'Unknown')[:45]
        azure_monthly = vm.get('azure_cost_total', 0)
        azure_annual = azure_monthly * 12
        aws_instance = vm.get('aws_equivalent', '')
        print(f'      {i}. {name:45} | Azure: ${azure_annual:>8,.0f} → {aws_instance}')

print()
print()

# Escenarios de pricing
print('='*100)
print('📈 ESCENARIOS DE PRICING')
print('='*100)
print()

strategies = [
    ('Azure Actual', total_azure_annual),
    ('AWS OnDemand', total_aws_annual),
    ('AWS 1yr Savings (30%)', total_aws_annual * 0.70),
    ('AWS 3yr Savings (50%)', total_aws_annual * 0.50),
    ('AWS Spot (70% off)', total_aws_annual * 0.30),
]

print(f'{"Escenario":<30} | {"Anual":>15} | {"Mensual":>15} | {"vs Azure":>15} | {"Status":>10}')
print('─'*100)

for scenario, annual_cost in strategies:
    monthly = annual_cost / 12
    vs_azure = total_azure_annual - annual_cost
    
    if scenario == 'Azure Actual':
        status = 'Base'
    elif vs_azure > 0:
        status = f'✅ {vs_azure/1000:.0f}k'
    else:
        status = f'❌ {abs(vs_azure)/1000:.0f}k'
    
    print(f'{scenario:<30} | ${annual_cost:>13,.0f} | ${monthly:>13,.0f} | ${vs_azure:>13,.0f} | {status:>10}')

print()
print()

# Top 10 VMs
print('='*100)
print('🎯 TOP 10 VMs MÁS COSTOSAS EN AZURE')
print('='*100)
print()

sorted_vms = sorted(vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:10]

print(f'{"#":<3} | {"Nombre":<35} | {"Azure/mes":>11} | {"Azure/año":>11} | {"AWS/año":>11} | {"Diferencia":>11}')
print('─'*100)

for i, vm in enumerate(sorted_vms, 1):
    name = vm.get('name', 'Unknown')[:35]
    azure_monthly = vm.get('azure_cost_total', 0)
    azure_annual = azure_monthly * 12
    aws_annual = vm.get('aws_cost_annual', 0)
    diff = azure_annual - aws_annual
    
    status = '✅' if diff > 0 else '❌'
    print(f'{i:<3} | {name:<35} | ${azure_monthly:>9,.0f} | ${azure_annual:>9,.0f} | ${aws_annual:>9,.0f} | {status} ${diff:>9,.0f}')

print()
print('='*100)
print()

# CONCLUSIÓN
print('🎯 CONCLUSIÓN')
print('='*100)
print()

if total_savings > 0:
    savings_pct = (total_savings / total_azure_annual * 100)
    print(f'✅ AWS OnDemand es la MEJOR OPCIÓN')
    print(f'   Ahorra: ${total_savings:,.0f}/año ({savings_pct:.1f}% más barato)')
else:
    savings_pct = (abs(total_savings) / total_aws_annual * 100)
    print(f'❌ Azure es más barato')
    print(f'   Ahorra: ${abs(total_savings):,.0f}/año ({savings_pct:.1f}%)')

print()

# Con 3yr Reserved
aws_3yr = total_aws_annual * 0.50
savings_3yr = total_azure_annual - aws_3yr
savings_3yr_pct = (savings_3yr / total_azure_annual * 100)

print(f'✅ AWS con 3yr Reserved es SIGNIFICATIVAMENTE mejor')
print(f'   Ahorra: ${savings_3yr:,.0f}/año ({savings_3yr_pct:.1f}% más barato)')

print()
print('='*100)
print()
