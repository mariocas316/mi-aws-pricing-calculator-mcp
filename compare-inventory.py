#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compare expected inventory vs Cost Management findings
"""

import pandas as pd

print("=" * 100)
print("COMPARACION: INVENTARIO ESPERADO vs COST MANAGEMENT")
print("=" * 100)

print("\n📋 INVENTARIO ESPERADO (del TCO Excel):")
print("-" * 100)
print("  Clusters AKS:    10")
print("  Nodos activos:   76")
print("  vCPUs:           1,456")
print("  Almacenamiento:  1,900 GiB")

print("\n📊 ENCONTRADO EN COST MANAGEMENT:")
print("-" * 100)

# Summary from previous analysis
findings = {
    'Dev': {
        'vmss_unique': 5,
        'total_cost': 3_749.75,
        'nodes': 5
    },
    'QA': {
        'vmss_unique': 1,  # aks-npbpsys pattern
        'total_cost': 8_991.20,
        'nodes': 1  # Rough estimate
    },
    'Prod': {
        'vmss_unique': 4,  # From earlier analysis
        'total_cost': 24_519.12,
        'nodes': 93  # From VMSS breakdown
    },
    'CentralHub': {
        'vmss_unique': 0,
        'total_cost': 0,
        'nodes': 0
    }
}

total_vmss = sum(f['vmss_unique'] for f in findings.values())
total_nodes_found = sum(f['nodes'] for f in findings.values())

print(f"  Clusters identificados:     ~{total_vmss} (VMSS patterns)")
print(f"  Nodos encontrados:          ~{total_nodes_found}")
print(f"  Análisis por ambiente:")

for env, data in findings.items():
    print(f"\n    {env}:")
    print(f"      - VMSS patterns: {data['vmss_unique']}")
    print(f"      - Nodos: {data['nodes']}")
    print(f"      - Costo mensual: ${data['total_cost']:,.2f}")

print("\n" + "=" * 100)
print("ANALISIS DE DISCREPANCIAS")
print("=" * 100)

print(f"\n1. CLUSTERS:")
print(f"   Esperado:   10 clusters")
print(f"   Encontrado: ~{total_vmss} VMSS patterns (nota: no son clusters, son instance groups)")
print(f"   Status: DISCREPANCIA - Cost Management no muestra clusters, muestra VMSS")

print(f"\n2. NODOS:")
print(f"   Esperado:   76 nodos activos")
print(f"   Encontrado: ~{total_nodes_found} nodos en billing")
print(f"   Diferencia: {total_nodes_found - 76:+d} nodos")

if total_nodes_found > 76:
    print(f"   Posible causa: Se están cobrando más nodos de los planificados")
elif total_nodes_found < 76:
    print(f"   Posible causa: Algunos nodos están en estado parado (no se cobran)")

print(f"\n3. vCPU:")
print(f"   Esperado:   1,456 vCPUs")

# Calculate from node count and typical sizes
if total_nodes_found > 0:
    avg_vcpu_per_node = 1456 / 76  # Expected average
    total_vcpu_if_filled = total_nodes_found * avg_vcpu_per_node
    print(f"   Si {total_nodes_found} nodos tuvieran {avg_vcpu_per_node:.1f} vCPU c/u:")
    print(f"   Total sería: ~{total_vcpu_if_filled:,.0f} vCPUs")

print(f"\n4. COSTOS:")
print(f"   Esperado TCO (AKS): $54,472/mes")
print(f"   Encontrado en Cost Management:")

total_cost_actual = sum(f['total_cost'] for f in findings.values())
# Add container services
container_services = 10_887.22

total_aks_actual = total_cost_actual + container_services

print(f"     - Worker Nodes: ${total_cost_actual:,.2f}")
print(f"     - Container Services: ${container_services:,.2f}")
print(f"     - TOTAL: ${total_aks_actual:,.2f}")
print(f"   Diferencia: ${total_aks_actual - 54_472:+,.2f} ({((total_aks_actual/54_472 - 1)*100):+.1f}%)")

print(f"\n" + "=" * 100)
print("CONCLUSION")
print("=" * 100)

print("""
COINCIDENCIA PARCIAL:

✓ El TCO menciona "10 clusters, 76 nodos activos, 1,456 vCPUs"
✗ Cost Management muestra datos diferentes:
  - Los clusters no están claramente separados (muestran VMSS)
  - Se encontraron ~{} nodos vs 76 esperados
  - La facturación actual es MENOR que lo presupuestado

EXPLICACIÓN PROBABLE:

1. Los 10 clusters están distribuidos en 4 ambientes (Dev/QA/Prod/CentralHub)
2. Los datos de billing muestran solo nodos ACTIVOS (facturados)
3. Puede haber:
   - Nodos que estaban planeados pero no se han desplegado
   - Nodos parados que no se facturan
   - O nodos adicionales en producción que incrementaron el gasto

PROXIMOS PASOS:

1. Verificar con el equipo de Azure qué clusters están activos
2. Confirmar si los {} nodos encontrados en billing son correctos
3. Validar vCPUs reales vs esperados
4. Actualizar el TCO con datos reales de Cost Management
""".format(total_nodes_found, total_nodes_found))

print("=" * 100)
