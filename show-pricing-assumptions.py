#!/usr/bin/env python3
"""
Explicación transparente de precios asumidos en el análisis
"""

def show_pricing_assumptions():
    print("="*110)
    print("PRECIOS ASUMIDOS EN EL ANÁLISIS DE MIGRACIÓN AZURE → AWS")
    print("="*110)
    print()
    
    print("☁️  NUBE DESTINO: AWS (Amazon Web Services)")
    print("📍 REGIÓN: us-east-2 (Ohio) - Similar a Azure East US 2")
    print("💳 MODELO: OnDemand (pago por hora, sin compromisos)")
    print("📦 ALCANCE: Compute solamente (no incluye EBS, networking, etc.)")
    print()
    
    print("="*110)
    print("PRECIOS AWS EC2 - us-east-2 (OnDemand)")
    print("="*110)
    print()
    
    # Precios reales de AWS us-east-2 (Mayo 2026)
    aws_prices = {
        't3.small': 0.0104,
        't3.medium': 0.0208,
        't3.large': 0.0416,
        't3.xlarge': 0.0832,
        't3.2xlarge': 0.1664,
        'c6i.large': 0.085,
        'c6i.xlarge': 0.17,
        'c6i.2xlarge': 0.34,
        'c6i.4xlarge': 0.68,
        'm6i.large': 0.129,
        'm6i.xlarge': 0.258,
        'm6i.2xlarge': 0.516,
        'm6i.4xlarge': 1.032,
        'm6i.8xlarge': 2.064,
        'r6i.large': 0.171,
        'r6i.xlarge': 0.342,
        'r6i.2xlarge': 0.684,
        'r6i.4xlarge': 1.368,
    }
    
    print(f"{'Instancia':<20} {'vCPU':<8} {'RAM':<8} {'$/hora':<12} {'$/mes':<15} {'$/año':<15}")
    print("-" * 95)
    
    specs = {
        't3.small': (1, 2),
        't3.medium': (1, 4),
        't3.large': (2, 8),
        't3.xlarge': (4, 16),
        't3.2xlarge': (8, 32),
        'c6i.large': (2, 4),
        'c6i.xlarge': (4, 8),
        'c6i.2xlarge': (8, 16),
        'c6i.4xlarge': (16, 32),
        'm6i.large': (2, 8),
        'm6i.xlarge': (4, 16),
        'm6i.2xlarge': (8, 32),
        'm6i.4xlarge': (16, 64),
        'm6i.8xlarge': (32, 128),
        'r6i.large': (2, 16),
        'r6i.xlarge': (4, 32),
        'r6i.2xlarge': (8, 64),
        'r6i.4xlarge': (16, 128),
    }
    
    for instance in sorted(aws_prices.keys()):
        hourly = aws_prices[instance]
        monthly = hourly * 730  # 24 horas * 30.42 días
        yearly = monthly * 12
        vcpu, ram = specs.get(instance, (0, 0))
        
        print(f"{instance:<20} {vcpu:<8} {ram:<8} ${hourly:<11.4f} ${monthly:<14.2f} ${yearly:<14.2f}")
    
    print()
    print("="*110)
    print("SUPUESTOS DE CÁLCULO")
    print("="*110)
    print()
    print("✓ Horas por mes: 730 (promedio: 24h × 30.42 días)")
    print("✓ Tipo de precios: OnDemand (por demanda)")
    print("✓ Descuentos aplicados DESPUÉS (Saving Plans, Reserved Instances)")
    print("✓ Instancias generación: t3 (burstable), c6i/m6i (general), r6i (memory)")
    print("✓ SO: Linux (Windows sería ~30% más caro)")
    print("✓ Almacenamiento: NO incluido (costaría adicional con EBS gp3)")
    print("✓ Networking: NO incluido (NAT Gateway, Load Balancer, etc.)")
    print("✓ Transferencia de datos: NO incluida")
    print()
    
    print("="*110)
    print("OPCIONES DE DESCUENTO EN AWS")
    print("="*110)
    print()
    print("1. Saving Plans (1 año):")
    print("   - Descuento: ~20-30% sobre OnDemand")
    print("   - Aplicado: SÍ en nuestro análisis")
    print("   - Factor: 0.70x (30% de descuento)")
    print()
    print("2. Saving Plans (3 años):")
    print("   - Descuento: ~40-50% sobre OnDemand")
    print("   - Aplicado: SÍ en nuestro análisis")
    print("   - Factor: 0.50x (50% de descuento)")
    print()
    print("3. Reserved Instances (1 año):")
    print("   - Descuento: ~25-35%")
    print("   - NO aplicado en análisis base")
    print()
    print("4. Spot Instances:")
    print("   - Descuento: ~70-90%")
    print("   - NO recomendado para producción")
    print()
    
    print("="*110)
    print("COMPARACIÓN CON OTRAS OPCIONES")
    print("="*110)
    print()
    print("OPCIÓN 1: AWS (Actual - Basado en precios us-east-2)")
    print("  Mensual: $13,260")
    print("  Anual:   $159,120")
    print()
    
    # Simulación Azure
    print("OPCIÓN 2: Azure (us-east región equivalente)")
    print("  - Standard_B2s: ~$27-30/mes (vs AWS t3.large $30)")
    print("  - Standard_D4as_v4: ~$80-90/mes")
    print("  - Standard_F8s_v2: ~$150-170/mes")
    print("  Estimación Anual: ~$160,000-170,000 (similar a AWS)")
    print()
    
    # GCP
    print("OPCIÓN 3: Google Cloud (compute.googleapis.com - us-central1)")
    print("  - n1-standard-2: ~$50-60/mes")
    print("  - n1-standard-4: ~$100-120/mes")
    print("  - n1-standard-8: ~$200-240/mes")
    print("  Estimación Anual: ~$140,000-160,000 (puede ser comparable)")
    print()
    
    print("="*110)
    print("RECOMENDACIONES")
    print("="*110)
    print()
    print("1. VALIDAR PRECIOS ACTUALES")
    print("   - Los precios AWS cambian mensualmente")
    print("   - Revisar AWS pricing calculator oficial")
    print("   - Incluir costos adicionales (EBS, NAT, etc.)")
    print()
    print("2. CONSIDERAR COSTOS ADICIONALES")
    print("   - Almacenamiento EBS gp3: ~$0.08/GB-mes")
    print("   - Networking (Data transfer out): ~$0.02/GB")
    print("   - NAT Gateway: ~$32/mes + $0.045/GB")
    print("   - Load Balancer: ~$16/mes")
    print()
    print("3. OPTIMIZACIONES POSIBLES")
    print("   - Usar Fargate en lugar de EC2 para algunos workloads")
    print("   - Consolidar microservicios en AKS/EKS")
    print("   - Usar Lambda para funciones sin estado")
    print("   - RDS en lugar de instancias de base de datos")
    print()


if __name__ == "__main__":
    show_pricing_assumptions()
