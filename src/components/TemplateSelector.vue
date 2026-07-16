<template>
  <div class="bg-surface rounded-lg shadow-sm p-4">
    <div class="flex items-center gap-3">
      <label class="text-sm font-medium text-gray-700">任务模板</label>
      <select
        v-model="selectedTemplateId"
        class="flex-1 max-w-xs px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
        @change="onTemplateChange"
      >
        <option value="">-- 选择模板 --</option>
        <option v-for="t in store.templates" :key="t.id" :value="t.id">
          {{ t.name }}
        </option>
      </select>
      <button
        class="px-3 py-2 text-sm bg-primary text-white rounded-lg hover:opacity-90 transition-opacity"
        @click="onSaveAsTemplate"
      >
        保存为模板
      </button>
      <button
        v-if="selectedTemplateId"
        class="px-3 py-2 text-sm bg-error text-white rounded-lg hover:opacity-90 transition-opacity"
        @click="onDeleteTemplate"
      >
        删除模板
      </button>
    </div>
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
  if (!name) return
  const description = prompt('请输入模板描述 (可选):') || undefined
  await saveCurrentAsTemplate(name, description)
}

async function onDeleteTemplate() {
  if (!selectedTemplateId.value) return
  if (!confirm('确定要删除这个模板吗?')) return
  await deleteTemplate(selectedTemplateId.value)
  selectedTemplateId.value = ''
}
</script>
