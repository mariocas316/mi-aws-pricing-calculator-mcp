#!/usr/bin/env python3
"""
Mapeo de recursos Azure Databricks a AWS y generación de estimaciones
"""

import pandas as pd
import json
import os
from datetime import datetime

OUTPUT_DIR = "aws-migration-estimates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapeo Azure → AWS
AZURE_TO_AWS_MAPPING = {
    # Databricks DBU → Equivalentes en AWS
    "Premium Serverless SQL DBU": {
        "aws_equivalent": "AWS Athena",
        "aws_service": "athena",
        "description": "SQL queries on data in S3",
        "main_component": "Athena",
        "supporting_services": ["S3", "Glue"]
    },
    "Premium All-Purpose Photon DBU": {
        "aws_equivalent": "AWS EMR (Spark) + Photon-like optimization",
        "aws_service": "emr",
        "description": "Spark clusters with optimized compute",
        "main_component": "EC2 (EMR Cluster)",
        "supporting_services": ["EBS", "S3"]
    },
    "Premium All-purpose Compute DBU": {
        "aws_equivalent": "AWS EMR (Spark) Cluster",
        "aws_service": "emr",
        "description": "General-purpose Spark computing",
        "main_component": "EC2 (EMR Cluster)",
        "supporting_services": ["EBS", "S3"]
    },
    "Premium Interactive Serverless Compute - Promo DBU": {
        "aws_equivalent": "AWS EMR Serverless or SageMaker",
        "aws_service": "emr-serverless",
        "description": "Serverless interactive compute",
        "main_component": "EMR Serverless",
        "supporting_services": ["S3"]
    },
    "Premium Automated Serverless Compute - Promo DBU": {
        "aws_equivalent": "AWS Lambda + Glue",
        "aws_service": "lambda-glue",
        "description": "Serverless automated jobs",
        "main_component": "AWS Glue",
        "supporting_services": ["Lambda", "S3"]
    },
    "Premium SQL Compute Pro DBU": {
        "aws_equivalent": "AWS Athena + Redshift",
        "aws_service": "athena-redshift",
        "description": "Advanced SQL compute",
        "main_component": "Redshift",
        "supporting_services": ["Athena", "S3"]
    }
}

def load_databricks_data():
    """Carga datos de Databricks"""
    csv_path = "databricks-analysis/databricks-detallado-completo.csv"
    df = pd.read_csv(csv_path)
    return df

def group_by_resource_group(df):
    """Agrupa datos por Resource Group"""
    grouped = {}
    
    for rg_name in df['ResourceGroupName'].unique():
        rg_data = df[df['ResourceGroupName'] == rg_name]
        grouped[rg_name] = {
            'total_cost': rg_data['CostUSD'].sum(),
            'records': len(rg_data),
            'meters': rg_data['Meter'].value_counts().to_dict(),
            'services': rg_data['ServiceName'].value_counts().to_dict(),
            'data': rg_data
        }
    
    return grouped

def create_aws_mapping_document(grouped_rg):
    """Crea documento de mapeo Azure→AWS"""
    
    mapping_doc = {
        "title": "Azure Databricks to AWS Migration Mapping",
        "date": datetime.now().isoformat(),
        "total_azure_cost": 0,
        "resource_groups": {}
    }
    
    print("\n" + "=" * 100)
    print("MAPEO DE RECURSOS AZURE → AWS")
    print("=" * 100)
    
    for rg_name, rg_info in grouped_rg.items():
        print(f"\n📊 Resource Group: {rg_name}")
        print(f"   Costo Total: ${rg_info['total_cost']:,.2f}")
        print(f"   Total Registros: {rg_info['records']}")
        
        rg_mapping = {
            "azure_name": rg_name,
            "azure_cost": rg_info['total_cost'],
            "estimated_aws_cost": 0,
            "aws_components": [],
            "data_migration": {
                "estimated_size_gb": 0,
                "estimated_transfer_cost": 0
            }
        }
        
        # Procesar cada tipo de métrica en el RG
        print("\n   📈 Componentes mapeados:")
        for meter, count in rg_info['meters'].items():
            if meter in AZURE_TO_AWS_MAPPING:
                mapping = AZURE_TO_AWS_MAPPING[meter]
                meter_rows = rg_info['data'][rg_info['data']['Meter'] == meter]
                meter_cost = meter_rows['CostUSD'].sum()
                
                aws_component = {
                    "azure_meter": meter,
                    "azure_cost": meter_cost,
                    "azure_count": count,
                    "aws_equivalent": mapping['aws_equivalent'],
                    "aws_service": mapping['aws_service'],
                    "main_component": mapping['main_component'],
                    "supporting_services": mapping['supporting_services']
                }
                
                # Estimación del costo en AWS
                aws_estimated = estimate_aws_cost(meter, meter_cost, mapping)
                aws_component['estimated_aws_cost'] = aws_estimated
                rg_mapping['estimated_aws_cost'] += aws_estimated
                
                rg_mapping['aws_components'].append(aws_component)
                
                print(f"      • {meter}")
                print(f"        Azure: ${meter_cost:,.2f} → AWS: ${aws_estimated:,.2f}")
                print(f"        Servicio: {mapping['main_component']}")
            else:
                # Servicios no DBU (Storage, Networking, etc)
                meter_rows = rg_info['data'][rg_info['data']['Meter'] == meter]
                meter_cost = meter_rows['CostUSD'].sum()
                
                aws_component = {
                    "azure_meter": meter,
                    "azure_cost": meter_cost,
                    "azure_count": count,
                    "aws_equivalent": map_non_dbu_services(meter),
                    "aws_service": "mixed",
                    "note": "Included in main compute services"
                }
                rg_mapping['aws_components'].append(aws_component)
                
                print(f"      • {meter}: ${meter_cost:,.2f} (incluido en servicios principales)")
        
        mapping_doc['resource_groups'][rg_name] = rg_mapping
        mapping_doc['total_azure_cost'] += rg_info['total_cost']
    
    # Resumen de costos
    print("\n" + "=" * 100)
    print("RESUMEN DE MIGRACIÓN")
    print("=" * 100)
    
    total_azure = sum(rg['azure_cost'] for rg in mapping_doc['resource_groups'].values())
    total_aws = sum(rg['estimated_aws_cost'] for rg in mapping_doc['resource_groups'].values())
    
    print(f"\n💰 Costo Azure Total: ${total_azure:,.2f}")
    print(f"💰 Costo AWS Estimado: ${total_aws:,.2f}")
    print(f"📊 Diferencia: ${total_aws - total_azure:,.2f} ({((total_aws/total_azure - 1) * 100):.1f}%)")
    
    # Guardar mapping
    mapping_path = os.path.join(OUTPUT_DIR, "azure-aws-mapping.json")
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_doc, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ Mapeo guardado: {mapping_path}")
    
    return mapping_doc

def estimate_aws_cost(meter, azure_cost, mapping):
    """Estima costo en AWS basado en servicio"""
    
    # Estimaciones aproximadas (puede variar según uso actual)
    # Databricks es relativamente más caro que EMR, pero más simple de usar
    
    if "Serverless SQL" in meter:
        # Athena es más barato para queries ocasionales
        return azure_cost * 0.70
    elif "All-Purpose Photon" in meter:
        # EMR con Photon-like optimization
        return azure_cost * 0.85
    elif "All-purpose Compute" in meter:
        # EMR estándar
        return azure_cost * 0.80
    elif "Serverless Compute" in meter:
        # Lambda + Glue es más barato
        return azure_cost * 0.60
    elif "Interactive Serverless" in meter:
        # EMR Serverless
        return azure_cost * 0.75
    else:
        # Default: 85% del costo
        return azure_cost * 0.85

def map_non_dbu_services(meter):
    """Mapea servicios no-DBU"""
    
    mappings = {
        "Storage": "AWS S3 + EBS",
        "Bandwidth": "AWS Data Transfer",
        "NAT Gateway": "AWS NAT Gateway",
        "Premium SSD Managed Disks": "AWS EBS",
        "Compute": "AWS EC2"
    }
    
    for key, value in mappings.items():
        if key.lower() in meter.lower():
            return value
    
    return "AWS Services (Mixed)"

def create_aws_service_summary(mapping_doc):
    """Crea resumen de servicios AWS requeridos"""
    
    aws_services_needed = {}
    
    for rg_name, rg_mapping in mapping_doc['resource_groups'].items():
        print(f"\n🔷 {rg_name}")
        for component in rg_mapping['aws_components']:
            main_service = component.get('main_component', 'Unknown')
            if main_service not in aws_services_needed:
                aws_services_needed[main_service] = {
                    'count': 0,
                    'estimated_cost': 0,
                    'resource_groups': []
                }
            
            aws_services_needed[main_service]['count'] += 1
            aws_services_needed[main_service]['estimated_cost'] += component.get('estimated_aws_cost', 0)
            aws_services_needed[main_service]['resource_groups'].append(rg_name)
    
    print("\n" + "=" * 100)
    print("SERVICIOS AWS REQUERIDOS")
    print("=" * 100)
    
    for service, info in sorted(aws_services_needed.items(), 
                                key=lambda x: x[1]['estimated_cost'], reverse=True):
        print(f"\n📦 {service}")
        print(f"   Costo Estimado: ${info['estimated_cost']:,.2f}")
        print(f"   Componentes: {info['count']}")
        print(f"   Resource Groups: {', '.join(info['resource_groups'][:2])}")
    
    # Guardar resumen
    summary_path = os.path.join(OUTPUT_DIR, "aws-services-needed.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(aws_services_needed, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ Resumen de servicios: {summary_path}")
    
    return aws_services_needed

def generate_calculator_payload(mapping_doc):
    """Genera payload para AWS Pricing Calculator"""
    
    print("\n" + "=" * 100)
    print("GENERANDO PAYLOADS PARA AWS PRICING CALCULATOR")
    print("=" * 100)
    
    payloads = {}
    
    for rg_name, rg_mapping in mapping_doc['resource_groups'].items():
        print(f"\n🔧 Preparando {rg_name}...")
        
        # Crear estructura para cada RG
        rg_services = {
            "region": "us-east-1",  # Equivalente a US East 2 de Azure
            "environment": rg_name,
            "components": []
        }
        
        # Agrupar componentes por tipo
        emr_components = [c for c in rg_mapping['aws_components'] if 'emr' in c.get('aws_service', '').lower()]
        athena_components = [c for c in rg_mapping['aws_components'] if 'athena' in c.get('aws_service', '').lower()]
        glue_components = [c for c in rg_mapping['aws_components'] if 'glue' in c.get('aws_service', '').lower()]
        
        if emr_components:
            rg_services['components'].append({
                'service': 'EMR',
                'type': 'Hadoop Cluster',
                'azure_cost': sum(c['azure_cost'] for c in emr_components),
                'estimated_aws_cost': sum(c.get('estimated_aws_cost', 0) for c in emr_components),
                'details': f"{len(emr_components)} cluster(s)"
            })
        
        if athena_components:
            rg_services['components'].append({
                'service': 'Athena',
                'type': 'SQL Query Engine',
                'azure_cost': sum(c['azure_cost'] for c in athena_components),
                'estimated_aws_cost': sum(c.get('estimated_aws_cost', 0) for c in athena_components),
                'details': f"SQL endpoints: {len(athena_components)}"
            })
        
        if glue_components:
            rg_services['components'].append({
                'service': 'Glue',
                'type': 'ETL Service',
                'azure_cost': sum(c['azure_cost'] for c in glue_components),
                'estimated_aws_cost': sum(c.get('estimated_aws_cost', 0) for c in glue_components),
                'details': f"Jobs: {len(glue_components)}"
            })
        
        # Agregar S3 para storage
        rg_services['components'].append({
            'service': 'S3',
            'type': 'Object Storage',
            'estimated_monthly_cost': 100,  # Estimado
            'details': 'Delta Lake compatibility'
        })
        
        payloads[rg_name] = rg_services
    
    # Guardar payloads
    payload_path = os.path.join(OUTPUT_DIR, "calculator-payloads.json")
    with open(payload_path, 'w', encoding='utf-8') as f:
        json.dump(payloads, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ Payloads generados: {payload_path}")
    
    # Crear resumen visual
    print("\n" + "-" * 100)
    for rg_name, services in payloads.items():
        print(f"\n📋 {rg_name}")
        for comp in services['components']:
            print(f"   • {comp['service']:15} | {comp.get('details', 'N/A')}")
    
    return payloads

def main():
    print("\n🚀 Iniciando análisis de migración Azure Databricks → AWS\n")
    
    # Cargar datos
    df = load_databricks_data()
    grouped_rg = group_by_resource_group(df)
    
    # Crear mapeo
    mapping_doc = create_aws_mapping_document(grouped_rg)
    
    # Crear resumen de servicios
    aws_services = create_aws_service_summary(mapping_doc)
    
    # Generar payloads para calculator
    payloads = generate_calculator_payload(mapping_doc)
    
    print("\n" + "=" * 100)
    print("✅ ANÁLISIS COMPLETO")
    print("=" * 100)
    print(f"\nArchivos generados en {OUTPUT_DIR}/:")
    print("  • azure-aws-mapping.json - Mapeo detallado")
    print("  • aws-services-needed.json - Servicios requeridos")
    print("  • calculator-payloads.json - Payloads para AWS Pricing Calculator")

if __name__ == "__main__":
    main()
