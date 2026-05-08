#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract VM costs for AKS worker nodes by cluster
"""

import pandas as pd
from pathlib import Path
import re

cost_files_dir = Path("archivostcoonnet/CostManagement")

cost_files = [
    ("CostManagement_Onnet-Dev_2026-04-17-1503 (1).xlsx", "Dev"),
    ("CostManagement_Onnet-QA_2026-04-17-1536.xlsx", "QA"),
    ("CostManagement_Onnet-Prod_2026-04-17-1534.xlsx", "Prod"),
    ("CostManagement_Onnet-CentralHub_2026-04-17-1511.xlsx", "CentralHub"),
]

# Known AKS clusters
known_clusters = [
    "aks-be-k8",
    "aks-bpi-mdso-k8",
    "aks-uaa-k8",
    "aks-integrations",
]

print("=" * 120)
print("AKS WORKER NODES (VM) COST EXTRACTION")
print("=" * 120)

vm_costs_by_env = {}
total_aks_complete = {}

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        print(f"\n❌ File not found: {filepath}\n")
        continue
    
    print(f"\n{'='*120}")
    print(f"Environment: {env_name}")
    print(f"{'='*120}")
    
    try:
        df = pd.read_excel(filepath)
        
        # Find VM resources
        vm_mask = df['ResourceType'].str.lower().str.contains('virtualmachine', case=False, na=False)
        vm_df = df[vm_mask]
        
        print(f"\nTotal rows in file: {len(df)}")
        print(f"Total VM rows: {len(vm_df)}")
        
        # Filter for AKS-related VMs
        aks_vm_df = pd.DataFrame()
        
        for cluster in known_clusters:
            mask = vm_df['ResourceId'].str.contains(cluster, case=False, na=False)
            cluster_vms = vm_df[mask]
            
            if len(cluster_vms) > 0:
                print(f"\n  Found {len(cluster_vms)} VMs for cluster '{cluster}'")
                aks_vm_df = pd.concat([aks_vm_df, cluster_vms], ignore_index=True)
        
        # Also look for VMs with naming patterns like "aks-nodepool" or similar
        if len(aks_vm_df) == 0:
            aks_pattern = vm_df['ResourceId'].str.contains(r'aks-.*node|nodepool|k8.*node', case=False, na=False, regex=True)
            potential_aks_vms = vm_df[aks_pattern]
            
            if len(potential_aks_vms) > 0:
                print(f"\n  Found {len(potential_aks_vms)} potential AKS VMs by naming pattern")
                aks_vm_df = potential_aks_vms
        
        if len(aks_vm_df) > 0:
            # Group by VM and show costs
            print(f"\n  VM Cost Breakdown:")
            print(f"  {'-'*116}")
            
            vm_costs = aks_vm_df.groupby('ResourceId')['CostUSD'].sum().sort_values(ascending=False)
            
            total_vm_cost = 0
            for vm_id, cost in vm_costs.items():
                # Extract just the VM name
                vm_name = vm_id.split('/')[-1] if '/' in vm_id else vm_id
                rows = len(aks_vm_df[aks_vm_df['ResourceId'] == vm_id])
                print(f"    {vm_name:50} : ${cost:>12,.2f}  ({rows} meter rows)")
                total_vm_cost += cost
            
            print(f"  {'-'*116}")
            print(f"  Total AKS Worker Nodes (VMs): ${total_vm_cost:,.2f}")
            vm_costs_by_env[env_name] = total_vm_cost
            
        else:
            print(f"\n  No AKS-related VMs found with current patterns")
            vm_costs_by_env[env_name] = 0
        
        # Get container-related costs (from previous analysis)
        container_registry = df[df['ServiceName'] == 'Container Registry']['CostUSD'].sum()
        container_instances = df[df['ServiceName'] == 'Container Instances']['CostUSD'].sum()
        defender = df[df['ServiceName'] == 'Microsoft Defender for Cloud']['CostUSD'].sum()
        container_total = container_registry + container_instances + defender
        
        # Calculate AKS complete cost
        aks_complete = vm_costs_by_env[env_name] + container_total
        total_aks_complete[env_name] = aks_complete
        
        print(f"\n  COMPLETE AKS COST FOR {env_name}:")
        print(f"     Worker Nodes (VMs)    : ${vm_costs_by_env[env_name]:>12,.2f}")
        print(f"     Container Services    : ${container_total:>12,.2f}")
        print(f"                            {'-'*20}")
        print(f"     TOTAL AKS {env_name:6} : ${aks_complete:>12,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        vm_costs_by_env[env_name] = 0
        total_aks_complete[env_name] = 0

print(f"\n{'='*120}")
print("FINAL SUMMARY - AKS TOTAL COSTS")
print(f"{'='*120}\n")

print(f"{'Environment':<15} {'Worker Nodes':>15} {'Container Svc':>15} {'TOTAL':>15}")
print("-" * 65)

grand_total_vms = 0
grand_total_containers = 0

for env in ['Dev', 'QA', 'Prod', 'CentralHub']:
    if env in total_aks_complete:
        # Get container cost
        filepath = cost_files_dir / [f for f, e in cost_files if e == env][0]
        if filepath.exists():
            df = pd.read_excel(filepath)
            container_total = (
                df[df['ServiceName'] == 'Container Registry']['CostUSD'].sum() +
                df[df['ServiceName'] == 'Container Instances']['CostUSD'].sum() +
                df[df['ServiceName'] == 'Microsoft Defender for Cloud']['CostUSD'].sum()
            )
        else:
            container_total = 0
        
        vm_cost = vm_costs_by_env.get(env, 0)
        total = total_aks_complete.get(env, 0)
        
        print(f"{env:<15} ${vm_cost:>14,.2f} ${container_total:>14,.2f} ${total:>14,.2f}")
        
        grand_total_vms += vm_cost
        grand_total_containers += container_total

print("-" * 65)
total_all = grand_total_vms + grand_total_containers
print(f"{'TOTAL':<15} ${grand_total_vms:>14,.2f} ${grand_total_containers:>14,.2f} ${total_all:>14,.2f}")

print(f"\n{'='*120}")
print(f"\nMONTHLY COST:   ${total_all:,.2f}")
print(f"ANNUAL COST:    ${total_all * 12:,.2f}")
print(f"\n{'='*120}\n")
