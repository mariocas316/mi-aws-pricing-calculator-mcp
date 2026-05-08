# Servidor MCP de AWS Pricing Calculator

Servidor de [Model Context Protocol](https://modelcontextprotocol.io) (MCP) que crea, lee y actualiza estimaciones de [AWS Pricing Calculator](https://calculator.aws/#/estimate) de forma programatica mediante lenguaje natural.

Documentacion tecnica completa del proyecto en espanol: [DOCUMENTACION_PROYECTO_ES.md](DOCUMENTACION_PROYECTO_ES.md)

## Caracteristicas Principales

- **Creacion de Estimaciones**: Soporta los mas de 436 servicios de AWS mediante definiciones en vivo desde el CDN de AWS Calculator
- **Gestion de Estimaciones**: Exporta y modifica estimaciones existentes de AWS Pricing Calculator (por ejemplo, cambiar regiones de AWS)
- **Importacion por Lotes**: Crea estimaciones desde archivos Excel/CSV usando parseo asistido por LLM
- **Sin Credenciales de AWS**: Funciona sin acceso a una cuenta de AWS

## Ejemplo

Prompt:
> Crea una estimacion de AWS Pricing Calculator para un entorno comun de Wordpress en AWS (Dev, Quality, Production).

Salida:
![](example1.png)

## Inicio Rapido

Requiere [Node.js®](https://nodejs.org/en/download).

```bash
git clone https://github.com/mariocas316/mi-aws-pricing-calculator-mcp.git
cd mi-aws-pricing-calculator-mcp
npm install
npm run build
```

El servidor se comunica por stdio usando el protocolo MCP; esta disenado para clientes compatibles con MCP (por ejemplo Claude, Kiro), no para ser invocado directamente por HTTP.

### Configuracion del Cliente MCP

Agrega esto en la configuracion de tu cliente MCP (por ejemplo, `~/.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "aws-pricing-calculator-mcp-server": {
      "command": "node",
      "args": ["/path/to/sample-aws-pricing-calculator-mcp/dist/mcp-server.js"]
    }
  }
}
```

## Herramientas MCP

| Herramienta | Descripcion |
|---|---|
| `search_services` | Busca servicios de AWS por nombre o clave. Soporta consultas separadas por comas. |
| `get_service_fields` | Obtiene IDs de campos de entrada, tipos, etiquetas y opciones validas para uno o mas servicios. |
| `create_estimate` | Crea una estimacion vacia nueva. Devuelve un ID de estimacion. |
| `create_eks_estimate` | Crea una estimacion EKS lista para exportar, dimensionada para cargas con contenedores (por ejemplo 100 contenedores), incluyendo sizing de workers EC2. |
| `add_service` | Agrega uno o mas servicios a una estimacion con valores de configuracion. Soporta modo batch. |
| `export_estimate` | Exporta una estimacion a calculator.aws y devuelve una URL compartible. |
| `map_azure_vm_to_ec2` | Mapea una VM de Azure a un tipo EC2 equivalente y retorna comparativa de costos por VM. |
| `get_azure_aws_cost_comparison` | Devuelve resumen de costos Azure vs AWS (totales, ahorros y porcentaje) con filtro opcional por ambiente. |
| `create_aws_migration_estimate` | Crea un estimate de migracion desde el mapeo Azure->AWS agregando instancias EC2 automaticamente. |

### Ejemplo Rapido: EKS para 100 Contenedores

1. Llama a `create_eks_estimate` con los valores por defecto:

```json
{
  "container_count": 100,
  "region": "us-east-1",
  "instance_type": "m5.xlarge"
}
```

2. Usa el `estimate_id` devuelto en `export_estimate`:

```json
{
  "estimate_id": "<returned-id>"
}
```

## Estructura del Proyecto

```
mcp-server.js                # Punto de entrada — servidor MCP por stdio
lib/
  aws-client.js              # Carga del manifest AWS, definiciones de servicio, extraccion de campos, API de guardado
  estimate-builder.js         # Constructor de estimaciones con generacion de payload AWS y exportacion
  ec2.js                     # Transformacion de config EC2 (amigable para agentes -> formato calculator)
test/
  aws-client.test.js         # Pruebas del cliente AWS
  ec2.test.js                # Pruebas de transformacion EC2
  estimate-builder.test.js   # Pruebas del constructor de estimaciones
  integration.test.js        # Pruebas de integracion
  validation.test.js         # Pruebas de validacion de configuracion
```

## Build

```bash
npm run build
```

Genera `dist/mcp-server.js`, un bundle de esbuild en un solo archivo (minificado, CJS, plataforma Node).

## Pruebas

```bash
npm test
```

## Arquitectura

```
┌─────────────────┐       stdio        ┌──────────────────────────────────────┐
│   MCP Client    │◄──────────────────►│         MCP Server                   │
│ (Kiro, Claude,  │   JSON-RPC over    │                                      │
│  Cursor, etc.)  │   stdin/stdout     │  mcp-server.js (entry point)         │
└─────────────────┘                    │    ├── lib/aws-client.js             │
                                       │    ├── lib/estimate-builder.js       │
                                       │    └── lib/ec2.js                    │
                                       └──────────┬───────────┬──────────────┘
                                                  │           │
                                        HTTPS GET │           │ HTTPS POST
                                                  ▼           ▼
                                       ┌──────────────┐  ┌──────────────────┐
                                       │ CloudFront   │  │ AWS Calculator   │
                                       │ CDN          │  │ Save API         │
                                       │              │  │                  │
                                       │ • manifest   │  │ POST /v2/saveAs  │
                                       │ • service    │  │ → devuelve       │
                                       │   definitions│  │   URL compartible│
                                       └──────────────┘  └──────────────────┘
```

- El servidor MCP corre como **proceso hijo local** lanzado por el cliente MCP. Se comunica exclusivamente por stdio; no es accesible por red.
- Todas las solicitudes salientes son por **HTTPS** hacia distribuciones publicas de AWS CloudFront sin autenticacion. No se requieren ni se usan credenciales de AWS.
- Los datos de la estimacion se mantienen **solo en memoria** y se pierden al terminar el proceso. No se persiste informacion en disco.

## Como Funciona

### Descubrimiento de Servicios

En el primer uso, el servidor obtiene el manifest de AWS Calculator desde CloudFront, que contiene mas de 436 servicios con sus claves, nombres y URLs de definicion. Las definiciones se piden bajo demanda y se cachean. La herramienta `get_service_fields` parsea esas definiciones para extraer IDs de campos de entrada, tipos, etiquetas y opciones validas en un formato plano y utilizable.

### Construccion de Estimaciones

`EstimateBuilder` mantiene servicios y grupos en memoria. Cuando agregas un servicio con `add_service`, la configuracion se guarda tal cual usando los IDs de campo de AWS. Los servicios se pueden organizar en grupos con nombre y se soportan multiples instancias del mismo servicio mediante claves compuestas (por ejemplo `aWSLambda:Compute`).

### Manejo de EC2

EC2 usa una transformacion personalizada (`lib/ec2.js`) que convierte campos amigables para agentes (tipo de instancia, SO, estrategia de precios) al formato `ec2Enhancement` que espera la calculadora. Esto incluye soporte para On-Demand, Savings Plans, Reserved Instances y Spot.

### Soporte de Particiones

El servidor soporta tres particiones de AWS:
- `aws` — regiones comerciales estandar
- `aws-iso` — US ISO East/West
- `aws-iso-b` — US ISOB East

### Exportacion a calculator.aws

Cuando se llama `export_estimate`, el constructor:

1. Resuelve el nombre de cada servicio contra el manifest
2. Obtiene la definicion del servicio para tener `version`, `serviceCode` y el ID de template correctos
3. Mapea las claves de configuracion a `calculationComponents` en el formato de payload de AWS
4. Hace POST del payload armado a la Save API de AWS Calculator
5. Devuelve la URL compartible de `calculator.aws`

AWS recalcula los costos reales cuando alguien abre el enlace.

## Actualizaciones Recientes (Mayo 2026)

- Se completo una estimacion de referencia para Joomla en produccion (1000 usuarios) con arquitectura HA y variante de RDS Single-AZ.
- Se valido flujo end-to-end con MCP: `create_estimate` -> `add_service` -> `export_estimate` para casos Joomla y migracion.
- Se ejecutaron cargas masivas de VMs standalone hacia AWS Pricing Calculator desde JSON de entrada por VM.
- Se generaron y validaron resultados de carga en archivos de salida para consumo operativo.

Archivos relevantes generados/actualizados en este flujo:

- `generate_joomla_calculator.py`
- `joomla_calculator_config.json`
- `joomla_calculator_analysis.json`
- `create-vm-ondemand-detailed-estimate.js`
- `vm-ondemand-detailed-result.json`

## Variables de Entorno

Todas opcionales:

| Variable | Valor por Defecto | Proposito |
|---|---|---|
| `AWS_MANIFEST_URL` | URL de manifest en CloudFront | Catalogo de servicios de AWS |
| `AWS_SAVE_URL` | URL de guardado en CloudFront | Persistencia de estimaciones |

## Problemas Conocidos

- Las APIs de save/manifest en CloudFront no estan documentadas y pueden cambiar sin previo aviso.
- Quien llama debe usar los IDs de campo correctos de AWS; puedes descubrirlos con `get_service_fields`.
- Las estimaciones viven en memoria y no persisten entre reinicios.
- No hay calculo local de costos; AWS calcula el precio cuando se abre el enlace compartible y se presiona `Update estimate`.
- Por ahora solo se soporta https://calculator.aws/

## Seguridad

Este es codigo de ejemplo con fines educativos. Debes trabajar con tus equipos de seguridad y legal para cumplir con los requisitos de seguridad, regulatorios y de cumplimiento de tu organizacion antes de desplegarlo.

### Modelo de Seguridad

Este servidor MCP es un **proveedor de herramientas local**. Corre como proceso hijo de un cliente MCP y no es accesible por red. No tiene capa de autenticacion ni autorizacion; el control de acceso es responsabilidad del cliente MCP que lo lanza.

El servidor no maneja credenciales de AWS, datos de clientes ni PII. Procesa unicamente parametros de configuracion de precios (por ejemplo, region, tipo de instancia, cantidad de requests) enviados por el cliente MCP.

Estos son los mismos endpoints publicos y sin autenticacion que usa el sitio [calculator.aws](https://calculator.aws). No se transmiten credenciales de AWS.

### Validacion y Sanitizacion de Entradas

- Todas las entradas de herramientas MCP se validan con esquemas de [Zod](https://zod.dev/) antes de procesarlas.
- Las descripciones y nombres de grupos provistos por el usuario se sanitizan removiendo caracteres `<`, `>` y `&` antes de incluirlos en payloads de API, evitando inyeccion HTML/XML en el frontend de la calculadora.
- Las claves de configuracion de servicios se validan contra definiciones de servicios AWS con deteccion de typos (distancia de Levenshtein), rechazando IDs invalidos antes de llegar a la API.

### Manejo de Datos

- Los datos de la estimacion se mantienen **solo en memoria** durante la vida del proceso. No se escriben en disco ni se persisten entre reinicios.
- Los datos consisten en configuracion de precios (codigos de region, parametros de servicio, tipos de instancia), no secretos, credenciales ni informacion personal identificable.
- Las URLs compartibles generadas en la exportacion contienen solo un ID opaco de estimacion. El contenido de la estimacion se guarda en AWS, no en este servidor.

### Reporte de Problemas de Seguridad

Consulta [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) para informacion sobre como reportar problemas de seguridad.

## Comparacion de Servidores MCP de AWS: Pricing y Cost Management

| | **AWS Pricing Calculator MCP (Este)** | **[AWS Billing & Cost Management MCP](https://github.com/awslabs/mcp#-cost--operations)** | **[AWS Pricing MCP](https://github.com/awslabs/mcp#-cost--operations)** |
|---|---|---|---|
| **Proposito** | Construir estimaciones de costo compartibles para nuevas cargas | Analizar gasto historico y optimizar costos actuales | Consultar precios en tiempo real desde Price List API |
| **Fuente de Datos** | AWS Pricing Calculator (calculator.aws) | Cost Explorer, Cost Optimization Hub, Compute Optimizer, Savings Plans, Budgets, Storage Lens | AWS Price List Bulk API |
| **Salida** | URL compartible de calculator.aws con estimacion completa | Insights de costos en lenguaje natural, recomendaciones de ahorro | Datos de precio crudos, reportes de costos (markdown/CSV) |
| **Caso de Uso** | "Cuanto costara esta arquitectura nueva?" | "En que estoy gastando de mas hoy?" | "Cual es el precio por unidad de X?" |
| **Alcance** | Estimaciones a futuro | Gasto historico y actual | Catalogo de precios actual |
| **Credenciales AWS** | No requeridas (usa API publica de calculator) | Requeridas (lee tus datos de facturacion) | Requeridas (permisos `pricing:*`) |

Resumen rapido: usa Pricing Calculator MCP para crear estimaciones en propuestas, Billing & Cost Management MCP para analizar y optimizar lo que ya gastas, y Pricing MCP para consultas granulares de precio unitario y analisis de costo para IaC.

## Licencia

Esta libreria esta licenciada bajo MIT-0. Consulta el archivo [LICENSE](LICENSE).

## Descargo de Responsabilidad

Antes de usar un servidor MCP, deberias realizar tu propia evaluacion independiente para asegurar que tu uso cumpla con tus practicas y estandares de seguridad y control de calidad, asi como con las leyes, reglas y regulaciones que aplican a ti y a tu contenido.