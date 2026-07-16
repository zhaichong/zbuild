<template>
  <div v-if="store.running || Object.keys(store.projectStates).length > 0" class="bg-surface rounded-lg shadow-sm p-4">
    <h2 class="text-lg font-semibold text-gray-800 mb-4">执行进度</h2>

    <div class="space-y-3">
      <div
        v-for="(state, name) in store.projectStates"
        :key="name"
        class="border border-gray-200 rounded-lg p-3"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="font-medium text-gray-800">{{ name }}</span>
          <span class="text-sm font-medium" :class="state.statusClass">
            {{ statusLabel(state.status) }}
          </span>
        </div>

        <div v-if="state.steps.length > 0" class="space-y-1">
          <div
            v-for="step in state.steps"
            :key="step.step"
            class="flex items-center gap-2 text-xs"
          >
            <span class="w-2 h-2 rounded-full" :class="stepDotClass(step.status)"></span>
            <span class="text-gray-600">{{ step.step }}</span>
            <span v-if="step.message" class="text-gray-400 ml-auto">{{ step.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/appStore'
import type { StepStatusType } from '@/types'

const store = useAppStore()

function statusLabel(status: StepStatusType): string {
  const labels: Record<StepStatusType, string> = {
    pending: '等待中',
    running: '执行中',
    done: '已完成',
    failed: '失败',
    skipped: '已跳过',
    retrying: '重试中',
  }
  return labels[status] || status
}

function stepDotClass(status: StepStatusType): string {
  switch (status) {
    case 'pending': return 'bg-gray-300'
    case 'running': return 'bg-blue-500 animate-pulse'
    case 'done': return 'bg-green-500'
    case 'failed': return 'bg-red-500'
    case 'skipped': return 'bg-yellow-500'
    case 'retrying': return 'bg-orange-500 animate-pulse'
    default: return 'bg-gray-300'
  }
}
</script>
