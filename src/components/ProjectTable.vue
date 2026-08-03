<template>
  <div class="card overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-5 py-3.5 border-b border-border-light">
      <h2 class="text-[15px] font-semibold text-text-1">
        项目列表
      </h2>
      <div class="flex gap-1.5">
        <button
          class="px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-white text-text-2 hover:bg-border-light transition-colors"
          @click="store.selectAll()"
        >
          全选
        </button>
        <button
          class="px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-white text-text-2 hover:bg-border-light transition-colors"
          @click="store.deselectAll()"
        >
          取消全选
        </button>
        <button
          class="px-3 py-1.5 rounded-md text-xs font-medium bg-primary-light text-primary border-0 hover:bg-blue-200 transition-colors disabled:opacity-50"
          :disabled="loading"
          @click="onSmartSelect"
        >
          {{ loading ? '检测中...' : '智能选择' }}
        </button>
        <button
          class="px-3 py-1.5 rounded-md text-xs font-medium border border-border bg-white text-text-2 hover:bg-border-light transition-colors"
          @click="onRefreshAll"
        >
          刷新分支
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 40px">
              <input
                type="checkbox"
                class="w-4 h-4 accent-primary cursor-pointer"
                :checked="allSelected"
                @change="allSelected ? store.deselectAll() : store.selectAll()"
              >
            </th>
            <th>项目名称</th>
            <th>当前分支</th>
            <th style="width: 160px">
              切换分支
            </th>
            <th>SVN Leaf</th>
            <th v-if="store.mode === 'server'">
              服务器路径
            </th>
            <th style="width: 90px">
              状态
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="project in store.projects"
            :key="project.projectName"
            :class="{ selected: store.selectedProjects.has(project.projectName) }"
          >
            <td>
              <input
                type="checkbox"
                class="w-4 h-4 accent-primary cursor-pointer"
                :checked="store.selectedProjects.has(project.projectName)"
                @change="store.toggleProject(project.projectName)"
              >
            </td>
            <td class="font-semibold text-text-1">
              {{ project.projectName }}
            </td>
            <td class="text-text-2">
              {{ store.projectBranches[project.projectName] || project.currentBranch }}
            </td>
            <td>
              <div class="flex items-center gap-1">
                <button
                  class="branch-picker px-2 py-1 border border-border rounded-md text-xs bg-white text-text-1 hover:bg-border-light hover:border-primary/30 transition-colors text-left flex-1 max-w-[130px] truncate"
                  @click="openBranchPicker(project)"
                >
                  {{ store.projectBranches[project.projectName] || project.currentBranch || '选择分支' }}
                  <svg
                    class="w-3 h-3 inline-block ml-1 opacity-50"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                <button
                  class="p-1 rounded-md text-text-3 hover:text-primary hover:bg-border-light transition-colors flex-shrink-0"
                  :class="{ 'animate-spin': refreshingProject === project.projectName }"
                  title="刷新此项目分支"
                  @click="onRefreshOne(project.projectName)"
                >
                  <svg
                    class="w-3.5 h-3.5"
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
            <td>
              <input
                class="px-2 py-1 border border-border rounded-md text-xs bg-white text-text-2 outline-none w-full max-w-[140px] focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-colors"
                :value="store.projectSvnLeaves[project.projectName] || project.defaultSvnLeaf || ''"
                placeholder="svn leaf 路径"
                @input="onSvnLeafInput(project.projectName, ($event.target as HTMLInputElement).value)"
              >
            </td>
            <td v-if="store.mode === 'server'">
              <input
                class="px-2 py-1 border border-border rounded-md text-xs bg-white text-text-2 outline-none w-full max-w-[160px] focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-colors"
                :value="store.projectServerPaths[project.projectName] || project.serverUploadPath || defaultServerPath(project.projectName)"
                placeholder="/home/data/web"
                @input="onServerPathInput(project.projectName, ($event.target as HTMLInputElement).value)"
              >
            </td>
            <td>
              <span
                v-if="store.projectStates[project.projectName]"
                class="status-badge"
                :class="store.projectStates[project.projectName].status"
              >
                {{ statusLabel(store.projectStates[project.projectName].status) }}
              </span>
              <span
                v-else
                class="status-badge pending"
              >待执行</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div
      v-if="store.projects.length === 0"
      class="flex flex-col items-center justify-center py-12 text-text-3"
    >
      <svg
        width="48"
        height="48"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        class="opacity-35 mb-3"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
        />
      </svg>
      <p class="text-sm">
        暂无项目，请先配置工作目录
      </p>
    </div>

    <!-- Branch Picker Dialog -->
    <PickerDialog
      ref="pickerRef"
      title="选择分支"
      :items="pickerItems"
      :current-value="pickerCurrentValue"
      @choose="onBranchChoose"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { refreshBranches } from '@/composables/useProjects'
import { useAffected } from '@/composables/useAffected'
import PickerDialog from '@/components/PickerDialog.vue'
import type { ProjectInfo, StepStatusType } from '@/types'

const store = useAppStore()
const { loading, detectAffectedStaged, selectAffected } = useAffected()

const pickerRef = ref<InstanceType<typeof PickerDialog> | null>(null)
const pickerItems = ref<string[]>([])
const pickerCurrentValue = ref('')
const pickerProjectName = ref('')
const refreshingProject = ref('')

const allSelected = computed(() => {
  return store.projects.length > 0 && store.selectedProjects.size === store.projects.length
})

function statusLabel(status: StepStatusType): string {
  const labels: Record<StepStatusType, string> = {
    pending: '待执行', running: '执行中', done: '已完成',
    failed: '失败', skipped: '已跳过', retrying: '重试中',
  }
  return labels[status] || status
}

function defaultServerPath(projectName: string): string {
  if (!store.config?.serverUploadPaths) return ''
  return store.config.serverUploadPaths[projectName] || ''
}

async function openBranchPicker(project: ProjectInfo) {
  pickerProjectName.value = project.projectName
  // If branch list is empty, fetch remote branches first so user can pick
  let branches = project.branches || []
  if (branches.length === 0) {
    try {
      refreshingProject.value = project.projectName
      await refreshBranches(project.projectName)
      const updated = store.projects.find((p) => p.projectName === project.projectName)
      if (updated) branches = updated.branches || []
    } catch (e) {
      console.error('Failed to refresh branches for ' + project.projectName + ':', e)
    } finally {
      refreshingProject.value = ''
    }
  }
  pickerItems.value = branches
  // Pass currentVal directly to show() — avoids Vue 3 reactivity timing issue
  // where props.currentValue inside the child may still hold the old value
  // when show() runs synchronously after the ref assignment above.
  const currentVal = store.projectBranches[project.projectName] || project.currentBranch || ''
  pickerCurrentValue.value = currentVal
  if (pickerRef.value) {
    pickerRef.value.show(currentVal)
  }
}

function onBranchChoose(branch: string) {
  if (pickerProjectName.value) {
    store.projectBranches[pickerProjectName.value] = branch
  }
}

function onSvnLeafInput(projectName: string, value: string) {
  store.projectSvnLeaves[projectName] = value
}

function onServerPathInput(projectName: string, value: string) {
  store.projectServerPaths[projectName] = value
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
