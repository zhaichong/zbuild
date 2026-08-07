import type { MiniStatus } from './types'

const petCardEl = document.getElementById('petCard') as HTMLDivElement
const pixelPetEl = document.getElementById('pixelPet') as HTMLDivElement
const mascotBoxEl = document.getElementById('mascotBox') as HTMLDivElement
const projectBadgeEl = document.getElementById('projectBadge') as HTMLSpanElement
const statusLabelEl = document.getElementById('statusLabel') as HTMLSpanElement
const stepTitleEl = document.getElementById('stepTitle') as HTMLDivElement
const logPreviewEl = document.getElementById('logPreview') as HTMLDivElement
const progressBarEl = document.getElementById('progressBar') as HTMLDivElement
const progressTextEl = document.getElementById('progressText') as HTMLSpanElement
const successPillEl = document.getElementById('successPill') as HTMLSpanElement
const failPillEl = document.getElementById('failPill') as HTMLSpanElement
const dismissBtn = document.getElementById('dismissBtn') as HTMLButtonElement
const openMainBtn = document.getElementById('openMainBtn') as HTMLButtonElement
const openMainLink = document.getElementById('openMainLink') as HTMLSpanElement

let currentPetState: string = 'idle'
let isWaveInteracting = false

function updateUI(status: MiniStatus) {
  if (!petCardEl) return

  currentPetState = status.state || 'idle'

  // Update root state class
  petCardEl.className = `pet-card ${status.state}`

  // Update pet sprite animation state
  if (pixelPetEl && !isWaveInteracting) {
    pixelPetEl.className = `pixel-pet state-${status.state || 'idle'}`
  }

  // 1. Project Badge & Status Pill
  if (status.currentProject) {
    projectBadgeEl.textContent = status.currentProject
    projectBadgeEl.style.display = 'inline-block'
  } else if (status.state === 'running') {
    projectBadgeEl.textContent = '打包进行中'
    projectBadgeEl.style.display = 'inline-block'
  } else if (status.state === 'complete') {
    projectBadgeEl.textContent = '构建完成'
    projectBadgeEl.style.display = 'inline-block'
  } else if (status.state === 'error') {
    projectBadgeEl.textContent = '构建异常'
    projectBadgeEl.style.display = 'inline-block'
  } else {
    projectBadgeEl.textContent = '待命中'
    projectBadgeEl.style.display = 'inline-block'
  }

  // 2. Status Label & Step Title
  if (status.state === 'running') {
    statusLabelEl.textContent = '打包进行中'
    stepTitleEl.textContent = status.currentStep || status.message || '正在执行流水线...'
  } else if (status.state === 'complete') {
    statusLabelEl.textContent = '打包完成'
    stepTitleEl.textContent = '🎉 所有项目已构建成功！'
  } else if (status.state === 'error') {
    statusLabelEl.textContent = '打包异常'
    stepTitleEl.textContent = status.currentStep || status.message || '部分项目构建遇到问题'
  } else {
    statusLabelEl.textContent = '桌宠待命'
    stepTitleEl.textContent = status.message || '等待任务开始...'
  }

  // 3. Log Preview
  if (status.latestLog) {
    logPreviewEl.textContent = status.latestLog
    logPreviewEl.style.display = 'block'
  } else if (status.message && status.message !== stepTitleEl.textContent) {
    logPreviewEl.textContent = status.message
    logPreviewEl.style.display = 'block'
  } else {
    logPreviewEl.textContent = status.state === 'running' ? '正在执行任务阶段...' : '双击可快速呼出主控制台'
  }

  // 4. Progress bar & Progress count
  const total = status.total || 0
  const completed = status.completed || 0
  let percent = 0
  if (status.state === 'complete') {
    percent = 100
  } else if (total > 0) {
    percent = Math.min(100, Math.round((completed / total) * 100))
  } else if (status.state === 'running') {
    percent = 15
  }

  progressBarEl.style.width = `${percent}%`
  progressTextEl.textContent = total > 0 ? `${completed} / ${total} (${percent}%)` : (status.state === 'running' ? '准备中...' : '0 / 0')

  // 5. Success and Failure count pills
  if (status.successCount > 0) {
    successPillEl.textContent = `✓ ${status.successCount}`
    successPillEl.style.display = 'inline-flex'
  } else {
    successPillEl.style.display = 'none'
  }

  if (status.failureCount > 0) {
    failPillEl.textContent = `✗ ${status.failureCount}`
    failPillEl.style.display = 'inline-flex'
  } else {
    failPillEl.style.display = 'none'
  }
}

if (window.mini) {
  window.mini.onStatus(updateUI)
}

function triggerOpenMain() {
  if (window.mini) {
    window.mini.openMain()
  }
}

// Click mascot avatar for wave animation
if (mascotBoxEl) {
  mascotBoxEl.addEventListener('click', (e) => {
    e.stopPropagation()
    if (!pixelPetEl || isWaveInteracting) return
    isWaveInteracting = true
    const prevClass = pixelPetEl.className
    pixelPetEl.className = 'pixel-pet state-wave'
    setTimeout(() => {
      isWaveInteracting = false
      pixelPetEl.className = prevClass
    }, 2000)
  })
}

if (dismissBtn) {
  dismissBtn.addEventListener('click', (e) => {
    e.stopPropagation()
    if (window.mini) {
      window.mini.dismiss()
    }
  })
}

if (openMainBtn) {
  openMainBtn.addEventListener('click', (e) => {
    e.stopPropagation()
    triggerOpenMain()
  })
}

if (openMainLink) {
  openMainLink.addEventListener('click', (e) => {
    e.stopPropagation()
    triggerOpenMain()
  })
}

document.addEventListener('dblclick', () => {
  triggerOpenMain()
})
