#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Search for all container-related services and compute that might belong to AKS
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
print("ALL CONTAINER-RELATED SERVICES BY ENVIRONMENT")
print("=" * 100)

total_by_env = {}

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    print(f"\n{env_name}:")
    print("-" * 100)
    
    try:
        df = pd.read_excel(filepath)
        
        # Filter for container-related services
        container_keywords = ['container', 'kubernetes', 'aks', 'registry', 'instances', 'managed', 'defender']
        mask = df['ServiceName'].str.lower().str.contains('|'.join(container_keywords), na=False)
        
        container_df = df[mask]
        
        if len(container_df) == 0:
            print(f"  No container-related services found")
        else:
            # Show all container services with costs
            grouped = container_df.groupby('ServiceName')['CostUSD'].sum().sort_values(ascending=False)
            
            env_total = 0
            for service, cost in grouped.items():
                rows_count = len(container_df[container_df['ServiceName'] == service])
                print(f"  {service:40} : ${cost:>12,.2f}  ({rows_count} rows)")
                env_total += cost
            
            print(f"  {'-'*100}")
            print(f"  Total container-related:                 : ${env_total:>12,.2f}")
            total_by_env[env_name] = env_total
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        total_by_env[env_name] = 0

print(f"\n{'='*100}")
print("SUMMARY - ALL CONTAINER SERVICES")
print(f"{'='*100}\n")

for env in ['Dev', 'QA', 'Prod', 'CentralHub']:
    cost = total_by_env.get(env, 0)
    print(f"  {env:15} : ${cost:>12,.2f}/month")

total_all = sum(total_by_env.values())
print(f"\n  {'Total':15} : ${total_all:>12,.2f}/month")
print(f"  {'Annual':15} : ${total_all * 12:>12,.2f}/year")

print("\n" + "=" * 100)
