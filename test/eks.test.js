const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { calculateEksNodePlan, getInstanceSpec } = require('../lib/eks');

describe('EKS sizing', () => {
  it('returns instance specs for supported instance type', () => {
    const spec = getInstanceSpec('m5.xlarge');
    assert.ok(spec);
    assert.equal(spec.vcpu, 4);
    assert.equal(spec.memoryGiB, 16);
  });

  it('calculates a node plan for 100 containers with defaults', () => {
    const plan = calculateEksNodePlan({
      containerCount: 100,
    });

    assert.equal(plan.instanceType, 'm5.xlarge');
    assert.ok(plan.nodeCount >= 2, 'must respect minimum nodes');
    assert.ok(plan.required.pods >= 100, 'required pods must include headroom');
    assert.ok(plan.constraints.nodesByPods >= 1);
  });

  it('increases node count when CPU request grows', () => {
    const baseline = calculateEksNodePlan({ containerCount: 100, containerCpu: 0.25 });
    const heavy = calculateEksNodePlan({ containerCount: 100, containerCpu: 1.0 });
    assert.ok(heavy.nodeCount > baseline.nodeCount);
  });

  it('throws for unsupported instance type', () => {
    assert.throws(
      () => calculateEksNodePlan({ instanceType: 'z9.unknown' }),
      /Unsupported instanceType/
    );
  });
});
