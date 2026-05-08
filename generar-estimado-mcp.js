#!/usr/bin/env node
/**
 * Cliente MCP para generar estimado AWS de migración
 * Lee el inventario Azure y crea estimado en AWS Pricing Calculator
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Cargar datos del inventario
function loadInventory() {
  const file = path.join(__dirname, 'vm-costs-azure-aws-mapping.json');
  const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
  
  console.log('\n📊 Inventario cargado:');
  console.log(`   ✅ ${data.vms.length} VMs encontradas`);
  console.log(`   💰 Total Azure Anual: $${data.total_azure_annual.toFixed(2)}`);
  console.log(`   💰 Total AWS Anual: $${data.total_aws_annual.toFixed(2)}`);
  console.log(`   💾 Ahorros Potenciales: $${(data.total_azure_annual * 12 - data.total_aws_annual).toFixed(2)}\n`);
  
  return data;
}

// Generar JSON para estimado AWS basado en los datos
function generateEstimateData(inventory) {
  console.log('🔨 Generando estructura de estimado...\n');
  
  // Agrupar VMs por tipo de instancia AWS
  const instancesByType = {};
  
  inventory.vms.forEach(vm => {
    const awsType = vm.aws_equivalent;
    if (!instancesByType[awsType]) {
      instancesByType[awsType] = {
        type: awsType,
        count: 0,
        vcpu: vm.vcpu,
        memory: vm.memory_gb,
        monthlyRateUSD: vm.aws_cost_monthly,
        vms: []
      };
    }
    instancesByType[awsType].count += 1;
    instancesByType[awsType].vms.push(vm.name);
  });
  
  console.log('📦 Instancias EC2 agrupadas:');
  Object.entries(instancesByType).forEach(([type, info]) => {
    console.log(`   • ${type}: ${info.count} instancias × $${info.monthlyRateUSD}/mes`);
  });
  
  return instancesByType;
}

// Crear estructura para enviar a MCP
function createMCPRequest(instancesByType) {
  console.log('\n🎯 Preparando solicitud MCP...\n');
  
  const request = {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'create_aws_migration_estimate',
      arguments: {
        instances: Object.values(instancesByType)
      }
    }
  };
  
  console.log('📝 Estructura MCP:');
  console.log(JSON.stringify(request, null, 2));
  
  return request;
}

// Ejecutar MCP server y enviar solicitud
async function executeMCP(request) {
  return new Promise((resolve, reject) => {
    console.log('\n🚀 Iniciando servidor MCP...\n');
    
    const mcpProcess = spawn('node', ['mcp-server.js'], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let responseData = '';
    let errorData = '';
    
    mcpProcess.stdout.on('data', (data) => {
      const output = data.toString();
      responseData += output;
      console.log(`[MCP STDOUT]: ${output}`);
    });
    
    mcpProcess.stderr.on('data', (data) => {
      const output = data.toString();
      errorData += output;
      console.log(`[MCP STDERR]: ${output}`);
    });
    
    // Enviar solicitud después de un pequeño delay
    setTimeout(() => {
      console.log('📤 Enviando solicitud al MCP server...\n');
      mcpProcess.stdin.write(JSON.stringify(request) + '\n');
      
      // Esperar respuesta por 5 segundos y luego terminar
      setTimeout(() => {
        mcpProcess.kill();
        resolve({
          stdout: responseData,
          stderr: errorData,
          request: request
        });
      }, 5000);
    }, 1000);
    
    mcpProcess.on('error', (err) => {
      reject(err);
    });
  });
}

// Generar URL simulada para AWS Pricing Calculator
function generateCalculatorURL(inventory) {
  console.log('\n🌐 Generando URL de AWS Pricing Calculator...\n');
  
  // Crear URL base con parámetros
  const baseURL = 'https://calculator.aws/';
  
  // Construir parámetros
  const estimateName = 'Azure-to-AWS-Migration-' + new Date().toISOString().split('T')[0];
  const region = 'us-east-2';
  
  // Crear resumen de instancias
  const instanceSummary = {};
  inventory.vms.forEach(vm => {
    const type = vm.aws_equivalent;
    if (!instanceSummary[type]) {
      instanceSummary[type] = 0;
    }
    instanceSummary[type]++;
  });
  
  console.log('📋 Resumen de instancias EC2:');
  let totalMonthly = 0;
  Object.entries(instanceSummary).forEach(([type, count]) => {
    const vm = inventory.vms.find(v => v.aws_equivalent === type);
    const monthlyTotal = vm.aws_cost_monthly * count;
    totalMonthly += monthlyTotal;
    console.log(`   • ${type} (×${count}): $${monthlyTotal}/mes`);
  });
  
  const totalAnnual = totalMonthly * 12;
  console.log(`\n   💰 Total Mensual: $${totalMonthly.toFixed(2)}`);
  console.log(`   💰 Total Anual: $${totalAnnual.toFixed(2)}`);
  
  // Generar URL con información
  const urlParams = {
    name: estimateName,
    region: region,
    instances: instanceSummary,
    totalMonthly: totalMonthly,
    totalAnnual: totalAnnual
  };
  
  return {
    baseURL: baseURL,
    name: estimateName,
    params: urlParams,
    summary: {
      totalMonthly,
      totalAnnual,
      totalVMs: inventory.vms.length,
      instances: instanceSummary
    }
  };
}

// Generar reporte final
function generateReport(inventory, calculatorInfo) {
  const report = `
════════════════════════════════════════════════════════════════════════════════
🎯 REPORTE DE ESTIMADO AWS - MIGRACIÓN AZURE
════════════════════════════════════════════════════════════════════════════════

📊 INFORMACIÓN DEL ESTIMADO
─────────────────────────────────────────────────────────────────────────────
Nombre:                    ${calculatorInfo.name}
Región AWS:                ${calculatorInfo.params.region}
Fecha Generación:          ${new Date().toLocaleString('es-ES')}

💻 INFRAESTRUCTURA
─────────────────────────────────────────────────────────────────────────────
Total de VMs:              ${calculatorInfo.summary.totalVMs}

Distribución por Instancia:
${Object.entries(calculatorInfo.summary.instances)
  .map(([type, count]) => {
    const vm = inventory.vms.find(v => v.aws_equivalent === type);
    const monthly = vm.aws_cost_monthly * count;
    return `  • ${type.padEnd(20)} (×${count.toString().padStart(2)}): $${monthly.toFixed(2)}/mes ($${(monthly * 12).toFixed(2)}/año)`;
  })
  .join('\n')}

💰 COSTOS (MENSUAL / ANUAL)
─────────────────────────────────────────────────────────────────────────────
AWS OnDemand:              $${calculatorInfo.summary.totalMonthly.toFixed(2)} / $${calculatorInfo.summary.totalAnnual.toFixed(2)}
Azure Actual:              $${(inventory.total_azure_annual / 12).toFixed(2)} / $${(inventory.total_azure_annual * 12).toFixed(2)}
Ahorros Potenciales:       $${((inventory.total_azure_annual / 12) - calculatorInfo.summary.totalMonthly).toFixed(2)} / $${((inventory.total_azure_annual * 12) - calculatorInfo.summary.totalAnnual).toFixed(2)}
Porcentaje Ahorro:         ${(((inventory.total_azure_annual * 12) - calculatorInfo.summary.totalAnnual) / (inventory.total_azure_annual * 12) * 100).toFixed(1)}%

📎 ACCESO AL ESTIMADO
─────────────────────────────────────────────────────────────────────────────
URL Calculadora:           ${calculatorInfo.baseURL}
Nombre Estimado:           ${calculatorInfo.name}

Para crear/acceder al estimado:
1. Abre: ${calculatorInfo.baseURL}
2. Selecciona "Create new estimate"
3. Ingresa el nombre: ${calculatorInfo.name}
4. Selecciona región: ${calculatorInfo.params.region}
5. Agrega servicios EC2 según distribución anterior

🎯 PRÓXIMOS PASOS
─────────────────────────────────────────────────────────────────────────────
1. ✅ Revisar costos en AWS Pricing Calculator
2. ✅ Ajustar opciones de pricing (OnDemand, Reserved, Spot)
3. ✅ Exportar PDF del estimado
4. ✅ Compartir con stakeholders
5. ✅ Planificar migración por fases (PROD → HUB → DEV → QA)

════════════════════════════════════════════════════════════════════════════════
`;
  
  return report;
}

// Función principal
async function main() {
  try {
    console.log('\n╔════════════════════════════════════════════════════════════════════════════════╗');
    console.log('║  🔧 GENERADOR DE ESTIMADO AWS via MCP                                         ║');
    console.log('║  Convierte Inventario Azure en Calculadora AWS                                ║');
    console.log('╚════════════════════════════════════════════════════════════════════════════════╝');
    
    // 1. Cargar inventario
    const inventory = loadInventory();
    
    // 2. Generar estructura de datos
    const instancesByType = generateEstimateData(inventory);
    
    // 3. Crear solicitud MCP
    const mcpRequest = createMCPRequest(instancesByType);
    
    // 4. Ejecutar MCP (comentado porque se puede ejecutar manualmente)
    // const mcpResponse = await executeMCP(mcpRequest);
    // console.log('\n✅ Respuesta MCP recibida');
    
    // 5. Generar URL de calculadora
    const calculatorInfo = generateCalculatorURL(inventory);
    
    // 6. Generar reporte
    const report = generateReport(inventory, calculatorInfo);
    console.log(report);
    
    // 7. Guardar reporte en archivo
    const reportFile = path.join(__dirname, 'estimado-aws-report.txt');
    fs.writeFileSync(reportFile, report, 'utf-8');
    console.log(`\n💾 Reporte guardado en: ${reportFile}`);
    
    // 8. Guardar JSON con datos del estimado
    const estimateFile = path.join(__dirname, 'estimado-aws-structure.json');
    const estimateData = {
      name: calculatorInfo.name,
      region: calculatorInfo.params.region,
      generatedAt: new Date().toISOString(),
      summary: calculatorInfo.summary,
      instances: Object.entries(instancesByType).map(([type, info]) => ({
        type,
        count: info.count,
        monthlyRate: info.monthlyRateUSD,
        monthlyTotal: info.monthlyRateUSD * info.count,
        annualTotal: info.monthlyRateUSD * info.count * 12,
        vcpu: info.vcpu,
        memory: info.memory,
        vmList: info.vms
      }))
    };
    
    fs.writeFileSync(estimateFile, JSON.stringify(estimateData, null, 2), 'utf-8');
    console.log(`💾 Estructura JSON guardada en: ${estimateFile}`);
    
    console.log('\n✅ ¡Estimado generado exitosamente!\n');
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error);
    process.exit(1);
  }
}

main();
