import type { RuntimeSetupStatus } from './types'

const spinnerEl = document.getElementById('spinner') as HTMLDivElement
const titleEl = document.getElementById('title') as HTMLHeadingElement
const subtitleEl = document.getElementById('subtitle') as HTMLDivElement
const fillEl = document.getElementById('fill') as HTMLDivElement
const phaseEl = document.getElementById('phase') as HTMLSpanElement
const bytesEl = document.getElementById('bytes') as HTMLSpanElement
const errorEl = document.getElementById('error') as HTMLDivElement
const actionsEl = document.getElementById('actions') as HTMLDivElement
const retryBtn = document.getElementById('retryBtn') as HTMLButtonElement
const recoveryBtn = document.getElementById('recoveryBtn') as HTMLButtonElement

const PHASE_TEXT: Record<string, string> = {
  starting: '正在准备…',
  downloading: '正在下载…',
  'retry-source': '下载源不可用，正在切换…',
  verifying: '正在校验文件完整性…',
  extracting: '正在解压…',
  'health-check': '正在检测运行环境…',
  installing: '正在安装…',
  done: '完成',
  error: '安装失败',
}

function fmtBytes(n?: number): string {
  if (typeof n !== 'number' || !Number.isFinite(n)) return '0 B'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`
  return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function updateUI(s: RuntimeSetupStatus) {
  if (s.title) titleEl.textContent = s.title
  if (s.label) subtitleEl.textContent = `正在安装${s.label}，请保持网络畅通，整个过程可能需要几分钟。`

  phaseEl.textContent = PHASE_TEXT[s.phase] || s.phase

  const isDownloading = s.phase === 'downloading'
  const hasTotal = isDownloading && typeof s.total === 'number' && s.total > 0
  const isError = s.phase === 'error'

  fillEl.classList.toggle('indeterminate', !hasTotal)
  if (hasTotal) {
    const pct = Math.min(100, Math.round(((s.downloaded || 0) / (s.total || 1)) * 100))
    fillEl.style.width = `${pct}%`
  }

  if (isDownloading) {
    bytesEl.textContent = hasTotal
      ? `${fmtBytes(s.downloaded)} / ${fmtBytes(s.total)}`
      : fmtBytes(s.downloaded)
  } else {
    bytesEl.textContent = ''
  }

  spinnerEl.classList.toggle('hidden', isError)
  errorEl.classList.toggle('visible', isError)
  if (isError) {
    errorEl.textContent = s.error || '未知错误'
  }
  actionsEl.classList.toggle('hidden', !isError)
}

if (window.runtimeSetup) {
  window.runtimeSetup.onStatus(updateUI)
  window.runtimeSetup.getState().then((s) => {
    if (s) updateUI(s)
  })
}

if (retryBtn) {
  retryBtn.addEventListener('click', () => {
    retryBtn.disabled = true
    errorEl.classList.remove('visible')
    actionsEl.classList.add('hidden')
    fillEl.classList.add('indeterminate')
    phaseEl.textContent = '正在重试…'
    if (window.runtimeSetup) window.runtimeSetup.retry().then(() => { retryBtn.disabled = false })
  })
}

if (recoveryBtn) {
  recoveryBtn.addEventListener('click', () => {
    if (window.runtimeSetup) window.runtimeSetup.openRecoveryDoc()
  })
}
