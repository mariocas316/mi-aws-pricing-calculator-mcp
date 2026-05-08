# 🚀 JOOMLA EN AWS - CALCULADORA PRODUCCIÓN (1000 USUARIOS)

## 📋 RESUMEN EJECUTIVO

```
JOOMLA CMS CON 1000 USUARIOS
═══════════════════════════════════════════════════════════

Usuarios concurrentes estimados:    100-200 en pico
Usuarios totales registrados:       1,000
Arquitectura:                       Highly Available
SLA esperado:                       99.5%
Costo estimado:                     $890-$1,100/mes
Tiempo de setup:                    2-3 horas
Backup automático:                  Diario
SSL/HTTPS:                          Incluido (AWS Certificate Manager)
```

---

## 🎯 ARQUITECTURA RECOMENDADA

```
┌──────────────────────────────────────────────────────────────┐
│                    JOOMLA EN PRODUCCIÓN                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                     ┌────────────────┐                       │
│                     │  Route 53 DNS  │                       │
│                     └────────┬────────┘                       │
│                              │                               │
│                     ┌────────▼────────┐                       │
│                     │ CloudFront CDN  │ ← Cache estático    │
│                     │  $85/mes        │                       │
│                     └────────┬────────┘                       │
│                              │                               │
│              ┌───────────────┴───────────────┐                │
│              │   Application Load Balancer   │                │
│              │          $20/mes              │                │
│              └──────────────┬────────────────┘                │
│                      ┌──────┴──────┐                          │
│        ┌─────────────▼─┐    ┌──────▼──────────┐              │
│        │ EC2 T4g.large│    │EC2 T4g.large   │              │
│        │ Joomla + PHP │    │ Joomla + PHP   │              │
│        │  (Standby)   │    │ (Active)       │              │
│        │  $30/mes     │    │ $30/mes        │              │
│        └──────────────┘    └──────┬─────────┘               │
│                                   │                          │
│              ┌────────────────────▼─────────────────┐         │
│              │   RDS MySQL 8.0 db.t4g.micro       │         │
│              │   Multi-AZ para HA                 │         │
│              │   Storage: 50 GB SSD               │         │
│              │   Backup: 35 días retencion        │         │
│              │   $120/mes                         │         │
│              └────────────────────────────────────┘         │
│                                                              │
│   S3 + CloudFront para media, plugins, templates             │
│   ├─ Storage: 50 GB ($1.15/mes)                             │
│   ├─ Transferencia: $0.085/GB                               │
│   └─ CloudFront: $85/mes (cache)                            │
│                                                              │
│   Servicios Adicionales:                                     │
│   ├─ CloudWatch Monitoring: $15/mes                         │
│   ├─ Backup automático (AWS Backup): $10/mes                │
│   ├─ Secrets Manager (credenciales): $0.40/mes              │
│   └─ NAT Gateway para outbound: $32/mes                      │
│                                                              │
│   ESTIMACIÓN TOTAL MENSUAL: $888/mes                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 💰 DESGLOSE DE COSTOS

```
┌─────────────────────────────────┬──────────┬─────────────┐
│ SERVICIO                        │ CANTIDAD │ COSTO/MES   │
├─────────────────────────────────┼──────────┼─────────────┤
│                                 │          │             │
│ COMPUTE                         │          │             │
│ ├─ EC2 T4g.large (x2)          │ 2        │ $60.00      │
│ ├─ Application Load Balancer    │ 1        │ $20.00      │
│ └─ Auto Scaling Group           │ N/A      │ GRATIS      │
│                                 │          │             │
│ DATABASE                         │          │             │
│ ├─ RDS MySQL Multi-AZ           │ 1        │ $120.00     │
│ ├─ Storage (50GB SSD)           │ 50 GB    │ $12.50      │
│ ├─ Backup storage (35 días)     │ 50 GB    │ $5.00       │
│ └─ Enhanced monitoring          │ 1        │ $10.00      │
│                                 │          │             │
│ CDN & CACHING                   │          │             │
│ ├─ CloudFront (cdn.domain.com)  │ 1        │ $85.00      │
│ ├─ S3 Standard storage (50GB)   │ 50 GB    │ $1.15       │
│ └─ S3 data transfer             │ 10 GB/mes│ $0.85       │
│                                 │          │             │
│ NETWORKING                      │          │             │
│ ├─ NAT Gateway                  │ 1        │ $32.00      │
│ ├─ NAT Gateway data transfer    │ 5 GB     │ $0.45       │
│ └─ Elastic IP                   │ 1        │ GRATIS      │
│                                 │          │             │
│ MONITORING & BACKUP             │          │             │
│ ├─ CloudWatch Logs              │ 100 GB   │ $15.00      │
│ ├─ AWS Backup                   │ 1 plan   │ $10.00      │
│ ├─ Secrets Manager (DB creds)   │ 1        │ $0.40       │
│ └─ SNS alerts                   │ 1        │ GRATIS      │
│                                 │          │             │
│ DOMAIN & SSL                    │          │             │
│ ├─ Route 53 hosted zone         │ 1        │ $0.50       │
│ ├─ Route 53 queries             │ 10M      │ $0.40       │
│ └─ ACM SSL (auto-renew)         │ 1        │ GRATIS      │
│                                 │          │             │
├─────────────────────────────────┼──────────┼─────────────┤
│ SUBTOTAL                        │          │ $373.20     │
│ AWS Support (Business)          │          │ $515.00     │
│                                 │          │             │
│ TOTAL MENSUAL                   │          │ $888.20     │
│ TOTAL ANUAL                     │          │ $10,658.40  │
│                                 │          │             │
│ Con margen de seguridad (+20%)  │          │ $1,065.84   │
└─────────────────────────────────┴──────────┴─────────────┘

Nota: Los precios están para región US East (Ohio) us-east-2
```

---

## 📊 PASO 1: CREAR NUEVA ESTIMACIÓN

```
1. Ir a: https://calculator.aws/#/
2. Click "Create estimate"
3. Región: "US East (Ohio)" - us-east-2
4. Nombre: "Joomla_Producción_1000Usuarios"
5. Click "Add service"
```

---

## 🖥️ PASO 2: AGREGAR EC2 (INSTANCIAS JOOMLA)

### EC2 Instancia 1 (Primary)

```
Service: Amazon EC2
Region: US East (Ohio)
Group: Joomla-Servers

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Operating System         │ Linux (Ubuntu)     │
│ Instance Type            │ t4g.large          │ ← Graviton ARM (económico)
│ Tenancy                  │ Shared             │
│ Quantity                 │ 1                  │
│ Pricing Strategy         │ On-Demand          │
│ Storage (EBS)            │ gp3 50GB           │
│ Monitoring               │ Detailed           │
│ Data Transfer            │ Outbound 5GB/mes   │
└──────────────────────────────────────────────┘

ESPECIFICACIONES:
├─ vCPU: 2 cores
├─ RAM: 8 GB
├─ Network: Hasta 5 Gbps
├─ Precio: $0.041/hora
└─ Mensual: ~$30/mes

Click: "Save and add service"
```

### EC2 Instancia 2 (Standby/Backup)

```
Service: Amazon EC2
Region: US East (Ohio)
Group: Joomla-Servers

CONFIGURACIÓN:
(Misma que arriba - t4g.large)
Quantity: 1
Pricing Strategy: On-Demand

PROPOSITO:
├─ Réplica en otra AZ
├─ High Availability
├─ Failover automático
└─ Costo: ~$30/mes

Click: "Save and add service"
```

**SUBTOTAL EC2: $60/mes**

---

## 🔄 PASO 3: AGREGAR APPLICATION LOAD BALANCER

```
Service: Application Load Balancer (ALB)
Region: US East (Ohio)
Group: Networking

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Load Balancer Type       │ Application        │
│ Number of ALBs           │ 1                  │
│ Processed Bytes/month    │ 100 GB             │
│ New Connections/second   │ 10                 │
│ Active Connections/min   │ 1,000              │
│ Rule Evaluations/month   │ 1 million          │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ ALB base: $16.00/mes
├─ LCU (Load Balancer Capacity Unit): $4.00/mes
└─ TOTAL: $20/mes

Click: "Save and add service"
```

**SUBTOTAL ALB: $20/mes**

---

## 🗄️ PASO 4: AGREGAR RDS MYSQL (BASE DE DATOS)

```
Service: Amazon RDS MySQL
Region: US East (Ohio)
Group: Database

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Engine                   │ MySQL 8.0          │
│ Database Instance Class  │ db.t4g.micro       │ ← Graviton
│ Multi-AZ deployment      │ Sí (HA)            │
│ Allocated Storage        │ 50 GB (SSD gp3)    │
│ Number of DB instances   │ 1                  │
│ Backup retention period  │ 35 days            │
│ Enhanced Monitoring      │ Sí                 │
│ Data exported/month      │ 0 GB               │
└──────────────────────────────────────────────┘

DESGLOSE:
├─ Primary DB instance: $60/mes (db.t4g.micro × 2 por Multi-AZ)
├─ Storage (50GB): $12.50/mes
├─ Backup (50GB × 35 días): $5.00/mes
├─ Enhanced Monitoring: $10/mes
└─ TOTAL: $87.50/mes

IMPORTANTE:
├─ Multi-AZ = Standby en otra availability zone
├─ Failover automático en caso de fallo
├─ Backups automáticos cada 24 horas
└─ Retención: 35 días = máximo

Click: "Save and add service"
```

**SUBTOTAL RDS: $87.50/mes**

---

## 🖼️ PASO 5: AGREGAR S3 (ALMACENAMIENTO DE ARCHIVOS/MEDIA)

```
Service: S3 Standard
Region: US East (Ohio)
Group: Storage

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ S3 Standard storage      │ 50 GB              │
│ Frequency               │ month              │
│ How moved to S3 Std     │ No movement        │
│ Average Object Size     │ 256 KB             │
│ PUT, COPY, POST, LIST   │ 10,000 requests    │
│ GET requests            │ 100,000 requests   │
│ Data returned by Select │ 0 GB               │
│ Data scanned by Select  │ 0 GB               │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ Storage (50GB): $1.15/mes
├─ PUT requests: $0.50
├─ GET requests: $0.20
├─ Data transfer OUT: $0.85/mes (10GB × $0.085)
└─ TOTAL: $2.70/mes

PROPOSITO:
├─ Joomla media library
├─ Plugin zips
├─ Template backups
├─ User uploads
└─ Versioning habilitado

Click: "Save and add service"
```

**SUBTOTAL S3: $2.70/mes**

---

## 🚀 PASO 6: AGREGAR CLOUDFRONT (CDN)

```
Service: CloudFront CDN
Region: us-east-2 (distribuidor global)
Group: CDN

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Edge locations          │ All (default)      │
│ Data transfer OUT       │ 10 GB/month        │
│ HTTP requests           │ 100,000            │
│ HTTPS requests          │ 100,000            │
│ Lambda@Edge (invoc)     │ 0                  │
│ Field-Level Encryption  │ No                 │
│ Origin: S3 Standard     │ Yes                │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ Data transfer OUT: $0.085 × 10GB = $0.85
├─ HTTP requests: $0.0075 × 100K = $0.75
├─ HTTPS requests: $0.01 × 100K = $1.00
├─ Shared cache invalidations: $0.005 × 1,000 = $5.00
└─ TOTAL: $7.60/mes

PERO CON CACHING AGRESIVO:
├─ Caché de 24 horas = $7.60
├─ Caché de 7 días = $5.20/mes
└─ (Usar 7 días para imágenes/CSS/JS)

RECOMENDADO: $85/mes (planing ahead para picos)

Click: "Save and add service"
```

**SUBTOTAL CloudFront: $85/mes**

---

## 🌐 PASO 7: AGREGAR NAT GATEWAY (SALIDA A INTERNET)

```
Service: NAT Gateway
Region: US East (Ohio)
Group: Networking

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Number of NAT Gateways  │ 1                  │
│ Data processed/month    │ 5 GB               │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ NAT Gateway (hourly): $32.00/mes
├─ Data processing: $0.045 × 5GB = $0.225
└─ TOTAL: $32.23/mes

PROPOSITO:
├─ EC2 accede a internet (updates, email, APIs)
├─ Joomla extensions que necesitan salida
├─ Backup a servicios externos
└─ Actualizaciones de seguridad

Click: "Save and add service"
```

**SUBTOTAL NAT Gateway: $32/mes**

---

## 📊 PASO 8: AGREGAR MONITORING (CLOUDWATCH)

```
Service: CloudWatch
Region: US East (Ohio)
Group: Monitoring

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ CloudWatch Logs         │ 100 GB ingestion   │
│ Log retention period    │ 30 days            │
│ Dashboards              │ 1                  │
│ Alarms                  │ 5                  │
│ Custom metrics          │ 50                 │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ Logs ingestion (100GB): $15.00/mes
├─ Log storage: ~$3.00/mes
├─ Dashboards: GRATIS (1 incluido)
├─ Alarms: GRATIS (hasta 10)
└─ TOTAL: $18/mes

Click: "Save and add service"
```

**SUBTOTAL CloudWatch: $18/mes**

---

## 🔒 PASO 9: AGREGAR AWS BACKUP

```
Service: AWS Backup
Region: US East (Ohio)
Group: Backup

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Protected resource type │ RDS              │
│ Number of backups/month │ 30 (daily)      │
│ Recovery point storage  │ 50 GB            │
│ Cross-region backup     │ No               │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ Backup storage (50GB): $10/mes
├─ Resource API: GRATIS
└─ TOTAL: $10/mes

PROPOSITO:
├─ Backups diarios automáticos
├─ RDS snapshots
├─ EBS volumes
├─ Retención: 35 días
└─ Recuperación en 1-2 minutos

Click: "Save and add service"
```

**SUBTOTAL AWS Backup: $10/mes**

---

## 🎫 PASO 10: AGREGAR AWS SECRETS MANAGER

```
Service: Secrets Manager
Region: US East (Ohio)
Group: Security

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Secrets stored          │ 1                  │
│ API calls               │ 100,000/month      │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ Secret stored: $0.40/mes (DB password)
├─ API calls: GRATIS hasta 1M
└─ TOTAL: $0.40/mes

PROPOSITO:
├─ Almacenar credenciales DB
├─ Rotación automática
├─ Evitar hardcoding passwords
└─ Auditoría de acceso

Click: "Save and add service"
```

**SUBTOTAL Secrets Manager: $0.40/mes**

---

## 🌍 PASO 11: AGREGAR ROUTE 53 (DNS)

```
Service: Route 53
Region: Global
Group: Networking

CONFIGURACIÓN:
┌──────────────────────────────────────────────┐
│ Hosted zones            │ 1                  │
│ Query volume            │ 10 million/month   │
│ Health checks           │ 0 (default)       │
└──────────────────────────────────────────────┘

CÁLCULO:
├─ Hosted zone: $0.50/mes
├─ Queries (10M): $0.40/mes
└─ TOTAL: $0.90/mes

Click: "Save and add service"
```

**SUBTOTAL Route 53: $0.90/mes**

---

## 📋 PASO 12: REVISAR TOTAL

Después de agregar todos los servicios, tu calculadora debe mostrar:

```
JOOMLA PRODUCCIÓN - RESUMEN MENSUAL
═════════════════════════════════════════════════════════

EC2 (2 × t4g.large)                      $60.00
Application Load Balancer                $20.00
RDS MySQL db.t4g.micro Multi-AZ         $87.50
S3 Standard (50GB)                       $2.70
CloudFront CDN                           $85.00
NAT Gateway                              $32.00
CloudWatch Logs                          $18.00
AWS Backup                               $10.00
Secrets Manager                          $0.40
Route 53 DNS                             $0.90
────────────────────────────────────────────────
SUBTOTAL                                $316.50

AWS Support Plan (Business - recomendado)  $515.00
────────────────────────────────────────────────
TOTAL ESTIMADO MENSUAL                  $831.50
TOTAL ANUAL                             $9,978.00

CON MARGEN SEGURIDAD (+20%)            $1,197.80/mes
```

---

## ✅ PASO 13: VALIDAR Y EXPORTAR

```
1. Click en "View summary" (parte superior)
2. Verifica:
   ├─ Todos los servicios están listados
   ├─ Región correcta: us-east-2
   ├─ Calculadora no tiene errores
   └─ Total visible

3. Click "Export" → "PDF" o "Save"
4. Click "Share" → Copiar URL pública
5. Guardar URL para presentar a stakeholders

EJEMPLO URL:
https://calculator.aws/#/estimate?id=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

---

## 🔧 CONFIGURACIÓN JOOMLA (TRAS DEPLEGAR)

### En EC2 - Instalación de Joomla

```bash
#!/bin/bash

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar LAMP Stack (Linux, Apache, MySQL, PHP)
sudo apt install -y apache2 php php-mysql libapache2-mod-php php-curl php-json

# Habilitar módulos Apache
sudo a2enmod rewrite
sudo systemctl restart apache2

# Descargar Joomla
cd /var/www/html
sudo wget https://github.com/joomla/joomla-cms/releases/download/4.4.1/Joomla_4.4.1-Stable-Full_Package.tar.gz
sudo tar -xzf Joomla_4.4.1-Stable-Full_Package.tar.gz

# Permisos
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Obtener credenciales RDS de Secrets Manager
DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id joomla/db/password --query SecretString --output text)

# Ejecutar instalación de Joomla
# (Ir a http://tu-dominio.com e instalar vía web)
```

### Conexión a RDS

```
En installer de Joomla:
├─ Host: (RDS endpoint - sin puerto 3306 si es default)
├─ Usuario: joomla_admin
├─ Contraseña: (desde Secrets Manager)
├─ BD: joomla_db
└─ Crear nuevas tablas: Sí
```

### Configuración CloudFront

```
En Joomla - System → Global Configuration:
├─ Media Path: s3://my-joomla-bucket/images/
├─ Use CDN: https://d1a2b3c4d5e6f7g.cloudfront.net/
└─ Cache time: 86400 (24 horas) para imágenes
```

---

## 🎯 MONITOREO EN PRODUCCIÓN

### Dashboards CloudWatch

```
Crear alerta si:
├─ CPU EC2 > 75% (escalar)
├─ DB connections > 80% (optimizar queries)
├─ ALB latency > 500ms (revisar app)
├─ RDS free storage < 10GB (aumentar)
└─ Network in/out > umbral (revisar tráfico)

Métricos recomendados:
├─ Usuarios concurrentes (en Joomla)
├─ Tiempo de carga promedio
├─ Tasa de error HTTP 5xx
├─ Disponibilidad (target health)
└─ Backup success rate
```

---

## 📈 ESCALA PARA 5,000 USUARIOS

Si futuro crece:

```
CAMBIOS NECESARIOS:
├─ EC2: t4g.xlarge (4 instancias, Auto Scaling)
├─ RDS: db.t4g.small Multi-AZ
├─ RDS storage: 200 GB
├─ S3: 200 GB
├─ CloudFront: $300/mes
├─ NAT Gateway: $64/mes (2 para HA)
└─ COSTO TOTAL: ~$2,500/mes

Escala automática:
├─ ASG con 2-4 instancias
├─ Target tracking: CPU 70%
├─ Health checks cada 30 segundos
└─ Reemplazo automático si falla
```

---

## 🚨 DISASTER RECOVERY

```
RTO (Recovery Time Objective):    15 minutos
RPO (Recovery Point Objective):   1 hora

PLAN:
├─ Primary falla → ALB detecta
├─ Tráfico → Standby EC2 (automático)
├─ Si DB falla → RDS Multi-AZ failover (2 min)
├─ Restaurar desde backup: 5 minutos
└─ Prueba DR: Mensual

Backup strategy:
├─ Diario: Full snapshot RDS
├─ Semanal: Cross-region copy
├─ Mensual: Long-term archive S3 Glacier
└─ Retención: 35 días
```

---

## 💡 TIPS PARA REDUCIR COSTOS

```
INMEDIATOS:
├─ Usar Reserved Instances: -30% EC2
├─ Usar Compute Savings Plans: -15% RDS
└─ Consolidar data transfer: -20%

DESPUÉS DE 1 MES:
├─ Ver patrones de uso real
├─ Ajustar tamaño RDS si sobredimencionado
├─ Aumentar CloudFront caché
└─ Usar S3 Intelligent-Tiering

DESPUÉS DE 3 MESES:
├─ Analizar logs para optimizar
├─ Considerar RDS Aurora si llega a 100 conexiones
├─ Usar ElastiCache para objeto cache
└─ Auto Scaling más agresivo
```

---

## ✅ CHECKLIST ANTES DE PRODUCCIÓN

```
☐ SSL/HTTPS configurado (AWS Certificate Manager)
☐ Backups probados (restore test)
☐ Monitoring activo (alarms funcionando)
☐ Auto Scaling configurado
☐ Health checks en ALB
☐ Security groups restringidos
☐ IAM roles sin permisos excesivos
☐ Joomla en última versión
☐ Plugins de seguridad instalados
☐ Load testing completado (1000 usuarios)
☐ DNS propagado globalmente
☐ Disaster recovery plan documentado
☐ On-call rotation establecido
☐ Backup retention verificado
☐ Costos estimados vs reales
```

---

**SIGUIENTE PASO:** Crear la estimación en https://calculator.aws/#/ siguiendo estos pasos y compartir el URL con tu equipo.

¿Necesitas ayuda con algo específico de la configuración?

