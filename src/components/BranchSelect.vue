<template>
  <div
    ref="containerRef"
    class="relative inline-block w-full max-w-[280px]"
  >
    <!-- Trigger Button / Display Box -->
    <div
      class="flex items-center justify-between px-3 py-1.5 border rounded-xl text-xs bg-white font-mono font-bold transition-all shadow-2xs cursor-pointer select-none group"
      :class="isOpen ? 'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/10' : 'border-slate-200 text-slate-900 hover:border-blue-400 hover:bg-slate-50/80'"
      @click="toggleDropdown"
    >
      <div class="flex items-center gap-1.5 min-w-0 flex-1">
        <!-- Git Branch Icon -->
        <svg
          class="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 shrink-0 transition-colors"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
          />
        </svg>
        <span
          class="truncate text-left"
          :class="modelValue ? 'text-slate-900 font-bold' : 'text-slate-400 font-normal'"
          :title="modelValue || '选择或搜索分支'"
        >
          {{ modelValue || '选择或搜索分支...' }}
        </span>
      </div>

      <!-- Chevron Down Arrow -->
      <svg
        class="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 shrink-0 ml-1.5 transition-transform duration-200"
        :class="{ 'rotate-180 text-blue-600': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </div>

    <!-- Dropdown Menu Panel (Teleported to body with highest z-index) -->
    <teleport to="body">
      <transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="transform scale-95 opacity-0 -translate-y-1"
        enter-to-class="transform scale-100 opacity-100 translate-y-0"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="transform scale-100 opacity-100 translate-y-0"
        leave-to-class="transform scale-95 opacity-0 -translate-y-1"
      >
        <div
          v-if="isOpen"
          ref="dropdownPanelRef"
          :style="dropdownStyle"
          class="bg-white border border-slate-200/90 rounded-2xl shadow-2xl overflow-hidden flex flex-col backdrop-blur-md"
          @click.stop
        >
          <!-- Search Input Header -->
          <div class="p-2.5 border-b border-slate-100 bg-slate-50/90 sticky top-0 z-10">
            <div class="relative flex items-center">
              <svg
                class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 pointer-events-none"
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
                ref="searchInputRef"
                v-model="searchQuery"
                type="text"
                class="w-full pl-8 pr-7 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-2xs"
                placeholder="模糊搜索分支或输入新分支..."
                @keydown.down.prevent="navigateDown"
                @keydown.up.prevent="navigateUp"
                @keydown.enter.prevent="selectHighlightedOrCustom"
                @keydown.esc="closeDropdown"
              />
              <button
                v-if="searchQuery"
                type="button"
                class="absolute right-2 text-slate-400 hover:text-slate-600 text-xs p-0.5 rounded cursor-pointer"
                @click="searchQuery = ''"
              >
                ✕
              </button>
            </div>
          </div>

          <!-- Branch List Container -->
          <div
            ref="listRef"
            class="flex-1 overflow-y-auto p-1.5 space-y-0.5 text-xs font-mono select-none"
            style="max-height: 240px;"
          >
            <!-- Exact/Custom Input Option if not found in list -->
            <div
              v-if="canUseCustomBranch"
              class="px-2.5 py-1.5 rounded-lg cursor-pointer flex items-center justify-between text-blue-600 bg-blue-50/70 hover:bg-blue-100/80 transition-colors font-bold"
              @click="selectBranch(searchQuery.trim())"
            >
              <div class="flex items-center gap-1.5 truncate">
                <span class="text-blue-500">＋</span>
                <span class="truncate">使用分支: <strong>{{ searchQuery.trim() }}</strong></span>
              </div>
              <span class="text-[10px] text-blue-500 uppercase font-sans font-bold">回车确认</span>
            </div>

            <!-- Filtered Branches -->
            <div
              v-for="(item, idx) in filteredBranches"
              :key="item"
              class="px-2.5 py-1.5 rounded-lg cursor-pointer flex items-center justify-between transition-colors"
              :class="[
                item === modelValue
                  ? 'bg-blue-50 text-blue-700 font-extrabold'
                  : highlightedIndex === idx
                    ? 'bg-slate-100 text-slate-900 font-bold'
                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900 font-medium'
              ]"
              @mouseenter="highlightedIndex = idx"
              @click="selectBranch(item)"
            >
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <!-- Checkmark for selected item -->
                <svg
                  v-if="item === modelValue"
                  class="w-3.5 h-3.5 text-blue-600 shrink-0"
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
                <span
                  v-else
                  class="w-3.5 h-3.5 shrink-0"
                />

                <span
                  class="truncate"
                  :title="item"
                  v-html="highlightMatch(item, searchQuery)"
                />
              </div>

              <!-- Custom Command Badge if matches -->
              <span
                v-if="hasCustomCommand(item)"
                class="text-[10px] px-1 py-0.5 rounded bg-amber-100 text-amber-700 border border-amber-200 font-bold ml-1.5 shrink-0"
                title="专属打包命令"
              >
                ⚡
              </span>
            </div>

            <!-- Empty State -->
            <div
              v-if="filteredBranches.length === 0 && !canUseCustomBranch"
              class="py-6 text-center text-slate-400 text-xs"
            >
              <p>未找到匹配的分支</p>
            </div>
          </div>

          <!-- Footer / Branch Count Summary -->
          <div class="px-3 py-1.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 font-sans">
            <span>共 {{ branches.length }} 个分支</span>
            <span v-if="filteredBranches.length < branches.length">匹配到 {{ filteredBranches.length }} 个</span>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted, CSSProperties } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    branches: string[]
    projectName?: string
    customCommands?: Record<string, string>
  }>(),
  {
    modelValue: '',
    branches: () => [],
    projectName: '',
    customCommands: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(0)
const dropdownStyle = ref<CSSProperties>({})

const containerRef = ref<HTMLElement | null>(null)
const dropdownPanelRef = ref<HTMLElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)
const listRef = ref<HTMLElement | null>(null)

// Calculate fixed position on viewport to completely bypass table overflow boundaries
function updatePosition() {
  if (!isOpen.value || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const panelHeight = 320 // estimated panel height
  const spaceBelow = viewportHeight - rect.bottom
  const spaceAbove = rect.top

  const isDropUp = spaceBelow < panelHeight && spaceAbove > spaceBelow
  const width = Math.max(rect.width, 290)

  if (isDropUp) {
    dropdownStyle.value = {
      position: 'fixed',
      left: `${rect.left}px`,
      bottom: `${viewportHeight - rect.top + 6}px`,
      width: `${width}px`,
      maxWidth: '380px',
      maxHeight: `${Math.min(panelHeight, spaceAbove - 16)}px`,
      zIndex: 99999,
    }
  } else {
    dropdownStyle.value = {
      position: 'fixed',
      left: `${rect.left}px`,
      top: `${rect.bottom + 6}px`,
      width: `${width}px`,
      maxWidth: '380px',
      maxHeight: `${Math.min(panelHeight, spaceBelow - 16)}px`,
      zIndex: 99999,
    }
  }
}

// Fuzzy filter matching
const filteredBranches = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return props.branches

  return props.branches.filter((b) => {
    const branchLower = b.toLowerCase()
    if (branchLower.includes(q)) return true
    let qIdx = 0
    for (let i = 0; i < branchLower.length && qIdx < q.length; i++) {
      if (branchLower[i] === q[qIdx]) {
        qIdx++
      }
    }
    return qIdx === q.length
  })
})

const canUseCustomBranch = computed(() => {
  const q = searchQuery.value.trim()
  if (!q) return false
  return !props.branches.some((b) => b.toLowerCase() === q.toLowerCase())
})

function hasCustomCommand(branch: string): boolean {
  if (!props.customCommands || !branch) return false
  if (props.customCommands[branch]) return true
  for (const pat of Object.keys(props.customCommands)) {
    if (pat.endsWith('*') && branch.startsWith(pat.slice(0, -1))) {
      return true
    }
  }
  return false
}

function highlightMatch(text: string, query: string): string {
  if (!query.trim()) return escapeHtml(text)
  const q = query.trim()
  const idx = text.toLowerCase().indexOf(q.toLowerCase())
  if (idx !== -1) {
    const before = escapeHtml(text.slice(0, idx))
    const match = escapeHtml(text.slice(idx, idx + q.length))
    const after = escapeHtml(text.slice(idx + q.length))
    return `${before}<mark class="bg-amber-200 text-slate-900 rounded-xs px-0.5 font-bold">${match}</mark>${after}`
  }
  return escapeHtml(text)
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function toggleDropdown() {
  if (isOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

function openDropdown() {
  isOpen.value = true
  searchQuery.value = ''
  highlightedIndex.value = 0

  nextTick(() => {
    updatePosition()
    searchInputRef.value?.focus()
    const selectedIdx = filteredBranches.value.indexOf(props.modelValue)
    if (selectedIdx >= 0) {
      highlightedIndex.value = selectedIdx
      scrollHighlightedIntoView()
    }
  })

  // Listen to viewport scroll/resize to dynamically reposition
  window.addEventListener('scroll', updatePosition, true)
  window.addEventListener('resize', updatePosition)
}

function closeDropdown() {
  isOpen.value = false
  searchQuery.value = ''
  window.removeEventListener('scroll', updatePosition, true)
  window.removeEventListener('resize', updatePosition)
}

function selectBranch(branch: string) {
  if (!branch) return
  emit('update:modelValue', branch)
  emit('change', branch)
  closeDropdown()
}

function navigateDown() {
  if (filteredBranches.value.length === 0) return
  if (highlightedIndex.value < filteredBranches.value.length - 1) {
    highlightedIndex.value++
    scrollHighlightedIntoView()
  }
}

function navigateUp() {
  if (highlightedIndex.value > 0) {
    highlightedIndex.value--
    scrollHighlightedIntoView()
  }
}

function selectHighlightedOrCustom() {
  if (canUseCustomBranch.value && filteredBranches.value.length === 0) {
    selectBranch(searchQuery.value.trim())
    return
  }
  if (filteredBranches.value[highlightedIndex.value]) {
    selectBranch(filteredBranches.value[highlightedIndex.value])
  } else if (searchQuery.value.trim()) {
    selectBranch(searchQuery.value.trim())
  }
}

function scrollHighlightedIntoView() {
  nextTick(() => {
    if (!listRef.value) return
    const items = listRef.value.children
    if (items[highlightedIndex.value]) {
      (items[highlightedIndex.value] as HTMLElement).scrollIntoView({
        block: 'nearest',
      })
    }
  })
}

// Click outside handler
function handleDocumentClick(e: MouseEvent) {
  if (!isOpen.value) return
  const target = e.target as Node
  const isInsideTrigger = containerRef.value?.contains(target)
  const isInsidePanel = dropdownPanelRef.value?.contains(target)
  if (!isInsideTrigger && !isInsidePanel) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
  window.removeEventListener('scroll', updatePosition, true)
  window.removeEventListener('resize', updatePosition)
})

// Reset highlight and update position when search results resize panel
watch(searchQuery, () => {
  highlightedIndex.value = 0
  nextTick(updatePosition)
})
</script>
