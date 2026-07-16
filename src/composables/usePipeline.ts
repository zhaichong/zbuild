import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { RunEvent } from '@/types'

export async function startRun(payload: Record<string, unknown>): Promise<boolean> {
  const store = useAppStore()
  store.running = true
  store.resetRunState()
  store.running = true

  return await ipc.startRun(payload)
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

    case 'step':
      if (event.project) {
        store.setStepState(event.project, event.step, event.status, event.message)
      }
      break

    case 'projectStart':
      store.setProjectState(event.project, {
        status: 'running',
        statusClass: 'text-blue-600',
        currentStep: '',
        steps: [],
      })
      break

    case 'projectResult':
      if (event.success) {
        store.setProjectState(event.project, {
          status: 'done',
          statusClass: 'text-green-600',
        })
      } else {
        store.setProjectState(event.project, {
          status: 'failed',
          statusClass: 'text-red-600',
        })
      }
      break

    case 'done':
      store.running = false
      store.addLog({
        message: '所有任务执行完成',
        level: 'success',
        timestamp: new Date().toISOString(),
      })
      break

    case 'error':
      store.addLog({
        message: event.message,
        level: 'error',
        timestamp: new Date().toISOString(),
      })
      break
  }
}

export function setupRunListeners() {
  ipc.onRunEvent(handleEvent)
  ipc.onRunExit((event) => {
    const store = useAppStore()
    store.running = false
    if (event.code !== 0) {
      store.addLog({
        message: `进程退出，代码: ${event.code}`,
        level: 'error',
        timestamp: new Date().toISOString(),
      })
    }
  })
}
