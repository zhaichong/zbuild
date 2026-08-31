<template>
  <div class="card bg-white border border-slate-200/90 rounded-2xl shadow-2xs flex-1 min-h-0 flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="shrink-0 flex flex-wrap items-center justify-between px-5 py-3 border-b border-slate-100 bg-slate-50/60 gap-3">
      <div class="flex items-center gap-2.5">
        <h2 class="text-sm font-bold text-slate-900 tracking-tight">
          项目列表
        </h2>
        <span class="text-xs text-slate-600 bg-slate-200/70 px-2.5 py-0.5 rounded-full font-mono font-bold">
          已选 <strong class="text-blue-600 font-extrabold">{{ store.selectedCount }}</strong> / {{ store.projects.length }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors cursor-pointer shadow-2xs"
          @click="store.selectAll()"
        >
          全选
        </button>
        <button
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors cursor-pointer shadow-2xs"
          @click="store.deselectAll()"
        >
          取消全选
        </button>
        <button
          type="button"
          class="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-1.5 shadow-2xs"
          :disabled="loading"
          @click="onSmartSelect"
        >
          <svg class="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>{{ loading ? '检测变动中...' : '智能选择变动' }}</span>
        </button>
        <button
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
          @click="onRefreshAll"
        >
          <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>刷新全部分支</span>
        </button>
      </div>
    </div>

    <!-- Data Table (Scrollable with Sticky Header) -->
    <div class="flex-1 min-h-0 overflow-y-auto overflow-x-auto">
      <table class="w-full border-collapse text-left">
        <thead class="sticky top-0 z-10 bg-slate-100/90 backdrop-blur-xs shadow-2xs border-b border-slate-200">
          <tr class="text-slate-700 text-xs font-bold uppercase tracking-wider">
            <th class="w-12 px-4 py-3 text-center">
              <input
                type="checkbox"
                class="w-4 h-4 accent-blue-600 rounded cursor-pointer transition-colors"
                :checked="allSelected"
                @change="allSelected ? store.deselectAll() : store.selectAll()"
              >
            </th>
            <th class="px-4 py-3 font-bold text-slate-800 min-w-[220px]">
              项目名称
            </th>
            <th class="px-4 py-3 font-bold text-slate-800 min-w-[240px]">
              目标分支
            </th>
            <th class="px-4 py-3 font-bold text-slate-800 w-36 text-center">
              执行状态
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-slate-800 text-sm">
          <tr
            v-for="project in store.projects"
            :key="project.projectName"
            class="transition-colors hover:bg-slate-50/90"
            :class="{ 'bg-blue-50/40': store.selectedProjects.has(project.projectName) }"
          >
            <!-- Checkbox -->
            <td class="px-4 py-3.5 text-center">
              <input
                type="checkbox"
                class="w-4 h-4 accent-blue-600 rounded cursor-pointer transition-colors"
                :checked="store.selectedProjects.has(project.projectName)"
                @change="store.toggleProject(project.projectName)"
              >
            </td>

            <!-- Project Name (Bold & Larger) -->
            <td class="px-4 py-3.5 font-bold text-slate-900 text-sm">
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-blue-500/70 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <span class="truncate" :title="project.projectName">
                  {{ project.projectName }}
                </span>
              </div>
            </td>

            <!-- Target Branch Inline Searchable Dropdown -->
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-2">
                <BranchSelect
                  :model-value="store.projectBranches[project.projectName] || project.currentBranch || ''"
                  :branches="getProjectBranches(project)"
                  :project-name="project.projectName"
                  :custom-commands="store.config?.branchBuildCommands?.[project.projectName] || {}"
                  @update:model-value="(val) => onBranchSelected(project.projectName, val)"
                />

                <!-- Custom Command Flash Indicator -->
                <span
                  v-if="hasBranchCustomCommand(project.projectName, store.projectBranches[project.projectName] || project.currentBranch)"
                  class="text-xs px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200 font-mono font-bold whitespace-nowrap cursor-help shrink-0"
                  :title="'此分支已配置专属打包命令: ' + store.getEffectiveBuildCommand(project.projectName, store.projectBranches[project.projectName] || project.currentBranch)"
                >
                  ⚡
                </span>

                <!-- Refresh Project Branch Button -->
                <button
                  type="button"
                  class="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors flex-shrink-0 cursor-pointer"
                  :class="{ 'animate-spin text-blue-600': refreshingProject === project.projectName }"
                  title="刷新此项目分支"
                  @click="onRefreshOne(project.projectName)"
                >
                  <svg
                    class="w-4 h-4"
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
                </button>
              </div>
            </td>

            <!-- Status Column (Bold & Centered) -->
            <td class="px-4 py-3.5 text-center">
              <span
                v-if="store.projectStates[project.projectName]"
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border shadow-2xs"
                :class="getStatusBadgeClass(store.projectStates[project.projectName].status)"
              >
                <span class="w-2 h-2 rounded-full" :class="getStatusDotClass(store.projectStates[project.projectName].status)" />
                {{ statusLabel(store.projectStates[project.projectName].status) }}
              </span>
              <span
                v-else
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200/80 shadow-2xs"
              >
                <span class="w-2 h-2 rounded-full bg-slate-400" />
                待执行
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div
      v-if="store.projects.length === 0"
      class="flex flex-col items-center justify-center py-12 text-slate-400"
    >
      <svg
        width="48"
        height="48"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        class="opacity-30 mb-3"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
        />
      </svg>
      <p class="text-sm font-bold text-slate-600">
        暂无项目，请先在右上角配置工作目录
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { refreshBranches } from '@/composables/useProjects'
import { useAffected } from '@/composables/useAffected'
import BranchSelect from '@/components/BranchSelect.vue'
import type { ProjectInfo, StepStatusType } from '@/types'

const store = useAppStore()
const { loading, detectAffectedStaged, selectAffected } = useAffected()

const refreshingProject = ref('')

const allSelected = computed(() => {
  return store.projects.length > 0 && store.selectedProjects.size === store.projects.length
})

function getProjectBranches(project: ProjectInfo): string[] {
  if (project.branches && project.branches.length > 0) {
    return project.branches
  }
  return project.currentBranch ? [project.currentBranch] : []
}

function onBranchSelected(projectName: string, branch: string) {
  if (!projectName || !branch) return
  store.projectBranches[projectName] = branch

  // Persist selected branch to localStorage for subsequent sessions
  try {
    const raw = localStorage.getItem('zbuild_selected_branches')
    const map = raw ? JSON.parse(raw) : {}
    map[projectName] = branch
    localStorage.setItem('zbuild_selected_branches', JSON.stringify(map))
  } catch {
    // ignore
  }
}

function statusLabel(status: StepStatusType): string {
  const labels: Record<StepStatusType, string> = {
    pending: '待执行', running: '执行中', done: '已完成',
    failed: '失败', skipped: '已跳过', retrying: '重试中',
  }
  return labels[status] || status
}

function getStatusBadgeClass(status: StepStatusType): string {
  if (status === 'done') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (status === 'failed') return 'bg-red-50 text-red-700 border-red-200'
  if (status === 'running') return 'bg-blue-50 text-blue-700 border-blue-200'
  if (status === 'skipped') return 'bg-amber-50 text-amber-700 border-amber-200'
  if (status === 'retrying') return 'bg-orange-50 text-orange-700 border-orange-200'
  return 'bg-slate-100 text-slate-600 border-slate-200'
}

function getStatusDotClass(status: StepStatusType): string {
  if (status === 'done') return 'bg-emerald-500'
  if (status === 'failed') return 'bg-red-500'
  if (status === 'running') return 'bg-blue-500 animate-ping'
  if (status === 'skipped') return 'bg-amber-500'
  if (status === 'retrying') return 'bg-orange-500'
  return 'bg-slate-400'
}

function hasBranchCustomCommand(projectName: string, branch: string): boolean {
  if (!branch) return false
  const branchCmds = store.config?.branchBuildCommands?.[projectName]
  if (!branchCmds) return false
  if (branchCmds[branch]) return true
  for (const pat of Object.keys(branchCmds)) {
    if (pat.endsWith('*') && branch.startsWith(pat.slice(0, -1))) {
      return true
    }
  }
  return false
}

async function onRefreshAll() {
  for (const project of store.projects) {
    try {
      await refreshBranches(project.projectName)
    } catch (err) {
      console.error('Failed to refresh ' + project.projectName + ':', err)
    }
  }
}

async function onRefreshOne(projectName: string) {
  refreshingProject.value = projectName
  try {
    await refreshBranches(projectName)
  } catch (err) {
    console.error('Failed to refresh ' + projectName + ':', err)
  } finally {
    refreshingProject.value = ''
  }
}

async function onSmartSelect() {
  const affected = await detectAffectedStaged()
  if (affected.length === 0) {
    store.showToast('未检测到有变更的项目', 'warning')
    return
  }
  selectAffected()
  store.showToast('已选择 ' + affected.length + ' 个有变更的项目: ' + affected.join('、'), 'success')
}
</script>
