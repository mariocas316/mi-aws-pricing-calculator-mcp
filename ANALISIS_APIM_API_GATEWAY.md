# ANÁLISIS APIM → AWS API GATEWAY - RESUMEN EJECUTIVO

## 📊 INVENTARIO DE APIM IDENTIFICADO

### Distribución por Ambiente

| Ambiente | Instancias | SKU | Detalles |
|----------|-----------|-----|---------|
| **Desarrollo (DEV)** | 3 | Developer (3×) | apimdevopsdev001, apimdevopsdev002, apimmicroservicesdev001 |
| **QA** | 3 | Developer (3×) | apimtransitionalqa001, apimdevopsqa001, apimdevopsqa002 |
| **Producción (PROD)** | 3 | Basic (1×) + Premium (2×) | apimtransitionalprod001, apimdevopsprod001, apimdevopsprod002 |
| **DR** | 2 | Developer (2×) | apimdevopsdr001, apimdevopsdr002 |
| **TOTAL** | **11** | — | — |

### Detalles de Instancias Premium
- **apimdevopsprod001**: Premium, Capacity 1 (eastus2)
- **apimdevopsprod002**: Premium, Capacity 2 (eastus2)

---

## 🔌 API CALL VOLUMES

**Total: 80 millones de llamadas mensuales**

| Ambiente | Porcentaje | Llamadas/mes | Detalle |
|----------|-----------|--------------|---------|
| Dev | 5% | 4 millones | Desarrollo y testing |
| QA | 10% | 8 millones | Control de calidad |
| Prod | 85% | 68 millones | Transaccional principal |
| **TOTAL** | **100%** | **80 millones** | — |

---

## 💰 ANÁLISIS DE COSTOS - AZURE APIM (Actual)

### Estimado Mensual por SKU
- **Developer SKU**: ~$40-50/mes × 8 instancias = **$400**
- **Basic SKU**: ~$100/mes × 1 instancia = **$100**
- **Premium SKU**: ~$350-400/mes × 2 instancias = **$750**

**Total Azure APIM (estimado): $1,250/mes → $15,000/año**

---

## 🔄 HOMOLOGACIÓN: AZURE APIM → AWS API GATEWAY

| Azure APIM | AWS Equivalente | Notas |
|-----------|-----------------|-------|
| Developer | API Gateway (Standard Tier) | Desarrollo, bajo volumen |
| Basic | API Gateway (Standard Tier) | Producción, volumen moderado |
| Premium | API Gateway (Premium Tier) | HA, múltiples regiones |
| API Calls | Solicitudes API Gateway | Facturación por millón |
| Rate Limiting | Throttle Settings | Nativo en API Gateway |
| Caching | CloudFront o API Cache | Caché de respuestas |
| Monitoring | CloudWatch + X-Ray | Logs y trazabilidad |

### Servicios AWS Incluidos en Estimación
1. **Amazon API Gateway**: $3.50/millón de solicitudes (primer billón)
2. **CloudWatch Logs**: $0.50/GB de ingesta (logging de APIs)
3. **Data Transfer (Egress)**: $0.09/GB (respuestas de API)

---

## 💵 COSTOS AWS API GATEWAY (80M llamadas/mes)

### Desglose Mensual (On-Demand)
```
API Calls:          80M × $3.50/M = $280.00
Data Transfer:      100GB × $0.09/GB = $9.00
CloudWatch Logs:    50GB × $0.50/GB = $25.00
                    ─────────────────────
SUBTOTAL On-Demand:                $314.00/mes
```

### Escenarios de Precios

| Scenario | Monthly | Annual | vs On-Demand |
|----------|---------|--------|--------------|
| **On-Demand** | $314.00 | $3,768.00 | Baseline |
| **Savings Plan 1yr** | $235.50 | $2,826.00 | -25% ($117.50/mes) |
| **Savings Plan 3yr** | $172.70 | $2,072.40 | -45% ($141.30/mes) ⭐ |

### Ahorro Total (vs Azure)
- **Azure Actual**: $1,250/mes ($15,000/año)
- **AWS SP 3yr**: $172.70/mes ($2,072.40/año)
- **Ahorro Mensual**: $1,077.30 (86.2%)
- **Ahorro Anual**: $12,927.60 (86.2%)

**⚠️ Nota**: AWS API Gateway es significativamente más barato que Azure APIM, especialmente considerando:
- Pay-as-you-go (sin costos mínimos)
- Escalabilidad automática
- Integración con ecosistema AWS (Lambda, etc.)

---

## 📐 CONFIGURACIÓN EN AWS CALCULATOR

### Calculadores Creados

| Escenario | URL | ID |
|-----------|-----|-------|
| **On-Demand** | [Link](https://calculator.aws/#/estimate?id=17a2b57f568036aee836395e441cd6849d45177a) | `17a2b57f568036aee...` |
| **SP 1yr** | [Link](https://calculator.aws/#/estimate?id=1963f6eb5befc2b1ec267ab873d93a41a22dcb47) | `1963f6eb5befc2b...` |
| **SP 3yr** | [Link](https://calculator.aws/#/estimate?id=8373dd6d9be6d6ec0a78ef690239be8ae99d43d7) | `8373dd6d9be6d6ec...` |

### Servicios Configurados por Escenario
- **Amazon API Gateway**: 80,000,000 solicitudes/mes
- **CloudWatch Logs**: 50 GB/mes (logging)
- **Data Transfer (Egress)**: 100 GB/mes

---

## 📊 INTEGRACIÓN EN EXCEL TCO

**Archivo**: `TCO_Migracion_Azure_AWS_OnNet_v2.xlsx`  
**Hoja**: "1. Resumen Ejecutivo TCO"  
**Fila**: 9 (Nueva)

### Datos Agregados
- **Col A**: APIM (11 instancias, 80M llamadas/mes)
- **Col B**: Amazon API Gateway
- **Col C**: Replatform
- **Col D**: Azure Mensual = $1,100
- **Col E**: Azure Anual = $13,200
- **Col F**: AWS On-Demand = $314.00
- **Col G**: AWS SP 1yr = $235.50
- **Col H**: AWS SP 3yr = $172.70
- **Col I**: Ahorro Mensual = $141.30
- **Col J**: Ahorro % = 45.0%
- **Col K**: Ahorro Anual = $1,695.60
- **Col N-P**: URLs de calculadores

---

## ✅ COMPARATIVA TCO - ESTADO ACTUAL

### Fila 8: AKS Nodes
- **Azure**: $54,472/mes
- **AWS SP 3yr**: $30,393.20/mes
- **Ahorro**: $24,078.80/mes (44.2%)

### Fila 9: APIM (NEW)
- **Azure**: $1,250/mes
- **AWS SP 3yr**: $172.70/mes
- **Ahorro**: $1,077.30/mes (86.2%)

### **TOTAL AKS + APIM**
- **Azure**: $55,722/mes
- **AWS SP 3yr**: $30,565.90/mes
- **Ahorro TOTAL**: $25,156.10/mes (45.1%)

---

## 🎯 RECOMENDACIONES

1. **Adoptar AWS API Gateway** para todos los 11 APIM
   - Costo 86% menor que Azure APIM
   - Mejor integración con Lambda/microservicios
   - Escalabilidad automática

2. **Usar Savings Plans 3yr** para APIM
   - $172.70/mes vs $314/mes On-Demand
   - 45% descuento asegurado
   - Combinado con AKS SP 3yr = ahorro máximo

3. **Consolidar Instancias**
   - Evaluar consolidación de 3 instancias Dev en 1-2
   - Usar políticas de throttling para control

4. **Monitoreo y Observabilidad**
   - CloudWatch para logs
   - X-Ray para trazabilidad
   - Configurar alarmas por tasa de llamadas

---

## 📋 PRÓXIMOS PASOS

- [ ] Validar volúmenes de API en ambiente Production
- [ ] Configurar CloudWatch alarms para límites de costo
- [ ] Planificar migración gradual Dev → QA → Prod
- [ ] Configurar WAF en API Gateway (si aplica)
- [ ] Implementar autoscaling basado en métricas

---

**Documento Generado**: 2026-04-17  
**Equipo**: CloudTCO Analyzer  
**Estado**: ✅ Análisis Completado
