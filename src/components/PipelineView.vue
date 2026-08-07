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

    <!-- Companion Status Banner -->
    <div class="px-3 py-2 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-slate-50 border-b border-slate-100 flex items-center gap-3 flex-shrink-0">
      <PixelPet :state="petState" size="mini" tooltip="点击与桌宠互动" />
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] font-bold text-slate-800">{{ petBannerTitle }}</span>
          <span class="text-[10px] text-slate-400">({{ overallProgressPercent }}%)</span>
        </div>
        <p class="text-[10.5px] text-slate-500 truncate">{{ petBannerMessage }}</p>
      </div>
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

  <!-- Empty state when idle with Desktop Pet Mascot -->
  <div
    v-else
    class="flex-1 h-full flex flex-col items-center justify-center p-8 text-center bg-slate-50/40 select-none relative"
  >
    <!-- Pixel Mascot Character -->
    <div class="mb-3 relative group">
      <div class="w-20 h-24 flex items-end justify-center">
        <PixelPet state="idle" size="md" tooltip="点击与桌宠打招呼！" />
      </div>
      <!-- Soft Shadow Base -->
      <div class="w-16 h-2 bg-slate-300/50 rounded-full mx-auto -mt-1 blur-[1px]"></div>
    </div>

    <h4 class="text-xs font-bold text-slate-800 mb-1 flex items-center gap-1.5 justify-center">
      <span>等待流水线任务</span>
      <span class="text-blue-500">✨</span>
    </h4>
    <p class="text-[11px] text-slate-400 max-w-[230px] leading-relaxed mb-4">
      在左侧配置好参数并勾选项目，点击「开始执行」即可全自动构建与打包
    </p>

    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-slate-200/80 text-[11px] font-medium text-slate-600 shadow-xs">
      <span
        class="w-1.5 h-1.5 rounded-full transition-colors"
        :class="store.selectedCount > 0 ? 'bg-emerald-500 ring-2 ring-emerald-100' : 'bg-slate-300'"
      />
      <span>已勾选 <strong class="text-slate-800 font-bold">{{ store.selectedCount }}</strong> 个项目</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import StageNode from '@/components/StageNode.vue'
import PixelPet from '@/components/PixelPet.vue'
import type { StepStatusType, StepState } from '@/types'

const store = useAppStore()

const hasProgress = computed(() => {
  return store.running || Object.keys(store.projectStates).length > 0
})

const petState = computed<'idle' | 'running' | 'complete' | 'error'>(() => {
  if (store.running) return 'running'
  const total = Object.keys(store.projectStates).length
  if (total > 0) {
    if (store.failureCount > 0) return 'error'
    if (store.successCount > 0) return 'complete'
  }
  return 'idle'
})

const petBannerTitle = computed(() => {
  if (store.running) return '桌宠正在监工打包中...'
  if (store.failureCount > 0) return '构建遇到异常'
  if (store.successCount > 0) return '所有项目打包完成！'
  return '桌宠待命中'
})

const petBannerMessage = computed(() => {
  if (store.running) {
    const activeProject = Object.values(store.projectStates).find((p) => p.status === 'running')
    if (activeProject) {
      return `当前项目: ${activeProject.projectName} (${activeProject.currentStep || '执行中...'})`
    }
    return '正在按流水线规则依次构建各项目...'
  }
  if (store.failureCount > 0) {
    return `有 ${store.failureCount} 个项目失败，可展开查看详细日志`
  }
  if (store.successCount > 0) {
    return '太棒了！所有勾选的模块均已成功生成'
  }
  return '配置项目后点击「开始执行」即可开工'
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

<style scoped>
.status-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 9999px;
}
.status-badge.pending {
  background: #f1f5f9;
  color: #64748b;
}
.status-badge.running {
  background: #dbeafe;
  color: #2563eb;
}
.status-badge.done {
  background: #dcfce7;
  color: #16a34a;
}
.status-badge.failed {
  background: #fee2e2;
  color: #dc2626;
}
.status-badge.skipped {
  background: #f1f5f9;
  color: #94a3b8;
}
.status-badge.retrying {
  background: #fef3c7;
  color: #d97706;
}

.progress-shimmer {
  background: linear-gradient(90deg, #2563eb 0%, #3b82f6 50%, #60a5fa 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite linear;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
