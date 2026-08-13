const { app, BrowserWindow, dialog, ipcMain, screen, Notification, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const os = require('os');
const { autoUpdater } = require('electron-updater');
const { resolvePython } = require('./runtime');
const {
  MOCK_HTTP_ALLOWED_METHODS,
  DB_ALLOWED_DATABASES,
  DB_MAX_STATEMENTS,
  assertSafeMockUrl,
  assertDbHostAllowed,
  assertSafeInsertSql,
} = require('./security');
const { encryptConfigSecrets, decryptConfigSecrets } = require('./configCrypto');

// ---- Asar-aware resource resolution ----
// Prefer a per-user path under the home directory (not a shared world-writable
// temp folder) to reduce resource-planting races on multi-user machines.
const isAsar = __dirname.endsWith('app.asar') || __dirname.includes('app.asar' + path.sep);
let rootDir;
let extractedRoot = null;

if (isAsar) {
  extractedRoot = path.join(os.homedir(), '.zbuild', 'extracted-resources');
  const asarRoot = path.resolve(__dirname, '..');

  function extractDir(dirName) {
    const src = path.join(asarRoot, dirName);
    const dst = path.join(extractedRoot, dirName);
    if (!fs.existsSync(dst)) {
      fs.mkdirSync(dst, { recursive: true, mode: 0o700 });
    }
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
      // Never follow symlinks out of the asar tree
      if (entry.isSymbolicLink && entry.isSymbolicLink()) continue;
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

// ---- Auto-update ----

let updateDownloadInProgress = false;

autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;
autoUpdater.disableWebInstaller = true;
autoUpdater.logger = {
  info: (msg) => debugLog('updater info: ' + msg),
  warn: (msg) => debugLog('updater warn: ' + msg),
  error: (msg) => debugLog('updater error: ' + msg),
  debug: (msg) => debugLog('updater debug: ' + msg),
};

function sendUpdateStatus(status) {
  debugLog('sendUpdateStatus: ' + JSON.stringify(status));
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('update:status', status);
  }
}

function updateState(state, extra) {
  sendUpdateStatus(Object.assign({ state }, extra || {}));
}

autoUpdater.on('checking-for-update', () => updateState('checking'));
autoUpdater.on('update-available', (info) => {
  updateState('available', { version: info.version || '', releaseNotes: info.releaseNotes || '' });
});
autoUpdater.on('update-not-available', () => updateState('not-available'));
autoUpdater.on('error', (err) => {
  debugLog('updater error event: ' + (err && err.message || err));
  updateState('error', { message: (err && err.message) || String(err) });
});
autoUpdater.on('download-progress', (progress) => {
  const percent = typeof progress.percent === 'number' ? Math.round(progress.percent * 10) / 10 : 0;
  updateState('downloading', {
    percent,
    bytesPerSecond: progress.bytesPerSecond || 0,
    transferred: progress.transferred || 0,
    total: progress.total || 0,
  });
});
autoUpdater.on('update-downloaded', (info) => {
  updateState('downloaded', { version: info.version || '' });
});

function initUpdater() {
  if (!app.isPackaged) {
    debugLog('updater skipped (dev mode)');
    return;
  }
  debugLog('updater initialized, renderer will trigger check');
}

function isTransientNetworkError(err) {
  const msg = (err && err.message) || String(err);
  return msg.includes('ERR_NETWORK_CHANGED') ||
         msg.includes('ERR_CONNECTION_RESET') ||
         msg.includes('ETIMEDOUT');
}

async function withNetworkRetry(fn, label) {
  try {
    return await fn();
  } catch (err) {
    if (isTransientNetworkError(err)) {
      debugLog(`updater: ${label} network glitch detected (${err.message || err}), retrying after 1s...`);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return await fn();
    }
    throw err;
  }
}

ipcMain.handle('update:check', async () => {
  if (!app.isPackaged) return { state: 'not-available' };
  try {
    await withNetworkRetry(() => autoUpdater.checkForUpdates(), 'checkForUpdates');
    return { state: 'checking' };
  } catch (err) {
    return { state: 'error', message: (err && err.message) || String(err) };
  }
});
ipcMain.handle('update:download', async () => {
  if (!app.isPackaged) return { state: 'not-available' };
  try {
    updateDownloadInProgress = true;
    await withNetworkRetry(() => autoUpdater.downloadUpdate(), 'downloadUpdate');
    updateDownloadInProgress = false;
    return { state: 'downloaded' };
  } catch (err) {
    updateDownloadInProgress = false;
    updateState('error', { message: (err && err.message) || String(err) });
    return { state: 'error', message: (err && err.message) || String(err) };
  }
});
ipcMain.handle('update:install', async () => {
  if (!app.isPackaged) return false;
  autoUpdater.quitAndInstall();
  return true;
});

// ---- Window management ----

function createWindow() {
  debugLog('createWindow');
  const iconPath = path.join(rootDir, 'assets', 'app.ico');
  const windowOpts = {
    width: 1440, height: 920, minWidth: 1180, minHeight: 760,
    backgroundColor: '#f4f7fb', title: '\u7279\u6b8a\u8ba2\u5355\u6253\u5305\u4e0a\u4f20\u5de5\u5177',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
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

let savedMiniBounds = null;

function createMiniWindow() {
  if (miniWindow && !miniWindow.isDestroyed()) return miniWindow;
  const { workArea } = screen.getPrimaryDisplay();
  const w = 390, h = 180;
  const defaultX = workArea.x + workArea.width - w - 24;
  const defaultY = workArea.y + workArea.height - h - 36;

  miniWindow = new BrowserWindow({
    width: w, height: h,
    x: savedMiniBounds ? savedMiniBounds.x : defaultX,
    y: savedMiniBounds ? savedMiniBounds.y : defaultY,
    frame: false, resizable: false, transparent: true,
    alwaysOnTop: true, skipTaskbar: true, show: false, backgroundColor: '#00000000',
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    }
  });

  miniWindow.on('moved', () => {
    if (miniWindow && !miniWindow.isDestroyed()) {
      savedMiniBounds = miniWindow.getBounds();
    }
  });

  if (isDev) miniWindow.loadURL(devServerUrl + '/mini.html');
  else miniWindow.loadFile(path.join(rootDir, 'dist', 'mini.html'));
  miniWindow.webContents.on('did-finish-load', () => sendMiniStatus());
  miniWindow.on('closed', () => { miniWindow = null; });
  return miniWindow;
}

function showMiniStatus(status) {
  if (status) {
    miniStatus = { ...miniStatus, ...status };
  }
  if (miniDismissed) return;

  const win = createMiniWindow();
  if (win && !win.isDestroyed()) {
    if (miniCloseTimer) {
      clearTimeout(miniCloseTimer);
      miniCloseTimer = null;
    }
    if (!win.isVisible()) {
      win.showInactive();
    }
    sendMiniStatus();
  }
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
  // OS system notification popup disabled as requested (desktop pet visual status is used instead)
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
  if (!evt || !evt.type) return;
  if (evt.type === 'projectStart') {
    miniStatus = {
      ...miniStatus,
      state: 'running',
      currentProject: evt.project || '',
      currentStep: '准备开始构建...',
      message: evt.project ? `正在构建：${evt.project}` : '正在执行任务'
    };
    showMiniStatus();
  } else if (evt.type === 'step-start' || evt.type === 'step_start') {
    const stepName = evt.step || evt.name || '';
    miniStatus = {
      ...miniStatus,
      state: 'running',
      currentStep: stepName,
      message: stepName ? `${miniStatus.currentProject ? miniStatus.currentProject + ' - ' : ''}${stepName}` : miniStatus.message
    };
    sendMiniStatus();
  } else if (evt.type === 'step-end' || evt.type === 'step_end') {
    const stepName = evt.step || evt.name || '';
    if (evt.success === false) {
      miniStatus = {
        ...miniStatus,
        currentStep: `${stepName} 遇到问题`
      };
    }
    sendMiniStatus();
  } else if (evt.type === 'projectResult') {
    const newCompleted = miniStatus.completed + 1;
    const newSuccess = miniStatus.successCount + (evt.success ? 1 : 0);
    const newFail = miniStatus.failureCount + (evt.success ? 0 : 1);
    miniStatus = {
      ...miniStatus,
      state: 'running',
      completed: newCompleted,
      successCount: newSuccess,
      failureCount: newFail,
      currentStep: evt.success ? `项目 ${evt.project || ''} 打包成功` : `项目 ${evt.project || ''} 打包失败`
    };
    sendMiniStatus();
  } else if (evt.type === 'log') {
    const rawMsg = evt.message || '';
    if (rawMsg && (rawMsg.includes('building') || rawMsg.includes('Building') || rawMsg.includes('npm run') || rawMsg.includes('vite') || rawMsg.includes('webpack') || rawMsg.includes('svn') || rawMsg.includes('Uploading') || evt.level === 'error')) {
      miniStatus.latestLog = rawMsg.slice(0, 80);
      sendMiniStatus();
    }
  } else if (evt.type === 'done') {
    const hasFail = (evt.failureCount || 0) > 0;
    miniStatus = {
      ...miniStatus,
      state: hasFail ? 'error' : 'complete',
      completed: evt.total || miniStatus.completed,
      successCount: evt.successCount ?? miniStatus.successCount,
      failureCount: evt.failureCount ?? miniStatus.failureCount,
      currentStep: hasFail ? '部分项目打包失败' : '所有项目打包已完成 🎉',
      message: hasFail ? '任务结束，存在失败项目' : '所有项目打包顺利完成！'
    };
    notifyDone(hasFail ? '任务结束' : '打包完成', miniStatus.message);
    sendMiniStatus();
    if (!hasFail) {
      closeMiniWindow(6000);
    }
  } else if (evt.type === 'error') {
    miniStatus = {
      ...miniStatus,
      state: 'error',
      currentStep: '发生错误',
      message: evt.message || '任务执行失败'
    };
    notifyDone('任务异常', miniStatus.message);
    sendMiniStatus();
  }
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

  // Dynamically collect common Python, Git, SVN, Node, and Windows system paths
  const localAppData = process.env.LOCALAPPDATA;
  const userProfile = process.env.USERPROFILE;
  const programFiles = process.env.ProgramFiles || 'C:\\Program Files';
  const programFilesX86 = process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)';
  const systemRoot = process.env.SystemRoot || 'C:\\Windows';

  const searchBases = [localAppData, userProfile, programFiles, programFilesX86].filter(Boolean);
  const detectedSystemPaths = [];

  // Python directories
  for (const base of searchBases) {
    const pyBase = path.join(base, 'Programs', 'Python');
    if (fs.existsSync(pyBase)) {
      try {
        for (const entry of fs.readdirSync(pyBase, { withFileTypes: true })) {
          if (entry.isDirectory()) detectedSystemPaths.push(path.join(pyBase, entry.name));
        }
      } catch (_) {}
    }
  }

  // Git, SVN, Node, Windows static candidates
  const staticAdditions = [
    path.join(programFiles, 'Git', 'cmd'),
    path.join(programFiles, 'Git', 'bin'),
    path.join(programFilesX86, 'Git', 'cmd'),
    path.join(programFilesX86, 'Git', 'bin'),
    localAppData && path.join(localAppData, 'Programs', 'Git', 'cmd'),
    localAppData && path.join(localAppData, 'Programs', 'Git', 'bin'),
    'D:\\application\\Git\\cmd',
    'D:\\application\\Git\\bin',
    path.join(programFiles, 'SlikSvn', 'bin'),
    path.join(programFiles, 'TortoiseSVN', 'bin'),
    path.join(programFilesX86, 'SlikSvn', 'bin'),
    path.join(programFilesX86, 'TortoiseSVN', 'bin'),
    'D:\\application\\SlikSvn\\bin',
    path.join(programFiles, 'nodejs'),
    'D:\\application\\nodejs',
    'D:\\application\\python',
    systemRoot,
    path.join(systemRoot, 'System32'),
  ].filter(Boolean);

  const systemPaths = [...detectedSystemPaths, ...staticAdditions].filter(
    p => fs.existsSync(p) && !((env.PATH || '').toLowerCase().includes(p.toLowerCase()))
  );

  const allExtra = [...extraPaths, ...systemPaths];
  if (allExtra.length) {
    env.PATH = allExtra.join(path.delimiter) + path.delimiter + (env.PATH || '');
  }
  const parts = (env.NODE_OPTIONS || '').split(/\s+/).filter(p => p && p !== '--openssl-legacy-provider');
  if (parts.length) env.NODE_OPTIONS = parts.join(' '); else delete env.NODE_OPTIONS;
  // Tell Python subprocesses where the Electron resources dir is so bundled.py
  // can find runtime/python, runtime/node etc. in the packaged app.
  if (process.resourcesPath) env.ZBUILD_RESOURCES_DIR = process.resourcesPath;
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
    enableDeskPet: py.enable_desk_pet !== false,
    deskPetStyle: py.desk_pet_style === 'blob' ? 'blob' : 'pixel',
    form: {
      hospitalName: py.hospital_name || '',
      orderNo: py.order_no || '',
      orderNotes: py.order_notes || '',
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
    order_notes: form.orderNotes || '',
    server_upload_paths: fe.serverUploadPaths || {},
    enable_desk_pet: fe.enableDeskPet !== false,
    desk_pet_style: fe.deskPetStyle === 'blob' ? 'blob' : 'pixel',
    projects: [],
  };
}

function nodeDetectTools(configTools) {
  const tools = { git: '', bash: '', svn: '', node: '', npm: '' };
  const configured = configTools || {};

  const findExecutable = (name, cfg, candidates) => {
    if (cfg && typeof cfg === 'string' && cfg.trim() && fs.existsSync(cfg.trim())) return cfg.trim();
    for (const c of candidates) {
      if (c && fs.existsSync(c)) return c;
    }
    try {
      const { spawnSync } = require('child_process');
      const res = spawnSync('where', [name], { windowsHide: true });
      if (res.status === 0 && res.stdout) {
        const firstLine = res.stdout.toString().split(/\r?\n/)[0].trim();
        if (firstLine && fs.existsSync(firstLine)) return firstLine;
      }
    } catch (_) {}
    return '';
  };

  const localAppData = process.env.LOCALAPPDATA || '';
  const userProfile = process.env.USERPROFILE || '';
  const programFiles = process.env.ProgramFiles || 'C:\\Program Files';
  const programFilesX86 = process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)';

  tools.git = findExecutable('git', configured.git, [
    path.join(programFiles, 'Git', 'cmd', 'git.exe'),
    path.join(programFiles, 'Git', 'bin', 'git.exe'),
    path.join(programFilesX86, 'Git', 'cmd', 'git.exe'),
    localAppData && path.join(localAppData, 'Programs', 'Git', 'cmd', 'git.exe'),
    userProfile && path.join(userProfile, 'AppData', 'Local', 'Programs', 'Git', 'cmd', 'git.exe'),
    'D:\\application\\Git\\cmd\\git.exe',
    'D:\\Git\\cmd\\git.exe',
    'C:\\Git\\cmd\\git.exe',
  ]);

  tools.bash = findExecutable('bash', configured.bash, [
    path.join(programFiles, 'Git', 'bin', 'bash.exe'),
    path.join(programFiles, 'Git', 'usr', 'bin', 'bash.exe'),
    path.join(programFilesX86, 'Git', 'bin', 'bash.exe'),
    localAppData && path.join(localAppData, 'Programs', 'Git', 'bin', 'bash.exe'),
    userProfile && path.join(userProfile, 'AppData', 'Local', 'Programs', 'Git', 'bin', 'bash.exe'),
    'D:\\application\\Git\\bin\\bash.exe',
  ]);

  tools.svn = findExecutable('svn', configured.svn, [
    path.join(programFiles, 'TortoiseSVN', 'bin', 'svn.exe'),
    path.join(programFiles, 'SlikSvn', 'bin', 'svn.exe'),
    path.join(programFilesX86, 'TortoiseSVN', 'bin', 'svn.exe'),
    path.join(programFilesX86, 'SlikSvn', 'bin', 'svn.exe'),
    localAppData && path.join(localAppData, 'Programs', 'TortoiseSVN', 'bin', 'svn.exe'),
    localAppData && path.join(localAppData, 'Programs', 'SlikSvn', 'bin', 'svn.exe'),
    'D:\\application\\SlikSvn\\bin\\svn.exe',
    'D:\\SlikSvn\\bin\\svn.exe',
    'D:\\TortoiseSVN\\bin\\svn.exe',
  ]);

  tools.node = findExecutable('node', configured.node, [
    process.resourcesPath && path.join(process.resourcesPath, 'runtime', 'node', 'node.exe'),
    path.join(programFiles, 'nodejs', 'node.exe'),
    path.join(programFilesX86, 'nodejs', 'node.exe'),
    localAppData && path.join(localAppData, 'Programs', 'nodejs', 'node.exe'),
    'D:\\application\\nodejs\\node.exe',
  ]);

  tools.npm = findExecutable('npm', configured.npm, [
    process.resourcesPath && path.join(process.resourcesPath, 'runtime', 'node', 'npm.cmd'),
    path.join(programFiles, 'nodejs', 'npm.cmd'),
    path.join(programFilesX86, 'nodejs', 'npm.cmd'),
    localAppData && path.join(localAppData, 'Programs', 'nodejs', 'npm.cmd'),
    'D:\\application\\nodejs\\npm.cmd',
  ]);

  const resultTools = {};
  for (const [k, v] of Object.entries(tools)) {
    resultTools[k] = { path: v, version: null };
  }
  return resultTools;
}

// ---- IPC handlers ----

// config & tool
ipcMain.handle('config:get', async () => {
  debugLog('config:get called');
  try {
    const result = await runPython('config');
    const config = decryptConfigSecrets(result.config || {});
    return pyConfigToFrontend(config);
  } catch (e) {
    debugLog('config:get ERROR, attempting fallback read: ' + e.message);
    const userData = app.getPath('userData');
    const configFile = path.join(userData, 'tool-config.json');
    if (fs.existsSync(configFile)) {
      try {
        const raw = decryptConfigSecrets(JSON.parse(fs.readFileSync(configFile, 'utf8')));
        return pyConfigToFrontend(raw);
      } catch (_) {}
    }
    return pyConfigToFrontend({});
  }
});
ipcMain.handle('config:save', async (_, p) => {
  const pyConfig = frontendConfigToPy(p);
  // Persist secrets via OS-backed safeStorage (DPAPI on Windows) when available
  const toStore = encryptConfigSecrets(pyConfig);
  try {
    await runPython('save-config', { config: toStore });
  } catch (e) {
    debugLog('config:save Python failed, saving directly to userData: ' + e.message);
    const userData = app.getPath('userData');
    const configFile = path.join(userData, 'tool-config.json');
    fs.mkdirSync(userData, { recursive: true });
    fs.writeFileSync(configFile, JSON.stringify(toStore, null, 2), 'utf8');
  }
  // Return the plaintext form state to the renderer (do not echo ciphertext)
  return p;
});
ipcMain.handle('tools:detect', async (_, p) => {
  debugLog('tools:detect called');
  try {
    const result = await runPython('detect-tools', p);
    return { tools: result.tools || {}, status: {} };
  } catch (e) {
    debugLog('tools:detect Python failed, fallback to Node detection: ' + e.message);
    const fallbackTools = nodeDetectTools(p && p.tools);
    return { tools: fallbackTools, status: {} };
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

// mock query proxy request (Node http/https backend) — hardened against SSRF
const http = require('http');
const https = require('https');
const dns = require('dns').promises;

const MOCK_HTTP_TIMEOUT_MS = 15000;
const MOCK_HTTP_MAX_BYTES = 2 * 1024 * 1024; // 2 MB

/** After DNS resolve, reject if any answer is cloud metadata IP. */
async function assertResolvedHostSafe(hostname) {
  try {
    const records = await dns.lookup(hostname, { all: true });
    for (const rec of records) {
      if (rec.address === '169.254.169.254') {
        throw new Error('DNS 解析指向云元数据地址，已拦截');
      }
    }
  } catch (e) {
    if (e && e.message && e.message.includes('云元数据')) throw e;
    // DNS failure is handled by the request itself
  }
}

ipcMain.handle('mock-query:request', async (_, { url: fullUrl, method = 'GET', body = null }) => {
  const parsed = assertSafeMockUrl(fullUrl);
  const verb = String(method || 'GET').toUpperCase();
  if (!MOCK_HTTP_ALLOWED_METHODS.has(verb)) {
    throw new Error(`不允许的 HTTP 方法: ${verb}（仅支持 GET/POST）`);
  }
  await assertResolvedHostSafe(parsed.hostname);

  return new Promise((resolve, reject) => {
    try {
      const requestLib = parsed.protocol === 'https:' ? https : http;
      const headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'zbuild-MockQueryTool/2.0',
      };
      let bodyData = null;
      if (body != null && verb !== 'GET') {
        bodyData = typeof body === 'string' ? body : JSON.stringify(body);
        if (Buffer.byteLength(bodyData) > MOCK_HTTP_MAX_BYTES) {
          reject(new Error('请求体过大'));
          return;
        }
        headers['Content-Length'] = Buffer.byteLength(bodyData);
      }
      const req = requestLib.request(
        parsed,
        { method: verb, headers, timeout: MOCK_HTTP_TIMEOUT_MS },
        (res) => {
          // Do not follow redirects automatically (Node default); reject 3xx with Location to private metadata
          if (res.statusCode >= 300 && res.statusCode < 400) {
            res.resume();
            reject(new Error(`拒绝跟随重定向 (${res.statusCode})`));
            return;
          }
          const chunks = [];
          let total = 0;
          res.on('data', (chunk) => {
            total += chunk.length;
            if (total > MOCK_HTTP_MAX_BYTES) {
              req.destroy();
              reject(new Error('响应体过大'));
              return;
            }
            chunks.push(chunk);
          });
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
        },
      );
      req.on('timeout', () => {
        req.destroy();
        reject(new Error(`请求超时 (${MOCK_HTTP_TIMEOUT_MS}ms)`));
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
  const r = await dialog.showOpenDialog(mainWindow, { defaultPath: p || pyRoot, filters: [{ name: 'Executable/Scripts', extensions: ['exe', 'bat', 'cmd'] }, { name: 'All files', extensions: ['*'] }], properties: ['openFile'] });
  return r.canceled ? '' : r.filePaths[0];
});

ipcMain.handle('tools:launch', async (_, payload) => {
  const { pathOrUrl, launchType, isCmd, cmdWorkDir } = payload || {};
  if (!pathOrUrl) throw new Error('路径或命令不能为空');

  const lowerPath = pathOrUrl.trim().toLowerCase();
  const isUrlType = launchType === 'url' || lowerPath.startsWith('http://') || lowerPath.startsWith('https://');
  const isCmdType = launchType === 'cmd' || isCmd;

  if (isCmdType) {
    const { exec } = require('child_process');
    const cwd = cmdWorkDir || pyRoot;
    const cmd = `start cmd.exe /k "cd /d ${cwd} && ${pathOrUrl}"`;
    exec(cmd, (err) => {
      if (err) {
        debugLog('Failed to launch command in cmd: ' + err.message);
      }
    });
    return { success: true, mode: 'cmd' };
  } else if (isUrlType) {
    await shell.openExternal(pathOrUrl);
    return { success: true, mode: 'url' };
  } else {
    if (!fs.existsSync(pathOrUrl)) {
      throw new Error(`路径不存在: ${pathOrUrl}`);
    }
    const err = await shell.openPath(pathOrUrl);
    if (err) {
      throw new Error(`打开路径失败: ${err}`);
    }
    return { success: true, mode: 'file' };
  }
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
  miniStatus = {
    state: 'running',
    total: Array.isArray(runPayload.projects) ? runPayload.projects.length : 0,
    completed: 0,
    successCount: 0,
    failureCount: 0,
    petStyle: payload.config?.deskPetStyle === 'blob' ? 'blob' : 'pixel',
    currentProject: '',
    currentStep: '正在准备打包环境...',
    message: '正在准备打包任务'
  };
  const isPetEnabled = payload.config ? payload.config.enableDeskPet !== false : true;
  miniCompletionNotified = false;
  miniDismissed = !isPetEnabled;
  if (isPetEnabled) {
    showMiniStatus();
  }
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

const mysql = require('mysql2/promise');

// MySQL connection and credential test
ipcMain.handle('db:test-connection', async (_event, payload) => {
  let host;
  try {
    host = assertDbHostAllowed((payload && payload.host) || '127.0.0.1');
  } catch (e) {
    return { success: false, error: e.message };
  }
  const port = parseInt((payload && payload.port) || '3306', 10);
  if (!Number.isFinite(port) || port < 1 || port > 65535) {
    return { success: false, error: '无效的数据库端口' };
  }
  const user = String((payload && payload.user) || 'root').slice(0, 64);
  const password = String((payload && payload.password) || '');
  const database = String((payload && payload.database) || 'YHDB');
  if (!DB_ALLOWED_DATABASES.has(database)) {
    return { success: false, error: `不允许的数据库名: ${database}` };
  }

  let connection = null;
  try {
    connection = await mysql.createConnection({
      host,
      port,
      user,
      password,
      database,
      connectTimeout: 5000,
      multipleStatements: false,
    });
    await connection.query('SELECT 1');
    return {
      success: true,
      message: `数据库连接成功：${user}@${host}:${port}/${database}`,
    };
  } catch (err) {
    const code = err && err.code;
    if (code === 'ER_ACCESS_DENIED_ERROR' || code === 'ER_DBACCESS_DENIED_ERROR') {
      return { success: false, error: '数据库认证失败：用户名或密码错误，或账号没有数据库权限' };
    }
    if (code === 'ER_BAD_DB_ERROR') {
      return { success: false, error: `数据库不存在：${database}` };
    }
    if (code === 'ETIMEDOUT' || code === 'ECONNREFUSED' || code === 'ENOTFOUND') {
      return { success: false, error: `无法连接数据库服务器 ${host}:${port}（${code}）` };
    }
    return { success: false, error: `数据库连接失败（${code || 'UNKNOWN'}）` };
  } finally {
    if (connection) {
      try { await connection.end(); } catch (_) {}
    }
  }
});

// Direct MySQL Execute SQL Handler (INSERT-only, private hosts, YHDB)
ipcMain.handle('db:execute-sql', async (_event, payload) => {
  let host;
  try {
    host = assertDbHostAllowed((payload && payload.host) || '127.0.0.1');
  } catch (e) {
    return { success: false, error: e.message, logs: `❌ ${e.message}` };
  }
  const port = parseInt((payload && payload.port) || '3306', 10);
  if (!Number.isFinite(port) || port < 1 || port > 65535) {
    return { success: false, error: '无效的数据库端口', logs: '❌ 无效的数据库端口' };
  }
  const user = String((payload && payload.user) || 'root').slice(0, 64);
  const password = (payload && payload.password) || '';
  const database = String((payload && payload.database) || 'YHDB');
  if (!DB_ALLOWED_DATABASES.has(database)) {
    return {
      success: false,
      error: `不允许的数据库名: ${database}（仅支持: ${[...DB_ALLOWED_DATABASES].join(', ')}）`,
      logs: `❌ 不允许的数据库名: ${database}`,
    };
  }
  const sqlStatements = (payload && payload.sqlStatements) || [];
  if (!Array.isArray(sqlStatements)) {
    return { success: false, error: 'sqlStatements 必须是数组', logs: '❌ sqlStatements 必须是数组' };
  }
  if (sqlStatements.length > DB_MAX_STATEMENTS) {
    return {
      success: false,
      error: `语句数量超过上限 (${DB_MAX_STATEMENTS})`,
      logs: `❌ 语句数量超过上限 (${DB_MAX_STATEMENTS})`,
    };
  }

  const logs = [];
  let successCount = 0;
  let skippedCount = 0;
  let errorCount = 0;

  let connection = null;
  try {
    connection = await mysql.createConnection({
      host,
      port,
      user,
      password,
      database,
      connectTimeout: 5000,
      // Defense in depth: never allow multiStatements at the driver level
      multipleStatements: false,
    });

    logs.push(`[${new Date().toLocaleTimeString()}] 已连接数据库 ${user}@${host}:${port}/${database}`);

    for (let i = 0; i < sqlStatements.length; i++) {
      let sql;
      try {
        sql = assertSafeInsertSql(sqlStatements[i]);
      } catch (err) {
        errorCount++;
        logs.push(`❌ [${i + 1}/${sqlStatements.length}] 拒绝执行: ${err.message}`);
        continue;
      }
      if (!sql) continue;

      try {
        const [result] = await connection.query(sql);
        const affected = result ? (result.affectedRows || 0) : 0;
        const warning = result ? (result.warningStatus || 0) : 0;

        if (affected > 0) {
          successCount++;
          logs.push(`✅ [${i + 1}/${sqlStatements.length}] 成功写入 ${affected} 行`);
        } else if (warning > 0 || affected === 0) {
          skippedCount++;
          logs.push(`⚠️ [${i + 1}/${sqlStatements.length}] 已存在(重复)被自动跳过`);
        }
      } catch (err) {
        errorCount++;
        logs.push(`❌ [${i + 1}/${sqlStatements.length}] 跳过异常行: ${err.message}`);
      }
    }

    logs.push(`\n===================================`);
    logs.push(`🎉 数据插入完成统计：`);
    logs.push(`- 成功写入库中: ${successCount} 条`);
    logs.push(`- 撞重忽略跳过: ${skippedCount} 条`);
    logs.push(`- 异常报错跳过: ${errorCount} 条`);
    logs.push(`===================================`);

    return {
      success: true,
      successCount,
      skippedCount,
      errorCount,
      logs: logs.join('\n'),
    };
  } catch (err) {
    return {
      success: false,
      error: `无法建立 MySQL 数据库连接 (${err.message})`,
      logs: `❌ 无法连接数据库 ${user}@${host}:${port}/${database}\n原因: ${err.message}`,
    };
  } finally {
    if (connection) {
      try { await connection.end(); } catch (_) {}
    }
  }
});

// ---- App lifecycle ----
process.on('uncaughtException', (err) => { debugLog('uncaughtException: ' + (err && err.stack || err)); });
process.on('unhandledRejection', (reason) => { debugLog('unhandledRejection: ' + reason); });
app.whenReady().then(() => { debugLog('app ready'); createWindow(); initUpdater(); });
app.on('window-all-closed', () => {
  debugLog('window-all-closed');
  stopCurrentRun();
  if (updateDownloadInProgress) {
    debugLog('download in progress, keeping app alive');
    return;
  }
  if (process.platform !== 'darwin') app.quit();
});
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
