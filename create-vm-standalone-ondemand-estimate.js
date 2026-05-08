const fs = require('fs');
const path = require('path');
const EstimateBuilder = require('./lib/estimate-builder');

const INPUT_FILE = path.join(__dirname, 'vm-standalone-aws-input.json');
const SUMMARY_FILE = path.join(__dirname, 'vm-standalone-summary.json');

async function run() {
  const input = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf8'));
  const summary = JSON.parse(fs.readFileSync(SUMMARY_FILE, 'utf8'));

  const region = input.region || 'us-east-2';
  const target = input.target_monthly_from_tco;

  console.log('='.repeat(90));
  console.log('CREANDO CALCULADORA ON-DEMAND - VMs STANDALONE (AZURE -> AWS)');
  console.log('='.repeat(90));
  console.log(`VMs inventariadas: ${summary.vm_standalone_count}`);
  console.log(`Target On-Demand TCO: $${target}/mes`);
  console.log(`Región: ${region}`);

  const builder = new EstimateBuilder(input.estimate_name || 'VMs Standalone Azure to AWS On-Demand', 'aws');

  let totalQty = 0;
  let totalDiskGb = 0;

  input.ec2_groups.forEach((g, idx) => {
    const qty = Number(g.quantity || 0);
    const diskGb = Number(g.disk_avg_gb || 30);
    totalQty += qty;
    totalDiskGb += qty * diskGb;

    builder.addService(`ec2Enhancement:vm-standalone-${idx + 1}`, {
      region,
      quantity: String(qty),
      instanceType: g.aws_instance_type,
      selectedOS: g.aws_selected_os,
      tenancy: 'shared',
      pricingStrategy: { model: 'ondemand' },
      storageType: 'Storage General Purpose gp3 GB Mo',
      storageAmount: { value: String(diskGb), unit: 'gb|NA' },
      snapshotFrequency: '0',
      description: `${g.aws_instance_type} ${g.aws_selected_os} x${qty}`,
    }, { group: g.aws_selected_os === 'windows' ? 'Windows Standalone' : 'Linux Standalone' });
  });

  // Complementary service: CloudWatch basic custom metrics equivalent from inventory
  const metricsCount = Number(summary?.complementary_services?.azure_monitor_enabled || 0);
  if (metricsCount > 0) {
    builder.addService('amazonCloudWatch', {
      region,
      customMetrics: { value: String(metricsCount), unit: 'count|month' },
      description: `CloudWatch metrics for ${metricsCount} monitored VMs`,
    }, { group: 'Monitoring' });
  }

  console.log(`\nEC2 grupos cargados: ${input.ec2_groups.length}`);
  console.log(`Total VMs en calculadora: ${totalQty}`);
  console.log(`Total disco aprox (GB): ${totalDiskGb}`);

  const exported = await builder.export();

  console.log('\n' + '='.repeat(90));
  console.log('RESULTADO');
  console.log('='.repeat(90));
  console.log(`Estimate ID: ${exported.estimateId}`);
  console.log(`URL: ${exported.shareableUrl}`);
  console.log(`Target TCO On-Demand: $${target}/mes`);
  console.log('Nota: AWS Calculator calcula el costo final en frontend al abrir la URL.');

  fs.writeFileSync(
    path.join(__dirname, 'vm-standalone-ondemand-result.json'),
    JSON.stringify({
      estimateId: exported.estimateId,
      url: exported.shareableUrl,
      targetMonthlyFromTco: target,
      vmCount: totalQty,
      diskGbTotalApprox: totalDiskGb,
      ec2GroupCount: input.ec2_groups.length,
      region,
    }, null, 2)
  );
}

run().catch((err) => {
  console.error('ERROR creando estimación:', err);
  process.exit(1);
});
