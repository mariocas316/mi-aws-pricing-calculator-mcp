#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

INV_PATH = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
OUT_PATH = Path("vm-standalone-per-vm-aws-input.json")

AWS_CANDIDATES_X86 = [
    {"type": "t3a.medium", "vcpu": 2, "mem": 4},
    {"type": "t3a.large", "vcpu": 2, "mem": 8},
    {"type": "t3a.xlarge", "vcpu": 4, "mem": 16},
    {"type": "t3a.2xlarge", "vcpu": 8, "mem": 32},
    {"type": "t3.medium", "vcpu": 2, "mem": 4},
    {"type": "t3.large", "vcpu": 2, "mem": 8},
    {"type": "t3.xlarge", "vcpu": 4, "mem": 16},
    {"type": "t3.2xlarge", "vcpu": 8, "mem": 32},
    {"type": "r5a.large", "vcpu": 2, "mem": 16},
    {"type": "m5a.xlarge", "vcpu": 4, "mem": 16},
    {"type": "r5a.xlarge", "vcpu": 4, "mem": 32},
    {"type": "c5a.2xlarge", "vcpu": 8, "mem": 16},
    {"type": "m5a.2xlarge", "vcpu": 8, "mem": 32},
    {"type": "m5a.4xlarge", "vcpu": 16, "mem": 64},
    {"type": "c5a.8xlarge", "vcpu": 32, "mem": 64},
    {"type": "m5a.8xlarge", "vcpu": 32, "mem": 128},
]

AWS_CANDIDATES_ARM = [
    {"type": "t4g.medium", "vcpu": 2, "mem": 4},
    {"type": "t4g.large", "vcpu": 2, "mem": 8},
    {"type": "t4g.xlarge", "vcpu": 4, "mem": 16},
    {"type": "t4g.2xlarge", "vcpu": 8, "mem": 32},
    {"type": "r6g.large", "vcpu": 2, "mem": 16},
    {"type": "m6g.xlarge", "vcpu": 4, "mem": 16},
    {"type": "r6g.xlarge", "vcpu": 4, "mem": 32},
    {"type": "c6g.2xlarge", "vcpu": 8, "mem": 16},
    {"type": "m6g.2xlarge", "vcpu": 8, "mem": 32},
    {"type": "m6g.4xlarge", "vcpu": 16, "mem": 64},
    {"type": "c6g.8xlarge", "vcpu": 32, "mem": 64},
    {"type": "m6g.8xlarge", "vcpu": 32, "mem": 128},
]


def to_num(v, default=0.0):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default


def pick_aws_instance(vcpu, mem, vm_size, os_type):
    candidates = AWS_CANDIDATES_ARM if str(os_type).strip().lower() == "linux" else AWS_CANDIDATES_X86
    exact = [c for c in candidates if c["vcpu"] == int(vcpu) and c["mem"] == int(mem)]
    if exact:
        non_gpu = [e for e in exact if not e["type"].startswith("g")]
        return (non_gpu[0] if non_gpu else exact[0]), True

    same_cpu = [c for c in candidates if c["vcpu"] == int(vcpu)]
    if same_cpu:
        best = sorted(same_cpu, key=lambda c: abs(c["mem"] - mem))[0]
        return best, False

    best = sorted(candidates, key=lambda c: abs(c["vcpu"] - vcpu) * 10 + abs(c["mem"] - mem))[0]
    return best, False


def pick_storage_type(disk_gb):
    # Use cheapest HDD tiers aggressively to reduce monthly storage cost.
    if disk_gb >= 50:
        return "Storage Cold HDD sc1 GB Mo"
    if disk_gb >= 30:
        return "Storage Throughput Optimized HDD st1 GB Mo"
    return "Storage General Purpose gp3 GB Mo"


def env_from_subscription(sub: str) -> str:
    s = str(sub).lower()
    if "dev" in s:
        return "Development"
    if "qa" in s:
        return "QA"
    if "prod" in s:
        return "Production"
    if "centralhub" in s:
        return "CentralHub"
    return "Other"


def utilization_by_environment(environment: str) -> int:
    # Dev/QA aggressive schedule with additional off windows.
    if environment in {"Development", "QA"}:
        return 45
    # CentralHub must run 24x7.
    if environment == "CentralHub":
        return 100
    # Production and shared platforms run conservatively 24x7.
    return 100


def main():
    vm_df = pd.read_excel(INV_PATH, sheet_name="Virtual Machines", dtype=object)

    vm = vm_df[vm_df["VM Name"].notna()].copy()
    vm = vm[~vm["Resource Group"].astype(str).str.contains("aks", case=False, na=False)].copy()

    vm["vcpus"] = vm["vCPUs"].apply(to_num)
    vm["memory_gib"] = vm["RAM (GiB)"].apply(to_num)
    vm["os_disk_gb"] = vm["OS Disk Size (GB)"].apply(to_num)
    vm["data_disk_gb"] = vm["Data Disk Size (GB)"].apply(to_num)
    vm["disk_total_gb_vm_sheet"] = vm["os_disk_gb"] + vm["data_disk_gb"]
    # Use VM sheet OS+Data disk sizes only to avoid inflating EC2 storage with backup/snapshot artifacts.
    vm["disk_total_gb"] = vm["disk_total_gb_vm_sheet"]

    ec2_entries = []
    for _, r in vm.iterrows():
        vcpu = int(to_num(r.get("vcpus"), 2))
        mem = int(to_num(r.get("memory_gib"), 4))
        aws, exact = pick_aws_instance(vcpu, mem, r.get("VM Size"), r.get("OS Type"))
        disk_gb = max(30, int(round(to_num(r.get("disk_total_gb"), 64))))
        storage_type = pick_storage_type(disk_gb)

        environment = env_from_subscription(str(r.get("Subscription")))
        utilization_pct = utilization_by_environment(environment)

        ec2_entries.append({
            "machine_id": str(r.get("VM Name")),
            "subscription": str(r.get("Subscription")),
            "environment": environment,
            "resource_group": str(r.get("Resource Group")),
            "azure_size": str(r.get("VM Size")),
            "azure_vcpu": vcpu,
            "azure_memory_gib": mem,
            "azure_disk_gb": disk_gb,
            "aws_instance_type": aws["type"],
            "aws_selected_os": "windows" if str(r.get("OS Type")).strip().lower() == "windows" else "linux",
            "aws_storage_type": storage_type,
            "aws_utilization_pct": utilization_pct,
            "aws_exact_cpu_mem_match": bool(exact),
        })

    out = {
        "region": "us-east-1",
        "estimate_name": "VM Standalone OnDemand env schedule v8",
        "vm_count": len(ec2_entries),
        "ec2_entries": ec2_entries,
    }

    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "file": str(OUT_PATH),
        "vm_count": len(ec2_entries),
        "exact_matches": sum(1 for x in ec2_entries if x["aws_exact_cpu_mem_match"]),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
