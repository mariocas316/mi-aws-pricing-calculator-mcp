# Comparación: Inventario ARI vs Cost Management - AKS

## 📊 Resumen Ejecutivo

He comparado el **Inventario de Recursos Azure (ARI)** con los datos de **Cost Management** para validar si coinciden los costos y la configuración de AKS.

---

## 🔍 Hallazgos Principales

### **1. CLUSTERS**

| Fuente | Encontrado | Detalle |
|---|---|---|
| **TCO Excel (Esperado)** | 10 clusters | Planeados originalmente |
| **ARI (Inventario)** | 13 clusters | Reales en Azure |
| **Cost Management** | ~10 VMSS patterns | Datos de facturación |

**Clusters identificados en ARI:**
- Dev: 3 clusters (aks-be-k8, aks-bpi-mdso-k8, aks-uaa-k8)
- QA: 5 clusters (aks-be-k8, aks-bpi-mdso-k8 x2, aks-uaa-k8, aks-integrations)
- Prod: 5 clusters (aks-be-k8, aks-bpi-mdso-k8 x2, aks-uaa-k8, aks-integrations)
- CentralHub: 0 clusters

**Status (total ARI)**: ❌ No coincide - Hay **13 clusters en ARI vs 10 en TCO**

### **Clusters AKS en estado Running (marcados como OK)**

Estos son los clusters que se deben considerar como "bien" para la comparación operativa:

- aks-be-k8-eastus2-dev-002
- aks-be-k8-eastus2-qa-001
- aks-be-k8-eastus2-prod-001
- aks-bpi-mdso-k8-eastus2-qa-001
- aks-bpi-mdso-k8-eastus2-prod-001
- aks-bpi-mdso-k8-eastus2-prod-002
- aks-uaa-k8-eastus2-qa-001
- aks-uaa-k8-eastus2-prod-001
- aks-integrations-eastus2-qa-001
- aks-integrations-eastus2-prod-002

**Status (solo Running)**: ✅ Sí coincide con el objetivo de **10 clusters**.

### **Clusters fuera de alcance (Stopped)**

- aks-bpi-mdso-k8-eastus2-dev-001
- aks-uaa-k8-eastus2-dev-001
- aks-bpi-mdso-k8-eastus2-qa-002

---

### **2. NODOS (INSTANCIAS)**

| Fuente | Nodos | vCPUs | Status |
|---|---|---|---|
| **TCO Excel (Esperado)** | 76 nodos | 1,456 vCPU | Planificado |
| **ARI (Instancias actuales)** | 78 nodos | 1,368 vCPU | Real |
| **ARI (Target Nodes)** | 91 nodos | ~ | Deseado |
| **Cost Management (Facturado)** | 99 nodos | ~1,897 vCPU | Billable |

**Scope Running (recomendado para validación):**
- ARI Running Target Nodes: **76 nodos**
- ARI Running vCPU (Target Nodes): **1,362 vCPU**
- ARI Running VMSS Instances>0: **78 nodos**, **1,368 vCPU**
- Cost Management (Workers solo VMSS Running): **$30,179.56/mes**
- Cost Management (AKS + workers Running): **$41,066.78/mes**

**Detalles por ambiente:**

#### **Dev**
- ARI Instancias actuales: 7 nodos
- ARI Target Nodes: 16 nodos
- vCPUs: 90

#### **QA**
- ARI Instancias actuales: 29 nodos
- ARI Target Nodes: 43 nodos
- vCPUs: 284

#### **Prod**
- ARI Instancias actuales: 42 nodos
- ARI Target Nodes: 32 nodos
- vCPUs: 994

---

### **3. ANALISIS DE DISCREPANCIAS**

#### **Nodos: ARI vs Cost Management**
```
ARI (Instancias actuales):    78 nodos
Cost Management (Facturado):  99 nodos
Diferencia:                   +21 nodos (27% más en billing)
```

**Posibles causas:**
1. **Nodos temporales de escalado**: Cost Management incluye nodos que se escalaron temporalmente
2. **Nodos de reserva**: Pueden haber nodos parados que ARI no contabiliza pero se facturan
3. **Desactualización**: El inventario ARI puede estar desactualizado
4. **Máquinas virtuales adicionales**: Puede haber VMs no incluidas en VMSS que se facturan

#### **vCPUs: ARI vs Cost Management**
```
ARI (Actual):                 1,368 vCPU
ARI (Target):                 1,547 vCPU (estimado)
Cost Management (Facturado):  ~1,897 vCPU
TCO (Esperado):               1,456 vCPU
```

**Análisis:**
- ARI muestra 1,368 vCPU en nodos actuales
- El TCO esperaba 1,456 vCPU (88 vCPU menos)
- Cost Management factura ~1,897 vCPU (441 vCPU más)
- Razón: 99 nodos x 19.2 vCPU promedio = 1,897 vCPU

---

### **4. COSTOS**

| Fuente | Costo Mensual | Costo Anual | Status |
|---|---|---|---|
| **TCO (Planificado)** | $54,472 | $653,664 | Base |
| **Cost Management (Real)** | $48,147.28 | $577,767.36 | Actual |
| **Diferencia** | -$6,324.72 | -$75,896.64 | -11.6% |

**Desglose de costo real:**
- Worker Nodes (VMs): $37,260.06/mes
- Container Services: $10,887.22/mes
  - Container Registry: $365.87
  - Container Instances: $318.93
  - Defender for Cloud: $10,202.43

---

## 📋 Tabla Comparativa Final

```
PARAMETRO                   TCO PLANEADO    ARI ACTUAL    COST MGT      COINCIDE
─────────────────────────────────────────────────────────────────────────────────
Clusters                    10              13            ~10            ❌ No
Nodos (Instancias)          76              78            99             ⚠️ Parcial
Target Nodes                -               91            -              -
vCPUs (estimado)            1,456           1,368         1,897          ❌ No
Costo mensual               $54,472         -             $48,147.28     ⚠️ 11.6% menos
```

### **Tabla validada (solo AKS Running)**

```
PARAMETRO                   TCO OBJETIVO    RUNNING ARI    COST MGT RUNNING   COINCIDE
─────────────────────────────────────────────────────────────────────────────────────────
Clusters                    10              10             10 (VMSS match)    ✅ Sí
Nodos (Target/Activos)      76              76             78                 ⚠️ Parcial (+2)
vCPUs                       1,456           1,362-1,368    -                  ❌ No (-88 a -94)
Costo mensual AKS+Workers   -               -              $41,066.78         Referencia
```

---

## 🎯 Conclusiones

### ✅ **LO QUE COINCIDE:**
1. La distribución de clusters entre Dev/QA/Prod es similar
2. Los tipos de VM (D4, D16, D32, D64) son consistentes
3. Los nombres de VMSS coinciden entre ARI y Cost Management
4. Tomando solo estado Running, **sí coincide el objetivo de 10 clusters AKS**

### ❌ **LO QUE NO COINCIDE:**
1. **Cantidad de clusters (total inventario)**: 10 en TCO vs 13 en ARI (+3 clusters), aunque 10 están Running
2. **Nodos en billing total**: 76 esperado vs 99 facturado (+23 nodos)
3. **vCPUs Running**: 1,456 esperado vs 1,362-1,368 real Running (faltan 88-94 vCPU)
4. **Costo total histórico**: $48,147.28/mes (incluye elementos fuera de Running estricto)

### ⚠️ **EXPLICACIÓN PROBABLE:**
- El TCO fue planificado con **10 clusters y 76 nodos**
- El inventario ARI muestra **13 clusters activos**
- Cost Management factura **99 nodos** (algunos pueden ser réplicas, backups o escalado temporal)
- A pesar de tener **más nodos (+23), el costo es MENOR (-11.6%)** porque:
  - Los nodos adicionales son más pequeños (menor vCPU)
  - O hay descuentos por reservas aplicadas
  - O algunos nodos tienen menor tiempo de facturación

---

## 🔄 Recomendaciones

1. **Actualizar TCO** con datos reales del inventario ARI (13 clusters, 78 nodos activos)
2. **Investigar** por qué se facturan 99 nodos si solo hay 78 activos
3. **Validar** si los nodos extras están en estatus de escalado automático
4. **Recalcular** la migración AKS → EKS con los valores reales
5. **Usar baseline Running** para comité: 10 clusters, 76 target nodes, 1,362-1,368 vCPU, $41,066.78/mes

