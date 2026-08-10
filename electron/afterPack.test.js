const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const afterPack = require('../build/afterPack');

test('afterPack removes npm documentation without removing its CLI', async (t) => {
  const appOutDir = fs.mkdtempSync(path.join(os.tmpdir(), 'zbuild-after-pack-'));
  t.after(() => fs.rmSync(appOutDir, { recursive: true, force: true }));

  const npmRoot = path.join(appOutDir, 'resources', 'runtime', 'node', 'node_modules', 'npm');
  fs.mkdirSync(path.join(npmRoot, 'node_modules', 'example-package', 'examples'), { recursive: true });
  fs.mkdirSync(path.join(npmRoot, 'bin'), { recursive: true });
  fs.writeFileSync(path.join(npmRoot, 'README.md'), 'documentation');
  fs.writeFileSync(path.join(npmRoot, 'LICENSE'), 'license');
  fs.writeFileSync(path.join(npmRoot, 'node_modules', 'example-package', 'examples', 'demo.js'), 'example');
  fs.writeFileSync(path.join(npmRoot, 'bin', 'npm-cli.js'), 'cli');

  await afterPack({ appOutDir });

  assert.equal(fs.existsSync(path.join(npmRoot, 'README.md')), false);
  assert.equal(fs.existsSync(path.join(npmRoot, 'LICENSE')), true);
  assert.equal(fs.existsSync(path.join(npmRoot, 'node_modules', 'example-package', 'examples')), false);
  assert.equal(fs.existsSync(path.join(npmRoot, 'bin', 'npm-cli.js')), true);
});
