<template>
  <div class="relative flex items-start gap-3 group">
    <!-- Connecting Line (Vertical) -->
    <div
      v-if="!isLast"
      class="absolute left-[13px] top-[26px] bottom-[-8px] w-[2px] transition-colors duration-300"
      :class="lineClass"
    />

    <!-- Step Icon / Indicator -->
    <div
      class="relative z-10 flex items-center justify-center w-7 h-7 rounded-full flex-shrink-0 transition-all duration-300"
      :class="nodeClass"
    >
      <!-- Done: Crisp Emerald Checkmark -->
      <svg
        v-if="status === 'done'"
        class="w-3.5 h-3.5 text-emerald-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M5 13l4 4L19 7"
        />
      </svg>

      <!-- Running: Animated Spinner with glow ring -->
      <div
        v-else-if="status === 'running'"
        class="relative flex items-center justify-center w-full h-full"
      >
        <div class="absolute inset-0 rounded-full running-ring bg-blue-400 opacity-30" />
        <svg
          class="w-3.5 h-3.5 text-blue-600 animate-spin"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="3"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>

      <!-- Failed: Coral Red Cross -->
      <svg
        v-else-if="status === 'failed'"
        class="w-3.5 h-3.5 text-red-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>

      <!-- Skipped: Amber Dash -->
      <svg
        v-else-if="status === 'skipped'"
        class="w-3.5 h-3.5 text-amber-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M5 12h14"
        />
      </svg>

      <!-- Retrying: Amber Spinner -->
      <svg
        v-else-if="status === 'retrying'"
        class="w-3.5 h-3.5 text-orange-500 animate-spin"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2.5"
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>

      <!-- Pending: Clean Index Number -->
      <span
        v-else
        class="text-[11px] font-semibold text-slate-400"
      >{{ index + 1 }}</span>
    </div>

    <!-- Step Details -->
    <div
      class="flex-1 pt-0.5 min-w-0 transition-all duration-200"
      :class="[
        isLast ? 'pb-1' : 'pb-2.5',
        { 'opacity-50': status === 'pending' && !active }
      ]"
    >
      <div class="flex items-center justify-between gap-2">
        <span
          class="text-xs font-medium truncate leading-tight"
          :class="titleClass"
        >
          {{ label }}
        </span>
        <span
          v-if="statusText"
          class="text-[10.5px] px-1.5 py-0.5 rounded font-medium flex-shrink-0"
          :class="statusBadgeClass"
        >
          {{ statusText }}
        </span>
      </div>

      <!-- Optional Error or Step Message -->
      <div
        v-if="message"
        class="mt-1.5 text-[11px] p-2 rounded-md leading-relaxed break-all flex items-start gap-1.5"
        :class="status === 'failed' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-50 text-slate-600'"
      >
        <svg
          v-if="status === 'failed'"
          class="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <span>{{ message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StepStatusType } from '@/types'

const props = withDefaults(
  defineProps<{
    label: string
    index: number
    status: StepStatusType
    active?: boolean
    message?: string
    isLast?: boolean
  }>(),
  {
    active: false,
    message: '',
    isLast: false,
  }
)

const nodeClass = computed(() => {
  switch (props.status) {
    case 'done':
      return 'bg-emerald-50 text-emerald-600 border border-emerald-300 shadow-sm'
    case 'running':
      return 'bg-blue-50 text-blue-600 border border-blue-400 shadow-sm ring-2 ring-blue-100'
    case 'failed':
      return 'bg-red-50 text-red-600 border border-red-300 shadow-sm'
    case 'skipped':
      return 'bg-amber-50 text-amber-600 border border-amber-200'
    case 'retrying':
      return 'bg-orange-50 text-orange-600 border border-orange-300 shadow-sm'
    default:
      return props.active
        ? 'bg-blue-50 text-blue-500 border border-blue-200'
        : 'bg-slate-50 text-slate-400 border border-slate-200'
  }
})

const lineClass = computed(() => {
  if (props.status === 'done') {
    return 'bg-emerald-300'
  } else if (props.status === 'running') {
    return 'bg-gradient-to-b from-blue-400 to-slate-200'
  } else if (props.status === 'failed') {
    return 'bg-red-300'
  }
  return 'bg-slate-200'
})

const titleClass = computed(() => {
  switch (props.status) {
    case 'done':
      return 'text-slate-700 font-semibold'
    case 'running':
      return 'text-blue-700 font-bold'
    case 'failed':
      return 'text-red-700 font-semibold'
    case 'skipped':
      return 'text-slate-400 line-through'
    case 'retrying':
      return 'text-orange-600 font-semibold'
    default:
      return props.active ? 'text-blue-600 font-medium' : 'text-slate-600'
  }
})

const statusText = computed(() => {
  switch (props.status) {
    case 'done':
      return '已完成'
    case 'running':
      return '处理中...'
    case 'failed':
      return '失败'
    case 'skipped':
      return '已跳过'
    case 'retrying':
      return '重试中'
    default:
      return ''
  }
})

const statusBadgeClass = computed(() => {
  switch (props.status) {
    case 'done':
      return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
    case 'running':
      return 'bg-blue-50 text-blue-700 border border-blue-200 animate-pulse'
    case 'failed':
      return 'bg-red-50 text-red-700 border border-red-200'
    case 'skipped':
      return 'bg-slate-100 text-slate-500'
    case 'retrying':
      return 'bg-orange-50 text-orange-700 border border-orange-200'
    default:
      return ''
  }
})
</script>
