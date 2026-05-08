#!/usr/bin/env python3
"""
Optimizador de Costos AWS - Recomendaciones para mejorar ROI
"""

import json
from collections import defaultdict

# Cargar datos
with open('vm-costs-azure-aws-mapping.json', 'r') as f:
    data = json.load(f)

vms = data['vms']

print('\n' + '='*100)
print('💡 OPTIMIZADOR DE COSTOS AWS - RECOMENDACIONES')
print('='*100)
print()

# 1. Análisis de instancias overprovisioned
print('1️⃣  INSTANCIAS OVERPROVISIONED')
print('─'*100)
print()

overprovisioned = []
for vm in vms:
    if vm.get('vcpu', 0) >= 8 and vm.get('azure_cost_total', 0) < 500:
        overprovisioned.append(vm)

if overprovisioned:
    print(f'Encontradas {len(overprovisioned)} máquinas que podrían ser downsized:')
    print()
    print(f'{"Nombre":<40} | {"Actual":<15} | {"Propuesta":<15} | {"Ahorro":>12}')
    print('─'*100)
    
    for vm in overprovisioned[:10]:
        name = vm['name'][:40]
        current = vm['aws_equivalent']
        current_cost = vm['aws_cost_annual']
        
        # Sugerir tamaño más pequeño
        vcpu = vm.get('vcpu', 0)
        memory = vm.get('memory_gb', 0)
        
        if vcpu >= 16:
            proposed = 't3.xlarge'
            proposed_cost = 720
        elif vcpu >= 8:
            proposed = 't3.large'
            proposed_cost = 360
        else:
            proposed = 'c6i.large'
            proposed_cost = 600
        
        savings = current_cost - proposed_cost
        
        print(f'{name:<40} | {current:<15} | {proposed:<15} | ${savings:>10,.0f}')
    
    total_savings = sum(vm['aws_cost_annual'] - 360 for vm in overprovisioned if vm['aws_cost_annual'] > 360)
    print()
    print(f'Potencial de ahorro total: ${total_savings:,.0f}/año')
    print()

# 2. Análisis por ambiente - aplicar estrategias diferentes
print()
print('2️⃣  ESTRATEGIA DE PRICING POR AMBIENTE')
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

strategies = {
    'Prod': ('3yr Reserved', 0.50, '✅ Commitments garantizados'),
    'Dev': ('Spot + OnDemand Mix', 0.60, '🎯 Mezclar Spot (70% desc) con OnDemand'),
    'QA': ('Spot Instances', 0.30, '💰 Máximo ahorro posible'),
    'CentralHub': ('1yr Savings', 0.70, '⚖️  Balance entre costo y flexibilidad'),
}

print(f'{"Ambiente":<15} | {"VMs":>4} | {"OnDemand":>12} | {"Recomendado":>12} | {"Ahorro":>10} | {"Estrategia":<35}')
print('─'*100)

for env_name, env_vms in sorted(envs.items()):
    if not env_vms:
        continue
    
    ondemand = sum(vm['aws_cost_annual'] for vm in env_vms)
    
    if env_name in strategies:
        strategy_name, discount, description = strategies[env_name]
        optimized = ondemand * discount
        savings = ondemand - optimized
        
        print(f'{env_name:<15} | {len(env_vms):>4} | ${ondemand:>10,.0f} | ${optimized:>10,.0f} | ${savings:>8,.0f} | {description:<35}')
    else:
        print(f'{env_name:<15} | {len(env_vms):>4} | ${ondemand:>10,.0f} | {"-":>12} | {"-":>10} | Revisar manualmente')

print()
print()

# 3. Cálculo optimizado
print('3️⃣  CÁLCULO OPTIMIZADO CON ESTRATEGIAS')
print('─'*100)
print()

total_ondemand = 0
total_optimized = 0

for env_name, env_vms in envs.items():
    if not env_vms:
        continue
    
    ondemand = sum(vm['aws_cost_annual'] for vm in env_vms)
    total_ondemand += ondemand
    
    if env_name in strategies:
        strategy_name, discount, _ = strategies[env_name]
        optimized = ondemand * discount
        total_optimized += optimized

print(f'AWS OnDemand Total:        ${total_ondemand:>15,.2f}/año')
print(f'AWS Optimizado:            ${total_optimized:>15,.2f}/año')
print(f'Ahorro Total:              ${total_ondemand - total_optimized:>15,.2f}/año')
print()

# 4. Comparación vs Azure
print('4️⃣  COMPARACIÓN: AZURE vs AWS OPTIMIZADO')
print('─'*100)
print()

total_azure = sum(vm['azure_cost_total'] for vm in vms)
print(f'Azure Actual:              ${total_azure:>15,.2f}/año')
print(f'AWS Optimizado:            ${total_optimized:>15,.2f}/año')

if total_optimized < total_azure:
    diff = total_azure - total_optimized
    pct = (diff / total_azure * 100)
    print(f'Ahorro Potencial:          ${diff:>15,.2f}/año ({pct:.1f}%)')
    print()
    print('✅ AWS es más económico que Azure con optimizaciones')
else:
    diff = total_optimized - total_azure
    pct = (diff / total_azure * 100)
    print(f'Costo Adicional:           ${diff:>15,.2f}/año ({pct:.1f}%)')
    print()
    print('❌ Azure sigue siendo más económico incluso con optimizaciones')

print()
print()

# 5. Análisis de instancias pequeñas agrupables
print('5️⃣  CONSOLIDACIÓN - INSTANCIAS AGRUPABLES')
print('─'*100)
print()

small_vms = [vm for vm in vms if vm.get('aws_equivalent', '').startswith('t3.') and vm.get('vcpu', 0) <= 2]

print(f'Instancias t3.small/medium/large encontradas: {len(small_vms)}')
print(f'Costo actual: ${sum(vm["aws_cost_annual"] for vm in small_vms):,.0f}/año')
print()

# Agrupar por tamaño
consolidation = defaultdict(list)
for vm in small_vms:
    inst = vm['aws_equivalent']
    consolidation[inst].append(vm)

print(f'{"Tipo Instancia":<15} | {"Cantidad":>8} | {"Costo Total":>15} | {"Consolidación Sugerida":<40}')
print('─'*100)

for inst_type in sorted(consolidation.keys()):
    vms_inst = consolidation[inst_type]
    cost = sum(vm['aws_cost_annual'] for vm in vms_inst)
    
    # Sugerir consolidación
    if inst_type == 't3.large' and len(vms_inst) >= 3:
        suggest = f'Consolidar en t3.2xlarge (3 → 1 instancia)'
    elif inst_type == 't3.large' and len(vms_inst) >= 2:
        suggest = f'Considerar t3.xlarge para 2 apps'
    else:
        suggest = 'Revisar manualmente'
    
    print(f'{inst_type:<15} | {len(vms_inst):>8} | ${cost:>13,.0f} | {suggest:<40}')

print()
print()

# 6. Plan de migración recomendado
print('6️⃣  PLAN DE MIGRACIÓN RECOMENDADO')
print('─'*100)
print()

print('FASE 1: Análisis (2 semanas)')
print('  ☐ Revisar uso real de CPU/RAM en Azure con performance monitoring')
print('  ☐ Identificar instancias overprovisioned')
print('  ☐ Validar licencias (Windows, SQL Server) para pricing correcto')
print()

print('FASE 2: Piloto (1 mes)')
print('  ☐ Migrar ambiente DEV a AWS con Spot Instances')
print('  ☐ Testing y validación de performance')
print('  ☐ Estimar costos reales vs proyectado')
print()

print('FASE 3: Rollout (3 meses)')
print('  ☐ QA: Spot + pequeño % OnDemand para reliability')
print('  ☐ Prod: 3yr Reserved Instances para máximo ahorro')
print('  ☐ CentralHub: 1yr Savings Plan (balance flexible)')
print()

print('FASE 4: Optimización Continua')
print('  ☐ Implementar auto-scaling')
print('  ☐ Usar Lambda/Fargate para aplicaciones adecuadas')
print('  ☐ Revisar y ajustar tamaños mensualmente')
print()

print('='*100)
print()
print(f'Resumen: Potencial de ahorro estimado con optimizaciones: ${total_ondemand - total_optimized:,.0f}/año')
print('='*100)
print()
