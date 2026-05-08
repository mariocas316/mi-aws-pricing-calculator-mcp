#!/usr/bin/env python3
"""
Extrae información de APIM del inventario de Azure
Busca: Azure API Management, endpoints, policies, productos
"""
import json
from pathlib import Path

# El inventario ARI típicamente está en formato JSON o Excel
# Voy a buscar el archivo y extraer datos de APIM

inventory_dir = Path('inventarioAri')

print("=" * 80)
print("BUSCANDO RECURSOS APIM EN INVENTARIO ARI")
print("=" * 80)

# Listar archivos en el directorio
print("\nArchivos encontrados:")
for file in inventory_dir.glob('*'):
    print(f"  - {file.name}")

# El archivo es Excel, necesito datos de APIM
# Voy a crear un template de preguntas para que el usuario confirme los datos

template = """
PREGUNTAS PARA EXTRAER DATOS DE APIM:

1. ¿Cuántas instancias de API Management (APIM) tienes en Azure?
   - Environment: _______ (Dev/QA/Prod)
   - SKU: _______ (Developer/Standard/Premium)
   - Cantidad: _______ 

2. ¿Cuántos productos/APIs expuestos en APIM?
   - Por ambiente: Dev _____, QA _____, Prod _____

3. ¿Cuántas llamadas mensuales a las APIs?
   - Total mensual: _______ (ej: 10 millones, 50 millones, etc)
   - Por ambiente (si lo sabes): Dev _____, QA _____, Prod _____

4. ¿Qué tipos de políticas aplicas? (Rate limiting, caching, transformación, etc)

5. ¿Usas Custom Domains?

6. ¿Tienes certificados SSL?
"""

print("\n" + template)

# Alternativa: buscar datos en Excel usando PowerShell
print("\n" + "=" * 80)
print("INTENTANDO EXTRAER CON POWERSHELL...")
print("=" * 80)
