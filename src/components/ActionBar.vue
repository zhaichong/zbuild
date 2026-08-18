<template>
  <div class="card flex items-center justify-between px-5 py-3 bg-white border border-slate-200/90 shadow-2xs">
    <!-- Stat Counters with clean visual dividers -->
    <div class="flex items-center gap-6">
      <div class="flex items-baseline gap-2">
        <span class="text-2xl font-black text-slate-900 font-mono tracking-tight">{{ store.projects.length }}</span>
        <span class="text-xs font-semibold text-slate-500">总项目</span>
      </div>
      <div class="h-6 w-px bg-slate-200" />
      <div class="flex items-baseline gap-2">
        <span class="text-2xl font-black text-blue-600 font-mono tracking-tight">{{ store.selectedCount }}</span>
        <span class="text-xs font-semibold text-slate-500">已选择</span>
      </div>
      <div class="h-6 w-px bg-slate-200" />
      <div class="flex items-baseline gap-2">
        <span class="text-2xl font-black text-emerald-600 font-mono tracking-tight">{{ store.successCount }}</span>
        <span class="text-xs font-semibold text-slate-500">成功</span>
      </div>
      <div class="h-6 w-px bg-slate-200" />
      <div class="flex items-baseline gap-2">
        <span class="text-2xl font-black text-rose-600 font-mono tracking-tight">{{ store.failureCount }}</span>
        <span class="text-xs font-semibold text-slate-500">失败</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2.5">
      <button
        v-if="!store.running && store.failureCount > 0"
        class="run-btn retry cursor-pointer"
        @click="emit('retry')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>重试失败项目</span>
      </button>
      <button
        v-if="!store.running"
        class="run-btn cursor-pointer"
        :disabled="store.selectedCount === 0"
        @click="emit('start')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>开始执行</span>
      </button>
      <button
        v-else
        class="run-btn stop cursor-pointer"
        @click="emit('stop')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
        </svg>
        <span>停止执行</span>
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
