#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora Completa de Inventario Azure → AWS
Visualiza todas las VMs con su mapeo a AWS y análisis de costos
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class VM:
    name: str
    azure_size: str
    aws_equivalent: str
    vcpu: int
    memory_gb: float
    azure_cost_monthly: float
    azure_cost_annual: float
    aws_cost_monthly: float
    aws_cost_annual: float
    savings_annual: float
    savings_percentage: float
    environment: str = "Desconocido"

    def savings_verdict(self) -> str:
        """Retorna si AWS es mejor o peor que Azure"""
        if self.savings_annual > 0:
            return "✅ MIGRAR"
        else:
            return "❌ NO MIGRAR"

class CalculadoraInventario:
    def __init__(self, json_file: str = "vm-costs-azure-aws-mapping.json"):
        self.json_file = json_file
        self.vms: List[VM] = []
        self.environments: Dict[str, List[VM]] = {}
        self.cargar_inventario()
    
    def cargar_inventario(self):
        """Carga el inventario desde el archivo JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n📊 Cargando inventario desde {self.json_file}...")
            
            for vm_data in data.get('vms', []):
                azure_monthly = vm_data.get('azure_cost_total', 0)
                azure_annual = azure_monthly * 12
                aws_annual = vm_data.get('aws_cost_annual', 0)
                
                savings = azure_annual - aws_annual
                savings_pct = (savings / azure_annual * 100) if azure_annual > 0 else 0
                
                # Inferir ambiente del nombre de la VM
                name = vm_data.get('name', '').lower()
                if 'prod' in name:
                    env = 'PRODUCCIÓN'
                elif 'dev' in name:
                    env = 'DESARROLLO'
                elif 'qa' in name:
                    env = 'QA'
                elif 'central' in name or 'hub' in name:
                    env = 'CENTRAL HUB'
                else:
                    env = 'DESCONOCIDO'
                
                vm = VM(
                    name=vm_data.get('name', ''),
                    azure_size=vm_data.get('azure_size', ''),
                    aws_equivalent=vm_data.get('aws_equivalent', ''),
                    vcpu=vm_data.get('vcpu', 0),
                    memory_gb=vm_data.get('memory_gb', 0),
                    azure_cost_monthly=azure_monthly,
                    azure_cost_annual=azure_annual,
                    aws_cost_monthly=vm_data.get('aws_cost_monthly', 0),
                    aws_cost_annual=aws_annual,
                    savings_annual=savings,
                    savings_percentage=savings_pct,
                    environment=env
                )
                self.vms.append(vm)
                
                if env not in self.environments:
                    self.environments[env] = []
                self.environments[env].append(vm)
            
            print(f"✅ {len(self.vms)} VMs cargadas correctamente")
            print(f"   Ambientes: {', '.join(self.environments.keys())}\n")
        
        except FileNotFoundError:
            print(f"❌ Error: No se encontró {self.json_file}")
            exit(1)
        except json.JSONDecodeError:
            print(f"❌ Error: Formato JSON inválido en {self.json_file}")
            exit(1)
    
    def resumen_general(self):
        """Muestra resumen general de costos"""
        print("\n" + "="*80)
        print("📈 RESUMEN GENERAL DEL INVENTARIO")
        print("="*80)
        
        azure_total = sum(vm.azure_cost_annual for vm in self.vms)
        aws_total = sum(vm.aws_cost_annual for vm in self.vms)
        ahorros_total = azure_total - aws_total
        pct_ahorro = (ahorros_total / azure_total * 100) if azure_total > 0 else 0
        
        print(f"\n📊 Totales (Anual):")
        print(f"   Total Azure:           ${azure_total:,.2f}")
        print(f"   Total AWS OnDemand:    ${aws_total:,.2f}")
        print(f"   Diferencia:            ${ahorros_total:,.2f}")
        print(f"   Porcentaje ahorro:     {pct_ahorro:.1f}%")
        
        print(f"\n🖥️  Cantidad de VMs:        {len(self.vms)}")
        migrables = len([vm for vm in self.vms if vm.savings_annual > 0])
        print(f"   VMs a migrar (🟢):     {migrables} ({migrables/len(self.vms)*100:.1f}%)")
        print(f"   VMs a mantener (🔴):  {len(self.vms)-migrables} ({(len(self.vms)-migrables)/len(self.vms)*100:.1f}%)")
    
    def analisis_por_ambiente(self):
        """Análisis detallado por ambiente"""
        print("\n" + "="*80)
        print("🌍 ANÁLISIS POR AMBIENTE")
        print("="*80)
        
        for env in sorted(self.environments.keys()):
            vms_env = self.environments[env]
            azure_env = sum(vm.azure_cost_annual for vm in vms_env)
            aws_env = sum(vm.aws_cost_annual for vm in vms_env)
            ahorros_env = azure_env - aws_env
            pct_env = (ahorros_env / azure_env * 100) if azure_env > 0 else 0
            migrables = len([vm for vm in vms_env if vm.savings_annual > 0])
            
            verdict = "✅ MIGRAR" if ahorros_env > 0 else "❌ NO MIGRAR"
            
            print(f"\n{env:.<30} {verdict}")
            print(f"   VMs: {len(vms_env):>3} | Azure: ${azure_env:>12,.0f} | AWS: ${aws_env:>12,.0f}")
            print(f"   Ahorros: ${ahorros_env:>12,.0f} ({pct_env:>6.1f}%) | Migrables: {migrables}/{len(vms_env)}")
    
    def listar_todas_vms(self, filtro_env: str = None):
        """Lista todas las VMs con sus detalles"""
        print("\n" + "="*80)
        
        if filtro_env:
            vms_mostrar = self.environments.get(filtro_env, [])
            titulo = f"📋 INVENTARIO DE VMs: {filtro_env}"
        else:
            vms_mostrar = self.vms
            titulo = "📋 INVENTARIO COMPLETO DE VMs"
        
        print(titulo)
        print("="*80)
        
        # Encabezados
        print(f"{'#':<3} {'Nombre de VM':<40} {'Size':<15} {'AWS':<12} {'Azure/año':<12} {'AWS/año':<12} {'Ahorro':<12} {'Veredicto':<10}")
        print("-"*155)
        
        # Datos
        for idx, vm in enumerate(vms_mostrar, 1):
            print(f"{idx:<3} {vm.name:<40} {vm.azure_size:<15} {vm.aws_equivalent:<12} "
                  f"${vm.azure_cost_annual:<11,.0f} ${vm.aws_cost_annual:<11,.0f} "
                  f"${vm.savings_annual:<11,.0f} {vm.savings_verdict():<10}")
        
        print("-"*155)
        print(f"Total: {len(vms_mostrar)} VMs\n")
    
    def top_vms_mayor_ahorro(self, n: int = 10):
        """Top N VMs con mayor potencial de ahorro"""
        print("\n" + "="*80)
        print(f"🏆 TOP {n} VMs CON MAYOR AHORRO")
        print("="*80)
        
        ordenadas = sorted(self.vms, key=lambda x: x.savings_annual, reverse=True)
        top_n = ordenadas[:n]
        
        print(f"{'#':<3} {'Nombre':<40} {'Azure/año':<12} {'AWS/año':<12} {'Ahorro/año':<12} {'%':<6}")
        print("-"*85)
        
        for idx, vm in enumerate(top_n, 1):
            print(f"{idx:<3} {vm.name:<40} ${vm.azure_cost_annual:<11,.0f} ${vm.aws_cost_annual:<11,.0f} "
                  f"${vm.savings_annual:<11,.0f} {vm.savings_percentage:>5.1f}%")
        
        print()
    
    def detalle_vm(self, nombre_vm: str):
        """Muestra detalles completos de una VM"""
        vm = next((v for v in self.vms if nombre_vm.lower() in v.name.lower()), None)
        
        if not vm:
            print(f"❌ VM '{nombre_vm}' no encontrada")
            return
        
        print("\n" + "="*80)
        print(f"🖥️  DETALLES DE: {vm.name}")
        print("="*80)
        
        print(f"\n📍 Ubicación: {vm.environment}")
        print(f"   Azure Size:    {vm.azure_size}")
        print(f"   AWS Equivalent: {vm.aws_equivalent}")
        
        print(f"\n💻 Recursos:")
        print(f"   vCPU:          {vm.vcpu}")
        print(f"   Memoria:       {vm.memory_gb:.1f} GB")
        
        print(f"\n💰 Costos (Anuales):")
        print(f"   Azure:         ${vm.azure_cost_annual:,.2f}")
        print(f"   AWS OnDemand:  ${vm.aws_cost_annual:,.2f}")
        print(f"   Ahorro/Costo:  ${vm.savings_annual:,.2f} ({vm.savings_percentage:.1f}%)")
        
        print(f"\n🎯 Veredicto:       {vm.savings_verdict()}")
        print()
    
    def escenarios_pricing(self):
        """Muestra diferentes escenarios de precios AWS"""
        print("\n" + "="*80)
        print("💳 ESCENARIOS DE PRICING AWS (Todas las VMs)")
        print("="*80)
        
        aws_base = sum(vm.aws_cost_annual for vm in self.vms)
        aws_1yr = aws_base * 0.70  # 30% descuento
        aws_3yr = aws_base * 0.50  # 50% descuento
        aws_spot = aws_base * 0.30  # 70% descuento (aproximado)
        
        azure_total = sum(vm.azure_cost_annual for vm in self.vms)
        
        print(f"\nPrecio Azure Total:        ${azure_total:>12,.2f}")
        print(f"\nEscenarios AWS:")
        print(f"  • OnDemand (sin contrato):  ${aws_base:>12,.2f}  Ahorro: ${azure_total - aws_base:>12,.2f} ({(azure_total - aws_base)/azure_total*100:>6.1f}%)")
        print(f"  • 1 año Reserved:           ${aws_1yr:>12,.2f}  Ahorro: ${azure_total - aws_1yr:>12,.2f} ({(azure_total - aws_1yr)/azure_total*100:>6.1f}%)")
        print(f"  • 3 años Reserved:          ${aws_3yr:>12,.2f}  Ahorro: ${azure_total - aws_3yr:>12,.2f} ({(azure_total - aws_3yr)/azure_total*100:>6.1f}%)")
        print(f"  • Spot (máximo ahorro):     ${aws_spot:>12,.2f}  Ahorro: ${azure_total - aws_spot:>12,.2f} ({(azure_total - aws_spot)/azure_total*100:>6.1f}%)")
        print()
    
    def exportar_csv(self, nombre_archivo: str = "inventario-azure-aws.csv"):
        """Exporta el inventario a CSV"""
        import csv
        
        try:
            with open(nombre_archivo, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Encabezados
                writer.writerow([
                    'Nombre VM',
                    'Ambiente',
                    'Size Azure',
                    'Equivalente AWS',
                    'vCPU',
                    'Memoria (GB)',
                    'Costo Azure (Mensual)',
                    'Costo Azure (Anual)',
                    'Costo AWS (Mensual)',
                    'Costo AWS (Anual)',
                    'Ahorro Anual',
                    'Porcentaje Ahorro',
                    'Veredicto'
                ])
                
                # Datos
                for vm in sorted(self.vms, key=lambda x: x.name):
                    writer.writerow([
                        vm.name,
                        vm.environment,
                        vm.azure_size,
                        vm.aws_equivalent,
                        vm.vcpu,
                        vm.memory_gb,
                        f"${vm.azure_cost_monthly:.2f}",
                        f"${vm.azure_cost_annual:.2f}",
                        f"${vm.aws_cost_monthly:.2f}",
                        f"${vm.aws_cost_annual:.2f}",
                        f"${vm.savings_annual:.2f}",
                        f"{vm.savings_percentage:.1f}%",
                        vm.savings_verdict()
                    ])
            
            print(f"\n✅ Inventario exportado a: {nombre_archivo}")
        except Exception as e:
            print(f"❌ Error al exportar: {e}")
    
    def menu_interactivo(self):
        """Menú interactivo principal"""
        while True:
            print("\n" + "="*80)
            print("🚀 CALCULADORA INVENTARIO AZURE → AWS")
            print("="*80)
            print("""
1. 📊 Resumen General
2. 🌍 Análisis por Ambiente
3. 📋 Listar todas las VMs
4. 📑 Listar VMs por Ambiente
5. 🏆 Top 10 VMs con mayor ahorro
6. 🖥️  Detalles de VM específica
7. 💳 Escenarios de Pricing AWS
8. 📁 Exportar a CSV
9. 🚪 Salir
""")
            opcion = input("Selecciona una opción (1-9): ").strip()
            
            if opcion == '1':
                self.resumen_general()
            elif opcion == '2':
                self.analisis_por_ambiente()
            elif opcion == '3':
                self.listar_todas_vms()
            elif opcion == '4':
                print("\nAmbientes disponibles:")
                for idx, env in enumerate(sorted(self.environments.keys()), 1):
                    print(f"  {idx}. {env} ({len(self.environments[env])} VMs)")
                try:
                    idx = int(input("Selecciona ambiente (número): ")) - 1
                    env = sorted(self.environments.keys())[idx]
                    self.listar_todas_vms(env)
                except:
                    print("❌ Selección inválida")
            elif opcion == '5':
                self.top_vms_mayor_ahorro(10)
            elif opcion == '6':
                nombre = input("Ingresa parte del nombre de la VM: ").strip()
                if nombre:
                    self.detalle_vm(nombre)
            elif opcion == '7':
                self.escenarios_pricing()
            elif opcion == '8':
                nombre_archivo = input("Nombre del archivo (Enter para 'inventario-azure-aws.csv'): ").strip()
                if not nombre_archivo:
                    nombre_archivo = "inventario-azure-aws.csv"
                self.exportar_csv(nombre_archivo)
            elif opcion == '9':
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
            
            input("\nPresiona Enter para continuar...")


def main():
    """Función principal"""
    print("\n🎯 INICIALIZANDO CALCULADORA DE INVENTARIO...")
    
    calc = CalculadoraInventario()
    calc.menu_interactivo()


if __name__ == "__main__":
    main()
