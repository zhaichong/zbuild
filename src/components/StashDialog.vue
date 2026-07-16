<template>
  <teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="visible = false"></div>
      <div class="relative bg-surface rounded-xl shadow-2xl p-6 w-full max-w-lg z-10">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800">本地变更检查</h2>
          <button class="text-gray-400 hover:text-gray-600" @click="visible = false">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="loading" class="text-center py-8 text-gray-500">
          正在检查本地变更...
        </div>

        <div v-else-if="changes.length === 0" class="text-center py-8 text-gray-500">
          所有项目均无本地变更
        </div>

        <div v-else class="space-y-3 max-h-80 overflow-y-auto">
          <div
            v-for="change in changes"
            :key="change.repoPath"
            class="border border-gray-200 rounded-lg p-3"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-800">{{ change.project || change.repoPath }}</span>
              <span class="text-xs text-gray-500">{{ change.branch }}</span>
            </div>
            <div class="text-sm text-gray-600">
              {{ change.total }} 个文件变更
              <span v-if="change.truncated" class="text-warning">(仅显示部分)</span>
            </div>
            <div class="mt-2 space-y-0.5">
              <div
                v-for="file in change.files.slice(0, 10)"
                :key="file"
                class="text-xs text-gray-500 font-mono truncate"
              >
                {{ file }}
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 mt-4">
          <button
            class="px-4 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
            @click="visible = false"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { LocalChangeSummary } from '@/types'

const visible = ref(false)
const loading = ref(false)
const changes = ref<LocalChangeSummary[]>([])

function show(changesList: LocalChangeSummary[]) {
  changes.value = changesList
  loading.value = false
  visible.value = true
}

function setLoading() {
  loading.value = true
  visible.value = true
}

defineExpose({ show, setLoading, visible })
</script>
