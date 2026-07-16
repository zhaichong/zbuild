<template>
  <div class="flex items-center justify-between bg-surface rounded-lg shadow-sm p-4">
    <div class="flex items-center gap-4">
      <h1 class="text-xl font-bold text-gray-800">特殊订单打包上传工具</h1>
      <span
        class="px-3 py-1 rounded-full text-xs font-medium"
        :class="modeBadgeClass"
      >
        {{ modeLabel }}
      </span>
    </div>
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2 text-sm text-gray-500">
        <span v-for="(status, name) in toolStatuses" :key="name" class="flex items-center gap-1">
          <span
            class="w-2 h-2 rounded-full"
            :class="status.ok ? 'bg-green-500' : 'bg-red-500'"
          ></span>
          <span>{{ name }}</span>
        </span>
      </div>
      <button
        class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        @click="showSettings = true"
        title="系统设置"
      >
        <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
const showSettings = ref(false)

const modeLabel = computed(() => {
  switch (store.mode) {
    case 'svn': return 'SVN上传'
    case 'server': return '服务器上传'
    case 'local': return '本地输出'
    default: return '未知'
  }
})

const modeBadgeClass = computed(() => {
  switch (store.mode) {
    case 'svn': return 'bg-blue-100 text-blue-800'
    case 'server': return 'bg-purple-100 text-purple-800'
    case 'local': return 'bg-gray-100 text-gray-800'
    default: return 'bg-gray-100 text-gray-800'
  }
})

const toolStatuses = computed(() => {
  if (!store.config) return {}
  return {
    git: { ok: !!store.config.tools.git, message: store.config.tools.git || '未配置' },
    bash: { ok: !!store.config.tools.bash, message: store.config.tools.bash || '未配置' },
    svn: { ok: !!store.config.tools.svn, message: store.config.tools.svn || '未配置' },
  }
})
</script>
