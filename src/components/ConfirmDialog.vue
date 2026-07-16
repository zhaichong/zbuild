<template>
  <dialog ref="dialogRef" class="modal confirm-modal">
    <form method="dialog" class="modal-card confirm-card">
      <div class="modal-header">
        <div>
          <div class="section-label">任务确认</div>
          <h2>确认开始打包</h2>
        </div>
        <button class="plain-close" value="cancel" aria-label="关闭">×</button>
      </div>
      <div class="confirm-body">
        <div class="confirm-summary">
          <span>模式: <strong>{{ mode }}</strong></span>
          <span v-if="hospital">医院: <strong>{{ hospital }}</strong></span>
          <span v-if="order">订单: <strong>{{ order }}</strong></span>
        </div>
        <div class="confirm-projects">
          <div v-for="p in projects" :key="p" class="confirm-project">
            {{ p }}
          </div>
        </div>
      </div>
      <div class="modal-actions">
        <button class="button ghost" value="cancel">取消</button>
        <button class="button primary" @click.prevent="$emit('confirm')">开始执行</button>
      </div>
    </form>
  </dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  mode: string
  hospital?: string
  order?: string
  projects: string[]
}>()

defineEmits<{ (e: 'confirm'): void }>()

const dialogRef = ref<HTMLDialogElement>()

function open() {
  dialogRef.value?.showModal()
}

defineExpose({ open })
</script>
