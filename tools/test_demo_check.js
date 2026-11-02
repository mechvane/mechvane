// tools/test_demo_check.js - Headless test for demo_check.js against recorded responses
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

let loadPyodide;
try {
  ({ loadPyodide } = await import('pyodide'));
} catch (e) {
  try {
    const fallbackPath = path.resolve('/tmp/pyodide-test/node_modules/pyodide/pyodide.mjs');
    if (fs.existsSync(fallbackPath)) {
      ({ loadPyodide } = await import(fallbackPath));
    } else {
      console.log('skip demo_check test: pyodide node package not installed');
      process.exit(0);
    }
  } catch (e2) {
    console.log('skip demo_check test: pyodide node package not installed');
    process.exit(0);
  }
}

import { checkInBrowser } from '../mechvane/ui/static/demo_check.js';

// Helper to create a mock SolidCraft app from recorded responses
function createMockApp(recorded) {
  const findRec = (cmd, predicate) => {
    for (const [k, v] of Object.entries(recorded)) {
      const parsed = JSON.parse(k);
      if (parsed[0] === cmd) {
        const p = parsed[1] && parsed[1] !== 'null' ? JSON.parse(parsed[1]) : {};
        if (!predicate || predicate(p)) return v;
      }
    }
    return undefined;
  };

  return {
    async execute(cmd, params = {}) {
      if (cmd === 'document.inspect') {
        return findRec('document.inspect', p => Boolean(p.measure) === Boolean(params.measure));
      }
      if (cmd === 'document.metadata') {
        return findRec('document.metadata') || { metadata: {} };
      }
      if (cmd === 'model.threads') {
        return findRec('model.threads') || { threads: [] };
      }
      if (cmd === 'inspect.measure') {
        return findRec('TOOL:measure') || {};
      }
      if (cmd === 'timeline.inspect') {
        return findRec('timeline.inspect', p => p.feature === params.feature) || {};
      }
      if (cmd === 'model.faces') {
        return findRec('model.faces', p => p.body === params.body) || { faces: [] };
      }
      if (cmd === 'model.edges') {
        return findRec('model.edges', p => p.body === params.body) || { edges: [] };
      }
      throw new Error(`Unexpected command in mock: ${cmd}`);
    },
    async request(cmd, params) {
      return this.execute(cmd, params);
    }
  };
}

async function main() {
  console.log('Testing demo_check.js with Node + Pyodide...');

  const fixturesPath = path.join(repoRoot, 'tests', 'mechvane', 'demo_check_fixtures.json');
  const fixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf-8'));

  // Ensure mechvane.zip is built
  const zipPath = path.join(repoRoot, 'site', 'demo', 'mechvane.zip');
  let zipBuf;
  if (fs.existsSync(zipPath)) {
    zipBuf = fs.readFileSync(zipPath);
  } else {
    // Build on the fly via python
    const tmpZip = path.join('/tmp', 'mechvane_test.zip');
    execFileSync('python3', ['-c', `
import zipfile
from pathlib import Path
repo = Path('${repoRoot}')
modules = ['__init__.py', 'browser_check.py', 'design_rules.py', 'geometry.py',
           'hole_tables.py', 'standard_parts.py', 'sketch_rule.py', 'documents.py',
           'solidcraft.py', 'install.py']
with zipfile.ZipFile('${tmpZip}', 'w', zipfile.ZIP_DEFLATED) as zf:
    for name in modules:
        zf.write(repo / 'mechvane' / name, f'mechvane/{name}')
`]);
    zipBuf = fs.readFileSync(tmpZip);
  }

  const pyodide = await loadPyodide();

  // Test 1: Flange
  const flangeApp = createMockApp(fixtures.flange.recorded);
  const flangeExpected = fixtures.flange.expected;

  const flangeActual = await checkInBrowser(flangeApp, 'flange.solidcraft', {
    pyodide,
    zipBuffer: zipBuf,
  });

  if (flangeActual.verdict !== flangeExpected.verdict) {
    throw new Error(`Flange verdict mismatch: got ${flangeActual.verdict}, expected ${flangeExpected.verdict}`);
  }
  if (flangeActual.findings.length !== flangeExpected.findings.length) {
    throw new Error(`Flange findings count mismatch: got ${flangeActual.findings.length}, expected ${flangeExpected.findings.length}`);
  }
  console.log('✓ Flange check passed:', flangeActual.verdict, `(${flangeActual.findings.length} findings)`);

  // Test 2: Bracket
  const bracketApp = createMockApp(fixtures.bracket.recorded);
  const bracketExpected = fixtures.bracket.expected;

  const bracketActual = await checkInBrowser(bracketApp, 'bracket.solidcraft', {
    pyodide,
    zipBuffer: zipBuf,
  });

  if (bracketActual.verdict !== bracketExpected.verdict) {
    throw new Error(`Bracket verdict mismatch: got ${bracketActual.verdict}, expected ${bracketExpected.verdict}`);
  }
  if (bracketActual.findings.length !== bracketExpected.findings.length) {
    throw new Error(`Bracket findings count mismatch: got ${bracketActual.findings.length}, expected ${bracketExpected.findings.length}`);
  }
  console.log('✓ Bracket check passed:', bracketActual.verdict, `(${bracketActual.findings.length} findings)`);

  console.log('All demo_check tests passed successfully!');
}

main().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});
