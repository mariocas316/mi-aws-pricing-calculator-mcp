const { loadManifest, findService, fetchServiceDefinition } = require('./lib/aws-client');

(async () => {
  const manifest = await loadManifest('aws');
  const svc = findService(manifest, 'awsEks');
  console.log('Servicio encontrado:', svc.name);
  
  const definition = await fetchServiceDefinition(manifest, svc.key, 'aws');
  console.log('\nCampos de configuración EKS:');
  if (definition.inputFields) {
    definition.inputFields.forEach(field => {
      console.log(`  - ${field.id}: ${field.label} (tipo: ${field.type})`);
      if (field.options) {
        console.log(`    Opciones: ${field.options.map(o => o.label).join(', ')}`);
      }
    });
  }
})();
