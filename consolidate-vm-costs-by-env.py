#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

INV_PATH = Path("inventarioAri/AzureResourceInventory_Report_2026-04-16_16_43.xlsx")
COST_DIR = Path("archivostcoonnet/CostManagement")
TCO_PATH = Path("archivostcoonnet/TCO_Migracion_Azure_AWS_OnNet_v2.xlsx")


def env_from_filename(name: str) -> str:
    n = name.lower()
    if "onnet-dev" in n:
        return "Onnet-Dev"
    if "onnet-qa" in n:
        return "Onnet-QA"
    if "onnet-prod" in n:
        return "Onnet-Prod"
    if "onnet-centralhub" in n:
        return "Onnet-CentralHub"
    return "Unknown"


def extract_vm_name_from_resource_id(resource_id: str) -> str:
    if not isinstance(resource_id, str):
        return ""
    m = re.search(r"/providers/microsoft\.compute/virtualmachines/([^/]+)", resource_id, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def main():
    vm_df = pd.read_excel(INV_PATH, sheet_name="Virtual Machines", dtype=object)
    tco_df = pd.read_excel(TCO_PATH, sheet_name="1. Resumen Ejecutivo TCO", dtype=object)

    # Inventario VM standalone (excluye AKS por Resource Group)
    vm = vm_df[vm_df["VM Name"].notna()].copy()
    vm = vm[~vm["Resource Group"].astype(str).str.contains("aks", case=False, na=False)].copy()

    vm["Environment"] = vm["Subscription"].astype(str)
    vm["vm_name_lc"] = vm["VM Name"].astype(str).str.lower()

    inv_by_env = vm.groupby("Environment", dropna=False).agg(
        inventory_vm_count=("VM Name", "count"),
        inventory_total_vcpu=("vCPUs", "sum"),
        inventory_total_ram_gib=("RAM (GiB)", "sum"),
    ).reset_index()

    vm_names_by_env = {
        env: set(g["vm_name_lc"].tolist())
        for env, g in vm.groupby("Environment", dropna=False)
    }

    rows = []
    details = {}

    cost_files = sorted(COST_DIR.glob("CostManagement_*.xlsx"))
    for fp in cost_files:
        env = env_from_filename(fp.name)
        if env == "Unknown":
            continue

        df = pd.read_excel(fp, sheet_name="Data", dtype=object)
        df["ResourceType_lc"] = df["ResourceType"].astype(str).str.lower()
        df["ResourceId_str"] = df["ResourceId"].astype(str)
        df["vm_name"] = df["ResourceId_str"].apply(extract_vm_name_from_resource_id)
        df["vm_name_lc"] = df["vm_name"].str.lower()
        df["CostUSD_num"] = pd.to_numeric(df["CostUSD"], errors="coerce").fillna(0.0)

        # Costo estricto de VMs (compute virtualmachines)
        vm_cost_rows = df[
            (df["ResourceType_lc"] == "microsoft.compute/virtualmachines")
            & (df["vm_name_lc"] != "")
        ].copy()

        inv_names = vm_names_by_env.get(env, set())
        vm_cost_rows = vm_cost_rows[vm_cost_rows["vm_name_lc"].isin(inv_names)]

        # Excluir accidentalmente AKS por nombre/rg en costos (defensivo)
        vm_cost_rows = vm_cost_rows[
            ~vm_cost_rows["ResourceGroupName"].astype(str).str.contains("aks", case=False, na=False)
        ]

        total_cost = float(vm_cost_rows["CostUSD_num"].sum())
        billed_vm_names = sorted(set(vm_cost_rows["vm_name_lc"].tolist()))
        billed_count = len(billed_vm_names)

        inv_count = int(inv_by_env[inv_by_env["Environment"] == env]["inventory_vm_count"].sum())
        missing = sorted(inv_names - set(billed_vm_names))

        rows.append({
            "environment": env,
            "inventory_vm_count": inv_count,
            "billed_vm_count": billed_count,
            "vm_compute_cost_usd": round(total_cost, 2),
            "missing_vm_count_in_cost": len(missing),
            "coverage_pct": round((billed_count / inv_count * 100.0), 2) if inv_count else 0.0,
        })

        details[env] = {
            "sample_missing_vms": missing[:25],
            "sample_billed_vms": billed_vm_names[:25],
        }

    summary_df = pd.DataFrame(rows).sort_values("environment")

    total_inventory = int(summary_df["inventory_vm_count"].sum()) if not summary_df.empty else 0
    total_billed = int(summary_df["billed_vm_count"].sum()) if not summary_df.empty else 0
    total_cost = float(summary_df["vm_compute_cost_usd"].sum()) if not summary_df.empty else 0.0

    # Referencia TCO (Azure mensual para VMs Standalone)
    tco_match = tco_df[tco_df.iloc[:, 0].astype(str).str.contains("VMs Standalone", case=False, na=False)]
    tco_azure_monthly = None
    if not tco_match.empty and pd.notna(tco_match.iloc[0].iloc[3]):
        tco_azure_monthly = float(tco_match.iloc[0].iloc[3])

    out = {
        "scope": "Azure VMs standalone only (microsoft.compute/virtualmachines), excluding AKS RG",
        "by_environment": summary_df.to_dict(orient="records"),
        "totals": {
            "inventory_vm_count": total_inventory,
            "billed_vm_count": total_billed,
            "vm_compute_cost_usd": round(total_cost, 2),
            "coverage_pct": round((total_billed / total_inventory * 100.0), 2) if total_inventory else 0.0,
            "tco_azure_monthly_reference": tco_azure_monthly,
        },
        "details": details,
    }

    Path("vm-costs-by-env.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
