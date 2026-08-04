<template>
  <div class="flex-1 min-h-0 overflow-y-auto bg-[#f1f5f9] p-5 sm:p-6 text-slate-800 font-sans">
    <div class="max-w-6xl mx-auto space-y-4">
      
      <!-- Top Banner / Header Card (Matches Tool Design System) -->
      <div class="card p-5 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-blue-600 shadow-2xs">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-base font-bold text-slate-900">开发者中心与应用工作台</span>
            <span class="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 text-[11px] font-mono font-bold">v2.0</span>
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-medium">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              内部服务正常
            </span>
          </div>
          <p class="text-xs text-slate-500 leading-relaxed">
            集中调度智慧病房项目自动化构建打包、SVN/远程部署发布、终端链路抓取以及数据库造数控制台。
          </p>
        </div>

        <button
          type="button"
          class="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-lg transition-colors cursor-pointer shrink-0 flex items-center gap-1.5 shadow-2xs"
          @click="showAddAppModal = true"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>添加自定义扩展</span>
        </button>
      </div>



      <!-- Filter Controls Row -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        <!-- Category Filter -->
        <div class="flex items-center gap-1 bg-white p-1 rounded-xl border border-slate-200 shadow-2xs">
          <button
            v-for="cat in categories"
            :key="cat.value"
            type="button"
            class="px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer select-none"
            :class="selectedCategory === cat.value ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'"
            @click="selectedCategory = cat.value"
          >
            {{ cat.label }}
          </button>
        </div>

        <!-- Search Input -->
        <div class="relative w-full sm:w-64">
          <svg class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索工具或扩展应用..."
            class="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 outline-none focus:border-blue-500 transition-all font-sans shadow-2xs"
          >
        </div>
      </div>

      <!-- App Cards Grid (Tool Shared Card Style) -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Main Tool Cards -->
        <div
          v-for="app in filteredApps"
          :key="app.id"
          class="card p-5 bg-white hover:border-blue-400 transition-all duration-200 flex flex-col justify-between group cursor-pointer hover:shadow-md"
          @click="onLaunchApp(app)"
        >
          <div>
            <!-- Top Icon & Status -->
            <div class="flex items-start justify-between mb-3">
              <div
                class="w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 border"
                :class="app.iconBg || 'bg-blue-50 text-blue-600 border-blue-100'"
              >
                <span v-if="app.iconType === 'build'">📦</span>
                <span v-else-if="app.iconType === 'data'">⚡</span>
                <span v-else>{{ app.icon }}</span>
              </div>

              <span
                class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border"
                :class="app.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-600 border-slate-200'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="app.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400'" />
                {{ app.statusLabel || (app.status === 'active' ? '就绪' : '扩展') }}
              </span>
            </div>

            <!-- Title & Description -->
            <h3 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors mb-1.5">
              {{ app.name }}
            </h3>
            <p class="text-xs text-slate-500 leading-relaxed mb-4 line-clamp-2">
              {{ app.description }}
            </p>

            <!-- Feature Badges -->
            <div class="flex flex-wrap gap-1 mb-4">
              <span
                v-for="tag in app.tags"
                :key="tag"
                class="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-[11px] text-slate-600 font-mono"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- Bottom Action -->
          <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-[11px] font-medium text-slate-400">{{ app.category }}</span>

            <button
              type="button"
              class="px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors cursor-pointer flex items-center gap-1 shadow-2xs"
              @click.stop="onLaunchApp(app)"
            >
              <span>进入应用</span>
              <svg class="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Dashed Add Card -->
        <div
          class="card p-5 border-2 border-dashed border-slate-300 hover:border-blue-400 bg-white/70 hover:bg-white transition-all flex flex-col items-center justify-center text-center cursor-pointer min-h-[200px] group"
          @click="showAddAppModal = true"
        >
          <div class="w-10 h-10 rounded-lg bg-slate-100 text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600 border border-slate-200 flex items-center justify-center mb-2.5 transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <span class="text-xs font-bold text-slate-800 group-hover:text-blue-600 transition-colors mb-1">
            添加第三方应用 / 扩展入口
          </span>
          <span class="text-[11px] text-slate-400 max-w-[200px] leading-relaxed">
            关联本地可执行快捷方式、网页链接或工具脚本
          </span>
        </div>
      </div>

    </div>

    <!-- Add Custom App Modal -->
    <teleport to="body">
      <div
        v-if="showAddAppModal"
        class="fixed inset-0 z-[9999] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4"
      >
        <div class="bg-white rounded-xl border border-slate-200 max-w-md w-full p-5 shadow-xl space-y-3 text-slate-800">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <h3 class="text-sm font-bold text-slate-900">
              添加自定义扩展应用
            </h3>
            <button
              class="text-slate-400 hover:text-slate-600 cursor-pointer"
              @click="showAddAppModal = false"
            >
              ✕
            </button>
          </div>

          <div class="space-y-2.5 text-xs">
            <div>
              <label class="block text-slate-600 mb-1 font-medium">应用名称</label>
              <input
                v-model="newApp.name"
                type="text"
                class="w-full px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs outline-none focus:border-blue-500"
                placeholder="例如: 接口 Mock 抓包工具"
              >
            </div>
            <div>
              <label class="block text-slate-600 mb-1 font-medium">应用类别</label>
              <select
                v-model="newApp.category"
                class="w-full px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs outline-none focus:border-blue-500"
              >
                <option value="核心构建">核心构建</option>
                <option value="调试造数">调试造数</option>
                <option value="扩展应用">扩展应用</option>
              </select>
            </div>
            <div>
              <label class="block text-slate-600 mb-1 font-medium">功能说明描述</label>
              <textarea
                v-model="newApp.description"
                rows="2"
                class="w-full px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs outline-none focus:border-blue-500"
                placeholder="简要说明该扩展工具的功用..."
              />
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2.5 border-t border-slate-100">
            <button
              type="button"
              class="px-3 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer"
              @click="showAddAppModal = false"
            >
              取消
            </button>
            <button
              type="button"
              class="px-3.5 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer shadow-2xs"
              @click="confirmAddApp"
            >
              添加应用
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'

export interface PortalApp {
  id: string
  name: string
  description: string
  icon: string
  iconType?: 'build' | 'data' | 'custom'
  category: string
  tags?: string[]
  status: 'active' | 'extension'
  statusLabel?: string
  iconBg?: string
}

const emit = defineEmits<{
  'launch-app': [appId: string]
}>()

const store = useAppStore()
const showAddAppModal = ref(false)
const selectedCategory = ref<string>('all')
const searchQuery = ref<string>('')

const categories = [
  { label: '全部工具', value: 'all' },
  { label: '核心构建', value: '核心构建' },
  { label: '调试造数', value: '调试造数' },
  { label: '扩展应用', value: '扩展应用' },
]

const newApp = ref({
  name: '',
  icon: '🛠️',
  category: '扩展应用',
  description: '',
})

const apps = ref<PortalApp[]>([
  {
    id: 'zbuild',
    name: '智慧病房系统构建与调试工具',
    description: '支持多医疗子系统自动化编译打包、多目录产物匹配、SVN 需求清单生成、远程服务器部署与提测发布。',
    icon: '📦',
    iconType: 'build',
    category: '核心构建',
    tags: ['Electron', 'SVN', 'SSH 部署', '多工程模版'],
    status: 'active',
    statusLabel: '就绪',
    iconBg: 'bg-blue-50 text-blue-600 border-blue-100',
  },
  {
    id: 'mock-query',
    name: '终端数据链路提取控制台',
    description: '跨接口终端设备链路数据代理提取，自动抓取机构、护理单元与患者数据，支持数据库全类型增量造数。',
    icon: '⚡',
    iconType: 'data',
    category: '调试造数',
    tags: ['MySQL 直连', '跨域代理', '自动组装', '6 大数据模版'],
    status: 'active',
    statusLabel: '内置',
    iconBg: 'bg-amber-50 text-amber-600 border-amber-100',
  },
])

const filteredApps = computed(() => {
  return apps.value.filter((app) => {
    const matchesCategory =
      selectedCategory.value === 'all' ||
      (selectedCategory.value === '扩展应用' ? app.status === 'extension' : app.category === selectedCategory.value)

    const matchesSearch =
      !searchQuery.value.trim() ||
      app.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.value.toLowerCase())

    return matchesCategory && matchesSearch
  })
})

function onLaunchApp(app: PortalApp) {
  if (app.id === 'zbuild') {
    emit('launch-app', 'zbuild')
  } else if (app.id === 'mock-query') {
    emit('launch-app', 'mock-query')
  } else {
    store.showToast(`已拉起「${app.name}」扩展环境`, 'info')
  }
}

function confirmAddApp() {
  if (!newApp.value.name.trim()) {
    store.showToast('请输入应用名称', 'warning')
    return
  }
  apps.value.push({
    id: 'custom-' + Date.now(),
    name: newApp.value.name.trim(),
    description: newApp.value.description.trim() || '自定义扩展工具入口',
    icon: newApp.value.icon || '🛠️',
    iconType: 'custom',
    category: newApp.value.category || '扩展应用',
    tags: ['自定义扩展', '脚本入口'],
    status: 'extension',
    statusLabel: '扩展',
    iconBg: 'bg-purple-50 text-purple-600 border-purple-100',
  })
  newApp.value = { name: '', icon: '🛠️', category: '扩展应用', description: '' }
  showAddAppModal.value = false
  store.showToast('成功添加自定义应用入口', 'success')
}
</script>
