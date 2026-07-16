<template>
  <div v-if="Object.keys(store.projectStates).length > 0" class="grid grid-cols-4 gap-4">
    <div class="bg-surface rounded-lg shadow-sm p-4 text-center">
      <div class="text-2xl font-bold text-gray-800">{{ store.projects.length }}</div>
      <div class="text-sm text-gray-500 mt-1">总项目数</div>
    </div>
    <div class="bg-surface rounded-lg shadow-sm p-4 text-center">
      <div class="text-2xl font-bold text-blue-600">{{ store.selectedCount }}</div>
      <div class="text-sm text-gray-500 mt-1">已选择</div>
    </div>
    <div class="bg-surface rounded-lg shadow-sm p-4 text-center">
      <div class="text-2xl font-bold text-green-600">{{ store.successCount }}</div>
      <div class="text-sm text-gray-500 mt-1">成功</div>
    </div>
    <div class="bg-surface rounded-lg shadow-sm p-4 text-center">
      <div class="text-2xl font-bold text-red-600">{{ store.failureCount }}</div>
      <div class="text-sm text-gray-500 mt-1">失败</div>
    </div>
  </div>

  <div class="flex justify-center gap-4 mt-6">
    <button
      v-if="!store.running"
      class="px-8 py-3 bg-primary text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
      :disabled="store.selectedCount === 0"
      @click="onStart"
    >
      开始执行
    </button>
    <button
      v-else
      class="px-8 py-3 bg-error text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
      @click="onStop"
    >
      停止执行
    </button>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/appStore'
import { startRun, stopRun } from '@/composables/usePipeline'

const store = useAppStore()

async function onStart() {
  const selectedList = Array.from(store.selectedProjects).map((name) => ({
    project: name,
    branch: store.projectBranches[name] || '',
  }))

  const payload = {
    config: store.config,
    projects: selectedList,
    mode: store.mode,
  }

  await startRun(payload)
}

async function onStop() {
  await stopRun()
}
</script>
