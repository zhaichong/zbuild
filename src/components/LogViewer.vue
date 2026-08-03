<template>
  <div class="flex-1 h-full flex flex-col overflow-hidden bg-slate-900 relative select-text">
    <!-- macOS Terminal Header Bar -->
    <div class="flex items-center justify-between px-3.5 py-2.5 bg-[#0f172a] border-b border-slate-800 text-slate-300 select-none flex-shrink-0">
      <!-- Window Controls & Title -->
      <div class="flex items-center gap-2.5">
        <div class="flex items-center gap-1.5">
          <div class="w-2.5 h-2.5 rounded-full bg-[#ff5f56] opacity-80" />
          <div class="w-2.5 h-2.5 rounded-full bg-[#ffbd2e] opacity-80" />
          <div class="w-2.5 h-2.5 rounded-full bg-[#27c93f] opacity-80" />
        </div>
        <div class="flex items-center gap-1.5 pl-1.5 border-l border-slate-700">
          <svg
            class="w-3.5 h-3.5 text-blue-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <span class="text-xs font-mono font-bold tracking-tight text-slate-200">zbuild.log</span>
          <span
            v-if="store.logs.length > 0"
            class="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400 border border-slate-700"
          >
            {{ filteredLogs.length }} / {{ store.logs.length }}
          </span>
        </div>
      </div>

      <!-- Controls & Actions -->
      <div class="flex items-center gap-1.5">
        <!-- Project Filter Dropdown -->
        <select
          v-if="logProjects.length > 1"
          v-model="projectFilter"
          class="px-2 py-0.5 bg-slate-800/90 border border-slate-700 hover:border-slate-600 rounded text-[11px] font-mono text-slate-300 outline-none cursor-pointer max-w-[130px] truncate"
        >
          <option value="">
            全部项目 ({{ logProjects.length }})
          </option>
          <option
            v-for="p in logProjects"
            :key="p"
            :value="p"
          >
            {{ p }}
          </option>
        </select>

        <!-- Search Bar -->
        <div class="relative flex items-center">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索日志..."
            class="w-24 focus:w-36 transition-all duration-200 px-2 py-0.5 pl-6 bg-slate-800/90 border border-slate-700 focus:border-blue-500 rounded text-[11px] font-mono text-slate-200 placeholder-slate-500 outline-none"
          >
          <svg
            class="w-3 h-3 text-slate-500 absolute left-1.5 pointer-events-none"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <button
            v-if="searchKeyword"
            class="absolute right-1 text-slate-400 hover:text-slate-200 text-xs"
            @click="searchKeyword = ''"
          >
            ×
          </button>
        </div>

        <!-- Copy All Button -->
        <button
          class="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          :title="copied ? '已复制' : '复制全部日志'"
          @click="copyAllLogs"
        >
          <svg
            v-if="!copied"
            class="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
            />
          </svg>
          <svg
            v-else
            class="w-3.5 h-3.5 text-emerald-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </button>

        <!-- Clear Button -->
        <button
          class="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
          title="清空日志"
          @click="store.clearLogs()"
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
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Quick Level Filter Bar -->
    <div
      v-if="store.logs.length > 0"
      class="flex items-center gap-1 px-3.5 py-1 bg-[#0b0f19] border-b border-slate-800/80 text-[10.5px] font-mono select-none"
    >
      <button
        class="px-2 py-0.5 rounded transition-colors"
        :class="levelFilter === '' ? 'bg-slate-700 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
        @click="levelFilter = ''"
      >
        全部 ({{ counts.all }})
      </button>
      <button
        class="px-2 py-0.5 rounded transition-colors flex items-center gap-1"
        :class="levelFilter === 'info' ? 'bg-blue-900/60 text-blue-300 font-bold border border-blue-700/50' : 'text-slate-400 hover:text-slate-200'"
        @click="levelFilter = 'info'"
      >
        信息 ({{ counts.info }})
      </button>
      <button
        class="px-2 py-0.5 rounded transition-colors flex items-center gap-1"
        :class="levelFilter === 'success' ? 'bg-emerald-900/60 text-emerald-300 font-bold border border-emerald-700/50' : 'text-emerald-500/80 hover:text-emerald-400'"
        @click="levelFilter = 'success'"
      >
        成功 ({{ counts.success }})
      </button>
      <button
        v-if="counts.warning > 0"
        class="px-2 py-0.5 rounded transition-colors flex items-center gap-1"
        :class="levelFilter === 'warning' ? 'bg-amber-900/60 text-amber-300 font-bold border border-amber-700/50' : 'text-amber-500/80 hover:text-amber-400'"
        @click="levelFilter = 'warning'"
      >
        警告 ({{ counts.warning }})
      </button>
      <button
        v-if="counts.error > 0"
        class="px-2 py-0.5 rounded transition-colors flex items-center gap-1"
        :class="levelFilter === 'error' ? 'bg-red-900/60 text-red-300 font-bold border border-red-700/50' : 'text-red-400 hover:text-red-300'"
        @click="levelFilter = 'error'"
      >
        错误 ({{ counts.error }})
      </button>
    </div>

    <!-- Terminal Canvas -->
    <div
      ref="logContainer"
      class="flex-1 overflow-y-auto terminal px-3.5 py-3 relative"
      @scroll="onScroll"
    >
      <!-- Empty state -->
      <div
        v-if="store.logs.length === 0"
        class="flex flex-col items-center justify-center h-full py-16 text-slate-500 font-mono select-none"
      >
        <div class="w-12 h-12 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-center mb-3">
          <span class="text-blue-400 font-bold text-base">&gt;_</span>
        </div>
        <div class="text-xs font-semibold text-slate-400 mb-1">
          终端就绪
        </div>
        <div class="text-[11px] text-slate-600">
          点击“开始执行”后将在此处实时输出任务日志
        </div>
      </div>

      <!-- No search results -->
      <div
        v-else-if="filteredLogs.length === 0"
        class="flex flex-col items-center justify-center py-12 text-slate-500 font-mono text-xs"
      >
        <span>未找到与筛选条件匹配的日志</span>
        <button
          class="mt-2 text-blue-400 underline text-[11px]"
          @click="resetFilters"
        >
          重置筛选
        </button>
      </div>

      <!-- Log Entries -->
      <template
        v-for="(log, i) in filteredLogs"
        :key="i"
      >
        <!-- Lifecycle Banner (=== 开始执行 === / === 执行完成 ===) -->
        <div
          v-if="isBannerLog(log.message)"
          class="log-banner"
          :class="{ success: log.level === 'success' }"
        >
          <span class="log-banner-text">{{ log.message }}</span>
        </div>

        <!-- Normal Log Row -->
        <div
          v-else
          class="log-line"
          :class="log.level"
        >
          <!-- Timestamp -->
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>

          <!-- Project Tag -->
          <span
            v-if="log.project"
            class="log-project"
          >
            {{ log.project }}
          </span>

          <!-- Status Icon -->
          <span
            v-if="log.level === 'success'"
            class="log-icon text-emerald-400"
          >
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </span>
          <span
            v-else-if="log.level === 'error'"
            class="log-icon text-red-400"
          >
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </span>
          <span
            v-else-if="log.level === 'warning'"
            class="log-icon text-amber-400"
          >
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
                d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </span>

          <!-- Message Text with Keyword Highlights -->
          <span
            class="log-msg"
            v-html="highlightMessage(log.message)"
          />
        </div>
      </template>
    </div>

    <!-- Floating Scroll-to-Bottom Button -->
    <transition name="fade">
      <button
        v-if="!autoScroll && store.logs.length > 5"
        class="absolute bottom-4 right-5 z-20 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-600/90 hover:bg-blue-500 text-white text-[11px] font-mono shadow-lg shadow-black/40 backdrop-blur border border-blue-400/40 transition-all transform hover:scale-105"
        @click="scrollToBottomManual"
      >
        <svg
          class="w-3 h-3 animate-bounce"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2.5"
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
        <span>跳至最新日志</span>
      </button>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, nextTick } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useLog } from '@/composables/useLog'

const store = useAppStore()
const { filteredLogs, levelFilter, projectFilter, searchKeyword, counts } = useLog()
const logContainer = ref<HTMLElement>()
const autoScroll = ref(true)
const copied = ref(false)

// Extract unique project names from logs
const logProjects = computed(() => {
  const names = new Set<string>()
  for (const log of store.logs) {
    if (log.project) names.add(log.project)
  }
  return Array.from(names).sort()
})

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${h}:${m}:${s}`
  } catch {
    return ts
  }
}

function isBannerLog(msg: string): boolean {
  return /^[=\-]{3,}.+[=\-]{3,}$/.test(msg.trim())
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function highlightMessage(rawMsg: string): string {
  let escaped = escapeHtml(rawMsg)

  // Highlight SVN revision tags like r12345
  escaped = escaped.replace(/(r\d{3,7})\b/g, '<span style="color:#38bdf8;font-weight:600">$1</span>')

  // Highlight execution durations like 1.23s or 450ms
  escaped = escaped.replace(/(\d+(?:\.\d+)?(?:s|ms|min))\b/g, '<span style="color:#a78bfa">$1</span>')

  // Highlight success keywords
  escaped = escaped.replace(/(成功|完成|PASS|SUCCESS)/g, '<span style="color:#4ade80;font-weight:600">$1</span>')

  // Highlight error keywords
  escaped = escaped.replace(/(失败|错误|ERROR|FAIL|EXCEPTION)/gi, '<span style="color:#f87171;font-weight:600">$1</span>')

  return escaped
}

function resetFilters() {
  projectFilter.value = ''
  levelFilter.value = ''
  searchKeyword.value = ''
}

async function copyAllLogs() {
  if (store.logs.length === 0) return
  const text = store.logs
    .map((l) => `[${formatTime(l.timestamp)}] ${l.project ? `[${l.project}] ` : ''}${l.level.toUpperCase()}: ${l.message}`)
    .join('\n')

  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    store.showToast('已复制全部日志到剪贴板', 'success')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    store.showToast('复制失败，请手动选择复制', 'warning')
  }
}

function scrollToBottomManual() {
  autoScroll.value = true
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function onScroll() {
  if (!logContainer.value) return
  const el = logContainer.value
  // If user is within 30px from bottom, keep autoScroll on
  const isBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 30
  autoScroll.value = isBottom
}

watch(
  () => store.logs.length,
  async () => {
    if (!autoScroll.value) return
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>

