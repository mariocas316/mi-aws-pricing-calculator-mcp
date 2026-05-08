#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compare AKS data from Azure Resource Inventory vs Cost Management
"""

import pandas as pd
from pathlib import Path

print("=" * 120)
print("COMPARACION: INVENTARIO ARI vs COST MANAGEMENT")
print("=" * 120)

# Read AKS data from Azure Resource Inventory
inventory_file = 'inventarioari/AzureResourceInventory_Report_2026-04-16_16_43.xlsx'

print("\n1. LEYENDO INVENTARIO DE RECURSOS AZURE (ARI)")
print("-" * 120)

try:
    aks_inv = pd.read_excel(inventory_file, sheet_name='AKS')
    print(f"\nAKS sheet columns: {list(aks_inv.columns)}\n")
    print(f"Total rows in AKS sheet: {len(aks_inv)}")
    print("\nFirst few rows:")
    print(aks_inv.head(10))
    
except Exception as e:
    print(f"Error reading AKS sheet: {e}")
    aks_inv = None

# Also read Virtual Machine Scale Sets
print("\n\n2. VIRTUAL MACHINE SCALE SETS (VMSS) - AKS Worker Nodes")
print("-" * 120)

try:
    vmss_inv = pd.read_excel(inventory_file, sheet_name='Virtual Machine Scale Sets')
    print(f"\nVMSS sheet columns: {list(vmss_inv.columns)}\n")
    print(f"Total rows in VMSS sheet: {len(vmss_inv)}")
    
    # Filter for AKS-related VMSS
    if 'Name' in vmss_inv.columns:
        aks_vmss = vmss_inv[vmss_inv['Name'].str.contains('aks-', case=False, na=False)]
        print(f"\nAKS-related VMSS: {len(aks_vmss)}")
        
        if len(aks_vmss) > 0:
            print("\nAKS VMSS Details:")
            for idx, row in aks_vmss.iterrows():
                name = row.get('Name', 'N/A')
                location = row.get('Location', 'N/A')
                rg = row.get('Resource Group', row.get('ResourceGroup', 'N/A'))
                print(f"  - {name} (RG: {rg}, Location: {location})")
            
            print("\nFull VMSS data:")
            print(aks_vmss[['Name', 'Location', 'Resource Group'] if 'Resource Group' in aks_vmss.columns else ['Name', 'Location']].to_string())
    
except Exception as e:
    print(f"Error reading VMSS sheet: {e}")
    vmss_inv = None

# Read Registries (Container Registry)
print("\n\n3. CONTAINER REGISTRIES")
print("-" * 120)

try:
    registries = pd.read_excel(inventory_file, sheet_name='Registries')
    print(f"Total registries: {len(registries)}")
    
    if 'Name' in registries.columns:
        print("\nRegistry names:")
        for name in registries['Name'].unique():
            print(f"  - {name}")
    
except Exception as e:
    print(f"Error reading Registries: {e}")

print("\n" + "=" * 120)
print("SUMMARY - COMPARACION ARI vs COST MANAGEMENT")
print("=" * 120)

print(f"\nINVENTARIO ARI (Azure Resource Inventory):")

if aks_inv is not None:
    print(f"  AKS clusters sheet: {len(aks_inv)} registros")

if vmss_inv is not None:
    aks_vmss_count = len(aks_vmss) if 'aks_vmss' in locals() else 0
    print(f"  VMSS (AKS worker nodes) sheet: {aks_vmss_count} registros")

print(f"\nCOST MANAGEMENT (Análisis anterior):")
print(f"  Nodos encontrados: 99")
print(f"  Costo total: $48,147.28/mes")
print(f"    - Workers: $37,260.06/mes")
print(f"    - Container Services: $10,887.22/mes")

print(f"\n" + "=" * 120)
