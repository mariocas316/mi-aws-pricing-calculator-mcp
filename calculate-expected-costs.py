#!/usr/bin/env python3
"""
Calcula los costos esperados de EC2 basado en precios reales de AWS us-east-2
"""

# Precios hora en US East 2 (Ohio) - Linux On-Demand (abril 2026)
# Fuente: https://aws.amazon.com/ec2/pricing/on-demand/
prices_per_hour = {
    'm6i.xlarge': 0.216,      # 4 vCPU, 16 GB
    'm6i.16xlarge': 3.456,    # 64 vCPU, 256 GB
    'r6i.12xlarge': 2.688,    # 48 vCPU, 384 GB
    'c6i.8xlarge': 1.36,      # 32 vCPU, 64 GB
    'c6i.4xlarge': 0.68,      # 16 vCPU, 32 GB
    'c5.xlarge': 0.17,        # 4 vCPU, 8 GB
    't3.large': 0.0928,       # 2 vCPU, 8 GB
}

# Distribución de nodos de los estimados
nodes = [
    ('m6i.xlarge', 3),      # dev-aks-be-002
    ('r6i.12xlarge', 2),    # dev-aks-db-001
    ('c6i.8xlarge', 6),     # qa-aks-be-001
    ('m6i.16xlarge', 5),    # qa-aks-be-002
    ('m6i.xlarge', 4),      # qa-aks-db-001
    ('m6i.xlarge', 2),      # qa-aks-ap-001
    ('c6i.8xlarge', 8),     # prod-aks-be-001
    ('c6i.4xlarge', 3),     # prod-aks-be-002
    ('m6i.16xlarge', 6),    # prod-aks-be-003
    ('r6i.12xlarge', 4),    # prod-aks-db-001
    ('r6i.12xlarge', 2),    # prod-aks-db-002
    ('c5.xlarge', 14),      # prod-aks-ap-001
    ('t3.large', 3),        # prod-aks-ap-002
]

# Calcular totales
total_nodes = sum(qty for _, qty in nodes)
print("=" * 80)
print("ANÁLISIS DE COSTOS EC2 - CONFIGURACIÓN ESTIMADOS")
print("=" * 80)
print(f"\nTotal de nodos: {total_nodes}")
print("\nDistribución:")
for instance_type, qty in nodes:
    price = prices_per_hour[instance_type]
    print(f"  {instance_type:20} x {qty:2} = {qty:3} nodos @ ${price:7.4f}/hr")

# Calcular costos
hours_per_month = 730  # Promedio: 365 días / 12 meses * 24 horas
print(f"\nCálculo (base: {hours_per_month} horas/mes):")
print("-" * 80)

total_monthly_ondemand = 0
instance_costs = []

for instance_type, qty in nodes:
    price_per_hour = prices_per_hour[instance_type]
    monthly_cost = qty * price_per_hour * hours_per_month
    total_monthly_ondemand += monthly_cost
    instance_costs.append({
        'type': instance_type,
        'qty': qty,
        'hourly': price_per_hour,
        'monthly': monthly_cost
    })
    print(f"{instance_type:20} x {qty:2} nodos: ${monthly_cost:>12,.2f}/mes")

# Agregar costos de infraestructura
eks_cost = 730 * 0.10 * 10  # 10 clusters a $0.10/hora
nat_gateway_cost = 32.50 * 3  # $32.50/mes por NAT Gateway x 3
alb_cost = 16.20 * 2  # $16.20/mes por ALB x 2
cloudwatch_cost = 0.30 * 50  # $0.30 por métrica personalizada x 50

print(f"\nInfraestructura adicional:")
print(f"  EKS (10 clusters @ $0.10/hr): ${eks_cost:>12,.2f}/mes")
print(f"  NAT Gateways (3 @ $32.50/mes): ${nat_gateway_cost:>12,.2f}/mes")
print(f"  ALB (2 @ $16.20/mes): ${alb_cost:>12,.2f}/mes")
print(f"  CloudWatch (50 métricas): ${cloudwatch_cost:>12,.2f}/mes")

infraestructura_total = eks_cost + nat_gateway_cost + alb_cost + cloudwatch_cost
ec2_storage_cost = 500 * 76 / 1024 / 1024 * 0.10 * 730  # 38TB EBS gp3

print(f"  EBS (500GB x 76 nodos = 38TB @ $0.10/GB): ${ec2_storage_cost:>12,.2f}/mes")

# TOTALES
total_ondemand = total_monthly_ondemand + infraestructura_total + ec2_storage_cost

print("\n" + "=" * 80)
print("RESUMEN - ON-DEMAND:")
print("=" * 80)
print(f"EC2 Instances:           ${total_monthly_ondemand:>12,.2f}/mes")
print(f"Infrastructure:          ${infraestructura_total:>12,.2f}/mes")
print(f"Storage (EBS):           ${ec2_storage_cost:>12,.2f}/mes")
print(f"{'TOTAL ON-DEMAND':30}: ${total_ondemand:>12,.2f}/mes")
print(f"{'TOTAL ANUAL':30}: ${total_ondemand * 12:>12,.2f}/año")

# Aplicar descuentos Savings Plans
sp1yr_discount = 0.15  # 15% discount
sp3yr_discount = 0.33  # 33% discount

total_sp1yr = total_ondemand * (1 - sp1yr_discount)
total_sp3yr = total_ondemand * (1 - sp3yr_discount)

print("\n" + "=" * 80)
print("SAVINGS PLANS (solo EC2, no aplica a EKS/NAT/ALB):")
print("=" * 80)
ec2_sp1yr = total_monthly_ondemand * (1 - sp1yr_discount)
ec2_sp3yr = total_monthly_ondemand * (1 - sp3yr_discount)

print(f"\nSavings Plan 1yr (15% descuento en EC2):")
print(f"  EC2: ${ec2_sp1yr:>12,.2f}/mes")
print(f"  Otros: ${infraestructura_total + ec2_storage_cost:>12,.2f}/mes")
print(f"  TOTAL: ${ec2_sp1yr + infraestructura_total + ec2_storage_cost:>12,.2f}/mes")
print(f"  TOTAL ANUAL: ${(ec2_sp1yr + infraestructura_total + ec2_storage_cost) * 12:>12,.2f}/año")

print(f"\nSavings Plan 3yr (33% descuento en EC2):")
print(f"  EC2: ${ec2_sp3yr:>12,.2f}/mes")
print(f"  Otros: ${infraestructura_total + ec2_storage_cost:>12,.2f}/mes")
print(f"  TOTAL: ${ec2_sp3yr + infraestructura_total + ec2_storage_cost:>12,.2f}/mes")
print(f"  TOTAL ANUAL: ${(ec2_sp3yr + infraestructura_total + ec2_storage_cost) * 12:>12,.2f}/año")

print("\n" + "=" * 80)
print("VALORES ESPERADOS DEL TCO:")
print("=" * 80)
print("On-Demand:  $52,923/mes | $635,076/año")
print("SP 1yr:     $44,984/mes | $539,808/año")
print("SP 3yr:     $36,369/mes | $436,428/año")

print("\n" + "=" * 80)
print("COMPARACIÓN:")
print("=" * 80)
actual_ondemand = total_ondemand
expected_ondemand = 52923
print(f"On-Demand:   Actual ${actual_ondemand:,.2f} vs Esperado ${expected_ondemand:,.2f} → Diferencia: ${actual_ondemand - expected_ondemand:+,.2f}")

actual_sp1yr = ec2_sp1yr + infraestructura_total + ec2_storage_cost
expected_sp1yr = 44984
print(f"SP 1yr:      Actual ${actual_sp1yr:,.2f} vs Esperado ${expected_sp1yr:,.2f} → Diferencia: ${actual_sp1yr - expected_sp1yr:+,.2f}")

actual_sp3yr = ec2_sp3yr + infraestructura_total + ec2_storage_cost
expected_sp3yr = 36369
print(f"SP 3yr:      Actual ${actual_sp3yr:,.2f} vs Esperado ${expected_sp3yr:,.2f} → Diferencia: ${actual_sp3yr - expected_sp3yr:+,.2f}")
print("=" * 80)
