<template>
  <div class="bg-surface rounded-lg shadow-sm p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800">项目列表</h2>
      <div class="flex gap-2">
        <button
          class="px-3 py-1.5 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
          @click="store.selectAll()"
        >
          全选
        </button>
        <button
          class="px-3 py-1.5 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
          @click="store.deselectAll()"
        >
          取消全选
        </button>
        <button
          class="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:opacity-90 transition-opacity"
          @click="onRefreshAll"
        >
          刷新分支
        </button>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200">
            <th class="text-left py-2 px-3 w-10">
              <input
                type="checkbox"
                :checked="allSelected"
                @change="allSelected ? store.deselectAll() : store.selectAll()"
                class="rounded"
              />
            </th>
            <th class="text-left py-2 px-3">项目名称</th>
            <th class="text-left py-2 px-3">当前分支</th>
            <th class="text-left py-2 px-3">切换分支</th>
            <th class="text-left py-2 px-3">状态</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="project in store.projects"
            :key="project.projectName"
            class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
          >
            <td class="py-2 px-3">
              <input
                type="checkbox"
                :checked="store.selectedProjects.has(project.projectName)"
                @change="store.toggleProject(project.projectName)"
                class="rounded"
              />
            </td>
            <td class="py-2 px-3 font-medium text-gray-800">{{ project.projectName }}</td>
            <td class="py-2 px-3 text-gray-600">{{ store.projectBranches[project.projectName] || project.currentBranch }}</td>
            <td class="py-2 px-3">
              <select
                :value="store.projectBranches[project.projectName] || project.currentBranch"
                class="px-2 py-1 border border-gray-300 rounded text-xs focus:ring-2 focus:ring-primary focus:border-transparent"
                @change="onBranchChange(project.projectName, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="branch in project.branches" :key="branch" :value="branch">
                  {{ branch }}
                </option>
              </select>
            </td>
            <td class="py-2 px-3">
              <span
                v-if="store.projectStates[project.projectName]"
                class="text-xs font-medium"
                :class="store.projectStates[project.projectName].statusClass"
              >
                {{ store.projectStates[project.projectName].status }}
              </span>
              <span v-else class="text-xs text-gray-400">待执行</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="store.projects.length === 0" class="text-center py-8 text-gray-400">
      暂无项目，请先配置工作目录
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { refreshBranches } from '@/composables/useProjects'

const store = useAppStore()

const allSelected = computed(() => {
  return store.projects.length > 0 && store.selectedProjects.size === store.projects.length
})

function onBranchChange(projectName: string, branch: string) {
  store.projectBranches[projectName] = branch
}

async function onRefreshAll() {
  for (const project of store.projects) {
    try {
      await refreshBranches(project.projectName)
    } catch (err) {
      console.error(`Failed to refresh ${project.projectName}:`, err)
    }
  }
}
</script>
