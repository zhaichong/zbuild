<template>
  <div v-if="store.config">
    <!-- SVN 模式: 订单信息 -->
    <div
      v-if="store.mode === 'svn'"
      class="card p-5 space-y-4"
    >
      <!-- Section Header with Actions -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
        <div class="flex items-center gap-2 text-text-1 font-bold text-sm">
          <svg
            width="16"
            height="16"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            class="text-primary shrink-0"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 01-2-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span>订单与提测单信息</span>
        </div>

        <!-- Checkbox & Manual Trigger Button -->
        <div v-if="store.config?.orderDirPath" class="flex flex-wrap items-center gap-3">
          <label class="inline-flex items-center gap-1.5 cursor-pointer text-xs font-medium text-text-2 select-none hover:text-primary transition-colors">
            <input
              v-model="store.config.form.createOrderDir"
              type="checkbox"
              class="w-4 h-4 accent-primary rounded cursor-pointer shrink-0"
              @change="scheduleAutoSave"
            >
            <span>自动创建提测目录</span>
            <span
              class="text-[10px] text-text-3 font-normal max-w-[150px] truncate"
              :title="store.config.orderDirPath"
            >({{ store.config.orderDirPath }})</span>
          </label>
          <button
            type="button"
            class="px-2 py-1 text-xs border border-border rounded bg-white text-text-2 hover:bg-slate-50 transition-colors shrink-0"
            :disabled="creatingOrderDir"
            title="手动创建提测目录并生成 Excel 提测单"
            @click="onGenerateOrderDirManually"
          >
            {{ creatingOrderDir ? '创建中...' : '手动生成提测目录' }}
          </button>
        </div>
      </div>

      <!-- 极客摸鱼/打包段子驿站 (自动记录且每次打包不重样) -->
      <DevJokeBar />

      <!-- Row 1: Hospital Name & Order No -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- 医院名称 -->
        <div class="flex flex-col gap-1.5 min-w-0">
          <label class="text-xs font-semibold text-text-2">医院名称</label>
          <div class="flex gap-1.5">
            <input
              v-model="store.config.form.hospitalName"
              type="text"
              class="form-input flex-1 min-w-0"
              placeholder="输入或选择医院名称"
              @input="scheduleAutoSave"
            >
            <button
              class="px-3 rounded-lg border border-border bg-white text-text-3 hover:text-primary hover:border-primary/40 transition-colors flex items-center shrink-0 cursor-pointer shadow-2xs"
              title="从 SVN 浏览选择医院"
              :disabled="svnLoading"
              @click="pickHospital"
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
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- 订单号 -->
        <div class="flex flex-col gap-1.5 min-w-0">
          <label class="text-xs font-semibold text-text-2">订单号</label>
          <div class="flex gap-1.5">
            <input
              v-model="store.config.form.orderNo"
              type="text"
              class="form-input flex-1 min-w-0"
              placeholder="输入或选择订单号"
              @input="scheduleAutoSave"
            >
            <button
              class="px-3 rounded-lg border border-border bg-white text-text-3 hover:text-primary hover:border-primary/40 transition-colors flex items-center shrink-0 cursor-pointer shadow-2xs"
              title="从 SVN 浏览选择订单号"
              :disabled="svnLoading || !store.config.form.hospitalName"
              @click="pickOrder"
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
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Row 2: Multi-line Change Notes Textarea (仅在勾选自动创建提测目录时展示) -->
      <div
        v-if="store.config.form.createOrderDir"
        class="flex flex-col gap-1.5 pt-1"
      >
        <div class="flex items-center justify-between text-xs">
          <label class="font-semibold text-text-2">本次更改内容（自动写入提测单 B12）</label>
          <span class="text-[11px] text-text-3 font-normal">支持按 Enter 换行多行输入（留空则默认按选中的项目及分支自动填充）</span>
        </div>
        <textarea
          v-model="store.config.form.orderNotes"
          rows="3"
          class="form-input w-full font-sans text-xs resize-y leading-relaxed p-2.5"
          placeholder="例如:&#10;1、增加新首页&#10;2、修复已知问题"
          @input="scheduleAutoSave"
        />
      </div>

      <PickerDialog
        ref="pickerRef"
        :title="pickerTitle"
        :items="pickerItems"
        :current-value="pickerCurrentValue"
        @choose="onPickerChoose"
      />
    </div>

    <!-- 服务器模式: 服务器配置 -->
    <div
      v-if="store.mode === 'server'"
      class="card p-4 bg-white border border-slate-200/90 shadow-2xs"
    >
      <div class="flex items-center gap-1.5 mb-2.5 text-slate-800 font-bold text-xs tracking-tight">
        <svg
          width="15"
          height="15"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          class="text-blue-600 shrink-0"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 12h14M5 12a2 2 0 012-2h10a2 2 0 012 2m-14 0a2 2 0 002 2h10a2 2 0 002-2M7 8l5-5 5 5"
          />
        </svg>
        <span>服务器连接配置</span>
      </div>
      <div class="flex items-end gap-3 flex-nowrap">
        <!-- 服务器地址 -->
        <div class="flex flex-col gap-1 w-48 shrink-0">
          <label class="text-xs text-slate-700 font-semibold">服务器地址</label>
          <input
            v-model="store.config.form.serverAddress"
            type="text"
            class="form-input w-full font-mono text-xs text-slate-800"
            placeholder="例如 192.168.78.63"
            @input="scheduleAutoSave"
          >
        </div>

        <!-- 服务器用户名 -->
        <div class="flex flex-col gap-1 w-36 shrink-0">
          <label class="text-xs text-slate-700 font-semibold">服务器用户名</label>
          <input
            v-model="store.config.form.serverUsername"
            type="text"
            class="form-input w-full text-xs text-slate-800"
            placeholder="用户名"
            @input="scheduleAutoSave"
          >
        </div>

        <!-- 服务器密码 -->
        <div class="flex flex-col gap-1 w-36 shrink-0">
          <label class="text-xs text-slate-700 font-semibold">服务器密码</label>
          <input
            v-model="store.config.form.serverPassword"
            type="password"
            class="form-input w-full text-xs text-slate-800"
            placeholder="密码"
            @input="scheduleAutoSave"
          >
        </div>

        <!-- 测试连接 按钮 + 结果消息 (紧凑同行组合) -->
        <div class="flex items-center gap-2 shrink-0 h-[36px]">
          <button
            class="px-3.5 text-xs font-bold rounded-lg transition-all whitespace-nowrap shadow-2xs cursor-pointer flex items-center justify-center shrink-0 h-[36px]"
            :class="testResult === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100' : testResult === 'error' ? 'bg-rose-50 text-rose-700 border border-rose-300 hover:bg-rose-100' : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-98'"
            :disabled="testing"
            @click="onTestServer"
          >
            <span
              v-if="testing"
              class="flex items-center gap-1.5"
            >
              <svg
                class="w-3.5 h-3.5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              测试中...
            </span>
            <span v-else>测试连接</span>
          </button>

          <!-- 测试结果提示消息 (紧跟在 测试连接 按钮右侧) -->
          <transition
            enter-active-class="transition ease-out duration-200"
            enter-from-class="opacity-0 translate-x-1"
            enter-to-class="opacity-100 translate-x-0"
            leave-active-class="transition ease-in duration-150"
            leave-from-class="opacity-100 translate-x-0"
            leave-to-class="opacity-0 translate-x-1"
          >
            <div
              v-if="testMessage"
              class="inline-flex items-center gap-1.5 px-3 rounded-lg text-xs font-semibold border h-[36px] shrink-0 whitespace-nowrap shadow-2xs"
              :class="testResult === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-300' : 'bg-rose-50 text-rose-800 border-rose-300'"
            >
              <svg
                v-if="testResult === 'success'"
                class="w-3.5 h-3.5 shrink-0 text-emerald-600"
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
              <svg
                v-else
                class="w-3.5 h-3.5 shrink-0 text-rose-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{{ testMessage }}</span>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import { saveConfig } from '@/composables/useConfig'
import PickerDialog from '@/components/PickerDialog.vue'
import DevJokeBar from '@/components/DevJokeBar.vue'
import type { SvnLocationItem } from '@/types'

const store = useAppStore()
const svnLoading = ref(false)
const pickerRef = ref<InstanceType<typeof PickerDialog> | null>(null)
const pickerItems = ref<string[]>([])
const pickerCurrentValue = ref('')
const pickerTitle = ref('')
const pickerKind = ref<'hospital' | 'order'>('hospital')

const svnLocationOptions = computed<SvnLocationItem[]>(() => {
  const locs = store.config?.svnLocations || []
  if (locs.length > 0) return locs
  if (store.config?.svnRootUrl) {
    return [
      {
        id: 'loc-default',
        name: '默认特殊订单库',
        url: store.config.svnRootUrl,
        isDefault: true,
      },
    ]
  }
  return []
})

function isCurrentSvn(url: string): boolean {
  const current = (store.config?.svnRootUrl || '').trim().replace(/\/$/, '')
  const target = (url || '').trim().replace(/\/$/, '')
  return current === target
}

function onSelectSvnLocation(loc: SvnLocationItem) {
  if (!store.config) return
  if (store.config.svnRootUrl === loc.url) return
  store.config.svnRootUrl = loc.url
  if (store.config.svnLocations) {
    store.config.svnLocations.forEach((item) => {
      item.isDefault = item.url === loc.url
    })
  }
  saveConfig(store.config).catch((e) => console.warn('Auto save config failed:', e))
  store.showToast(`已切换至 SVN 目录源: ${loc.name}`, 'info')
}

const testing = ref(false)
const testResult = ref<'success' | 'error' | ''>('')
const testMessage = ref('')

let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
let autoSaveInFlight = false

// Only actual user input schedules a save. Watching the whole reactive config
// caused a loop because saveConfig replaces store.config with the API response.
function scheduleAutoSave() {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(async () => {
    if (!store.config || autoSaveInFlight) return
    autoSaveInFlight = true
    try {
      await saveConfig(store.config)
    } catch (e) {
      console.warn('Auto-save config failed:', e)
    } finally {
      autoSaveInFlight = false
    }
  }, 1200)
}

onBeforeUnmount(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
})

async function onTestServer() {
  if (!store.config) return
  const { serverAddress, serverUsername, serverPassword } = store.config.form
  if (!serverAddress || !serverUsername) {
    testResult.value = 'error'
    testMessage.value = '请先填写服务器地址和用户名'
    return
  }

  // 点击测试连接时立即保存配置
  try {
    await saveConfig(store.config)
  } catch (e) {
    console.warn('Save config before test failed:', e)
  }

  testing.value = true
  testResult.value = ''
  testMessage.value = ''
  try {
    const res = await ipc.testServer(serverAddress, serverUsername, serverPassword)
    if (res.success) {
      testResult.value = 'success'
      testMessage.value = res.message || '连接成功'
    } else {
      testResult.value = 'error'
      testMessage.value = res.error || '连接失败'
    }
  } catch (e: unknown) {
    testResult.value = 'error'
    testMessage.value = e instanceof Error ? e.message : '连接异常'
  } finally {
    testing.value = false
  }
}

async function pickHospital() {
  const cfg = store.config
  if (!cfg?.svnRootUrl || !cfg.form) {
    store.showToast('请先在设置中配置 SVN 根 URL', 'warning')
    return
  }
  const svnUser = cfg.form.svnUsername || ''
  const svnPass = cfg.form.svnPassword || ''
  if (!svnUser || !svnPass) {
    store.showToast('请先在设置中填写 SVN 用户名和密码', 'warning')
    return
  }

  svnLoading.value = true
  try {
    const items = await ipc.svnList(cfg.tools?.svn || 'svn', cfg.svnRootUrl, svnUser, svnPass)
    pickerKind.value = 'hospital'
    pickerTitle.value = '选择医院'
    pickerItems.value = items
    pickerCurrentValue.value = cfg.form.hospitalName || ''
    if (pickerRef.value) {
      pickerRef.value.show(cfg.form.hospitalName || '')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    store.showToast('SVN 列表获取失败: ' + msg, 'error')
  } finally {
    svnLoading.value = false
  }
}

async function pickOrder() {
  const cfg = store.config
  if (!cfg?.svnRootUrl || !cfg.form || !cfg.form.hospitalName) return

  const svnUser = cfg.form.svnUsername || ''
  const svnPass = cfg.form.svnPassword || ''

  svnLoading.value = true
  try {
    const svnRoot = cfg.svnRootUrl.replace(/\/$/, '')
    const hospitalUrl = svnRoot + '/' + encodeURIComponent(cfg.form.hospitalName)
    const items = await ipc.svnList(cfg.tools?.svn || 'svn', hospitalUrl, svnUser, svnPass)
    pickerKind.value = 'order'
    pickerTitle.value = '选择订单号'
    pickerItems.value = items
    pickerCurrentValue.value = cfg.form.orderNo || ''
    if (pickerRef.value) {
      pickerRef.value.show(cfg.form.orderNo || '')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    store.showToast('SVN 列表获取失败: ' + msg, 'error')
  } finally {
    svnLoading.value = false
  }
}

function onPickerChoose(value: string) {
  if (!store.config || !store.config.form) return
  const cleanVal = (value || '').trim()
  if (pickerKind.value === 'hospital') {
    store.config.form.hospitalName = cleanVal
    // Clear order number since it depends on hospital
    store.config.form.orderNo = ''
    store.showToast(`已选择医院: ${cleanVal}`, 'success')
  } else {
    store.config.form.orderNo = cleanVal
    store.showToast(`已选择订单号: ${cleanVal}`, 'success')
  }
  saveConfig(store.config).catch((e) => console.warn('Auto save failed:', e))
}

const creatingOrderDir = ref(false)

async function onGenerateOrderDirManually() {
  if (!store.config || !store.config.form) return
  const { hospitalName, orderNo, orderNotes } = store.config.form
  const orderDirPath = store.config.orderDirPath
  if (!orderDirPath) {
    store.showToast('请先在设置中配置提测目录根路径', 'warning')
    return
  }
  if (!hospitalName || !orderNo) {
    store.showToast('请先填写医院名称和订单号', 'warning')
    return
  }

  creatingOrderDir.value = true
  try {
    const enabledProjs = (store.projects || [])
      .filter((p) => p.enabled)
      .map((p) => ({
        projectName: p.projectName,
        branch: store.projectBranches[p.projectName] || p.currentBranch || '',
      }))

    const res = await ipc.createOrderDir({
      order_dir_base: orderDirPath,
      order_no: orderNo,
      hospital_name: hospitalName,
      order_notes: orderNotes || '',
      projects: enabledProjs,
    })

    if (res && res.success) {
      store.showToast(res.message || '成功生成提测目录、Excel 提测单及 Word 升级说明', 'success')
    } else {
      store.showToast('生成提测单失败: ' + (res?.message || '未知错误'), 'error')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    store.showToast('生成提测单失败: ' + msg, 'error')
  } finally {
    creatingOrderDir.value = false
  }
}
</script>
