/**
 * Web File System Access API 服务
 * 允许现代浏览器（Chrome / Edge 等）在获得用户一次授权后，
 * 直接在用户客户端本地磁盘的指定目录中自动创建子文件夹并写入提测文件，
 * 无需经过浏览器的 Downloads 默认下载目录，实现类似桌面应用的直接落盘体验。
 */

const DB_NAME = 'zbuild_fs_db'
const STORE_NAME = 'handles'
const KEY_ORDER_DIR_HANDLE = 'order_dir_directory_handle'

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      return reject(new Error('IndexedDB 不可用'))
    }
    const request = indexedDB.open(DB_NAME, 1)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME)
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function getStoredHandle(): Promise<FileSystemDirectoryHandle | null> {
  try {
    const db = await openDatabase()
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const req = store.get(KEY_ORDER_DIR_HANDLE)
      req.onsuccess = () => resolve(req.result || null)
      req.onerror = () => resolve(null)
    })
  } catch {
    return null
  }
}

async function setStoredHandle(handle: FileSystemDirectoryHandle): Promise<void> {
  try {
    const db = await openDatabase()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const req = store.put(handle, KEY_ORDER_DIR_HANDLE)
      req.onsuccess = () => resolve()
      req.onerror = () => reject(req.error)
    })
  } catch (e) {
    console.warn('Failed to store directory handle in IndexedDB:', e)
  }
}

/**
 * 检查当前浏览器是否支持 File System Access API
 */
export function isFileSystemAccessSupported(): boolean {
  return typeof window !== 'undefined' && 'showDirectoryPicker' in window
}

/**
 * 校验并请求文件夹句柄的读写权限
 */
async function verifyPermission(
  fileHandle: FileSystemDirectoryHandle,
  readWrite = true,
): Promise<boolean> {
  const options: any = {}
  if (readWrite) {
    options.mode = 'readwrite'
  }
  if ((await (fileHandle as any).queryPermission(options)) === 'granted') {
    return true
  }
  if ((await (fileHandle as any).requestPermission(options)) === 'granted') {
    return true
  }
  return false
}

/**
 * 调起浏览器目录选择器，选择目标目录并持久化存储句柄
 */
export async function pickAndStoreLocalDirectory(): Promise<{
  handle: FileSystemDirectoryHandle
  name: string
} | null> {
  if (!isFileSystemAccessSupported()) {
    throw new Error('当前浏览器不支持 File System Access API，请使用 Chrome 或 Edge 浏览器')
  }
  try {
    const handle = await (window as any).showDirectoryPicker({
      mode: 'readwrite',
      startIn: 'documents',
    })
    await setStoredHandle(handle)
    return {
      handle,
      name: handle.name,
    }
  } catch (e: any) {
    if (e.name === 'AbortError') {
      return null
    }
    throw e
  }
}

/**
 * 获取已授权的目录句柄，如未授权则调起选择器
 */
export async function getOrPromptDirectoryHandle(): Promise<FileSystemDirectoryHandle | null> {
  let handle = await getStoredHandle()
  if (handle) {
    const hasPermission = await verifyPermission(handle, true).catch(() => false)
    if (hasPermission) {
      return handle
    }
  }
  const picked = await pickAndStoreLocalDirectory()
  return picked ? picked.handle : null
}

export interface FileDownloadSpec {
  filename: string
  downloadUrl: string
}

/**
 * 将服务端生成的文件直接写入到客户端本地目录中的指定子文件夹
 */
export async function writeFilesToLocalDirectory(
  folderName: string,
  files: FileDownloadSpec[],
): Promise<{ success: boolean; message: string; writtenCount: number }> {
  if (!isFileSystemAccessSupported()) {
    return {
      success: false,
      message: '浏览器不支持本地直写，已降级为标准下载通道',
      writtenCount: 0,
    }
  }

  try {
    const rootHandle = await getOrPromptDirectoryHandle()
    if (!rootHandle) {
      return {
        success: false,
        message: '用户取消了文件夹授权',
        writtenCount: 0,
      }
    }

    // 1. 在选定目录下创建订单同名子文件夹
    const subDirHandle = await rootHandle.getDirectoryHandle(folderName, { create: true })

    // 2. 依次拉取文件流并写入本地磁盘文件
    let writtenCount = 0
    for (const file of files) {
      if (!file.downloadUrl) continue
      try {
        const response = await fetch(file.downloadUrl)
        if (!response.ok) {
          console.warn(`Failed to fetch file for local write: ${file.filename}, status: ${response.status}`)
          continue
        }
        const blob = await response.blob()
        const fileHandle = await subDirHandle.getFileHandle(file.filename, { create: true })
        const writable = await (fileHandle as any).createWritable()
        await writable.write(blob)
        await writable.close()
        writtenCount++
      } catch (err) {
        console.warn(`Failed to write file ${file.filename} to local folder:`, err)
      }
    }

    return {
      success: writtenCount > 0,
      message: `已成功在客户端本地目录 [${rootHandle.name}\\${folderName}] 中直接生成并落盘 ${writtenCount} 个文件！`,
      writtenCount,
    }
  } catch (e: any) {
    return {
      success: false,
      message: e.message || '写入本地磁盘失败',
      writtenCount: 0,
    }
  }
}
