<template>
  <div class="card flex items-center justify-between px-5 py-3.5">
    <div class="flex gap-5">
      <div>
        <div class="text-[22px] font-bold text-text-1">
          {{ store.projects.length }}
        </div>
        <div class="text-xs text-text-3">
          总项目
        </div>
      </div>
      <div>
        <div class="text-[22px] font-bold text-primary">
          {{ store.selectedCount }}
        </div>
        <div class="text-xs text-text-3">
          已选择
        </div>
      </div>
      <div>
        <div class="text-[22px] font-bold text-success">
          {{ store.successCount }}
        </div>
        <div class="text-xs text-text-3">
          成功
        </div>
      </div>
      <div>
        <div class="text-[22px] font-bold text-error">
          {{ store.failureCount }}
        </div>
        <div class="text-xs text-text-3">
          失败
        </div>
      </div>
    </div>
    <div class="flex gap-2">
      <button
        v-if="!store.running && store.failureCount > 0"
        class="run-btn retry"
        @click="emit('retry')"
      >
        重试失败项目
      </button>
      <button
        v-if="!store.running"
        class="run-btn"
        :disabled="store.selectedCount === 0"
        @click="emit('start')"
      >
        开始执行
      </button>
      <button
        v-else
        class="run-btn stop"
        @click="emit('stop')"
      >
        停止执行
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
const emit = defineEmits<{
  start: []
  stop: []
  retry: []
}>()
</script>
