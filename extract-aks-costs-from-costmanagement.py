#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract AKS costs from Cost Management files by environment
"""

import pandas as pd
import os
from pathlib import Path

# Define cost files location
cost_files_dir = Path("archivostcoonnet/CostManagement")

# Files to process: (filename, environment_name)
cost_files = [
    ("CostManagement_Onnet-Dev_2026-04-17-1503 (1).xlsx", "Dev"),
    ("CostManagement_Onnet-QA_2026-04-17-1536.xlsx", "QA"),
    ("CostManagement_Onnet-Prod_2026-04-17-1534.xlsx", "Prod"),
    ("CostManagement_Onnet-CentralHub_2026-04-17-1511.xlsx", "CentralHub"),
]

aks_costs_by_env = {}
total_aks_cost = 0

print("=" * 80)
print("AKS COST EXTRACTION FROM COST MANAGEMENT FILES")
print("=" * 80)
print()

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        continue
    
    try:
        print(f"\n📊 Processing: {env_name}")
        print(f"   File: {filename}")
        
        # Read the Excel file
        df = pd.read_excel(filepath)
        
        print(f"   Total rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        
        # Print sample of data to understand structure
        if len(df) > 0:
            print(f"   First row sample:")
            for col in df.columns[:5]:
                print(f"      {col}: {df.iloc[0][col]}")
        
        # Try to find AKS-related rows
        # Look for ResourceType containing 'kubernetes' or 'managedClusters' or 'AKS'
        aks_indicators = [
            'kubernetes',
            'managedClusters',
            'aks',
            'containerservice',
            'container'
        ]
        
        # Try different column names for resource type
        resource_type_columns = ['ResourceType', 'resourceType', 'Resource Type', 'resource_type']
        service_columns = ['ServiceName', 'serviceName', 'Service Name', 'service_name']
        meter_columns = ['Meter', 'meter', 'MeterName', 'meterName']
        cost_columns = ['CostUSD', 'costUSD', 'Cost USD', 'PreTaxCost', 'pretaxcost', 'MeterCharges']
        
        resource_type_col = None
        service_col = None
        meter_col = None
        cost_col = None
        
        for col in resource_type_columns:
            if col in df.columns:
                resource_type_col = col
                break
        
        for col in service_columns:
            if col in df.columns:
                service_col = col
                break
        
        for col in meter_columns:
            if col in df.columns:
                meter_col = col
                break
        
        for col in cost_columns:
            if col in df.columns:
                cost_col = col
                break
        
        print(f"   Columns found: ResourceType='{resource_type_col}', Service='{service_col}', Meter='{meter_col}', Cost='{cost_col}'")
        
        # Filter AKS costs
        aks_rows = pd.DataFrame()
        
        if resource_type_col and cost_col:
            # Filter by ResourceType
            mask = df[resource_type_col].fillna('').str.lower().str.contains('|'.join(aks_indicators), regex=True)
            aks_rows = df[mask]
        
        if len(aks_rows) > 0:
            # Group by meter if available
            if meter_col and cost_col:
                aks_summary = aks_rows.groupby(meter_col)[cost_col].sum()
                print(f"   AKS-related meters found: {len(aks_summary)}")
                for meter, cost in aks_summary.items():
                    print(f"      - {meter}: ${cost:,.2f}")
            
            total_env_cost = aks_rows[cost_col].sum()
            aks_costs_by_env[env_name] = total_env_cost
            total_aks_cost += total_env_cost
            print(f"   ✅ AKS Total Cost: ${total_env_cost:,.2f}")
        else:
            print(f"   ⚠️  No AKS-related rows found")
            print(f"   Unique ResourceTypes sample:")
            if resource_type_col:
                unique_types = df[resource_type_col].unique()[:10]
                for rt in unique_types:
                    print(f"      - {rt}")
            aks_costs_by_env[env_name] = 0
        
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        aks_costs_by_env[env_name] = 0

print("\n" + "=" * 80)
print("SUMMARY - AKS COSTS BY ENVIRONMENT")
print("=" * 80)

for env_name, cost in aks_costs_by_env.items():
    print(f"{env_name:15} : ${cost:>12,.2f}/month")

print(f"\n{'Total AKS':15} : ${total_aks_cost:>12,.2f}/month")
print(f"{'Annual':15} : ${total_aks_cost * 12:>12,.2f}/year")

print("\n" + "=" * 80)
