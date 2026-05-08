#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

INV_PATH = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
TCO_PATH = Path("archivostcoonnet/TCO_Migracion_Azure_AWS_OnNet_v2.xlsx")


def safe_float(v):
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def normalize_family(size_name):
    if not isinstance(size_name, str) or not size_name:
        return "unknown"
    # Example: Standard_D4s_v5 -> Dsv5
    s = size_name.replace("Standard_", "")
    base = s.split("_")[0]
    parts = base.split("v")
    if len(parts) == 2 and parts[0]:
        return f"{parts[0]}v{parts[1]}"
    return base


def parse_disks(vm_df):
    disk_cols = [c for c in vm_df.columns if "disk" in str(c).lower()]
    result = []
    for _, row in vm_df.iterrows():
        vm_name = row.get("Name")
        if pd.isna(vm_name):
            continue
        total_disk_gb = 0.0
        disk_details = {}
        for col in disk_cols:
            val = row.get(col)
            if pd.isna(val):
                continue
            sval = str(val)
            # Extract simple numeric sizes that look like GB values in text
            nums = []
            token = ""
            for ch in sval:
                if ch.isdigit() or ch == '.':
                    token += ch
                else:
                    if token:
                        nums.append(token)
                        token = ""
            if token:
                nums.append(token)
            # Heuristic: keep first numeric values <= 65536 as GB candidates
            gb_vals = []
            for n in nums:
                try:
                    f = float(n)
                    if 1 <= f <= 65536:
                        gb_vals.append(f)
                except Exception:
                    pass
            if gb_vals:
                disk_details[col] = gb_vals
                total_disk_gb += sum(gb_vals)
        result.append({
            "Name": str(vm_name),
            "disk_total_gb_est": round(total_disk_gb, 2),
            "disk_raw": disk_details,
        })
    return result


def main():
    vm_df = pd.read_excel(INV_PATH, sheet_name="Virtual Machines", dtype=object)
    disk_df = pd.read_excel(INV_PATH, sheet_name="Disks", dtype=object)
    tco_df = pd.read_excel(TCO_PATH, sheet_name="1. Resumen Ejecutivo TCO", dtype=object)

    vm_cols = list(vm_df.columns)
    disk_cols = list(disk_df.columns)

    # Locate key columns with robust matching
    name_col = next((c for c in vm_cols if str(c).strip().lower() == "name"), None)
    size_col = next((c for c in vm_cols if "size" in str(c).lower()), None)
    vcpu_col = next((c for c in vm_cols if "vcpu" in str(c).lower() or "cpu" in str(c).lower()), None)
    mem_col = next((c for c in vm_cols if "memory" in str(c).lower() or "ram" in str(c).lower()), None)
    rg_col = next((c for c in vm_cols if "resource group" in str(c).lower()), None)
    sub_col = next((c for c in vm_cols if str(c).strip().lower() == "subscription"), None)
    os_col = next((c for c in vm_cols if "os" in str(c).lower()), None)

    vm_core = vm_df.copy()
    if name_col:
        vm_core = vm_core[vm_core[name_col].notna()].copy()

    # Exclude AKS nodes (standalone scope only)
    if rg_col:
        vm_core = vm_core[~vm_core[rg_col].astype(str).str.contains("aks", case=False, na=False)]

    vm_core["family"] = vm_core[size_col].astype(str).apply(normalize_family) if size_col else "unknown"

    # Build disk map from Disks sheet (attached VM name typically appears in Managed By/VM Name columns)
    disk_name_col = next((c for c in disk_cols if str(c).strip().lower() == "name"), None)
    disk_size_col = next((c for c in disk_cols if "size" in str(c).lower() and "gb" in str(c).lower()), None)
    managed_by_col = next((c for c in disk_cols if "managed by" in str(c).lower() or "vm" in str(c).lower()), None)

    disk_by_vm = {}
    if managed_by_col and disk_size_col:
        for _, row in disk_df.iterrows():
            managed = row.get(managed_by_col)
            size = safe_float(row.get(disk_size_col))
            if pd.isna(managed) or size is None:
                continue
            managed_str = str(managed)
            vm_name = managed_str.split("/")[-1]
            if not vm_name:
                continue
            disk_by_vm.setdefault(vm_name.lower(), 0.0)
            disk_by_vm[vm_name.lower()] += size

    # Fallback parsing from VM row if disk sheet mapping is incomplete
    fallback_disks = parse_disks(vm_core)
    fallback_map = {d["Name"].lower(): d["disk_total_gb_est"] for d in fallback_disks if d["disk_total_gb_est"] > 0}

    rows = []
    for _, row in vm_core.iterrows():
        name = str(row.get(name_col)) if name_col else "unknown"
        size = str(row.get(size_col)) if size_col else "unknown"
        vcpu = safe_float(row.get(vcpu_col)) if vcpu_col else None
        mem = safe_float(row.get(mem_col)) if mem_col else None
        sub = str(row.get(sub_col)) if sub_col else ""
        rg = str(row.get(rg_col)) if rg_col else ""
        os_name = str(row.get(os_col)) if os_col else ""

        d1 = disk_by_vm.get(name.lower(), 0.0)
        d2 = fallback_map.get(name.lower(), 0.0)
        disk_gb = d1 if d1 > 0 else d2

        rows.append({
            "name": name,
            "subscription": sub,
            "resource_group": rg,
            "azure_size": size,
            "family": normalize_family(size),
            "vcpu": vcpu,
            "memory_gib": mem,
            "disk_gb_total": round(disk_gb, 2),
            "os": os_name,
        })

    vm_detail = pd.DataFrame(rows)
    vm_detail = vm_detail[vm_detail["name"].notna()]

    # Group summary by size for calculator building
    grp = vm_detail.groupby(["azure_size", "family", "vcpu", "memory_gib"], dropna=False).agg(
        quantity=("name", "count"),
        disk_gb_total=("disk_gb_total", "sum"),
        disk_gb_avg=("disk_gb_total", "mean"),
    ).reset_index().sort_values("quantity", ascending=False)

    # Read TCO row for standalone VMs
    tco_row = None
    for _, r in tco_df.iterrows():
        col_a = str(r.iloc[0]) if not pd.isna(r.iloc[0]) else ""
        if "VMs Standalone" in col_a:
            tco_row = {
                "service": col_a,
                "azure_monthly": r.iloc[3] if len(r) > 3 else None,
                "aws_ondemand_monthly": r.iloc[5] if len(r) > 5 else None,
                "aws_sp1yr_monthly": r.iloc[6] if len(r) > 6 else None,
                "aws_sp3yr_monthly": r.iloc[7] if len(r) > 7 else None,
            }
            break

    out = {
        "vm_sheet_columns": vm_cols,
        "disk_sheet_columns": disk_cols,
        "vm_total_standalone": int(len(vm_detail)),
        "vm_summary_by_size": grp.to_dict(orient="records"),
        "vm_detail": vm_detail.to_dict(orient="records"),
        "tco_vm_row": tco_row,
    }

    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
