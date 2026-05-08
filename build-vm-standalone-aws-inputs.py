#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

INV_PATH = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
TCO_PATH = Path("archivostcoonnet/TCO_Migracion_Azure_AWS_OnNet_v2.xlsx")
OUT_SUMMARY = Path("vm-standalone-summary.json")
OUT_AWS_INPUT = Path("vm-standalone-aws-input.json")

# Minimal candidate catalog for homologation by vCPU/memory
AWS_CANDIDATES = [
    {"type": "t3.medium", "vcpu": 2, "mem": 4},
    {"type": "t3.large", "vcpu": 2, "mem": 8},
    {"type": "r6i.large", "vcpu": 2, "mem": 16},
    {"type": "m6i.xlarge", "vcpu": 4, "mem": 16},
    {"type": "r6i.xlarge", "vcpu": 4, "mem": 32},
    {"type": "c6i.2xlarge", "vcpu": 8, "mem": 16},
    {"type": "m6i.2xlarge", "vcpu": 8, "mem": 32},
    {"type": "m6i.4xlarge", "vcpu": 16, "mem": 64},
    {"type": "c6i.8xlarge", "vcpu": 32, "mem": 64},
    {"type": "m6i.8xlarge", "vcpu": 32, "mem": 128},
    # GPU-ish fallback for NV8as_v4 (closest practical in EC2)
    {"type": "g4dn.2xlarge", "vcpu": 8, "mem": 32},
]


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
    if "_" in disk_name:
        return disk_name.split("_")[0]
    return ""


def pick_aws_instance(vcpu, mem, vm_size):
    # First exact vCPU+mem match
    exact = [c for c in AWS_CANDIDATES if c["vcpu"] == int(vcpu) and c["mem"] == int(mem)]
    if exact:
        # Prefer non-GPU unless Azure size is NV
        if "NV" in str(vm_size):
            gpu = [e for e in exact if e["type"].startswith("g")]
            return gpu[0] if gpu else exact[0], True
        non_gpu = [e for e in exact if not e["type"].startswith("g")]
        return (non_gpu[0] if non_gpu else exact[0]), True

    # Then same vCPU, nearest memory
    same_cpu = [c for c in AWS_CANDIDATES if c["vcpu"] == int(vcpu)]
    if same_cpu:
        best = sorted(same_cpu, key=lambda c: abs(c["mem"] - mem))[0]
        return best, False

    # Last resort by nearest vCPU+mem weighted
    best = sorted(AWS_CANDIDATES, key=lambda c: abs(c["vcpu"] - vcpu) * 10 + abs(c["mem"] - mem))[0]
    return best, False


def os_to_aws(os_type):
    return "windows" if str(os_type).strip().lower() == "windows" else "linux"


def main():
    vm_df = pd.read_excel(INV_PATH, sheet_name="Virtual Machines", dtype=object)
    disk_df = pd.read_excel(INV_PATH, sheet_name="Disks", dtype=object)
    tco_df = pd.read_excel(TCO_PATH, sheet_name="1. Resumen Ejecutivo TCO", dtype=object)

    vm = vm_df[vm_df["VM Name"].notna()].copy()  # keep all 112 as per TCO row
    vm["vcpus"] = vm["vCPUs"].apply(to_num)
    vm["memory_gib"] = vm["RAM (GiB)"].apply(to_num)
    vm["os_disk_gb"] = vm["OS Disk Size (GB)"].apply(to_num)
    vm["data_disk_gb"] = vm["Data Disk Size (GB)"].apply(to_num)
    vm["disk_total_gb_vm_sheet"] = vm["os_disk_gb"] + vm["data_disk_gb"]

    disks = disk_df[disk_df["Disk Name"].notna()].copy()
    disks["vm_name_guess"] = disks["Disk Name"].astype(str).apply(extract_vm_name_from_disk).str.lower()
    disks["disk_size_gb"] = disks["Disk Size"].apply(to_num)
    disks = disks[disks["Disk State"].astype(str).str.lower() == "attached"]
    disk_sum = disks.groupby("vm_name_guess")["disk_size_gb"].sum().to_dict()

    vm["vm_name_lc"] = vm["VM Name"].astype(str).str.lower()
    vm["disk_total_gb_disks_sheet"] = vm["vm_name_lc"].map(disk_sum).fillna(0.0)
    vm["disk_total_gb"] = vm.apply(
        lambda r: r["disk_total_gb_disks_sheet"] if r["disk_total_gb_disks_sheet"] > 0 else r["disk_total_gb_vm_sheet"],
        axis=1,
    )

    vm["has_public_ip"] = vm["Public IP"].notna() & (vm["Public IP"].astype(str).str.strip() != "")
    vm["has_nsg"] = vm["NSG"].notna() & (vm["NSG"].astype(str).str.strip() != "")

    # Summary by Azure size+OS+shape
    summary = vm.groupby(["VM Size", "OS Type", "vcpus", "memory_gib"], dropna=False).agg(
        quantity=("VM Name", "count"),
        disk_total_gb=("disk_total_gb", "sum"),
        disk_avg_gb=("disk_total_gb", "mean"),
    ).reset_index().sort_values(["quantity", "VM Size"], ascending=[False, True])

    mapped_rows = []
    for _, r in summary.iterrows():
        vcpu = int(r["vcpus"])
        mem = int(r["memory_gib"])
        aws, is_exact = pick_aws_instance(vcpu, mem, r["VM Size"])
        avg_disk = max(30, int(round(float(r["disk_avg_gb"]))))
        mapped_rows.append({
            "azure_size": r["VM Size"],
            "os_type": r["OS Type"],
            "vcpu": vcpu,
            "memory_gib": mem,
            "quantity": int(r["quantity"]),
            "disk_avg_gb": avg_disk,
            "aws_instance_type": aws["type"],
            "aws_exact_cpu_mem_match": bool(is_exact),
            "aws_selected_os": os_to_aws(r["OS Type"]),
        })

    mapped_df = pd.DataFrame(mapped_rows)

    # Consolidate by aws target + OS + disk
    aws_groups = mapped_df.groupby(["aws_instance_type", "aws_selected_os", "disk_avg_gb"], dropna=False).agg(
        quantity=("quantity", "sum"),
        source_rows=("azure_size", "count"),
        exact_matches=("aws_exact_cpu_mem_match", "sum"),
    ).reset_index().sort_values("quantity", ascending=False)

    tco_match = tco_df[tco_df.iloc[:, 0].astype(str).str.contains("VMs Standalone", case=False, na=False)]
    tco_row = None
    if not tco_match.empty:
        rr = tco_match.iloc[0]
        tco_row = {
            "service": str(rr.iloc[0]),
            "aws_ondemand_monthly": float(rr.iloc[5]) if pd.notna(rr.iloc[5]) else None,
            "aws_sp1yr_monthly": float(rr.iloc[6]) if pd.notna(rr.iloc[6]) else None,
            "aws_sp3yr_monthly": float(rr.iloc[7]) if pd.notna(rr.iloc[7]) else None,
        }

    summary_out = {
        "vm_standalone_count": int(vm.shape[0]),
        "totals": {
            "total_vcpu": int(vm["vcpus"].sum()),
            "total_memory_gib": int(vm["memory_gib"].sum()),
            "total_disk_gb": int(vm["disk_total_gb"].sum()),
        },
        "complementary_services": {
            "nics": int(vm["NIC Name"].nunique(dropna=True)),
            "vnets": int(vm["Virtual Network"].nunique(dropna=True)),
            "subnets": int(vm["Subnet"].nunique(dropna=True)),
            "nsg_attached": int(vm["has_nsg"].sum()),
            "public_ips": int(vm["has_public_ip"].sum()),
            "boot_diagnostics_enabled": int(vm["Boot Diagnostics"].astype(str).str.lower().isin(["true", "enabled", "yes", "1"]).sum()),
            "azure_monitor_enabled": int(vm["Azure Monitor"].astype(str).str.lower().isin(["true", "enabled", "yes", "1"]).sum()),
        },
        "by_azure_size": mapped_rows,
        "tco_reference": tco_row,
    }

    aws_input = {
        "region": "us-east-2",
        "estimate_name": "VMs Standalone Azure->AWS On-Demand",
        "target_monthly_from_tco": tco_row["aws_ondemand_monthly"] if tco_row else None,
        "ec2_groups": aws_groups.to_dict(orient="records"),
    }

    OUT_SUMMARY.write_text(json.dumps(summary_out, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_AWS_INPUT.write_text(json.dumps(aws_input, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "summary_file": str(OUT_SUMMARY),
        "aws_input_file": str(OUT_AWS_INPUT),
        "vm_standalone_count": summary_out["vm_standalone_count"],
        "target_ondemand_tco": aws_input["target_monthly_from_tco"],
        "aws_group_count": int(aws_groups.shape[0]),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
