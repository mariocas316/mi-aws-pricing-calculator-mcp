#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Calculadora AWS para Joomla en Producción
Genera la configuración completa para importar a AWS Pricing Calculator
1000 usuarios, Alta Disponibilidad, Multi-AZ
"""

import json
from datetime import datetime

def generate_joomla_calculator():
    """
    Genera la configuración completa de Joomla para AWS Pricing Calculator
    """
    
    # Configuración base
    estimate = {
        "estimateName": "Joomla_Produccion_1000Usuarios_HA",
        "currency": "USD",
        "region": "us-east-2",  # US East (Ohio)
        "createdAt": datetime.now().isoformat(),
        "lastModified": datetime.now().isoformat(),
        "services": []
    }
    
    # ===== SERVICIO 1: EC2 Primary (Joomla - t4g.large) =====
    ec2_primary = {
        "serviceName": "Amazon EC2",
        "description": "EC2 Primary - Joomla App Server (t4g.large)",
        "resourceGroup": "Joomla-Servers",
        "configuration": {
            "operatingSystem": "Linux",
            "instanceType": "t4g.large",
            "tenancy": "Shared",
            "quantity": 1,
            "pricingStrategy": "OnDemand",
            "detailedMonitoring": True,
            "monthlyPricePerInstance": 0.041,
            "hoursPerMonth": 730,
            "monthlyHours": 730,
        },
        "estimatedMonthlyCost": 0.041 * 730,  # $29.93
        "notes": "Primary Joomla instance - t4g.large (2vCPU, 8GB RAM)"
    }
    estimate["services"].append(ec2_primary)
    
    # ===== SERVICIO 2: EC2 Standby (Joomla - t4g.large) =====
    ec2_standby = {
        "serviceName": "Amazon EC2",
        "description": "EC2 Standby - Joomla Replica (t4g.large)",
        "resourceGroup": "Joomla-Servers",
        "configuration": {
            "operatingSystem": "Linux",
            "instanceType": "t4g.large",
            "tenancy": "Shared",
            "quantity": 1,
            "pricingStrategy": "OnDemand",
            "detailedMonitoring": True,
            "monthlyPricePerInstance": 0.041,
            "hoursPerMonth": 730,
        },
        "estimatedMonthlyCost": 0.041 * 730,  # $29.93
        "notes": "Standby instance in different AZ for High Availability"
    }
    estimate["services"].append(ec2_standby)
    
    # ===== SERVICIO 3: Application Load Balancer =====
    alb = {
        "serviceName": "Application Load Balancer",
        "description": "ALB - Joomla Load Balancer",
        "resourceGroup": "Networking",
        "configuration": {
            "numberOfAlb": 1,
            "processedBytesPerMonth": 100,  # GB
            "newConnectionsPerSecond": 10,
            "activeConnectionsPerMinute": 1000,
        },
        "estimatedMonthlyCost": 16.00 + 4.00,  # $20
        "notes": "ALB for distributing traffic to EC2 instances"
    }
    estimate["services"].append(alb)
    
    # ===== SERVICIO 4: RDS MySQL Multi-AZ =====
    rds = {
        "serviceName": "Amazon RDS MySQL",
        "description": "RDS MySQL - Joomla Database (Multi-AZ)",
        "resourceGroup": "Database",
        "configuration": {
            "engine": "MySQL",
            "instanceType": "db.t4g.micro",
            "multiAz": True,
            "allocatedStorageGb": 50,
            "backupRetentionDays": 35,
            "enhancedMonitoring": True,
            "iops": 1000,
        },
        "estimatedMonthlyCost": 60.00 + 12.50 + 5.00 + 10.00,  # $87.50
        "notes": "Multi-AZ MySQL 8.0 with 35-day backup retention"
    }
    estimate["services"].append(rds)
    
    # ===== SERVICIO 5: S3 Standard Storage =====
    s3 = {
        "serviceName": "Amazon S3 Standard",
        "description": "S3 Standard - Joomla Media Library",
        "resourceGroup": "Storage",
        "configuration": {
            "storageGb": 50,
            "storageClass": "Standard",
            "frequency": "month",
            "pricePerGb": 0.023,
            "putCopyPostListRequests": 10000,
            "getSelectOtherRequests": 100000,
            "dataTransferOut": 10,  # GB
        },
        "estimatedMonthlyCost": (50 * 0.023) + (10000 * 0.000005) + (100000 * 0.0000004) + 0.85,
        "notes": "50GB storage for images, plugins, templates, user uploads"
    }
    estimate["services"].append(s3)
    
    # ===== SERVICIO 6: CloudFront CDN =====
    cloudfront = {
        "serviceName": "CloudFront CDN",
        "description": "CloudFront - Content Delivery Network",
        "resourceGroup": "CDN",
        "configuration": {
            "edgeLocations": "All",
            "dataTransferOutGb": 10,
            "httpRequests": 100000,
            "httpsRequests": 100000,
            "lambdaEdge": 0,
        },
        "estimatedMonthlyCost": (10 * 0.085) + (100000 * 0.0075/1000) + (100000 * 0.01/1000) + 5.00,
        "notes": "CloudFront for caching images, CSS, JS - reduces S3 calls"
    }
    estimate["services"].append(cloudfront)
    
    # ===== SERVICIO 7: NAT Gateway =====
    nat_gateway = {
        "serviceName": "NAT Gateway",
        "description": "NAT Gateway - EC2 Internet Access",
        "resourceGroup": "Networking",
        "configuration": {
            "numberOfNatGateways": 1,
            "dataProcessedGb": 5,
        },
        "estimatedMonthlyCost": 32.00 + (5 * 0.045),
        "notes": "NAT Gateway for EC2 outbound traffic (updates, extensions, email)"
    }
    estimate["services"].append(nat_gateway)
    
    # ===== SERVICIO 8: CloudWatch Logs =====
    cloudwatch = {
        "serviceName": "CloudWatch",
        "description": "CloudWatch - Monitoring and Logs",
        "resourceGroup": "Monitoring",
        "configuration": {
            "logsIngestionGb": 100,
            "logRetentionDays": 30,
            "dashboards": 1,
            "alarms": 5,
            "customMetrics": 50,
        },
        "estimatedMonthlyCost": 15.00 + 3.00,  # Logs + Storage
        "notes": "CloudWatch Logs for Apache, MySQL, Application monitoring"
    }
    estimate["services"].append(cloudwatch)
    
    # ===== SERVICIO 9: AWS Backup =====
    backup = {
        "serviceName": "AWS Backup",
        "description": "AWS Backup - Automated Backups",
        "resourceGroup": "Backup",
        "configuration": {
            "protectedResourceType": "RDS",
            "backupsPerMonth": 30,
            "recoveryPointStorageGb": 50,
            "crossRegionBackup": False,
        },
        "estimatedMonthlyCost": 10.00,
        "notes": "Daily automated backups for RDS (35-day retention)"
    }
    estimate["services"].append(backup)
    
    # ===== SERVICIO 10: Secrets Manager =====
    secrets = {
        "serviceName": "Secrets Manager",
        "description": "Secrets Manager - Database Credentials",
        "resourceGroup": "Security",
        "configuration": {
            "secretsStored": 1,
            "apiCallsPerMonth": 100000,
        },
        "estimatedMonthlyCost": 0.40,
        "notes": "Store RDS database password securely"
    }
    estimate["services"].append(secrets)
    
    # ===== SERVICIO 11: Route 53 DNS =====
    route53 = {
        "serviceName": "Route 53",
        "description": "Route 53 - DNS Management",
        "resourceGroup": "Networking",
        "configuration": {
            "hostedZones": 1,
            "queryVolume": 10000000,  # 10M queries per month
            "healthChecks": 1,
        },
        "estimatedMonthlyCost": 0.50 + 0.40,
        "notes": "DNS hosting and health checks for ALB"
    }
    estimate["services"].append(route53)
    
    # ===== SERVICIO 12: ACM SSL Certificate (GRATIS) =====
    ssl = {
        "serviceName": "AWS Certificate Manager",
        "description": "ACM - SSL/TLS Certificate",
        "resourceGroup": "Security",
        "configuration": {
            "certificates": 1,
            "autoRenewal": True,
        },
        "estimatedMonthlyCost": 0.00,
        "notes": "Free public SSL certificate with auto-renewal"
    }
    estimate["services"].append(ssl)
    
    # Calcular total
    total_cost = sum(service.get("estimatedMonthlyCost", 0) for service in estimate["services"])
    
    estimate["summary"] = {
        "totalServiceCount": len(estimate["services"]),
        "estimatedMonthlyCost": round(total_cost, 2),
        "estimatedAnnualCost": round(total_cost * 12, 2),
        "pricingMode": "On-Demand Only",
        "supportPlan": "Business ($515/mes recommended)",
        "grandTotalWithSupport": round(total_cost + 515, 2),
    }
    
    return estimate


def print_summary(estimate):
    """Imprime un resumen legible de la estimación"""
    print("\n" + "="*80)
    print("ESTIMACIÓN AWS - JOOMLA PRODUCCIÓN (1000 USUARIOS)")
    print("="*80 + "\n")
    
    print(f"Nombre: {estimate['estimateName']}")
    print(f"Región: {estimate['region']}")
    print(f"Moneda: {estimate['currency']}")
    print(f"Fecha: {estimate['createdAt']}\n")
    
    print("-" * 80)
    print(f"{'Servicio':<40} {'Costo/mes':>12}")
    print("-" * 80)
    
    for service in estimate["services"]:
        cost = service.get("estimatedMonthlyCost", 0)
        desc = service.get("description", "")[:35]
        print(f"{desc:<40} ${cost:>11,.2f}")
    
    print("-" * 80)
    print(f"{'SUBTOTAL (Servicios AWS)':<40} ${estimate['summary']['estimatedMonthlyCost']:>11,.2f}")
    print(f"{'AWS Support Plan (Business)':<40} ${'515.00':>11}")
    print(f"{'TOTAL MENSUAL':<40} ${estimate['summary']['grandTotalWithSupport']:>11,.2f}")
    print(f"{'TOTAL ANUAL':<40} ${(estimate['summary']['grandTotalWithSupport']*12):>11,.2f}")
    print("\n" + "="*80 + "\n")
    
    print("RECOMENDACIONES:")
    print(f"  • Con Reserved Instances (1 año): -30% = ${estimate['summary']['grandTotalWithSupport']*0.7:,.2f}/mes")
    print(f"  • Con Savings Plans (1 año): -25% = ${estimate['summary']['grandTotalWithSupport']*0.75:,.2f}/mes")
    print(f"  • Costo por usuario/año: ${(estimate['summary']['grandTotalWithSupport']*12)/1000:,.2f}")
    print("\n" + "="*80 + "\n")


def main():
    """Función principal"""
    print("\n🔧 Generando configuración para AWS Pricing Calculator...")
    print("Joomla Producción: 1000 usuarios, Alta Disponibilidad\n")
    
    # Generar estimación
    estimate = generate_joomla_calculator()
    
    # Guardar a JSON
    output_file = "joomla_calculator_config.json"
    with open(output_file, "w") as f:
        json.dump(estimate, f, indent=2)
    
    print(f"✅ Configuración guardada en: {output_file}\n")
    
    # Mostrar resumen
    print_summary(estimate)
    
    # Información adicional
    print("\n📝 NOTAS IMPORTANTES:")
    print("\n1. ARQUITECTURA HA (High Availability):")
    print("   - 2 EC2 en diferentes AZ")
    print("   - ALB distribuye tráfico")
    print("   - RDS Multi-AZ con failover automático")
    print("   - Disponibilidad: 99.5%\n")
    
    print("2. SEGURIDAD:")
    print("   - SSL/TLS gratuito con ACM")
    print("   - RDS en subnet privada")
    print("   - Security Groups restrictivos")
    print("   - Passwords en Secrets Manager\n")
    
    print("3. BACKUPS Y RECUPERACIÓN:")
    print("   - RDS backups diarios (35 días)")
    print("   - AWS Backup automático")
    print("   - RTO: 15 minutos")
    print("   - RPO: 1 hora\n")
    
    print("4. PASOS SIGUIENTES:")
    print("   a) Ir a: https://calculator.aws/#/")
    print("   b) Crear nuevo 'Estimate'")
    print("   c) Agregar servicios MANUALMENTE (referencia: archivo JSON)")
    print("   d) Exportar y compartir el enlace\n")
    
    print("5. COSTO POR USUARIO:")
    monthly_total = estimate['summary']['grandTotalWithSupport']
    cost_per_user = (monthly_total * 12) / 1000
    print(f"   - Costo anual total: ${monthly_total*12:,.2f}")
    print(f"   - Por usuario/año: ${cost_per_user:,.2f}")
    print(f"   - Por usuario/mes: ${cost_per_user/12:,.2f}\n")
    
    return estimate


if __name__ == "__main__":
    estimate = main()
    
    # Exportar datos adicionales para análisis
    export_data = {
        "estimate": estimate,
        "metadata": {
            "script_version": "1.0",
            "generated_date": datetime.now().isoformat(),
            "joomla_specs": {
                "users": 1000,
                "concurrent_users_estimate": 100,
                "architecture": "Multi-AZ High Availability",
                "sla": "99.5%"
            },
            "aws_specs": {
                "region": "us-east-2",
                "ec2_type": "t4g.large",
                "ec2_count": 2,
                "rds_type": "db.t4g.micro",
                "storage_gb": 50,
                "backup_retention_days": 35
            },
            "costs": {
                "monthly_services": estimate['summary']['estimatedMonthlyCost'],
                "monthly_with_support": estimate['summary']['grandTotalWithSupport'],
                "annual_total": estimate['summary']['grandTotalWithSupport'] * 12,
                "cost_per_user_annual": (estimate['summary']['grandTotalWithSupport'] * 12) / 1000,
            }
        }
    }
    
    # Guardar análisis completo
    with open("joomla_calculator_analysis.json", "w") as f:
        json.dump(export_data, f, indent=2)
    
    print("✅ Análisis completo guardado en: joomla_calculator_analysis.json\n")

