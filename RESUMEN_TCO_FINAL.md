# ✅ TCO ACTUALIZADO - AKS → EKS Migration

## Fecha
6 de Mayo de 2026

## Datos Finales (Fila 8 - AKS Nodes)

### Costos Mensuales
| Escenario | Costo Mensual | Vs Azure |
|-----------|---------------|----------|
| **Azure (Actual)** | $54,472.00 | Baseline |
| **AWS On-Demand** | $54,314.64 | -0.3% |
| **AWS SP 1yr** | $40,936.63 | -24.9% |
| **AWS SP 3yr (Recomendado)** | $30,393.20 | -44.2% ✅ |

### Ahorros (Scenario SP 3yr)
- **Ahorro Mensual:** $24,078.80
- **Ahorro Anual:** $288,945.60
- **Ahorro Porcentual:** 44.2%

### Infraestructura
- **Clusters EKS:** 10 (Dev 1, QA 4, Prod 5)
- **Nodos EC2:** 76 (Dev 7, QA 28, Prod 41)
- **Almacenamiento EBS:** 38 TB (500 GB × 76 nodos)
- **Networking:** 3 NAT Gateways, 2 ALBs
- **Monitoreo:** CloudWatch con 50 métricas

### URLs de Calculadora
| Escenario | URL |
|-----------|-----|
| **On-Demand** | https://calculator.aws/#/estimate?id=ab9b48fa6e478ba7bfaf28ed1ea8e6a67e6d170f |
| **SP 1yr** | https://calculator.aws/#/estimate?id=7c23c3f1f9c6cb888de6184877209a6bfad2b5ad |
| **SP 3yr** | https://calculator.aws/#/estimate?id=980f081b3c800ab9f3308e088f20f029f317fe8e |

## Homologación AKS → EKS

### Development (7 nodos)
- 7 × m6i.xlarge
- 1 × EKS Control Plane

### QA (28 nodos)
- 3 × c6i.4xlarge
- 8 × c6i.8xlarge
- 10 × m6i.xlarge
- 2 × t3.large
- 5 × c5.xlarge
- 4 × EKS Control Planes

### Production (41 nodos)
- 2 × c5.xlarge
- 6 × m6i.16xlarge
- 1 × t3.large
- 16 × m6i.xlarge
- 6 × r6i.12xlarge
- 7 × c5.xlarge
- 3 × m6i.16xlarge
- 5 × EKS Control Planes

## Archivo Actualizado
- **Ruta:** `archivostcoonnet/TCO_Migracion_Azure_AWS_OnNet_v2.xlsx`
- **Hoja:** 1. Resumen Ejecutivo TCO
- **Fila:** 8 (AKS Nodes)
- **Columnas Actualizadas:**
  - F: AWS On-Demand Mensual
  - G: AWS SP 1yr Mensual
  - H: AWS SP 3yr Mensual
  - I: Ahorro Mensual
  - J: Ahorro %
  - K: Ahorro Anual
  - N, O, P: URLs de Calculadora

## Beneficios Clave
1. **Ahorro de $24K/mes** con Savings Plan 3 años
2. **44.2% reducción** vs costo Azure actual
3. **10 control planes** incluidos (homologación 1:1 de clusters)
4. **76 nodos** distribuidos estratégicamente por ambiente
5. **Arquitectura enterprise-ready** con observabilidad y seguridad

## Próximos Pasos (Opcionales)
1. Optimización con Karpenter (autoscaling inteligente)
2. Spot instances en QA/Dev (70% descuento adicional)
3. Reserved Capacity para picos predecibles
4. CloudFormation/Terraform para IaC
