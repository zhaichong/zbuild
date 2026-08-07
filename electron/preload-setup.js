const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('runtimeSetup', {
  getState: () => ipcRenderer.invoke('runtime-setup:get-state'),
  retry: () => ipcRenderer.invoke('runtime-setup:retry'),
  openRecoveryDoc: () => ipcRenderer.invoke('runtime-setup:open-recovery'),
  onStatus: (handler) => {
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on('runtime-setup:status', listener);
    return () => ipcRenderer.removeListener('runtime-setup:status', listener);
  },
});
