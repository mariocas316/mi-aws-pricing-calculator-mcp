const EstBuilder = require('./lib/estimate-builder.js');

// CONFIGURACIÓN EXACTA - 76 NODOS TOTALES
// Basado en análisis de costos esperados del TCO
const nodeConfig = {
  'dev': [
    { cluster: 'aks-dev-001', type: 'm6i.xlarge', qty: 5 },
    { cluster: 'aks-dev-001', type: 'r6i.12xlarge', qty: 2 }
  ],
  'qa': [
    { cluster: 'aks-qa-001', type: 'c6i.8xlarge', qty: 8 },
    { cluster: 'aks-qa-001', type: 'm6i.xlarge', qty: 2 },
    { cluster: 'aks-qa-002', type: 'm6i.16xlarge', qty: 5 },
    { cluster: 'aks-qa-002', type: 'm6i.xlarge', qty: 4 },
    { cluster: 'aks-qa-003', type: 'c6i.4xlarge', qty: 3 },
    { cluster: 'aks-qa-003', type: 't3.large', qty: 2 }
  ],
  'prod': [
    { cluster: 'aks-prod-001', type: 'c6i.8xlarge', qty: 8 },
    { cluster: 'aks-prod-001', type: 'm6i.xlarge', qty: 10 },
    { cluster: 'aks-prod-002', type: 'm6i.16xlarge', qty: 4 },
    { cluster: 'aks-prod-002', type: 'r6i.12xlarge', qty: 4 },
    { cluster: 'aks-prod-003', type: 'c5.xlarge', qty: 14 },
    { cluster: 'aks-prod-003', type: 't3.large', qty: 1 },
    { cluster: 'aks-prod-004', type: 'm6i.16xlarge', qty: 3 },
    { cluster: 'aks-prod-004', type: 'r6i.12xlarge', qty: 2 },
    { cluster: 'aks-prod-005', type: 'c6i.4xlarge', qty: 1 }
  ]
};

const scenarios = [
  {
    name: 'AKS→EKS Migration - On-Demand',
    pricing: { model: 'ondemand' },
    expected: 52923
  },
  {
    name: 'AKS→EKS Migration - Savings Plan 1yr No Upfront',
    pricing: { model: 'computeSavings', term: '1yr', upfrontPayment: 'None' },
    expected: 44984
  },
  {
    name: 'AKS→EKS Migration - Savings Plan 3yr No Upfront',
    pricing: { model: 'computeSavings', term: '3yr', upfrontPayment: 'None' },
    expected: 36369
  }
];

async function createOptimizedEstimates() {
  const results = [];
  
  for (const scenario of scenarios) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`Creando: ${scenario.name}`);
    console.log(`Costo esperado: $${scenario.expected.toLocaleString()}/mes`);
    console.log(`${'='.repeat(80)}`);
    
    const builder = new EstBuilder(scenario.name, 'aws');
    
    let totalNodes = 0;
    
    // Agregar nodos por ambiente
    for (const [env, clusters] of Object.entries(nodeConfig)) {
      for (const clusterConfig of clusters) {
        const serviceKey = `ec2Enhancement:${clusterConfig.cluster}`;
        
        console.log(`  [${env.toUpperCase()}] ${clusterConfig.cluster}: ${clusterConfig.qty}x ${clusterConfig.type}`);
        totalNodes += clusterConfig.qty;
        
        builder.addService(serviceKey, {
          region: 'us-east-2',
          quantity: String(clusterConfig.qty),
          instanceType: clusterConfig.type,
          selectedOS: 'linux',
          tenancy: 'shared',
          pricingStrategy: scenario.pricing,
          storageType: 'Storage General Purpose gp3 GB Mo',
          storageAmount: { value: '500', unit: 'gb|NA' }
        }, { group: env === 'dev' ? 'Development' : env === 'qa' ? 'QA' : 'Production' });
      }
    }
    
    console.log(`\n  Total de nodos: ${totalNodes}`);
    
    // Agregar EKS control plane (10 clusters - CADA UNO POR SEPARADO)
    console.log(`  Agregando: AWS EKS Control Planes (10 clusters)`);
    for (let i = 1; i <= 10; i++) {
      builder.addService(`awsEks:cluster-${i}`, {
        region: 'us-east-2',
        numberOfClusters: '1'
      }, { group: 'Infrastructure' });
    }
    
    // Agregar EBS storage
    console.log(`  Agregando: EBS Storage`);
    builder.addService('amazonEbs', {
      region: 'us-east-2',
      snapshotStorageGBMonthly: { value: '0', unit: 'gb|month' }
    }, { group: 'Infrastructure' });
    
    // Agregar NAT Gateways
    console.log(`  Agregando: NAT Gateways (3)`);
    builder.addService('amazonVpc', {
      region: 'us-east-2',
      numberOfNatGateways: '3'
    }, { group: 'Networking' });
    
    // Agregar ALBs
    console.log(`  Agregando: Application Load Balancers (2)`);
    builder.addService('applicationLoadBalancer', {
      region: 'us-east-2',
      numberOfLoadBalancers: '2'
    }, { group: 'Networking' });
    
    // Agregar CloudWatch
    console.log(`  Agregando: CloudWatch Monitoring`);
    builder.addService('amazonCloudWatch', {
      region: 'us-east-2',
      customMetrics: { value: '50', unit: 'count|month' }
    }, { group: 'Monitoring' });
    
    try {
      const exportResult = await builder.export();
      console.log(`\n✓ Estimado creado:`);
      console.log(`  ID: ${exportResult.estimateId}`);
      console.log(`  URL: ${exportResult.shareableUrl}`);
      
      results.push({
        scenario: scenario.name,
        expected: scenario.expected,
        url: exportResult.shareableUrl
      });
    } catch (error) {
      console.error(`✗ Error: ${error.message}`);
    }
  }
  
  // Resumen
  console.log(`\n\n${'='.repeat(80)}`);
  console.log('RESUMEN DE ESTIMADOS OPTIMIZADOS');
  console.log(`${'='.repeat(80)}`);
  
  for (const result of results) {
    console.log(`\n${result.scenario}`);
    console.log(`  Esperado: $${result.expected.toLocaleString()}/mes`);
    console.log(`  URL: ${result.url}`);
  }
  
  return results;
}

createOptimizedEstimates().then(() => {
  process.exit(0);
}).catch(err => {
  console.error('Error fatal:', err);
  process.exit(1);
});
