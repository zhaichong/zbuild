<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-xs"
        @click="visible = false"
      />
      <div
        class="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl z-10 flex flex-col overflow-hidden border border-slate-200 text-slate-800"
        style="height: 80vh; max-height: 680px;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white shrink-0">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-base font-bold">
              🚀
            </div>
            <div>
              <h2 class="text-base font-bold text-slate-900 leading-tight">测试订单部署 — 独立模块配置</h2>
              <p class="text-xs text-slate-400">独立管理 SVN 目录源、目标服务器凭据及各前端包解压部署路径</p>
            </div>
          </div>
          <button
            class="text-slate-400 hover:text-slate-600 transition-colors p-1.5 rounded-lg hover:bg-slate-100 cursor-pointer"
            @click="visible = false"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Main Body (Scrollable) -->
        <div class="flex-1 min-h-0 overflow-y-auto p-6 space-y-5 bg-slate-50/50">
          
          <!-- Section 1: SVN 目录源管理 (可配置多个源) -->
          <div class="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-2xs">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-blue-500" />
                <h4 class="text-xs font-bold text-slate-800">常用 SVN 目录源管理 (多源配置)</h4>
              </div>
              <button
                type="button"
                class="px-2.5 py-1 text-xs text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg font-medium flex items-center gap-1 transition-colors cursor-pointer"
                @click="showAddSvnLocModal = !showAddSvnLocModal"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                添加 SVN 目录源
              </button>
            </div>

            <!-- Inline Add Form -->
            <div
              v-if="showAddSvnLocModal"
              class="flex flex-wrap items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-blue-200"
            >
              <input
                v-model="newSvnLocName"
                type="text"
                class="w-36 px-2.5 py-1.5 text-xs border border-slate-300 rounded-md bg-white text-slate-800 outline-none focus:border-blue-500"
                placeholder="源名称 (如 特殊订单)"
                @keyup.enter="confirmAddSvnLocation"
              >
              <input
                v-model="newSvnLocUrl"
                type="text"
                class="flex-1 min-w-[10rem] px-2.5 py-1.5 text-xs font-mono border border-slate-300 rounded-md bg-white text-slate-800 outline-none focus:border-blue-500"
                placeholder="https://10.1.1.120/svn/..."
                @keyup.enter="confirmAddSvnLocation"
              >
              <button
                type="button"
                class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-opacity cursor-pointer font-semibold"
                @click="confirmAddSvnLocation"
              >
                添加
              </button>
              <button
                type="button"
                class="px-2.5 py-1.5 text-xs border border-slate-300 bg-white text-slate-600 rounded-md hover:bg-slate-50 transition-colors cursor-pointer"
                @click="showAddSvnLocModal = false"
              >
                取消
              </button>
            </div>

            <!-- List -->
            <div class="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              <div
                v-for="(loc, idx) in localConfig.svnLocations"
                :key="loc.id || idx"
                class="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 transition-colors"
              >
                <input
                  v-model="loc.name"
                  type="text"
                  class="w-32 px-2 py-0.5 text-xs font-semibold border border-transparent hover:border-slate-300 focus:border-blue-500 rounded bg-transparent outline-none"
                  placeholder="源名称"
                >
                <input
                  v-model="loc.url"
                  type="text"
                  class="flex-1 min-w-0 px-2 py-0.5 text-xs font-mono border border-transparent hover:border-slate-300 focus:border-blue-500 rounded bg-white outline-none"
                  placeholder="SVN URL"
                >
                <button
                  type="button"
                  class="px-2 py-0.5 text-[11px] rounded transition-colors cursor-pointer shrink-0"
                  :class="localConfig.currentSvnUrl === loc.url ? 'bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200' : 'bg-slate-200 text-slate-600 hover:bg-blue-50 hover:text-blue-600'"
                  :title="localConfig.currentSvnUrl === loc.url ? '当前选中的目录源' : '设为默认选中源'"
                  @click="setDefaultSvnLocation(loc)"
                >
                  {{ localConfig.currentSvnUrl === loc.url ? '当前默认' : '设为默认' }}
                </button>
                <button
                  type="button"
                  class="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors shrink-0 cursor-pointer"
                  title="删除此目录源"
                  @click="removeSvnLocation(idx)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              <div v-if="!localConfig.svnLocations || localConfig.svnLocations.length === 0" class="text-center py-3 text-xs text-slate-400">
                暂无自定义目录源
              </div>
            </div>

            <!-- SVN 认证凭据 (独立) -->
            <div class="grid grid-cols-2 gap-3 pt-2.5 border-t border-slate-100">
              <div>
                <label class="block text-[11px] text-slate-500 mb-1">SVN 账号 (可选)</label>
                <input
                  v-model="localConfig.svnUsername"
                  type="text"
                  class="w-full form-input text-xs"
                  placeholder="留空则读取系统全局凭据"
                >
              </div>
              <div>
                <label class="block text-[11px] text-slate-500 mb-1">SVN 密码 (可选)</label>
                <input
                  v-model="localConfig.svnPassword"
                  type="password"
                  class="w-full form-input text-xs"
                  placeholder="留空则读取系统全局凭据"
                >
              </div>
            </div>
          </div>

          <!-- Section 2: 前端包解压与部署目标路径映射 (独立) -->
          <div class="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-2xs">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-xs font-bold text-slate-800">前端包解压到服务器的路径映射</h4>
                <p class="text-[11px] text-slate-400">当识别到对应前端包名时，自动将其解压覆盖到服务器指定的部署目录</p>
              </div>
              <button
                type="button"
                class="px-2.5 py-1 text-xs text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg font-medium flex items-center gap-1 transition-colors cursor-pointer"
                @click="showAddPkgModal = !showAddPkgModal"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                添加包映射
              </button>
            </div>

            <!-- Inline Add Pkg Path Form -->
            <div
              v-if="showAddPkgModal"
              class="flex items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-blue-200"
            >
              <input
                v-model="newPkgName"
                type="text"
                class="w-44 px-2.5 py-1.5 text-xs border border-slate-300 rounded-md bg-white text-slate-800 outline-none focus:border-blue-500"
                placeholder="包/项目名 (如 yarward-web-frontend)"
                @keyup.enter="confirmAddPkgPath"
              >
              <input
                v-model="newPkgPath"
                type="text"
                class="flex-1 px-2.5 py-1.5 text-xs font-mono border border-slate-300 rounded-md bg-white text-slate-800 outline-none focus:border-blue-500"
                placeholder="服务器目标路径 (如 /home/data/web)"
                @keyup.enter="confirmAddPkgPath"
              >
              <button
                type="button"
                class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-opacity cursor-pointer font-semibold"
                @click="confirmAddPkgPath"
              >
                添加
              </button>
              <button
                type="button"
                class="px-2.5 py-1.5 text-xs border border-slate-300 bg-white text-slate-600 rounded-md hover:bg-slate-50 transition-colors cursor-pointer"
                @click="showAddPkgModal = false"
              >
                取消
              </button>
            </div>

            <!-- List -->
            <div class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              <div
                v-for="(_, pkgName) in localConfig.packageUploadPaths"
                :key="pkgName"
                class="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 transition-colors"
              >
                <span class="text-xs font-semibold text-slate-800 w-44 truncate shrink-0" :title="String(pkgName)">
                  {{ pkgName }}
                </span>
                <input
                  v-model="localConfig.packageUploadPaths[pkgName]"
                  type="text"
                  class="flex-1 px-2.5 py-1 text-xs font-mono border border-slate-200 rounded-md bg-white text-slate-700 focus:border-blue-500 outline-none"
                  placeholder="/home/data/web"
                >
                <button
                  type="button"
                  class="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors shrink-0 cursor-pointer"
                  title="删除此包路径映射"
                  @click="removePkgPath(String(pkgName))"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between px-6 py-3.5 border-t border-slate-100 bg-white shrink-0">
          <div class="text-[11px] text-slate-400">
            💡 本模块配置完全独立存储，不会影响智慧病房构建主工具
          </div>
          <div class="flex items-center gap-2.5">
            <button
              class="px-4 py-1.5 text-xs border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
              @click="visible = false"
            >
              取消
            </button>
            <button
              class="px-5 py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-opacity shadow-sm flex items-center gap-1.5 cursor-pointer"
              @click="onSave"
            >
              保存配置
            </button>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { SvnLocationItem } from '@/types'

const store = useAppStore()
const visible = ref(false)

const showAddSvnLocModal = ref(false)
const newSvnLocName = ref('')
const newSvnLocUrl = ref('')

const showAddPkgModal = ref(false)
const newPkgName = ref('')
const newPkgPath = ref('/home/data/web')

const DEFAULT_PACKAGE_UPLOAD_PATHS: Record<string, string> = {
  'yarward-ntv-frontend': '/home/data/web',
  'yarward-web-frontend': '/home/data/web',
  'zbuild': '/home/data/web',
  'zhbf-bedhead-frontend': '/home/data/web/a10',
  'zhbf-fontend': '/home/data/web/a10',
  'zhbf-frontend': '/home/data/web/a10',
  'zhbf-web': '/home/data/web',
}

const DEFAULT_SVN_LOCATIONS: SvnLocationItem[] = [
  {
    id: 'loc-default',
    name: '特殊订单仓库',
    url: 'https://10.1.1.120/svn/智慧病房特殊订单',
    isDefault: true,
  },
]

const localConfig = reactive({
  svnLocations: [] as SvnLocationItem[],
  currentSvnUrl: '',
  svnUsername: '',
  svnPassword: '',
  serverAddress: '192.168.31.202',
  serverUsername: 'yahua',
  serverPassword: '',
  packageUploadPaths: {} as Record<string, string>,
})

const emit = defineEmits<{
  'saved': [config: typeof localConfig]
}>()

function loadFromStorage() {
  const raw = localStorage.getItem('zbuild_order_deploy_config')
  if (raw) {
    try {
      const parsed = JSON.parse(raw)
      localConfig.svnLocations = parsed.svnLocations || [...DEFAULT_SVN_LOCATIONS]
      localConfig.currentSvnUrl = parsed.currentSvnUrl || localConfig.svnLocations[0]?.url || ''
      localConfig.svnUsername = parsed.svnUsername || ''
      localConfig.svnPassword = parsed.svnPassword || ''
      localConfig.serverAddress = parsed.serverAddress || '192.168.31.202'
      localConfig.serverUsername = parsed.serverUsername || 'yahua'
      localConfig.serverPassword = parsed.serverPassword || ''
      localConfig.packageUploadPaths = parsed.packageUploadPaths || { ...DEFAULT_PACKAGE_UPLOAD_PATHS }
      return
    } catch (_) {}
  }

  // Initial defaults
  localConfig.svnLocations = [...DEFAULT_SVN_LOCATIONS]
  localConfig.currentSvnUrl = DEFAULT_SVN_LOCATIONS[0].url
  localConfig.packageUploadPaths = { ...DEFAULT_PACKAGE_UPLOAD_PATHS }
}

watch(visible, (val) => {
  if (val) {
    loadFromStorage()
  }
})

function confirmAddSvnLocation() {
  const name = newSvnLocName.value.trim()
  const url = newSvnLocUrl.value.trim()
  if (!name || !url) {
    store.showToast('请输入名称与 SVN 目录地址', 'warning')
    return
  }
  localConfig.svnLocations.push({
    id: 'loc-' + Date.now(),
    name,
    url,
  })
  if (localConfig.svnLocations.length === 1) {
    localConfig.currentSvnUrl = url
  }
  newSvnLocName.value = ''
  newSvnLocUrl.value = ''
  showAddSvnLocModal.value = false
}

function removeSvnLocation(idx: number) {
  localConfig.svnLocations.splice(idx, 1)
}

function setDefaultSvnLocation(loc: SvnLocationItem) {
  localConfig.currentSvnUrl = loc.url
  store.showToast(`已设为默认源: ${loc.name}`, 'success')
}

function confirmAddPkgPath() {
  const name = newPkgName.value.trim()
  const path = newPkgPath.value.trim() || '/home/data/web'
  if (!name) {
    store.showToast('请输入前端包/项目名称', 'warning')
    return
  }
  localConfig.packageUploadPaths[name] = path
  newPkgName.value = ''
  newPkgPath.value = '/home/data/web'
  showAddPkgModal.value = false
}

function removePkgPath(name: string) {
  delete localConfig.packageUploadPaths[name]
}

function onSave() {
  localStorage.setItem('zbuild_order_deploy_config', JSON.stringify(localConfig))
  emit('saved', localConfig)
  visible.value = false
  store.showToast('测试订单部署模块配置已保存', 'success')
}

function open() {
  loadFromStorage()
  visible.value = true
}

defineExpose({
  open,
  visible,
  localConfig,
})
</script>
