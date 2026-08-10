<template>
  <div
    v-if="visible && status.state !== 'not-available' && status.state !== 'idle'"
    class="fixed inset-0 z-50 flex items-center justify-center"
  >
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      @click="onBackdrop"
    />
    <div class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-md z-10 flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border-light">
        <h2 class="text-lg font-bold text-text-1 flex items-center gap-2">
          <svg
            class="w-5 h-5 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          <span v-if="status.state === 'downloading'">正在下载更新</span>
          <span v-else-if="status.state === 'downloaded'">更新已就绪</span>
          <span v-else-if="status.state === 'error'">更新出错了</span>
          <span v-else>发现新版本</span>
        </h2>
        <button
          v-if="status.state !== 'downloading'"
          class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
          @click="dismiss"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-4">
        <!-- available -->
        <template v-if="status.state === 'available'">
          <div class="rounded-xl bg-bg-base border border-border-light p-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs text-text-3">当前版本</span>
              <span class="text-sm font-bold text-text-1">{{ currentVersion }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-text-3">最新版本</span>
              <span class="text-sm font-bold text-primary">{{ status.version }}</span>
            </div>
          </div>
          <div
            v-if="releaseNotesText"
            class="text-xs text-text-2 leading-relaxed max-h-[30vh] overflow-y-auto whitespace-pre-wrap break-words"
          >
            {{ releaseNotesText }}
          </div>
          <div v-else class="text-xs text-text-2">
            有新版本可用，是否立即更新？
          </div>
        </template>

        <!-- downloading -->
        <template v-else-if="status.state === 'downloading'">
          <div class="rounded-xl bg-bg-base border border-border-light p-4 space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span class="text-text-3">下载中</span>
              <span class="font-bold text-text-1">{{ status.percent || 0 }}%</span>
            </div>
            <div class="h-2 rounded-full bg-border-light overflow-hidden">
              <div
                class="h-full bg-primary transition-all duration-300"
                :style="{ width: `${Math.min(status.percent || 0, 100)}%` }"
              />
            </div>
            <div v-if="downloadSpeedText" class="text-[10px] text-text-3 text-right">
              {{ downloadSpeedText }}
            </div>
          </div>
        </template>

        <!-- downloaded -->
        <template v-else-if="status.state === 'downloaded'">
          <div class="rounded-xl bg-bg-base border border-border-light p-4 text-center">
            <div class="text-3xl mb-2">✅</div>
            <div class="text-sm font-semibold text-text-1">下载完成，重启应用即可完成安装</div>
            <div v-if="status.version" class="text-xs text-text-3 mt-1">
              新版本：{{ status.version }}
            </div>
          </div>
        </template>

        <!-- error -->
        <template v-else-if="status.state === 'error'">
          <div class="rounded-xl bg-red-50 border border-red-200 p-4 text-xs text-red-700 leading-relaxed break-words">
            {{ errorMessageFormatted }}
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light">
        <template v-if="status.state === 'available'">
          <button
            class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="dismiss"
          >
            以后再说
          </button>
          <button
            class="px-6 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium flex items-center gap-1.5 shadow-md shadow-primary/20"
            @click="startDownload"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            ><path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            /></svg>
            立即更新
          </button>
        </template>
        <template v-else-if="status.state === 'downloaded'">
          <button
            class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="dismiss"
          >
            稍后
          </button>
          <button
            class="px-6 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium flex items-center gap-1.5 shadow-md shadow-primary/20"
            @click="install"
          >
            重启并安装
          </button>
        </template>
        <template v-else-if="status.state === 'downloading'">
          <button
            class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="dismiss"
          >
            后台下载
          </button>
        </template>
        <template v-else-if="status.state === 'error'">
          <button
            class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="dismiss"
          >
            取消
          </button>
          <button
            class="px-6 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium shadow-md shadow-primary/20"
            @click="retry"
          >
            重试
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ipc } from '@/services/ipc'
import type { UpdateStatus } from '@/types'

const visible = ref(false)
const status = ref<UpdateStatus>({ state: 'idle' })
let unsubscribe: (() => void) | null = null

const currentVersion = computed(() => {
  try {
    return `v${ipc.version}`
  } catch {
    return ''
  }
})

const releaseNotesText = computed(() => {
  const raw = status.value.releaseNotes || ''
  if (!raw) return ''
  const text = raw.replace(/<[^>]+>/g, '').trim()
  return text || ''
})

const downloadSpeedText = computed(() => {
  const bps = status.value.bytesPerSecond || 0
  if (!bps) return ''
  if (bps >= 1024 * 1024) return `${(bps / 1024 / 1024).toFixed(1)} MB/s`
  if (bps >= 1024) return `${Math.round(bps / 1024)} KB/s`
  return `${Math.round(bps)} B/s`
})

const errorMessageFormatted = computed(() => {
  const msg = status.value.message || ''
  if (msg.includes('ERR_NETWORK_CHANGED')) {
    return '网络连接已变更（如切换了网络/VPN），导致检查更新中断。请确认网络就绪后点击“重试”。'
  }
  if (msg.includes('ERR_INTERNET_DISCONNECTED')) {
    return '当前网络已断开，请检查网络连接后重试。'
  }
  if (msg.includes('ERR_CONNECTION_TIMED_OUT') || msg.includes('ETIMEDOUT')) {
    return '连接服务器超时，请检查网络或代理设置。'
  }
  if (msg.includes('ERR_NAME_NOT_RESOLVED')) {
    return '域名解析失败，请检查 DNS 或代理设置。'
  }
  return msg || '检查更新失败，请稍后重试'
})

function handleStatus(next: UpdateStatus) {
  status.value = next
  if (next.state === 'available' || next.state === 'downloaded' || next.state === 'error') {
    visible.value = true
  } else if (next.state === 'downloading') {
    visible.value = true
  }
}

function dismiss() {
  visible.value = false
  if (status.value.state === 'error') {
    status.value = { state: 'idle' }
  }
}

function onBackdrop() {
  if (status.value.state === 'downloading') return
  dismiss()
}

async function startDownload() {
  const next = await ipc.downloadUpdate()
  if (next.state === 'error') {
    status.value = next
  }
}

async function install() {
  await ipc.installUpdate()
}

function check() {
  return ipc.checkForUpdates()
}

async function retry() {
  status.value = { state: 'checking' }
  const res = await check()
  if (res && res.state === 'error') {
    status.value = res
  }
}

onMounted(() => {
  unsubscribe = ipc.onUpdateStatus(handleStatus)
})

onBeforeUnmount(() => {
  if (unsubscribe) unsubscribe()
})

defineExpose({ check, visible })
</script>
