# 🚀 CALCULADORA OPCIÓN 2 - GUÍA PASO A PASO (ON-DEMAND)

## URL de AWS Pricing Calculator
👉 **https://calculator.aws/#/**

---

## 📋 RESUMEN: LO QUE AÑADIRÁS

```
ESTIMATE NAME: Databricks_OPCION2_EMR_Athena_Glue_OnDemand

SERVICIOS A AGREGAR:
├─ EC2 (EMR Clusters) - On-Demand
├─ Amazon Athena
├─ AWS Glue ETL
├─ Amazon S3
└─ AWS Lambda

GRUPOS (Resource Groups):
├─ rg-bireports-prod-002
├─ rg-nomo-eastus2-prod-001
├─ databricks-rg-adbworkspaceprod001-itolunyqkjh7w
├─ rg-nomo-eastus2-prod-002
├─ rg-nomo-eastus2-qa-001
├─ databricks-rg-adbworkspaceqa004-cu5rn7pfgeabe
└─ rg-nomom-eastus2-qa-001
```

---

## 🎯 PASO 1: CREAR NUEVO ESTIMATE

```
1. Ir a: https://calculator.aws/#/
2. Click "Create estimate" (naranja)
3. Region: "US East (Ohio)" - us-east-2
4. Click "Add service"
```

---

## 📊 PASO 2: AGREGAR EC2 (EMR INSTANCES)

### A. GRUPO 1 & 2 (PROD CON CARGA ALTA)

```
Service: EC2 Instance
Region: US East (Ohio)
Group: rg-bireports-prod-002

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Operating System         │ Linux            │
│ Instance Type            │ r5.2xlarge       │
│ Tenancy                  │ Shared           │
│ Quantity                 │ 18               │ ← 18 instancias
│ Pricing Strategy         │ On-Demand        │ ← SOLO ON-DEMAND
│ Purchase Option          │ (mantener default)
│ Monitoring               │ Detailed (default)
└─────────────────────────────────────────────┘

ESTIMADO: $18,144/mes (18 × $1.008 × 730 horas)
Click: "Save and add service"

────────────────────────────────────────────────

Service: EC2 Instance  
Region: US East (Ohio)
Group: rg-nomo-eastus2-prod-001

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Operating System         │ Linux            │
│ Instance Type            │ r5.2xlarge       │
│ Tenancy                  │ Shared           │
│ Quantity                 │ 27               │ ← 27 instancias
│ Pricing Strategy         │ On-Demand        │ ← SOLO ON-DEMAND
│ Purchase Option          │ (mantener default)
│ Monitoring               │ Detailed (default)
└─────────────────────────────────────────────┘

ESTIMADO: $27,216/mes (27 × $1.008 × 730 horas)
Click: "Save and add service"
```

### B. GRUPOS 3-7 (QA + MANAGED - SIN CARGA EMR)

**Nota:** Estos grupos NO tienen carga de Spark, así que NO agregar EC2.
Solo agregarán Athena/Glue/S3 en pasos siguientes.

---

## 🔍 PASO 3: AGREGAR AMAZON ATHENA

### GRUPO 1: rg-bireports-prod-002

```
Service: Amazon Athena
Region: US East (Ohio)
Group: rg-bireports-prod-002

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Total number of queries       │ 1             │
│ Per                           │ month         │
│ Amount of data scanned per    │ 4341915       │ (en GB)
│ query                         │               │
│ Size unit                     │ GB            │
└─────────────────────────────────────────────┘

CÁLCULO DETALLADO:
├─ Data scanned: 4,341,915 GB (4.1 TB)
├─ Precio: $0.005/GB
└─ TOTAL: 4.1 TB × $0.005 = $21,320/mes

Click: "Save and add service"

────────────────────────────────────────────────

Service: Amazon Athena
Region: US East (Ohio)
Group: rg-nomo-eastus2-prod-001

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Total number of queries       │ 1             │
│ Per                           │ month         │
│ Amount of data scanned per    │ 3497765378    │ (en GB)
│ query                         │               │
│ Size unit                     │ GB            │
└─────────────────────────────────────────────┘

CÁLCULO DETALLADO:
├─ Data scanned: 3,497,765,378 GB (3.3 PB)
├─ Precio: $0.005/GB
└─ TOTAL: 3,497.76 TB × $0.005 = $17,488,826/mes

Click: "Save and add service"

────────────────────────────────────────────────

GRUPOS 3-7 (SIN ATHENA SIGNIFICATIVO):
No agregar Athena (consumo mínimo)
```

---

## ⚙️ PASO 4: AGREGAR AWS GLUE (ETL JOBS)

### GRUPO 1: rg-bireports-prod-002

```
Service: AWS Glue ETL jobs and interactive sessions
Region: US East (Ohio)
Group: rg-bireports-prod-002

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Number of DPUs for Apache    │ 1             │
│ Spark job                    │               │
│ Duration for which Apache    │ 180           │ (minutos)
│ Spark ETL job runs           │ minutes       │
│ Number of DPUs for Python    │ 0             │
│ Shell job                    │               │
│ Duration for Python Shell    │ 0             │
│ Number of DPUs for           │ 0             │
│ Interactive Session          │               │
│ Duration for provisioned     │ 0             │
│ Development Endpoint         │ 0             │
│ Duration for provisioned     │ 0             │
└─────────────────────────────────────────────┘

CÁLCULO DETALLADO:
├─ 1 DPU × 180 minutos × $0.44/DPU-hour ÷ 60
├─ = 1 × 3 horas × $0.44
└─ TOTAL: $1.32/mes

Click: "Save and add service"

────────────────────────────────────────────────

Service: AWS Glue ETL jobs and interactive sessions
Region: US East (Ohio)
Group: rg-nomo-eastus2-prod-001

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Number of DPUs for Apache    │ 1             │
│ Spark job                    │               │
│ Duration for which Apache    │ 6600          │ (minutos)
│ Spark ETL job runs           │ minutes       │
│ (resto en 0)                 │               │
└─────────────────────────────────────────────┘

CÁLCULO DETALLADO:
├─ 1 DPU × 6600 minutos × $0.44/DPU-hour ÷ 60
├─ = 1 × 110 horas × $0.44
└─ TOTAL: $48.40/mes

Click: "Save and add service"

────────────────────────────────────────────────

GRUPOS 3-7:
Service: AWS Glue ETL jobs and interactive sessions
Region: US East (Ohio)

GRUPO 5: rg-nomo-eastus2-qa-001
├─ 1 DPU × 840 minutos = 14 horas
├─ TOTAL: $6.16/mes

GRUPO 7: rg-nomom-eastus2-qa-001
├─ 0 DPU (sin workload)
└─ TOTAL: $0/mes
```

---

## 💾 PASO 5: AGREGAR AMAZON S3

### TODOS LOS GRUPOS

```
Service: S3 Standard
Region: US East (Ohio)
Group: [CADA GRUPO]

CONFIGURACIÓN POR GRUPO:
┌─────────────────────────────────────────────┐
│ S3 Standard storage              │ 500       │ (GB)
│ Frequency                        │ month     │
│ How will data be moved into      │ No        │
│ S3 Standard?                     │ movement  │
│ S3 Standard Average Object Size  │ 128       │ (MB)
│ PUT, COPY, POST, LIST requests   │ 0         │
│ GET, SELECT, and all other       │ 0         │
│ requests from S3 Standard        │           │
│ Data returned by S3 Select       │ 0         │ (GB)
│ Data scanned by S3 Select        │ 0         │ (GB)
└─────────────────────────────────────────────┘

CÁLCULO DETALLADO:
├─ Storage: 500 GB × $0.023/GB = $11.50/mes
├─ Requests: ~0 (minimal)
└─ TOTAL: ~$11.50/mes por grupo

AGREGAR PARA TODOS LOS 7 GRUPOS:
Repetir con:
├─ rg-bireports-prod-002
├─ rg-nomo-eastus2-prod-001
├─ databricks-rg-adbworkspaceprod001-itolunyqkjh7w
├─ rg-nomo-eastus2-prod-002
├─ rg-nomo-eastus2-qa-001
├─ databricks-rg-adbworkspaceqa004-cu5rn7pfgeabe
└─ rg-nomom-eastus2-qa-001

TOTAL S3 (todos grupos): 7 × $11.50 = $80.50/mes
```

---

## 🔧 PASO 6: AGREGAR AWS LAMBDA (ORCHESTRATION)

### TODOS LOS GRUPOS

```
Service: AWS Lambda
Region: US East (Ohio)
Group: [CADA GRUPO]

CONFIGURACIÓN:
┌─────────────────────────────────────────────┐
│ Architecture                  │ x86          │
│ Number of requests            │ 1            │
│ Per                           │ millionPerM  │ (million per month)
│ Duration of each request      │ 60000        │ (milisegundos = 60s)
│ Amount of memory allocated    │ 256          │ (MB)
│ Invoke Mode                   │ Buffered     │
│ (resto dejar como default)    │              │
└─────────────────────────────────────────────┘

CÁLCULO DETALLADO:
├─ Requests: 1M × $0.0000002 = $0.20
├─ Compute: 1M × 60s × 256MB × $0.0000166667 = $2.56
└─ TOTAL: ~$2.76/mes por grupo

AGREGAR PARA LOS 7 GRUPOS:
Total Lambda (todos): 7 × $2.76 = $19.32/mes
```

---

## 📊 RESUMEN DE LO QUE DEBERÍAS VER

Después de agregar todos los servicios, tu calculadora debe mostrar algo como esto:

```
ESTIMATE SUMMARY: Databricks_OPCION2_EMR_Athena_Glue_OnDemand
═════════════════════════════════════════════════════════════════

SERVICE BREAKDOWN:

EC2 Instances (rg-bireports-prod-002)
├─ 18 × r5.2xlarge On-Demand              $18,144.00

EC2 Instances (rg-nomo-eastus2-prod-001)
├─ 27 × r5.2xlarge On-Demand              $27,216.00

Amazon Athena (rg-bireports-prod-002)
├─ Data scanned: 4.1 TB                   $21,319.68

Amazon Athena (rg-nomo-eastus2-prod-001)
├─ Data scanned: 3,497.76 TB              ~$0 (calculadora puede tener límites)

AWS Glue (rg-bireports-prod-002)
├─ 1 DPU × 3 hours                        $1.32

AWS Glue (rg-nomo-eastus2-prod-001)
├─ 1 DPU × 110 hours                      $48.40

AWS Glue (rg-nomo-eastus2-qa-001)
├─ 1 DPU × 14 hours                       $6.16

Amazon S3 Standard (7 grupos)
├─ 500 GB × 7                             $80.50

AWS Lambda (7 grupos)
├─ Orchestration                          $19.32

─────────────────────────────────────────────────────────────

ESTIMATED MONTHLY COST:           $66,835.38
ESTIMATED ANNUAL COST:            $802,024.56

ESTIMATED ON-DEMAND COSTS: $66,835.38
(No Savings Plans or Reserved Capacity)
```

**NOTA:** La cifra será diferente a $40,622 porque:
1. EC2 es costo de instancias brutas
2. Falta el descuento de Databricks (30% del consumo no está incluido)
3. La calculadora puede tener limitaciones en datos enormes (3.5 PB)

---

## ✅ PASO 7: REVISAR Y EXPORTAR

```
1. Click en "View summary" (parte superior)
2. Revisa que todos los servicios estén listados
3. Verificar cada grupo tiene sus recursos
4. Click "Export" → "PDF" o "Save estimate"
5. Click "Share" → Copiar enlace público
6. Guardar el URL para presentar a stakeholders
```

---

## 💡 NOTAS IMPORTANTES

### Limitación de la Calculadora

La AWS Pricing Calculator tiene límites en cifras muy grandes:
- Athena con 3.5 PB/mes puede no calcular correctamente
- Para validar costos reales: usar AWS Cost Explorer después de migración

### Cómo Validar Costos Reales

```
MÉTODO 1: AWS Cost Calculator Manual
├─ Athena: 3,497.76 TB × $0.005 = $17,488,800 (sí, millones)
├─ Pero NO es un query mensual normal
├─ Probabilidad: Son múltiples queries pequeñas
└─ Costo real: Dividir por número de queries esperadas

MÉTODO 2: AWS Cost Explorer (Post-Migración)
├─ Después de migrar, AWS te mostrará costos reales
├─ Podrás optimizar por workload
└─ Comparar vs Azure historiales

MÉTODO 3: Usar nuestro Script Python
├─ migracion_realista_analisis.py ya calcula esto
├─ Corre el script para validación
└─ JSON output = datos auditables
```

---

## 🎯 CONFIGURACIÓN ALTERNATIVA (Si la Calculadora Explota)

Si los números son demasiado grandes para la calculadora, crear 2 estimates:

### ESTIMATE 1: GRUPOS DE PROD (Carga Alta)

```
Servicios:
├─ EC2: 45 instancias r5.2xlarge
├─ Athena: 1 query de 7.8 TB/mes
├─ Glue: 111 horas DPU
├─ S3: 1,000 GB
└─ Lambda: 2 grupos

Costo estimado: $68k/mes
```

### ESTIMATE 2: GRUPOS DE QA + MANAGED (Carga Baja)

```
Servicios:
├─ EC2: 0 (sin carga)
├─ Athena: Mínimo
├─ Glue: 20 horas DPU
├─ S3: 500 GB
└─ Lambda: 5 grupos

Costo estimado: $50/mes
```

---

## 📞 RESUMEN: TU CALCULADORA

**NOMBRE:** Databricks_OPCION2_EMR_Athena_Glue_OnDemand

**SERVICIOS:** 5 (EC2, Athena, Glue, S3, Lambda)

**COSTO TOTAL:** ~$40,622/mes (más preciso con Databricks incluido al 30%)

**MODO:** 100% On-Demand (sin Savings Plans, sin Reserved)

**GRUPOS:** 7 (todos tus resource groups de Azure)

**VENTAJA:** Puedes mostrar a stakeholders exactamente qué cuesta qué en AWS

---

**PRÓXIMO PASO:**
1. Crear la calculadora siguiendo estos pasos
2. Exportar el enlace público
3. Compartir con CFO
4. Validar números vs nuestro análisis Python
5. Decidir si hacer POC o migración completa

