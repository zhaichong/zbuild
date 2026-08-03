<template>
  <div class="card px-4 py-3 flex items-center gap-3">
    <label class="text-sm font-medium text-text-2 whitespace-nowrap">模板</label>
    <select
      v-model="selectedTemplateId"
      class="flex-1 form-input text-xs"
      @change="onTemplateChange"
    >
      <option value="">
        -- 选择模板 --
      </option>
      <option
        v-for="t in store.templates"
        :key="t.id"
        :value="t.id"
      >
        {{ t.name }}
      </option>
    </select>
    <button
      class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-primary text-white hover:opacity-90 transition-opacity cursor-pointer shrink-0"
      @click="onSaveAsTemplate"
    >
      保存模板
    </button>
    <button
      v-if="selectedTemplateId"
      class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-error-light text-error hover:bg-red-100 transition-colors cursor-pointer shrink-0"
      @click="onDeleteTemplate"
    >
      删除
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { loadTemplates, applyTemplate, saveCurrentAsTemplate, deleteTemplate } from '@/composables/useTemplates'

const store = useAppStore()
const selectedTemplateId = ref('')

onMounted(async () => {
  await loadTemplates()
})

async function onTemplateChange() {
  if (selectedTemplateId.value) {
    await applyTemplate(selectedTemplateId.value)
  }
}

async function onSaveAsTemplate() {
  const name = prompt('请输入模板名称:')
  if (!name || !name.trim()) return
  const description = prompt('请输入模板描述 (可选):') || undefined
  try {
    const t = await saveCurrentAsTemplate(name.trim(), description)
    if (t && t.id) {
      selectedTemplateId.value = t.id
    }
  } catch (e: unknown) {
    store.showToast('保存模板失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}

async function onDeleteTemplate() {
  if (!selectedTemplateId.value) return
  if (!confirm('确定要删除这个模板吗?')) return
  try {
    await deleteTemplate(selectedTemplateId.value)
    selectedTemplateId.value = ''
  } catch (e: unknown) {
    store.showToast('删除模板失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}
</script>
