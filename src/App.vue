<template>
  <div class="min-h-screen bg-bg-base">
    <div class="max-w-7xl mx-auto p-6">
      <HeaderBar />
      <div class="mt-6 space-y-6">
        <TemplateSelector />
        <CommandForm />
        <ProjectTable />
        <PipelineView />
        <LogViewer />
        <RunSummary />
      </div>
      <SettingsDialog />
      <StashDialog />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import HeaderBar from '@/components/HeaderBar.vue'
import TemplateSelector from '@/components/TemplateSelector.vue'
import CommandForm from '@/components/CommandForm.vue'
import ProjectTable from '@/components/ProjectTable.vue'
import PipelineView from '@/components/PipelineView.vue'
import LogViewer from '@/components/LogViewer.vue'
import RunSummary from '@/components/RunSummary.vue'
import SettingsDialog from '@/components/SettingsDialog.vue'
import StashDialog from '@/components/StashDialog.vue'
import { refreshProjects } from '@/composables/useProjects'
import { setupRunListeners } from '@/composables/usePipeline'

const store = useAppStore()

onMounted(async () => {
  try {
    store.config = await ipc.getConfig()
    await refreshProjects()
    setupRunListeners()
  } catch (error) {
    console.error('Failed to initialize:', error)
  }
})
</script>
