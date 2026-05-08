#!/usr/bin/env python3
"""
Calculadora de Migración Azure → AWS (CORRECCIÓN APLICADA)
IMPORTANTE: Precios de Azure son MENSUALES, no anuales
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


class AWSMigrationCalculator:
    def __init__(self, mapping_file: str = 'vm-costs-azure-aws-mapping.json'):
        """Cargar datos de mapeo"""
        self.data = self._load_data(mapping_file)
        self.vms = self.data.get('vms', [])
        self.environments = self._extract_environments()
        
        # CORRECCIÓN: Azure costs son MENSUALES
        self.total_azure_monthly = self.data.get('total_azure_annual', 0)
        self.total_azure_annual = self.total_azure_monthly * 12
        self.total_aws_annual = self.data.get('total_aws_annual', 0)
    
    def _load_data(self, filepath: str) -> Dict:
        """Cargar archivo JSON"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {filepath}")
            sys.exit(1)
    
    def _extract_environments(self) -> Dict[str, List]:
        """Extraer VMs por ambiente"""
        envs = {'Prod': [], 'Dev': [], 'QA': [], 'CentralHub': [], 'Unknown': []}
        
        for vm in self.vms:
            name = vm.get('name', '').lower()
            
            if 'prod' in name:
                envs['Prod'].append(vm)
            elif 'dev' in name:
                envs['Dev'].append(vm)
            elif 'qa' in name:
                envs['QA'].append(vm)
            elif 'central' in name or 'centralhub' in name:
                envs['CentralHub'].append(vm)
            else:
                envs['Unknown'].append(vm)
        
        return envs
    
    def show_menu(self):
        """Menú principal"""
        while True:
            print('\n' + '='*80)
            print('🧮 CALCULADORA AWS - MIGRACIÓN DESDE AZURE')
            print('='*80)
            print()
            print('1. 📊 Resumen General')
            print('2. 🌍 Análisis por Ambiente')
            print('3. 🔍 Detalles de VMs')
            print('4. 💰 Comparación de Costos')
            print('5. 📈 Estimaciones con Descuentos')
            print('6. 🎯 Top 10 VMs Más Costosas')
            print('7. 📋 Exportar Análisis a CSV')
            print('8. ❌ Salir')
            print()
            
            choice = input('Seleccione opción (1-8): ').strip()
            
            if choice == '1':
                self.show_summary()
            elif choice == '2':
                self.show_by_environment()
            elif choice == '3':
                self.show_vm_details()
            elif choice == '4':
                self.show_cost_comparison()
            elif choice == '5':
                self.show_discount_estimates()
            elif choice == '6':
                self.show_top_vms()
            elif choice == '7':
                self.export_to_csv()
            elif choice == '8':
                print('\n✅ Hasta luego!\n')
                break
            else:
                print('❌ Opción no válida')
    
    def show_summary(self):
        """Mostrar resumen general"""
        print('\n' + '='*80)
        print('📊 RESUMEN GENERAL')
        print('='*80)
        print()
        
        total_vms = len(self.vms)
        
        # Calcular por ambiente
        for env_name, vms in self.environments.items():
            if not vms:
                continue
            
            env_azure_monthly = sum(vm.get('azure_cost_total', 0) for vm in vms)
            env_azure_annual = env_azure_monthly * 12
            env_aws = sum(vm.get('aws_cost_annual', 0) for vm in vms)
            env_savings = env_azure_annual - env_aws
            env_savings_pct = (env_savings / env_azure_annual * 100) if env_azure_annual > 0 else 0
            
            status = '✅' if env_savings > 0 else '❌'
            print(f'{status} {env_name:15} | VMs: {len(vms):3} | Azure: ${env_azure_annual:>10,.0f}/año | AWS: ${env_aws:>10,.0f}/año | Ahorro: ${env_savings:>10,.0f} ({env_savings_pct:>6.1f}%)')
        
        print()
        print('─'*80)
        print(f'📈 TOTALES           | VMs: {total_vms:3} | Azure: ${self.total_azure_annual:>10,.0f}/año | AWS: ${self.total_aws_annual:>10,.0f}/año')
        
        total_savings = self.total_azure_annual - self.total_aws_annual
        total_savings_pct = (total_savings / self.total_azure_annual * 100)
        print(f'{'✅' if total_savings > 0 else '❌'} AHORRO: ${total_savings:>10,.0f}/año ({total_savings_pct:>6.1f}%)')
        print('─'*80)
        
        # Detalles
        print()
        print('💾 RECURSOS CONSUMIDOS:')
        total_vcpu = sum(vm.get('vcpu', 0) for vm in self.vms)
        total_ram = sum(vm.get('memory_gb', 0) for vm in self.vms)
        print(f'   vCPUs totales: {total_vcpu}')
        print(f'   RAM total:    {total_ram:,.0f} GB ({total_ram/1024:.1f} TB)')
        print()
    
    def show_by_environment(self):
        """Análisis por ambiente"""
        print('\n' + '='*80)
        print('🌍 ANÁLISIS POR AMBIENTE')
        print('='*80)
        
        for env_name, vms in self.environments.items():
            if not vms:
                continue
            
            print(f'\n📍 {env_name.upper()}')
            print('─'*80)
            print(f'   Total VMs: {len(vms)}')
            
            env_azure_monthly = sum(vm.get('azure_cost_total', 0) for vm in vms)
            env_azure_annual = env_azure_monthly * 12
            env_aws = sum(vm.get('aws_cost_annual', 0) for vm in vms)
            env_savings = env_azure_annual - env_aws
            
            print(f'   Costo Azure:    ${env_azure_annual:>12,.0f}/año (${env_azure_monthly:>10,.0f}/mes)')
            print(f'   Costo AWS:      ${env_aws:>12,.0f}/año (${env_aws/12:>10,.0f}/mes)')
            print(f'   Potencial:      ${env_savings:>12,.0f}/año')
            
            if env_azure_annual > 0:
                savings_pct = (env_savings / env_azure_annual * 100)
                status = '✅ AWS más barato' if env_savings > 0 else '❌ Azure más barato'
                print(f'   Status:         {status} ({abs(savings_pct):>6.1f}%)')
            
            # Top 3 VMs en este ambiente
            top_vms = sorted(vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:3]
            print(f'\n   Top 3 VMs más costosas:')
            for i, vm in enumerate(top_vms, 1):
                name = vm.get('name', 'Unknown')[:40]
                cost = vm.get('azure_cost_total', 0)
                print(f'      {i}. {name:40} → ${cost*12:>8,.0f}/año (${cost:>8,.0f}/mes)')
    
    def show_vm_details(self):
        """Mostrar detalles de VMs"""
        print('\n' + '='*80)
        print('🔍 DETALLES DE VMs')
        print('='*80)
        print()
        
        search = input('Buscar VM por nombre (parcial): ').strip().lower()
        
        matches = [vm for vm in self.vms if search in vm.get('name', '').lower()]
        
        if not matches:
            print(f'❌ No se encontraron VMs con "{search}"')
            return
        
        print(f'\n✅ Encontradas {len(matches)} VM(s):')
        print()
        
        for vm in matches[:20]:
            print(f"📌 {vm.get('name')}")
            print(f"   Azure Size:       {vm.get('azure_size')}")
            print(f"   AWS Equivalent:   {vm.get('aws_equivalent')}")
            print(f"   vCPUs/RAM:        {vm.get('vcpu')}/{vm.get('memory_gb')} GB")
            
            azure_monthly = vm.get('azure_cost_total', 0)
            azure_annual = azure_monthly * 12
            aws_annual = vm.get('aws_cost_annual', 0)
            
            print(f"   Azure Cost:       ${azure_annual:>10,.0f}/año (${azure_monthly:>8,.0f}/mes)")
            print(f"   AWS Cost:         ${aws_annual:>10,.0f}/año")
            
            savings = azure_annual - aws_annual
            if azure_annual > 0:
                savings_pct = (savings / azure_annual * 100)
            else:
                savings_pct = 0
            
            status = '✅' if savings > 0 else '❌'
            print(f"   {status} Diferencia: ${savings:>10,.0f}/año ({abs(savings_pct):>6.1f}%)")
            print()
    
    def show_cost_comparison(self):
        """Comparación de costos"""
        print('\n' + '='*80)
        print('💰 COMPARACIÓN DE COSTOS')
        print('='*80)
        print()
        
        print(f'Azure (Actual):              ${self.total_azure_annual:>12,.0f}/año (${self.total_azure_monthly:>10,.0f}/mes)')
        print(f'AWS OnDemand:                ${self.total_aws_annual:>12,.0f}/año (${self.total_aws_annual/12:>10,.0f}/mes)')
        print()
        
        # Con descuentos
        aws_1yr = self.total_aws_annual * 0.70
        aws_3yr = self.total_aws_annual * 0.50
        aws_spot = self.total_aws_annual * 0.30
        
        print('CON DESCUENTOS:')
        print(f'AWS 1yr Savings (30%):       ${aws_1yr:>12,.0f}/año (${aws_1yr/12:>10,.0f}/mes)')
        print(f'AWS 3yr Savings (50%):       ${aws_3yr:>12,.0f}/año (${aws_3yr/12:>10,.0f}/mes)')
        print(f'AWS Spot Instances (70%):    ${aws_spot:>12,.0f}/año (${aws_spot/12:>10,.0f}/mes)')
        print()
        
        # Análisis
        print('ANÁLISIS:')
        diff_ondemand = self.total_azure_annual - self.total_aws_annual
        if diff_ondemand > 0:
            print(f'✅ AWS OnDemand es ${diff_ondemand:,.0f}/año más barato ({(diff_ondemand/self.total_azure_annual*100):.1f}%)')
        else:
            print(f'❌ Azure es ${abs(diff_ondemand):,.0f}/año más barato')
        
        diff_3yr = self.total_azure_annual - aws_3yr
        print(f'✅ AWS 3yr Reserved es ${diff_3yr:,.0f}/año más barato ({(diff_3yr/self.total_azure_annual*100):.1f}%)')
    
    def show_discount_estimates(self):
        """Estimaciones con descuentos"""
        print('\n' + '='*80)
        print('📈 ESTIMACIONES CON DESCUENTOS')
        print('='*80)
        print()
        
        strategies = [
            ('Azure (Actual)', self.total_azure_annual),
            ('AWS OnDemand', self.total_aws_annual),
            ('AWS 1yr Savings Plan (30%)', self.total_aws_annual * 0.70),
            ('AWS 3yr Savings Plan (50%)', self.total_aws_annual * 0.50),
            ('AWS Spot (Best Case)', self.total_aws_annual * 0.30),
        ]
        
        print('ESCENARIOS DE PRICING:')
        print()
        print(f'{"Estrategia":<30} | {"Costo Anual":>15} | {"Costo Mensual":>15} | {"vs Azure":>15} | {"Status":>8}')
        print('─'*80)
        
        for strategy, cost in strategies:
            monthly = cost / 12
            vs_azure = self.total_azure_annual - cost
            status = '✅' if vs_azure > 0 else '❌'
            
            print(f'{strategy:<30} | ${cost:>13,.0f} | ${monthly:>13,.0f} | ${vs_azure:>13,.0f} | {status:>8}')
    
    def show_top_vms(self):
        """Top 10 VMs más costosas"""
        print('\n' + '='*80)
        print('🎯 TOP 10 VMs MÁS COSTOSAS')
        print('='*80)
        print()
        
        sorted_vms = sorted(self.vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:10]
        
        print(f'{"#":<3} | {"Nombre":<40} | {"Azure/mes":>10} | {"Azure/año":>10} | {"AWS":>10}')
        print('─'*80)
        
        for i, vm in enumerate(sorted_vms, 1):
            name = vm.get('name', 'Unknown')[:40]
            azure_monthly = vm.get('azure_cost_total', 0)
            azure_annual = azure_monthly * 12
            aws_cost = vm.get('aws_cost_annual', 0)
            
            print(f'{i:<3} | {name:<40} | ${azure_monthly:>8,.0f} | ${azure_annual:>8,.0f} | ${aws_cost:>8,.0f}')
    
    def export_to_csv(self):
        """Exportar a CSV"""
        import csv
        
        filename = 'analisis-migracion-aws-correcto.csv'
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Nombre VM',
                    'Azure Size',
                    'AWS Equivalent',
                    'vCPUs',
                    'RAM (GB)',
                    'Azure Mensual',
                    'Azure Anual',
                    'AWS Anual',
                    'Diferencia',
                    'Status'
                ])
                
                # Datos
                for vm in self.vms:
                    azure_monthly = vm.get('azure_cost_total', 0)
                    azure_annual = azure_monthly * 12
                    aws_annual = vm.get('aws_cost_annual', 0)
                    diff = azure_annual - aws_annual
                    status = 'AWS' if diff > 0 else 'Azure'
                    
                    writer.writerow([
                        vm.get('name', ''),
                        vm.get('azure_size', ''),
                        vm.get('aws_equivalent', ''),
                        vm.get('vcpu', ''),
                        vm.get('memory_gb', ''),
                        f'{azure_monthly:.2f}',
                        f'{azure_annual:.2f}',
                        f'{aws_annual:.2f}',
                        f'{diff:.2f}',
                        status
                    ])
            
            print(f'\n✅ Archivo exportado: {filename}')
        except Exception as e:
            print(f'❌ Error al exportar: {e}')


def main():
    """Función principal"""
    calc = AWSMigrationCalculator()
    calc.show_menu()


if __name__ == '__main__':
    main()
