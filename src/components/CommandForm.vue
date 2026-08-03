<template>
  <div v-if="store.config">
    <!-- SVN 模式: 订单信息 -->
    <div
      v-if="store.mode === 'svn'"
      class="card p-5"
    >
      <div class="flex items-center gap-1.5 mb-3 text-text-2 font-semibold text-sm">
        <svg
          width="14"
          height="14"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        订单信息
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-text-3 font-medium">医院名称</label>
          <div class="flex gap-1">
            <input
              v-model="store.config.form.hospitalName"
              type="text"
              class="form-input flex-1"
              placeholder="输入或选择医院名称"
            >
            <button
              class="px-2.5 rounded-lg border border-border bg-white text-text-3 hover:text-primary hover:border-primary/30 transition-colors flex items-center"
              title="从 SVN 浏览选择"
              :disabled="svnLoading"
              @click="pickHospital"
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
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-text-3 font-medium">订单号</label>
          <div class="flex gap-1">
            <input
              v-model="store.config.form.orderNo"
              type="text"
              class="form-input flex-1"
              placeholder="输入或选择订单号"
            >
            <button
              class="px-2.5 rounded-lg border border-border bg-white text-text-3 hover:text-primary hover:border-primary/30 transition-colors flex items-center"
              title="从 SVN 浏览选择"
              :disabled="svnLoading || !store.config.form.hospitalName"
              @click="pickOrder"
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
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </div>
        </div>
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
      class="card p-5"
    >
      <div class="flex items-center gap-1.5 mb-3 text-text-2 font-semibold text-sm">
        <svg
          width="14"
          height="14"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 12h14M5 12a2 2 0 012-2h10a2 2 0 012 2m-14 0a2 2 0 002 2h10a2 2 0 002-2M7 8l5-5 5 5"
          />
        </svg>
        服务器配置
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-xs text-text-3 mb-1.5 font-medium">服务器地址</label>
          <div class="flex gap-2">
            <input
              v-model="store.config.form.serverAddress"
              type="text"
              class="flex-1 form-input"
              placeholder="例如 10.1.1.100"
            >
            <button
              class="px-3.5 py-2 text-xs font-semibold rounded-lg transition-all whitespace-nowrap shadow-sm"
              :class="testResult === 'success' ? 'bg-success-light text-success border border-success/30' : testResult === 'error' ? 'bg-error-light text-error border border-error/30' : 'bg-primary text-white hover:opacity-90'"
              :disabled="testing"
              @click="onTestServer"
            >
              <span
                v-if="testing"
                class="flex items-center gap-1"
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
                测试中
              </span>
              <span v-else>测试连接</span>
            </button>
          </div>
          <div
            v-if="testMessage"
            class="mt-1.5 text-xs flex items-center gap-1"
            :class="testResult === 'success' ? 'text-success' : 'text-error'"
          >
            <svg
              v-if="testResult === 'success'"
              class="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            <svg
              v-else
              class="w-3.5 h-3.5"
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
            {{ testMessage }}
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-text-3 font-medium">服务器用户名</label>
            <input
              v-model="store.config.form.serverUsername"
              type="text"
              class="form-input w-full"
              placeholder="用户名"
            >
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-text-3 font-medium">服务器密码</label>
            <input
              v-model="store.config.form.serverPassword"
              type="password"
              class="form-input w-full"
              placeholder="密码"
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import PickerDialog from '@/components/PickerDialog.vue'

const store = useAppStore()
const svnLoading = ref(false)
const pickerRef = ref<InstanceType<typeof PickerDialog> | null>(null)
const pickerItems = ref<string[]>([])
const pickerCurrentValue = ref('')
const pickerTitle = ref('')
const pickerKind = ref<'hospital' | 'order'>('hospital')

const testing = ref(false)
const testResult = ref<'success' | 'error' | ''>('')
const testMessage = ref('')

async function onTestServer() {
  if (!store.config) return
  const { serverAddress, serverUsername, serverPassword } = store.config.form
  if (!serverAddress || !serverUsername) {
    testResult.value = 'error'
    testMessage.value = '请先填写服务器地址和用户名'
    return
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
  if (pickerKind.value === 'hospital') {
    store.config.form.hospitalName = value
    // Clear order number since it depends on hospital
    store.config.form.orderNo = ''
  } else {
    store.config.form.orderNo = value
  }
}
</script>
