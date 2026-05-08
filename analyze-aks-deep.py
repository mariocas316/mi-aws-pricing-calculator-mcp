#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deep search for AKS costs (managedClusters and related resources)
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

print("=" * 100)
print("DETAILED AKS COST ANALYSIS - INCLUDING COMPUTE AND ADDONS")
print("=" * 100)

aks_costs = {}
total_monthly = 0

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    print(f"\n{'='*100}")
    print(f"Environment: {env_name}")
    print(f"{'='*100}")
    
    try:
        df = pd.read_excel(filepath)
        
        # Search in ResourceId for managedclusters
        managed_mask = df['ResourceId'].str.contains('managedclusters', case=False, na=False)
        managed_df = df[managed_mask]
        
        print(f"\nTotal rows in file: {len(df)}")
        print(f"Rows with 'managedclusters' in ResourceId: {len(managed_df)}")
        
        if len(managed_df) > 0:
            print(f"\n  AKS-related cost breakdown:")
            
            # Group by Meter and ServiceName
            grouped = managed_df.groupby(['ServiceName', 'Meter'])['CostUSD'].sum().sort_values(ascending=False)
            
            total_cost = 0
            for (service, meter), cost in grouped.items():
                print(f"    {service:30} | {meter:40} | ${cost:>10,.2f}")
                total_cost += cost
            
            print(f"\n  Subtotal (managedClusters): ${total_cost:,.2f}")
            aks_costs[env_name] = total_cost
        else:
            print(f"  ⚠️  No managedClusters found")
            aks_costs[env_name] = 0
        
        # Show all row details
        if len(managed_df) > 0:
            print(f"\n  Raw data rows:")
            for idx, row in managed_df.iterrows():
                print(f"    ResourceType: {row['ResourceType']}")
                print(f"    ResourceId (partial): ...{row['ResourceId'][-60:]}")
                print(f"    ServiceName: {row['ServiceName']}")
                print(f"    Meter: {row['Meter']}")
                print(f"    CostUSD: ${row['CostUSD']:.2f}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        aks_costs[env_name] = 0

print(f"\n{'='*100}")
print("SUMMARY - AKS COSTS (Defender addon only)")
print(f"{'='*100}")

for env, cost in sorted(aks_costs.items()):
    print(f"  {env:15} : ${cost:>12,.2f}/month")

total_aks = sum(aks_costs.values())
print(f"\n  {'Total':15} : ${total_aks:>12,.2f}/month")
print(f"  {'Annual':15} : ${total_aks * 12:>12,.2f}/year")

print(f"\n⚠️  NOTE: These costs represent only 'Microsoft Defender for Cloud' addon on managedClusters.")
print(f"   The actual AKS cluster compute costs may be listed under a different ResourceType or")
print(f"   may not be separately itemized in these Cost Management exports.")

print("\n" + "=" * 100)
