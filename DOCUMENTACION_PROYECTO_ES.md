# Documentacion Tecnica del Proyecto (Espanol)

Este documento describe todo el proyecto de forma tecnica y operativa: arquitectura, modulos, herramientas MCP, pruebas, flujos de datos, mantenimiento y recomendaciones de uso.

## 1) Resumen del Proyecto

Este repositorio implementa un servidor MCP (Model Context Protocol) que permite construir estimaciones en AWS Pricing Calculator mediante herramientas programaticas.

Objetivo principal:
- Crear y administrar estimaciones de costo de AWS sin credenciales AWS locales.
- Descubrir servicios y campos de configuracion desde el catalogo real de calculator.aws.
- Exportar la estimacion para obtener una URL oficial compartible.

Tecnologias:
- Node.js (CommonJS)
- @modelcontextprotocol/sdk
- Zod (validacion de entrada)
- esbuild (empaquetado)

## 2) Inventario del Repositorio

Archivos de documentacion y meta:
- README.md
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- LICENSE
- .gitignore

Entrada principal del servidor:
- mcp-server.js

Modulos de negocio:
- lib/aws-client.js
- lib/estimate-builder.js
- lib/ec2.js
- lib/eks.js

Pruebas:
- test/aws-client.test.js
- test/estimate-builder.test.js
- test/ec2.test.js
- test/validation.test.js
- test/eks.test.js
- test/integration.test.js

Configuracion local de cliente MCP:
- .vscode/mcp.json

Empaquetado/ejecucion:
- package.json
- package-lock.json

## 3) Arquitectura General

El servidor se ejecuta como proceso local por stdio y expone herramientas MCP. Internamente usa dos piezas base:

1. Capa de catalogo AWS (lib/aws-client.js)
- Carga manifest por particion.
- Busca servicios.
- Descarga definiciones de servicio.
- Extrae campos configurables.
- Persiste estimaciones via Save API.

2. Capa de construccion de estimaciones (lib/estimate-builder.js)
- Mantiene el estado in-memory de servicios/grupos.
- Convierte configuraciones al payload esperado por AWS Calculator.
- Soporta exportacion a URL compartible.

El servidor MCP (mcp-server.js) orquesta validacion, herramientas y manejo del estado de estimaciones activas.

## 4) Flujo de Datos End-to-End

Flujo tipico:

1. Cliente MCP llama search_services
- Se carga manifest desde CloudFront.
- Se retorna lista de servicios candidatos.

2. Cliente MCP llama get_service_fields
- Se descarga definicion del servicio.
- Se extraen IDs y tipos de campos validos.

3. Cliente MCP llama create_estimate
- Se crea objeto EstimateBuilder in-memory.
- Se devuelve estimate_id.

4. Cliente MCP llama add_service
- Se valida JSON de entrada.
- Se validan IDs de campos contra definicion de servicio (excepto EC2 especial).
- Se agregan servicios al estimate actual.

5. Cliente MCP llama export_estimate
- Se arma payload AWS final.
- Se envia a Save API.
- Se devuelve URL calculator.aws oficial.

## 5) mcp-server.js (API MCP)

Herramientas expuestas:

1. create_eks_estimate
- Dimensiona workers EKS automaticamente (CPU/mem/pods/headroom).
- Agrega EC2 workers como ec2Enhancement.
- Intenta agregar control plane EKS detectando el mejor service key en el manifest.
- Retorna estimate_id y resumen de sizing.

2. search_services
- Busca servicios por key/nombre/keywords.
- Soporta multiples terminos separados por coma.

3. get_service_fields
- Retorna campos de entrada por servicio (ID, tipo, opciones, unidades).

4. create_estimate
- Crea una estimacion vacia (estado in-memory).

5. add_service
- Agrega uno o varios servicios en batch JSON.
- Valida claves de config contra definicion real.
- Soporta transformacion especial para ec2Enhancement.

6. export_estimate
- Exporta la estimacion y devuelve URL oficial.

Funciones internas relevantes:
- levenshtein / suggestMatch: sugerencias de typo en field IDs.
- validateConfigKeys: control de claves invalidas y sugerencias.
- pickEksServiceKey: heuristica para hallar servicio EKS activo.

Estado interno:
- estimates: Map en memoria (estimate_id -> EstimateBuilder).

## 6) lib/aws-client.js (Catalogo y Persistencia)

Responsabilidades:
- Definir particiones soportadas (aws, aws-iso, aws-iso-b).
- Cargar manifest por particion.
- Buscar servicios en el manifest.
- Descargar definiciones de servicio con cache.
- Parsear respuesta doble-encoded del Save API.
- Enviar payload final al endpoint saveAs.
- Extraer campos de entrada desde templates complejos.

Comportamientos clave:
- Caching en memoria:
  - manifestCache
  - definitionCache
- Resiliencia:
  - Si falla loadManifest en una particion, limpia cache de esa particion para permitir reintento.
- Extraccion robusta de campos:
  - Omite elementos decorativos.
  - Deduplica campos repetidos entre templates.
  - Soporta metadatos especiales para fileSize.

## 7) lib/estimate-builder.js (Construccion de Payload)

Clase principal: EstimateBuilder

Capacidades:
- Genera ID unico por estimacion.
- Organiza servicios en grupo o no agrupados.
- Deduplica composite key cuando hay colision usando description.
- Valida consistencia de particion (evita mezcla aws + aws-iso).
- Resuelve metadata de servicio (version/serviceCode/template).
- Construye payload final compatible con AWS Calculator.

Manejo de EC2:
- Detecta ec2Enhancement y usa transformador dedicado (lib/ec2.js).

Seguridad de texto:
- sanitize elimina caracteres < > & en textos sensibles.

Export:
- export() llama saveEstimate() y devuelve URL final.
- Para particiones ISO agrega parametros de contrato en URL.

## 8) lib/ec2.js (Transformacion EC2)

Objetivo:
- Convertir configuracion amigable a formato exacto esperado por calculator para ec2Enhancement.

Incluye:
- Parseo de shorthand de pricing:
  - computeSavings1yrNoUpfront
  - instanceSavings3yrAllUpfront
  - reserved/convertible/ondemand/spot
- Normalizacion de tenancy:
  - reserved/convertible se remapean si tenancy es shared.
- Construccion de workload/pricingStrategy/storage/dataTransfer.

Resultado:
- Un objeto calculationComponents listo para payload AWS.

## 9) lib/eks.js (Sizing EKS)

Objetivo:
- Calcular nodeCount recomendado para workloads de contenedores.

Entradas:
- containerCount, containerCpu, containerMemoryGiB
- headroomPercent
- instanceType
- minNodes, azCount
- reservas de sistema y overcommit

Salida:
- required (cpu/mem/pods)
- perNode allocatable
- constraints (nodesByCpu, nodesByMemory, nodesByPods)
- nodeCount final = max(constraints, minNodes, azCount)

Uso principal:
- Alimenta create_eks_estimate en mcp-server.js.

## 10) Suite de Pruebas

test/aws-client.test.js
- searchServices (busqueda, filtros de actividad y subServiceSelector)
- parseDoubleEncodedResponse
- extractInputFields

test/estimate-builder.test.js
- deduplicacion de servicios
- construccion de payload
- fallback cuando falla fetch de definicion
- soporte de particiones y URL compartible

test/ec2.test.js
- transformConfig minimo
- estrategias de pricing (on-demand/savings/reserved/spot)
- manejo de storage y tenancy

test/validation.test.js
- levenshtein / suggestMatch
- validacion de field IDs de configuracion

test/eks.test.js
- sizing base de EKS
- crecimiento de nodos por mayor CPU
- validacion de tipos de instancia no soportados

test/integration.test.js
- prueba real contra Save API de calculator.aws
- valida estimateId + URL funcional

Ejecucion:
- npm test
- node --test test/integration.test.js (si se desea corrida explicita)

## 11) Configuracion y Operacion Local

Scripts definidos (package.json):
- npm run mcp
- npm run test
- npm run build

Build:
- Genera dist/mcp-server.js con esbuild (bundle minificado).
- Genera dist/aws-calculator.zip con fuentes clave.

Config cliente MCP local:
- .vscode/mcp.json apunta a dist/mcp-server.js por stdio.

## 12) Variables de Entorno

Variables opcionales:
- AWS_MANIFEST_URL
- AWS_SAVE_URL

Uso:
- Redirigir endpoints para pruebas, proxy o cambios de infraestructura.

## 13) Seguridad y Riesgos

Modelo de seguridad:
- Proveedor local por stdio.
- Sin autenticacion propia en servidor.
- Control de acceso delegado al cliente MCP que lo ejecuta.

Buenas practicas implementadas:
- Validacion de entradas con Zod.
- Sanitizacion de textos.
- Rechazo de field IDs invalidos con sugerencias.

Riesgos conocidos:
- APIs CloudFront no documentadas oficialmente (pueden cambiar).
- Estado solo en memoria (no persistencia local de estimaciones).

## 14) Mantenimiento y Evolucion Recomendada

Mejoras tecnicas sugeridas:

1. Extraer utilidades de validacion de mcp-server.js a modulo dedicado
- Facilita test unitario directo y reduce codigo duplicado en pruebas.

2. Agregar cobertura de create_eks_estimate
- Tests de integracion de herramienta MCP con mocks de manifest.

3. Introducir capa opcional de persistencia local (feature flag)
- Permitiria retomar estimaciones tras reinicio si el caso de uso lo requiere.

4. Versionado y monitoreo de contratos de API externa
- Detectar cambios en manifest/save endpoint mas rapido.

5. Aumentar observabilidad
- Logs estructurados y niveles de logging configurables.

## 15) Glosario Rapido

- MCP: Model Context Protocol.
- Manifest: catalogo de servicios de AWS Calculator.
- Service Definition: esquema de campos de un servicio.
- ec2Enhancement: formato especial de EC2 usado por la calculadora.
- EstimateBuilder: clase que arma y exporta payload.
- Save API: endpoint que devuelve savedKey para URL compartible.

## 16) Referencias internas

- README.md
- mcp-server.js
- lib/aws-client.js
- lib/estimate-builder.js
- lib/ec2.js
- lib/eks.js
- test/aws-client.test.js
- test/estimate-builder.test.js
- test/ec2.test.js
- test/validation.test.js
- test/eks.test.js
- test/integration.test.js
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- LICENSE
