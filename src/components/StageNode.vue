<template>
  <div class="stage-node" :class="[`stage-${status}`]">
    <div class="stage-icon">
      <svg v-if="status === 'done'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      <svg v-else-if="status === 'failed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
      </svg>
      <svg v-else-if="status === 'running'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="spin">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
      <svg v-else-if="status === 'skipped'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
      <span v-else class="stage-dot" />
    </div>
    <div class="stage-label">
      <span class="stage-name">{{ label }}</span>
      <span v-if="message" class="stage-msg">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StepStatusType } from '@/types'

defineProps<{
  label: string
  status: StepStatusType
  message?: string
}>()
</script>
