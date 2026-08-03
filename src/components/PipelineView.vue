<template>
  <div
    v-if="hasProgress"
    class="flex-1 min-h-0 flex flex-col overflow-hidden bg-white"
  >
    <!-- Header -->
    <div class="px-4 py-2.5 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 rounded-md bg-blue-100/80 text-blue-600 flex items-center justify-center">
          <svg
            class="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
        <div>
          <h3 class="text-xs font-bold text-slate-800 tracking-tight">
            流水线执行进度
          </h3>
        </div>
      </div>

      <!-- Global Summary Badge -->
      <div class="flex items-center gap-2">
        <span
          class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
          :class="overallStatusBadgeClass"
        >
          {{ overallStatusText }}
        </span>
      </div>
    </div>

    <!-- Overall Progress Bar -->
    <div class="w-full bg-slate-100 h-1 relative overflow-hidden flex-shrink-0">
      <div
        class="h-full transition-all duration-500 ease-out"
        :class="overallProgressBarClass"
        :style="{ width: `${overallProgressPercent}%` }"
      />
    </div>

    <!-- Projects List -->
    <div class="p-3 space-y-2.5 overflow-y-auto flex-1 min-h-0">
      <div
        v-for="(state, name) in store.projectStates"
        :key="name"
        class="border border-slate-200 rounded-xl bg-slate-50/40 p-3.5 transition-all hover:border-slate-300 hover:shadow-sm"
      >
        <!-- Project Title & Branch & Status -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2 min-w-0">
            <svg
              class="w-4 h-4 text-slate-500 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
            <span class="text-xs font-bold text-slate-900 truncate">{{ name }}</span>

            <!-- Git Branch Badge -->
            <span
              v-if="getProjectBranch(String(name))"
              class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-indigo-50 border border-indigo-100 text-indigo-700 text-[10px] font-medium max-w-[140px] truncate"
              :title="getProjectBranch(String(name))"
            >
              <svg
                class="w-2.5 h-2.5 flex-shrink-0 text-indigo-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                />
              </svg>
              <span class="truncate">{{ getProjectBranch(String(name)) }}</span>
            </span>
          </div>

          <!-- Project Status Pill -->
          <span
            class="status-badge"
            :class="state.status"
          >
            {{ statusLabel(state.status) }}
          </span>
        </div>

        <!-- Project Step Progress Indicator -->
        <div
          v-if="state.steps.length > 0"
          class="mb-3"
        >
          <div class="flex items-center justify-between text-[10.5px] text-slate-500 mb-1">
            <span>阶段完成度 ({{ getCompletedStepCount(state.steps) }}/{{ state.steps.length }})</span>
            <span class="font-semibold text-slate-700">{{ getProjectPercent(state.steps) }}%</span>
          </div>
          <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="state.status === 'failed' ? 'bg-red-500' : state.status === 'done' ? 'bg-emerald-500' : 'bg-blue-600'"
              :style="{ width: `${getProjectPercent(state.steps)}%` }"
            />
          </div>
        </div>

        <!-- Timeline Steps -->
        <div
          v-if="state.steps.length > 0"
          class="pl-1 pt-1"
        >
          <StageNode
            v-for="(step, idx) in state.steps"
            :key="step.step"
            :label="step.step"
            :index="idx"
            :status="step.status"
            :active="step.step === state.currentStep"
            :message="step.message"
            :is-last="idx === state.steps.length - 1"
          />
        </div>

        <!-- Fallback current step -->
        <div
          v-else-if="state.currentStep"
          class="flex items-center gap-2 text-xs text-blue-600 font-medium bg-blue-50/80 p-2.5 rounded-lg border border-blue-100"
        >
          <svg
            class="w-3.5 h-3.5 animate-spin text-blue-600 flex-shrink-0"
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
          <span class="truncate">当前步骤: {{ state.currentStep }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Empty state when idle -->
  <div
    v-else
    class="flex-1 h-full flex flex-col items-center justify-center p-8 text-center bg-slate-50/40 select-none"
  >
    <div class="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100/80 text-blue-500 flex items-center justify-center mb-3 shadow-xs">
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.75"
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />
      </svg>
    </div>
    <h4 class="text-xs font-bold text-slate-700 mb-1">
      等待流水线任务
    </h4>
    <p class="text-[11px] text-slate-400 max-w-[220px] leading-relaxed mb-4">
      在左侧配置好参数并勾选项目，点击「开始执行」查看实时打包进度
    </p>
    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-slate-200/80 text-[11px] font-medium text-slate-500 shadow-xs">
      <span
        class="w-1.5 h-1.5 rounded-full"
        :class="store.selectedCount > 0 ? 'bg-emerald-500' : 'bg-slate-300'"
      />
      <span>已勾选 {{ store.selectedCount }} 个项目</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import StageNode from '@/components/StageNode.vue'
import type { StepStatusType, StepState } from '@/types'

const store = useAppStore()

const hasProgress = computed(() => {
  return store.running || Object.keys(store.projectStates).length > 0
})

function getProjectBranch(projectName: string): string {
  if (store.projectBranches[projectName]) {
    return store.projectBranches[projectName]
  }
  const proj = store.projects.find((p) => p.projectName === projectName)
  return proj?.currentBranch || ''
}

function statusLabel(status: StepStatusType): string {
  const labels: Record<StepStatusType, string> = {
    pending: '等待中',
    running: '执行中',
    done: '已完成',
    failed: '执行失败',
    skipped: '已跳过',
    retrying: '重试中',
  }
  return labels[status] || status
}

function getCompletedStepCount(steps: StepState[]): number {
  return steps.filter((s) => s.status === 'done' || s.status === 'skipped').length
}

function getProjectPercent(steps: StepState[]): number {
  if (!steps.length) return 0
  const completed = getCompletedStepCount(steps)
  return Math.round((completed / steps.length) * 100)
}

const overallProgressPercent = computed(() => {
  const projectList = Object.values(store.projectStates)
  if (!projectList.length) return store.running ? 10 : 0

  let totalSteps = 0
  let completedSteps = 0

  for (const p of projectList) {
    if (p.steps && p.steps.length > 0) {
      totalSteps += p.steps.length
      completedSteps += getCompletedStepCount(p.steps)
    } else {
      totalSteps += 1
      if (p.status === 'done') completedSteps += 1
    }
  }

  if (totalSteps === 0) return store.running ? 30 : 100
  return Math.round((completedSteps / totalSteps) * 100)
})

const overallStatusText = computed(() => {
  if (store.running) {
    const activeProject = Object.values(store.projectStates).find((p) => p.status === 'running')
    if (activeProject) {
      return `正在执行: ${activeProject.projectName}`
    }
    return '正在执行中...'
  }
  const total = Object.keys(store.projectStates).length
  if (total > 0) {
    if (store.failureCount > 0) {
      return `执行结束 (失败 ${store.failureCount})`
    }
    return `全部完成 (${store.successCount}/${total})`
  }
  return '准备就绪'
})

const overallStatusBadgeClass = computed(() => {
  if (store.running) {
    return 'bg-blue-100 text-blue-700'
  }
  if (store.failureCount > 0) {
    return 'bg-red-100 text-red-700'
  }
  if (store.successCount > 0) {
    return 'bg-emerald-100 text-emerald-700'
  }
  return 'bg-slate-200 text-slate-600'
})

const overallProgressBarClass = computed(() => {
  if (store.running) {
    return 'progress-shimmer'
  }
  if (store.failureCount > 0) {
    return 'bg-red-500'
  }
  return 'bg-emerald-500'
})
</script>
