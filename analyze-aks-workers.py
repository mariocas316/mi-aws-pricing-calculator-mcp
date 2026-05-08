#!/usr/bin/env python3
"""
Análisis de AKS Workers: Extrae y mapea máquinas de Kubernetes
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

INVENTORY_FILE = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")

def extract_aks_workers():
    """Extrae información de workers de AKS"""
    print("📦 Leyendo AKS Node Pools...\n")
    
    df_aks = pd.read_excel(INVENTORY_FILE, sheet_name='AKS')
    
    print(f"Total node pools encontrados: {len(df_aks)}\n")
    
    aks_workers = []
    total_workers = 0
    total_vcpu = 0
    total_ram = 0
    
    for idx, row in df_aks.iterrows():
        cluster_name = row['Clusters']
        node_pool_name = row['Node Pool Name']
        node_size = row['Node Pool Size']
        target_nodes = row['Target Nodes']
        vcpu_per_node = row['vCPUs (Per Node)']
        ram_per_node = row['RAM (GB) Per Node']
        instance_type = row['Node Pool Size']  # Esto es el tipo de instancia
        power_state = row['Node Pool Power State']
        subscription = row['Subscription']
        
        # Usar Target Nodes si está disponible, sino usar el conteo del pool
        num_nodes = int(target_nodes) if pd.notna(target_nodes) and target_nodes != 0 else 1
        
        total_workers += num_nodes
        vcpu_total = vcpu_per_node * num_nodes if pd.notna(vcpu_per_node) else 0
        ram_total = ram_per_node * num_nodes if pd.notna(ram_per_node) else 0
        
        total_vcpu += vcpu_total
        total_ram += ram_total
        
        # Encontrar tipo de instancia
        instance_col = None
        for col in ['Node Pool Image', 'Node Pool Size']:
            if col in df_aks.columns:
                val = row.get(col)
                if pd.notna(val) and 'Standard_' in str(val):
                    instance_col = val
                    break
        
        # Buscar en las columnas que puedan tener el tipo
        instance_type = None
        if 'Standard_' in str(target_nodes):
            instance_type = str(target_nodes).split()[0]
        
        # Intenta buscar en Node Pool Image
        node_image = row.get('Node Pool Image', '')
        if pd.notna(node_image) and 'Standard_' in str(node_image):
            instance_type = str(node_image)
        
        # Busca directamente en otros campos
        for key in df_aks.columns:
            val = str(row.get(key, ''))
            if val.startswith('Standard_'):
                instance_type = val.split()[0]
                break
        
        worker_info = {
            'cluster': cluster_name,
            'node_pool': node_pool_name,
            'subscription': subscription,
            'num_nodes': num_nodes,
            'instance_type': instance_type or 'Unknown',
            'vcpu_per_node': vcpu_per_node,
            'ram_per_node': ram_per_node,
            'vcpu_total': vcpu_total,
            'ram_total': ram_total,
            'power_state': power_state,
            'os_type': row.get('Node Pool OS Type', 'Unknown'),
            'os': row.get('Node Pool OS', 'Unknown'),
        }
        
        aks_workers.append(worker_info)
    
    return aks_workers, total_workers, total_vcpu, total_ram


def analyze_aks_vs_vms():
    """Compara AKS workers con VMs tradicionales"""
    print("="*100)
    print("ANÁLISIS: AKS WORKERS vs VMs TRADICIONALES")
    print("="*100 + "\n")
    
    # Cargar datos
    with open('vm-azure-aws-mapping.json', 'r', encoding='utf-8') as f:
        traditional_vms = json.load(f)
    
    aks_workers, total_workers, total_aks_vcpu, total_aks_ram = extract_aks_workers()
    
    print("📊 RESUMEN AKS WORKERS\n")
    print(f"   Node pools: {len(aks_workers)}")
    print(f"   Total worker nodes: {total_workers}")
    print(f"   vCPUs totales: {total_aks_vcpu}")
    print(f"   RAM total: {total_aks_ram} GB")
    
    print("\n📊 RESUMEN VMs TRADICIONALES\n")
    print(f"   Total VMs: {len(traditional_vms)}")
    total_vm_vcpu = sum(vm['vcpu'] or 0 for vm in traditional_vms)
    total_vm_ram = sum(vm['memory_gb'] or 0 for vm in traditional_vms)
    print(f"   vCPUs totales: {total_vm_vcpu}")
    print(f"   RAM total: {total_vm_ram} GB")
    
    print("\n📈 COMPARACIÓN TOTAL\n")
    print(f"   VMs + AKS Workers: {len(traditional_vms) + total_workers} nodos totales")
    print(f"   vCPUs (VMs + AKS): {total_vm_vcpu + total_aks_vcpu}")
    print(f"   RAM (VMs + AKS): {total_vm_ram + total_aks_ram} GB")
    
    print("\n🖥️  DETALLE DE AKS NODE POOLS\n")
    print(f"{'Cluster':<35} {'Node Pool':<20} {'Nodes':<6} {'Instancia':<22} {'vCPU':<8} {'RAM (GB)':<10}")
    print("-" * 100)
    
    for worker in aks_workers:
        print(f"{worker['cluster']:<35} {worker['node_pool']:<20} {worker['num_nodes']:<6} "
              f"{worker['instance_type']:<22} {worker['vcpu_total']:<8} {worker['ram_total']:<10}")
    
    print("\n📦 AGRUPACIÓN POR TIPO DE INSTANCIA\n")
    instance_dist = defaultdict(lambda: {'count': 0, 'vcpu': 0, 'ram': 0})
    for worker in aks_workers:
        instance_dist[worker['instance_type']]['count'] += worker['num_nodes']
        instance_dist[worker['instance_type']]['vcpu'] += worker['vcpu_total']
        instance_dist[worker['instance_type']]['ram'] += worker['ram_total']
    
    for instance in sorted(instance_dist.keys(), 
                          key=lambda x: instance_dist[x]['count'], 
                          reverse=True):
        dist = instance_dist[instance]
        print(f"   {instance:<25} {dist['count']:3d} nodos  ({dist['vcpu']:3.0f} vCPU, {dist['ram']:5.0f} GB RAM)")
    
    # Por ambiente
    print("\n🌍 AGRUPACIÓN POR AMBIENTE\n")
    env_dist = defaultdict(lambda: {'workers': 0, 'vcpu': 0, 'ram': 0})
    for worker in aks_workers:
        sub = worker['subscription']
        env_dist[sub]['workers'] += worker['num_nodes']
        env_dist[sub]['vcpu'] += worker['vcpu_total']
        env_dist[sub]['ram'] += worker['ram_total']
    
    for env in sorted(env_dist.keys()):
        dist = env_dist[env]
        print(f"   {env:<25} {dist['workers']:3d} workers ({dist['vcpu']:3.0f} vCPU, {dist['ram']:5.0f} GB)")
    
    # Mapeo a AWS
    print("\n☁️  MAPEO A AWS (Equivalentes aproximados)\n")
    aws_prices = {
        't3.large': 30.00, 't3.xlarge': 60.00, 't3.2xlarge': 120.00,
        'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00, 'c6i.4xlarge': 400.00,
        'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00, 'm6i.4xlarge': 600.00,
        'm6i.8xlarge': 1200.00,
    }
    
    print(f"{'Azure Size':<25} {'Nodos':<8} {'AWS Equivalente':<20} {'$/mes (c/u)':<15} {'Costo Total':<15}")
    print("-" * 85)
    
    aks_total_cost = 0
    for instance, dist in sorted(instance_dist.items(), 
                                  key=lambda x: x[1]['count'], 
                                  reverse=True):
        # Mapear a AWS
        aws_equiv = map_azure_to_aws(instance, dist['vcpu']/dist['count'] if dist['count'] > 0 else 0)
        price = aws_prices.get(aws_equiv, 100.00)
        cost_total = price * dist['count']
        aks_total_cost += cost_total
        
        print(f"{instance:<25} {dist['count']:<8} {aws_equiv:<20} ${price:<14.2f} ${cost_total:<14.2f}")
    
    print(f"\n{'TOTAL AKS/EKS':<25} {total_workers:<8} {'':<20} {'':<15} ${aks_total_cost:<14.2f}")
    
    # Cargar costos de VMs
    print("\n💰 COSTO TOTAL DE INFRAESTRUCTURA\n")
    
    vm_total_cost = 0
    aws_prices_vm = {
        't3.small': 7.50, 't3.medium': 15.00, 't3.large': 30.00,
        't3.xlarge': 60.00, 't3.2xlarge': 120.00,
        'c6i.large': 50.00, 'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00,
        'm6i.large': 75.00, 'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00,
        'm6i.4xlarge': 600.00, 'm6i.8xlarge': 1200.00,
    }
    
    for vm in traditional_vms:
        price = aws_prices_vm.get(vm['aws_equivalent'], 75.00)
        vm_total_cost += price
    
    print(f"   Costo VMs tradicionales:     ${vm_total_cost:>10,.2f}/mes")
    print(f"   Costo AKS/EKS Workers:       ${aks_total_cost:>10,.2f}/mes")
    print(f"   Costo TOTAL (VMs + AKS):     ${vm_total_cost + aks_total_cost:>10,.2f}/mes")
    print(f"\n   Anual (VMs + AKS):           ${(vm_total_cost + aks_total_cost) * 12:>10,.2f}")
    print(f"   Anual con 3 años reservado:  ${(vm_total_cost + aks_total_cost) * 12 * 0.50:>10,.2f} (50% desc)")
    
    # Salvar JSON
    output_file = Path("aks-workers-analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'aks_node_pools': len(aks_workers),
            'total_aks_workers': total_workers,
            'total_aks_vcpu': total_aks_vcpu,
            'total_aks_ram': total_aks_ram,
            'traditional_vms': len(traditional_vms),
            'total_vm_vcpu': total_vm_vcpu,
            'total_vm_ram': total_vm_ram,
            'aks_workers_details': aks_workers,
            'total_monthly_cost_vms': vm_total_cost,
            'total_monthly_cost_aks': aks_total_cost,
            'total_monthly_cost_combined': vm_total_cost + aks_total_cost,
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Análisis guardado en: {output_file}")


def map_azure_to_aws(azure_size, vcpu_per_node):
    """Mapea tamaño de Azure a equivalente AWS"""
    if 'D2' in azure_size or 'd2' in azure_size.lower():
        return 't3.large'
    elif 'D4' in azure_size or 'd4' in azure_size.lower():
        return 't3.xlarge' if vcpu_per_node <= 4 else 'c6i.xlarge'
    elif 'D8' in azure_size or 'd8' in azure_size.lower():
        return 't3.2xlarge' if vcpu_per_node <= 8 else 'c6i.2xlarge'
    elif 'D16' in azure_size or 'd16' in azure_size.lower():
        return 'c6i.2xlarge'
    elif 'D32' in azure_size or 'd32' in azure_size.lower():
        return 'm6i.4xlarge'
    elif 'E' in azure_size or 'e' in azure_size.lower():
        return 'm6i.4xlarge' if vcpu_per_node >= 16 else 't3.2xlarge'
    elif 'B' in azure_size or 'b' in azure_size.lower():
        return 't3.large'
    else:
        return 't3.large'  # Default


if __name__ == "__main__":
    analyze_aks_vs_vms()
