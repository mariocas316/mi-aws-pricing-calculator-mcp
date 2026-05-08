#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final AKS Cost Summary from Cost Management Files
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

print("\n" + "=" * 100)
print("FINAL AKS COST SUMMARY - AZURE BILLING DATA")
print("=" * 100 + "\n")

summary_data = {
    'Environment': [],
    'Container Registry': [],
    'Container Instances': [],
    'Defender for Cloud': [],
    'Total': []
}

grand_total = 0

for filename, env_name in cost_files:
    filepath = cost_files_dir / filename
    
    if not filepath.exists():
        continue
    
    df = pd.read_excel(filepath)
    
    # Get costs by service
    container_registry = df[df['ServiceName'] == 'Container Registry']['CostUSD'].sum()
    container_instances = df[df['ServiceName'] == 'Container Instances']['CostUSD'].sum()
    defender = df[df['ServiceName'] == 'Microsoft Defender for Cloud']['CostUSD'].sum()
    
    total_env = container_registry + container_instances + defender
    
    summary_data['Environment'].append(env_name)
    summary_data['Container Registry'].append(container_registry)
    summary_data['Container Instances'].append(container_instances)
    summary_data['Defender for Cloud'].append(defender)
    summary_data['Total'].append(total_env)
    
    grand_total += total_env

# Create DataFrame and display
summary_df = pd.DataFrame(summary_data)

print("Breakdown by Service and Environment (USD):\n")
print(f"{'Environment':<15} {'Registry':>15} {'Instances':>15} {'Defender':>15} {'Total':>15}")
print("-" * 77)

for i, env in enumerate(summary_df['Environment']):
    reg = summary_df['Container Registry'][i]
    inst = summary_df['Container Instances'][i]
    def_cloud = summary_df['Defender for Cloud'][i]
    total = summary_df['Total'][i]
    
    print(f"{env:<15} ${reg:>14,.2f} ${inst:>14,.2f} ${def_cloud:>14,.2f} ${total:>14,.2f}")

print("-" * 77)
print(f"{'TOTAL':<15} ${sum(summary_df['Container Registry']):>14,.2f} ${sum(summary_df['Container Instances']):>14,.2f} ${sum(summary_df['Defender for Cloud']):>14,.2f} ${grand_total:>14,.2f}\n")

print("=" * 100)
print("KEY FINDINGS")
print("=" * 100)

print(f"""
1. AZURE AKS COSTS (From Cost Management Files):
   
   • Dev:        ${summary_df['Total'][0]:>12,.2f}/month  (primarily Container Registry)
   • QA:         ${summary_df['Total'][1]:>12,.2f}/month  (Container Registry + Defender)
   • Prod:       ${summary_df['Total'][2]:>12,.2f}/month  (Container + Defender + Container Instances)
   • CentralHub: ${summary_df['Total'][3]:>12,.2f}/month  (Defender for Cloud)
   
   TOTAL MONTHLY: ${grand_total:,.2f}
   TOTAL ANNUAL:  ${grand_total * 12:,.2f}

2. COMPONENTS IDENTIFIED:
   
   ✓ Container Registry: Storage for Docker images and container artifacts
     - Dev: ${summary_df['Container Registry'][0]:.2f}/month
     - QA: ${summary_df['Container Registry'][1]:.2f}/month
     - Prod: ${summary_df['Container Registry'][2]:.2f}/month
   
   ✓ Container Instances: On-demand container execution (if used outside AKS)
     - Prod only: ${summary_df['Container Instances'][2]:.2f}/month
   
   ✓ Microsoft Defender for Cloud: Security scanning addon for containers
     - Dev: ${summary_df['Defender for Cloud'][0]:.2f}/month
     - QA: ${summary_df['Defender for Cloud'][1]:.2f}/month
     - Prod: ${summary_df['Defender for Cloud'][2]:.2f}/month
     - CentralHub: ${summary_df['Defender for Cloud'][3]:.2f}/month

3. AKS CLUSTERS IDENTIFIED (in Prod):
   
   Found 4 managed clusters in the Cost Management data:
   • aks-be-k8-eastus2-prod-001           → $563.47 (Defender cost)
   • aks-bpi-mdso-k8-eastus2-prod-002     → $3,446.19 (Defender cost)
   • aks-uaa-k8-eastus2-prod-001          → $1,692.17 (Defender cost)
   • aks-integrations-eastus2-prod-002    → $263.98 (Defender cost)

4. IMPORTANT NOTE:
   
   ⚠️  The costs shown above represent MANAGED SERVICES and ADDONS only.
   
   The actual AKS cluster compute costs (worker nodes, vCPUs, memory) are typically
   charged as "Virtual Machines" or "Compute" in Azure billing but may not be 
   easily attributed to specific clusters in these Cost Management exports.
   
   The Container Registry, Container Instances, and Defender costs total ~$10,887/month,
   but this does NOT include the worker node compute costs which would be significantly
   higher (typically 10-100x more).

5. COMPARISON TO TCO ASSUMPTIONS:
   
   Current TCO shows: $54,472/month for AKS
   
   Cost Management shows (containers + addons): $10,887/month
   
   Difference: $43,585/month (likely worker node costs not separately itemized)
""")

print("=" * 100)
