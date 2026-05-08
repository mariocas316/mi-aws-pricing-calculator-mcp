#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

inv = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
vm = pd.read_excel(inv, sheet_name="Virtual Machines", dtype=object)
dk = pd.read_excel(inv, sheet_name="Disks", dtype=object)

print("VM columns:")
for i, c in enumerate(vm.columns):
    print(f"{i:03d}: {c}")

print("\nVM sample rows (first 5, selected columns):")
sel = [c for c in vm.columns if any(k in str(c).lower() for k in ["name", "resource group", "subscription", "size", "vcpu", "cpu", "memory", "ram", "os", "disk"]) ]
print(vm[sel].head(8).to_string(index=False))

print("\nDisks columns:")
for i, c in enumerate(dk.columns):
    print(f"{i:03d}: {c}")

print("\nDisks sample rows (first 8, selected columns):")
sel_d = [c for c in dk.columns if any(k in str(c).lower() for k in ["name", "resource group", "subscription", "size", "gb", "managed", "vm", "disk", "sku"]) ]
print(dk[sel_d].head(8).to_string(index=False))
