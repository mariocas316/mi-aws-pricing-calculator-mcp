const fs = require('fs');
const path = require('path');
const EstimateBuilder = require('./lib/estimate-builder');

const INPUT = path.join(__dirname, 'vm-standalone-per-vm-aws-input.json');

async function main() {
  const data = JSON.parse(fs.readFileSync(INPUT, 'utf8'));
  const builder = new EstimateBuilder('VM Standalone Savings Plan 1yr v1', 'aws');

  let count = 0;
  for (const vm of data.ec2_entries) {
    const keySafeId = String(vm.machine_id || `vm-${count + 1}`).replace(/[^a-zA-Z0-9-_.]/g, '-');
    const group = vm.environment || 'Other';

    builder.addService(`ec2Enhancement:${keySafeId}`, {
      region: data.region || 'us-east-1',
      quantity: '1',
      instanceType: vm.aws_instance_type,
      selectedOS: vm.aws_selected_os,
      tenancy: 'shared',
      utilization: String(vm.aws_utilization_pct || 100),
      pricingStrategy: { model: 'computeSavings', term: '1yr', upfrontPayment: 'None' },
      storageType: vm.aws_storage_type || 'Storage Cold HDD sc1 GB Mo',
      storageAmount: { value: String(vm.azure_disk_gb || 64), unit: 'gb|NA' },
      snapshotFrequency: '0',
      description: `${vm.machine_id} | ${vm.environment} | ${vm.resource_group} | SP1yr`,
    }, { group });

    count += 1;
  }

  const exported = await builder.export();
  const out = {
    estimateId: exported.estimateId,
    url: exported.shareableUrl,
    vmCount: count,
    region: data.region || 'us-east-1',
    pricing: 'Savings Plan 1yr No Upfront',
  };

  fs.writeFileSync(path.join(__dirname, 'vm-sp1yr-detailed-result.json'), JSON.stringify(out, null, 2));

  console.log('VMs cargadas:', count);
  console.log('Estimate ID:', out.estimateId);
  console.log('URL:', out.url);
}

main().catch((err) => {
  console.error('ERROR:', err);
  process.exit(1);
});
