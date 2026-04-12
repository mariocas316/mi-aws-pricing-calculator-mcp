const MANIFEST_URL = process.env.AWS_MANIFEST_URL || 'https://d1qsjq9pzbk1k6.cloudfront.net/manifest/en_US.json';
const SAVE_URL = process.env.AWS_SAVE_URL || 'https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs';
const CDN_BASE = 'https://d1qsjq9pzbk1k6.cloudfront.net';

let manifestPromise = null;
const definitionCache = new Map();

async function loadManifest() {
  if (manifestPromise) return manifestPromise;

  manifestPromise = (async () => {
    const res = await fetch(MANIFEST_URL);
    if (!res.ok) throw new Error(`Manifest fetch failed: HTTP ${res.status}`);
    const manifest = await res.json();
    const services = new Map();
    manifest.awsServices.forEach(s => {
      const key = s.key || s.serviceCode;
      if (key) services.set(key, { ...s, key });
    });
    console.error(`Loaded ${services.size} services from manifest`);
    return services;
  })();

  // Allow retry on failure
  manifestPromise.catch(() => { manifestPromise = null; });

  return manifestPromise;
}

function findService(manifest, name) {
  const lower = name.toLowerCase();
  for (const [key, svc] of manifest) {
    if (key.toLowerCase() === lower) return svc;
  }
  return null;
}

function searchServices(manifest, query) {
  const terms = query.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
  const search = (term) => {
    const matches = [];
    for (const [key, svc] of manifest) {
      if (svc.subType === 'subServiceSelector') continue;
      if (svc.isActive === 'false') continue;
      const hit = key.toLowerCase().includes(term)
        || (svc.name && svc.name.toLowerCase().includes(term))
        || svc.searchKeywords?.some(kw => kw.toLowerCase().includes(term));
      if (hit) matches.push({ key, name: svc.name });
    }
    return matches;
  };
  if (terms.length === 1) return search(terms[0]);
  const results = {};
  for (const term of terms) results[term] = search(term);
  return results;
}

async function fetchServiceDefinition(manifest, serviceCode) {
  if (definitionCache.has(serviceCode)) return definitionCache.get(serviceCode);

  const svc = manifest.get(serviceCode);
  if (!svc) return null;

  const urlPath = svc.serviceDefinitionUrlPath || `/data/${serviceCode}/en_US.json`;
  const res = await fetch(`${CDN_BASE}${urlPath}`);
  if (!res.ok) throw new Error(`Definition fetch failed for ${serviceCode}: HTTP ${res.status}`);

  const definition = await res.json();
  definitionCache.set(serviceCode, definition);
  return definition;
}

function parseDoubleEncodedResponse(rawText) {
  let result;
  try { result = JSON.parse(rawText); }
  catch { throw new Error('AWS save API returned invalid JSON'); }

  let body;
  try { body = JSON.parse(result.body); }
  catch { throw new Error('AWS save API returned invalid body'); }

  if (!body.savedKey) {
    throw new Error(`AWS save API did not return a savedKey: ${JSON.stringify(body).substring(0, 200)}`);
  }
  return body;
}

async function saveEstimate(payload) {
  const jsonBody = JSON.stringify(payload);
  console.error(`[save] Sending ${jsonBody.length} bytes, ${Object.keys(payload.groups || {}).length} groups, ${Object.keys(payload.services || {}).length} ungrouped services`);
  const res = await fetch(SAVE_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'Referer': 'https://calculator.aws/' },
    body: jsonBody,
  });
  const rawText = await res.text();
  if (!res.ok) {
    console.error(`[save] HTTP ${res.status}: ${rawText.substring(0, 500)}`);
    let detail;
    try {
      const body = parseDoubleEncodedResponse(rawText);
      detail = body.message || rawText.substring(0, 200);
    } catch {
      detail = rawText.substring(0, 200);
    }
    throw new Error(`AWS save API returned HTTP ${res.status}: ${detail}`);
  }
  const body = parseDoubleEncodedResponse(rawText);
  console.error(`[save] OK → ${body.savedKey}`);
  return {
    estimateId: body.savedKey,
    shareableUrl: `https://calculator.aws/#/estimate?id=${body.savedKey}`,
  };
}

const INPUT_TYPES = new Set([
  'input', 'numericInput', 'frequency', 'fileSize', 'durationInput', 'percentInput',
]);
const INPUT_SUBTYPES = new Set([
  'dropdown', 'numericInput', 'frequency', 'fileSize', 'durationInput',
  'columnFormIPM', 'dataTransferV2',
]);

function extractInputFields(definition) {
  const fields = [];
  const seen = new Set();

  const walk = (obj) => {
    if (!obj || typeof obj !== 'object') return;
    if (obj.id && (INPUT_TYPES.has(obj.type) || INPUT_SUBTYPES.has(obj.subType))) {
      const fieldType = obj.subType || obj.type;
      // Skip non-input decorative types
      if (['bodyText', 'headerText', 'alert'].includes(fieldType)) return;
      // Skip "without free tier" / MVP duplicate fields — these are alternate
      // versions of the same inputs for different pricing modes
      if (obj.id.includes('WithoutFreeTier') || obj.id.includes('_withoutFree') || obj.id.endsWith('_MVP')) return;
      // Deduplicate (some definitions repeat fields across templates)
      const dedupKey = obj.id + ':' + fieldType;
      if (seen.has(dedupKey)) return;
      seen.add(dedupKey);

      const field = { id: obj.id, type: fieldType };
      if (obj.label) field.label = obj.label;
      if (obj.options) {
        field.options = obj.options
          .filter(o => o.id !== undefined || o.label !== undefined)
          .map(o => {
            const opt = {};
            if (o.id !== undefined) opt.id = o.id;
            if (o.label) opt.label = o.label;
            return opt;
          });
      }
      if (obj.unit) field.unit = obj.unit;
      // fileSize fields: include valid size units and default unit format
      if (fieldType === 'fileSize') {
        const sizes = obj.dropDownSize?.map(s => s.value || s.id) || ['gb'];
        const defaultSize = obj.defaultOption?.size || 'gb';
        const defaultFreq = obj.defaultOption?.frequency || 'NA';
        field.unitFormat = `{value}|{size}|{frequency} — sizes: [${sizes.join(', ')}], default: "${defaultSize}|${defaultFreq}"`;
        field.validSizes = sizes;
        field.defaultUnit = `${defaultSize}|${defaultFreq}`;
      }
      fields.push(field);
    }
    for (const v of Object.values(obj)) {
      if (Array.isArray(v)) v.forEach(walk);
      else if (typeof v === 'object') walk(v);
    }
  };

  walk(definition.templates || definition);
  return fields;
}

module.exports = { loadManifest, findService, searchServices, fetchServiceDefinition, saveEstimate, extractInputFields, parseDoubleEncodedResponse };
