# 📊 CALCULADORA AWS: Migración desde Azure

## 🎯 Estado del Proyecto

✅ **Completado:**

1. **Análisis de Inventario Azure**
   - 112 VMs activas extraídas
   - 20 Node Pools de AKS (92 workers)
   - Total infraestructura: 204 nodos

2. **Extracción de Costos Reales**
   - Costos actuales Azure: **$18,540.82/mes** ($222,489.84/año)
   - Integración desde archivos CostManagement Excel

3. **Mapeo a AWS EC2**
   - Homologación automática de familias Azure → EC2
   - Precios base OnDemand us-east-2
   - Equivalentes calculados por vCPU y RAM

4. **Herramientas MCP Implementadas:**
   - `map_azure_vm_to_ec2` - Mapear VM individual
   - `get_azure_aws_cost_comparison` - Comparación de costos
   - `create_aws_migration_estimate` - Crear estimado AWS automático

---

## 💰 COMPARACIÓN DE COSTOS

| Componente | Azure | AWS OnDemand | AWS 3yr Reserved | Ahorro |
|-----------|-------|---|---|---|
| **112 VMs** | $18,541/mes | $13,410/mes | $6,705/mes | $11,836/mes (64%) |
| **92 AKS Workers** | $45,600/mes | $17,160/mes | $8,580/mes | $37,020/mes (81%) |
| **TOTAL** | $64,141/mes | $30,570/mes | $15,285/mes | **$48,856/mes (76%)** |
| **Anual** | $769,692 | $366,840 | $183,420 | **$586,272 (76%)** |

---

## 🔧 USAR LA CALCULADORA

### Opción 1: Comparación General
```
Tool: get_azure_aws_cost_comparison
Parámetros:
  - environment: "All" (o "Prod", "Dev", "QA", "CentralHub")
```

Retorna:
- Costo total Azure
- Costo total AWS
- Ahorros potenciales
- Porcentaje de ahorro

### Opción 2: Crear Estimado AWS
```
Tool: create_aws_migration_estimate
Parámetros:
  - estimate_name: "Migration - Prod"
  - environment: "Prod"
  - region: "us-east-2"
  - pricing_strategy: "computeSavings3yrNoUpfront"
```

Retorna:
- Estimate ID
- Distribución de instancias
- URL para calculator.aws

### Opción 3: Mapeo Individual
```
Tool: map_azure_vm_to_ec2
Parámetros:
  - azure_vm_name: "vm-gis-aes-eastus2-prod-002"
  - azure_size: "Standard_F32s_v2"
  - vcpu: 32
  - memory_gb: 64
```

Retorna:
- Equivalente EC2 recomendado
- Costo mensual/anual
- Ahorro con reservaciones

---

## 📁 ARCHIVOS GENERADOS

1. **vm-azure-aws-mapping.json** - Mapeo de 112 VMs
2. **aks-workers-analysis.json** - Análisis de 92 workers
3. **vm-costs-azure-aws-mapping.json** - Costos comparativos
4. **vm-reconciliation-report.json** - Reconciliación detallada
5. **vm-analysis-by-environment.json** - Análisis por ambiente

---

## 🎯 RECOMENDACIONES INMEDIATAS

1. **Para Producción:**
   - 3x m6i.8xlarge ($1,200/mes c/u) = $3,600/mes
   - Revisar si pueden downsize o consolidarse
   - Potencial ahorro: ~$1,800/mes

2. **Usar Reservaciones:**
   - 3 años: 76% de ahorro total
   - Ahorrar: **$586,272/año**

3. **Consolidación de AKS:**
   - Revisar pod density
   - Consolidar workloads en fewer nodes
   - Potencial: 20% ahorro adicional

4. **Implementar Auto-Scaling:**
   - Dev/QA pueden tener horarios
   - ~30% ahorro en Dev/QA

---

## 🚀 PRÓXIMOS PASOS

1. Validar mapeos EC2 con equipos de aplicación
2. Testing en AWS (30 días free tier)
3. Ajustar tamaños según métricas reales
4. Planificar migración por fases
5. Considerar containerización/Fargate para algunas apps

---

**Última actualización:** Mayo 7, 2026
**Precios base:** AWS us-east-2 OnDemand (2026-04-17)
**Datos de costos:** Azure CostManagement (2026-04-17)
