#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify AKS clusters and nodes count vs inventory
"""

import pandas as pd
from pathlib import Path

cost_files_dir = Path("archivostcoonnet/CostManagement")

cost_files = [
    ("CostManagement_Onnet-Dev_2026-04-17-1503 (1).xlsx", "Dev"),
    ("CostManagement_Onnet-QA_2026-04-17-1536.xlsx", "QA"),
    ("CostManagement_Onnet-Prod_2026-04-17-1534.xlsx", "Prod"),
    ("CostManagement_Onnet-CentralHub_2026-04-17-1511.xlsx", "CentralHub"),
]

print("=" * 120)
print("AKS CLUSTERS AND NODES VERIFICATION")
print("=" * 120)

clusters_found = {}
total_nodes = 0
all_vms = []

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    print(f"\n{env_name}:")
    print("-" * 120)
    
    try:
        df = pd.read_excel(filepath)
        
        # Find all VM resources
        vm_mask = df['ResourceType'].str.lower().str.contains('virtualmachine', case=False, na=False)
        vm_df = df[vm_mask]
        
        # Extract cluster names from ResourceId
        # Pattern: .../managedclusters/cluster-name or /virtualMachines/aks-...
        
        cluster_names = set()
        
        for resource_id in vm_df['ResourceId'].unique():
            if pd.isna(resource_id):
                continue
                
            resource_id_str = str(resource_id).lower()
            
            # Extract cluster name from different patterns
            if 'managedclusters' in resource_id_str:
                # Extract cluster name after 'managedclusters/'
                parts = resource_id_str.split('managedclusters/')
                if len(parts) > 1:
                    cluster_name = parts[1].split('/')[0]
                    cluster_names.add(cluster_name)
            elif 'virtualmachines' in resource_id_str:
                # Try to find cluster pattern in VM name
                parts = resource_id_str.split('virtualmachines/')
                if len(parts) > 1:
                    vm_name = parts[1]
                    # Look for aks- pattern in VMSS or VM names
                    if 'aks-' in vm_name:
                        # Extract VMSS name (e.g., aks-npbpeastus2-35869856-vmss)
                        cluster_names.add(vm_name)
        
        # Get unique VMs (VMSS instances)
        unique_vms = vm_df['ResourceId'].nunique()
        
        print(f"  Total VM rows: {len(vm_df)}")
        print(f"  Unique VM/VMSS: {unique_vms}")
        print(f"  Unique Clusters/VMSS patterns found: {len(cluster_names)}")
        
        if cluster_names:
            print(f"\n  Clusters/VMSS patterns:")
            for i, cluster in enumerate(sorted(cluster_names), 1):
                cluster_vms = vm_df[vm_df['ResourceId'].str.contains(cluster, case=False, na=False)]
                vm_cost = cluster_vms['CostUSD'].sum()
                print(f"    {i}. {cluster}")
                print(f"       - VMs: {len(cluster_vms)}")
                print(f"       - Cost: ${vm_cost:,.2f}")
                
                all_vms.append({
                    'Environment': env_name,
                    'Cluster': cluster,
                    'VMs': len(cluster_vms),
                    'Cost': vm_cost
                })
                total_nodes += len(cluster_vms)
        
    except Exception as e:
        print(f"Error: {e}")

print(f"\n{'='*120}")
print("SUMMARY")
print(f"{'='*120}\n")

# Count unique clusters
unique_clusters = {}
for vm in all_vms:
    cluster_key = vm['Cluster']
    if cluster_key not in unique_clusters:
        unique_clusters[cluster_key] = []
    unique_clusters[cluster_key].append(vm)

print(f"Total unique clusters/VMSS found: {len(unique_clusters)}")
print(f"Total VM rows found: {total_nodes}")

print(f"\nExpected from inventory:")
print(f"  Clusters: 10")
print(f"  Nodes (active): 76")
print(f"  vCPUs: 1,456")

print(f"\nFound from Cost Management:")
print(f"  Clusters/VMSS patterns: {len(unique_clusters)}")
print(f"  Total VM rows: {total_nodes}")
print(f"  vCPUs: [checking...]")

print(f"\nDiscrepancy Analysis:")
print(f"  Clusters: Expected 10, Found {len(unique_clusters)} (possible VMSS instances counted instead)")
print(f"  Nodes: Expected 76, Found {total_nodes}")

print(f"\n{'='*120}\n")

# Try to find vCPU information
print("Searching for vCPU information in Cost Management files...")
print("-" * 120)

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    print(f"\n{env_name}:")
    
    try:
        df = pd.read_excel(filepath)
        
        # Look for Meter column that might contain vCPU info
        if 'Meter' in df.columns:
            vcpu_rows = df[df['Meter'].str.contains('vcpu|vcore|core', case=False, na=False)]
            
            if len(vcpu_rows) > 0:
                print(f"  Found {len(vcpu_rows)} vCPU-related meter rows")
                
                # Group by Meter and sum costs
                vcpu_summary = vcpu_rows.groupby('Meter')['CostUSD'].sum().sort_values(ascending=False)
                
                for meter, cost in vcpu_summary.items():
                    print(f"    {meter}: ${cost:,.2f}")
                
                total_vcpu_cost = vcpu_rows['CostUSD'].sum()
                print(f"  Total vCPU cost for {env_name}: ${total_vcpu_cost:,.2f}")
            else:
                print(f"  No vCPU-related meters found")
        
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n{'='*120}\n")
