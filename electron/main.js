const { app, BrowserWindow, dialog, ipcMain, screen, Notification } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const os = require('os');
const { resolvePython } = require('./runtime');

// ---- Asar-aware resource resolution ----
const isAsar = __dirname.endsWith('app.asar') || __dirname.includes('app.asar' + path.sep);
let rootDir;
let extractedRoot = null;

if (isAsar) {
  extractedRoot = path.join(os.tmpdir(), 'zbuild-resources');
  const asarRoot = path.resolve(__dirname, '..');

  function extractDir(dirName) {
    const src = path.join(asarRoot, dirName);
    const dst = path.join(extractedRoot, dirName);
    if (!fs.existsSync(dst)) {
      fs.mkdirSync(dst, { recursive: true });
    }
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
      const s = path.join(src, entry.name);
      const d = path.join(dst, entry.name);
      if (entry.isDirectory()) {
        extractDir(path.join(dirName, entry.name));
      } else {
        // Force overwrite to keep extracted assets in sync
        try { fs.copyFileSync(s, d); } catch (_) {}
      }
    }
  }

  extractDir('scripts');
  extractDir('references');
}

rootDir = path.resolve(__dirname, '..');
const pyRoot = extractedRoot || rootDir;

const runnerPath = path.join(pyRoot, 'scripts', 'electron_runner.py');
const debugLogPath = path.join(pyRoot, 'tmp', 'electron-debug.log');

const isDev = !!process.env.VITE_DEV_SERVER;
const devServerUrl = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173';

let mainWindow = null;
let miniWindow = null;
let currentRun = null;
let miniCloseTimer = null;
let miniCompletionNotified = false;
let miniDismissed = false;
let miniStatus = {
  state: 'idle', total: 0, completed: 0,
  successCount: 0, failureCount: 0,
  currentProject: '', message: '\u7b49\u5f85\u4efb\u52a1\u5f00\u59cb'
};

function debugLog(msg) {
  try {
    fs.mkdirSync(path.dirname(debugLogPath), { recursive: true });
    if (fs.existsSync(debugLogPath)) {
      const stats = fs.statSync(debugLogPath);
      if (stats.size > 5 * 1024 * 1024) {
        fs.writeFileSync(debugLogPath, `[${new Date().toISOString()}] --- Log truncated (exceeded 5MB) ---\n`, 'utf8');
      }
    }
    fs.appendFileSync(debugLogPath, `[${new Date().toISOString()}] ${msg}\n`, 'utf8');
  } catch (_) {}
}

// ---- Window management ----

function createWindow() {
  debugLog('createWindow');
  const iconPath = path.join(rootDir, 'assets', 'app.ico');
  const windowOpts = {
    width: 1440, height: 920, minWidth: 1180, minHeight: 760,
    backgroundColor: '#f4f7fb', title: '\u7279\u6b8a\u8ba2\u5355\u6253\u5305\u4e0a\u4f20\u5de5\u5177',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false
    }
  };
  if (fs.existsSync(iconPath)) windowOpts.icon = iconPath;
  mainWindow = new BrowserWindow(windowOpts);
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
  const w = 380, h = 200;
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
  // Mini window feature disabled as requested by user
  return;
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
  debugLog('sendRunEvent: ' + JSON.stringify(evt));
  if (evt && evt.type === 'log') {
    if (evt.level === 'warn') evt.level = 'warning';
    else if (evt.level === 'debug' || evt.level === 'normal') evt.level = 'info';
  }
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('run:event', evt);
  updateMini(evt);
}

function updateMini(evt) {
  if (!miniWindow || miniWindow.isDestroyed() || !evt || !evt.type) return;
  if (evt.type === 'projectStart') {
    miniStatus = { ...miniStatus, state: 'running', currentProject: evt.project || '', message: evt.project ? `\u6b63\u5728\u6267\u884c\uff1a${evt.project}` : '\u6b63\u5728\u6267\u884c\u4efb\u52a1' };
  } else if (evt.type === 'projectResult') {
    miniStatus = { ...miniStatus, state: 'running', completed: miniStatus.completed + 1, successCount: miniStatus.successCount + (evt.success ? 1 : 0), failureCount: miniStatus.failureCount + (evt.success ? 0 : 1) };
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

function buildEnv() {
  const candidates = [
    path.join(pyRoot, 'tmp', 'node-shims'),
    path.join(pyRoot, 'runtime', 'node'),
    path.join(pyRoot, 'tools', 'node'),
    path.join(pyRoot, 'tools-cache', 'node'),
  ];
  const env = { ...process.env, PYTHONUTF8: '1', ZBUILD_DATA_DIR: app.getPath('userData') };
  const extraPaths = candidates.filter(c => fs.existsSync(c));

  // Ensure py.exe / Git and common system dirs are always on PATH.
  // When Electron is launched from a desktop shortcut the user PATH may omit
  // Git, which previously made discover return empty branch lists.
  const systemPaths = [
    'D:\\application\\python',
    'C:\\Users\\zhaichong\\AppData\\Local\\Programs\\Python\\Python312',
    'C:\\Program Files\\Git\\cmd',
    'C:\\Program Files\\Git\\bin',
    'D:\\application\\Git\\cmd',
    'D:\\application\\Git\\bin',
    'C:\\Windows',
    'C:\\Windows\\system32',
  ].filter(p => fs.existsSync(p) && !((env.PATH || '').toLowerCase().includes(p.toLowerCase())));

  const allExtra = [...extraPaths, ...systemPaths];
  if (allExtra.length) {
    env.PATH = allExtra.join(path.delimiter) + path.delimiter + (env.PATH || '');
  }
  // Always strip --openssl-legacy-provider: it is only valid for Node >= 17 (OpenSSL 3)
  // and causes Node 14 (used by legacy frontend projects) to abort at startup.
  const parts = (env.NODE_OPTIONS || '').split(/\s+/).filter(p => p && p !== '--openssl-legacy-provider');
  if (parts.length) env.NODE_OPTIONS = parts.join(' '); else delete env.NODE_OPTIONS;
  return env;
}

function runPython(cmd, payload, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    const py = resolvePython(pyRoot);
    const child = spawn(py.exe, [...py.args, runnerPath, cmd], { cwd: pyRoot, windowsHide: true, env: buildEnv(), stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    let timer = null;

    if (timeoutMs > 0) {
      timer = setTimeout(() => {
        try { child.kill('SIGKILL'); } catch (_) {}
        reject(new Error(`Python 命令 '${cmd}' 执行超时 (${timeoutMs}ms)`));
      }, timeoutMs);
    }

    child.stdout.on('data', c => { stdout += c.toString('utf8'); });
    child.stderr.on('data', c => { stderr += c.toString('utf8'); });
    child.on('error', (err) => {
      if (timer) clearTimeout(timer);
      reject(err);
    });
    child.on('close', code => {
      if (timer) clearTimeout(timer);
      const lines = stdout.split(/\r?\n/).filter(Boolean);
      const events = [];
      for (const line of lines) { try { events.push(JSON.parse(line)); } catch { events.push({ type: 'log', message: line }); } }
      const errEvt = events.find(e => e.type === 'error');
      if (code !== 0 && errEvt) { reject(new Error(errEvt.message || stderr)); return; }
      if (code !== 0 && !events.length) { reject(new Error(stderr || 'Python exited ' + code)); return; }
      const resultEvt = events.find(e => e.type === 'result') || {};
      const { type: _t, ...resultData } = resultEvt;
      if (resultData.success === false) {
        reject(new Error(resultData.error || 'Python command failed'));
        return;
      }
      resolve(resultData);
    });
    child.stdin.end(JSON.stringify(payload || {}));
  });
}

let runStopping = false;
function stopCurrentRun() {
  if (!currentRun) return;
  runStopping = true;
  try { currentRun.kill(); } catch {}
  currentRun = null;
  miniDismissed = false;
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('run:exit', { code: 1 });
  showMiniStatus({ state: 'error', message: '\u4efb\u52a1\u5df2\u505c\u6b62', currentProject: '' });
}

// ---- Config format conversion ----

function pyConfigToFrontend(py) {
  const server = py.server || {};
  const svnCreds = py.svn_credentials || {};
  const tools = py.tools || {};
  return {
    rootPath: py.root_path || '',
    svnRootUrl: py.svn_root || '',
    buildCommand: py.build_command || 'deploy.sh',
    buildCommands: py.build_commands || {},
    artifactPaths: py.artifact_paths || ['dist'],
    projectArtifactPaths: py.project_artifact_paths || {},
    orderDirPath: py.order_dir_path || '',
    selectedProjects: py.selected_projects || py.selectedProjects || [],
    projectBranches: py.project_branches || py.projectBranches || {},
    projectSvnLeaves: py.project_svn_leaves || py.projectSvnLeaves || {},
    projectServerPaths: py.project_server_paths || py.projectServerPaths || py.server_upload_paths || {},
    projectBuildCommands: py.project_build_commands || py.projectBuildCommands || py.build_commands || {},
    tools: {
      git: tools.git || '',
      bash: tools.bash || '',
      svn: tools.svn || '',
      node: tools.node || '',
      npm: tools.npm || '',
    },
    uploadAfterBuild: py.mode === 'local' ? false : (py.auto_install_deps !== false),
    uploadToServer: py.mode === 'server',
    localOutputDir: py.local_output || '',
    serverUploadPaths: py.server_upload_paths || {},
    form: {
      hospitalName: py.hospital_name || '',
      orderNo: py.order_no || '',
      createOrderDir: py.create_order_dir !== undefined ? py.create_order_dir : (py.form ? py.form.createOrderDir : false),
      svnUsername: svnCreds.username || '',
      svnPassword: svnCreds.password || '',
      serverAddress: server.host || '',
      serverUsername: server.username || '',
      serverPassword: server.password || '',
    },
  };
}

function frontendConfigToPy(fe) {
  const form = fe.form || {};
  const artifactPaths = Array.isArray(fe.artifactPaths)
    ? fe.artifactPaths
    : (typeof fe.artifactPaths === 'string'
        ? fe.artifactPaths.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean)
        : ['dist']);
  return {
    mode: fe.uploadToServer ? 'server' : (fe.uploadAfterBuild === false ? 'local' : 'svn'),
    root_path: fe.rootPath || '',
    svn_root: fe.svnRootUrl || '',
    local_output: fe.localOutputDir || '',
    order_dir_path: fe.orderDirPath || '',
    create_order_dir: !!form.createOrderDir,
    build_command: (fe.buildCommand || 'deploy.sh').trim(),
    build_commands: fe.buildCommands || {},
    artifact_paths: artifactPaths.length ? artifactPaths : ['dist'],
    project_artifact_paths: fe.projectArtifactPaths || {},
    selected_projects: fe.selectedProjects || [],
    project_branches: fe.projectBranches || {},
    project_svn_leaves: fe.projectSvnLeaves || {},
    project_server_paths: fe.projectServerPaths || fe.serverUploadPaths || {},
    project_build_commands: fe.projectBuildCommands || fe.buildCommands || {},
    auto_install_deps: true,
    auto_pull: true,
    skip_svn_commit: false,
    node_required_version: '14.21.3',
    tools: {
      git: (fe.tools && fe.tools.git) || '',
      bash: (fe.tools && fe.tools.bash) || '',
      svn: (fe.tools && fe.tools.svn) || '',
      node: (fe.tools && fe.tools.node) || '',
      npm: (fe.tools && fe.tools.npm) || '',
    },
    svn_credentials: {
      username: form.svnUsername || '',
      password: form.svnPassword || '',
    },
    server: {
      host: form.serverAddress || '',
      port: 22,
      username: form.serverUsername || '',
      password: form.serverPassword || '',
    },
    hospital_name: form.hospitalName || '',
    order_no: form.orderNo || '',
    server_upload_paths: fe.serverUploadPaths || {},
    projects: [],
  };
}

// ---- IPC handlers ----

// config & tool
ipcMain.handle('config:get', async () => {
  debugLog('config:get called');
  try {
    const result = await runPython('config');
    debugLog('config:get runPython result keys: ' + Object.keys(result || {}).join(','));
    const config = result.config || {};
    debugLog('config:get config keys: ' + Object.keys(config).join(','));
    const fe = pyConfigToFrontend(config);
    debugLog('config:get frontend config keys: ' + Object.keys(fe).join(','));
    return fe;
  } catch (e) {
    debugLog('config:get ERROR: ' + e.message + ' | ' + e.stack);
    throw e;
  }
});
ipcMain.handle('config:save', async (_, p) => {
  const pyConfig = frontendConfigToPy(p);
  await runPython('save-config', { config: pyConfig });
  return p;
});
ipcMain.handle('tools:detect', async (_, p) => {
  debugLog('tools:detect called, payload type: ' + typeof p);
  try {
    const result = await runPython('detect-tools', p);
    debugLog('tools:detect result keys: ' + Object.keys(result || {}).join(','));
    return { tools: result.tools || {}, status: {} };
  } catch (e) {
    debugLog('tools:detect ERROR: ' + e.message);
    throw e;
  }
});
ipcMain.handle('order-dir:create', async (_, p) => {
  return await runPython('create-order-dir', p);
});

// projects
ipcMain.handle('projects:discover', async (_, p) => {
  debugLog('projects:discover called, payload type: ' + typeof p);
  try {
    const result = await runPython('discover', p);
    debugLog('projects:discover result projects count: ' + (result.projects || []).length);
    return (result.projects || []).map(pr => ({
    projectName: pr.name,
    repoPath: pr.path,
    currentBranch: pr.current_branch,
    branches: pr.branches || [],
    defaultSvnLeaf: pr.default_svn_leaf,
    serverUploadPath: pr.server_upload_path || '',
    buildCommand: pr.build_command || '',
  }));
  } catch (e) {
    debugLog('projects:discover ERROR: ' + e.message);
    throw e;
  }
});
ipcMain.handle('projects:refresh-branches', async (_, p) => {
  const result = await runPython('refresh-branches', p);
  return {
    projectName: result.project_name || p.projectName || p.name || '',
    repoPath: p.repoPath || '',
    currentBranch: result.current_branch || '',
    branches: result.branches || [],
  };
});
ipcMain.handle('projects:check-local-changes', async (_, p) => {
  const result = await runPython('check-local-changes', p);
  return (result.changes || []).map(c => ({
    dirty: c.has_changes || false,
    total: (c.staged_count || 0) + (c.unstaged_count || 0) + (c.untracked_count || 0),
    files: [...(c.staged || []), ...(c.unstaged || []), ...(c.untracked || [])],
    truncated: false,
    project: c.project || '',
    repoPath: '',
    branch: c.branch || '',
  }));
});
ipcMain.handle('projects:detect-affected', async (_, p) => {
  const result = await runPython('detect-affected', p);
  return {
    affectedProjects: result.affected_projects || [],
    baseRef: result.base_ref || 'main',
    headRef: result.head_ref || 'HEAD',
  };
});
ipcMain.handle('projects:detect-affected-staged', async (_, p) => {
  const result = await runPython('detect-affected-staged', p);
  return { affectedProjects: result.affected_projects || [] };
});

// SVN & server
ipcMain.handle('svn:list', async (_, p) => {
  // Frontend sends flat {svn, url, username, password} — pass through directly
  const result = await runPython('svn-list', p);
  const entries = result.items || result.entries || [];
  // Extract name strings from entry dicts (list_svn_contents returns [{name, kind, rev}])
  if (Array.isArray(entries) && entries.length > 0 && typeof entries[0] === 'object') {
    return entries.map((e) => e.name || '').filter(Boolean);
  }
  return entries;
});
ipcMain.handle('server:test', async (_, p) => {
  const result = await runPython('server-test', p);
  return { success: result.success !== false, message: result.message || '', error: result.error || '' };
});

// templates
ipcMain.handle('templates:list', async () => {
  const result = await runPython('template-list');
  return (result.templates || []).map(t => {
    const feCfg = t.config ? pyConfigToFrontend(t.config) : {};
    return {
      id: t.template_id || t.id,
      name: t.name || '',
      description: t.description || '',
      config: feCfg,
    };
  });
});
ipcMain.handle('templates:get', async (_, id) => {
  const result = await runPython('template-get', { id });
  const t = result.template || result;
  const feCfg = t.config ? pyConfigToFrontend(t.config) : {};
  return {
    id: t.template_id || t.id,
    name: t.name || '',
    description: t.description || '',
    config: feCfg,
  };
});
ipcMain.handle('templates:save', async (_, t) => {
  const feConfig = t.config || {};
  const pyTemplate = {
    id: t.id || '',
    template_id: t.id || '',
    name: t.name,
    description: t.description || '',
    mode: feConfig.uploadToServer ? 'server' : (feConfig.uploadAfterBuild === false ? 'local' : 'svn'),
    config: feConfig ? frontendConfigToPy(feConfig) : {},
  };
  const result = await runPython('template-save', pyTemplate);
  const savedObj = result.template || result;
  return {
    id: savedObj.template_id || savedObj.id || t.id,
    name: savedObj.name || t.name,
    description: savedObj.description || t.description,
    config: savedObj.config ? pyConfigToFrontend(savedObj.config) : (t.config || {}),
  };
});
ipcMain.handle('templates:delete', async (_, id) => { await runPython('template-delete', { id }); return true; });

// history
ipcMain.handle('history:list', async () => {
  const result = await runPython('history-list');
  return (result.records || []).map(r => {
    const projs = r.projects || [];
    const successCount = projs.filter(p => p && p.success === true).length;
    const failureCount = projs.filter(p => p && p.success === false).length;
    return {
      id: r.run_id || r.id,
      startedAt: typeof r.started_at === 'number' ? new Date(r.started_at * 1000).toISOString() : (r.started_at || r.startedAt || ''),
      finishedAt: typeof r.finished_at === 'number' ? new Date(r.finished_at * 1000).toISOString() : (r.finished_at || r.finishedAt || undefined),
      status: r.success === true ? 'success' : r.success === false ? 'failed' : (r.status || 'running'),
      total: r.project_count || projs.length || 0,
      successCount,
      failureCount,
      projects: projs.map(p => p && (p.project_name || p.name) || '').filter(Boolean),
      mode: r.mode || 'svn',
      hospitalName: (r.config_snapshot && r.config_snapshot.hospital_name) || r.hospital_name || r.hospitalName || '',
      orderNo: (r.config_snapshot && r.config_snapshot.order_no) || r.order_no || r.orderNo || '',
    };
  });
});
ipcMain.handle('history:get', async (_, id) => {
  const result = await runPython('history-get', { id });
  const r = result.record || result;
  const projs = r.projects || [];
  const successCount = projs.filter(p => p && p.success === true).length;
  const failureCount = projs.filter(p => p && p.success === false).length;
  const cfgSnap = r.config_snapshot || {};
  return {
    id: r.run_id || r.id,
    startedAt: typeof r.started_at === 'number' ? new Date(r.started_at * 1000).toISOString() : (r.started_at || r.startedAt || ''),
    finishedAt: typeof r.finished_at === 'number' ? new Date(r.finished_at * 1000).toISOString() : (r.finished_at || r.finishedAt || undefined),
    status: r.success === true ? 'success' : r.success === false ? 'failed' : (r.status || 'running'),
    total: projs.length,
    successCount,
    failureCount,
    projects: projs.map(p => p && (p.project_name || p.name) || '').filter(Boolean),
    mode: r.mode || cfgSnap.mode || 'svn',
    hospitalName: cfgSnap.hospital_name || r.hospital_name || r.hospitalName || '',
    orderNo: cfgSnap.order_no || r.order_no || r.orderNo || '',
  };
});

// mock query proxy request (Node http/https backend)
const http = require('http');
const https = require('https');

ipcMain.handle('mock-query:request', async (_, { url: fullUrl, method = 'GET', body = null }) => {
  return new Promise((resolve, reject) => {
    try {
      const parsed = new URL(fullUrl);
      const requestLib = parsed.protocol === 'https:' ? https : http;
      const headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MockQueryTool/1.0',
      };
      let bodyData = null;
      if (body) {
        bodyData = typeof body === 'string' ? body : JSON.stringify(body);
        headers['Content-Length'] = Buffer.byteLength(bodyData);
      }
      const req = requestLib.request(parsed, { method: method || 'GET', headers }, (res) => {
        let chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => {
          const dataStr = Buffer.concat(chunks).toString('utf-8');
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const parsedData = JSON.parse(dataStr);
              const finalData = parsedData.data !== undefined ? parsedData.data : parsedData;
              resolve(finalData);
            } catch (e) {
              resolve(dataStr);
            }
          } else {
            reject(new Error(`远程服务器返回错误 ${res.statusCode}: ${dataStr.substring(0, 200)}`));
          }
        });
      });
      req.on('error', (err) => reject(err));
      if (bodyData) req.write(bodyData);
      req.end();
    } catch (e) {
      reject(e);
    }
  });
});

// dialogs
ipcMain.handle('dialog:directory', async (_, p) => {
  const r = await dialog.showOpenDialog(mainWindow, { defaultPath: p || pyRoot, properties: ['openDirectory'] });
  return r.canceled ? '' : r.filePaths[0];
});
ipcMain.handle('dialog:executable', async (_, p) => {
  const r = await dialog.showOpenDialog(mainWindow, { defaultPath: p || pyRoot, filters: [{ name: 'Executable', extensions: ['exe'] }, { name: 'All files', extensions: ['*'] }], properties: ['openFile'] });
  return r.canceled ? '' : r.filePaths[0];
});

// run lifecycle
ipcMain.handle('run:start', async (_, payload) => {
  debugLog('run:start called, projects: ' + (payload.projects || []).map(p => p.name).join(', '));
  if (currentRun) throw new Error('\u5df2\u6709\u4efb\u52a1\u6b63\u5728\u6267\u884c\u3002');
  // Convert frontend camelCase config to Python snake_case for the pipeline
  const pyConfig = payload.config ? frontendConfigToPy(payload.config) : {};
  const runPayload = {
    ...pyConfig,
    mode: payload.mode || pyConfig.mode || 'svn',
    stash: payload.stash || false,
    projects: (payload.projects || []).map(p => ({
      name: p.name || p.project || '',
      path: p.path || p.repoPath || '',
      branch: p.branch || '',
      svn_leaf: p.svn_leaf || p.svnLeaf || '',
      server_upload_path: p.server_upload_path || p.serverUploadPath || '',
      build_command: p.build_command || p.buildCommand || (payload.config && payload.config.buildCommands && payload.config.buildCommands[p.name || p.project]) || '',
      enabled: p.enabled !== false,
    })),
  };
  const py = resolvePython(pyRoot);
  miniStatus = { state: 'running', total: Array.isArray(runPayload.projects) ? runPayload.projects.length : 0, completed: 0, successCount: 0, failureCount: 0, currentProject: '', message: '\u6b63\u5728\u6267\u884c\u4efb\u52a1' };
  miniCompletionNotified = false;
  miniDismissed = false;
  showMiniStatus();
  debugLog('spawning python: ' + py.exe + ' ' + py.args.join(' ') + ' ' + runnerPath);
  currentRun = spawn(py.exe, [...py.args, runnerPath, 'run'], { cwd: pyRoot, windowsHide: true, env: buildEnv(), stdio: ['pipe', 'pipe', 'pipe'] });
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
  currentRun.stderr.on('data', c => {
    const msg = c.toString('utf8');
    debugLog('runner stderr: ' + msg);
    sendRunEvent({ type: 'log', level: 'error', message: msg });
  });
  currentRun.on('error', e => {
    debugLog('runner spawn error: ' + e.message);
    sendRunEvent({ type: 'error', message: e.message });
    currentRun = null;
  });
  currentRun.on('close', code => {
    debugLog('runner process closed, exit code: ' + code);
    if (runStopping) { runStopping = false; currentRun = null; return; }
    if (buffer.trim()) { try { sendRunEvent(JSON.parse(buffer)); } catch { sendRunEvent({ type: 'log', message: buffer, level: 'normal' }); } }
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('run:exit', { code });
    if (miniWindow && !miniWindow.isDestroyed() && miniStatus.state === 'running') {
      const failed = code !== 0;
      showMiniStatus({ state: failed ? 'error' : 'complete', completed: miniStatus.total || miniStatus.completed, message: failed ? `\u4efb\u52a1\u7ed3\u675f\uff0c\u9000\u51fa\u7801 ${code}` : '\u4efb\u52a1\u6267\u884c\u5b8c\u6210', currentProject: '' });
      notifyDone(failed ? '\u4efb\u52a1\u7ed3\u675f' : '\u4efb\u52a1\u5b8c\u6210', miniStatus.message);
    }
    currentRun = null;
  });
  currentRun.stdin.end(JSON.stringify(runPayload));
  return true;
});
ipcMain.handle('run:stop', async () => { stopCurrentRun(); return true; });

// mini window
ipcMain.handle('mini:open-main', async () => {
  if (mainWindow && !mainWindow.isDestroyed()) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.show(); mainWindow.focus(); }
  return true;
});
ipcMain.handle('mini:dismiss', async () => { miniDismissed = true; closeMiniWindow(); return true; });

// ---- App lifecycle ----
process.on('uncaughtException', (err) => { debugLog('uncaughtException: ' + (err && err.stack || err)); });
process.on('unhandledRejection', (reason) => { debugLog('unhandledRejection: ' + reason); });
app.whenReady().then(() => { debugLog('app ready'); createWindow(); });
app.on('window-all-closed', () => { debugLog('window-all-closed'); stopCurrentRun(); if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
