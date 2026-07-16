const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('tool', {
  // config
  getConfig: () => ipcRenderer.invoke('config:get'),
  saveConfig: (payload) => ipcRenderer.invoke('config:save', payload),

  // tools
  detectTools: (payload) => ipcRenderer.invoke('tools:detect', payload),

  // projects
  discoverProjects: (payload) => ipcRenderer.invoke('projects:discover', payload),
  refreshProjectBranches: (payload) => ipcRenderer.invoke('projects:refresh-branches', payload),
  checkLocalChanges: (payload) => ipcRenderer.invoke('projects:check-local-changes', payload),

  // SVN & server
  svnList: (payload) => ipcRenderer.invoke('svn:list', payload),
  testServer: (payload) => ipcRenderer.invoke('server:test', payload),

  // dialogs
  chooseDirectory: (currentPath) => ipcRenderer.invoke('dialog:directory', currentPath),
  chooseExecutable: (currentPath) => ipcRenderer.invoke('dialog:executable', currentPath),

  // run lifecycle
  startRun: (payload) => ipcRenderer.invoke('run:start', payload),
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
  saveTemplate: (template) => ipcRenderer.invoke('templates:save', template),
  deleteTemplate: (id) => ipcRenderer.invoke('templates:delete', id),

  // history
  listHistory: () => ipcRenderer.invoke('history:list'),
  getHistory: (id) => ipcRenderer.invoke('history:get', id),
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
