<template>
  <teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/50" @click="visible = false"></div>
      <div class="relative bg-surface rounded-xl shadow-2xl p-6 w-full max-w-lg z-10">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800">系统设置</h2>
          <button class="text-gray-400 hover:text-gray-600" @click="visible = false">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="store.config" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">工作目录</label>
            <div class="flex gap-2">
              <input
                v-model="store.config.rootPath"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="选择工作目录"
              />
              <button
                class="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                @click="onChooseDir('rootPath')"
              >
                浏览
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">SVN 根 URL</label>
            <input
              v-model="store.config.svnRootUrl"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              placeholder="SVN 根 URL"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Git 路径</label>
            <div class="flex gap-2">
              <input
                v-model="store.config.tools.git"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <button
                class="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                @click="onChooseExe('git')"
              >
                浏览
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Bash 路径</label>
            <div class="flex gap-2">
              <input
                v-model="store.config.tools.bash"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <button
                class="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                @click="onChooseExe('bash')"
              >
                浏览
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">SVN 路径</label>
            <div class="flex gap-2">
              <input
                v-model="store.config.tools.svn"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <button
                class="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                @click="onChooseExe('svn')"
              >
                浏览
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">本地输出目录</label>
            <div class="flex gap-2">
              <input
                v-model="store.config.localOutputDir"
                type="text"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <button
                class="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                @click="onChooseDir('localOutputDir')"
              >
                浏览
              </button>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              class="px-4 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
              @click="visible = false"
            >
              取消
            </button>
            <button
              class="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:opacity-90 transition-opacity"
              @click="onSave"
            >
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { saveConfig } from '@/composables/useConfig'
import { ipc } from '@/services/ipc'

const store = useAppStore()
const visible = ref(false)

async function onChooseDir(field: 'rootPath' | 'localOutputDir') {
  if (!store.config) return
  const current = store.config[field] || ''
  const result = await ipc.chooseDirectory(current)
  if (result) {
    store.config[field] = result
  }
}

async function onChooseExe(tool: 'git' | 'bash' | 'svn') {
  if (!store.config) return
  const current = store.config.tools[tool] || ''
  const result = await ipc.chooseExecutable(current)
  if (result) {
    store.config.tools[tool] = result
  }
}

async function onSave() {
  if (!store.config) return
  await saveConfig(store.config)
  visible.value = false
}

defineExpose({ visible })
</script>
