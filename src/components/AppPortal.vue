<template>
  <div class="flex-1 min-h-0 overflow-y-auto bg-slate-50 p-6 sm:p-8">
    <div class="max-w-6xl mx-auto space-y-6">
      <!-- Top Banner -->
      <div class="bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-800 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs text-blue-200 font-medium mb-3">
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
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                />
              </svg>
              <span>开发者应用中心 & 工具矩阵</span>
            </div>
            <h2 class="text-2xl font-bold tracking-tight mb-2">
              工作台应用大厅 (App Portal)
            </h2>
            <p class="text-sm text-blue-200/90 max-w-xl leading-relaxed">
              集中管理与调度医疗项目构建、部署、测试单生成及自动化辅助工具。支持灵活扩展添加自定义应用。
            </p>
          </div>
          <button
            type="button"
            class="self-start md:self-auto px-4 py-2.5 bg-white text-blue-900 hover:bg-blue-50 font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer shrink-0"
            @click="showAddAppModal = true"
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            添加自定义应用
          </button>
        </div>

        <!-- Decorative background glow -->
        <div class="absolute -right-10 -bottom-10 w-60 h-60 rounded-full bg-blue-500/20 blur-3xl pointer-events-none" />
      </div>

      <!-- App Grid Section -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span>已集成应用与工具</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-600 font-normal">({{ apps.length }})</span>
          </h3>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <!-- App Cards -->
          <div
            v-for="app in apps"
            :key="app.id"
            class="group bg-white border border-slate-200/80 hover:border-blue-400 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all duration-200 flex flex-col justify-between"
          >
            <div>
              <div class="flex items-start justify-between mb-3">
                <div
                  class="w-12 h-12 rounded-xl flex items-center justify-center text-xl shadow-xs shrink-0"
                  :class="app.bgColor || 'bg-blue-50 text-blue-600 border border-blue-100'"
                >
                  <span>{{ app.icon }}</span>
                </div>
                <span
                  class="text-[11px] font-medium px-2.5 py-0.5 rounded-full"
                  :class="app.status === 'active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500 border border-slate-200'"
                >
                  {{ app.statusLabel || (app.status === 'active' ? '已就绪' : '扩展模组') }}
                </span>
              </div>

              <h4 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors mb-1.5">
                {{ app.name }}
              </h4>
              <p class="text-xs text-slate-500 leading-relaxed mb-4 line-clamp-2">
                {{ app.description }}
              </p>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span class="text-[11px] text-slate-400 font-mono">{{ app.category || '内部工具' }}</span>
              <button
                type="button"
                class="px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 cursor-pointer"
                :class="app.status === 'active' ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-2xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                @click="onLaunchApp(app)"
              >
                <span>{{ app.status === 'active' ? '打开应用' : '启动/查看' }}</span>
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
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- Add Application Dashed Card -->
          <div
            class="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all hover:bg-blue-50/30 group min-h-[190px]"
            @click="showAddAppModal = true"
          >
            <div class="w-10 h-10 rounded-full bg-slate-100 group-hover:bg-blue-100 text-slate-400 group-hover:text-blue-600 flex items-center justify-center mb-3 transition-colors">
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
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </div>
            <span class="text-xs font-bold text-slate-700 group-hover:text-blue-600 transition-colors mb-1">
              添加第三方应用 / 脚本
            </span>
            <span class="text-[11px] text-slate-400 max-w-[200px]">
              支持关联本地可执行程序、网页链接或快捷命令入口
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Custom App Modal -->
    <teleport to="body">
      <div
        v-if="showAddAppModal"
        class="fixed inset-0 z-[9999] bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4"
      >
        <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
          <div class="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 class="text-sm font-bold text-slate-800">
              添加自定义扩展应用
            </h3>
            <button
              class="text-slate-400 hover:text-slate-600"
              @click="showAddAppModal = false"
            >
              ✕
            </button>
          </div>

          <div class="space-y-3 text-xs">
            <div>
              <label class="block text-slate-600 mb-1 font-medium">应用名称</label>
              <input
                v-model="newApp.name"
                type="text"
                class="form-input w-full"
                placeholder="例如: 接口 Mock 服务"
              >
            </div>
            <div>
              <label class="block text-slate-600 mb-1 font-medium">应用图标 (Emoji 或 缩写)</label>
              <input
                v-model="newApp.icon"
                type="text"
                class="form-input w-full"
                placeholder="例如: 🚀 或 API"
              >
            </div>
            <div>
              <label class="block text-slate-600 mb-1 font-medium">应用描述</label>
              <textarea
                v-model="newApp.description"
                rows="2"
                class="form-input w-full"
                placeholder="输入该应用的功能简介..."
              />
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              class="px-3.5 py-1.5 text-xs rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
              @click="showAddAppModal = false"
            >
              取消
            </button>
            <button
              type="button"
              class="px-4 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'

export interface PortalApp {
  id: string
  name: string
  description: string
  icon: string
  category: string
  status: 'active' | 'extension'
  statusLabel?: string
  bgColor?: string
}

const emit = defineEmits<{
  'launch-app': [appId: string]
}>()

const store = useAppStore()
const showAddAppModal = ref(false)

const newApp = ref({
  name: '',
  icon: '🛠️',
  description: '',
})

const apps = ref<PortalApp[]>([
  {
    id: 'zbuild',
    name: '特殊订单打包上传工具',
    description: '自动化项目打包、多目录产物匹配、SVN 订单上传、远程服务器部署及官方提测单自动生成。',
    icon: '📦',
    category: '核心工具',
    status: 'active',
    statusLabel: '已集成 / 运行中',
    bgColor: 'bg-blue-50 text-blue-600 border border-blue-100',
  },
  {
    id: 'mock-query',
    name: '终端数据链路提取控制台',
    description: '跨接口终端数据自动匹配提取，包含机构、护理单元、床头卡与患者信息抓取与组装。',
    icon: '⚡',
    category: '调试工具',
    status: 'active',
    statusLabel: '已集成 / 内置原生',
    bgColor: 'bg-amber-50 text-amber-600 border border-amber-100',
  },
  {
    id: 'conflict-checker',
    name: '代码分支比对与冲突检测',
    description: '智能扫描多项目 Git 依赖分支、未合并 Commit 差异及本地改动冲突预警。',
    icon: '🌿',
    category: '代码开发',
    status: 'extension',
    statusLabel: '预置模组',
    bgColor: 'bg-indigo-50 text-indigo-600 border border-indigo-100',
  },
  {
    id: 'excel-archive',
    name: '提测单与归档记录管理',
    description: '快捷检索、历史查看及离线导出已生成的订单 Excel 提测件与构建记录。',
    icon: '📊',
    category: '提测管理',
    status: 'extension',
    statusLabel: '预置模组',
    bgColor: 'bg-emerald-50 text-emerald-600 border border-emerald-100',
  },
  {
    id: 'mock-server',
    name: '医疗设备联调 Mock 服务',
    description: '针对智慧病房床头卡、呼叫主机及 Web 端的轻量化 HTTP/WebSocket 模拟响应。',
    icon: '⚙️',
    category: '调试工具',
    status: 'extension',
    statusLabel: '预置模组',
    bgColor: 'bg-slate-100 text-slate-600 border border-slate-200',
  },
])

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
    description: newApp.value.description.trim() || '自定义扩展工具',
    icon: newApp.value.icon || '🛠️',
    category: '自定义扩展',
    status: 'extension',
    statusLabel: '自定义组件',
    bgColor: 'bg-slate-100 text-slate-700 border border-slate-200',
  })
  newApp.value = { name: '', icon: '🛠️', description: '' }
  showAddAppModal.value = false
  store.showToast('成功添加自定义应用入口', 'success')
}
</script>
