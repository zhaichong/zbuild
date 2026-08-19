<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs"
    >
      <div
        class="relative bg-white rounded-2xl shadow-2xl w-full max-w-4xl z-10 flex flex-col overflow-hidden border border-slate-200 text-slate-800"
        style="height: 85vh; max-height: 760px;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 bg-slate-50/80 shrink-0">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-base font-bold shrink-0">
              📄
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="text-sm font-bold text-slate-900 truncate" :title="fileName">
                  {{ fileName }}
                </h3>
                <span class="px-2 py-0.5 text-[10px] rounded-full bg-slate-200 text-slate-700 font-mono font-semibold shrink-0">
                  {{ fileFormatTag }}
                </span>
                <span v-if="fileSizeFormatted" class="text-[11px] text-slate-400 font-mono shrink-0">
                  {{ fileSizeFormatted }}
                </span>
              </div>
              <p class="text-[11px] text-slate-400 font-mono truncate" :title="filePath">
                {{ filePath }}
              </p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0">
            <!-- Copy button -->
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
              @click="copyContent"
            >
              <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span>{{ copyStatusText }}</span>
            </button>

            <!-- Download button -->
            <button
              v-if="content"
              type="button"
              class="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
              title="下载文件到本地"
              @click="downloadFile"
            >
              <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>下载</span>
            </button>

            <!-- Open with system default app -->
            <button
              v-if="filePath && ipc.isElectron()"
              type="button"
              class="px-3 py-1.5 text-xs font-semibold bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
              title="使用系统默认程序 (如 Navicat / VSCode / 记事本等) 打开"
              @click="openInSystem"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              <span>用系统程序打开</span>
            </button>

            <!-- Close -->
            <button
              class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 cursor-pointer ml-1"
              @click="visible = false"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Code Viewer Body -->
        <div class="flex-1 min-h-0 flex flex-col bg-[#1e1e2e] text-[#cdd6f4] font-mono text-xs overflow-hidden">
          <!-- Quick search toolbar inside editor -->
          <div class="flex items-center justify-between px-4 py-1.5 bg-[#181825] border-b border-[#313244] text-[11px]">
            <div class="flex items-center gap-3 text-slate-400">
              <span>共 {{ lineCount }} 行</span>
              <span>•</span>
              <span>编码: UTF-8</span>
            </div>
            <div class="flex items-center gap-2">
              <input
                v-model="searchKeyword"
                type="text"
                placeholder="搜索关键词 (Ctrl+F)..."
                class="px-2 py-0.5 rounded bg-[#313244] text-[#cdd6f4] placeholder-slate-500 border border-[#45475a] outline-none text-[11px] focus:border-blue-500 w-44"
              >
              <span v-if="searchKeyword" class="text-[10px] text-slate-400">
                匹配: {{ matchCount }} 处
              </span>
            </div>
          </div>

          <!-- Code Lines Container with line numbers -->
          <div class="flex-1 min-h-0 overflow-auto p-3 select-text code-scrollbar">
            <div class="table w-full border-collapse">
              <div
                v-for="(line, idx) in lines"
                :key="idx"
                class="table-row hover:bg-[#313244]/40"
                :class="{ 'bg-yellow-500/20': searchKeyword && line.toLowerCase().includes(searchKeyword.toLowerCase()) }"
              >
                <!-- Line number -->
                <span class="table-cell select-none text-right pr-4 text-[#6c7086] text-[11px] w-12 shrink-0 font-mono">
                  {{ idx + 1 }}
                </span>
                <!-- Line content -->
                <span class="table-cell whitespace-pre font-mono text-[12px] leading-relaxed text-[#cdd6f4] break-all">
                  {{ line }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-5 py-2.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 shrink-0">
          <div class="flex items-center gap-2 text-[11px]">
            <span class="text-emerald-600 font-bold">●</span>
            <span>已成功从 SVN 导出并载入预览</span>
          </div>
          <button
            type="button"
            class="px-4 py-1 text-xs border border-slate-200 rounded-lg hover:bg-slate-100 text-slate-700 cursor-pointer"
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
import { ref, computed } from 'vue'
import { ipc } from '@/services/ipc'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
const visible = ref(false)
const fileName = ref('')
const filePath = ref('')
const content = ref('')
const fileSize = ref(0)
const searchKeyword = ref('')
const copyStatusText = ref('复制内容')

const lines = computed(() => {
  if (!content.value) return ['']
  return content.value.split('\n')
})

const lineCount = computed(() => lines.value.length)

const matchCount = computed(() => {
  if (!searchKeyword.value.trim()) return 0
  const kw = searchKeyword.value.trim().toLowerCase()
  return lines.value.filter((l) => l.toLowerCase().includes(kw)).length
})

const fileFormatTag = computed(() => {
  const name = fileName.value.toLowerCase()
  if (name.endsWith('.sql')) return 'SQL 脚本'
  if (name.endsWith('.json')) return 'JSON 数据'
  if (name.endsWith('.xml')) return 'XML'
  if (name.endsWith('.yaml') || name.endsWith('.yml')) return 'YAML'
  if (name.endsWith('.md')) return 'Markdown'
  if (name.endsWith('.txt') || name.endsWith('.log')) return '文本文件'
  if (name.endsWith('.sh') || name.endsWith('.bat')) return 'Shell / 批处理'
  return '代码/文本'
})

const fileSizeFormatted = computed(() => {
  const size = fileSize.value
  if (!size) return ''
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
})

function show(options: {
  fileName: string
  filePath: string
  content: string
  size?: number
}) {
  fileName.value = options.fileName || '文件预览'
  filePath.value = options.filePath || ''
  content.value = options.content || ''
  fileSize.value = options.size || 0
  searchKeyword.value = ''
  copyStatusText.value = '复制内容'
  visible.value = true
}

async function copyContent() {
  if (!content.value) return
  try {
    await navigator.clipboard.writeText(content.value)
    copyStatusText.value = '✓ 已复制'
    store.showToast('已复制文件内容到剪贴板', 'success')
    setTimeout(() => {
      copyStatusText.value = '复制内容'
    }, 2000)
  } catch (err: unknown) {
    store.showToast('复制失败: ' + String(err), 'error')
  }
}

async function downloadFile() {
  if (!content.value) return
  try {
    const blob = new Blob([content.value], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName.value || 'download.txt'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    store.showToast('已开始下载文件', 'success')
  } catch (err: unknown) {
    store.showToast('下载失败: ' + String(err), 'error')
  }
}

async function openInSystem() {
  if (!filePath.value) return
  store.showToast('正在调用系统程序打开...', 'info')
  const res = await ipc.openPath(filePath.value)
  if (res.success) {
    store.showToast('已调用系统程序打开文件', 'success')
  } else {
    store.showToast('打开失败: ' + (res.error || '未找到关联程序'), 'error')
  }
}

defineExpose({
  show,
  visible,
})
</script>

<style scoped>
.code-scrollbar::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
.code-scrollbar::-webkit-scrollbar-track {
  background: #181825;
}
.code-scrollbar::-webkit-scrollbar-thumb {
  background: #45475a;
  border-radius: 4px;
}
.code-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #585b70;
}
</style>
