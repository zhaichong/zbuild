<template>
  <dialog ref="dialogRef" class="modal" @close="onClose">
    <form method="dialog" class="modal-card picker-card">
      <div class="modal-header">
        <div>
          <div class="section-label">快速选择</div>
          <h2>{{ title }}</h2>
        </div>
        <button class="plain-close" value="cancel" aria-label="关闭">×</button>
      </div>
      <input
        v-model="search"
        class="picker-search"
        placeholder="输入关键字搜索"
        @input="onSearch"
      />
      <div class="picker-list">
        <button
          v-for="item in filtered"          :key="item"          type="button"
          class="picker-item"          :class="{ active: selected === item }"
          @click="selected = item"
        >
          {{ item }}
        </button>
        <p v-if="!filtered.length" class="picker-empty">无匹配结果</p>
      </div>
      <div class="modal-actions">
        <button class="button ghost" value="cancel">取消</button>
        <button class="button primary" :disabled="!selected" @click.prevent="onConfirm">确定</button>
      </div>
    </form>
  </dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  title: string
  items: string[]
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'confirm', value: string): void
}>()

const dialogRef = ref<HTMLDialogElement>()
const search = ref('')
const selected = ref(props.modelValue || '')

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.items
  return props.items.filter(i => i.toLowerCase().includes(q))
})

function onSearch() {
  if (!filtered.value.includes(selected.value)) selected.value = ''
}

function onConfirm() {
  if (!selected.value) return
  emit('update:modelValue', selected.value)
  emit('confirm', selected.value)
  dialogRef.value?.close(selected.value)
}

function onClose() {
  search.value = ''
}

function open() {
  dialogRef.value?.showModal()
}

defineExpose({ open })
</script>
