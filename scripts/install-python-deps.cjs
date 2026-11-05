const { spawnSync } = require('node:child_process');
const { existsSync, copyFileSync } = require('node:fs');
const path = require('node:path');

const python = process.env.FITTRACK_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const venvPython = process.env.FITTRACK_VENV_PYTHON || path.join(
  process.cwd(),
  '.venv',
  process.platform === 'win32' ? 'Scripts' : 'bin',
  process.platform === 'win32' ? 'python.exe' : 'python'
);

if (!existsSync('.env')) copyFileSync('.env.example', '.env');

if (!existsSync(venvPython)) {
  let create = spawnSync(python, ['-m', 'venv', '.venv'], { stdio: 'inherit' });
  if ((create.error || create.status !== 0) && process.platform === 'win32' && !process.env.FITTRACK_PYTHON) {
    create = spawnSync('py', ['-3', '-m', 'venv', '.venv'], { stdio: 'inherit' });
  }
  if (create.error) {
    console.error('Could not run Python. Install Python 3.10+ and ensure python or the py launcher is on PATH.');
    process.exit(1);
  }
  if (create.status !== 0) process.exit(create.status || 1);
}

const pip = spawnSync(venvPython, ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
  stdio: 'inherit'
});
if (pip.error) {
  console.error('Could not install Python requirements. Check that Python 3.10+ and pip are available.');
  process.exit(pip.status || 1);
}
process.exit(pip.status || 0);
