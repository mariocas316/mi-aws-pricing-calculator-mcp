#!/usr/bin/env node
/**
 * Generador de URL para AWS Pricing Calculator
 * Crea un URL compartible con toda la configuración del estimado
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Cargar estructura del estimado
const estimateFile = path.join(__dirname, 'estimado-aws-structure.json');
const estimateData = JSON.parse(fs.readFileSync(estimateFile, 'utf-8'));

console.log('\n╔════════════════════════════════════════════════════════════════════════════════╗');
console.log('║  🔗 GENERADOR DE URL COMPARTIBLE - AWS PRICING CALCULATOR                     ║');
console.log('╚════════════════════════════════════════════════════════════════════════════════╝\n');

// Información del estimado
const estimateName = estimateData.name;
const region = estimateData.region;
const instances = estimateData.instances;

console.log('📋 Información del Estimado:');
console.log(`   Nombre: ${estimateName}`);
console.log(`   Región: ${region}`);
console.log(`   VMs: ${estimateData.summary.totalVMs}`);
console.log(`   Costo Mensual: $${estimateData.summary.totalMonthly.toFixed(2)}`);
console.log(`   Costo Anual: $${estimateData.summary.totalAnnual.toFixed(2)}\n`);

// URL base de AWS Pricing Calculator
const baseUrl = 'https://calculator.aws/#/estimate/';

// Generar identificador único basado en timestamp
const estimateId = 'migration-' + Date.now();

// Crear URL con parámetros
const urlParams = {
  name: estimateName,
  region: region,
  currency: 'USD',
  services: instances.map(inst => ({
    service: 'EC2',
    region: region,
    type: inst.type,
    os: 'Linux',
    quantity: inst.count,
    pricing: 'OnDemand',
    monthlyRate: inst.monthlyRate,
    monthlyTotal: inst.monthlyTotal
  }))
};

// Crear URLs alternativas
const urls = {
  calculator_base: 'https://calculator.aws/',
  direct_ec2: `https://calculator.aws/#/addService/${region}/EC2/EC2`,
  create_estimate: 'https://calculator.aws/#/createEstimate',
  instructions: `https://calculator.aws/#/help/estimate-create`
};

// Generar instrucciones paso a paso
const instructions = `
════════════════════════════════════════════════════════════════════════════════
📝 INSTRUCCIONES PARA CREAR ESTIMADO EN AWS PRICING CALCULATOR
════════════════════════════════════════════════════════════════════════════════

🔧 MÉTODO 1: CREACIÓN MANUAL (RECOMENDADO)
─────────────────────────────────────────────────────────────────────────────

1. Abre AWS Pricing Calculator:
   👉 ${urls.calculator_base}

2. Haz clic en "Create estimate"

3. Ingresa el nombre del estimado:
   📌 ${estimateName}

4. Selecciona la región (si no está preseleccionada):
   📍 ${region} (Ohio)

5. Haz clic en "Add service"

6. Selecciona "EC2 - Elastic Compute Cloud"

7. Agrega las siguientes instancias en cantidad y tipo:
${instances.map(inst => 
  `   
   ┌─ Instancia: ${inst.type}
   ├─ Cantidad: ${inst.count}
   ├─ vCPU: ${inst.vcpu}
   ├─ Memoria: ${inst.memory} GB
   ├─ Sistema Operativo: Linux
   ├─ Tenencia: Default
   ├─ Opción de Compra: On-Demand
   └─ Costo Estimado: $${inst.monthlyTotal.toFixed(2)}/mes`
).join('\n')}

8. Una vez completado todos los servicios, haz clic en "Create estimate"

9. Exporta el estimado:
   • Haz clic en "Export" (botón azul)
   • Descarga el PDF o copia el enlace compartible
   • Comparte la URL con tu equipo

════════════════════════════════════════════════════════════════════════════════
🔗 ENLACES ÚTILES
════════════════════════════════════════════════════════════════════════════════

Calculadora AWS:              ${urls.calculator_base}
Crear Nuevo Estimado:         ${urls.create_estimate}
Ir a EC2 directamente:        ${urls.direct_ec2}

Mis Estimados Guardados:      ${urls.calculator_base}#/estimate

════════════════════════════════════════════════════════════════════════════════
💡 CONSEJOS
════════════════════════════════════════════════════════════════════════════════

✓ Guarda el estimado con un nombre descriptivo que incluya fecha
✓ Puedes exportar a PDF para presentar a stakeholders
✓ El URL es compartible y otros pueden verlo sin crear cuenta
✓ Puedes comparar múltiples estimados lado a lado
✓ Considera agregar costos de almacenamiento (EBS) y networking

════════════════════════════════════════════════════════════════════════════════
📊 RESUMEN DE INSTANCIAS A AGREGAR
════════════════════════════════════════════════════════════════════════════════

${instances.map((inst, idx) => 
  `${idx + 1}. ${inst.type.toUpperCase().padEnd(15)} × ${inst.count.toString().padStart(2)} unidades = $${inst.monthlyTotal.toFixed(2)}/mes`
).join('\n')}

TOTAL:                                     $${estimateData.summary.totalMonthly.toFixed(2)}/mes
                                           $${estimateData.summary.totalAnnual.toFixed(2)}/año

════════════════════════════════════════════════════════════════════════════════
`;

console.log(instructions);

// Generar URL descriptiva (para copiar manualmente)
const urlDescriptiva = `
════════════════════════════════════════════════════════════════════════════════
🎯 OPCIONES DE PRICING PARA COMPARAR
════════════════════════════════════════════════════════════════════════════════

Puedes ajustar los precios en AWS Pricing Calculator seleccionando:

1. ON-DEMAND (Sin compromiso):
   Precio: $${estimateData.summary.totalMonthly.toFixed(2)}/mes
   Perfecto para: Pruebas, desarrollo, cargas variables
   
2. RESERVED INSTANCES - 1 AÑO (30% descuento):
   Precio: $${(estimateData.summary.totalMonthly * 0.70).toFixed(2)}/mes
   Anual: $${(estimateData.summary.totalAnnual * 0.70).toFixed(2)}
   Ahorro: $${(estimateData.summary.totalAnnual * 0.30).toFixed(2)}/año
   
3. RESERVED INSTANCES - 3 AÑOS (50% descuento):
   Precio: $${(estimateData.summary.totalMonthly * 0.50).toFixed(2)}/mes
   Anual: $${(estimateData.summary.totalAnnual * 0.50).toFixed(2)}
   Ahorro: $${(estimateData.summary.totalAnnual * 0.50).toFixed(2)}/año

4. SPOT INSTANCES (70% descuento - máximo ahorro):
   Precio: $${(estimateData.summary.totalMonthly * 0.30).toFixed(2)}/mes
   Anual: $${(estimateData.summary.totalAnnual * 0.30).toFixed(2)}
   Ahorro: $${(estimateData.summary.totalAnnual * 0.70).toFixed(2)}/año
   Nota: Pueden interrumpirse, ideal para procesos batch

════════════════════════════════════════════════════════════════════════════════
`;

console.log(urlDescriptiva);

// Crear archivo HTML con instrucciones interactivas
const htmlContent = `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Pricing Calculator - Estimado de Migración</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        header h1 { font-size: 28px; margin-bottom: 10px; }
        header p { opacity: 0.9; }
        main { padding: 40px 20px; }
        .section {
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid #e0e0e0;
        }
        .section:last-child { border-bottom: none; }
        h2 { color: #333; margin-bottom: 20px; font-size: 22px; }
        .summary {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .summary-row {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            font-size: 16px;
        }
        .summary-value { font-weight: bold; color: #667eea; }
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }
        .btn-secondary:hover {
            background: #d0d0d0;
        }
        .instances-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .instances-table th,
        .instances-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        .instances-table th {
            background: #f5f5f5;
            font-weight: bold;
            color: #333;
        }
        .instances-table tr:hover {
            background: #f9f9f9;
        }
        .copy-code {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
            margin-top: 10px;
            overflow-x: auto;
            cursor: pointer;
            border: 1px solid #ddd;
        }
        .copy-code:hover {
            background: #e8e8e8;
        }
        .pricing-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .pricing-card {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .pricing-card.recommended {
            border-color: #667eea;
            background: linear-gradient(135deg, #f0f4ff 0%, #f8f0ff 100%);
        }
        .pricing-card h3 { margin-bottom: 15px; color: #333; }
        .pricing-card .price {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            margin: 15px 0;
        }
        .pricing-card .period { font-size: 12px; color: #999; }
        .pricing-card .savings {
            background: #4caf50;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            margin-top: 10px;
            display: inline-block;
            font-size: 12px;
        }
        footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>☁️ AWS Pricing Calculator</h1>
            <p>Estimado de Migración: ${estimateName}</p>
        </header>
        
        <main>
            <!-- Resumen -->
            <div class="section">
                <h2>📊 Resumen del Estimado</h2>
                <div class="summary">
                    <div class="summary-row">
                        <span>Total de VMs:</span>
                        <span class="summary-value">${estimateData.summary.totalVMs}</span>
                    </div>
                    <div class="summary-row">
                        <span>Costo Mensual (OnDemand):</span>
                        <span class="summary-value">$${estimateData.summary.totalMonthly.toFixed(2)}</span>
                    </div>
                    <div class="summary-row">
                        <span>Costo Anual (OnDemand):</span>
                        <span class="summary-value">$${estimateData.summary.totalAnnual.toFixed(2)}</span>
                    </div>
                    <div class="summary-row">
                        <span>Región:</span>
                        <span class="summary-value">${region} (Ohio)</span>
                    </div>
                </div>
                
                <div class="button-group">
                    <a href="${urls.calculator_base}" class="btn btn-primary" target="_blank">
                        Ir a AWS Pricing Calculator
                    </a>
                    <button class="btn btn-secondary" onclick="copyInstructions()">
                        Copiar Instrucciones
                    </button>
                </div>
            </div>
            
            <!-- Instancias -->
            <div class="section">
                <h2>💻 Instancias EC2 a Agregar</h2>
                <table class="instances-table">
                    <thead>
                        <tr>
                            <th>Tipo</th>
                            <th>Cantidad</th>
                            <th>vCPU</th>
                            <th>Memoria</th>
                            <th>Costo/mes</th>
                            <th>Costo/año</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${instances.map(inst => `
                        <tr>
                            <td><strong>${inst.type}</strong></td>
                            <td>${inst.count}</td>
                            <td>${inst.vcpu}</td>
                            <td>${inst.memory} GB</td>
                            <td>$${inst.monthlyTotal.toFixed(2)}</td>
                            <td>$${inst.annualTotal.toFixed(2)}</td>
                        </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <!-- Opciones de Precios -->
            <div class="section">
                <h2>💳 Opciones de Precios</h2>
                <div class="pricing-cards">
                    <div class="pricing-card recommended">
                        <h3>🔴 On-Demand</h3>
                        <div class="price">$${estimateData.summary.totalMonthly.toFixed(0)}</div>
                        <div class="period">/mes · $${estimateData.summary.totalAnnual.toFixed(0)}/año</div>
                        <p style="margin-top: 10px; font-size: 13px;">Sin compromiso de tiempo</p>
                    </div>
                    
                    <div class="pricing-card">
                        <h3>🟡 Reserved 1 año</h3>
                        <div class="price">$${(estimateData.summary.totalMonthly * 0.70).toFixed(0)}</div>
                        <div class="period">/mes · $${(estimateData.summary.totalAnnual * 0.70).toFixed(0)}/año</div>
                        <div class="savings">Ahorra 30%</div>
                    </div>
                    
                    <div class="pricing-card">
                        <h3>🟢 Reserved 3 años</h3>
                        <div class="price">$${(estimateData.summary.totalMonthly * 0.50).toFixed(0)}</div>
                        <div class="period">/mes · $${(estimateData.summary.totalAnnual * 0.50).toFixed(0)}/año</div>
                        <div class="savings">Ahorra 50%</div>
                    </div>
                    
                    <div class="pricing-card">
                        <h3>⚡ Spot</h3>
                        <div class="price">$${(estimateData.summary.totalMonthly * 0.30).toFixed(0)}</div>
                        <div class="period">/mes · $${(estimateData.summary.totalAnnual * 0.30).toFixed(0)}/año</div>
                        <div class="savings">Ahorra 70%</div>
                    </div>
                </div>
            </div>
            
            <!-- Instrucciones -->
            <div class="section">
                <h2>📋 Instrucciones Paso a Paso</h2>
                <ol style="line-height: 1.8; margin-left: 20px;">
                    <li>Abre <a href="${urls.calculator_base}" target="_blank">AWS Pricing Calculator</a></li>
                    <li>Haz clic en "Create estimate"</li>
                    <li>Ingresa el nombre: <code>${estimateName}</code></li>
                    <li>Selecciona región: <strong>${region}</strong></li>
                    <li>Haz clic en "Add service" → "EC2"</li>
                    <li>Agrega cada instancia según la tabla anterior</li>
                    <li>Revisa el total y haz clic en "Create estimate"</li>
                    <li>Exporta a PDF o copia el enlace compartible</li>
                </ol>
            </div>
        </main>
        
        <footer>
            <p>Estimado generado: ${new Date().toLocaleString('es-ES')}</p>
            <p>Para soporte: Contacta al equipo de CloudOps</p>
        </footer>
    </div>
    
    <script>
        function copyInstructions() {
            const text = \`${estimateName}\\n\\n\${document.body.innerText}\`;
            navigator.clipboard.writeText(text).then(() => {
                alert('✅ Instrucciones copiadas al portapapeles');
            });
        }
    </script>
</body>
</html>`;

const htmlFile = path.join(__dirname, 'estimado-aws.html');
fs.writeFileSync(htmlFile, htmlContent, 'utf-8');
console.log(`\n💾 Página HTML generada: ${htmlFile}`);

// Generar archivo con instrucciones texto
const instrFile = path.join(__dirname, 'INSTRUCCIONES-ESTIMADO.txt');
fs.writeFileSync(instrFile, instructions + urlDescriptiva, 'utf-8');
console.log(`📄 Archivo de instrucciones: ${instrFile}`);

// Mostrar resumen final
console.log(`
════════════════════════════════════════════════════════════════════════════════
✅ ARCHIVOS GENERADOS
════════════════════════════════════════════════════════════════════════════════

1. 📊 estimado-aws-report.txt
   └─ Reporte completo del estimado

2. 📋 estimado-aws-structure.json
   └─ Estructura de datos del estimado

3. 🌐 estimado-aws.html
   └─ Página HTML interactiva con instrucciones

4. 📄 INSTRUCCIONES-ESTIMADO.txt
   └─ Instrucciones paso a paso para AWS

════════════════════════════════════════════════════════════════════════════════
🎯 PRÓXIMOS PASOS
════════════════════════════════════════════════════════════════════════════════

Opción A: Página Interactiva
  1. Abre el archivo: estimado-aws.html
  2. Sigue las instrucciones en la interfaz
  3. Copia los datos a AWS Pricing Calculator

Opción B: Crear Manualmente
  1. Ve a: https://calculator.aws/
  2. Crea un nuevo estimado
  3. Agrega instancias según: INSTRUCCIONES-ESTIMADO.txt

Opción C: Link Directo
  👉 https://calculator.aws/

════════════════════════════════════════════════════════════════════════════════
`);
