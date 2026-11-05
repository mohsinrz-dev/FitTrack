const { spawn } = require('node:child_process');
const path = require('node:path');

const python = process.env.FITTRACK_VENV_PYTHON || path.join(
  process.cwd(),
  '.venv',
  process.platform === 'win32' ? 'Scripts' : 'bin',
  process.platform === 'win32' ? 'python.exe' : 'python'
);
const app = spawn(python, ['app.py'], { stdio: 'inherit', env: process.env });
app.on('error', (error) => {
  console.error(`Could not start the app with ${python}. Run npm install first.`, error.message);
  process.exit(1);
});
app.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exit(code ?? 1);
});
