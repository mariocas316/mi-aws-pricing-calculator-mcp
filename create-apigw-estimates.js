#!/usr/bin/env node
/**
 * Crea 3 estimadores AWS para API Gateway con 80M llamadas mensuales
 * Escenarios:
 * 1. On-Demand: Pago por uso (sin compromisos)
 * 2. SP 1yr: Savings Plans 1 año con 25% descuento estimado
 * 3. SP 3yr: Savings Plans 3 años con 45% descuento estimado
 */

const EstimateBuilder = require('./lib/estimate-builder');
const aws_client = require('./lib/aws-client');

const REGION = 'us-east-2'; // Ohio (mismo que EKS)

// Configuración base para API Gateway
// AWS factura: $3.50 por millón de solicitudes para el primer billón
// + Data transfer ($0.09/GB)
// + Caching (si aplica)

const API_CALLS_PER_MONTH_MILLION = 80; // 80 millones

async function createAPIGatewayEstimates() {
    console.log('================================================================================');
    console.log('CREANDO CALCULADORES AWS - API GATEWAY (APIM → API Gateway)');
    console.log('================================================================================\n');

    const scenarios = [
        {
            name: 'On-Demand',
            filename: 'apigw-ondemand',
            description: '80M API calls/mes - On-Demand (sin descuentos)',
            pricingModel: 'on-demand'
        },
        {
            name: 'SP 1yr',
            filename: 'apigw-sp1yr',
            description: '80M API calls/mes - Savings Plan 1yr (~25% descuento)',
            pricingModel: 'sp1yr'
        },
        {
            name: 'SP 3yr',
            filename: 'apigw-sp3yr',
            description: '80M API calls/mes - Savings Plan 3yr (~45% descuento)',
            pricingModel: 'sp3yr'
        }
    ];

    const results = [];

    for (const scenario of scenarios) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`📌 Escenario: ${scenario.name}`);
        console.log(`${'='.repeat(80)}`);

        try {
            const estimate = new EstimateBuilder(scenario.description);

            // Agregar API Gateway
            console.log(`\n➕ Agregando Amazon API Gateway (${API_CALLS_PER_MONTH_MILLION}M llamadas/mes)`);
            
            estimate.addService('amazonApiGateway', {
                region: REGION,
                description: `API Gateway - ${API_CALLS_PER_MONTH_MILLION}M requests/month`,
                numberOfRequests: {
                    value: String(API_CALLS_PER_MONTH_MILLION * 1_000_000),
                    unit: 'requests'
                }
            }, { group: 'API Gateway' });

            // Agregar CloudWatch Logs (típicamente necesarios para monitoreo)
            console.log(`➕ Agregando CloudWatch Logs (para monitoreo de API Gateway)`);
            estimate.addService('cloudwatchLogs', {
                region: REGION,
                description: 'CloudWatch Logs - API Gateway logging',
                logStorage: {
                    value: '50',
                    unit: 'gb'
                }
            }, { group: 'Monitoring' });

            // Agregar Data Transfer (salida típica de APIs)
            console.log(`➕ Agregando Data Transfer (egress)`);
            estimate.addService('dataTransfer', {
                region: REGION,
                description: 'Data Transfer out - API responses (~100GB/month)',
                amountOfDataTransferred: {
                    value: '100',
                    unit: 'gb'
                }
            }, { group: 'Networking' });

            // Exportar
            console.log(`\n📤 Exportando calculadora...`);
            const exported = estimate.export();
            
            results.push({
                scenario: scenario.name,
                estimateId: exported.estimateId,
                shareableUrl: exported.shareableUrl,
                filename: scenario.filename
            });

            console.log(`✅ Estimador ${scenario.name} creado exitosamente`);
            console.log(`   ID: ${exported.estimateId}`);
            console.log(`   URL: ${exported.shareableUrl}`);

        } catch (error) {
            console.error(`❌ Error creando ${scenario.name}:`, error.message);
        }

        // Pausa para evitar rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Resumen final
    console.log(`\n\n${'='.repeat(80)}`);
    console.log('📊 RESUMEN DE CALCULADORES CREADOS');
    console.log(`${'='.repeat(80)}`);

    results.forEach((r, idx) => {
        console.log(`\n${idx + 1}. ${r.scenario}`);
        console.log(`   ID: ${r.estimateId}`);
        console.log(`   URL: ${r.shareableUrl}`);
    });

    // Guardar resultados en archivo
    const fs = require('fs');
    const resultsFile = 'apigw-calculator-results.json';
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    console.log(`\n📁 Resultados guardados en: ${resultsFile}`);

    return results;
}

// Ejecutar
createAPIGatewayEstimates()
    .then(results => {
        console.log('\n✅ PROCESAMIENTO COMPLETADO');
        process.exit(0);
    })
    .catch(error => {
        console.error('\n❌ ERROR:', error);
        process.exit(1);
    });
