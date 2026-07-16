import type { MiniStatus } from './types'

const titleEl = document.getElementById('title') as HTMLDivElement
const messageEl = document.getElementById('message') as HTMLDivElement
const progressBarEl = document.getElementById('progressBar') as HTMLDivElement
const progressTextEl = document.getElementById('progressText') as HTMLDivElement
const resultTextEl = document.getElementById('resultText') as HTMLDivElement
const countTextEl = document.getElementById('countText') as HTMLDivElement
const dismissBtn = document.getElementById('dismissBtn') as HTMLButtonElement

function updateUI(status: MiniStatus) {
  if (status.state === 'running') {
    titleEl.textContent = `正在处理: ${status.currentProject || '...'}`
    messageEl.textContent = status.message || '执行中...'
    const percent = status.total > 0 ? (status.completed / status.total) * 100 : 0
    progressBarEl.style.width = `${percent}%`
    progressTextEl.textContent = `${status.completed} / ${status.total}`
    resultTextEl.style.display = 'none'
    countTextEl.textContent = `成功: ${status.successCount} | 失败: ${status.failureCount}`
  } else if (status.state === 'success') {
    titleEl.textContent = '执行完成'
    messageEl.textContent = '所有任务已成功完成'
    progressBarEl.style.width = '100%'
    progressTextEl.textContent = `${status.total} / ${status.total}`
    resultTextEl.style.display = 'block'
    resultTextEl.className = 'result success'
    resultTextEl.textContent = `✓ 成功: ${status.successCount}`
    countTextEl.textContent = ''
  } else if (status.state === 'failed') {
    titleEl.textContent = '执行失败'
    messageEl.textContent = status.message || '部分任务失败'
    progressBarEl.style.width = '100%'
    progressTextEl.textContent = `${status.completed} / ${status.total}`
    resultTextEl.style.display = 'block'
    resultTextEl.className = 'result error'
    resultTextEl.textContent = `✗ 失败: ${status.failureCount}`
    countTextEl.textContent = `成功: ${status.successCount}`
  }
}

if (window.mini) {
  window.mini.onStatus(updateUI)
}

dismissBtn.addEventListener('click', () => {
  if (window.mini) {
    window.mini.dismiss()
  }
})

document.addEventListener('dblclick', () => {
  if (window.mini) {
    window.mini.openMain()
  }
})
