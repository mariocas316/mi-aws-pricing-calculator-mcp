#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detailed comparison: ARI Inventory vs Cost Management
"""

import pandas as pd

print("=" * 130)
print("COMPARACION DETALLADA: INVENTARIO ARI vs COST MANAGEMENT")
print("=" * 130)

# Read AKS data from Azure Resource Inventory
inventory_file = 'inventarioari/AzureResourceInventory_Report_2026-04-16_16_43.xlsx'

print("\n1. ANALISIS DEL INVENTARIO ARI")
print("-" * 130)

try:
    # Read AKS sheet
    aks_inv = pd.read_excel(inventory_file, sheet_name='AKS')
    
    # Count clusters
    clusters_in_ari = aks_inv['Clusters'].nunique()
    print(f"Clusters únicos en ARI: {clusters_in_ari}")
    
    # Get cluster details
    print("\nClusters en ARI:")
    for cluster in aks_inv['Clusters'].unique():
        cluster_data = aks_inv[aks_inv['Clusters'] == cluster]
        subscription = cluster_data['Subscription'].iloc[0]
        print(f"  - {cluster} ({subscription})")
    
    # Get node pool information
    print(f"\nNode Pools en ARI: {len(aks_inv)} registros")
    
    # Read VMSS sheet for node details
    vmss_inv = pd.read_excel(inventory_file, sheet_name='Virtual Machine Scale Sets')
    
    # Filter for AKS VMSS
    aks_vmss = vmss_inv[vmss_inv['Name'].str.contains('aks-', case=False, na=False)]
    
    print(f"\nVMSS (Node Pools) en VMSS sheet: {len(aks_vmss)}")
    
    # Calculate total nodes from VMSS
    print("\nDetalle de VMSS por ambiente:")
    
    total_instances = 0
    total_vcpu = 0
    
    for idx, row in aks_vmss.iterrows():
        vmss_name = row['Name']
        instances = row.get('Instances', 0)
        vcpus_per = row.get('vCPUs (per Instance)', 0)
        memory = row.get('Memory (GB) (per Instance)', 0)
        vm_size = row.get('VM Size', 'N/A')
        
        if pd.notna(instances):
            total_instances += instances
            if pd.notna(vcpus_per):
                total_vcpu += instances * vcpus_per
        
        sub = row.get('Subscription', 'N/A')
        print(f"  {vmss_name:40} | Sub: {sub:12} | Size: {vm_size:20} | Instances: {instances:3} | vCPU/inst: {vcpus_per}")
    
    print(f"\n{'TOTAL (ARI)':40} | {'':12} | {'':20} | Instances: {total_instances:3} | Total vCPU: {total_vcpu}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*130}")
print("2. COMPARACION CON COST MANAGEMENT")
print("-" * 130)

print(f"""
INVENTARIO ARI (Azure Resource Inventory Report):
  Clusters:        {clusters_in_ari}
  VMSS (Node Pools): {len(aks_vmss)}
  Instancias (nodos): {total_instances}
  vCPUs totales:   {total_vcpu}

COST MANAGEMENT (Billing Data):
  Nodos encontrados: 99
  Costo total:     $48,147.28/mes
    - Workers:     $37,260.06/mes
    - Containers:  $10,887.22/mes

DIFERENCIA EN NODOS:
  ARI: {total_instances}
  Cost Management: 99
  Diferencia: {total_instances - 99} nodos

POSIBLES EXPLICACIONES:
  1. Los nodos en ARI pueden ser "deseados" (Target Nodes)
  2. Cost Management muestra nodos REALES facturados
  3. Puede haber nodos temporales o escalables no contabilizados en ARI
  4. El inventario puede estar desactualizado
""")

# Now get more detailed info about target nodes vs actual
print(f"\n{'='*130}")
print("3. ANALISIS DE TARGET NODES vs ACTUAL NODES (ARI)")
print("-" * 130)

try:
    aks_data = pd.read_excel(inventory_file, sheet_name='AKS')
    
    if 'Target Nodes' in aks_data.columns:
        total_target = aks_data['Target Nodes'].sum()
        print(f"\nTarget Nodes (deseados en ARI): {total_target}")
        
        # Show by cluster
        for cluster in aks_data['Clusters'].unique():
            cluster_data = aks_data[aks_data['Clusters'] == cluster]
            target = cluster_data['Target Nodes'].sum()
            print(f"  - {cluster}: {target} target nodes")
    
    if 'vCPUs (Per Node)' in aks_data.columns:
        avg_vcpu = aks_data['vCPUs (Per Node)'].mean()
        print(f"\nPromedio vCPU por nodo (ARI): {avg_vcpu:.1f}")
        
        print("\nDetalles por Node Pool:")
        for idx, row in aks_data.iterrows():
            cluster = row['Clusters']
            nodepool = row.get('Node Pool Name', 'N/A')
            vcpu = row.get('vCPUs (Per Node)', 0)
            ram = row.get('RAM (GB) Per Node', 0)
            vm_size = row.get('Node Pool Size', 'N/A')
            target = row.get('Target Nodes', 0)
            print(f"  {cluster} / {nodepool:20} | vCPU: {vcpu:3} | RAM: {ram:5} | VM Size: {vm_size:20} | Target: {target}")

except Exception as e:
    print(f"Error: {e}")

print(f"\n{'='*130}\n")
