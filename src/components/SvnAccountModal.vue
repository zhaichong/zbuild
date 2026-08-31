<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[9999] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4"
      @click.self="handleCancel"
    >
      <div
        class="relative bg-white rounded-2xl border border-slate-200/80 shadow-2xl w-full max-w-md overflow-hidden text-slate-800 transform transition-all animate-in fade-in zoom-in-95 duration-150"
      >
        <!-- Top Visual Accent Banner -->
        <div class="relative bg-gradient-to-br from-blue-50 via-indigo-50/40 to-white px-6 pt-5 pb-4 border-b border-slate-100">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-500/25 shrink-0">
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
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-900 tracking-tight">
                  配置 SVN 账户
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                  {{ targetAppName ? `进入「${targetAppName}」需先配置 SVN 凭据` : '进入核心功能前请先配置 SVN 账号信息' }}
                </p>
              </div>
            </div>

            <button
              type="button"
              class="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center cursor-pointer transition-colors"
              @click="handleCancel"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Form Body -->
        <div class="p-6 space-y-4 text-xs">
          <!-- Notification Notice -->
          <div class="p-3 bg-blue-50/70 border border-blue-100 rounded-xl text-blue-800 text-xs flex items-start gap-2.5">
            <svg
              class="w-4 h-4 text-blue-600 mt-0.5 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span class="leading-relaxed">
              系统将使用该账户拉取医院订单目录树、自动比对工程分支并执行提测构建与产物上传。
            </span>
          </div>

          <!-- SVN Username Input -->
          <div class="space-y-1.5">
            <label class="block text-slate-700 font-semibold">
              SVN 用户名 <span class="text-rose-500">*</span>
            </label>
            <div class="relative">
              <div class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none flex items-center">
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
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </div>
              <input
                ref="usernameInputRef"
                v-model="username"
                type="text"
                autocomplete="username"
                class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all shadow-2xs"
                placeholder="请输入 SVN 账号 (如: zhangsan)"
                @keydown.enter="focusPasswordOrSubmit"
              >
            </div>
          </div>

          <!-- SVN Password Input -->
          <div class="space-y-1.5">
            <label class="block text-slate-700 font-semibold">
              SVN 密码 <span class="text-rose-500">*</span>
            </label>
            <div class="relative">
              <div class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none flex items-center">
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
                    d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                  />
                </svg>
              </div>
              <input
                ref="passwordInputRef"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                class="w-full pl-9 pr-9 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all shadow-2xs"
                placeholder="请输入 SVN 密码"
                @keydown.enter="handleSave"
              >
              <button
                type="button"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 rounded-md cursor-pointer transition-colors"
                :title="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
              >
                <svg
                  v-if="!showPassword"
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
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
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- Error Tip -->
          <div
            v-if="errorMessage"
            class="text-rose-500 text-[11px] font-medium flex items-center gap-1 animate-in fade-in duration-150"
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
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{{ errorMessage }}</span>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="flex items-center justify-end gap-2.5 px-6 py-4 bg-slate-50/50 border-t border-slate-100">
          <button
            type="button"
            class="px-4 py-2 text-xs font-medium rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors"
            @click="handleCancel"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="saving"
            class="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl cursor-pointer shadow-xs shadow-blue-500/30 transition-all active:scale-98"
            @click="handleSave"
          >
            <svg
              v-if="saving"
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
                stroke-width="2.5"
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>{{ saving ? '保存中...' : '保存并进入应用' }}</span>
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { saveConfig } from '@/composables/useConfig'

const store = useAppStore()

const visible = ref(false)
const saving = ref(false)
const showPassword = ref(false)
const errorMessage = ref('')
const username = ref('')
const password = ref('')
const targetAppId = ref<string>('')
const targetAppName = ref<string>('')

const usernameInputRef = ref<HTMLInputElement | null>(null)
const passwordInputRef = ref<HTMLInputElement | null>(null)

const emit = defineEmits<{
  success: [appId: string]
  cancel: []
}>()

function show(options?: { targetAppId?: string; targetAppName?: string }) {
  targetAppId.value = options?.targetAppId || ''
  targetAppName.value = options?.targetAppName || ''
  
  // Prefill existing from store if any
  const currentUsername = store.config?.form?.svnUsername?.trim() || ''
  username.value = currentUsername
  password.value = currentUsername ? (store.config?.form?.svnPassword || '') : ''
  showPassword.value = false
  errorMessage.value = ''
  saving.value = false
  visible.value = true

  nextTick(() => {
    if (!username.value) {
      usernameInputRef.value?.focus()
    } else {
      passwordInputRef.value?.focus()
    }
  })
}

function handleCancel() {
  visible.value = false
  emit('cancel')
}

function focusPasswordOrSubmit() {
  if (!username.value.trim()) {
    errorMessage.value = '请输入 SVN 用户名'
    return
  }
  if (!password.value.trim()) {
    passwordInputRef.value?.focus()
  } else {
    handleSave()
  }
}

async function handleSave() {
  const u = username.value.trim()
  const p = password.value.trim()

  if (!u) {
    errorMessage.value = '请输入 SVN 用户名'
    usernameInputRef.value?.focus()
    return
  }

  if (!p) {
    errorMessage.value = '请输入 SVN 密码'
    passwordInputRef.value?.focus()
    return
  }

  errorMessage.value = ''
  saving.value = true

  try {
    if (store.config) {
      if (!store.config.form) {
        store.config.form = {
          hospitalName: '',
          orderNo: '',
          createOrderDir: false,
          orderNotes: '',
          serverAddress: '',
          serverUsername: '',
          serverPassword: '',
          svnUsername: '',
          svnPassword: '',
        }
      }
      store.config.form.svnUsername = u
      store.config.form.svnPassword = p
      await saveConfig(store.config)
    }

    // Keep localStorage in sync for web mode submitter and quick access
    localStorage.setItem('zbuild_svn_username', u)
    localStorage.setItem('zbuild.submitter', u)

    store.showToast('SVN 账户配置已保存', 'success')
    visible.value = false
    emit('success', targetAppId.value)
  } catch (err: any) {
    errorMessage.value = `保存失败: ${err.message || String(err)}`
  } finally {
    saving.value = false
  }
}

defineExpose({
  show,
  visible,
})
</script>
