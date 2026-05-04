// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const INSTANCE_SPECS = {
  't3.large': { vcpu: 2, memoryGiB: 8, maxPods: 35 },
  'm5.large': { vcpu: 2, memoryGiB: 8, maxPods: 29 },
  'm5.xlarge': { vcpu: 4, memoryGiB: 16, maxPods: 58 },
  'm6i.xlarge': { vcpu: 4, memoryGiB: 16, maxPods: 58 },
  'c6i.xlarge': { vcpu: 4, memoryGiB: 8, maxPods: 58 },
  'r6i.xlarge': { vcpu: 4, memoryGiB: 32, maxPods: 58 },
};

function round2(n) {
  return Math.round(n * 100) / 100;
}

function getInstanceSpec(instanceType) {
  return INSTANCE_SPECS[instanceType] || null;
}

function calculateEksNodePlan(options = {}) {
  const {
    containerCount = 100,
    containerCpu = 0.25,
    containerMemoryGiB = 0.5,
    headroomPercent = 20,
    instanceType = 'm5.xlarge',
    minNodes = 2,
    azCount = 2,
    systemReserveCpu = 0.3,
    systemReserveMemoryGiB = 0.5,
    daemonsetReservePods = 2,
    cpuOvercommit = 1,
    memoryOvercommit = 1,
  } = options;

  if (!Number.isFinite(containerCount) || containerCount <= 0) {
    throw new Error('containerCount must be a positive number.');
  }

  const spec = getInstanceSpec(instanceType);
  if (!spec) {
    throw new Error(
      `Unsupported instanceType "${instanceType}". Supported values: ${Object.keys(INSTANCE_SPECS).join(', ')}`
    );
  }

  const factor = 1 + (headroomPercent / 100);
  const requiredCpu = containerCount * containerCpu * factor;
  const requiredMemoryGiB = containerCount * containerMemoryGiB * factor;
  const requiredPods = Math.ceil(containerCount * factor);

  const allocCpuPerNode = Math.max((spec.vcpu - systemReserveCpu) * cpuOvercommit, 0.1);
  const allocMemoryGiBPerNode = Math.max((spec.memoryGiB - systemReserveMemoryGiB) * memoryOvercommit, 0.1);
  const allocPodsPerNode = Math.max(spec.maxPods - daemonsetReservePods, 1);

  const nodesByCpu = Math.ceil(requiredCpu / allocCpuPerNode);
  const nodesByMemory = Math.ceil(requiredMemoryGiB / allocMemoryGiBPerNode);
  const nodesByPods = Math.ceil(requiredPods / allocPodsPerNode);

  const nodeCount = Math.max(nodesByCpu, nodesByMemory, nodesByPods, minNodes, azCount);

  return {
    instanceType,
    nodeCount,
    required: {
      cpu: round2(requiredCpu),
      memoryGiB: round2(requiredMemoryGiB),
      pods: requiredPods,
    },
    perNode: {
      allocCpu: round2(allocCpuPerNode),
      allocMemoryGiB: round2(allocMemoryGiBPerNode),
      allocPods: allocPodsPerNode,
    },
    constraints: {
      nodesByCpu,
      nodesByMemory,
      nodesByPods,
      minNodes,
      azCount,
      headroomPercent,
    },
  };
}

module.exports = {
  INSTANCE_SPECS,
  getInstanceSpec,
  calculateEksNodePlan,
};
