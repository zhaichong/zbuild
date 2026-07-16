<template>
  <div class="bg-surface rounded-lg shadow-sm p-4">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold text-gray-800">执行日志</h2>
      <div class="flex items-center gap-2">
        <select
          v-model="levelFilter"
          class="px-2 py-1 border border-gray-300 rounded text-xs"
        >
          <option value="">全部级别</option>
          <option value="info">信息</option>
          <option value="success">成功</option>
          <option value="warning">警告</option>
          <option value="error">错误</option>
        </select>
        <button
          class="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
          @click="store.clearLogs()"
        >
          清空日志
        </button>
      </div>
    </div>

    <div ref="logContainer" class="terminal rounded-lg p-3 h-64 overflow-y-auto">
      <div
        v-for="(log, i) in filteredLogs"
        :key="i"
        class="log-line"
        :class="log.level"
      >
        <span class="text-gray-500 mr-2">{{ formatTime(log.timestamp) }}</span>
        <span v-if="log.project" class="text-blue-400 mr-2">[{{ log.project }}]</span>
        <span>{{ log.message }}</span>
      </div>
      <div v-if="filteredLogs.length === 0" class="text-gray-500 text-center py-8">
        暂无日志
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, ref, nextTick } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useLog } from '@/composables/useLog'

const store = useAppStore()
const { filteredLogs, levelFilter } = useLog()
const logContainer = ref<HTMLElement>()

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('zh-CN', { hour12: false })
  } catch {
    return ts
  }
}

watch(() => store.logs.length, async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
})
</script>
