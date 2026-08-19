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
          class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light cursor-pointer"
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
            placeholder="搜索关键词，点击项目或按回车确定..."
            autofocus
            @keydown.enter.prevent="handleOk"
          >
        </div>
      </div>

      <!-- List -->
      <div class="flex-1 min-h-0 overflow-auto px-3 py-2 space-y-1">
        <!-- Custom Input Action Row when user types a non-exact query -->
        <div
          v-if="searchQuery.trim() && !exactMatchInItems"
          class="px-3 py-2 text-sm rounded-xl cursor-pointer transition-all bg-blue-50 hover:bg-blue-100/80 border border-blue-200 text-blue-700 font-medium flex items-center justify-between shadow-2xs"
          @click="confirmItem(searchQuery.trim())"
        >
          <span class="truncate">➕ 使用输入: <strong>{{ searchQuery.trim() }}</strong></span>
          <span class="text-xs text-blue-500 shrink-0 ml-2 font-mono">按回车确认</span>
        </div>

        <div
          v-if="filteredItems.length === 0 && !searchQuery.trim()"
          class="text-xs text-text-3 text-center py-8 space-y-1"
        >
          <div class="font-medium text-slate-500">暂无列表选项</div>
          <div class="text-[11px] text-slate-400">可在上方搜索框直接输入自定义内容并确认</div>
        </div>

        <div
          v-else-if="filteredItems.length === 0 && searchQuery.trim() && exactMatchInItems"
          class="text-xs text-text-3 text-center py-8"
        >
          无匹配项
        </div>

        <div
          v-for="item in filteredItems"
          :key="item"
          class="px-3 py-2 text-sm rounded-xl cursor-pointer transition-colors"
          :class="effectiveSelectedValue === item
            ? 'bg-primary/10 text-primary font-medium border border-primary/20'
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
          class="px-4 py-2 text-sm rounded-xl border border-border text-text-2 hover:bg-border-light transition-colors cursor-pointer"
          @click="visible = false"
        >
          取消
        </button>
        <button
          class="px-5 py-2 text-sm rounded-xl bg-primary text-white hover:opacity-90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          :disabled="!effectiveSelectedValue"
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
  if (!searchQuery.value.trim()) return props.items || []
  const q = searchQuery.value.trim().toLowerCase()
  return (props.items || []).filter((item) => item.toLowerCase().includes(q))
})

const exactMatchInItems = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return (props.items || []).some((item) => item.toLowerCase() === q)
})

// 计算有效的当前选中项（支持搜索框手动高亮、匹配第一项或直接输入）
const effectiveSelectedValue = computed(() => {
  const q = searchQuery.value.trim()
  if (selectedValue.value && filteredItems.value.includes(selectedValue.value)) {
    return selectedValue.value
  }
  if (filteredItems.value.length > 0) {
    return filteredItems.value[0]
  }
  if (q) {
    return q
  }
  return selectedValue.value || ''
})

watch(
  () => props.currentValue,
  (val) => {
    selectedValue.value = val || ''
  },
)

watch(filteredItems, (list) => {
  if (list.length > 0 && (!selectedValue.value || !list.includes(selectedValue.value))) {
    selectedValue.value = list[0]
  }
})

function selectItem(item: string) {
  selectedValue.value = item
}

function confirmItem(item: string) {
  const val = (item || '').trim()
  if (!val) return
  selectedValue.value = val
  emit('choose', val)
  visible.value = false
}

function handleOk() {
  const q = searchQuery.value.trim()
  const val = (q && !filteredItems.value.includes(selectedValue.value)) ? q : (effectiveSelectedValue.value || q)
  if (val) {
    confirmItem(val)
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
