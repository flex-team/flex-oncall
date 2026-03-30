#!/usr/bin/env node
// brain/build-graph.js — graph.html + domain-map.ttl → self-contained HTML
const fs = require('fs');
const path = require('path');

const brainDir = path.dirname(__filename);
const html = fs.readFileSync(path.join(brainDir, 'graph.html'), 'utf8');
const ttl = fs.readFileSync(path.join(brainDir, 'domain-map.ttl'), 'utf8');

// Escape backticks and ${} for template literal embedding
const escaped = ttl.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');

const inlineInit = `// ── Inline TTL data (built by build-graph.js) ──
(function() {
  const ttlText = \`${escaped}\`;
  const data = parseTTL(ttlText);
  domains = data.domains; notes = data.notes; glossary = data.glossary;
  buildColorPalette();
  document.getElementById('loading').classList.add('hidden');
  initCy('domains');
})();`;

// Replace the async fetch IIFE
const output = html.replace(
  /\/\/ ── Load domain-map\.ttl dynamically & Init ──[\s\S]*?\}\)\(\);/,
  inlineInit,
);

if (output === html) {
  console.error('ERROR: fetch IIFE pattern not found in graph.html');
  process.exit(1);
}

const outPath = process.argv[2] || path.join(brainDir, 'graph-standalone.html');
fs.writeFileSync(outPath, output, 'utf8');
console.log(`✓ ${outPath} (${(Buffer.byteLength(output) / 1024).toFixed(0)} KB)`);
