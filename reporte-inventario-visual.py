#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reporte Visual del Inventario Azure → AWS
Muestra análisis completo en formato tabla clara
"""

import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
import sys

class ReporteInventario:
    def __init__(self, json_file: str = "vm-costs-azure-aws-mapping.json"):
        self.json_file = json_file
        self.vms = []
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos del JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for vm_data in data.get('vms', []):
                azure_monthly = vm_data.get('azure_cost_total', 0)
                azure_annual = azure_monthly * 12
                aws_annual = vm_data.get('aws_cost_annual', 0)
                savings = azure_annual - aws_annual
                savings_pct = (savings / azure_annual * 100) if azure_annual > 0 else 0
                
                # Inferir ambiente
                name = vm_data.get('name', '').lower()
                if 'prod' in name:
                    env = 'PROD'
                elif 'dev' in name:
                    env = 'DEV'
                elif 'qa' in name:
                    env = 'QA'
                elif 'central' in name or 'hub' in name:
                    env = 'HUB'
                else:
                    env = '???'
                
                self.vms.append({
                    'nombre': vm_data.get('name', ''),
                    'env': env,
                    'azure_size': vm_data.get('azure_size', ''),
                    'aws_eq': vm_data.get('aws_equivalent', ''),
                    'vcpu': vm_data.get('vcpu', 0),
                    'ram': vm_data.get('memory_gb', 0),
                    'azure_monthly': azure_monthly,
                    'azure_annual': azure_annual,
                    'aws_annual': aws_annual,
                    'savings': savings,
                    'savings_pct': savings_pct,
                    'verdict': '✅' if savings > 0 else '❌'
                })
        
        except FileNotFoundError:
            print(f"❌ Error: No se encontró {self.json_file}")
            sys.exit(1)
    
    def titulo(self, text: str, char: str = "="):
        """Imprime título formateado"""
        print(f"\n{char * 100}")
        print(f"{text.center(100)}")
        print(f"{char * 100}")
    
    def seccion(self, text: str):
        """Imprime encabezado de sección"""
        print(f"\n{'─' * 100}")
        print(f"  {text}")
        print(f"{'─' * 100}")
    
    def generar_reporte(self):
        """Genera el reporte completo"""
        
        # PORTADA
        self.titulo("📊 REPORTE DE INVENTARIO: AZURE → AWS", "═")
        print(f"\n  Total de VMs:              {len(self.vms):>3}")
        print(f"  Fecha:                     {Path(self.json_file).stat().st_mtime_ns if Path(self.json_file).exists() else 'N/A'}")
        
        # RESUMEN GENERAL
        self.seccion("1️⃣  RESUMEN GENERAL")
        
        azure_total = sum(vm['azure_annual'] for vm in self.vms)
        aws_total = sum(vm['aws_annual'] for vm in self.vms)
        ahorros_total = azure_total - aws_total
        pct_ahorro = (ahorros_total / azure_total * 100) if azure_total > 0 else 0
        migrables = len([vm for vm in self.vms if vm['savings'] > 0])
        
        print(f"\n  💰 COSTOS (ANUAL):")
        print(f"     Azure Total:                 ${azure_total:>15,.2f}")
        print(f"     AWS OnDemand Total:          ${aws_total:>15,.2f}")
        print(f"     Ahorros Potenciales:         ${ahorros_total:>15,.2f}")
        print(f"     Porcentaje de Ahorro:        {pct_ahorro:>14.1f}%")
        
        print(f"\n  📊 DISTRIBUCIÓN:")
        print(f"     VMs para Migrar (✅):        {migrables:>16} ({migrables/len(self.vms)*100:>5.1f}%)")
        print(f"     VMs sin Beneficio (❌):      {len(self.vms)-migrables:>16} ({(len(self.vms)-migrables)/len(self.vms)*100:>5.1f}%)")
        
        # ANÁLISIS POR AMBIENTE
        self.seccion("2️⃣  ANÁLISIS POR AMBIENTE")
        
        by_env = defaultdict(list)
        for vm in self.vms:
            by_env[vm['env']].append(vm)
        
        print(f"\n{'Ambiente':<10} {'VMs':<6} {'Azure/Año':<16} {'AWS/Año':<16} {'Ahorro':<16} {'%':<8} {'Veredicto':<12}")
        print("─" * 94)
        
        for env in sorted(by_env.keys()):
            vms_env = by_env[env]
            azure_env = sum(vm['azure_annual'] for vm in vms_env)
            aws_env = sum(vm['aws_annual'] for vm in vms_env)
            ahorros_env = azure_env - aws_env
            pct_env = (ahorros_env / azure_env * 100) if azure_env > 0 else 0
            verdict = "✅ MIGRAR" if ahorros_env > 0 else "❌ NO"
            
            print(f"{env:<10} {len(vms_env):<6} ${azure_env:<15,.0f} ${aws_env:<15,.0f} ${ahorros_env:<15,.0f} {pct_env:>6.1f}% {verdict:<12}")
        
        # TOP 15 VMs
        self.seccion("3️⃣  TOP 15 VMs CON MAYOR AHORRO POTENCIAL")
        
        vms_sorted = sorted(self.vms, key=lambda x: x['savings'], reverse=True)[:15]
        
        print(f"\n{'#':<3} {'Nombre':<45} {'Azure/Año':<14} {'AWS/Año':<14} {'Ahorro':<14} {'%':<7}")
        print("─" * 100)
        
        for idx, vm in enumerate(vms_sorted, 1):
            nombre_trunc = vm['nombre'][:44] if len(vm['nombre']) > 44 else vm['nombre']
            print(f"{idx:<3} {nombre_trunc:<45} ${vm['azure_annual']:<13,.0f} ${vm['aws_annual']:<13,.0f} ${vm['savings']:<13,.0f} {vm['savings_pct']:>5.1f}%")
        
        # MAPEO DE RECURSOS
        self.seccion("4️⃣  MAPEO DE RECURSOS: AZURE → AWS")
        
        print(f"\n{'Tamaño Azure':<20} {'Equivalente AWS':<20} {'vCPU':<6} {'Memoria':<10} {'Cantidad':<10}")
        print("─" * 66)
        
        mappings = {}
        for vm in self.vms:
            key = (vm['azure_size'], vm['aws_eq'])
            if key not in mappings:
                mappings[key] = {'vcpu': vm['vcpu'], 'ram': vm['ram'], 'count': 0}
            mappings[key]['count'] += 1
        
        for (azure, aws), info in sorted(mappings.items()):
            print(f"{azure:<20} {aws:<20} {info['vcpu']:<6} {info['ram']:.1f} GB{'':<3} {info['count']:<10}")
        
        # ESCENARIOS DE PRICING
        self.seccion("5️⃣  ESCENARIOS DE PRICING AWS (ANUAL)")
        
        aws_base = aws_total
        aws_1yr = aws_base * 0.70
        aws_3yr = aws_base * 0.50
        aws_spot = aws_base * 0.30
        
        print(f"\n{'Escenario':<30} {'Costo AWS':<18} {'vs Azure':<18} {'Ahorro':<14} {'%':<8}")
        print("─" * 88)
        print(f"{'OnDemand (sin contrato)':<30} ${aws_base:<17,.0f} ${azure_total - aws_base:<17,.0f} ${ahorros_total:<13,.0f} {pct_ahorro:>6.1f}%")
        print(f"{'Contrato 1 año (30% desc.)':<30} ${aws_1yr:<17,.0f} ${azure_total - aws_1yr:<17,.0f} ${azure_total - aws_1yr:<13,.0f} {(azure_total - aws_1yr)/azure_total*100:>6.1f}%")
        print(f"{'Contrato 3 años (50% desc.)':<30} ${aws_3yr:<17,.0f} ${azure_total - aws_3yr:<17,.0f} ${azure_total - aws_3yr:<13,.0f} {(azure_total - aws_3yr)/azure_total*100:>6.1f}%")
        print(f"{'Spot (70% desc. máximo)':<30} ${aws_spot:<17,.0f} ${azure_total - aws_spot:<17,.0f} ${azure_total - aws_spot:<13,.0f} {(azure_total - aws_spot)/azure_total*100:>6.1f}%")
        
        # TABLA COMPLETA DE VMs
        self.seccion("6️⃣  TABLA COMPLETA DE TODAS LAS VMs")
        
        print(f"\n{'#':<4} {'Ambiente':<6} {'Nombre':<42} {'Tamaño':<15} {'AWS':<12} {'Azure/Año':<13} {'AWS/Año':<13} {'Ahorro':<13} {'Veredicto':<10}")
        print("─" * 129)
        
        for idx, vm in enumerate(sorted(self.vms, key=lambda x: (x['env'], x['nombre'])), 1):
            nombre_trunc = vm['nombre'][:41] if len(vm['nombre']) > 41 else vm['nombre']
            print(f"{idx:<4} {vm['env']:<6} {nombre_trunc:<42} {vm['azure_size']:<15} {vm['aws_eq']:<12} "
                  f"${vm['azure_annual']:<12,.0f} ${vm['aws_annual']:<12,.0f} ${vm['savings']:<12,.0f} {vm['verdict']:<10}")
        
        # CONCLUSIONES
        self.seccion("7️⃣  CONCLUSIONES Y RECOMENDACIONES")
        
        print(f"\n  ✅ MIGRACIÓN A AWS: {'RECOMENDADA' if ahorros_total > 0 else 'NO RECOMENDADA'}")
        print(f"\n  📌 Hallazgos Clave:")
        print(f"     • {migrables} de {len(self.vms)} VMs tienen beneficio financiero migrando a AWS")
        print(f"     • Ahorro potencial anual: ${ahorros_total:,.2f}")
        print(f"     • Reducción de costos: {pct_ahorro:.1f}%")
        print(f"     • Ambiente con mayor ahorro: {max(by_env.items(), key=lambda x: sum(v['savings'] for v in x[1]))[0]}")
        print(f"     • Ambiente con menos ahorro: {min(by_env.items(), key=lambda x: sum(v['savings'] for v in x[1]))[0]}")
        
        top_vm = max(self.vms, key=lambda x: x['savings'])
        print(f"\n  🏆 VM con Mayor Ahorro Potencial:")
        print(f"     • Nombre: {top_vm['nombre']}")
        print(f"     • Ahorro Anual: ${top_vm['savings']:,.2f}")
        print(f"     • Porcentaje: {top_vm['savings_pct']:.1f}%")
        
        # FIRMA
        self.titulo("FIN DEL REPORTE", "═")
        print(f"\nTotal de VMs Analizadas: {len(self.vms)}")
        print(f"Fecha de Generación: {Path.cwd()}")
        print()


def main():
    """Función principal"""
    print("\n🚀 Generando reporte visual del inventario...\n")
    
    reporte = ReporteInventario()
    reporte.generar_reporte()
    
    print("✅ Reporte generado exitosamente.\n")


if __name__ == "__main__":
    main()
