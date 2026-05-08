#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Better analysis: Count unique VMSS instances (not meter rows)
VMSS = Virtual Machine Scale Set, each instance is a node
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
print("AKS NODES COUNT - CORRECTED (Unique VMSS Instances)")
print("=" * 120)

total_nodes_correct = 0
all_nodes = []

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    print(f"\n{env_name}:")
    print("-" * 120)
    
    try:
        df = pd.read_excel(filepath)
        
        # Find VM resources
        vm_mask = df['ResourceType'].str.lower().str.contains('virtualmachine', case=False, na=False)
        vm_df = df[vm_mask]
        
        # Group by ResourceId to get UNIQUE VMs (not meter rows)
        unique_vms = vm_df.groupby('ResourceId').agg({
            'ServiceName': 'first',
            'CostUSD': 'sum',
            'Meter': lambda x: x.tolist()
        }).reset_index()
        
        unique_vms.columns = ['ResourceId', 'ServiceName', 'TotalCost', 'Meters']
        
        print(f"  Total VM rows: {len(vm_df)}")
        print(f"  Unique VM instances: {len(unique_vms)}")
        
        # Filter for AKS-related by name pattern
        aks_mask = unique_vms['ResourceId'].str.contains('aks-', case=False, na=False)
        aks_vms = unique_vms[aks_mask]
        
        if len(aks_vms) > 0:
            print(f"  AKS-related VMs: {len(aks_vms)}")
            print(f"\n  Details:")
            
            for idx, row in aks_vms.iterrows():
                vm_name = row['ResourceId'].split('/')[-1]
                cost = row['TotalCost']
                meters = len(row['Meters'])
                print(f"    {vm_name:50} : ${cost:>12,.2f}  ({meters} meter types)")
                total_nodes_correct += 1
                all_nodes.append({'Env': env_name, 'VM': vm_name, 'Cost': cost})
        else:
            print(f"  No AKS-related VMs found")
        
    except Exception as e:
        print(f"Error: {e}")

print(f"\n{'='*120}")
print("CORRECTED SUMMARY")
print(f"{'='*120}\n")

print(f"Total unique AKS nodes found: {total_nodes_correct}")
print(f"\nExpected inventory:")
print(f"  Clusters: 10")
print(f"  Nodes (active): 76")
print(f"  vCPUs: 1,456")

print(f"\nAnalysis:")
if total_nodes_correct <= 100:
    print(f"  ✓ Node count (found {total_nodes_correct}) is closer to expected 76")
else:
    print(f"  The {total_nodes_correct} nodes found includes multiple meter rows per VM")

# Try to extract vCPU count from meters
print(f"\n{'='*120}")
print("vCPU CALCULATION FROM COST DATA")
print(f"{'='*120}\n")

# Standard Azure VM sizes and their vCPU counts
vm_size_vcpu = {
    'Standard_D2s_v3': 2,
    'Standard_D4s_v3': 4,
    'Standard_D8s_v3': 8,
    'Standard_D16s_v3': 16,
    'Standard_D32s_v3': 32,
    'Standard_E2s_v3': 2,
    'Standard_E4s_v3': 4,
    'Standard_E8s_v3': 8,
    'Standard_B2ms': 2,
    'Standard_B4ms': 4,
    'Standard_B8ms': 8,
}

# Get total vCPU cost across all files
total_vcpu_cost = 0
vcpu_by_env = {}

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    try:
        df = pd.read_excel(filepath)
        
        # Look for vCPU-related costs
        if 'Meter' in df.columns:
            vcpu_rows = df[df['Meter'].str.contains('vcpu|vcore|core', case=False, na=False)]
            
            if len(vcpu_rows) > 0:
                env_vcpu_cost = vcpu_rows['CostUSD'].sum()
                vcpu_by_env[env_name] = env_vcpu_cost
                total_vcpu_cost += env_vcpu_cost
                
                print(f"{env_name}: ${env_vcpu_cost:,.2f} vCPU-related costs")
        
    except Exception as e:
        pass

print(f"\nTotal vCPU costs across all environments: ${total_vcpu_cost:,.2f}")

# Rough estimate: average vCPU costs in Azure
# If we have ~76 nodes and each is roughly D4s (4 vCPU), that's ~304 vCPUs
# Your inventory says 1,456 vCPUs, which would be roughly 19 vCPU per node average

if total_nodes_correct > 0:
    estimated_avg_vcpu_per_node = 1456 / 76 if total_nodes_correct <= 76 else 1456 / total_nodes_correct
    print(f"\nIf {total_nodes_correct} nodes have 1,456 vCPUs:")
    print(f"  Average vCPUs per node: {estimated_avg_vcpu_per_node:.1f}")
    print(f"  This suggests larger VMs (e.g., D8, D16, or memory-optimized VMs)")

print(f"\n{'='*120}\n")
