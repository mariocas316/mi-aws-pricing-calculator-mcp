#!/usr/bin/env python3
"""
Script para crear estimaciones en AWS Pricing Calculator
Utiliza la herramienta MCP de AWS Pricing Calculator
"""

import json
import os
from datetime import datetime

OUTPUT_DIR = "aws-migration-estimates"

def load_mapping():
    """Carga el mapeo de Azure a AWS"""
    mapping_path = os.path.join(OUTPUT_DIR, "azure-aws-mapping.json")
    with open(mapping_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_calculator_instructions(mapping_doc):
    """Genera instrucciones para crear estimaciones en AWS Pricing Calculator"""
    
    instructions = {
        "summary": {
            "title": "AWS Pricing Calculator - Databricks Migration Estimates",
            "total_azure_cost": mapping_doc['total_azure_cost'],
            "estimated_aws_cost": 0,
            "created_date": datetime.now().isoformat(),
            "instructions": "Create separate estimates for each resource group using AWS Pricing Calculator"
        },
        "resource_group_estimates": []
    }
    
    print("\n" + "=" * 100)
    print("INSTRUCCIONES PARA CREAR ESTIMACIONES EN AWS PRICING CALCULATOR")
    print("=" * 100)
    
    for rg_name, rg_mapping in mapping_doc['resource_groups'].items():
        print(f"\n📋 RESOURCE GROUP: {rg_name}")
        print(f"   Azure Cost: ${rg_mapping['azure_cost']:,.2f}")
        print(f"   AWS Estimated: ${rg_mapping['estimated_aws_cost']:,.2f}")
        
        rg_estimate = {
            "name": f"Databricks_{rg_name.replace('rg-', '').replace('-', '_')}",
            "azure_rg": rg_name,
            "azure_cost": rg_mapping['azure_cost'],
            "estimated_aws_cost": 0,  # Inicializar, se actualiza conforme se agregan servicios
            "services_to_add": []
        }
        
        # Procesar componentes
        emr_cost = 0
        athena_cost = 0
        glue_cost = 0
        storage_cost = 0
        
        print("\n   Servicios a configurar:")
        
        for component in rg_mapping['aws_components']:
            if 'EMR' in component.get('main_component', '') or 'emr' in component.get('aws_service', ''):
                emr_cost += component.get('estimated_aws_cost', 0)
            elif 'Athena' in component.get('aws_equivalent', ''):
                athena_cost += component.get('estimated_aws_cost', 0)
            elif 'Glue' in component.get('main_component', ''):
                glue_cost += component.get('estimated_aws_cost', 0)
        
        # EMR Cluster
        if emr_cost > 0:
            emr_info = {
                "service": "EC2 (EMR Cluster)",
                "description": f"Spark cluster for Databricks workloads",
                "estimated_monthly_cost": emr_cost,
                "configuration": {
                    "instance_type": "r5.2xlarge",  # Aproximado a workloads de Databricks
                    "instance_count": calculate_emr_instances(emr_cost),
                    "operating_system": "Linux",
                    "workload": "Analytics",
                    "on_demand_or_reserved": "On-Demand"
                }
            }
            rg_estimate['services_to_add'].append(emr_info)
            rg_estimate['estimated_aws_cost'] += emr_cost
            print(f"      ✓ EMR Cluster: ${emr_cost:,.2f}")
        
        # Athena
        if athena_cost > 0:
            athena_info = {
                "service": "Athena",
                "description": "SQL queries on S3 data",
                "estimated_monthly_cost": athena_cost,
                "configuration": {
                    "query_type": "Standard",
                    "data_scanned_gb_per_month": calculate_data_scanned(athena_cost)
                }
            }
            rg_estimate['services_to_add'].append(athena_info)
            rg_estimate['estimated_aws_cost'] += athena_cost
            print(f"      ✓ Athena: ${athena_cost:,.2f}")
        
        # Glue
        if glue_cost > 0:
            glue_info = {
                "service": "AWS Glue",
                "description": "ETL and data catalog",
                "estimated_monthly_cost": glue_cost,
                "configuration": {
                    "dpu_hours_per_month": calculate_glue_dpus(glue_cost)
                }
            }
            rg_estimate['services_to_add'].append(glue_info)
            rg_estimate['estimated_aws_cost'] += glue_cost
            print(f"      ✓ AWS Glue: ${glue_cost:,.2f}")
        
        # S3 Storage (siempre necesario)
        s3_cost = 100  # Estimado
        s3_info = {
            "service": "S3",
            "description": "Object storage for data lake",
            "estimated_monthly_cost": s3_cost,
            "configuration": {
                "storage_class": "Standard",
                "estimated_storage_gb": 500,
                "data_transfer_gb": 10
            }
        }
        rg_estimate['services_to_add'].append(s3_info)
        rg_estimate['estimated_aws_cost'] += s3_cost
        print(f"      ✓ S3: ${s3_cost:,.2f}")
        
        # Lambda para jobs serverless
        lambda_cost = 20  # Estimado
        lambda_info = {
            "service": "Lambda",
            "description": "Serverless compute for job orchestration",
            "estimated_monthly_cost": lambda_cost,
            "configuration": {
                "memory_mb": 256,
                "duration_seconds": 60,
                "monthly_invocations": 1000000
            }
        }
        rg_estimate['services_to_add'].append(lambda_info)
        rg_estimate['estimated_aws_cost'] += lambda_cost
        print(f"      ✓ Lambda: ${lambda_cost:,.2f}")
        
        instructions['resource_group_estimates'].append(rg_estimate)
        if 'estimated_aws_cost' not in instructions:
            instructions['estimated_aws_cost'] = 0
        instructions['estimated_aws_cost'] += rg_estimate.get('estimated_aws_cost', 0)
    
    # Resumen final
    print("\n" + "=" * 100)
    print("RESUMEN FINAL")
    print("=" * 100)
    print(f"\n💰 Costo Azure Total: ${instructions['summary']['total_azure_cost']:,.2f}")
    print(f"💰 Costo AWS Total Estimado: ${instructions['estimated_aws_cost']:,.2f}")
    print(f"📊 Ahorro Potencial: ${instructions['summary']['total_azure_cost'] - instructions['estimated_aws_cost']:,.2f}")
    print(f"📊 % Ahorro: {((instructions['summary']['total_azure_cost'] - instructions['estimated_aws_cost']) / instructions['summary']['total_azure_cost'] * 100):.1f}%")
    
    # Guardar instrucciones
    inst_path = os.path.join(OUTPUT_DIR, "calculator-instructions.json")
    with open(inst_path, 'w', encoding='utf-8') as f:
        json.dump(instructions, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ Instrucciones guardadas: {inst_path}")
    
    return instructions

def calculate_emr_instances(cost):
    """Calcula número aproximado de instancias EMR"""
    # r5.2xlarge cuesta aproximadamente $0.504/hora
    # Asumiendo 24x7 = 730 horas/mes
    cost_per_hour_per_instance = 0.5
    hours_per_month = 730
    cost_per_instance_per_month = cost_per_hour_per_instance * hours_per_month
    
    return max(1, int(cost / cost_per_instance_per_month))

def calculate_data_scanned(cost):
    """Calcula GB de datos escaneados por Athena"""
    # Athena cuesta $5 por TB = $0.005 per GB
    return int((cost / 0.005) * 1000)  # en GB

def calculate_glue_dpus(cost):
    """Calcula DPU-horas para Glue"""
    # Glue cuesta aproximadamente $0.44 por DPU-hora
    return int(cost / 0.44)

def create_mcp_format_payloads(instructions):
    """Crea payloads en formato compatible con MCP"""
    
    mcp_payloads = {
        "metadata": {
            "source": "Databricks Azure Migration",
            "date": datetime.now().isoformat(),
            "total_estimates": len(instructions['resource_group_estimates']),
            "note": "Use these payloads with AWS Pricing Calculator MCP tool"
        },
        "estimates": []
    }
    
    print("\n" + "=" * 100)
    print("PAYLOADS EN FORMATO MCP")
    print("=" * 100)
    
    for estimate in instructions['resource_group_estimates']:
        print(f"\n📋 Estimate: {estimate['name']}")
        
        estimate_payload = {
            "name": estimate['name'],
            "region": "us-east-1",
            "group": "Databricks Migration",
            "services": []
        }
        
        for service_config in estimate['services_to_add']:
            service_name = service_config['service']
            
            # Solo procesar servicios conocidos
            if service_name == "EC2 (EMR Cluster)":
                service_payload = {
                    "service": "amazonEC2",
                    "instance": "On Demand",
                    "config": {
                        "quantity": str(service_config['configuration']['instance_count']),
                        "selectedOS": "linux",
                        "instanceType": "r5.2xlarge",
                        "tenancy": "shared",
                        "region": "us-east-1"
                    }
                }
                estimate_payload['services'].append(service_payload)
                print(f"   ✓ {service_name}: ${service_config['estimated_monthly_cost']:,.2f}")
            
            elif service_name == "Athena":
                service_payload = {
                    "service": "amazonAthena",
                    "config": {
                        "region": "us-east-1",
                        "description": "SQL on S3"
                    }
                }
                estimate_payload['services'].append(service_payload)
                print(f"   ✓ {service_name}: ${service_config['estimated_monthly_cost']:,.2f}")
            
            elif service_name == "AWS Glue":
                service_payload = {
                    "service": "awsGlue",
                    "config": {
                        "region": "us-east-1",
                        "description": "ETL Jobs"
                    }
                }
                estimate_payload['services'].append(service_payload)
                print(f"   ✓ {service_name}: ${service_config['estimated_monthly_cost']:,.2f}")
            
            elif service_name == "S3":
                service_payload = {
                    "service": "amazonS3",
                    "config": {
                        "region": "us-east-1",
                        "description": "Data Lake Storage"
                    }
                }
                estimate_payload['services'].append(service_payload)
                print(f"   ✓ {service_name}: ${service_config['estimated_monthly_cost']:,.2f}")
            
            elif service_name == "Lambda":
                service_payload = {
                    "service": "awsLambda",
                    "config": {
                        "region": "us-east-1",
                        "description": "Job Orchestration"
                    }
                }
                estimate_payload['services'].append(service_payload)
                print(f"   ✓ {service_name}: ${service_config['estimated_monthly_cost']:,.2f}")
        
        mcp_payloads['estimates'].append(estimate_payload)
    
    # Guardar MCP payloads
    mcp_path = os.path.join(OUTPUT_DIR, "mcp-calculator-payloads.json")
    with open(mcp_path, 'w', encoding='utf-8') as f:
        json.dump(mcp_payloads, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ MCP Payloads guardados: {mcp_path}")
    
    return mcp_payloads

def create_step_by_step_guide(instructions):
    """Crea guía paso a paso para crear estimaciones manualmente"""
    
    guide = []
    guide.append("=" * 100)
    guide.append("GUÍA PASO A PASO PARA AWS PRICING CALCULATOR")
    guide.append("=" * 100)
    guide.append("")
    
    for idx, estimate in enumerate(instructions['resource_group_estimates'], 1):
        guide.append(f"\n📋 ESTIMACIÓN {idx}: {estimate['name']}")
        guide.append(f"   Azure Resource Group: {estimate['azure_rg']}")
        guide.append(f"   Costo Azure: ${estimate['azure_cost']:,.2f}")
        guide.append(f"   Costo AWS Estimado: ${estimate['estimated_aws_cost']:,.2f}")
        guide.append("")
        guide.append("   PASOS:")
        
        step = 1
        for service in estimate['services_to_add']:
            guide.append(f"\n   {step}. {service['service']}")
            guide.append(f"      Descripción: {service['description']}")
            guide.append(f"      Costo Estimado: ${service['estimated_monthly_cost']:,.2f}")
            
            if 'configuration' in service:
                guide.append(f"      Configuración:")
                for key, value in service['configuration'].items():
                    guide.append(f"         • {key}: {value}")
            
            step += 1
    
    guide.append("\n" + "=" * 100)
    guide.append("TOTAL ESTIMATED SAVINGS")
    guide.append("=" * 100)
    
    total_azure = instructions['summary']['total_azure_cost']
    total_aws = instructions['estimated_aws_cost']
    savings = total_azure - total_aws
    
    guide.append(f"\nAzure Databricks Total: ${total_azure:,.2f}")
    guide.append(f"AWS Equivalent Total:   ${total_aws:,.2f}")
    guide.append(f"Estimated Savings:      ${savings:,.2f} ({(savings/total_azure*100):.1f}%)")
    guide.append("")
    
    # Guardar guía
    guide_path = os.path.join(OUTPUT_DIR, "step-by-step-guide.txt")
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(guide))
    
    print(f"\n✓ Guía paso a paso: {guide_path}")
    
    # Mostrar guía
    print("\n".join(guide))

def main():
    print("\n" + "=" * 100)
    print("🚀 GENERACIÓN DE ESTIMACIONES PARA AWS PRICING CALCULATOR")
    print("=" * 100)
    
    # Cargar mapeo
    mapping_doc = load_mapping()
    
    # Generar instrucciones
    instructions = generate_calculator_instructions(mapping_doc)
    
    # Crear payloads MCP
    mcp_payloads = create_mcp_format_payloads(instructions)
    
    # Crear guía paso a paso
    create_step_by_step_guide(instructions)
    
    print("\n✅ GENERACIÓN COMPLETADA")

if __name__ == "__main__":
    main()
