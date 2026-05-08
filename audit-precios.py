#!/usr/bin/env python3
"""
IMPORTANTE: Revisar y validar precios de AWS

Los datos actuales muestran que AWS es 8.7x más caro que Azure, lo que es poco realista.
Este script ayuda a identificar el problema.
"""

import json

# Cargar datos
with open('vm-costs-azure-aws-mapping.json', 'r') as f:
    data = json.load(f)

print('\n' + '='*100)
print('🔍 AUDITORÍA DE PRECIOS AWS')
print('='*100)
print()

vms = data['vms']

print('ANÁLISIS DE PRECIOS POR TIPO DE INSTANCIA:')
print()

# Agrupar por instancia AWS
instances = {}
for vm in vms:
    aws_inst = vm['aws_equivalent']
    if aws_inst not in instances:
        instances[aws_inst] = []
    instances[aws_inst].append(vm)

# Analizar cada tipo
print(f'{"Instancia":<20} | {"Qty":>3} | {"Precio/Mes":>12} | {"Mín/Máx Anual":>25} | {"Promedio Anual":>15}')
print('─'*100)

for inst_type in sorted(instances.keys()):
    vms_inst = instances[inst_type]
    
    annual_costs = [vm['aws_cost_annual'] for vm in vms_inst]
    
    min_cost = min(annual_costs)
    max_cost = max(annual_costs)
    avg_cost = sum(annual_costs) / len(annual_costs)
    monthly = avg_cost / 12
    
    print(f'{inst_type:<20} | {len(vms_inst):>3} | ${monthly:>10,.0f} | ${min_cost:>10,.0f} - ${max_cost:>10,.0f} | ${avg_cost:>13,.0f}')

print()
print('─'*100)
print()

# Precios típicos de AWS (referencia)
print('PRECIOS TÍPICOS AWS (us-east-2) - REFERENCIA:')
print()

typical_prices = {
    't3.small': 30/30,       # ~$30/mes = $1/día
    't3.medium': 40/30,
    't3.large': 60/30,       # ~$60/mes = $2/día
    't3.xlarge': 120/30,
    't3.2xlarge': 240/30,
    'c6i.large': 85/30,
    'c6i.2xlarge': 170/30,
    'm6i.4xlarge': 600/30,
    'm6i.8xlarge': 1200/30,
    'r6i.large': 100/30,
    'r6i.xlarge': 200/30,
}

print(f'{"Instancia":<20} | {"Precio/Mes":>12} | {"Precio/Año":>12}')
print('─'*100)

for inst, daily_price in sorted(typical_prices.items()):
    monthly = daily_price * 30
    annual = monthly * 12
    print(f'{inst:<20} | ${monthly:>10,.0f} | ${annual:>10,.0f}')

print()
print('─'*100)
print()

# Comparación
print('PROBLEMAS IDENTIFICADOS:')
print()

issues = []
for inst_type in sorted(instances.keys()):
    vms_inst = instances[inst_type]
    
    if inst_type not in typical_prices:
        # Estimar precio típico
        if 'large' in inst_type:
            typical = 85
        elif 'xlarge' in inst_type:
            typical = 120
        else:
            typical = 60
    else:
        typical = typical_prices[inst_type] * 30  # Convertir a mensual
    
    actual_monthly = vms_inst[0]['aws_cost_annual'] / 12
    
    if actual_monthly > typical * 1.5:  # 50% más caro
        ratio = actual_monthly / typical
        print(f'⚠️  {inst_type}: ${actual_monthly:.0f}/mes (${typical:.0f} típico) = {ratio:.1f}x más caro')
        issues.append((inst_type, ratio))

print()

if issues:
    print('RECOMENDACIÓN:')
    print('─'*100)
    print()
    print('Los precios de AWS en los datos son significativamente más altos que los precios')
    print('de mercado típicos. Esto podría deberse a:')
    print()
    print('1. ERROR DE CÁLCULO: Multiplicador incorrecto en mcp-server.js')
    print('2. PRECIOS DE WINDOWS: Si son instancias Windows (costo 20-30% más)')
    print('3. ALMACENAMIENTO: Si incluyen costos de EBS/networking')
    print('4. DATOS ANTICUADOS: Si los precios no son actuales')
    print()
    print('ACCIONES SUGERIDAS:')
    print('─'*100)
    print()
    print('1. Revisar mcp-server.js función loadAzureAwsMapping() y verify pricing')
    print('2. Usar calculadora oficial de AWS (https://calculator.aws/)')
    print('3. Aplicar descuentos realistas:')
    print('   - Producción: 3yr Reserved (50% off)')
    print('   - Dev/QA: Spot Instances (70% off)')
    print('   - Steady workloads: 1yr Savings Plan (30% off)')
    print()
    print('4. CORRECCIÓN RÁPIDA:')
    print('   Multiplicar todos los precios AWS por 0.3-0.4 para obtener precios realistas')
    print()

print('='*100)
print()
