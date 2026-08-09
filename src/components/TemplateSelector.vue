<template>
  <div class="flex items-center gap-2">
    <!-- Template Selector Dropdown & Header Controls -->
    <div class="flex items-center gap-1.5 bg-white/15 backdrop-blur-md rounded-lg p-1 border border-white/20 shadow-2xs">
      <span class="text-xs font-semibold text-white/90 px-1.5 flex items-center gap-1 select-none shrink-0">
        <svg
          class="w-3.5 h-3.5 text-white/80"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
        模板
      </span>

      <select
        v-model="selectedTemplateId"
        class="bg-black/20 text-white text-xs rounded-md px-2 py-1 border border-white/10 outline-none cursor-pointer max-w-[160px] sm:max-w-[210px] truncate"
        style="color: #fff;"
        @change="onTemplateChange"
      >
        <option
          value=""
          style="background: #1e293b; color: #fff;"
        >
          -- 选择模板 --
        </option>
        <option
          v-for="t in store.templates"
          :key="t.id"
          :value="t.id"
          style="background: #1e293b; color: #fff;"
        >
          {{ t.name }} {{ getTemplateSummaryBadge(t) }}
        </option>
      </select>

      <!-- Details Preview Button -->
      <button
        v-if="selectedTemplate"
        type="button"
        class="px-2 py-1 rounded-md text-[11px] font-medium bg-white/20 hover:bg-white/30 text-white transition-all cursor-pointer shrink-0 flex items-center gap-1"
        title="查看模板配置明细"
        @click="showPreviewModal = true"
      >
        <span>详情</span>
      </button>

      <!-- Save Button -->
      <button
        type="button"
        class="px-2.5 py-1 rounded-md text-[11px] font-bold bg-white text-blue-700 hover:bg-blue-50 transition-all cursor-pointer shrink-0 flex items-center gap-1 shadow-xs"
        title="保存当前配置为模板"
        @click="openSaveModal"
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
            d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
          />
        </svg>
        <span>保存</span>
      </button>

      <!-- Delete Button -->
      <button
        v-if="selectedTemplateId"
        type="button"
        class="px-2 py-1 rounded-md text-[11px] font-medium bg-red-500/30 hover:bg-red-500/50 text-white transition-colors cursor-pointer"
        title="删除此模板"
        @click="openDeleteModal"
      >
        删除
      </button>
    </div>

    <!-- Save / Update Template Modal Dialog -->
    <div
      v-if="showSaveModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="showSaveModal = false"
      />
      <div class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-md z-10 flex flex-col overflow-hidden border border-border-light">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border-light">
          <h3 class="text-base font-bold text-text-1 flex items-center gap-2">
            <svg
              class="w-5 h-5 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
              />
            </svg>
            {{ isUpdating ? '更新模板' : '保存为新模板' }}
          </h3>
          <button
            class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
            @click="showSaveModal = false"
          >
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="p-6 space-y-4">
          <!-- Action Mode Toggle (Only if template is currently selected) -->
          <div
            v-if="selectedTemplate"
            class="flex p-1 bg-bg-base rounded-xl border border-border-light"
          >
            <button
              type="button"
              class="flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer"
              :class="saveMode === 'update' ? 'bg-surface text-primary shadow-xs' : 'text-text-3 hover:text-text-2'"
              @click="setSaveMode('update')"
            >
              更新已有模板 ({{ selectedTemplate.name }})
            </button>
            <button
              type="button"
              class="flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer"
              :class="saveMode === 'new' ? 'bg-surface text-primary shadow-xs' : 'text-text-3 hover:text-text-2'"
              @click="setSaveMode('new')"
            >
              另存为新模板
            </button>
          </div>

          <!-- Template Name Input -->
          <div>
            <label class="block text-xs font-medium text-text-2 mb-1">
              模板名称 <span class="text-error">*</span>
            </label>
            <input
              v-model="templateForm.name"
              type="text"
              class="w-full form-input text-xs"
              placeholder="请输入模板名称，如：日常常规版本发布"
            >
            <p
              v-if="nameError"
              class="text-[11px] text-error mt-1"
            >
              {{ nameError }}
            </p>
          </div>

          <!-- Template Description Input -->
          <div>
            <label class="block text-xs font-medium text-text-2 mb-1">
              模板描述 (可选)
            </label>
            <textarea
              v-model="templateForm.description"
              rows="2"
              class="w-full form-input text-xs resize-none"
              placeholder="添加模板使用说明或备注信息..."
            />
          </div>

          <!-- Config Summary Card -->
          <div class="rounded-xl bg-bg-base/70 border border-border-light p-3 space-y-2">
            <div class="text-xs font-semibold text-text-2 flex items-center justify-between">
              <span>将被保存的当前配置摘要</span>
              <span class="px-2 py-0.5 text-[10px] rounded-md font-bold bg-primary/10 text-primary">
                {{ store.mode === 'svn' ? 'SVN 模式' : store.mode === 'server' ? '服务器模式' : '本地模式' }}
              </span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs text-text-3">
              <div>已选项目: <span class="font-bold text-text-1">{{ store.selectedProjects.size }} 个</span></div>
              <div
                class="truncate"
                :title="store.config?.form?.hospitalName || '未设置'"
              >
                医院名称: <span class="font-bold text-text-1">{{ store.config?.form?.hospitalName || '-' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light bg-bg-base/30">
          <button
            class="px-4 py-1.5 text-xs rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="showSaveModal = false"
          >
            取消
          </button>
          <button
            class="px-5 py-1.5 text-xs font-medium rounded-xl bg-primary text-white hover:opacity-90 transition-opacity"
            @click="confirmSaveTemplate"
          >
            确认保存
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <div
      v-if="showPreviewModal && selectedTemplate"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="showPreviewModal = false"
      />
      <div class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-lg z-10 flex flex-col overflow-hidden border border-border-light max-h-[85vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border-light">
          <div>
            <h3 class="text-base font-bold text-text-1">
              模板明细预览：「{{ selectedTemplate.name }}」
            </h3>
            <p
              v-if="selectedTemplate.description"
              class="text-xs text-text-3 mt-0.5"
            >
              {{ selectedTemplate.description }}
            </p>
          </div>
          <button
            class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
            @click="showPreviewModal = false"
          >
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="p-6 overflow-y-auto space-y-4 text-xs">
          <div class="grid grid-cols-2 gap-3">
            <div class="p-2.5 rounded-xl bg-bg-base border border-border-light">
              <span class="text-text-3 block text-[11px]">执行模式</span>
              <span class="font-bold text-text-1">{{ getModeLabel(selectedTemplate) }}</span>
            </div>
            <div class="p-2.5 rounded-xl bg-bg-base border border-border-light">
              <span class="text-text-3 block text-[11px]">包含勾选项目</span>
              <span class="font-bold text-text-1">{{ getProjectCount(selectedTemplate) }} 个</span>
            </div>
          </div>

          <!-- Project List -->
          <div>
            <h4 class="font-bold text-text-2 mb-2">
              模板包含的项目与分支配置
            </h4>
            <div
              v-if="getTemplateProjects(selectedTemplate).length > 0"
              class="border border-border-light rounded-xl divide-y divide-border-light overflow-hidden max-h-[30vh] overflow-y-auto"
            >
              <div
                v-for="proj in getTemplateProjects(selectedTemplate)"
                :key="proj"
                class="px-3 py-2 bg-surface flex items-center justify-between"
              >
                <span class="font-semibold text-text-1">{{ proj }}</span>
                <span class="text-text-3 text-[11px]">
                  分支: <code class="bg-bg-base px-1.5 py-0.5 rounded text-primary">{{ getTemplateProjectBranch(selectedTemplate, proj) }}</code>
                </span>
              </div>
            </div>
            <div
              v-else
              class="text-text-3 italic p-4 text-center border border-dashed rounded-xl"
            >
              此模板未勾选特定项目
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-border-light bg-bg-base/30">
          <button
            class="px-4 py-1.5 text-xs rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="showPreviewModal = false"
          >
            关闭
          </button>
          <button
            class="px-5 py-1.5 text-xs font-medium rounded-xl bg-primary text-white hover:opacity-90 transition-opacity"
            @click="reapplyCurrentTemplate(); showPreviewModal = false"
          >
            应用此模板
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="showDeleteModal = false"
      />
      <div class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-sm z-10 flex flex-col overflow-hidden border border-border-light p-6 text-center">
        <div class="w-12 h-12 rounded-full bg-error-light text-error flex items-center justify-center mx-auto mb-3">
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </div>
        <h3 class="text-base font-bold text-text-1 mb-1">
          删除模板
        </h3>
        <p class="text-xs text-text-3 mb-5">
          确定要删除模板「<span class="font-semibold text-text-1">{{ selectedTemplate?.name }}</span>」吗？此操作无法撤销。
        </p>
        <div class="flex items-center justify-center gap-3">
          <button
            class="px-4 py-1.5 text-xs rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
            @click="showDeleteModal = false"
          >
            取消
          </button>
          <button
            class="px-5 py-1.5 text-xs font-medium rounded-xl bg-error text-white hover:opacity-90 transition-opacity"
            @click="confirmDeleteTemplate"
          >
            确认删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { loadTemplates, applyTemplate, saveCurrentAsTemplate, deleteTemplate } from '@/composables/useTemplates'
import type { TaskTemplate } from '@/types'

const store = useAppStore()
const selectedTemplateId = ref('')

const showSaveModal = ref(false)
const showDeleteModal = ref(false)
const showPreviewModal = ref(false)

const saveMode = ref<'update' | 'new'>('new')
const templateForm = ref({
  name: '',
  description: '',
})
const nameError = ref('')

watch(() => store.activeTemplateId, (newId) => {
  if (newId !== selectedTemplateId.value) {
    selectedTemplateId.value = newId
  }
})

const selectedTemplate = computed(() => {
  if (!selectedTemplateId.value) return null
  return store.templates.find(t => t.id === selectedTemplateId.value) || null
})

const isUpdating = computed(() => saveMode.value === 'update' && !!selectedTemplate.value)

onMounted(async () => {
  await loadTemplates()
})

async function onTemplateChange() {
  if (selectedTemplateId.value) {
    await applyTemplate(selectedTemplateId.value)
  } else {
    store.activeTemplateId = ''
  }
}

async function reapplyCurrentTemplate() {
  if (selectedTemplateId.value) {
    await applyTemplate(selectedTemplateId.value)
  }
}

function getTemplateSummaryBadge(t: TaskTemplate): string {
  const cfg = t.config as any
  if (!cfg) return ''
  const modeStr = cfg.uploadToServer ? '服务器' : (cfg.uploadAfterBuild === false ? '本地' : 'SVN')
  const count = Array.isArray(cfg.selectedProjects) ? cfg.selectedProjects.length : 0
  return `(${modeStr} | ${count}个项目)`
}

function getModeLabel(t: TaskTemplate): string {
  const cfg = t.config as any
  if (!cfg) return 'SVN 模式'
  if (cfg.uploadToServer) return '服务器部署模式'
  if (cfg.uploadAfterBuild === false) return '本地输出模式'
  return 'SVN 提测模式'
}

function getProjectCount(t: TaskTemplate): number {
  const cfg = t.config as any
  if (!cfg || !Array.isArray(cfg.selectedProjects)) return 0
  return cfg.selectedProjects.length
}

function getHospitalName(t: TaskTemplate): string {
  const cfg = t.config as any
  return cfg?.form?.hospitalName || ''
}

function getTemplateProjects(t: TaskTemplate): string[] {
  const cfg = t.config as any
  if (!cfg || !Array.isArray(cfg.selectedProjects)) return []
  return cfg.selectedProjects
}

function getTemplateProjectBranch(t: TaskTemplate, projName: string): string {
  const cfg = t.config as any
  if (cfg && cfg.projectBranches && cfg.projectBranches[projName]) {
    return cfg.projectBranches[projName]
  }
  return 'master'
}

function openSaveModal() {
  nameError.value = ''
  if (selectedTemplate.value) {
    saveMode.value = 'update'
    templateForm.value = {
      name: selectedTemplate.value.name,
      description: selectedTemplate.value.description || '',
    }
  } else {
    saveMode.value = 'new'
    templateForm.value = {
      name: '',
      description: '',
    }
  }
  showSaveModal.value = true
}

function setSaveMode(mode: 'update' | 'new') {
  saveMode.value = mode
  nameError.value = ''
  if (mode === 'update' && selectedTemplate.value) {
    templateForm.value.name = selectedTemplate.value.name
    templateForm.value.description = selectedTemplate.value.description || ''
  } else if (mode === 'new') {
    templateForm.value.name = selectedTemplate.value ? `${selectedTemplate.value.name} (副本)` : ''
  }
}

async function confirmSaveTemplate() {
  const name = templateForm.value.name.trim()
  if (!name) {
    nameError.value = '请填写模板名称'
    return
  }
  nameError.value = ''

  try {
    const updateId = isUpdating.value && selectedTemplate.value ? selectedTemplate.value.id : undefined
    const t = await saveCurrentAsTemplate(name, templateForm.value.description.trim() || undefined, updateId)
    if (t && t.id) {
      selectedTemplateId.value = t.id
    }
    showSaveModal.value = false
  } catch (e: unknown) {
    store.showToast('保存模板失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}

function openDeleteModal() {
  if (!selectedTemplateId.value) return
  showDeleteModal.value = true
}

async function confirmDeleteTemplate() {
  if (!selectedTemplateId.value) return
  try {
    await deleteTemplate(selectedTemplateId.value)
    selectedTemplateId.value = ''
    showDeleteModal.value = false
  } catch (e: unknown) {
    store.showToast('删除模板失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}
</script>
