#!/usr/bin/env node
// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { z } = require('zod');
const { PARTITIONS, loadManifest, findService, fetchServiceDefinition, extractInputFields, searchServices } = require('./lib/aws-client');
const EstimateBuilder = require('./lib/estimate-builder');
const { calculateEksNodePlan } = require('./lib/eks');

const estimates = new Map();
const DEFAULT_EXPORT_STABILIZE_MS = Number(process.env.EXPORT_STABILIZE_MS || 4000);

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const META_KEYS = new Set(['region', 'description']);
const EC2_KEYS = new Set([
  'tenancy', 'pricingStrategy', 'utilization', 'selectedOS', 'instanceType',
  'quantity', 'storageType', 'storageAmount', 'snapshotFrequency', 'dataTransferForEC2',
]);

function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const d = Array.from({ length: m + 1 }, (_, i) => i);
  for (let j = 1; j <= n; j++) {
    let prev = d[0];
    d[0] = j;
    for (let i = 1; i <= m; i++) {
      const tmp = d[i];
      d[i] = a[i - 1] === b[j - 1] ? prev : 1 + Math.min(prev, d[i], d[i - 1]);
      prev = tmp;
    }
  }
  return d[m];
}

function suggestMatch(invalid, validIds, max = 3) {
  const lower = invalid.toLowerCase();
  return validIds
    .map(id => ({ id, dist: levenshtein(lower, id.toLowerCase()) }))
    .filter(m => m.dist <= Math.max(Math.floor(invalid.length * 0.6), 3))
    .sort((a, b) => a.dist - b.dist)
    .slice(0, max)
    .map(m => m.id);
}

function pickEksServiceKey(manifest) {
  let best = null;
  let bestScore = -1;

  for (const [key, svc] of manifest) {
    if (svc.subType === 'subServiceSelector') continue;
    if (svc.isActive === 'false') continue;

    const keyLower = key.toLowerCase();
    const nameLower = (svc.name || '').toLowerCase();
    let score = 0;

    if (nameLower.includes('elastic kubernetes service')) score += 8;
    if (nameLower.includes('kubernetes')) score += 4;
    if (keyLower.includes('kubernetes')) score += 3;
    if (keyLower.includes('eks')) score += 2;

    if (score > bestScore) {
      best = key;
      bestScore = score;
    }
  }

  return bestScore > 0 ? best : null;
}

async function validateConfigKeys(serviceKey, config, partition) {
  if (serviceKey.toLowerCase() === 'ec2enhancement') return null;

  const configKeys = Object.keys(config).filter(k => !META_KEYS.has(k));
  if (configKeys.length === 0) return null;

  try {
    const manifest = await loadManifest(partition || 'aws');
    const svc = findService(manifest, serviceKey);
    if (!svc) return null; // service not found — will fail later at export

    const def = await fetchServiceDefinition(manifest, svc.key, partition || 'aws');
    if (!def) return null;

    const validIds = extractInputFields(def).map(f => f.id);
    const validSet = new Set(validIds);
    const invalid = configKeys.filter(k => !validSet.has(k));
    if (invalid.length === 0) return null;

    const lines = invalid.map(k => {
      const suggestions = suggestMatch(k, validIds);
      return suggestions.length
        ? `  "${k}" — did you mean: ${suggestions.map(s => `"${s}"`).join(', ')}?`
        : `  "${k}" — no close match found`;
    });
    return `Invalid field IDs for ${svc.key}:\n${lines.join('\n')}\nUse get_service_fields to discover valid field IDs.`;
  } catch {
    return null; // validation is best-effort; don't block on fetch failures
  }
}

const server = new McpServer({
  name: 'aws-calculator',
  version: '1.0.0',
});

server.tool(
  'create_eks_estimate',
  'Create a ready-to-export estimate for an Amazon EKS workload sized to run containers. It auto-calculates EC2 worker node count from container CPU/memory requests and adds an EKS control plane service when available.',
  {
    name: z.string().optional().describe('Estimate name (default: "EKS 100 Containers")'),
    region: z.string().optional().describe('AWS region for EKS and workers (default: "us-east-1")'),
    partition: z.string().optional().describe('AWS partition (default inferred from region). Valid: aws, aws-iso, aws-iso-b'),
    container_count: z.number().int().positive().optional().describe('Number of application containers to run (default: 100)'),
    container_cpu: z.number().positive().optional().describe('Requested vCPU per container (default: 0.25)'),
    container_memory_gib: z.number().positive().optional().describe('Requested memory GiB per container (default: 0.5)'),
    headroom_percent: z.number().min(0).max(200).optional().describe('Capacity headroom percentage (default: 20)'),
    instance_type: z.string().optional().describe('EC2 instance type for worker nodes (default: "m5.xlarge")'),
    min_nodes: z.number().int().positive().optional().describe('Minimum worker nodes (default: 2)'),
    az_count: z.number().int().positive().optional().describe('Target AZ count (default: 2)'),
    include_eks_control_plane: z.boolean().optional().describe('Add Amazon EKS control plane service entry (default: true)'),
    pricing_strategy: z.string().optional().describe('EC2 pricing strategy for workers. Examples: ondemand, spot, computeSavings1yrNoUpfront (default: ondemand)'),
    worker_storage_gib: z.number().int().positive().optional().describe('EBS gp3 storage per worker node in GiB (default: 50)'),
  },
  async (args) => {
    const region = args.region || 'us-east-1';
    const requestedPartition = args.partition;
    const includeEks = args.include_eks_control_plane !== false;
    const partition = requestedPartition || (region.startsWith('us-iso-') ? 'aws-iso' : (region.startsWith('us-isob-') ? 'aws-iso-b' : 'aws'));

    if (!PARTITIONS[partition]) {
      return { content: [{ type: 'text', text: `Unknown partition '${partition}'. Valid partitions: ${Object.keys(PARTITIONS).join(', ')}` }], isError: true };
    }

    let plan;
    try {
      plan = calculateEksNodePlan({
        containerCount: args.container_count ?? 100,
        containerCpu: args.container_cpu ?? 0.25,
        containerMemoryGiB: args.container_memory_gib ?? 0.5,
        headroomPercent: args.headroom_percent ?? 20,
        instanceType: args.instance_type || 'm5.xlarge',
        minNodes: args.min_nodes ?? 2,
        azCount: args.az_count ?? 2,
      });
    } catch (err) {
      return { content: [{ type: 'text', text: err.message }], isError: true };
    }

    const estimate = new EstimateBuilder(args.name || `EKS ${args.container_count ?? 100} Containers`, partition);

    estimate.addService('ec2Enhancement:EKSWorkerNodes', {
      region,
      description: `EKS worker nodes (${plan.nodeCount} x ${plan.instanceType})`,
      quantity: String(plan.nodeCount),
      instanceType: plan.instanceType,
      selectedOS: 'linux',
      tenancy: 'shared',
      pricingStrategy: args.pricing_strategy || 'ondemand',
      storageType: 'Storage General Purpose gp3 GB Mo',
      storageAmount: { value: String(args.worker_storage_gib ?? 50), unit: 'gb|NA' },
      snapshotFrequency: '0',
    }, { group: 'EKS' });

    let eksServiceAdded = false;
    let eksServiceKey = null;

    if (includeEks) {
      const manifest = await loadManifest(partition);
      eksServiceKey = pickEksServiceKey(manifest);
      if (eksServiceKey) {
        estimate.addService(eksServiceKey, {
          region,
          description: 'Amazon EKS control plane',
        }, { group: 'EKS' });
        eksServiceAdded = true;
      }
    }

    estimates.set(estimate.id, estimate);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          estimate_id: estimate.id,
          name: estimate.name,
          summary: {
            target_containers: args.container_count ?? 100,
            region,
            partition,
            workers: {
              instance_type: plan.instanceType,
              node_count: plan.nodeCount,
              pricing_strategy: args.pricing_strategy || 'ondemand',
            },
            eks_control_plane_added: eksServiceAdded,
            eks_service_key: eksServiceKey,
            sizing: plan,
          },
          next_step: `Call export_estimate with estimate_id \"${estimate.id}\" to generate the calculator.aws URL.`,
        }, null, 2),
      }],
    };
  }
);

server.tool(
  'search_services',
  'Search AWS services available in the calculator. Returns service keys and names. Use this to find the correct service key before adding it to an estimate. Supports multiple comma-separated search terms in a single call (e.g. "Lambda, S3, API Gateway, CloudWatch").',
  {
    query: z.string().describe('One or more search terms, comma-separated (e.g. "Lambda, S3, Amazon Personalize, API Gateway, CloudWatch")'),
    partition: z.string().optional().describe('AWS partition to search in (default: "aws"). Valid values: "aws", "aws-iso", "aws-iso-b"'),
  },
  async ({ query, partition }) => {
    const p = partition || 'aws';
    if (!PARTITIONS[p]) {
      return { content: [{ type: 'text', text: `Unknown partition '${p}'. Valid partitions: ${Object.keys(PARTITIONS).join(', ')}` }], isError: true };
    }
    const manifest = await loadManifest(p);
    const results = searchServices(manifest, query);
    return { content: [{ type: 'text', text: JSON.stringify(results, null, 2) }] };
  }
);

server.tool(
  'get_service_fields',
  'Get the input fields for one or more AWS services. Returns field IDs, types, labels, and valid options. Use this to discover what configuration a service accepts before adding it to an estimate. The field IDs returned here are the exact keys to use in add_service config. Accepts multiple comma-separated service keys.',
  { service: z.string().describe('One or more service keys, comma-separated (e.g. "aWSLambda, amazonS3, stepFunctionStandard, amazonApiGateway")'),
    partition: z.string().optional().describe('AWS partition to fetch from (default: "aws"). Valid values: "aws", "aws-iso", "aws-iso-b"'),
  },
  async ({ service, partition }) => {
    const p = partition || 'aws';
    if (!PARTITIONS[p]) {
      return { content: [{ type: 'text', text: `Unknown partition '${p}'. Valid partitions: ${Object.keys(PARTITIONS).join(', ')}` }], isError: true };
    }
    const manifest = await loadManifest(p);
    const keys = service.split(',').map(s => s.trim()).filter(Boolean);
    const results = [];
    const errors = [];

    for (const key of keys) {
      const svc = findService(manifest, key);
      if (!svc) { errors.push(`Service "${key}" not found.`); continue; }

      const definition = await fetchServiceDefinition(manifest, svc.key, p);
      if (!definition) { errors.push(`Failed to fetch definition for "${svc.key}".`); continue; }

      const fields = extractInputFields(definition);
      results.push({ serviceCode: svc.key, serviceName: svc.name, fields });
    }

    const output = errors.length
      ? { services: results, errors }
      : keys.length === 1 ? results[0] : results;
    return { content: [{ type: 'text', text: JSON.stringify(output, null, 2) }] };
  }
);

server.tool(
  'create_estimate',
  'Create a new empty estimate. Returns an estimate ID to use with add_service and export_estimate.',
  {
    name: z.string().optional().describe('Name for the estimate (default: "My Estimate")'),
    partition: z.string().optional().describe('AWS partition for this estimate (default: "aws"). Valid values: "aws", "aws-iso", "aws-iso-b"'),
  },
  async ({ name, partition }) => {
    const p = partition || undefined;
    if (p && !PARTITIONS[p]) {
      return { content: [{ type: 'text', text: `Unknown partition '${p}'. Valid partitions: ${Object.keys(PARTITIONS).join(', ')}` }], isError: true };
    }
    const estimate = new EstimateBuilder(name, p);
    estimates.set(estimate.id, estimate);
    return { content: [{ type: 'text', text: JSON.stringify({ estimate_id: estimate.id, name: estimate.name }) }] };
  }
);

server.tool(
  'add_service',
  `Add one or more AWS services to an estimate. Accepts a single service or a JSON array of services in the "services" parameter.

Field values follow these patterns based on field type:
- numericInput: plain string value, e.g. "1000"
- frequency: object with value and unit, e.g. {"value": "19", "unit": "millionPerMonth"}
- fileSize: object with value and unit. The unit format is "{size}|{frequency}" where size comes from the field's validSizes (gb, tb, mb, etc.) and frequency is usually "NA". Check the field's defaultUnit from get_service_fields. Examples: {"value": "512", "unit": "mb|NA"}, {"value": "1", "unit": "tb|NA"}, {"value": "10", "unit": "gb|NA"}, {"value": "8", "unit": "gb|month"}
- dropdown: string matching one of the option IDs from get_service_fields
- durationInput: object with value and unit, e.g. {"value": "960", "unit": "min"}
- pricingStrategy (Amazon EC2 only): object with model, term, and upfrontPayment keys, e.g. {"model": "computeSavings", "term": "1yr", "upfrontPayment": "None"}. Valid models: "instanceSavings" (EC2 Instance Savings Plans), "computeSavings" (Compute Savings Plans), "ondemand", "spot". For dedicated tenancy only: "reserved" (Standard RI), "convertible" (Convertible RI). Valid terms: "1yr", "3yr". Valid upfrontPayment: "None", "Partial", "All". Shorthand strings also work, e.g. "computeSavings1yrNoUpfront".

Amazon EC2 (ec2Enhancement) has special config fields handled automatically:
- "quantity": number of instances (e.g. "2" for 2 instances). Default: 1.
- "instanceType": instance type (e.g. "g6.12xlarge")
- "selectedOS": operating system. Default: "linux". Options: "linux", "windows", "rhel", "suse", etc.
- "tenancy": "shared" (default), "dedicated", or "host"
- "pricingStrategy": see above
- "storageType": EBS volume type (e.g. "Storage General Purpose gp3 GB Mo")
- "storageAmount": EBS storage, e.g. {"value": "30", "unit": "gb|NA"}
- "snapshotFrequency": snapshot frequency, e.g. "0" for none
Do NOT use get_service_fields for Amazon EC2 — these fields are handled by a custom transform.

Always include "region" in each service config. Use "description" to label what each service entry represents. IMPORTANT: descriptions and group names must NOT contain <, >, or & characters (AWS rejects them).

Config keys are validated against the service definition. Invalid field IDs will be rejected with suggested corrections. Use get_service_fields first to discover valid field IDs for a service.

For batch mode, pass a JSON array in "services":
[{"service":"aWSLambda","instance":"Compute","group":"Prod","config":{...}},{"service":"amazonS3Standard","group":"Prod","config":{...}}]`,
  {
    estimate_id: z.string().describe('Estimate ID from create_estimate'),
    services: z.string().describe('JSON array of service entries. Each entry: {"service":"serviceKey","instance":"optional","group":"optional","config":{...with region, description, and field values}}. Example: [{"service":"aWSLambda","group":"Prod","config":{"region":"eu-west-1","description":"Compute","numberOfRequests":{"value":"19","unit":"millionPerMonth"}}}]'),
  },
  async ({ estimate_id, services: servicesStr }) => {
    const estimate = estimates.get(estimate_id);
    if (!estimate) return { content: [{ type: 'text', text: `Estimate "${estimate_id}" not found.` }], isError: true };

    let entries;
    try {
      entries = JSON.parse(servicesStr);
      if (!Array.isArray(entries)) entries = [entries];
    } catch {
      return { content: [{ type: 'text', text: 'Invalid JSON in services parameter.' }], isError: true };
    }

    const results = [];
    for (const entry of entries) {
      const { service, instance, group } = entry;
      let config = entry.config;
      if (!service || !config) {
        results.push({ error: 'Missing "service" or "config" in entry', entry });
        continue;
      }
      // Handle config passed as JSON string within the array
      if (typeof config === 'string') {
        try { config = JSON.parse(config); } catch {
          results.push({ error: 'Invalid JSON in config', service });
          continue;
        }
      }
      const key = instance ? `${service}:${instance}` : service;
      const validationError = await validateConfigKeys(service, config, estimate.partition);
      if (validationError) {
        results.push({ error: validationError, service: key });
        continue;
      }
      estimate.addService(key, config, { group });
      results.push({ success: true, service: key, group: group || '(ungrouped)' });
    }
    return { content: [{ type: 'text', text: JSON.stringify(results, null, 2) }] };
  }
);

server.tool(
  'export_estimate',
  'Export an estimate to calculator.aws and get a shareable URL. The link will show the full estimate with AWS-calculated pricing.',
  {
    estimate_id: z.string().describe('Estimate ID from create_estimate'),
    ready_wait_ms: z.number().int().min(0).optional().describe('Optional wait before returning the URL so calculator.aws finishes initial render (default: 4000). Set 0 to disable.'),
  },
  async ({ estimate_id, ready_wait_ms }) => {
    const estimate = estimates.get(estimate_id);
    if (!estimate) return { content: [{ type: 'text', text: `Estimate "${estimate_id}" not found.` }], isError: true };

    try {
      const result = await estimate.export();
      const waitMs = ready_wait_ms ?? DEFAULT_EXPORT_STABILIZE_MS;
      if (waitMs > 0) await sleep(waitMs);
      const forceReloadUrl = `https://calculator.aws/?open=${Date.now()}#/estimate?id=${result.estimateId}`;
      const rawEstimateUrl = `https://d3knqfixx3sbls.cloudfront.net/${result.estimateId}`;
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            sharable_url: result.shareableUrl,
            open_url: forceReloadUrl,
            raw_estimate_url: rawEstimateUrl,
            aws_estimate_id: result.estimateId,
          }),
        }],
      };
    } catch (err) {
      return { content: [{ type: 'text', text: `Export failed: ${err.message}` }], isError: true };
    }
  }
);

// New Azure to AWS Migration Tools
const fs = require('fs');
const path = require('path');

// Load Azure to AWS cost mapping
function loadAzureAwsMapping() {
  try {
    const mappingFile = path.join(__dirname, 'vm-costs-azure-aws-mapping.json');
    if (fs.existsSync(mappingFile)) {
      return JSON.parse(fs.readFileSync(mappingFile, 'utf8'));
    }
  } catch (err) {
    console.error('Error loading Azure-AWS mapping:', err.message);
  }
  return null;
}

server.tool(
  'map_azure_vm_to_ec2',
  'Map an Azure VM to its equivalent AWS EC2 instance and calculate cost comparison.',
  {
    azure_vm_name: z.string().describe('Name of the Azure VM'),
    azure_size: z.string().describe('Azure VM size (e.g., Standard_D4as_v4)'),
    vcpu: z.number().describe('Number of vCPUs'),
    memory_gb: z.number().describe('Memory in GB'),
  },
  async ({ azure_vm_name, azure_size, vcpu, memory_gb }) => {
    const instanceMap = {
      1: 't3.small', 2: 't3.medium', 4: 't3.large',
      8: 't3.xlarge', 16: 't3.2xlarge',
    };
    
    const aws_prices = {
      't3.small': 7.50, 't3.medium': 15.00, 't3.large': 30.00,
      't3.xlarge': 60.00, 't3.2xlarge': 120.00,
      'c6i.large': 50.00, 'c6i.xlarge': 100.00, 'c6i.2xlarge': 200.00,
      'm6i.xlarge': 150.00, 'm6i.2xlarge': 300.00, 'm6i.4xlarge': 600.00,
      'm6i.8xlarge': 1200.00, 'r6i.xlarge': 200.00, 'r6i.2xlarge': 400.00,
    };
    
    let aws_equivalent = instanceMap[vcpu] || 't3.large';
    if (memory_gb > 32) aws_equivalent = 'm6i.4xlarge';
    else if (memory_gb > 16) aws_equivalent = 'm6i.2xlarge';
    else if (memory_gb > 8) aws_equivalent = 'm6i.xlarge';
    
    const aws_monthly = aws_prices[aws_equivalent] || 75.00;
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          azure_vm: {
            name: azure_vm_name,
            size: azure_size,
            vcpu, memory_gb,
          },
          aws_equivalent: {
            instance_type: aws_equivalent,
            monthly_cost: aws_monthly,
            annual_cost: aws_monthly * 12,
            savings_3yr_reserved: aws_monthly * 12 * 0.50,
          },
        }, null, 2),
      }],
    };
  }
);

server.tool(
  'get_azure_aws_cost_comparison',
  'Get cost comparison between Azure VMs and AWS EC2 equivalents. Returns total costs and savings analysis.',
  {
    environment: z.enum(['Prod', 'Dev', 'QA', 'CentralHub', 'All']).optional().describe('Filter by environment (default: All)'),
  },
  async ({ environment }) => {
    const mapping = loadAzureAwsMapping();
    if (!mapping) {
      return {
        content: [{
          type: 'text',
          text: 'Azure-AWS mapping data not available. Run extract-azure-costs.py first.',
        }],
        isError: true,
      };
    }
    
    let vms = mapping.vms || [];
    if (environment && environment !== 'All') {
      vms = vms.filter(vm => vm.name.toLowerCase().includes(environment.toLowerCase()));
    }
    
    const summary = {
      total_azure_annual: mapping.total_azure_annual,
      total_aws_annual: mapping.total_aws_annual,
      potential_savings: mapping.total_potential_savings,
      savings_percentage: mapping.savings_percentage,
      vm_count: vms.length,
      breakdown: {
        avg_azure_cost: (mapping.total_azure_annual / vms.length).toFixed(2),
        avg_aws_cost: (mapping.total_aws_annual / vms.length).toFixed(2),
      },
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(summary, null, 2),
      }],
    };
  }
);

server.tool(
  'create_aws_migration_estimate',
  'Create an AWS estimate for all mapped Azure VMs by automatically adding EC2 instances.',
  {
    estimate_name: z.string().optional().describe('Name for the estimate'),
    environment: z.enum(['Prod', 'Dev', 'QA', 'CentralHub', 'All']).optional().describe('Filter VMs by environment'),
    region: z.string().optional().describe('AWS region (default: us-east-2)'),
    pricing_strategy: z.enum(['ondemand', 'computeSavings1yrNoUpfront', 'computeSavings3yrNoUpfront']).optional().describe('Pricing strategy (default: ondemand)'),
  },
  async ({ estimate_name, environment, region, pricing_strategy }) => {
    const mapping = loadAzureAwsMapping();
    if (!mapping) {
      return {
        content: [{
          type: 'text',
          text: 'Azure-AWS mapping data not available. Run extract-azure-costs.py first.',
        }],
        isError: true,
      };
    }
    
    const estimate = new EstimateBuilder(estimate_name || 'Azure Migration to AWS', 'aws');
    const awsRegion = region || 'us-east-2';
    const strategy = pricing_strategy || 'ondemand';
    
    let vms = mapping.vms || [];
    if (environment && environment !== 'All') {
      vms = vms.filter(vm => vm.name.toLowerCase().includes(environment.toLowerCase()));
    }
    
    // Group by instance type
    const byInstance = {};
    vms.forEach(vm => {
      const key = vm.aws_equivalent;
      if (!byInstance[key]) {
        byInstance[key] = { count: 0, sampleNames: [] };
      }
      byInstance[key].count += 1;
      if (byInstance[key].sampleNames.length < 3) {
        byInstance[key].sampleNames.push(vm.name);
      }
    });
    
    // Add EC2 services for each instance type
    Object.entries(byInstance).forEach(([instanceType, data]) => {
      estimate.addService('ec2Enhancement', {
        region: awsRegion,
        description: `${data.count}x ${instanceType} (${data.sampleNames.join(', ')}...)`,
        quantity: String(data.count),
        instanceType,
        selectedOS: 'linux',
        tenancy: 'shared',
        pricingStrategy: strategy,
        storageType: 'Storage General Purpose gp3 GB Mo',
        storageAmount: { value: '50', unit: 'gb|NA' },
        snapshotFrequency: '0',
      }, { group: 'Migration' });
    });
    
    estimates.set(estimate.id, estimate);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          estimate_id: estimate.id,
          name: estimate.name,
          summary: {
            total_vms: vms.length,
            region: awsRegion,
            pricing_strategy: strategy,
            instance_distribution: byInstance,
            estimated_monthly_cost: mapping.total_aws_annual / 12,
            estimated_annual_cost: mapping.total_aws_annual,
          },
          next_step: `Call export_estimate with estimate_id "${estimate.id}" to get the calculator.aws URL.`,
        }, null, 2),
      }],
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
