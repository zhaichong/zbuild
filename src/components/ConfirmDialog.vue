<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center"
  >
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      @click="visible = false"
    />
    <div
      class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-lg z-10 flex flex-col overflow-hidden"
      style="max-height: 80vh;"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border-light">
        <h2 class="text-lg font-bold text-text-1">
          确认执行
        </h2>
        <button
          class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
          @click="visible = false"
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
      <div class="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-4">
        <!-- Summary grid -->
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-xl bg-bg-base border border-border-light p-3">
            <div class="text-xs text-text-3 mb-1">
              执行模式
            </div>
            <div class="text-sm font-bold text-text-1">
              {{ modeLabel }}
            </div>
          </div>
          <div
            v-if="mode === 'svn'"
            class="rounded-xl bg-bg-base border border-border-light p-3"
          >
            <div class="text-xs text-text-3 mb-1">
              医院 / 订单号
            </div>
            <div
              class="text-sm font-bold text-text-1 truncate"
              :title="`${hospitalName} / ${orderNo}`"
            >
              {{ hospitalName }} / {{ orderNo }}
            </div>
          </div>
          <div
            v-else-if="mode === 'server'"
            class="rounded-xl bg-bg-base border border-border-light p-3"
          >
            <div class="text-xs text-text-3 mb-1">
              服务器地址
            </div>
            <div
              class="text-sm font-bold text-text-1 truncate"
              :title="serverAddress"
            >
              {{ serverAddress }}
            </div>
          </div>
          <div
            v-else
            class="rounded-xl bg-bg-base border border-border-light p-3"
          >
            <div class="text-xs text-text-3 mb-1">
              输出路径
            </div>
            <div class="text-sm font-bold text-text-1 truncate">
              本地目录
            </div>
          </div>
        </div>

        <!-- Project list -->
        <div>
          <h3 class="text-xs font-semibold text-text-3 mb-2">
            即将执行的项目 ({{ selectedList.length }})
          </h3>
          <div class="border border-border-light rounded-xl overflow-hidden divide-y divide-border-light max-h-[40vh] overflow-y-auto">
            <div
              v-for="item in selectedList"
              :key="item.name"
              class="px-4 py-3 bg-bg-base/20 flex items-center justify-between text-xs"
            >
              <div>
                <div class="font-semibold text-text-1">
                  {{ item.name }}
                </div>
                <div class="text-text-3 mt-1">
                  分支: {{ item.branch }}
                </div>
              </div>
              <div
                v-if="mode === 'svn' || mode === 'server'"
                class="text-right"
              >
                <span
                  v-if="mode === 'svn'"
                  class="px-2.5 py-1 rounded bg-primary/10 text-primary font-semibold"
                >
                  {{ item.svn_leaf }}
                </span>
                <span
                  v-else
                  class="px-2.5 py-1 rounded bg-primary/10 text-primary font-semibold truncate max-w-[180px] inline-block"
                  :title="item.server_upload_path"
                >
                  {{ item.server_upload_path }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light">
        <button
          class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
          @click="visible = false"
        >
          取消
        </button>
        <button
          class="px-6 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium flex items-center gap-1.5 shadow-md shadow-primary/20"
          @click="onConfirm"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 3l14 9-14 9V3z"
          /></svg>
          开始执行
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { UploadMode } from '@/types'

interface SelectedProject {
  name: string
  path?: string
  branch: string
  svn_leaf?: string
  server_upload_path?: string
  enabled: boolean
}

const store = useAppStore()
const visible = ref(false)

const payload = ref<{
  config: Record<string, unknown>
  projects: SelectedProject[]
  mode: UploadMode
} | null>(null)

const mode = computed<UploadMode>(() => payload.value?.mode || store.mode)

const modeLabel = computed(() => {
  switch (mode.value) {
    case 'svn': return 'SVN 上传'
    case 'server': return '服务器上传'
    case 'local': return '本地输出'
    default: return mode.value
  }
})

const selectedList = computed(() => payload.value?.projects || [])

const hospitalName = computed(() => {
  const form = (payload.value?.config as Record<string, unknown> | undefined)?.form as Record<string, string> | undefined
  return form?.hospitalName || ''
})

const orderNo = computed(() => {
  const form = (payload.value?.config as Record<string, unknown> | undefined)?.form as Record<string, string> | undefined
  return form?.orderNo || ''
})

const serverAddress = computed(() => {
  const form = (payload.value?.config as Record<string, unknown> | undefined)?.form as Record<string, string> | undefined
  return form?.serverAddress || ''
})

function show(data: { config: Record<string, unknown>; projects: SelectedProject[]; mode: UploadMode }) {
  payload.value = data
  visible.value = true
}

const emit = defineEmits<{ confirm: [payload: typeof payload.value] }>()

function onConfirm() {
  visible.value = false
  emit('confirm', payload.value)
}

defineExpose({ visible, show })
</script>
