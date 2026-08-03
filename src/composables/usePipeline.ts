import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { RunEvent } from '@/types'

export async function startRun(payload: Record<string, unknown>): Promise<boolean> {
  const store = useAppStore()
  store.resetRunState()
  store.running = true

  try {
    return await ipc.startRun(payload)
  } catch (err: unknown) {
    store.running = false
    const errMsg = err instanceof Error ? err.message : String(err)
    store.addLog({
      message: '启动失败: ' + errMsg,
      level: 'error',
      timestamp: new Date().toISOString(),
    })
    throw err
  }
}

export async function stopRun(): Promise<boolean> {
  const store = useAppStore()
  const result = await ipc.stopRun()
  store.running = false
  return result
}

export function handleEvent(event: RunEvent) {
  const store = useAppStore()

  switch (event.type) {
    case 'log':
      store.addLog({
        message: event.message,
        level: event.level,
        timestamp: new Date().toISOString(),
        project: event.project,
      })
      break

    case 'step-start': {
      const stepName = event.step || ''
      const projName = event.project
      if (projName && store.projectStates[projName]) {
        store.setStepState(projName, stepName, 'running', '')
        store.setProjectState(projName, { currentStep: stepName })
      } else {
        for (const [name, state] of Object.entries(store.projectStates)) {
          if (state.status === 'running') {
            store.setStepState(name, stepName, 'running', '')
            store.setProjectState(name, { currentStep: stepName })
            break
          }
        }
      }
      break
    }

    case 'step-end': {
      const stepName = event.step || ''
      const success = event.success !== false
      const message = event.message || ''
      const projName = event.project
      if (projName && store.projectStates[projName]) {
        store.setStepState(projName, stepName, success ? 'done' : 'failed', message)
      } else {
        for (const [name, state] of Object.entries(store.projectStates)) {
          if (state.status === 'running') {
            store.setStepState(name, stepName, success ? 'done' : 'failed', message)
            break
          }
        }
      }
      break
    }

    case 'projectStart':
      store.setProjectState(event.project, {
        status: 'running',
        statusClass: 'text-blue-600',
        currentStep: '',
        steps: (event.steps || []).map((step: string) => ({
          step,
          status: 'pending'
        })),
      })
      store.showToast(`开始处理项目: ${event.project}`, 'info')
      break

    case 'projectResult':
      if (event.success) {
        store.setProjectState(event.project, {
          status: 'done',
          statusClass: 'text-green-600',
        })
        store.showToast(`项目 ${event.project} 处理成功！`, 'success')
      } else {
        store.setProjectState(event.project, {
          status: 'failed',
          statusClass: 'text-red-600',
        })
        store.showToast(`项目 ${event.project} 处理失败！`, 'error')
      }
      break

    case 'done': {
      store.running = false
      const failureCount = event.failureCount ?? 0
      const summary = `任务完成：成功 ${event.successCount ?? 0}，失败 ${failureCount}`
      store.addLog({
        message: summary,
        level: failureCount > 0 ? 'error' : 'success',
        timestamp: new Date().toISOString(),
      })
      store.showToast(summary, failureCount > 0 ? 'error' : 'success')
      break
    }

    case 'result':
      // Final result from pipeline emit_result -- run is complete
      store.running = false
      break

    case 'error':
      store.addLog({
        message: event.message,
        level: 'error',
        timestamp: new Date().toISOString(),
      })
      store.showToast(`执行发生异常: ${event.message}`, 'error')
      break
  }
}

let _cleanupEvent: (() => void) | null = null
let _cleanupExit: (() => void) | null = null

export function setupRunListeners() {
  // Clean up previous listeners to avoid duplicates on remount/HMR
  if (_cleanupEvent) { _cleanupEvent(); _cleanupEvent = null; }
  if (_cleanupExit) { _cleanupExit(); _cleanupExit = null; }

  _cleanupEvent = ipc.onRunEvent(handleEvent)
  _cleanupExit = ipc.onRunExit((event) => {
    const store = useAppStore()
    store.running = false
    if (event.code !== 0) {
      store.addLog({
        message: `\u8fdb\u7a0b\u9000\u51fa\uff0c\u4ee3\u7801: ${event.code}`,
        level: 'error',
        timestamp: new Date().toISOString(),
      })
    }
  })
}
