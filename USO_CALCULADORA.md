# 🧮 Calculadora AWS - Guía de Uso

## ¿Qué es?

Herramienta interactiva para analizar costos de migración Azure → AWS basada en datos reales del archivo `vm-costs-azure-aws-mapping.json`.

## 📋 Archivos Creados

### 1. **calculadora-aws.py** (Interactiva)
Menú interactivo con 8 opciones:
```bash
python calculadora-aws.py
```

**Opciones disponibles:**
1. **Resumen General** - Vista rápida de todos los ambientes
2. **Análisis por Ambiente** - Detalles por Prod/Dev/QA/CentralHub
3. **Detalles de VMs** - Buscar VM específica por nombre
4. **Comparación de Costos** - Azure vs AWS
5. **Estimaciones con Descuentos** - OnDemand, 1yr, 3yr, Spot
6. **Top 10 VMs Más Costosas** - Ranking de máquinas
7. **Exportar a CSV** - Guardar análisis en archivo
8. **Salir**

### 2. **demo-calculadora.py** (Automática)
Genera reporte completo sin interacción:
```bash
python demo-calculadora.py
```

Produce:
- ✅ Resumen por ambiente
- ✅ Análisis detallado
- ✅ Escenarios de pricing
- ✅ Top 10 VMs
- ✅ Exporta en pantalla automáticamente

## 📊 Datos Incluidos

| Métrica | Valor |
|---------|-------|
| **Total VMs** | 112 |
| **Ambientes** | Prod (44), Dev (11), QA (18), CentralHub (15), Unknown (24) |
| **vCPUs totales** | 568 |
| **RAM total** | 1.9 TB |
| **Costo Azure anual** | $18,540.82 |
| **Costo AWS anual** | $160,920.00 |

## 🔧 Características

### Resumen General
- Distribución por ambiente
- Desglose por instancia AWS (t3.large, m6i.8xlarge, etc.)
- Recursos consumidos (vCPU, RAM)

### Análisis por Ambiente
- Costo total por ambiente
- Top 3 VMs más costosas
- Comparativa costo/ahorro por ambiente

### Búsqueda de VMs
- Buscar por nombre (búsqueda parcial)
- Ver detalles: tamaño Azure, equivalente AWS, vCPU, RAM
- Calcular ahorro individual

### Escenarios de Precio
```
OnDemand               $160,920/año
1yr Savings Plan (30%) $112,644/año
3yr Savings Plan (50%) $ 80,460/año
Spot Instances         $ 48,276/año
```

### Exportación
- Genera `analisis-migracion-aws.csv` con todos los datos
- Incluye columnas: Nombre, Azure Size, AWS Equiv, vCPUs, RAM, Costos, Ahorro

## 🚀 Uso Rápido

### Ejecutar demo automática
```bash
python demo-calculadora.py > reporte-migracion.txt
```

### Ejecutar calculadora interactiva
```bash
python calculadora-aws.py
```

### Exportar a CSV
```bash
# En calculadora interactiva:
# Seleccionar opción 7 (Exportar a CSV)
```

## 📈 Ejemplo: Opciones Principales

### Opción 1: Resumen
```
🏢 Prod     | VMs: 44 | Azure: $11,756.01/año | AWS: $72,120.00/año | Ahorro: -$60,363.99 (-513.5%)
🏢 Dev      | VMs: 11 | Azure: $1,591.55/año  | AWS: $20,040.00/año | Ahorro: -$18,448.45
```

### Opción 2: Búsqueda
```
Buscar VM: vm-gis-aes-prod

📌 vm-gis-aes-eastus2-prod-002
   Azure Size:       Standard_F32s_v2
   AWS Equivalent:   m6i.8xlarge
   vCPUs/RAM:        32/64 GB
   Azure Cost:       $2,471.58/año
   AWS Cost:         $14,400.00/año
```

### Opción 5: Escenarios
```
OnDemand              $160,920/año | Diferencia vs Azure: -$142,379
1yr Savings (30%)     $112,644/año | Diferencia vs Azure: -$94,103
3yr Savings (50%)     $80,460/año  | Diferencia vs Azure: -$61,919
```

## ⚠️ IMPORTANTE - Análisis de Precios

### Observación Crítica
**Los precios de AWS en los datos son muy altos:**
- Azure actual: $18,540.82/año
- AWS estimado: $160,920.00 (8.7x más caro)

### Posibles Causas:
1. Los precios podrían no ser competitivos
2. Revisar si el mapeo de instancias es correcto
3. Considerar:
   - **Downsizing**: Las VMs podrían ser más grandes de lo necesario
   - **Consolidación**: Agrupar workloads en menos instancias
   - **Reservations**: Aplicar descuentos de 3 años (50%)
   - **Spot Instances**: Para workloads no críticas

### Recomendaciones:
```
Scenario                    Annual Cost    Monthly Cost    vs Azure
✓ OnDemand                 $160,920        $13,410         -$142k (8.7x más caro)
✓ 1yr Savings (30%)        $112,644        $9,387          -$94k  (6.1x más caro)
✓ 3yr Savings (50%)        $80,460         $6,705          -$62k  (4.3x más caro)
✓ Spot (Best Case)         $48,276         $4,023          -$30k  (2.6x más caro)
```

**CONCLUSIÓN:** Incluso con Spot Instances (caso más optimista), AWS sigue siendo 2.6x más caro que Azure actual. Esto requiere investigación adicional sobre:
- Validación de precios de AWS
- Posible downsizing de instancias
- Optimización de recursos

## 🔍 Próximos Pasos

1. **Revisar Precios**: Validar que los precios de AWS sean correctos
2. **Analizar Uso Real**: Revisar métricas de CPU/RAM/Disk en Azure
3. **Optimizar Tamaños**: Considerar downsize de instancias overprovisioned
4. **Estrategia Reservaciones**: Aplicar 3yr commitments para mejor pricing
5. **Considerar Alternativas**: Evaluate Spot, Fargate, Lambda para aplicaciones adecuadas

## 📁 Archivos de Datos

- `vm-costs-azure-aws-mapping.json` - Datos de precios y mapeos (entrada)
- `analisis-migracion-aws.csv` - Exportación completa (salida)

---

**Última actualización:** Mayo 7, 2026  
**Base de datos:** 112 VMs | 4 Ambientes  
**Precios:** AWS us-east-2 OnDemand (2026-04-17)
