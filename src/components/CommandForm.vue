<template>
  <div class="bg-surface rounded-lg shadow-sm p-4">
    <div class="flex items-center gap-4 mb-4">
      <label class="text-sm font-medium text-gray-700">上传模式</label>
      <div class="flex gap-2">
        <button
          v-for="m in modes"
          :key="m.value"
          class="px-4 py-2 text-sm rounded-lg transition-colors"
          :class="currentMode === m.value
            ? 'bg-primary text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          @click="setMode(m.value)"
        >
          {{ m.label }}
        </button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">医院名称</label>
        <input
          v-model="form.hospitalName"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="输入医院名称"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">订单号</label>
        <input
          v-model="form.orderNo"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="输入订单号"
        />
      </div>
    </div>

    <div v-if="currentMode === 'svn'" class="grid grid-cols-2 gap-4 mt-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">SVN 用户名</label>
        <input
          v-model="form.svnUsername"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="SVN 用户名"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">SVN 密码</label>
        <input
          v-model="form.svnPassword"
          type="password"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="SVN 密码"
        />
      </div>
    </div>

    <div v-if="currentMode === 'server'" class="grid grid-cols-3 gap-4 mt-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">服务器地址</label>
        <input
          v-model="form.serverAddress"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="服务器地址"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">服务器用户名</label>
        <input
          v-model="form.serverUsername"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="服务器用户名"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">服务器密码</label>
        <input
          v-model="form.serverPassword"
          type="password"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
          placeholder="服务器密码"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { UploadMode } from '@/types'

const store = useAppStore()

const modes = [
  { value: 'svn' as UploadMode, label: 'SVN 上传' },
  { value: 'server' as UploadMode, label: '服务器上传' },
  { value: 'local' as UploadMode, label: '本地输出' },
]

const form = ref({
  hospitalName: '',
  orderNo: '',
  svnUsername: '',
  svnPassword: '',
  serverAddress: '',
  serverUsername: '',
  serverPassword: '',
})

const currentMode = computed(() => store.mode)

watch(() => store.config, (cfg) => {
  if (cfg?.form) {
    form.value = { ...cfg.form }
  }
}, { immediate: true })

watch(form, (val) => {
  if (store.config) {
    store.config.form = { ...val }
  }
}, { deep: true })

function setMode(mode: UploadMode) {
  if (!store.config) return
  store.config.uploadAfterBuild = mode === 'svn'
  store.config.uploadToServer = mode === 'server'
}
</script>
