#!/usr/bin/env node
// Validates sbom.cdx.json against CycloneDX 1.7 and sbom.spdx.json against SPDX 2.3, offline,
// with the schemas bundled in ../assets/schemas.
//
// Usage: node validate_sbom.js <dir-with-sboms> --deps <dir>
//   --deps  a directory where `npm install ajv@8 ajv-formats@3` has been run
//           (the script prints the command if the packages are missing)

const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const args = process.argv.slice(2);
const dir = path.resolve(args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--deps') || '.');
const deps = args.includes('--deps') ? path.resolve(args[args.indexOf('--deps') + 1]) : process.cwd();
const req = createRequire(path.join(deps, 'package.json'));
let Ajv07; let Ajv2019; let addFormats;
try {
  Ajv07 = req('ajv');
  Ajv2019 = req('ajv/dist/2019');
  addFormats = req('ajv-formats');
} catch {
  console.error(`ajv not found in ${deps}. Run: npm install --prefix "${deps}" ajv@8 ajv-formats@3`);
  process.exit(2);
}
const schemas = path.join(__dirname, '..', 'assets', 'schemas');
const load = (f) => JSON.parse(fs.readFileSync(path.join(schemas, f), 'utf8'));
const report = (name, ajv, ok) => {
  if (ok) { console.log(`${name}: valid`); return true; }
  console.log(`${name}: INVALID`);
  for (const e of ajv.errors.slice(0, 20)) console.log(`  ${e.instancePath || '/'} ${e.message} ${JSON.stringify(e.params)}`);
  return false;
};

let allOk = true;
const cdxFile = path.join(dir, 'sbom.cdx.json');
if (fs.existsSync(cdxFile)) {
  const ajv = new Ajv07({ strict: false, allErrors: true, validateFormats: true });
  addFormats(ajv);
  // Formats ajv-formats does not ship; accept them instead of logging a warning per occurrence.
  ajv.addFormat('iri-reference', true);
  ajv.addFormat('idn-email', true);
  for (const f of ['spdx.schema.json', 'jsf-0.82.schema.json', 'cryptography-defs.schema.json']) ajv.addSchema(load(f));
  const doc = JSON.parse(fs.readFileSync(cdxFile, 'utf8'));
  allOk = report('sbom.cdx.json (CycloneDX 1.7)', ajv, ajv.validate(load('bom-1.7.schema.json'), doc)) && allOk;
  if (doc.specVersion !== '1.7') { console.log(`  specVersion is ${doc.specVersion}, expected 1.7`); allOk = false; }
} else { console.log('sbom.cdx.json: missing'); allOk = false; }

const spdxFile = path.join(dir, 'sbom.spdx.json');
if (fs.existsSync(spdxFile)) {
  const ajv = new Ajv2019({ strict: false, allErrors: true });
  addFormats(ajv);
  const doc = JSON.parse(fs.readFileSync(spdxFile, 'utf8'));
  allOk = report('sbom.spdx.json (SPDX 2.3)', ajv, ajv.validate(load('spdx-2.3.schema.json'), doc)) && allOk;
  // Checks the JSON schema cannot express.
  const ids = new Set([doc.SPDXID, ...(doc.packages || []).map((p) => p.SPDXID), ...(doc.files || []).map((f) => f.SPDXID)]);
  for (const r of doc.relationships || []) {
    for (const k of ['spdxElementId', 'relatedSpdxElement']) {
      if (!ids.has(r[k]) && !/^(NOASSERTION|NONE)$/.test(r[k])) { console.log(`  relationship refers to unknown ${r[k]}`); allOk = false; }
    }
  }
  const refs = new Set((doc.hasExtractedLicensingInfos || []).map((l) => l.licenseId));
  const used = JSON.stringify(doc).match(/LicenseRef-[A-Za-z0-9.-]+/g) || [];
  for (const u of new Set(used)) if (!refs.has(u)) { console.log(`  ${u} used but not defined in hasExtractedLicensingInfos`); allOk = false; }
} else { console.log('sbom.spdx.json: missing'); allOk = false; }

process.exit(allOk ? 0 : 1);
