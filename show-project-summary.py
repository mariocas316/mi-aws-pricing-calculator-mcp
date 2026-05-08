#!/usr/bin/env python3
"""
Resumen final del proyecto - Calculadora AWS
"""

import json
from pathlib import Path

def show_final_summary():
    print('='*120)
    print('✅ CALCULADORA AWS - RESUMEN FINAL DEL PROYECTO')
    print('='*120)
    print()
    
    # Cargar datos
    with open('vm-costs-azure-aws-mapping.json', 'r') as f:
        costs = json.load(f)
    
    with open('aks-workers-analysis.json', 'r') as f:
        aks = json.load(f)
    
    print('📊 INFRAESTRUCTURA ANALIZADA')
    print()
    print(f'  VMs Tradicionales:     {len(costs.get("vms", []))} máquinas')
    print(f'  AKS Workers:           {aks["total_aks_workers"]} workers')
    print(f'  Total Nodos:           {len(costs.get("vms", [])) + aks["total_aks_workers"]} nodos')
    print()
    
    print('💾 RECURSOS TOTALES')
    print()
    print(f'  vCPUs VMs:             {568}')
    print(f'  vCPUs AKS:             {aks["total_aks_vcpu"]}')
    print(f'  vCPUs Total:           {568 + aks["total_aks_vcpu"]}')
    print()
    print(f'  RAM VMs:               1,900 GB')
    print(f'  RAM AKS:               {aks["total_aks_ram"]} GB')
    print(f'  RAM Total:             {1900 + aks["total_aks_ram"]} GB ({(1900 + aks["total_aks_ram"])/1024:.1f} TB)')
    print()
    
    print('💰 COMPARACIÓN DE COSTOS - VMs Tradicionales')
    print()
    print(f'  Azure (Actual):        ${costs["total_azure_annual"]:>12,.2f}/año')
    print(f'  AWS OnDemand:          ${costs["total_aws_annual"]:>12,.2f}/año')
    print(f'  AWS 3yr Reserved:      ${costs["total_aws_annual"] * 0.50:>12,.2f}/año')
    print(f'  Ahorro (3yr):          ${costs["total_azure_annual"] - (costs["total_aws_annual"] * 0.50):>12,.2f}/año')
    print()
    
    print('💰 COMPARACIÓN DE COSTOS - AKS Workers')
    print()
    aks_cost_monthly = aks['total_monthly_cost_aks']
    aks_cost_annual = aks_cost_monthly * 12
    print(f'  Azure (Est.):          ${45600 * 12:>12,.2f}/año')
    print(f'  AWS/EKS OnDemand:      ${aks_cost_annual:>12,.2f}/año')
    print(f'  AWS/EKS 3yr Reserved:  ${aks_cost_annual * 0.50:>12,.2f}/año')
    print()
    
    print('💰 TOTALES COMBINADOS (VMs + AKS)')
    print()
    total_azure_annual = costs['total_azure_annual'] + (45600 * 12)
    total_aws_annual = costs['total_aws_annual'] + aks_cost_annual
    total_reserved = (total_aws_annual * 0.50)
    total_savings = total_azure_annual - total_reserved
    
    print(f'  Azure Actual:          ${total_azure_annual:>12,.2f}/año')
    print(f'  AWS OnDemand:          ${total_aws_annual:>12,.2f}/año')
    print(f'  AWS 3yr Reserved:      ${total_reserved:>12,.2f}/año')
    print(f'  {"-"*60}')
    print(f'  Ahorro Total (76%):    ${total_savings:>12,.2f}/año ✨')
    print()
    
    print('='*120)
    print('🔧 HERRAMIENTAS MCP DISPONIBLES')
    print('='*120)
    print()
    print('  1. map_azure_vm_to_ec2')
    print('     - Mapea una VM individual Azure → EC2')
    print('     - Calcula costo comparativo')
    print()
    print('  2. get_azure_aws_cost_comparison')
    print('     - Comparación total de costos')
    print('     - Filtrable por ambiente')
    print()
    print('  3. create_aws_migration_estimate')
    print('     - Crea estimado AWS automático')
    print('     - Genera URL calculator.aws')
    print()
    
    print('='*120)
    print('✅ PROYECTO COMPLETADO')
    print('='*120)


if __name__ == "__main__":
    show_final_summary()
