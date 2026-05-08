#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Search for managedClusters in Cost Management files
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
print("SEARCHING FOR MANAGED CLUSTERS AND KUBERNETES SERVICES")
print("=" * 100)

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        print(f"\n❌ File not found: {filepath}")
        continue
    
    print(f"\n📊 Environment: {env_name}")
    print(f"   File: {filename}")
    
    try:
        df = pd.read_excel(filepath)
        
        # Search for managedClusters
        managed = df[df['ResourceType'].str.contains('managedClusters', case=False, na=False)]
        
        if len(managed) > 0:
            print(f"   ✅ Found {len(managed)} managedClusters rows")
            print(f"\n   Details:")
            for idx, row in managed.iterrows():
                print(f"      ResourceType: {row['ResourceType']}")
                print(f"      ServiceName: {row['ServiceName']}")
                print(f"      ServiceTier: {row['ServiceTier']}")
                print(f"      Meter: {row['Meter']}")
                print(f"      CostUSD: ${row['CostUSD']:,.2f}")
                print()
        else:
            print(f"   ⚠️  No managedClusters found")
        
        # Show all unique ServiceNames related to containers/kubernetes
        print(f"\n   All unique ServiceNames in this file:")
        services = df['ServiceName'].unique()
        for service in sorted(services):
            if service and ('container' in str(service).lower() or 'kubernetes' in str(service).lower() or 'registry' in str(service).lower()):
                matching_rows = df[df['ServiceName'] == service]
                total_cost = matching_rows['CostUSD'].sum()
                print(f"      - {service}: ${total_cost:,.2f} ({len(matching_rows)} rows)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 100)
