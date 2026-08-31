import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { AppConfig } from '@/types'

const LOCAL_OUTPUT_KEY = 'zbuild_local_output_dir'
const ORDER_DIR_KEY = 'zbuild_order_dir_path'

/**
 * 将本地客户端缓存的独立目录路径覆盖到配置对象中，防止远端服务器接口将其覆盖或还原
 */
export function applyClientCachedPaths(config: AppConfig): AppConfig {
  if (!config) return config
  try {
    const cachedLocalOutput = localStorage.getItem(LOCAL_OUTPUT_KEY)
    if (cachedLocalOutput !== null) {
      config.localOutputDir = cachedLocalOutput
    }
    const cachedOrderDir = localStorage.getItem(ORDER_DIR_KEY)
    if (cachedOrderDir !== null) {
      config.orderDirPath = cachedOrderDir
    }
  } catch (e) {
    console.warn('Failed to apply client cached paths:', e)
  }
  return config
}

/**
 * 将客户端本地目录路径独立保存到当前浏览器的客户端缓存 (localStorage)
 */
export function saveClientCachedPaths(config: Partial<AppConfig>): void {
  try {
    if (config.localOutputDir !== undefined) {
      localStorage.setItem(LOCAL_OUTPUT_KEY, config.localOutputDir || '')
    }
    if (config.orderDirPath !== undefined) {
      localStorage.setItem(ORDER_DIR_KEY, config.orderDirPath || '')
    }
  } catch (e) {
    console.warn('Failed to save client cached paths:', e)
  }
}

export async function saveConfig(config: AppConfig): Promise<AppConfig> {
  const store = useAppStore()

  // 1. 优先将客户端本地输出目录与提测单目录缓存到本地当前客户端
  saveClientCachedPaths(config)

  // 2. 调用保存接口同步其他项目配置与状态
  const saved = await ipc.saveConfig(config)

  // 3. 强制应用当前客户端缓存的本地路径，确保远端服务器返回的数据绝不会将其还原
  applyClientCachedPaths(saved)
  store.config = saved

  const svnUser = saved.form?.svnUsername?.trim()
  if (svnUser) {
    localStorage.setItem('zbuild_svn_username', svnUser)
  } else {
    localStorage.removeItem('zbuild_svn_username')
    localStorage.removeItem('zbuild.submitter')
  }

  return saved
}


