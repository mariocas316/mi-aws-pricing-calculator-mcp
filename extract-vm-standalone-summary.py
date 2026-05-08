#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

INV_PATH = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
TCO_PATH = Path("archivostcoonnet/TCO_Migracion_Azure_AWS_OnNet_v2.xlsx")


def to_num(v, default=0.0):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default


def extract_vm_name_from_disk(disk_name: str) -> str:
    if not isinstance(disk_name, str) or not disk_name:
        return ""
    markers = ["_OsDisk_", "_disk", "-osdisk", "-datadisk"]
    lower = disk_name.lower()
    for m in markers:
        idx = lower.find(m.lower())
        if idx > 0:
            return disk_name[:idx]
    # Fallback: many names are vmName_<suffix>
    if "_" in disk_name:
        return disk_name.split("_")[0]
    return ""


def main():
    vm_df = pd.read_excel(INV_PATH, sheet_name="Virtual Machines", dtype=object)
    disk_df = pd.read_excel(INV_PATH, sheet_name="Disks", dtype=object)
    tco_df = pd.read_excel(TCO_PATH, sheet_name="1. Resumen Ejecutivo TCO", dtype=object)

    # Base VM inventory (standalone = excluding AKS worker nodes by RG naming)
    vm = vm_df.copy()
    vm = vm[vm["VM Name"].notna()].copy()
    vm = vm[~vm["Resource Group"].astype(str).str.contains("aks", case=False, na=False)].copy()

    vm["vcpus"] = vm["vCPUs"].apply(to_num)
    vm["memory_gib"] = vm["RAM (GiB)"].apply(to_num)
    vm["os_disk_gb"] = vm["OS Disk Size (GB)"].apply(to_num)
    vm["data_disk_gb"] = vm["Data Disk Size (GB)"].apply(to_num)
    vm["disk_total_gb_vm_sheet"] = vm["os_disk_gb"] + vm["data_disk_gb"]

    # Disk enrichment from Disks sheet
    disks = disk_df.copy()
    disks = disks[disks["Disk Name"].notna()].copy()
    disks["vm_name_guess"] = disks["Disk Name"].astype(str).apply(extract_vm_name_from_disk).str.lower()
    disks["disk_size_gb"] = disks["Disk Size"].apply(to_num)
    disks_attached = disks[disks["Disk State"].astype(str).str.lower() == "attached"].copy()

    disk_sum = disks_attached.groupby("vm_name_guess", dropna=False)["disk_size_gb"].sum().to_dict()

    vm["vm_name_lc"] = vm["VM Name"].astype(str).str.lower()
    vm["disk_total_gb_disks_sheet"] = vm["vm_name_lc"].map(disk_sum).fillna(0.0)
    vm["disk_total_gb"] = vm.apply(
        lambda r: r["disk_total_gb_disks_sheet"] if r["disk_total_gb_disks_sheet"] > 0 else r["disk_total_gb_vm_sheet"],
        axis=1,
    )

    # Complementary services indicators
    vm["has_public_ip"] = vm["Public IP"].notna() & (vm["Public IP"].astype(str).str.strip() != "")
    vm["has_nsg"] = vm["NSG"].notna() & (vm["NSG"].astype(str).str.strip() != "")
    vm["has_backup_or_monitoring"] = vm["Azure Monitor"].astype(str).str.lower().isin(["true", "enabled", "yes", "1"]) | vm["Performance Agent"].astype(str).str.lower().isin(["true", "enabled", "yes", "1"])

    # Summary by VM size
    grp = vm.groupby(["VM Size", "OS Type", "vcpus", "memory_gib"], dropna=False).agg(
        quantity=("VM Name", "count"),
        disk_total_gb=("disk_total_gb", "sum"),
        disk_avg_gb=("disk_total_gb", "mean"),
    ).reset_index().sort_values(["quantity", "VM Size"], ascending=[False, True])

    # TCO row lookup
    tco_match = tco_df[tco_df.iloc[:, 0].astype(str).str.contains("VMs Standalone", case=False, na=False)]
    tco_row = None
    if not tco_match.empty:
        r = tco_match.iloc[0]
        tco_row = {
            "service": str(r.iloc[0]),
            "aws_service": str(r.iloc[1]) if len(r) > 1 else None,
            "strategy": str(r.iloc[2]) if len(r) > 2 else None,
            "azure_monthly": float(r.iloc[3]) if len(r) > 3 and pd.notna(r.iloc[3]) else None,
            "azure_annual": float(r.iloc[4]) if len(r) > 4 and pd.notna(r.iloc[4]) else None,
            "aws_ondemand_monthly": float(r.iloc[5]) if len(r) > 5 and pd.notna(r.iloc[5]) else None,
            "aws_sp1yr_monthly": float(r.iloc[6]) if len(r) > 6 and pd.notna(r.iloc[6]) else None,
            "aws_sp3yr_monthly": float(r.iloc[7]) if len(r) > 7 and pd.notna(r.iloc[7]) else None,
        }

    output = {
        "vm_standalone_count": int(len(vm)),
        "complementary_services": {
            "vnet_count": int(vm["Virtual Network"].nunique(dropna=True)),
            "subnet_count": int(vm["Subnet"].nunique(dropna=True)),
            "nsg_attached_count": int(vm["has_nsg"].sum()),
            "public_ip_count": int(vm["has_public_ip"].sum()),
            "nic_count": int(vm["NIC Name"].nunique(dropna=True)),
            "boot_diagnostics_enabled": int(vm["Boot Diagnostics"].astype(str).str.lower().isin(["true", "enabled", "yes", "1"]).sum()),
            "azure_monitor_enabled": int(vm["Azure Monitor"].astype(str).str.lower().isin(["true", "enabled", "yes", "1"]).sum()),
            "availability_set_count": int(vm["Availability Set"].nunique(dropna=True)),
        },
        "vm_summary_by_size": grp.to_dict(orient="records"),
        "totals": {
            "total_vcpus": float(vm["vcpus"].sum()),
            "total_memory_gib": float(vm["memory_gib"].sum()),
            "total_disk_gb": float(vm["disk_total_gb"].sum()),
        },
        "tco_vm_standalone_row": tco_row,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
