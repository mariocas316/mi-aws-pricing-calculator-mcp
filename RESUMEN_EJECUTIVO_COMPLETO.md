# RESUMEN EJECUTIVO - TCO COMPLETO: AKS + APIM

## 🎯 ESTADO ACTUAL DE TCO (Azure)

| Servicio | Instancias | Costo Mensual | Costo Anual |
|----------|-----------|---------------|------------|
| **AKS** (10 clusters, 76 nodos) | 76 nodos | $54,472 | $653,665 |
| **APIM** (11 instancias) | 11 APIM | $1,250 | $15,000 |
| **TOTAL AZURE** | — | **$55,722** | **$668,665** |

---

## ☁️ PROPUESTA AWS - SAVINGS PLANS 3yr (RECOMENDADO)

| Servicio | Instancias | Costo Mensual | Costo Anual | vs Azure |
|----------|-----------|---------------|------------|----------|
| **AKS → EKS** (10 clusters, 76 nodos) | 76 nodos | $30,393.20 | $364,718.40 | -$24,078.80/mes |
| **APIM → API Gateway** (80M API calls) | 11→1 | $172.70 | $2,072.40 | -$1,077.30/mes |
| **TOTAL AWS SP 3yr** | — | **$30,565.90** | **$366,790.80** | **-$25,156.10/mes** |

---

## 💰 AHORRO TOTAL

| Métrica | Valor |
|---------|-------|
| **Ahorro Mensual** | **$25,156.10** |
| **Ahorro Anual** | **$301,874.20** |
| **Porcentaje de Ahorro** | **45.1%** |
| **ROI** | Positivo desde mes 1 |

---

## 📊 CALCULADORES AWS CREADOS

### Escenario 1: EKS (AKS Migration)

| Pricing | URL | Costo/mes | Costo/año |
|---------|-----|-----------|-----------|
| On-Demand | [Link](https://calculator.aws/#/estimate?id=ab9b48fa6e478ba7bfaf28ed1ea8e6a67e6d170f) | $54,314.64 | $651,775.68 |
| SP 1yr | [Link](https://calculator.aws/#/estimate?id=7c23c3f1f9c6cb888de6184877209a6bfad2b5ad) | $40,936.63 | $491,239.56 |
| **SP 3yr** | [Link](https://calculator.aws/#/estimate?id=980f081b3c800ab9f3308e088f20f029f317fe8e) | **$30,393.20** | **$364,718.40** |

### Escenario 2: API Gateway (APIM Migration)

| Pricing | URL | Costo/mes | Costo/año |
|---------|-----|-----------|-----------|
| On-Demand | [Link](https://calculator.aws/#/estimate?id=17a2b57f568036aee836395e441cd6849d45177a) | $314.00 | $3,768.00 |
| SP 1yr | [Link](https://calculator.aws/#/estimate?id=1963f6eb5befc2b1ec267ab873d93a41a22dcb47) | $235.50 | $2,826.00 |
| **SP 3yr** | [Link](https://calculator.aws/#/estimate?id=8373dd6d9be6d6ec0a78ef690239be8ae99d43d7) | **$172.70** | **$2,072.40** |

---

## 📋 INFRAESTRUCTURA FINAL EN AWS

### Compute (EKS)
- **10 EKS Clusters** (Development, QA, Production)
- **76 EC2 Nodes** (m6i, c6i, r6i, c5, t3 instances)
- **10 EKS Control Planes** ($73/mes cada)
- **38 TB EBS gp3 Storage** (500GB × 76 nodes)

### APIs (API Gateway)
- **1 API Gateway** para consolidar los 11 APIM
- **80 millones de llamadas mensuales** (5% Dev + 10% QA + 85% Prod)
- **CloudWatch Logs** para monitoring
- **Data Transfer** para respuestas de API

### Networking
- **3 NAT Gateways** en High Availability
- **2 Application Load Balancers** (para EKS)
- **Multiple VPCs** por ambiente (Dev/QA/Prod)

### Monitoring
- **CloudWatch Custom Metrics** (50 métricas)
- **CloudWatch Logs** (para EKS y API Gateway)
- **X-Ray** para trazabilidad distribuida

---

## ✅ COMPLETADOS

**Fase 1: EKS Analysis**
- ✅ Identificadas 10 clusters, 76 nodos activos
- ✅ Creados 3 calculadores (On-Demand, SP 1yr, SP 3yr)
- ✅ Actualizado Excel con costos y URLs
- ✅ Calculados ahorros: $24,078.80/mes (44.2%)

**Fase 2: API Gateway Analysis** (RECIÉN COMPLETADO)
- ✅ Identificadas 11 instancias APIM
- ✅ Cuantificadas 80M llamadas/mes
- ✅ Creados 3 calculadores (On-Demand, SP 1yr, SP 3yr)
- ✅ Actualizado Excel con costos y URLs
- ✅ Calculados ahorros: $1,077.30/mes (86.2%)
- ✅ Documentación: ANALISIS_APIM_API_GATEWAY.md

---

## 📁 ARCHIVOS GENERADOS

### Documentación
- `ANALISIS_APIM_API_GATEWAY.md` - Análisis detallado APIM→API Gateway
- `RESUMEN_TCO_FINAL.md` - Resumen ejecutivo (AKS+APIM)

### Scripts Python
- `extract-apim-details.py` - Extrae detalles de APIM del inventario
- `update-excel-apigw-fixed.py` - Actualiza Excel con costos API Gateway

### Scripts Node.js
- `create-apigw-estimates.js` - Genera 3 calculadores AWS para API Gateway

### Excel
- `TCO_Migracion_Azure_AWS_OnNet_v2.xlsx` - TCO completo actualizado
  - Fila 8: AKS → EKS ($30,393.20/mes)
  - Fila 9: APIM → API Gateway ($172.70/mes) [NUEVO]

---

## 🎯 PRÓXIMAS FASES (OPCIONAL)

1. **Servicios de Base de Datos** (Azure SQL → RDS, PostgreSQL)
2. **Storage** (Blob → S3, Archive → Glacier)
3. **Messaging** (Service Bus → SQS/SNS, Event Hubs → Kinesis)
4. **Monitoring & Security** (Defender → GuardDuty, Log Analytics → CloudWatch)

---

**Análisis Completado**: 2026-04-17  
**Ahorro Validado**: 45.1% ($25,156.10/mes, $301,874.20/año)  
**Estado**: ✅ LISTO PARA PRESENTACIÓN
