#!/usr/bin/env python3
"""
Calculadora de Migración Azure → AWS
Basada en costos reales y mapeos EC2
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
        total_azure = self.data.get('total_azure_annual', 0)
        total_aws = self.data.get('total_aws_annual', 0)
        
        # Calcular por ambiente
        for env_name, vms in self.environments.items():
            if not vms:
                continue
            
            env_azure = sum(vm.get('azure_cost_total', 0) for vm in vms)
            env_aws = sum(vm.get('aws_cost_annual', 0) for vm in vms)
            env_savings = env_azure - env_aws
            env_savings_pct = (env_savings / env_azure * 100) if env_azure > 0 else 0
            
            print(f'🏢 {env_name:15} | VMs: {len(vms):3} | Azure: ${env_azure:>10,.2f}/año | AWS: ${env_aws:>10,.2f}/año | Ahorro: ${env_savings:>10,.2f} ({env_savings_pct:>6.1f}%)')
        
        print()
        print('─'*80)
        print(f'📈 TOTALES           | VMs: {total_vms:3} | Azure: ${total_azure:>10,.2f}/año | AWS: ${total_aws:>10,.2f}/año')
        print('─'*80)
        
        # Detalles
        print()
        print('💾 RECURSOS CONSUMIDOS:')
        total_vcpu = sum(vm.get('vcpu', 0) for vm in self.vms)
        total_ram = sum(vm.get('memory_gb', 0) for vm in self.vms)
        print(f'   vCPUs totales: {total_vcpu}')
        print(f'   RAM total:    {total_ram:,.0f} GB ({total_ram/1024:.1f} TB)')
        print()
        
        # Distribución de instancias
        print('📦 DISTRIBUCIÓN DE INSTANCIAS AWS:')
        instance_dist = {}
        for vm in self.vms:
            instance = vm.get('aws_equivalent', 'Unknown')
            instance_dist[instance] = instance_dist.get(instance, 0) + 1
        
        for instance in sorted(instance_dist.keys()):
            count = instance_dist[instance]
            pct = count / total_vms * 100
            print(f'   {instance:15} x {count:2} ({pct:>5.1f}%)')
    
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
            
            env_azure = sum(vm.get('azure_cost_total', 0) for vm in vms)
            env_aws = sum(vm.get('aws_cost_annual', 0) for vm in vms)
            env_savings = env_azure - env_aws
            
            print(f'   Costo Azure:    ${env_azure:>12,.2f}/año (${env_azure/12:>10,.2f}/mes)')
            print(f'   Costo AWS:      ${env_aws:>12,.2f}/año (${env_aws/12:>10,.2f}/mes)')
            print(f'   Potencial:      ${env_savings:>12,.2f}/año')
            
            if env_azure > 0:
                savings_pct = (env_savings / env_azure * 100)
                print(f'   Ahorro (%):     {savings_pct:>12.1f}%')
            
            # Top 3 VMs en este ambiente
            top_vms = sorted(vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:3]
            print(f'\n   Top 3 VMs más costosas:')
            for i, vm in enumerate(top_vms, 1):
                name = vm.get('name', 'Unknown')[:40]
                cost = vm.get('azure_cost_total', 0)
                print(f'      {i}. {name:40} → ${cost:>8,.2f}/año')
    
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
        
        for vm in matches[:20]:  # Mostrar máximo 20
            print(f"📌 {vm.get('name')}")
            print(f"   Azure Size:       {vm.get('azure_size')}")
            print(f"   AWS Equivalent:   {vm.get('aws_equivalent')}")
            print(f"   vCPUs/RAM:        {vm.get('vcpu')}/{vm.get('memory_gb')} GB")
            print(f"   Azure Cost:       ${vm.get('azure_cost_total', 0):>10,.2f}/año")
            print(f"   AWS Cost:         ${vm.get('aws_cost_annual', 0):>10,.2f}/año")
            
            savings = vm.get('azure_cost_total', 0) - vm.get('aws_cost_annual', 0)
            if vm.get('azure_cost_total', 0) > 0:
                savings_pct = (savings / vm.get('azure_cost_total', 0) * 100)
            else:
                savings_pct = 0
            print(f"   Ahorro Potencial: ${savings:>10,.2f}/año ({savings_pct:>6.1f}%)")
            print()
    
    def show_cost_comparison(self):
        """Comparación de costos"""
        print('\n' + '='*80)
        print('💰 COMPARACIÓN DE COSTOS')
        print('='*80)
        print()
        
        total_azure = sum(vm.get('azure_cost_total', 0) for vm in self.vms)
        total_aws = sum(vm.get('aws_cost_annual', 0) for vm in self.vms)
        
        print(f'Azure (Actual):              ${total_azure:>12,.2f}/año (${total_azure/12:>10,.2f}/mes)')
        print(f'AWS OnDemand:                ${total_aws:>12,.2f}/año (${total_aws/12:>10,.2f}/mes)')
        print()
        
        # Con descuentos
        aws_1yr = total_aws * 0.70   # 30% descuento
        aws_3yr = total_aws * 0.50   # 50% descuento
        
        print('CON DESCUENTOS:')
        print(f'AWS 1yr Savings Plan (30%):  ${aws_1yr:>12,.2f}/año (${aws_1yr/12:>10,.2f}/mes)')
        print(f'AWS 3yr Savings Plan (50%):  ${aws_3yr:>12,.2f}/año (${aws_3yr/12:>10,.2f}/mes)')
        print()
        
        # Análisis
        print('ANÁLISIS:')
        if total_azure < total_aws:
            diff = total_aws - total_azure
            print(f'❌ AWS OnDemand es ${diff:,.2f}/año más caro que Azure')
            print(f'   Con 3yr Reserved: ${total_azure - aws_3yr:,.2f}/año más caro aún')
        else:
            diff = total_azure - total_aws
            print(f'✅ AWS OnDemand ahorra ${diff:,.2f}/año vs Azure')
            print(f'   Con 3yr Reserved: ${total_azure - aws_3yr:,.2f}/año de ahorro')
    
    def show_discount_estimates(self):
        """Estimaciones con descuentos"""
        print('\n' + '='*80)
        print('📈 ESTIMACIONES CON DESCUENTOS')
        print('='*80)
        print()
        
        total_azure = sum(vm.get('azure_cost_total', 0) for vm in self.vms)
        total_aws = sum(vm.get('aws_cost_annual', 0) for vm in self.vms)
        
        strategies = [
            ('OnDemand', 1.0),
            ('1yr Savings Plan', 0.70),
            ('3yr Savings Plan', 0.50),
            ('Spot (Best Case)', 0.30),
        ]
        
        print('ESCENARIOS DE PRICING:')
        print()
        print(f'{"Estrategia":<25} | {"Costo Anual":>15} | {"Costo Mensual":>15} | {"vs Azure":>15} | {"ROI":>8}')
        print('─'*80)
        
        for strategy, discount in strategies:
            cost = total_aws * discount
            monthly = cost / 12
            savings = total_azure - cost
            roi = (savings / total_azure * 100) if total_azure > 0 else 0
            
            print(f'{strategy:<25} | ${cost:>14,.2f} | ${monthly:>14,.2f} | ${savings:>14,.2f} | {roi:>7.1f}%')
    
    def show_top_vms(self):
        """Top 10 VMs más costosas"""
        print('\n' + '='*80)
        print('🎯 TOP 10 VMs MÁS COSTOSAS')
        print('='*80)
        print()
        
        sorted_vms = sorted(self.vms, key=lambda x: x.get('azure_cost_total', 0), reverse=True)[:10]
        
        print(f'{"#":<3} | {"Nombre":<40} | {"Azure":<12} | {"AWS":<12} | {"Ahorro":<12}')
        print('─'*80)
        
        for i, vm in enumerate(sorted_vms, 1):
            name = vm.get('name', 'Unknown')[:40]
            azure_cost = vm.get('azure_cost_total', 0)
            aws_cost = vm.get('aws_cost_annual', 0)
            savings = azure_cost - aws_cost
            
            print(f'{i:<3} | {name:<40} | ${azure_cost:>10,.0f} | ${aws_cost:>10,.0f} | ${savings:>10,.0f}')
    
    def export_to_csv(self):
        """Exportar a CSV"""
        import csv
        
        filename = 'analisis-migracion-aws.csv'
        
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
                    'Costo Azure Anual',
                    'Costo AWS Anual',
                    'Ahorro Potencial',
                    '% Ahorro'
                ])
                
                # Datos
                for vm in self.vms:
                    azure_cost = vm.get('azure_cost_total', 0)
                    aws_cost = vm.get('aws_cost_annual', 0)
                    savings = azure_cost - aws_cost
                    savings_pct = (savings / azure_cost * 100) if azure_cost > 0 else 0
                    
                    writer.writerow([
                        vm.get('name', ''),
                        vm.get('azure_size', ''),
                        vm.get('aws_equivalent', ''),
                        vm.get('vcpu', ''),
                        vm.get('memory_gb', ''),
                        f'{azure_cost:.2f}',
                        f'{aws_cost:.2f}',
                        f'{savings:.2f}',
                        f'{savings_pct:.1f}'
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
