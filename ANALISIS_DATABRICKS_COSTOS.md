# 📊 Análisis de Costos de Databricks en Azure

**Fecha de Extracción:** 7 de mayo de 2026  
**Período Analizado:** Datos de Azure Cost Management - Abril 2026

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|--------|
| **Costo Total de Databricks** | **$47,990.62** |
| **Total de Registros** | **36,249** |
| **Ambientes Analizados** | 2 (Prod, QA) |
| **Workspaces Databricks** | 3 |
| **Grupos de Recursos** | 6 |

### Distribución por Ambiente
- **Producción (Prod):** $47,957.09 (99.93%)
- **Quality Assurance (QA):** $33.53 (0.07%)

---

## 💰 Desglose de Costos

### 1. **PRODUCCIÓN - $47,957.09**

#### Por Tipo de Computación (Meter)

| Tipo de Computación | Costo USD | % del Total |
|---------------------|-----------|------------|
| Premium Serverless SQL DBU | $24,984.04 | 52.1% |
| Premium All-Purpose Photon DBU | $14,480.56 | 30.2% |
| Premium All-purpose Compute DBU | $5,627.96 | 11.7% |
| D4 v2/DS4 v2 | $689.13 | 1.4% |
| D5 v2/DS5 v2 | $538.03 | 1.1% |
| Hot GRS Data Stored | $329.10 | 0.7% |
| Otros (Discos, Networking, etc.) | $708.27 | 1.6% |

#### Por Grupo de Recursos (Resource Group)

| Grupo de Recursos | Costo USD | % del Total | Descripción |
|-------------------|-----------|------------|-------------|
| rg-nomo-eastus2-prod-001 | $37,130.47 | 77.4% | Principal - Proyecto NOMO |
| rg-bireports-prod-002 | $8,177.97 | 17.1% | Reportes BI |
| rg-nomo-eastus2-prod-002 | $1,894.80 | 4.0% | Secondary - Proyecto NOMO |
| databricks-rg-adbworkspaceprod001-itolunyqkjh7w | $753.85 | 1.6% | Managed Resource Group |

#### Workspaces de Databricks en Prod

1. **adbworkspaceprod001** (rg-bireports-prod-002)
   - Ubicación: US East 2
   - Costo Total: $8,177.97
   - Usos Principales:
     - Premium All-purpose Compute DBU: $1,875.99
     - Premium SQL Compute Pro DBU: $8.51
     - Premium Interactive Serverless Compute: $2.90
     - Premium Automated Serverless Compute (Promo): $0.90
     - Networking & Storage: $0.05

2. **adbnomoeastus2prod001** (rg-nomo-eastus2-prod-001)
   - Ubicación: US East 2
   - Costo Total: $37,130.47
   - Usos Principales:
     - Premium Serverless SQL DBU: $8,328.01
     - Premium All-Purpose Photon DBU: $3,989.16
     - Premium Automated Serverless Compute: $27.09
     - Compute Instances: $1,227.16
     - Almacenamiento: $0.05

---

### 2. **QA - $33.53**

#### Por Tipo de Computación

| Tipo de Computación | Costo USD | % del Total |
|---------------------|-----------|------------|
| Standard Node | $13.12 | 39.1% |
| Premium Automated Serverless Compute (Promo) | $10.34 | 30.8% |
| Hot GRS Data Stored | $9.95 | 29.7% |
| Otros | $0.11 | 0.4% |

#### Por Grupo de Recursos

| Grupo de Recursos | Costo USD | % del Total |
|-------------------|-----------|------------|
| rg-nomom-eastus2-qa-001 | $16.52 | 49.3% |
| rg-nomo-eastus2-qa-001 | $10.34 | 30.8% |
| databricks-rg-adbworkspaceqa004-cu5rn7pfgeabe | $6.68 | 19.9% |

---

## 🔍 Análisis Detallado

### Componentes de Costo en Databricks

#### **1. DBU (Databricks Units) - El Mayor Costo**

Los DBU son la unidad de cobro principal en Databricks. Hay varios tipos:

- **Serverless SQL DBU**: Para consultas SQL interactivas
  - Costo: $24,984.04 (52.1% del total)
  - Uso: Análisis interactivo y reportes

- **All-Purpose Photon DBU**: Para trabajos de ETL y análisis
  - Costo: $14,480.56 (30.2% del total)
  - Uso: Procesamiento de datos y machine learning

- **All-Purpose Compute DBU**: Computación general
  - Costo: $5,627.96 (11.7% del total)
  - Uso: Notebooks y trabajos

#### **2. Infraestructura de Compute**

Instancias de máquinas virtuales para ejecutar workloads:
- D4/DS4 v2, D5/DS5 v2: ~$1,227
- Spot instances y otras: ~$227

#### **3. Almacenamiento y Networking**

- Hot GRS Data Stored: $329.10
- Data Transfer & NAT Gateway: Minimal

---

## 📋 Recursos Identificados

### Proyectos Principales

**1. NOMO (77.4% del costo - $37,130.47)**
- Workspace: adbnomoeastus2prod001
- Resource Group: rg-nomo-eastus2-prod-001
- Enfoque: Migración y procesamiento de datos
- Tags: environment:prod, project:nomo, service:migration

**2. SIRIUS/BI Reports (17.1% del costo - $8,177.97)**
- Workspace: adbworkspaceprod001
- Resource Group: rg-bireports-prod-002
- Enfoque: Reportes y análisis de BI
- Tags: environment:prod, project:sirius, service:reportsbi

**3. Otros (5.6% del costo)**
- Secondary prod resources y QA environments

---

## 🎯 Oportunidades de Optimización

### 1. **Serverless SQL (Principal Oportunidad de Ahorro)**
- **Costo Actual:** $24,984.04 (52.1%)
- **Recomendación:** 
  - Revisar consultas no optimizadas que pueden estar generando overhead
  - Considerar cambiar a All-Purpose compute para ciertas cargas
  - Implementar Query History y analytics para optimización

### 2. **All-Purpose Photon**
- **Costo Actual:** $14,480.56 (30.2%)
- **Recomendación:**
  - Evaluar si todos los clusters necesitan Photon (optimización de IO)
  - Considerar usar Standard Apache Spark para cargas que no requieran Photon
  - Implementar Job termination policies para evitar clusters idle

### 3. **Cluster Idle & Termination**
- **Recomendación:**
  - Implementar auto-termination policies (máximo 30 min de inactividad)
  - Revisar tags: muchos jobs de "predictive optimization" pueden estar completados

### 4. **Instance Types**
- **Costo Actual:** $689-$538 por tipo
- **Recomendación:**
  - Evaluar usar D2 v2 en lugar de D4/D5 para cargas ligeras
  - Considerar Spot instances para workloads batch

---

## 💡 Estimación de Ahorros Potenciales

| Medida | Ahorro Potencial | Complejidad |
|--------|------------------|------------|
| Optimizar Serverless SQL | 10-20% ($2,500-$5,000) | Media |
| Auto-termination de clusters | 15-25% ($7,000-$12,000) | Baja |
| Cambiar a Standard Spark (no Photon) | 5-10% ($725-$1,450) | Media |
| Usar Spot instances | 5-15% ($363-$1,089) | Alta |
| **TOTAL POTENCIAL** | **$10,588-$19,539** | — |

**Porcentaje de ahorro:** 22-41% del costo actual

---

## 📊 Datos Técnicos

### Columnas de Datos Disponibles
- ResourceId, ResourceType, ResourceLocation, ResourceGroupName
- ServiceName, ServiceTier, Meter
- Tags (con metadata de proyecto, cluster, job, etc.)
- CostUSD, Currency

### Archivos Generados
- `databricks-detallado-completo.csv`: 36,249 registros con todos los detalles
- `databricks-resumen-detallado.json`: Resumen estructurado para programación

---

## 📌 Próximos Pasos Recomendados

1. ✅ **Revisar Tags de Proyectos**
   - Validar que proyectos (NOMO, SIRIUS) son esenciales
   - Identificar si hay proyectos legacy que pueden ser eliminados

2. ✅ **Auditoría de Clusters**
   - Revisar todos los clusters "predictive optimization"
   - Verificar si están activos o pueden ser terminados

3. ✅ **Benchmarking de Queries**
   - Analizar query history en SQL endpoints
   - Optimizar queries más costosas

4. ✅ **Explorar Alternativas**
   - Comparar costo vs AWS Glue + Athena
   - Evaluar migración a AWS EMR para cargas específicas

---

## 📅 Historial de Cambios

| Fecha | Acción |
|-------|--------|
| 2026-05-07 | Extracción inicial de datos de Cost Management |
| | Análisis de costos por ambiente |
| | Generación de reporte consolidado |

---

*Reporte generado por: Databricks Cost Analysis Tool*  
*Datos de: Azure Cost Management - Abril 2026*
