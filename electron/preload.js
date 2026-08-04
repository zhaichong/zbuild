const { contextBridge, ipcRenderer } = require('electron');

function parsePayload(payload) {
  if (typeof payload === 'string') {
    try {
      return JSON.parse(payload);
    } catch (_) {
      return payload;
    }
  }
  return payload;
}

contextBridge.exposeInMainWorld('tool', {
  // config
  getConfig: () => ipcRenderer.invoke('config:get'),
  saveConfig: (payload) => ipcRenderer.invoke('config:save', parsePayload(payload)),

  // tools
  detectTools: (payload) => ipcRenderer.invoke('tools:detect', parsePayload(payload)),

  // projects
  discoverProjects: (payload) => ipcRenderer.invoke('projects:discover', parsePayload(payload)),
  refreshProjectBranches: (payload) => ipcRenderer.invoke('projects:refresh-branches', parsePayload(payload)),
  checkLocalChanges: (payload) => ipcRenderer.invoke('projects:check-local-changes', parsePayload(payload)),
  detectAffected: (payload) => ipcRenderer.invoke('projects:detect-affected', parsePayload(payload)),
  detectAffectedStaged: (payload) => ipcRenderer.invoke('projects:detect-affected-staged', parsePayload(payload)),

  // SVN & server
  svnList: (payload) => ipcRenderer.invoke('svn:list', parsePayload(payload)),
  testServer: (payload) => ipcRenderer.invoke('server:test', parsePayload(payload)),

  // dialogs
  chooseDirectory: (currentPath) => ipcRenderer.invoke('dialog:directory', currentPath),
  chooseExecutable: (currentPath) => ipcRenderer.invoke('dialog:executable', currentPath),

  // order directory
  createOrderDir: (payload) => ipcRenderer.invoke('order-dir:create', parsePayload(payload)),

  // run lifecycle
  startRun: (payload) => ipcRenderer.invoke('run:start', parsePayload(payload)),
  stopRun: () => ipcRenderer.invoke('run:stop'),
  onRunEvent: (handler) => {
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on('run:event', listener);
    return () => ipcRenderer.removeListener('run:event', listener);
  },
  onRunExit: (handler) => {
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on('run:exit', listener);
    return () => ipcRenderer.removeListener('run:exit', listener);
  },

  // templates
  listTemplates: () => ipcRenderer.invoke('templates:list'),
  getTemplate: (id) => ipcRenderer.invoke('templates:get', id),
  saveTemplate: (template) => ipcRenderer.invoke('templates:save', parsePayload(template)),
  deleteTemplate: (id) => ipcRenderer.invoke('templates:delete', id),

  // history
  listHistory: () => ipcRenderer.invoke('history:list'),
  getHistory: (id) => ipcRenderer.invoke('history:get', id),

  // mock query request
  mockQueryRequest: (payload) => ipcRenderer.invoke('mock-query:request', parsePayload(payload)),

  // db test connection
  testDbConnection: (payload) => ipcRenderer.invoke('db:test-connection', parsePayload(payload)),

  // db execute sql
  executeDbSql: (payload) => ipcRenderer.invoke('db:execute-sql', parsePayload(payload)),
});

contextBridge.exposeInMainWorld('mini', {
  onStatus: (handler) => {
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on('mini:status', listener);
    return () => ipcRenderer.removeListener('mini:status', listener);
  },
  openMain: () => ipcRenderer.invoke('mini:open-main'),
  dismiss: () => ipcRenderer.invoke('mini:dismiss'),
});
