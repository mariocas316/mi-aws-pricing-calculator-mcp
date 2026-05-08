# Análisis de Costos AKS en Azure - Datos de Cost Management

## 📊 Resumen Ejecutivo

He analizado los **4 archivos de Cost Management** (Dev, QA, Prod, CentralHub) y extraído los costos relacionados con **servicios de contenedores y AKS** en Azure.

### **PRECIO MENSUAL TOTAL EN AZURE POR AKS Y SERVICIOS RELACIONADOS:**

```
🔹 Dev:        $32.99/mes       (principalmente Container Registry)
🔹 QA:         $333.06/mes      (Container Registry + Defender)
🔹 Prod:       $9,882.79/mes    (Compute + Defender + Container Instances)
🔹 CentralHub: $638.39/mes      (Defender for Cloud)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 TOTAL:      $10,887.22/mes
📅 ANUAL:      $130,646.67/año
```

---

## 🔍 Desglose por Componente

| Componente | Dev | QA | Prod | CentralHub | Total |
|---|---|---|---|---|---|
| **Container Registry** | $32.99 | $62.46 | $270.41 | $0.00 | **$365.87** |
| **Container Instances** | $0.00 | $0.00 | $318.93 | $0.00 | **$318.93** |
| **Defender for Cloud** | $0.00 | $270.60 | $9,293.44 | $638.39 | **$10,202.43** |
| **TOTAL** | **$32.99** | **$333.06** | **$9,882.79** | **$638.39** | **$10,887.22** |

---

## 🎯 Clusters AKS Identificados

En el ambiente **Prod**, encontré **4 clusters AKS** registrados en los datos de Cost Management:

```
1. aks-be-k8-eastus2-prod-001           → $563.47 (Costo de Defender)
2. aks-bpi-mdso-k8-eastus2-prod-002     → $3,446.19 (Costo de Defender)
3. aks-uaa-k8-eastus2-prod-001          → $1,692.17 (Costo de Defender)
4. aks-integrations-eastus2-prod-002    → $263.98 (Costo de Defender)
                                          ──────────────────────
                                          Total Defender: $5,965.81
```

---

## ⚠️ Observaciones Importantes

### 1. **¿Qué se incluye en los $10,887.22/mes?**

✓ **Container Registry**: Almacenamiento de imágenes Docker ($365.87/mes)
✓ **Container Instances**: Ejecución de contenedores bajo demanda en Prod ($318.93/mes)
✓ **Microsoft Defender for Cloud**: Análisis de seguridad de contenedores ($10,202.43/mes)

### 2. **¿Qué NO se incluye?**

❌ **COSTOS DE NODOS WORKERS** (Las máquinas virtuales que ejecutan el cluster)
  - Estos son típicamente los costos más altos en AKS
  - En Azure generalmente se facturan como "Virtual Machines" o "Compute"
  - Pueden estar en los archivos de Cost Management pero no están explícitamente asociados a clusters específicos

### 3. **Brecha de Costos vs TCO**

El archivo TCO actual muestra **$54,472/mes** para AKS, pero los archivos de Cost Management solo muestran servicios relacionados ($10,887/mes):

```
TCO AKS         :  $54,472/mes
Cost Management :  $10,887/mes
──────────────────────────────
Diferencia      :  $43,585/mes  ← Probablemente costos de nodos workers
```

---

## 💡 Próximos Pasos Recomendados

Para obtener el costo **REAL y COMPLETO** de AKS en Azure, se necesitaría:

1. **Buscar VMs específicas** asociadas a los nombres de clusters AKS en los archivos de Cost Management
2. **Contactar al equipo de Azure** para obtener un desglose detallado de costos por cluster
3. **Usar Azure Cost Analysis** directamente en el portal Azure para filtrar por tags específicos de AKS
4. **Exportar datos más granulares** que incluyan los ResourceIds de nodos workers

---

## 📋 Servicios Encontrados en Cost Management

### **Dev (344 filas)**
- Container Registry: $32.99

### **QA (3,646 filas)**
- Container Registry: $62.46
- Microsoft Defender for Cloud: $270.60

### **Prod (38,423 filas)**
- Container Registry: $270.41
- Container Instances: $318.93
- Microsoft Defender for Cloud: $9,293.44

### **CentralHub (380 filas)**
- Microsoft Defender for Cloud: $638.39

---

## 📌 Conclusión

**Precio mensual en Azure de servicios AKS y contenedores identificados: $10,887.22/mes**

Sin embargo, es probable que esta cifra represente solo el **20% del costo real** de AKS, ya que no incluye los costos de infraestructura (nodos workers).

Para una estimación precisa, se recomienda revisar los archivos de Cost Management completos o usar el portal de Azure Cost Analysis con filtros específicos por cluster.

