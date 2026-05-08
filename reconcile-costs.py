#!/usr/bin/env python3
"""
Recalcula costos esperados vs actuales y ajusta configuración
"""

# Costos esperados del TCO
expected = {
    'on_demand': 52923,
    'sp1yr': 44984,
    'sp3yr': 36369
}

# Infraestructura compartida (constante en todos)
infrastructure = {
    'eks_control_plane': 730,      # 10 clusters x $73/mes
    'nat_gateways': 97.50,         # 3 x $32.50
    'alb': 32.40,                  # 2 x $16.20
    'cloudwatch': 15.00,           # 50 métricas x $0.30
    'ebs_storage': 50               # 38TB a tarifa baja
}

total_infra = sum(infrastructure.values())
print(f"Infraestructura compartida: ${total_infra:,.2f}/mes")

# Costo EC2 esperado (restando infraestructura)
ec2_expected = {
    'on_demand': expected['on_demand'] - total_infra,
    'sp1yr': expected['sp1yr'] - total_infra,
    'sp3yr': expected['sp3yr'] - total_infra
}

print(f"\nCostos EC2 esperados (76 nodos):")
print(f"  On-Demand: ${ec2_expected['on_demand']:,.2f}/mes")
print(f"  SP 1yr: ${ec2_expected['sp1yr']:,.2f}/mes")
print(f"  SP 3yr: ${ec2_expected['sp3yr']:,.2f}/mes")

# Costo promedio por nodo
cost_per_node_od = ec2_expected['on_demand'] / 76
print(f"\nCosto promedio por nodo (On-Demand): ${cost_per_node_od:,.2f}/mes")

# Con descuentos
sp1yr_discount = (expected['on_demand'] - expected['sp1yr']) / expected['on_demand']
sp3yr_discount = (expected['on_demand'] - expected['sp3yr']) / expected['on_demand']

print(f"\nDescuentos detectados:")
print(f"  SP 1yr: {sp1yr_discount*100:.1f}%")
print(f"  SP 3yr: {sp3yr_discount*100:.1f}%")

# Precios reales en us-east-2 (LinkedIn, AWS docs)
print("\n" + "="*80)
print("PRECIOS REALES AWS US-EAST-2 (On-Demand)")
print("="*80)

prices = {
    'm6i.xlarge': 0.192,
    'c6i.8xlarge': 1.36,
    'c6i.4xlarge': 0.68,
    'm6i.16xlarge': 3.072,
    'r6i.12xlarge': 3.024,
    'c5.xlarge': 0.17,
    't3.large': 0.0832
}

# Distribución actual (76 nodos)
distribution = [
    ('m6i.xlarge', 33),
    ('c6i.8xlarge', 8),
    ('c6i.4xlarge', 3),
    ('m6i.16xlarge', 9),
    ('r6i.12xlarge', 6),
    ('c5.xlarge', 14),
    ('t3.large', 3)
]

hours_per_month = 730
total_ec2_od = 0

print("\nInstancia Type         | Qty | $/hr   | Monthly/Unit | Total Monthly")
print("-" * 75)

for inst_type, qty in distribution:
    price_hr = prices[inst_type]
    monthly_per_unit = price_hr * hours_per_month
    total_month = monthly_per_unit * qty
    total_ec2_od += total_month
    print(f"{inst_type:20} | {qty:3} | {price_hr:6.4f} | ${monthly_per_unit:10,.2f} | ${total_month:10,.2f}")

print("-" * 75)
print(f"{'TOTAL EC2 ON-DEMAND':47} | ${total_ec2_od:10,.2f}")
print(f"Infrastructure                              | ${total_infra:10,.2f}")
print(f"{'TOTAL':47} | ${total_ec2_od + total_infra:10,.2f}")

print("\n" + "="*80)
print("ANÁLISIS DE DIFERENCIA")
print("="*80)

actual_od = total_ec2_od + total_infra
expected_od = expected['on_demand']
diff_od = actual_od - expected_od

print(f"Costo Esperado (TCO):     ${expected_od:>10,.2f}/mes")
print(f"Costo Calculado:          ${actual_od:>10,.2f}/mes")
print(f"Diferencia:               ${diff_od:>10,.2f}/mes ({diff_od/expected_od*100:+.1f}%)")

if diff_od > 0:
    print(f"\n⚠️  COSTO MÁS ALTO de lo esperado")
    print(f"   Posibles causas:")
    print(f"   1. Precios de instancias más altos")
    print(f"   2. Menos nodos optimizados")
    print(f"   3. Sin aprovechar descuentos Savings Plans")
else:
    print(f"\n✓ COSTO MÁS BAJO de lo esperado")

# Aplicar descuentos SP
ec2_sp1yr = total_ec2_od * (1 - sp1yr_discount)
ec2_sp3yr = total_ec2_od * (1 - sp3yr_discount)

total_sp1yr = ec2_sp1yr + total_infra
total_sp3yr = ec2_sp3yr + total_infra

print("\n" + "="*80)
print("PROYECCIÓN CON DESCUENTOS")
print("="*80)
print(f"\nSavings Plan 1yr ({sp1yr_discount*100:.1f}% descuento):")
print(f"  EC2: ${ec2_sp1yr:>10,.2f}/mes")
print(f"  Infra: ${total_infra:>10,.2f}/mes")
print(f"  TOTAL: ${total_sp1yr:>10,.2f}/mes vs Esperado ${expected['sp1yr']:>10,.2f} → ${total_sp1yr - expected['sp1yr']:+.2f}")

print(f"\nSavings Plan 3yr ({sp3yr_discount*100:.1f}% descuento):")
print(f"  EC2: ${ec2_sp3yr:>10,.2f}/mes")
print(f"  Infra: ${total_infra:>10,.2f}/mes")
print(f"  TOTAL: ${total_sp3yr:>10,.2f}/mes vs Esperado ${expected['sp3yr']:>10,.2f} → ${total_sp3yr - expected['sp3yr']:+.2f}")

print("\n" + "="*80)
print("CONCLUSIÓN")
print("="*80)
if abs(actual_od - expected_od) < 2000:
    print("✓ Los costos están ALINEADOS (diferencia < 5%)")
elif abs(actual_od - expected_od) < 5000:
    print("⚠️  Diferencia MODERADA (5-10%) - Revisar configuración")
else:
    print("❌ Diferencia SIGNIFICATIVA (> 10%) - Ajustar estimado")
