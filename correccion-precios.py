#!/usr/bin/env python3
"""
CORRECCIÓN CRÍTICA: Azure prices are MONTHLY, not annual
Recalculating all comparisons...
"""

import json

# Cargar datos
with open('vm-costs-azure-aws-mapping.json', 'r') as f:
    data = json.load(f)

print('\n' + '='*100)
print('🔄 RECÁLCULO CON DATOS CORRECTOS: Azure en MENSUAL')
print('='*100)
print()

vms = data['vms']

# CORRECCIÓN: Azure costs son mensuales, multiplicar por 12
total_azure_monthly = data.get('total_azure_annual', 0)  # Esto es en realidad MENSUAL
total_azure_annual = total_azure_monthly * 12

total_aws_annual = data.get('total_aws_annual', 0)

print('CORRECCIÓN DE DATOS:')
print()
print(f'Azure (Lo que había):          ${total_azure_monthly:>12,.2f}        ← MENSUAL (no anual)')
print(f'Azure (Correcto - anual):      ${total_azure_annual:>12,.2f}/año')
print()
print(f'AWS (OnDemand - anual):        ${total_aws_annual:>12,.2f}/año')
print()

# Comparación correcta
print('COMPARACIÓN CORRECTA:')
print('─'*100)
print()

difference = total_azure_annual - total_aws_annual
if difference > 0:
    print(f'❌ Azure es MÁS CARO:')
    print(f'   Diferencia: ${difference:,.2f}/año ({(difference/total_aws_annual*100):.1f}% más caro)')
else:
    print(f'✅ AWS es MÁS CARO:')
    print(f'   Diferencia: ${abs(difference):,.2f}/año ({(abs(difference)/total_azure_annual*100):.1f}% más caro)')

print()
print()

# Análisis por ambiente (recalculado)
print('ANÁLISIS POR AMBIENTE - CORRECTO:')
print('─'*100)
print()

# Extraer ambientes
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

print(f'{"Ambiente":<15} | {"VMs":>3} | {"Azure/mes":>12} | {"Azure/año":>12} | {"AWS/año":>12} | {"Diferencia":>12} | {"Status":>8}')
print('─'*100)

total_azure_corrected = 0
total_aws_corrected = 0

for env_name in sorted(envs.keys()):
    env_vms = envs[env_name]
    if not env_vms:
        continue
    
    env_azure_monthly = sum(vm.get('azure_cost_total', 0) for vm in env_vms)
    env_azure_annual = env_azure_monthly * 12
    env_aws = sum(vm.get('aws_cost_annual', 0) for vm in env_vms)
    
    total_azure_corrected += env_azure_annual
    total_aws_corrected += env_aws
    
    diff = env_azure_annual - env_aws
    status = '✅ AWS' if diff > 0 else '❌ Azure'
    
    print(f'{env_name:<15} | {len(env_vms):>3} | ${env_azure_monthly:>10,.2f} | ${env_azure_annual:>10,.2f} | ${env_aws:>10,.2f} | ${diff:>10,.2f} | {status:>8}')

print()
print('─'*100)
print()

# Escenarios de pricing (CORRECTO)
print('ESCENARIOS DE PRICING - CORRECTO:')
print('─'*100)
print()

strategies = [
    ('Azure Actual', total_azure_annual),
    ('AWS OnDemand', total_aws_annual),
    ('AWS 1yr Savings (30%)', total_aws_annual * 0.70),
    ('AWS 3yr Savings (50%)', total_aws_annual * 0.50),
    ('AWS Spot (70% off)', total_aws_annual * 0.30),
]

print(f'{"Escenario":<30} | {"Costo Anual":>15} | {"Costo Mensual":>15} | {"vs Azure":>15}')
print('─'*100)

for scenario, annual_cost in strategies:
    monthly = annual_cost / 12
    vs_azure = annual_cost - total_azure_annual
    status = '✅' if vs_azure < 0 else '❌'
    
    print(f'{scenario:<30} | ${annual_cost:>13,.2f} | ${monthly:>13,.2f} | {status} ${vs_azure:>13,.2f}')

print()
print()

# Conclusión
print('='*100)
print('🎯 CONCLUSIÓN CORRECTA')
print('='*100)
print()

if total_aws_annual < total_azure_annual:
    savings = total_azure_annual - total_aws_annual
    pct = (savings / total_azure_annual * 100)
    print(f'✅ AWS OnDemand es MEJOR OPCIÓN:')
    print(f'   Ahorra ${savings:,.2f}/año ({pct:.1f}% más barato)')
else:
    extra = total_azure_annual - total_aws_annual
    pct = (extra / total_aws_annual * 100)
    print(f'❌ Azure es mejor:')
    print(f'   Ahorra ${extra:,.2f}/año ({pct:.1f}% más barato)')

print()
print('CON 3yr RESERVED INSTANCES:')
print()
aws_3yr = total_aws_annual * 0.50
savings_3yr = total_azure_annual - aws_3yr
pct_3yr = (savings_3yr / total_azure_annual * 100)

if savings_3yr > 0:
    print(f'✅ AWS es SIGNIFICATIVAMENTE más barato:')
    print(f'   Ahorra ${savings_3yr:,.2f}/año ({pct_3yr:.1f}% de descuento)')
else:
    print(f'Azure sigue siendo mejor en ${abs(savings_3yr):,.2f}/año')

print()
print('='*100)
print()
