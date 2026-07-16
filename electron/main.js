const { app, BrowserWindow, dialog, ipcMain, screen, Notification } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const rootDir = path.resolve(__dirname, '..');
const runnerPath = path.join(rootDir, 'scripts', 'electron_runner.py');
const debugLogPath = path.join(rootDir, 'tmp', 'electron-debug.log');

const isDev = !!process.env.VITE_DEV_SERVER;
const devServerUrl = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173';

let mainWindow = null;
let miniWindow = null;
let currentRun = null;
let miniCloseTimer = null;
let miniCompletionNotified = false;
let miniStatus = {
  state: 'idle', total: 0, completed: 0,
  successCount: 0, failureCount: 0,
  currentProject: '', message: '\u7b49\u5f85\u4efb\u52a1\u5f00\u59cb'
};

function debugLog(msg) {
  try {
    fs.mkdirSync(path.dirname(debugLogPath), { recursive: true });
    fs.appendFileSync(debugLogPath, `[${new Date().toISOString()}] ${msg}\n`, 'utf8');
  } catch (_) {}
}

// ---- Window management ----

function createWindow() {
  debugLog('createWindow');
  mainWindow = new BrowserWindow({
    width: 1440, height: 920, minWidth: 1180, minHeight: 760,
    backgroundColor: '#f4f7fb', title: '\u7279\u6b8a\u8ba2\u5355\u6253\u5305\u4e0a\u4f20\u5de5\u5177',
    icon: path.join(rootDir, 'assets', 'app.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false
    }
  });
  if (isDev) {
    debugLog('loading dev: ' + devServerUrl);
    mainWindow.loadURL(devServerUrl);
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(rootDir, 'dist', 'index.html'));
  }
  mainWindow.webContents.on('did-finish-load', () => debugLog('renderer loaded'));
  mainWindow.webContents.on('did-fail-load', (_, c, d) => debugLog('fail-load ' + c + ' ' + d));
  mainWindow.on('close', (event) => {
    if (!currentRun) return;
    const choice = dialog.showMessageBoxSync(mainWindow, {
      type: 'warning', buttons: ['\u7ee7\u7eed\u7b49\u5f85', '\u505c\u6b62\u5e76\u5173\u95ed'],
      defaultId: 0, cancelId: 0, title: '\u4efb\u52a1\u6b63\u5728\u6267\u884c',
      message: '\u6253\u5305\u4efb\u52a1\u4ecd\u5728\u6267\u884c\uff0c\u5173\u95ed\u7a97\u53e3\u4f1a\u505c\u6b62\u5f53\u524d\u4efb\u52a1\u3002'
    });
    if (choice === 0) { event.preventDefault(); return; }
    stopCurrentRun();
  });
}

function createMiniWindow() {
  if (miniWindow && !miniWindow.isDestroyed()) return miniWindow;
  const { workArea } = screen.getPrimaryDisplay();
  const w = 380, h = 150;
  miniWindow = new BrowserWindow({
    width: w, height: h,
    x: workArea.x + workArea.width - w - 18, y: workArea.y + workArea.height - h - 18,
    frame: false, resizable: false, transparent: true,
    alwaysOnTop: true, skipTaskbar: true, show: false, backgroundColor: '#00000000',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false }
  });
  if (isDev) miniWindow.loadURL(devServerUrl + '/mini.html');
  else miniWindow.loadFile(path.join(rootDir, 'dist', 'mini.html'));
  miniWindow.webContents.on('did-finish-load', () => sendMiniStatus());
  miniWindow.on('closed', () => { miniWindow = null; });
  return miniWindow;
}

function showMiniStatus(status) {
  if (miniCloseTimer) { clearTimeout(miniCloseTimer); miniCloseTimer = null; }
  miniStatus = { ...miniStatus, ...(status || {}) };
  const win = createMiniWindow();
  if (!win.isVisible()) win.showInactive();
  sendMiniStatus();
}

function closeMiniWindow(delay) {
  if (miniCloseTimer) clearTimeout(miniCloseTimer);
  miniCloseTimer = setTimeout(() => {
    miniCloseTimer = null;
    if (miniWindow && !miniWindow.isDestroyed()) miniWindow.close();
  }, delay || 0);
}

function sendMiniStatus() {
  if (miniWindow && !miniWindow.isDestroyed() && !miniWindow.webContents.isLoading()) {
    miniWindow.webContents.send('mini:status', miniStatus);
  }
}

function notifyDone(title, body) {
  if (miniCompletionNotified) return;
  miniCompletionNotified = true;
  try { if (Notification.isSupported()) new Notification({ title, body, silent: false }).show(); }
  catch (e) { debugLog('notify fail: ' + e.message); }
}

function sendRunEvent(evt) {
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('run:event', evt);
  updateMini(evt);
}

function updateMini(evt) {
  if (!miniWindow || miniWindow.isDestroyed() || !evt || !evt.type) return;
  if (evt.type === 'projectStart') {
    miniStatus = { ...miniStatus, state: 'running', currentProject: evt.project || '', message: evt.project ? `\u6b63\u5728\u6267\u884c\uff1a${evt.project}` : '\u6b63\u5728\u6267\u884c\u4efb\u52a1' };
  } else if (evt.type === 'projectResult') {
    const r = evt.data || {};
    miniStatus = { ...miniStatus, state: 'running', completed: miniStatus.completed + 1, successCount: miniStatus.successCount + (r.success ? 1 : 0), failureCount: miniStatus.failureCount + (r.success ? 0 : 1) };
  } else if (evt.type === 'done') {
    miniStatus = { ...miniStatus, state: evt.failureCount ? 'error' : 'complete', completed: evt.total || miniStatus.completed, successCount: evt.successCount || 0, failureCount: evt.failureCount || 0, message: evt.failureCount ? '\u4efb\u52a1\u7ed3\u675f\uff0c\u5b58\u5728\u5931\u8d25\u9879\u76ee' : '\u4efb\u52a1\u6267\u884c\u5b8c\u6210' };
    notifyDone(evt.failureCount ? '\u4efb\u52a1\u7ed3\u675f' : '\u4efb\u52a1\u5b8c\u6210', miniStatus.message);
  } else if (evt.type === 'error') {
    miniStatus = { ...miniStatus, state: 'error', message: evt.message || '\u4efb\u52a1\u6267\u884c\u5931\u8d25' };
    notifyDone('\u4efb\u52a1\u5f02\u5e38', miniStatus.message);
  }
  sendMiniStatus();
}

// ---- Python bridge ----

function resolvePython() {
  const cands = [path.join(rootDir, 'tools', 'python', 'python.exe'), path.join(rootDir, 'tools-cache', 'python', 'python.exe')];
  const found = cands.find(c => fs.existsSync(c));
  return found ? { exe: found, args: [] } : { exe: 'py', args: ['-3'] };
}

function buildEnv() {
  const nd = fs.existsSync(path.join(rootDir, 'tools', 'node')) ? path.join(rootDir, 'tools', 'node') : path.join(rootDir, 'tools-cache', 'node');
  const env = { ...process.env, PYTHONUTF8: '1' };
  if (fs.existsSync(nd)) {
    env.PATH = nd + path.delimiter + (env.PATH || '');
    const parts = (env.NODE_OPTIONS || '').split(/\s+/).filter(p => p && p !== '--openssl-legacy-provider');
    if (parts.length) env.NODE_OPTIONS = parts.join(' '); else delete env.NODE_OPTIONS;
  }
  return env;
}

function runPython(cmd, payload) {
  return new Promise((resolve, reject) => {
    const py = resolvePython();
    const child = spawn(py.exe, [...py.args, runnerPath, cmd], { cwd: rootDir, windowsHide: true, env: buildEnv(), stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    child.stdout.on('data', c => { stdout += c.toString('utf8'); });
    child.stderr.on('data', c => { stderr += c.toString('utf8'); });
    child.on('error', reject);
    child.on('close', code => {
      const lines = stdout.split(/\r?\n/).filter(Boolean);
      const events = [];
      for (const line of lines) { try { events.push(JSON.parse(line)); } catch { events.push({ type: 'log', message: line }); } }
      const errEvt = events.find(e => e.type === 'error');
      if (code !== 0 && errEvt) { reject(new Error(errEvt.message || stderr)); return; }
      if (code !== 0 && !events.length) { reject(new Error(stderr || 'Python exited ' + code)); return; }
      resolve(events.find(e => e.type === 'result') || events[events.length - 1] || { type: 'result', data: null });
    });
    child.stdin.end(JSON.stringify(payload || {}));
  });
}

function stopCurrentRun() {
  if (!currentRun) return;
  try { currentRun.kill(); } catch {}
  currentRun = null;
  showMiniStatus({ state: 'error', message: '\u4efb\u52a1\u5df2\u505c\u6b62', currentProject: '' });
}

// ---- IPC handlers ----

// config & tools
ipcMain.handle('config:get', async () => (await runPython('config')).data);
ipcMain.handle('config:save', async (_, p) => (await runPython('save-config', p)).data);
ipcMain.handle('tools:detect', async (_, p) => (await runPython('detect-tools', p)).data);

// projects
ipcMain.handle('projects:discover', async (_, p) => (await runPython('discover', p)).data);
ipcMain.handle('projects:refresh-branches', async (_, p) => (await runPython('refresh-branches', p)).data);
ipcMain.handle('projects:check-local-changes', async (_, p) => (await runPython('check-local-changes', p)).data);

// SVN & server
ipcMain.handle('svn:list', async (_, p) => (await runPython('svn-list', p)).data);
ipcMain.handle('server:test', async (_, p) => (await runPython('server-test', p)).data);

// templates
ipcMain.handle('templates:list', async () => (await runPython('template-list')).data);
ipcMain.handle('templates:get', async (_, id) => (await runPython('template-get', { id })).data);
ipcMain.handle('templates:save', async (_, t) => (await runPython('template-save', t)).data);
ipcMain.handle('templates:delete', async (_, id) => { await runPython('template-delete', { id }); return true; });

// history
ipcMain.handle('history:list', async () => (await runPython('history-list')).data);
ipcMain.handle('history:get', async (_, id) => (await runPython('history-get', { id })).data);

// dialogs
ipcMain.handle('dialog:directory', async (_, p) => {
  const r = await dialog.showOpenDialog(mainWindow, { defaultPath: p || rootDir, properties: ['openDirectory'] });
  return r.canceled ? '' : r.filePaths[0];
});
ipcMain.handle('dialog:executable', async (_, p) => {
  const r = await dialog.showOpenDialog(mainWindow, { defaultPath: p || rootDir, filters: [{ name: 'Executable', extensions: ['exe'] }, { name: 'All files', extensions: ['*'] }], properties: ['openFile'] });
  return r.canceled ? '' : r.filePaths[0];
});

// run lifecycle
ipcMain.handle('run:start', async (_, payload) => {
  if (currentRun) throw new Error('\u5df2\u6709\u4efb\u52a1\u6b63\u5728\u6267\u884c\u3002');
  miniStatus = { state: 'running', total: Array.isArray(payload.projects) ? payload.projects.length : 0, completed: 0, successCount: 0, failureCount: 0, currentProject: '', message: '\u6b63\u5728\u6267\u884c\u4efb\u52a1' };
  miniCompletionNotified = false;
  showMiniStatus();
  const py = resolvePython();
  currentRun = spawn(py.exe, [...py.args, runnerPath, 'run'], { cwd: rootDir, windowsHide: true, env: buildEnv(), stdio: ['pipe', 'pipe', 'pipe'] });
  let buffer = '';
  currentRun.stdout.on('data', chunk => {
    buffer += chunk.toString('utf8');
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || '';
    lines.forEach(line => {
      if (!line.trim()) return;
      try { sendRunEvent(JSON.parse(line)); } catch { sendRunEvent({ type: 'log', message: line, level: 'normal' }); }
    });
  });
  currentRun.stderr.on('data', c => sendRunEvent({ type: 'log', level: 'error', message: c.toString('utf8') }));
  currentRun.on('error', e => { sendRunEvent({ type: 'error', message: e.message }); currentRun = null; });
  currentRun.on('close', code => {
    if (buffer.trim()) { try { sendRunEvent(JSON.parse(buffer)); } catch { sendRunEvent({ type: 'log', message: buffer, level: 'normal' }); } }
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('run:exit', { code });
    if (miniWindow && !miniWindow.isDestroyed() && miniStatus.state === 'running') {
      const failed = code !== 0;
      showMiniStatus({ state: failed ? 'error' : 'complete', completed: miniStatus.total || miniStatus.completed, message: failed ? `\u4efb\u52a1\u7ed3\u675f\uff0c\u9000\u51fa\u7801 ${code}` : '\u4efb\u52a1\u6267\u884c\u5b8c\u6210', currentProject: '' });
      notifyDone(failed ? '\u4efb\u52a1\u7ed3\u675f' : '\u4efb\u52a1\u5b8c\u6210', miniStatus.message);
    }
    currentRun = null;
  });
  currentRun.stdin.end(JSON.stringify(payload));
  return true;
});
ipcMain.handle('run:stop', async () => { stopCurrentRun(); return true; });

// mini window
ipcMain.handle('mini:open-main', async () => {
  if (mainWindow && !mainWindow.isDestroyed()) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.show(); mainWindow.focus(); }
  return true;
});
ipcMain.handle('mini:dismiss', async () => { closeMiniWindow(); return true; });

// ---- App lifecycle ----
app.whenReady().then(() => { debugLog('app ready'); createWindow(); });
app.on('window-all-closed', () => { debugLog('window-all-closed'); stopCurrentRun(); if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
