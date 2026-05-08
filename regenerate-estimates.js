const EstBuilder = require('./lib/estimate-builder.js');

// Configuración común para los 3 estimados (76 nodos)
const nodeDistribution = [
  { type: 'ec2Enhancement:dev-aks-be-002', quantity: 5, instanceType: 'm6i.xlarge' },      // +2
  { type: 'ec2Enhancement:dev-aks-db-001', quantity: 3, instanceType: 'r6i.12xlarge' },    // +1
  { type: 'ec2Enhancement:qa-aks-be-001', quantity: 9, instanceType: 'c6i.8xlarge' },      // +3
  { type: 'ec2Enhancement:qa-aks-be-002', quantity: 7, instanceType: 'm6i.16xlarge' },     // +2
  { type: 'ec2Enhancement:qa-aks-db-001', quantity: 6, instanceType: 'm6i.xlarge' },       // +2
  { type: 'ec2Enhancement:qa-aks-ap-001', quantity: 3, instanceType: 'm6i.xlarge' },       // +1
  { type: 'ec2Enhancement:prod-aks-be-001', quantity: 12, instanceType: 'c6i.8xlarge' },   // +4
  { type: 'ec2Enhancement:prod-aks-be-002', quantity: 4, instanceType: 'c6i.4xlarge' },    // +1
  { type: 'ec2Enhancement:prod-aks-be-003', quantity: 8, instanceType: 'm6i.16xlarge' },   // +2
  { type: 'ec2Enhancement:prod-aks-db-001', quantity: 5, instanceType: 'r6i.12xlarge' },   // +1
  { type: 'ec2Enhancement:prod-aks-db-002', quantity: 2, instanceType: 'r6i.12xlarge' },
  { type: 'ec2Enhancement:prod-aks-ap-001', quantity: 14, instanceType: 'c5.xlarge' },
  { type: 'ec2Enhancement:prod-aks-ap-002', quantity: 3, instanceType: 't3.large' }
];

const estimates = [
  {
    name: 'EKS AKS Nodes - On Demand',
    pricing: { model: 'ondemand' }
  },
  {
    name: 'EKS AKS Nodes - Savings Plan 1yr No Upfront',
    pricing: { model: 'computeSavings', term: '1yr', upfrontPayment: 'None' }
  },
  {
    name: 'EKS AKS Nodes - Savings Plan 3yr No Upfront',
    pricing: { model: 'computeSavings', term: '3yr', upfrontPayment: 'None' }
  }
];

async function regenerateEstimates() {
  const results = [];
  
  for (const est of estimates) {
    console.log(`\n\n=== Creando estimado: ${est.name} ===`);
    
    const builder = new EstBuilder(est.name, 'aws');
    
    // Agregar nodos EC2
    for (const node of nodeDistribution) {
      builder.addService(node.type, {
        region: 'us-east-2',
        quantity: String(node.quantity),
        instanceType: node.instanceType,
        selectedOS: 'linux',
        tenancy: 'shared',
        pricingStrategy: est.pricing,
        storageType: 'Storage General Purpose gp3 GB Mo',
        storageAmount: { value: '500', unit: 'gb|NA' }
      }, { group: node.type.includes('dev') ? 'Development' : node.type.includes('qa') ? 'QA' : 'Production' });
    }
    
    // Agregar EKS (10 clusters)
    builder.addService('awsEks', {
      region: 'us-east-2',
      numberOfClusters: '10'
    }, { group: 'Infrastructure' });
    
    // Agregar EBS (almacenamiento)
    builder.addService('amazonEbsSnapshots', {
      region: 'us-east-2',
      snapshotStorageGBMonthly: { value: '0', unit: 'gb|month' }
    }, { group: 'Infrastructure' });
    
    // Agregar NAT Gateways
    builder.addService('amazonEC2NatGateway', {
      region: 'us-east-2',
      numberOfNatGateways: '3'
    }, { group: 'Networking' });
    
    // Agregar ALB
    builder.addService('applicationLoadBalancer', {
      region: 'us-east-2',
      numberOfLoadBalancers: '2'
    }, { group: 'Networking' });
    
    // Agregar CloudWatch
    builder.addService('amazonCloudWatch', {
      region: 'us-east-2',
      customMetrics: { value: '50', unit: 'count|month' }
    }, { group: 'Monitoring' });
    
    try {
      const exportResult = await builder.export();
      console.log(`✓ URL generada: ${exportResult.shareableUrl}`);
      results.push({
        scenario: est.name,
        url: exportResult.shareableUrl
      });
    } catch (error) {
      console.error(`✗ Error: ${error.message}`);
    }
  }
  
  console.log('\n\n=== RESUMEN DE URLs ===');
  results.forEach(r => {
    console.log(`${r.scenario}:`);
    console.log(`  ${r.url}`);
    console.log('');
  });
  
  return results;
}

regenerateEstimates().then(results => {
  console.log('\n✓ Regeneración completada');
  process.exit(0);
}).catch(err => {
  console.error('Error fatal:', err);
  process.exit(1);
});
