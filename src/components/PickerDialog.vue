<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center"
  >
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      @click="visible = false"
    />
    <div
      class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-md z-10 flex flex-col overflow-hidden"
      style="max-height: 70vh;"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-5 pt-4 pb-3 border-b border-border-light">
        <h2 class="text-base font-bold text-text-1">
          {{ title }}
        </h2>
        <button
          class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
          @click="visible = false"
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

      <!-- Search -->
      <div class="px-5 py-3 border-b border-border-light">
        <div class="relative">
          <svg
            class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-3"
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
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            class="w-full pl-8 pr-3 py-2 text-sm rounded-xl border border-border-light bg-bg-base text-text-1 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-colors"
            placeholder="搜索..."
            autofocus
          >
        </div>
      </div>

      <!-- List -->
      <div class="flex-1 min-h-0 overflow-auto px-3 py-2">
        <div
          v-if="filteredItems.length === 0"
          class="text-xs text-text-3 text-center py-8"
        >
          无匹配项
        </div>
        <div
          v-for="item in filteredItems"
          :key="item"
          class="px-3 py-2 text-sm rounded-xl cursor-pointer transition-colors"
          :class="selectedValue === item
            ? 'bg-primary/10 text-primary font-medium'
            : 'text-text-1 hover:bg-border-light'"
          @click="selectItem(item)"
          @dblclick="confirmItem(item)"
        >
          {{ item }}
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-5 py-3 border-t border-border-light">
        <button
          class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors"
          @click="visible = false"
        >
          取消
        </button>
        <button
          class="px-5 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!selectedValue"
          @click="handleOk"
        >
          确定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps<{
  title: string
  items: string[]
  currentValue?: string
}>()

const visible = ref(false)
const searchQuery = ref('')
const selectedValue = ref('')
const searchInput = ref<HTMLInputElement>()

const filteredItems = computed(() => {
  if (!searchQuery.value) return props.items
  const q = searchQuery.value.toLowerCase()
  return props.items.filter((item) => item.toLowerCase().includes(q))
})

watch(
  () => props.currentValue,
  (val) => {
    selectedValue.value = val || ''
  },
)

function selectItem(item: string) {
  selectedValue.value = item
}

function confirmItem(item: string) {
  selectedValue.value = item
  emit('choose', item)
  visible.value = false
}

function handleOk() {
  if (selectedValue.value) {
    emit('choose', selectedValue.value)
    visible.value = false
  }
}

const emit = defineEmits<{
  choose: [value: string]
}>()

function show(currentValue?: string) {
  searchQuery.value = ''
  selectedValue.value = currentValue || props.currentValue || ''
  visible.value = true
  nextTick(() => {
    searchInput.value?.focus()
  })
}

defineExpose({ visible, show })
</script>
