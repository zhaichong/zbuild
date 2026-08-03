<template>
  <div class="flex-1 min-h-0 bg-slate-50 p-6 flex flex-col overflow-hidden">
    <div class="max-w-6xl mx-auto w-full flex-1 min-h-0 flex flex-col overflow-hidden">
      <!-- Main Grid Section -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">
        <!-- Left Panel: Configuration (5 cols) -->
        <div class="lg:col-span-5 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs flex flex-col justify-between overflow-y-auto space-y-4">
          <div class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-blue-600" />
                <span>提取配置与参数组装</span>
              </h3>
              <span class="text-xs text-slate-400 font-mono">Step 1-4</span>
            </div>

            <!-- Step 1: Base URL -->
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-slate-700">
                1. 目标服务器 Base URL
              </label>
              <div class="flex gap-2">
                <input
                  v-model="baseUrl"
                  type="text"
                  class="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 focus:border-blue-500 focus:bg-white rounded-xl text-xs text-slate-800 placeholder-slate-400 outline-none transition-all font-mono"
                  placeholder="http://192.168.xxx.xxx"
                >
                <button
                  type="button"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-2xs transition-all flex items-center gap-1 shrink-0 cursor-pointer disabled:opacity-50"
                  :disabled="connecting || !baseUrl.trim()"
                  @click="onConnect"
                >
                  <svg v-if="connecting" class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>{{ connecting ? '连接中...' : '连接' }}</span>
                </button>
              </div>
            </div>

            <!-- Step 2: Org Select -->
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-slate-700">
                2. 选择机构 (Org)
              </label>
              <select
                v-model="selectedOrgId"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 focus:border-blue-500 focus:bg-white rounded-xl text-xs text-slate-800 outline-none transition-all disabled:opacity-50 cursor-pointer"
                :disabled="orgs.length === 0"
                @change="onOrgChange"
              >
                <option value="" disabled>
                  {{ orgs.length > 0 ? '-- 请选择机构 --' : '尚未获取机构列表' }}
                </option>
                <option v-for="org in orgs" :key="org.orgId" :value="org.orgId">
                  {{ org.orgName || org.orgId }} (ID: {{ org.orgId }})
                </option>
              </select>
            </div>

            <!-- Step 3: Dept Select -->
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-slate-700">
                3. 选择护理单元 (Department)
              </label>
              <select
                v-model="selectedDeptId"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 focus:border-blue-500 focus:bg-white rounded-xl text-xs text-slate-800 outline-none transition-all disabled:opacity-50 cursor-pointer"
                :disabled="depts.length === 0"
                @change="onDeptChange"
              >
                <option value="" disabled>
                  {{ depts.length > 0 ? '-- 请选择护理单元 --' : '请先选择机构' }}
                </option>
                <option v-for="dept in depts" :key="dept.deptId" :value="dept.deptId">
                  {{ dept.deptName || dept.deptId }} (Key: {{ dept.deptKey || dept.deptId }})
                </option>
              </select>
            </div>

            <!-- Step 4: Device Select -->
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-slate-700">
                4. 匹配终端设备 (wnBedHead/wnBedSide)
              </label>
              <select
                v-model="selectedDeviceId"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 focus:border-blue-500 focus:bg-white rounded-xl text-xs text-slate-800 outline-none transition-all disabled:opacity-50 cursor-pointer"
                :disabled="devices.length === 0"
              >
                <option value="" disabled>
                  {{ devices.length > 0 ? '-- 请选择终端设备 --' : '请先选择护理单元' }}
                </option>
                <option v-for="dev in devices" :key="dev.deviceId" :value="dev.deviceId">
                  {{ dev.deviceName || dev.deviceId }} [床号: {{ dev.bedName || '未指定' }}]
                </option>
              </select>
            </div>

            <!-- Submit Action -->
            <div class="pt-2">
              <button
                type="button"
                class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                :disabled="extracting || !selectedDeviceId"
                @click="onStartExtract"
              >
                <svg v-if="extracting" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>{{ extracting ? '数据提取与匹配中...' : '🚀 开始智能提取数据链路' }}</span>
              </button>
            </div>
          </div>

          <!-- Description Footer -->
          <div class="bg-blue-50/60 border border-blue-100 rounded-xl p-3 text-xs text-slate-600 space-y-1">
            <div class="font-bold text-blue-900 flex items-center gap-1.5">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>内置连接引擎</span>
            </div>
            <p class="leading-relaxed text-[11px]">
              支持自动跨域代理连接，直连测试目标服务，提取设备、机构与患者信息。
            </p>
          </div>
        </div>

        <!-- Right Panel: Result Console (7 cols) -->
        <div class="lg:col-span-7 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs flex flex-col min-h-0 overflow-hidden space-y-3">
          <div class="flex items-center justify-between border-b border-slate-100 pb-3 shrink-0">
            <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
              <span>提取结果与数据组装</span>
            </h3>

            <button
              v-if="formattedResult"
              type="button"
              class="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
              @click="copyResult"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
              </svg>
              <span>一键复制结果</span>
            </button>
          </div>

          <!-- Code Display Terminal with Auto Flex Height & Internal Scrollbar -->
          <div class="flex-1 min-h-0 bg-slate-900 border border-slate-800 rounded-xl p-4 font-mono text-xs text-emerald-400 leading-relaxed overflow-y-auto shadow-inner custom-result-scrollbar">
            <pre v-if="formattedResult" class="whitespace-pre-wrap font-mono">{{ formattedResult }}</pre>
            <div v-else-if="extracting" class="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
              <svg class="w-8 h-8 animate-spin text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>正在向目标服务器提取数据...</span>
            </div>
            <div v-else class="h-full flex flex-col items-center justify-center text-slate-500 space-y-2">
              <svg class="w-10 h-10 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>请在左侧配置目标 URL 并选择终端设备后点击「智能提取数据链路」</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import {
  fetchOrgs,
  fetchDepts,
  fetchDevices,
  extractLinkData,
  type OrgItem,
  type DeptItem,
  type DeviceItem,
} from '@/services/mockQuery'

const store = useAppStore()

const baseUrl = ref('http://192.168.78.63')
const connecting = ref(false)
const extracting = ref(false)

const orgs = ref<OrgItem[]>([])
const depts = ref<DeptItem[]>([])
const devices = ref<DeviceItem[]>([])

const selectedOrgId = ref('')
const selectedDeptId = ref('')
const selectedDeviceId = ref('')

const formattedResult = ref('')

async function onConnect() {
  if (!baseUrl.value.trim()) return
  connecting.value = true
  orgs.value = []
  depts.value = []
  devices.value = []
  selectedOrgId.value = ''
  selectedDeptId.value = ''
  selectedDeviceId.value = ''
  formattedResult.value = ''

  try {
    const list = await fetchOrgs(baseUrl.value)
    orgs.value = list
    if (list.length > 0) {
      selectedOrgId.value = list[0].orgId
      await onOrgChange()
    }
    store.showToast(`成功获取 ${list.length} 个机构`, 'success')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`连接失败: ${msg}`, 'error')
  } finally {
    connecting.value = false
  }
}

async function onOrgChange() {
  if (!selectedOrgId.value) return
  depts.value = []
  devices.value = []
  selectedDeptId.value = ''
  selectedDeviceId.value = ''

  try {
    const list = await fetchDepts(baseUrl.value, selectedOrgId.value)
    depts.value = list
    if (list.length > 0) {
      selectedDeptId.value = list[0].deptId
      await onDeptChange()
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`获取护理单元失败: ${msg}`, 'error')
  }
}

async function onDeptChange() {
  if (!selectedDeptId.value) return
  devices.value = []
  selectedDeviceId.value = ''

  try {
    const list = await fetchDevices(baseUrl.value, selectedDeptId.value)
    devices.value = list
    if (list.length > 0) {
      selectedDeviceId.value = list[0].deviceId
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`获取终端设备失败: ${msg}`, 'error')
  }
}

async function onStartExtract() {
  if (!selectedDeviceId.value) return
  extracting.value = true
  formattedResult.value = ''

  try {
    const selectedDev = devices.value.find((d) => d.deviceId === selectedDeviceId.value)
    const result = await extractLinkData(
      baseUrl.value,
      selectedDeviceId.value,
      selectedDeptId.value,
      selectedDev?.bedName,
    )
    formattedResult.value = result.formattedText
    store.showToast('数据链路提取与患者匹配成功', 'success')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`提取数据失败: ${msg}`, 'error')
  } finally {
    extracting.value = false
  }
}

function copyResult() {
  if (!formattedResult.value) return
  navigator.clipboard.writeText(formattedResult.value)
  store.showToast('提取结果已复制到剪贴板', 'success')
}
</script>

<style scoped>
.custom-result-scrollbar {
  overflow-y: auto !important;
}
.custom-result-scrollbar::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.custom-result-scrollbar::-webkit-scrollbar-track {
  background: #0f172a;
  border-radius: 6px;
}
.custom-result-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 6px;
  border: 2px solid #0f172a;
}
.custom-result-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
