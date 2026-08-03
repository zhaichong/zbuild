<template>
  <header class="app-header">
    <div class="flex items-center gap-3">
      <!-- App Hub Launcher Button -->
      <button
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer select-none"
        :style="activeApp === 'portal' ? 'background: #fff; color: #1e40af; shadow: 0 1px 2px rgba(0,0,0,0.1)' : 'background: rgba(255,255,255,0.15); color: #fff;'"
        title="打开应用中心大厅"
        @click="emit('switch-app', activeApp === 'portal' ? 'zbuild' : 'portal')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
        <span>应用大厅</span>
      </button>

      <span class="text-white/30 text-xs">/</span>

      <h1 class="text-sm font-semibold tracking-wide flex items-center gap-2">
        <span v-if="activeApp === 'mock-query'">终端数据链路提取控制台</span>
        <span v-else-if="activeApp === 'portal'">开发者应用中心 & 工具矩阵</span>
        <span v-else>特殊订单打包上传</span>
      </h1>

      <div v-if="activeApp === 'zbuild'" class="mode-switch">
        <button
          v-for="m in modes"
          :key="m.value"
          class="mode-btn"
          :class="{ active: store.mode === m.value }"
          @click="emit('set-mode', m.value)"
        >
          {{ m.label }}
        </button>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <!-- Tool status indicators (only in zbuild mode) -->
      <div
        v-if="activeApp === 'zbuild'"
        class="flex items-center gap-3 text-xs"
        style="color: rgba(255,255,255,.7)"
      >
        <span
          v-for="(status, name) in toolStatuses"
          :key="name"
          class="flex items-center gap-1.5"
        >
          <span
            class="w-[7px] h-[7px] rounded-full"
            :class="status && status.ok ? 'bg-green-400' : 'bg-red-400'"
          />
          {{ name }}
        </span>
      </div>

      <!-- Auto-detect tools button (only in zbuild mode) -->
      <button
        v-if="activeApp === 'zbuild'"
        class="h-[34px] px-3 rounded-lg flex items-center gap-1.5 transition-colors text-xs font-medium"
        style="background: rgba(255,255,255,.12); color: #fff; border: none; cursor: pointer;"
        :disabled="detecting"
        :title="detecting ? '检测中...' : '自动检测工具路径'"
        @click="onDetectTools"
      >
        <svg
          v-if="!detecting"
          class="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <svg
          v-else
          class="w-4 h-4 animate-spin"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        {{ detecting ? '检测中' : '检测工具' }}
      </button>

      <!-- Server test button (only in server mode) -->
      <button
        v-if="activeApp === 'zbuild' && store.mode === 'server'"
        class="h-[34px] px-3 rounded-lg flex items-center gap-1.5 transition-colors text-xs font-medium"
        :style="serverTestStyle"
        :disabled="testingServer"
        title="测试服务器连接"
        @click="onTestServer"
      >
        <svg
          v-if="!testingServer"
          class="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2"
          />
        </svg>
        <svg
          v-else
          class="w-4 h-4 animate-spin"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        {{ testingServer ? '测试中' : '测试连接' }}
      </button>

      <!-- Settings button -->
      <button
        class="w-[34px] h-[34px] rounded-lg flex items-center justify-center transition-colors"
        style="background: rgba(255,255,255,.12); color: #fff; border: none; cursor: pointer;"
        title="设置"
        @click="emit('open-settings')"
      >
        <svg
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.8"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <circle
            cx="12"
            cy="12"
            r="3"
          />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, toRaw } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { UploadMode } from '@/types'

withDefaults(defineProps<{
  activeApp?: string
}>(), {
  activeApp: 'zbuild',
})

const store = useAppStore()
const emit = defineEmits<{
  'open-settings': []
  'set-mode': [mode: UploadMode]
  'switch-app': [appId: string]
}>()

const detecting = ref(false)
const testingServer = ref(false)

const modes = [
  { value: 'svn' as UploadMode, label: 'SVN 上传' },
  { value: 'server' as UploadMode, label: '服务器上传' },
  { value: 'local' as UploadMode, label: '本地输出' },
]

const toolStatuses = computed(() => {
  if (!store.config) return {} as Record<string, { ok: boolean }>
  return {
    Git: { ok: !!store.config.tools.git },
    Bash: { ok: !!store.config.tools.bash },
    ...(store.mode === 'svn' ? { SVN: { ok: !!store.config.tools.svn } } : {}),
  }
})

const serverTestStyle = computed(() => {
  return {
    background: 'rgba(255,255,255,.12)',
    color: '#fff',
    border: 'none',
    cursor: 'pointer',
  }
})

async function onDetectTools() {
  if (!store.config || detecting.value) return
  detecting.value = true
  try {
    const detection = await ipc.detectTools(JSON.parse(JSON.stringify(toRaw(store.config))))
    if (detection.tools) {
      const d = detection.tools as unknown as Record<string, { path?: string; version?: string } | string>
      const getPath = (key: string) => {
        const v = d[key]
        return typeof v === 'string' ? v : (v && typeof v === 'object' && 'path' in v ? v.path || '' : '')
      }
      const git = getPath('git')
      const bash = getPath('bash')
      const svn = getPath('svn')
      if (git) store.config.tools.git = git
      if (bash) store.config.tools.bash = bash
      if (svn && !store.config.tools.svn) store.config.tools.svn = svn
    }
  } catch (e) {
    console.warn('Auto-detect tools failed:', e)
  } finally {
    detecting.value = false
  }
}

async function onTestServer() {
  if (!store.config || testingServer.value) return
  const form = store.config.form
  if (!form.serverAddress || !form.serverUsername) {
    store.showToast('请先在设置中配置服务器地址和用户名', 'warning')
    return
  }
  testingServer.value = true
  try {
    const result = await ipc.testServer(form.serverAddress, form.serverUsername, form.serverPassword)
    if (result.success) {
      store.showToast('服务器连接成功: ' + (result.message || 'OK'), 'success')
    } else {
      store.showToast('服务器连接失败: ' + (result.error || result.message || '未知错误'), 'error')
    }
  } catch (e: unknown) {
    store.showToast('服务器连接测试失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  } finally {
    testingServer.value = false
  }
}
</script>
