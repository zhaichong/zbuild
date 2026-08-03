<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="onCancel"
      />
      <div
        class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-lg z-10 flex flex-col overflow-hidden"
        style="max-height: 80vh;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border-light">
          <div class="flex items-center gap-2">
            <svg
              class="w-5 h-5 text-warning"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <h2 class="text-lg font-bold text-text-1">
              检测到本地修改
            </h2>
          </div>
          <button
            class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
            @click="onCancel"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="flex-1 min-h-0 overflow-y-auto px-6 py-4">
          <p class="text-xs text-text-3 mb-4">
            以下项目存在未提交的本地修改，继续执行可能会覆盖这些更改：
          </p>

          <div
            v-if="loading"
            class="text-center py-8 text-text-3"
          >
            正在检查本地变更...
          </div>

          <div
            v-else-if="changes.length === 0"
            class="text-center py-8 text-text-3"
          >
            所有项目均无本地变更。
          </div>

          <div
            v-else
            class="space-y-3"
          >
            <div
              v-for="change in changes"
              :key="change.repoPath"
              class="border border-border-light rounded-xl p-3"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-text-1">{{ change.project || change.repoPath }}</span>
                <span class="text-[10px] text-text-3">
                  {{ change.branch }} · {{ change.total }} 个文件
                </span>
              </div>
              <div class="space-y-0.5 max-h-24 overflow-auto">
                <div
                  v-for="file in change.files.slice(0, 20)"
                  :key="file"
                  class="text-[11px] text-text-3 font-mono"
                >
                  {{ file }}
                </div>
              </div>
              <p
                v-if="change.truncated"
                class="text-[10px] text-text-3 mt-1 italic"
              >
                ... 还有更多文件未显示
              </p>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light">
          <button
            class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="onCancel"
          >
            取消执行
          </button>
          <button
            class="px-4 py-2 text-sm rounded-xl border border-warning text-warning bg-warning/10 hover:bg-warning/20 transition-colors"
            @click="onSkip"
          >
            跳过这些项目
          </button>
          <button
            class="inline-flex items-center gap-1.5 px-5 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium"
            @click="onStash"
          >
            继续并 stash
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

const emit = defineEmits<{
  cancel: []
  skip: []
  stash: []
}>()

function close() {
  visible.value = false
}

function onCancel() {
  close()
  emit('cancel')
}

function onSkip() {
  close()
  emit('skip')
}

function onStash() {
  close()
  emit('stash')
}

defineExpose({ show, visible })
</script>
