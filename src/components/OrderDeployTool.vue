<template>
  <div class="app-shell flex-1 min-h-0">
    <!-- Left: Main column (Top fixed, Bottom fixed, Middle scrollable) -->
    <div class="main-col flex flex-col h-full overflow-hidden p-3 gap-2.5">
      
      <!-- Top Fixed: 订单信息 & 服务器配置 -->
      <div class="card p-3 space-y-2 shrink-0">
        <!-- Row 1: 订单信息与 SVN 控制 -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-end">
          <!-- 医院名称 -->
          <div class="md:col-span-4 flex flex-col gap-1 min-w-0">
            <label class="text-[11px] font-semibold text-text-2 flex items-center gap-1">
              <span>医院名称</span>
            </label>
            <div class="flex gap-1">
              <input
                v-model="hospitalName"
                type="text"
                class="form-input flex-1 min-w-0 py-1 px-2.5 text-xs"
                placeholder="例如: 北京中能建医院"
                @keyup.enter="loadTree"
              >
              <button
                class="px-2.5 py-1 rounded-lg border border-border bg-white text-text-3 hover:text-primary hover:border-primary/40 transition-colors flex items-center shrink-0 cursor-pointer shadow-2xs"
                title="从 SVN 浏览选择医院"
                :disabled="loadingTree"
                @click="pickHospital"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 订单号 -->
          <div class="md:col-span-3 flex flex-col gap-1 min-w-0">
            <label class="text-[11px] font-semibold text-text-2 flex items-center gap-1">
              <span>订单号</span>
            </label>
            <div class="flex gap-1">
              <input
                v-model="orderNo"
                type="text"
                class="form-input flex-1 min-w-0 py-1 px-2.5 text-xs"
                placeholder="例如: 2026-1437"
                @keyup.enter="loadTree"
              >
              <button
                class="px-2.5 py-1 rounded-lg border border-border bg-white text-text-3 hover:text-primary hover:border-primary/40 transition-colors flex items-center shrink-0 cursor-pointer shadow-2xs"
                title="从 SVN 浏览选择订单号"
                :disabled="loadingTree"
                @click="pickOrder"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- SVN 目录源 & 模块设置 -->
          <div class="md:col-span-3 flex flex-col gap-1 min-w-0">
            <div class="flex items-center justify-between">
              <label class="text-[11px] font-semibold text-text-2">SVN 目录源</label>
              <button
                type="button"
                class="text-[11px] text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5 cursor-pointer"
                title="管理 SVN 多源与解压路径配置"
                @click="openSettings"
              >
                <span>⚙️ 模块配置</span>
              </button>
            </div>
            <select
              v-model="currentSvnUrl"
              class="form-input py-1 px-2 text-xs truncate"
              @change="onSvnUrlChanged"
            >
              <option
                v-for="loc in svnLocationOptions"
                :key="loc.id"
                :value="loc.url"
              >
                {{ loc.name }}
              </option>
            </select>
          </div>

          <!-- 读取/刷新文件按钮 -->
          <div class="md:col-span-2 flex items-end">
            <button
              type="button"
              class="w-full h-[30px] bg-primary hover:opacity-90 text-white rounded-lg font-semibold text-xs flex items-center justify-center gap-1.5 cursor-pointer shadow-2xs transition-all disabled:opacity-50"
              :disabled="loadingTree || !computedOrderSvnUrl"
              @click="loadTree"
            >
              <svg v-if="!loadingTree" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{{ loadingTree ? '读取中...' : '读取文件' }}</span>
            </button>
          </div>
        </div>

        <!-- Row 2: 服务器配置 (精简同行) -->
        <div class="pt-2 border-t border-border/50 grid grid-cols-1 md:grid-cols-12 gap-2.5 items-end">
          <!-- 服务器地址 -->
          <div class="md:col-span-4 flex flex-col gap-1 min-w-0">
            <label class="text-[11px] font-semibold text-text-2 flex items-center gap-1">
              <span class="text-primary text-[10px]">🔒</span>
              <span>服务器地址</span>
            </label>
            <input
              v-model="serverAddress"
              type="text"
              class="form-input font-mono py-1 px-2.5 text-xs"
              placeholder="192.168.31.202"
            >
          </div>

          <!-- 用户名 -->
          <div class="md:col-span-3 flex flex-col gap-1 min-w-0">
            <label class="text-[11px] font-semibold text-text-2">用户名</label>
            <input
              v-model="serverUsername"
              type="text"
              class="form-input py-1 px-2.5 text-xs"
              placeholder="yahua"
            >
          </div>

          <!-- 密码 -->
          <div class="md:col-span-3 flex flex-col gap-1 min-w-0">
            <label class="text-[11px] font-semibold text-text-2">密码</label>
            <input
              v-model="serverPassword"
              type="password"
              class="form-input py-1 px-2.5 text-xs"
              placeholder="••••••••••"
            >
          </div>

          <!-- 测试连接按钮 + 状态 -->
          <div class="md:col-span-2 flex items-center gap-1.5">
            <button
              type="button"
              class="flex-1 h-[30px] bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 text-xs font-semibold rounded-lg transition-all cursor-pointer shadow-2xs flex items-center justify-center gap-1"
              :disabled="testingServer"
              @click="onTestServer"
            >
              <svg v-if="testingServer" class="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{{ testingServer ? '测试中' : '测试连接' }}</span>
            </button>

            <!-- 结果徽章 -->
            <span
              v-if="testResultMsg"
              class="text-[10px] px-1.5 py-1 rounded font-mono font-bold shrink-0 truncate max-w-[80px]"
              :class="testResultOk ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'"
              :title="testResultMsg"
            >
              {{ testResultOk ? '✓ 成功' : '✕ 失败' }}
            </span>
          </div>
        </div>

        <!-- Row 3: SVN 路径小字预览 -->
        <div v-if="computedOrderSvnUrl" class="text-[10.5px] font-mono text-text-3 truncate pt-1 border-t border-border/40 flex items-center gap-1">
          <span class="font-sans font-medium text-slate-400 shrink-0">SVN 路径:</span>
          <span class="text-blue-600 truncate" :title="computedOrderSvnUrl">{{ computedOrderSvnUrl }}</span>
        </div>
      </div>

      <!-- Middle Flex-1 Card: 目录与文件树状展示 (独立纵向滚动) -->
      <div class="card p-3 flex-1 min-h-0 flex flex-col overflow-hidden">
        <!-- 列表头部工具栏 (固定) -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-border/60 shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-text-1">订单文件与前端包列表</span>
            <span class="text-[11px] text-text-3 font-mono">
              (共 {{ flatList.length }} 项，已选 {{ selectedCount }} 个部署包)
            </span>
          </div>

          <!-- 批量操作按钮组 -->
          <div class="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              class="px-2 py-0.5 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-50 transition-colors cursor-pointer shadow-2xs"
              @click="selectAll(true)"
            >
              全选
            </button>
            <button
              type="button"
              class="px-2 py-0.5 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-50 transition-colors cursor-pointer shadow-2xs"
              @click="selectAll(false)"
            >
              取消全选
            </button>
            <button
              type="button"
              class="px-2.5 py-0.5 text-xs bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 rounded-lg font-semibold transition-colors cursor-pointer shadow-2xs"
              @click="smartSelectFrontend"
            >
              智能选择前端包
            </button>
            <button
              type="button"
              class="px-2 py-0.5 text-xs border border-border rounded-lg bg-white text-text-3 hover:text-text-1 hover:bg-slate-50 transition-colors cursor-pointer shadow-2xs"
              @click="toggleExpandAll"
            >
              {{ isAllExpanded ? '折叠全部' : '展开全部' }}
            </button>
          </div>
        </div>

        <!-- 树形列表容器 (自适应占满并带独立平滑滚动) -->
        <div class="mt-2 border border-border/70 rounded-xl overflow-hidden bg-slate-50/40 flex-1 min-h-0 flex flex-col">
          <!-- 树形表头 (固定) -->
          <div class="grid grid-cols-12 gap-2 px-3 py-1.5 bg-slate-100/90 border-b border-border/70 text-[11px] font-bold text-text-2 select-none shrink-0">
            <div class="col-span-6 sm:col-span-5 flex items-center gap-2">
              <span>文件/目录名称</span>
            </div>
            <div class="col-span-2 sm:col-span-2 text-center">
              <span>文件大小</span>
            </div>
            <div class="col-span-4 sm:col-span-3">
              <span>目标部署路径 (解压至)</span>
            </div>
            <div class="col-span-12 sm:col-span-2 flex items-center justify-end gap-3 text-right">
              <span>选择/操作</span>
            </div>
          </div>

          <!-- 树形节点滚动区域 (独立纵向滚动) -->
          <div v-if="treeData.length > 0" class="divide-y divide-border/40 flex-1 min-h-0 overflow-y-auto p-1 bg-white">
            <template v-for="node in treeData" :key="node.id">
              <TreeNodeRow
                :node="node"
                :depth="0"
                :expanded-keys="expandedKeys"
                :selected-map="selectedMap"
                :target-paths="customTargetPaths"
                @toggle-expand="toggleExpand"
                @toggle-select="toggleNodeSelect"
                @select-only="selectOnlyNode"
                @update-path="updateTargetPath"
                @open-file="onOpenFile"
              />
            </template>
          </div>

          <!-- 空状态 -->
          <div v-else-if="!loadingTree" class="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white">
            <div class="w-10 h-10 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mb-2 text-lg">
              📂
            </div>
            <div class="text-xs font-semibold text-text-2">暂无文件列表</div>
            <p class="text-[11px] text-text-3 mt-1">
              请确认上方医院名称与订单号无误后，点击「读取文件」获取 SVN 文件目录树。
            </p>
          </div>

          <!-- 加载状态 -->
          <div v-else class="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white gap-2">
            <svg class="w-6 h-6 animate-spin text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span class="text-xs text-text-2 font-medium">正在从 SVN 递归读取订单目录与文件树，请稍候...</span>
          </div>
        </div>
      </div>

      <!-- Bottom Fixed: 底部操作与统计栏 (始终固定吸附在底部) -->
      <div class="card p-2.5 px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0 shadow-sm border-t border-border">
        <!-- 统计信息 -->
        <div class="flex items-center gap-5 text-center select-none">
          <div class="space-y-0.5">
            <div class="text-sm font-bold text-slate-800 font-mono">{{ flatList.length }}</div>
            <div class="text-[10px] text-slate-400">总文件/目录</div>
          </div>
          <div class="space-y-0.5">
            <div class="text-sm font-bold text-blue-600 font-mono">{{ selectedCount }}</div>
            <div class="text-[10px] text-blue-500 font-semibold">已勾选部署包</div>
          </div>
          <div class="space-y-0.5">
            <div class="text-sm font-bold text-emerald-600 font-mono">{{ deploySuccessCount }}</div>
            <div class="text-[10px] text-emerald-500">部署成功</div>
          </div>
          <div class="space-y-0.5">
            <div class="text-sm font-bold text-rose-600 font-mono">{{ deployFailCount }}</div>
            <div class="text-[10px] text-rose-500">部署失败</div>
          </div>
        </div>

        <!-- 动作按钮 -->
        <div class="flex items-center gap-2.5">
          <button
            v-if="store.running"
            type="button"
            class="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer flex items-center gap-1.5"
            @click="onStopDeploy"
          >
            <span>停止执行</span>
          </button>

          <button
            v-else
            type="button"
            class="px-5 py-2 bg-primary hover:opacity-90 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="selectedCount === 0 || !serverAddress || !serverUsername"
            @click="onStartDeployConfirm"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>开始执行部署 ({{ selectedCount }})</span>
          </button>
        </div>
      </div>

    </div>

    <!-- Right: Side panel (progress + logs tabs) -->
    <div class="side-col">
      <!-- Tabs Header -->
      <div class="p-2 bg-slate-50 border-b border-slate-200 flex-shrink-0 select-none">
        <div class="flex items-center gap-1 p-1 bg-slate-200/70 rounded-xl">
          <button
            type="button"
            class="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer"
            :class="activeSideTab === 'pipeline' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
            @click="activeSideTab = 'pipeline'"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>流水线部署进度</span>
          </button>

          <button
            type="button"
            class="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer"
            :class="activeSideTab === 'logs' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
            @click="activeSideTab = 'logs'"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>实时日志</span>
            <span v-if="store.logs.length > 0" class="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-slate-300 text-slate-700 font-semibold">
              {{ store.logs.length }}
            </span>
          </button>
        </div>
      </div>

      <div v-show="activeSideTab === 'pipeline'" class="flex-1 min-h-0 flex flex-col overflow-hidden">
        <PipelineView />
      </div>

      <div v-show="activeSideTab === 'logs'" class="flex-1 min-h-0 flex flex-col overflow-hidden">
        <LogViewer />
      </div>
    </div>

    <!-- SVN 选择弹窗 (选择医院 / 选择订单号) -->
    <PickerDialog
      ref="pickerRef"
      :title="pickerTitle"
      :items="pickerItems"
      :current-value="pickerCurrentValue"
      @choose="onPickerChoose"
    />

    <!-- 模块专属独立配置弹窗 -->
    <OrderDeploySettingsDialog
      ref="settingsDialogRef"
      @saved="onSettingsSaved"
    />

    <!-- 代码/文本文件内嵌快速预览弹窗 (支持 SQL, TXT, LOG, JSON, MD 等) -->
    <FilePreviewDialog ref="previewDialogRef" />

    <!-- 部署二次确认弹窗 -->
    <teleport to="body">
      <div v-if="showConfirmModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
        <div class="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4 text-slate-800">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg">
              🚀
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-900">确认执行测试订单部署？</h3>
              <p class="text-xs text-slate-500">将把选中的前端包从 SVN 下载并上传解压部署到目标服务器</p>
            </div>
          </div>

          <div class="bg-slate-50 rounded-xl p-3.5 border border-slate-200 text-xs space-y-2 font-mono">
            <div class="flex justify-between">
              <span class="text-slate-500">目标服务器:</span>
              <span class="font-bold text-slate-800">{{ serverUsername }}@{{ serverAddress }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">选中的包数:</span>
              <span class="font-bold text-blue-600">{{ selectedCount }} 个</span>
            </div>
            <div class="border-t border-slate-200 pt-2 space-y-1 max-h-40 overflow-y-auto pr-1">
              <div v-for="item in selectedPackagesList" :key="item.id" class="flex items-center justify-between text-[11px]">
                <span class="text-slate-700 truncate max-w-[200px]" :title="item.name">{{ item.name }}</span>
                <span class="text-slate-400 truncate max-w-[180px]" :title="item.targetPath">-> {{ item.targetPath }}</span>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-2.5 pt-2">
            <button
              type="button"
              class="px-4 py-2 text-xs border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 cursor-pointer"
              @click="showConfirmModal = false"
            >
              取消
            </button>
            <button
              type="button"
              class="px-5 py-2 text-xs font-bold bg-primary hover:opacity-90 text-white rounded-lg cursor-pointer shadow-sm"
              @click="executeDeploy"
            >
              立即部署
            </button>
          </div>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import type { SvnTreeNode, SvnLocationItem } from '@/types'
import PipelineView from '@/components/PipelineView.vue'
import LogViewer from '@/components/LogViewer.vue'
import PickerDialog from '@/components/PickerDialog.vue'
import TreeNodeRow from '@/components/TreeNodeRow.vue'
import OrderDeploySettingsDialog from '@/components/OrderDeploySettingsDialog.vue'
import FilePreviewDialog from '@/components/FilePreviewDialog.vue'

const store = useAppStore()
const activeSideTab = ref<'pipeline' | 'logs'>('pipeline')
const settingsDialogRef = ref<InstanceType<typeof OrderDeploySettingsDialog> | null>(null)
const previewDialogRef = ref<InstanceType<typeof FilePreviewDialog> | null>(null)

const currentSvnUrl = ref('')
const hospitalName = ref('')
const orderNo = ref('')
const svnUsername = ref('')
const svnPassword = ref('')

const serverAddress = ref('192.168.31.202')
const serverUsername = ref('yahua')
const serverPassword = ref('')
const testingServer = ref(false)
const testResultOk = ref(false)
const testResultMsg = ref('')

const moduleSvnLocations = ref<SvnLocationItem[]>([])
const packageUploadPaths = ref<Record<string, string>>({})

const loadingTree = ref(false)
const treeData = ref<SvnTreeNode[]>([])
const flatList = ref<SvnTreeNode[]>([])
const expandedKeys = reactive<Record<string, boolean>>({})
const selectedMap = reactive<Record<string, boolean>>({})
const customTargetPaths = reactive<Record<string, string>>({})

const pickerRef = ref<InstanceType<typeof PickerDialog> | null>(null)
const pickerKind = ref<'hospital' | 'order'>('hospital')
const pickerTitle = ref('选择医院')
const pickerItems = ref<string[]>([])
const pickerCurrentValue = ref('')

const showConfirmModal = ref(false)
const deploySuccessCount = ref(0)
const deployFailCount = ref(0)

const svnLocationOptions = computed(() => {
  if (moduleSvnLocations.value.length > 0) return moduleSvnLocations.value
  return [
    {
      id: 'loc-default',
      name: '特殊订单仓库',
      url: 'https://10.1.1.120/svn/智慧病房特殊订单',
      isDefault: true,
    },
  ]
})

const computedOrderSvnUrl = computed(() => {
  const root = (currentSvnUrl.value || svnLocationOptions.value[0]?.url || '').trim().replace(/\/$/, '')
  if (!root) return ''
  if (!hospitalName.value.trim() && !orderNo.value.trim()) return root
  if (hospitalName.value.trim() && !orderNo.value.trim()) {
    return `${root}/${hospitalName.value.trim()}`
  }
  if (!hospitalName.value.trim() && orderNo.value.trim()) {
    return `${root}/${orderNo.value.trim()}`
  }
  return `${root}/${hospitalName.value.trim()}/${orderNo.value.trim()}`
})

const selectedCount = computed(() => {
  return flatList.value.filter((e) => e.kind === 'file' && selectedMap[e.id]).length
})

const selectedPackagesList = computed(() => {
  return flatList.value
    .filter((e) => e.kind === 'file' && selectedMap[e.id])
    .map((e) => ({
      id: e.id,
      name: e.name,
      relativePath: e.relativePath,
      matchedProjectName: e.matchedProjectName,
      targetPath: customTargetPaths[e.id] || e.matchedServerPath || packageUploadPaths.value[e.matchedProjectName || ''] || '/home/data/web',
    }))
})

const isAllExpanded = computed(() => {
  const dirNodes = flatList.value.filter((e) => e.kind === 'dir')
  if (dirNodes.length === 0) return false
  return dirNodes.every((n) => expandedKeys[n.id])
})

function savePluginConfig() {
  const data = {
    svnLocations: moduleSvnLocations.value,
    currentSvnUrl: currentSvnUrl.value,
    hospitalName: hospitalName.value,
    orderNo: orderNo.value,
    svnUsername: svnUsername.value,
    svnPassword: svnPassword.value,
    serverAddress: serverAddress.value,
    serverUsername: serverUsername.value,
    serverPassword: serverPassword.value,
    packageUploadPaths: packageUploadPaths.value,
  }
  localStorage.setItem('zbuild_order_deploy_config', JSON.stringify(data))
}

function loadPluginConfig() {
  const raw = localStorage.getItem('zbuild_order_deploy_config')
  if (raw) {
    try {
      const parsed = JSON.parse(raw)
      moduleSvnLocations.value = parsed.svnLocations || []
      currentSvnUrl.value = parsed.currentSvnUrl || moduleSvnLocations.value[0]?.url || 'https://10.1.1.120/svn/智慧病房特殊订单'
      hospitalName.value = parsed.hospitalName || ''
      orderNo.value = parsed.orderNo || ''
      svnUsername.value = parsed.svnUsername || ''
      svnPassword.value = parsed.svnPassword || ''
      serverAddress.value = parsed.serverAddress || '192.168.31.202'
      serverUsername.value = parsed.serverUsername || 'yahua'
      serverPassword.value = parsed.serverPassword || ''
      packageUploadPaths.value = parsed.packageUploadPaths || {}
      return
    } catch {
      // fallback to initial defaults
    }
  }
  // Default values
  currentSvnUrl.value = 'https://10.1.1.120/svn/智慧病房特殊订单'
  moduleSvnLocations.value = [
    {
      id: 'loc-default',
      name: '特殊订单仓库',
      url: 'https://10.1.1.120/svn/智慧病房特殊订单',
      isDefault: true,
    },
  ]
}

function openSettings() {
  if (settingsDialogRef.value) {
    settingsDialogRef.value.open()
  }
}

function onSettingsSaved(cfg: any) {
  moduleSvnLocations.value = cfg.svnLocations || []
  currentSvnUrl.value = cfg.currentSvnUrl || currentSvnUrl.value
  svnUsername.value = cfg.svnUsername || ''
  svnPassword.value = cfg.svnPassword || ''
  serverAddress.value = cfg.serverAddress || serverAddress.value
  serverUsername.value = cfg.serverUsername || serverUsername.value
  serverPassword.value = cfg.serverPassword || serverPassword.value
  packageUploadPaths.value = cfg.packageUploadPaths || {}
}

function onSvnUrlChanged() {
  treeData.value = []
  flatList.value = []
  savePluginConfig()
}

async function onTestServer() {
  const host = serverAddress.value.trim()
  const user = serverUsername.value.trim()
  const pass = serverPassword.value
  if (!host || !user) {
    store.showToast('请先输入服务器地址和用户名', 'warning')
    return
  }
  testingServer.value = true
  testResultMsg.value = ''
  testResultOk.value = false

  // Save plugin config independently
  savePluginConfig()

  try {
    const res = await ipc.testServer(host, user, pass)
    if (res.success) {
      testResultOk.value = true
      testResultMsg.value = res.message || '连接成功'
      store.showToast('服务器连接成功！', 'success')
    } else {
      testResultOk.value = false
      testResultMsg.value = res.error || '连接失败'
      store.showToast('连接失败: ' + (res.error || ''), 'error')
    }
  } catch (err: unknown) {
    testResultOk.value = false
    testResultMsg.value = err instanceof Error ? err.message : String(err)
    store.showToast('连接异常: ' + testResultMsg.value, 'error')
  } finally {
    testingServer.value = false
  }
}

async function pickHospital() {
  const root = currentSvnUrl.value || store.config?.svnRootUrl || ''
  const svnUser = svnUsername.value || store.config?.form.svnUsername || ''
  const svnPass = svnPassword.value || store.config?.form.svnPassword || ''
  if (!root) {
    store.showToast('请先选择或配置 SVN 根路径', 'warning')
    return
  }
  loadingTree.value = true
  try {
    const items = await ipc.svnList(store.config?.tools.svn || 'svn', root, svnUser, svnPass)
    pickerKind.value = 'hospital'
    pickerTitle.value = '选择医院'
    pickerItems.value = items
    pickerCurrentValue.value = hospitalName.value
    if (pickerRef.value) {
      pickerRef.value.show(hospitalName.value)
    }
  } catch (e: unknown) {
    store.showToast('获取医院列表失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  } finally {
    loadingTree.value = false
  }
}

async function pickOrder() {
  const root = currentSvnUrl.value || store.config?.svnRootUrl || ''
  const svnUser = svnUsername.value || store.config?.form.svnUsername || ''
  const svnPass = svnPassword.value || store.config?.form.svnPassword || ''
  if (!root) return

  let fetchUrl = root.replace(/\/$/, '')
  if (hospitalName.value.trim()) {
    fetchUrl += '/' + encodeURIComponent(hospitalName.value.trim())
  }

  loadingTree.value = true
  try {
    const items = await ipc.svnList(store.config?.tools.svn || 'svn', fetchUrl, svnUser, svnPass)
    pickerKind.value = 'order'
    pickerTitle.value = '选择订单号'
    pickerItems.value = items
    pickerCurrentValue.value = orderNo.value
    if (pickerRef.value) {
      pickerRef.value.show(orderNo.value)
    }
  } catch (e: unknown) {
    store.showToast('获取订单号列表失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  } finally {
    loadingTree.value = false
  }
}

function onPickerChoose(val: string) {
  const clean = (val || '').trim()
  if (pickerKind.value === 'hospital') {
    hospitalName.value = clean
    orderNo.value = ''
    store.showToast(`已选择医院: ${clean}`, 'success')
  } else {
    orderNo.value = clean
    store.showToast(`已选择订单号: ${clean}`, 'success')
    // Automatically load tree
    loadTree()
  }
}

async function loadTree() {
  const targetUrl = computedOrderSvnUrl.value
  if (!targetUrl) {
    store.showToast('请先选择或输入 SVN 路径及订单信息', 'warning')
    return
  }
  // Persist current input
  savePluginConfig()

  loadingTree.value = true
  try {
    const res = await ipc.orderDeployList({
      svnUrl: targetUrl,
      svn: store.config?.tools.svn || 'svn',
      svnUsername: svnUsername.value || store.config?.form.svnUsername || '',
      svnPassword: svnPassword.value || store.config?.form.svnPassword || '',
      serverUploadPaths: packageUploadPaths.value || {},
    })

    if (res.success) {
      treeData.value = (res.tree as SvnTreeNode[]) || []
      flatList.value = (res.flatList as SvnTreeNode[]) || []
      
      // Auto expand top-level nodes
      treeData.value.forEach((n) => {
        expandedKeys[n.id] = true
      })

      // Smart auto select frontend packages
      smartSelectFrontend()
      if (flatList.value.length === 0) {
        store.showToast('该路径下未读取到文件，请检查医院名称与订单号是否准确', 'info')
      } else {
        store.showToast(`成功读取 ${flatList.value.length} 个目录与文件项`, 'success')
      }
    } else {
      store.showToast('读取 SVN 文件树失败: ' + (res.error || '未知错误'), 'error')
    }
  } catch (err: unknown) {
    store.showToast('读取异常: ' + (err instanceof Error ? err.message : String(err)), 'error')
  } finally {
    loadingTree.value = false
  }
}

async function onOpenFile(node: SvnTreeNode) {
  if (node.kind === 'dir') return
  const root = (computedOrderSvnUrl.value || '').trim().replace(/\/$/, '')
  const fileUrl = node.fullUrl || `${root}/${node.relativePath.replace(/^\//, '')}`
  if (!fileUrl) {
    store.showToast('无法解析文件的 SVN 地址', 'warning')
    return
  }

  store.showToast(`正在从 SVN 获取 ${node.name}...`, 'info')
  try {
    const res = await ipc.orderDeployOpenFile({
      fileUrl,
      svn: store.config?.tools.svn || 'svn',
      svnUsername: svnUsername.value || store.config?.form.svnUsername || '',
      svnPassword: svnPassword.value || store.config?.form.svnPassword || '',
    })

    if (res.success) {
      if (res.isText && res.content !== undefined && previewDialogRef.value) {
        // 代码与文本文件 (如 .sql, .txt, .md, .json, .log 等): 内置弹窗查看
        previewDialogRef.value.show({
          fileName: node.name,
          filePath: res.filePath || '',
          content: res.content,
          size: res.size || node.size,
        })
        store.showToast(`已载入预览: ${node.name}`, 'success')
      } else if (res.filePath) {
        // 其它文件 (如 .docx, .xlsx, .pdf 等): 调用系统关联程序打开
        const openRes = await ipc.openPath(res.filePath)
        if (openRes.success) {
          store.showToast(`已调用系统程序打开: ${node.name}`, 'success')
        } else {
          store.showToast(`打开失败: ${openRes.error || '未找到系统关联程序'}`, 'error')
        }
      }
    } else {
      store.showToast(`获取文件失败: ${res.error || '未知错误'}`, 'error')
    }
  } catch (err: unknown) {
    store.showToast(`操作异常: ${err instanceof Error ? err.message : String(err)}`, 'error')
  }
}

function toggleExpand(id: string) {
  expandedKeys[id] = !expandedKeys[id]
}

function toggleExpandAll() {
  const next = !isAllExpanded.value
  flatList.value.forEach((node) => {
    if (node.kind === 'dir') {
      expandedKeys[node.id] = next
    }
  })
}

function toggleNodeSelect(node: SvnTreeNode, checked: boolean) {
  selectedMap[node.id] = checked
}

function selectOnlyNode(node: SvnTreeNode) {
  flatList.value.forEach((n) => {
    selectedMap[n.id] = n.id === node.id
  })
}

function selectAll(checked: boolean) {
  flatList.value.forEach((n) => {
    if (n.kind === 'file') {
      selectedMap[n.id] = checked
    }
  })
}

function smartSelectFrontend() {
  flatList.value.forEach((n) => {
    if (n.kind === 'file') {
      selectedMap[n.id] = Boolean(n.isFrontendPackage)
    }
  })
}

function updateTargetPath(nodeId: string, path: string) {
  customTargetPaths[nodeId] = path
}

function onStartDeployConfirm() {
  if (selectedCount.value === 0) {
    store.showToast('请先勾选需要部署的前端包', 'warning')
    return
  }
  showConfirmModal.value = true
}

async function executeDeploy() {
  showConfirmModal.value = false
  activeSideTab.value = 'pipeline'
  store.clearLogs()
  deploySuccessCount.value = 0
  deployFailCount.value = 0
  store.running = true

  savePluginConfig()

  try {
    await ipc.orderDeployStart({
      svnUrl: computedOrderSvnUrl.value,
      orderNo: orderNo.value,
      hospitalName: hospitalName.value,
      svn: store.config?.tools.svn || 'svn',
      svnUsername: svnUsername.value || store.config?.form.svnUsername || '',
      svnPassword: svnPassword.value || store.config?.form.svnPassword || '',
      serverAddress: serverAddress.value.trim(),
      serverUsername: serverUsername.value.trim(),
      serverPassword: serverPassword.value,
      selectedFiles: selectedPackagesList.value.map((p) => ({
        name: p.name,
        relativePath: p.relativePath,
        targetServerPath: p.targetPath,
        matchedProjectName: p.matchedProjectName,
      })),
    })
  } catch (err: unknown) {
    store.showToast('启动部署任务失败: ' + (err instanceof Error ? err.message : String(err)), 'error')
    store.running = false
  }
}

async function onStopDeploy() {
  await ipc.stopRun()
  store.running = false
  store.showToast('已请求停止任务', 'info')
}

onMounted(() => {
  loadPluginConfig()
})

defineExpose({
  openSettings,
})
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.main-col {
  flex: 1 1 0%;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  padding: 0.75rem;
}

.side-col {
  width: 440px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #e2e8f0;
  background-color: #fff;
  height: 100%;
  overflow: hidden;
}

@media (max-width: 1024px) {
  .app-shell {
    flex-direction: column;
  }
  .side-col {
    width: 100%;
    height: 380px;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }
}
</style>
