# 🧮 CALCULADORA AWS - MIGRACIÓN DESDE AZURE

## 📌 Resumen Rápido

He creado una **calculadora completa** para analizar la migración de 112 VMs de Azure a AWS usando datos reales de costos.

### ⚡ Inicio Rápido

```bash
# Opción 1: Calculadora interactiva
python calculadora-aws.py

# Opción 2: Reporte automático
python demo-calculadora.py

# Opción 3: Análisis de optimización
python optimizador-costos.py
```

---

## 🎯 Hallazgos Clave

| Métrica | Valor | Status |
|---------|-------|--------|
| **Total VMs** | 112 | ✅ |
| **vCPUs** | 568 | ✅ |
| **RAM** | 1.9 TB | ✅ |
| **Azure Actual** | $1,545.07/mes ($18,540.82/año) | Base |
| **AWS OnDemand** | $160,920/año | ❌ 8.7x más caro |
| **AWS con 3yr Reserved** | $80,460/año | ❌ 4.3x más caro |
| **AWS con Spot** | $48,276/año | ❌ 2.6x más caro |

**Conclusión:** ❌ Azure es más económico - incluso con máximas optimizaciones

---

## 📊 4 Herramientas Principales

### 1️⃣ **Calculadora Interactiva** 
**Archivo:** `calculadora-aws.py` (13 KB)

```bash
python calculadora-aws.py
```

**Menú con 8 opciones:**
- Resumen general
- Análisis por ambiente
- Búsqueda de VMs
- Comparación de costos
- Estimaciones con descuentos
- Top 10 máquinas costosas
- Exportación a CSV
- Salir

**Ideal para:** Exploración interactiva, análisis ad-hoc, búsquedas específicas

---

### 2️⃣ **Reporte Automático**
**Archivo:** `demo-calculadora.py` (5 KB)

```bash
python demo-calculadora.py
# o guardar en archivo
python demo-calculadora.py > reporte-migracion.txt
```

**Genera:**
- Resumen por ambiente
- Análisis detallado de costos
- Escenarios de pricing
- Top 10 VMs más costosas
- Distribución de instancias

**Ideal para:** Reportes ejecutivos, documentación, auditoría

---

### 3️⃣ **Auditoría de Precios**
**Archivo:** `audit-precios.py` (4 KB)

```bash
python audit-precios.py
```

**Valida:**
- Precios competitivos vs mercado
- Anomalías en pricing
- Instancias overprovisioned

**Resultado:** ✅ Los precios son correctos y competitivos

---

### 4️⃣ **Optimizador de Costos**
**Archivo:** `optimizador-costos.py` (7 KB)

```bash
python optimizador-costos.py
```

**Identifica:**
- Instancias overprovisioned (28 máquinas)
- Estrategia de pricing por ambiente
- Consolidación de máquinas pequeñas
- Plan de migración en 4 fases

**Ahorro potencial:** $97,032/año (pero aún 244% más caro que Azure)

---

## 📈 Análisis Detallado por Ambiente

```
Prod:       44 VMs | Azure: $11,756/año  | AWS: $72,120/año  | Diferencia: +$60,364
Dev:        11 VMs | Azure: $1,591/año   | AWS: $20,040/año  | Diferencia: +$18,449
QA:         18 VMs | Azure: $811/año     | AWS: $20,760/año  | Diferencia: +$19,949
CentralHub: 15 VMs | Azure: $2,836/año   | AWS: $13,680/año  | Diferencia: +$10,844
Unknown:    24 VMs | Azure: $1,546/año   | AWS: $34,320/año  | Diferencia: +$32,774
────────────────────────────────────────────────────────────────────────────
TOTAL:     112 VMs | Azure: $18,540/año  | AWS: $160,920/año | Diferencia: +$142,379
```

Nota de consistencia de costos:
- Azure total anual real: $18,540.82
- Azure equivalente mensual: $1,545.07
- AWS On-Demand anual: $160,920
- AWS On-Demand mensual: $13,410

---

## 💰 Estrategias de Pricing Recomendadas

| Ambiente | Estrategia | Descuento | Costo Anual |
|----------|-----------|-----------|------------|
| **Prod** | 3yr Reserved | 50% | $36,060 |
| **Dev** | Spot + OnDemand Mix | 60% | $12,024 |
| **QA** | Spot Instances | 70% | $6,228 |
| **CentralHub** | 1yr Savings | 30% | $9,576 |
| **TOTAL** | Optimizado | - | **$63,888** |

**Aún así:** AWS optimizado = 244% más caro que Azure

---

## 🔍 Top 5 VMs Más Costosas

| # | Máquina | vCPU | RAM | Azure/año | AWS | |
|---|---------|------|-----|-----------|-----|---|
| 1 | vm-gis-aes-eastus2-prod-002 | 32 | 64GB | $2,472 | m6i.8xlarge | |
| 2 | vm-gis-aes-eastus2-prod-003 | 32 | 64GB | $2,466 | m6i.8xlarge | |
| 3 | vm-bp-uaa-eastus2-dev-002 | 32 | 128GB | $1,418 | m6i.8xlarge | |
| 4 | vm-gisdsk-eastus2-centralhub-003 | 8 | 28GB | $806 | t3.2xlarge | |
| 5 | vm-gis-nss-eastus2-prod-001 | 8 | 32GB | $731 | t3.2xlarge | |

---

## ⚠️ Observaciones Importantes

### Azure es MUCHO más barato
- $18,540.82/año en Azure actual
- $160,920/año en AWS OnDemand (8.7x más caro)
- Incluso con máximas optimizaciones sigue siendo 2.6x más caro

### Posibles Causas:
1. **Azure bien precificado:** Posible que tengan descuentos corporativos
2. **Error en datos:** Validar costos de Azure contra facturas reales
3. **Licencias Windows:** Si incluye SQL Server/Windows, podría justificar Azure
4. **Workloads específicas:** Si tienen requisitos de AWS (AI/ML, compliance, etc.)

---

## 🚀 Recomendaciones Inmediatas

### ✅ HACER AHORA
- [ ] Validar que los costos de Azure en los datos son correctos
- [ ] Confirmar si la migración a AWS es obligatoria o opcional
- [ ] Si es obligatoria, aplicar 3yr Reserved Instances

### ⚠️ REVISAR
- [ ] Por qué Azure es 8.7x más barato
- [ ] Si hay descuentos Azure no aplicados
- [ ] Si hay instancias overprovisioned (28 VMs identificadas)

### 💡 SI SE MIGRA A AWS
1. Aplicar 3yr Reserved en Prod (máximo ahorro)
2. Usar Spot en QA/Dev (70% descuento)
3. Downsizar 28 VMs overprovisioned
4. Consolidar aplicaciones pequeñas

---

## 📁 Archivos Generados

### Herramientas (Esta Sesión)
```
✅ calculadora-aws.py           (13 KB) - Calculadora interactiva
✅ demo-calculadora.py          (5 KB)  - Reporte automático
✅ audit-precios.py             (4 KB)  - Validación de precios
✅ optimizador-costos.py        (7 KB)  - Recomendaciones de ahorro
✅ USO_CALCULADORA.md           - Guía de uso detallada
✅ RESUMEN_EJECUTIVO.md         - Resumen ejecutivo completo
✅ README.md                    - Este archivo
```

### Datos de Entrada
```
📊 vm-costs-azure-aws-mapping.json  - 112 VMs con costos comparativos
```

### Salidas Generadas
```
📊 analisis-migracion-aws.csv       - Exportación completa (generado por calculadora)
📊 vm-ondemand-detailed-result.json - Resultado de carga MCP de 111 VMs standalone
```

---

## 🎓 Ejemplos de Uso

### Generar reporte completo
```bash
python demo-calculadora.py > reporte-$(date +%Y%m%d).txt
```

### Ejecutar calculadora y seleccionar opción 1
```bash
python calculadora-aws.py
# Presionar 1 para ver resumen general
```

### Ver recomendaciones de optimización
```bash
python optimizador-costos.py
```

### Exportar a CSV
```bash
python calculadora-aws.py
# Seleccionar opción 7 en el menú
```

---

## 📞 Documentación Relacionada

- [USO_CALCULADORA.md](USO_CALCULADORA.md) - Guía completa de uso
- [RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md) - Análisis ejecutivo detallado
- [CALCULADORA_AWS_README.md](CALCULADORA_AWS_README.md) - Documentación anterior

---

## 🔧 Requisitos

- Python 3.6+
- pandas (incluida en el ambiente)
- json (estándar)
- csv (estándar)

---

## ❓ Preguntas Frecuentes

**P: ¿Por qué AWS es tan caro?**
A: Se está comparando Azure (bien precificado) vs AWS OnDemand. Con reservaciones baja significativamente.

**P: ¿Qué pasa si migro?**
A: Costo aumentaría de $18,540 a mínimo $48,276/año (con Spot) = +$29,735/año adicional.

**P: ¿Hay razones para migrar entonces?**
A: Sí, si hay requirements de negocio (compliance, features, consolidación global, etc.)

**P: ¿Cómo reduzco costos en AWS?**
A: Aplicar estrategias por ambiente (3yr Prod, Spot QA/Dev, 1yr balance CentralHub).

---

## 📊 Datos Base

- **Total VMs Analizadas:** 112
- **Ambientes:** Prod (44), Dev (11), QA (18), CentralHub (15), Unknown (24)
- **Distribución AWS:** t3.large (35), t3.xlarge (20), t3.2xlarge (18), c6i.large (22), etc.
- **Precios:** AWS us-east-2 OnDemand (2026-04-17)
- **Última actualización:** Mayo 7, 2026

---

## 💬 Soporte

Para más información, consulte:
1. Ejecutar `python calculadora-aws.py` para explorar interactivamente
2. Ver [RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md) para análisis completo
3. Revisar [USO_CALCULADORA.md](USO_CALCULADORA.md) para guía de uso

---

**Status:** ✅ Calculadora completa y lista para usar
