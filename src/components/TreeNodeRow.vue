<template>
  <div
    class="grid grid-cols-12 gap-2 px-3 py-2 items-center text-xs hover:bg-slate-50 transition-colors border-b border-border/30 last:border-b-0"
    :class="{ 'bg-blue-50/40': isSelected }"
  >
    <!-- Column 1: Expand Arrow + Icon + Name + Badge -->
    <div
      class="col-span-6 sm:col-span-5 flex items-center min-w-0"
      :style="{ paddingLeft: `${depth * 18}px` }"
    >
      <!-- Expand button for folders -->
      <button
        v-if="isDir"
        type="button"
        class="w-4 h-4 flex items-center justify-center text-slate-400 hover:text-slate-700 cursor-pointer shrink-0 mr-1 select-none text-[10px]"
        @click="emit('toggle-expand', node.id)"
      >
        {{ isExpanded ? '▼' : '▶' }}
      </button>
      <span v-else class="w-4 mr-1 shrink-0" />

      <!-- Icon -->
      <span class="mr-1.5 text-sm select-none shrink-0">
        <template v-if="isDir">{{ isExpanded ? '📂' : '📁' }}</template>
        <template v-else-if="node.isFrontendPackage">📦</template>
        <template v-else>📄</template>
      </span>

      <!-- Name + Open hint -->
      <span
        class="truncate font-mono select-none"
        :class="[
          isDir ? 'font-bold text-slate-800 cursor-pointer' : '',
          node.isFrontendPackage ? 'font-semibold text-slate-900' : 'text-slate-700',
          !isDir ? 'cursor-pointer hover:text-blue-600 hover:underline' : ''
        ]"
        :title="isDir ? node.relativePath : `双击打开此文件 (${node.name})`"
        @click="isDir ? emit('toggle-expand', node.id) : undefined"
        @dblclick="!isDir ? emit('open-file', node) : undefined"
      >
        {{ node.name }}
      </span>

      <!-- Preview open icon button for non-dirs -->
      <button
        v-if="!isDir"
        type="button"
        class="ml-1 text-slate-400 hover:text-blue-600 opacity-60 hover:opacity-100 transition-opacity p-0.5 cursor-pointer shrink-0"
        :title="`打开/查看 ${node.name}`"
        @click="emit('open-file', node)"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </button>

      <!-- Frontend package badge -->
      <span
        v-if="node.isFrontendPackage && !isDir"
        class="ml-1.5 px-1.5 py-0.2 text-[10px] rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-sans font-medium shrink-0"
      >
        前端包
      </span>
    </div>

    <!-- Column 2: Size -->
    <div class="col-span-2 sm:col-span-2 text-center text-slate-400 font-mono text-[11px] truncate">
      {{ node.sizeFormatted || (isDir ? '-' : '') }}
    </div>

    <!-- Column 3: Target Server Path (Editable for frontend packages) -->
    <div class="col-span-4 sm:col-span-3 min-w-0">
      <input
        v-if="!isDir && node.isFrontendPackage"
        type="text"
        class="w-full px-2 py-0.5 text-[11px] font-mono border border-slate-200 rounded bg-white text-slate-700 focus:border-blue-500 outline-none"
        :value="currentTargetPath"
        placeholder="/home/data/web"
        @input="onPathInput"
      >
      <span v-else class="text-[11px] text-slate-400 font-mono truncate block">
        {{ currentTargetPath || '-' }}
      </span>
    </div>

    <!-- Column 4: Selection Checkbox & Single Select Radio -->
    <div class="col-span-12 sm:col-span-2 flex items-center justify-end gap-2 shrink-0 select-none">
      <template v-if="!isDir">
        <button
          type="button"
          class="text-[11px] text-slate-400 hover:text-blue-600 cursor-pointer mr-1 hidden sm:inline-block"
          title="仅勾选此包"
          @click="emit('select-only', node)"
        >
          仅选
        </button>
        <input
          type="checkbox"
          class="w-4 h-4 accent-blue-600 cursor-pointer rounded"
          :checked="isSelected"
          @change="onCheckboxChange"
        >
      </template>
      <template v-else>
        <span
          class="text-[11px] text-slate-400 cursor-pointer hover:text-slate-600"
          @click="emit('toggle-expand', node.id)"
        >
          {{ hasChildren ? `${node.children?.length} 项` : '目录' }}
        </span>
      </template>
    </div>
  </div>

  <!-- Recursive Children -->
  <template v-if="isDir && isExpanded && hasChildren">
    <TreeNodeRow
      v-for="child in node.children"
      :key="child.id"
      :node="child"
      :depth="depth + 1"
      :expanded-keys="expandedKeys"
      :selected-map="selectedMap"
      :target-paths="targetPaths"
      @toggle-expand="(id) => emit('toggle-expand', id)"
      @toggle-select="(n, c) => emit('toggle-select', n, c)"
      @select-only="(n) => emit('select-only', n)"
      @update-path="(id, p) => emit('update-path', id, p)"
      @open-file="(n) => emit('open-file', n)"
    />
  </template>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SvnTreeNode } from '@/types'

defineOptions({
  name: 'TreeNodeRow',
})

const props = defineProps<{
  node: SvnTreeNode
  depth: number
  expandedKeys: Record<string, boolean>
  selectedMap: Record<string, boolean>
  targetPaths: Record<string, string>
}>()

const emit = defineEmits<{
  'toggle-expand': [nodeId: string]
  'toggle-select': [node: SvnTreeNode, checked: boolean]
  'select-only': [node: SvnTreeNode]
  'update-path': [nodeId: string, path: string]
  'open-file': [node: SvnTreeNode]
}>()

const isDir = computed(() => props.node.kind === 'dir')
const isExpanded = computed(() => isDir.value && Boolean(props.expandedKeys[props.node.id]))
const hasChildren = computed(() => isDir.value && Array.isArray(props.node.children) && props.node.children.length > 0)
const isSelected = computed(() => !isDir.value && Boolean(props.selectedMap[props.node.id]))

const currentTargetPath = computed(() => {
  return (
    props.targetPaths[props.node.id] ||
    props.node.matchedServerPath ||
    (props.node.isFrontendPackage ? '/home/data/web' : '')
  )
})

function onCheckboxChange(e: Event) {
  const target = e.target as HTMLInputElement
  emit('toggle-select', props.node, target.checked)
}

function onPathInput(e: Event) {
  const target = e.target as HTMLInputElement
  emit('update-path', props.node.id, target.value)
}
</script>
