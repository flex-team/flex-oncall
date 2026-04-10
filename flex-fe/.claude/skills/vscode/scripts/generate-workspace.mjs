#!/usr/bin/env node

import { readdirSync, writeFileSync, mkdirSync } from 'fs';
import { join, resolve } from 'path';

const WORKSPACE_ROOT = process.env.FLEX_FE_ROOT || resolve(import.meta.dirname, '../../..');
const WORKSPACES_DIR = join(WORKSPACE_ROOT, 'workspaces');

const ticket = process.argv[2];
if (!ticket) {
  console.error('Usage: generate-workspace.mjs <ticket-id>');
  process.exit(1);
}

const ticketLower = ticket.toLowerCase();

const worktrees = readdirSync(WORKSPACE_ROOT, { withFileTypes: true })
  .filter(d => d.isDirectory() && d.name.includes(`--${ticketLower}`))
  .map(d => d.name);

if (worktrees.length === 0) {
  console.error(`No worktrees found for ticket: ${ticket}`);
  process.exit(1);
}

const folders = worktrees.map(wt => ({
  name: wt.replace(`--${ticketLower}`, '').replace(/^flex-frontend-?/, '').replace('apps-', '') || 'frontend',
  path: join(WORKSPACE_ROOT, wt),
}));

const workspace = {
  folders,
  settings: {
    'files.exclude': {
      '**/.git': true,
      '**/.yarn': true,
      '**/node_modules': true,
      '**/.pnp.*': true,
    },
    'search.exclude': {
      '**/.yarn': true,
      '**/node_modules': true,
      '**/dist': true,
      '**/.next': true,
    },
    'typescript.tsdk': '.yarn/sdks/typescript/lib',
    'editor.defaultFormatter': 'esbenp.prettier-vscode',
    'editor.formatOnSave': true,
  },
};

mkdirSync(WORKSPACES_DIR, { recursive: true });
const outPath = join(WORKSPACES_DIR, `${ticketLower}.code-workspace`);
writeFileSync(outPath, JSON.stringify(workspace, null, 2));
console.log(`Workspace created: ${outPath}`);
console.log(`Worktrees: ${worktrees.join(', ')}`);
