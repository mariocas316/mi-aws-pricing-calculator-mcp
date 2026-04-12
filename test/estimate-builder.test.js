const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const EstimateBuilder = require('../lib/estimate-builder');

describe('EstimateBuilder', () => {
  describe('description field', () => {
    it('defaults to empty string when no description provided', async () => {
      const { sanitize } = require('../lib/estimate-builder');
      const result = sanitize(undefined);
      assert.equal(result, '', 'sanitize(undefined) should return empty string');
      assert.equal(sanitize(undefined) || null, null, 'demonstrates the bug with || null');
    });
  });

  describe('addService deduplication', () => {
    it('deduplicates same service key using description', () => {
      const eb = new EstimateBuilder('test');
      eb.addService('aWSLambda', { description: 'API handler', region: 'us-east-1' });
      eb.addService('aWSLambda', { description: 'Cron jobs', region: 'us-east-1' });
      const keys = Object.keys(eb.services);
      assert.equal(keys.length, 2, 'should have two entries');
      assert.ok(keys.includes('aWSLambda'), 'first entry uses original key');
      assert.ok(keys.some(k => k.includes('Cronjobs')), 'second entry has description suffix');
    });

    it('recognizes ec2Enhancement as EC2 service', () => {
      const eb = new EstimateBuilder('test');
      // Agents use ec2Enhancement (from search) not eC2Next (inactive)
      // _isEC2 must recognize both keys so the EC2 transform is applied
      assert.ok(eb._isEC2({ key: 'ec2Enhancement' }), 'should recognize ec2Enhancement');
      assert.ok(!eb._isEC2({ key: 'eC2Next' }), 'eC2Next is inactive, not supported');
      assert.ok(!eb._isEC2({ key: 'aWSLambda' }), 'should not match other services');
    });

    it('places services in groups when specified', () => {
      const eb = new EstimateBuilder('test');
      eb.addService('aWSLambda', { region: 'us-east-1' }, { group: 'Prod' });
      assert.equal(Object.keys(eb.services).length, 0, 'ungrouped should be empty');
      assert.ok(eb.groups.Prod, 'Prod group should exist');
      assert.equal(Object.keys(eb.groups.Prod.services).length, 1);
    });
  });
});
