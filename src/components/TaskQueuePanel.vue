<template>
  <section class="h-full min-h-0 flex flex-col bg-white" aria-label="团队任务队列">
    <header class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
      <div>
        <h2 class="text-sm font-bold text-slate-900">团队任务</h2>
        <p class="text-[11px] text-slate-500 mt-0.5">运行中、等待队列和最近完成</p>
      </div>
      <button class="text-xs font-semibold text-blue-600 hover:text-blue-800" @click="loadTasks">
        刷新
      </button>
    </header>

    <div class="flex-1 min-h-0 overflow-auto p-3 space-y-2">
      <p v-if="loading && tasks.length === 0" class="text-xs text-slate-500 p-3">正在读取队列…</p>
      <div v-else-if="tasks.length === 0" class="rounded-xl border border-dashed border-slate-300 p-5 text-center">
        <p class="text-sm font-semibold text-slate-700">暂无团队任务</p>
        <p class="text-xs text-slate-500 mt-1">开始构建后会显示在这里，关闭页面也会继续运行。</p>
      </div>

      <article
        v-for="task in tasks"
        :key="task.taskId"
        class="rounded-xl border border-slate-200 bg-slate-50/70 p-3"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full" :class="statusDot(task.status)" />
              <span class="text-xs font-bold text-slate-800">{{ statusLabel(task.status) }}</span>
              <span v-if="task.status === 'queued'" class="text-[10px] text-slate-500">等待 #{{ task.queuePosition }}</span>
            </div>
            <p class="text-xs text-slate-700 mt-1.5 truncate">
              {{ task.projects.map((item) => `${item.name} · ${item.branch}`).join('，') || '医嘱部署任务' }}
            </p>
            <p class="text-[10px] text-slate-500 mt-1">{{ task.submitter }} · {{ formatTime(task.createdAt) }}</p>
          </div>
          <button
            v-if="task.status === 'queued' || task.status === 'preparing' || task.status === 'running'"
            class="shrink-0 text-[11px] font-semibold text-red-600 hover:text-red-800"
            @click="cancel(task.taskId)"
          >
            取消
          </button>
        </div>
        <div v-if="artifacts[task.taskId]?.length" class="mt-2 pt-2 border-t border-slate-200 flex flex-wrap gap-1.5">
          <a
            v-for="artifact in artifacts[task.taskId]"
            :key="artifact.artifactId"
            :href="webApi.getArtifactUrl(task.taskId, artifact.artifactId)"
            class="text-[11px] text-blue-700 hover:underline"
            download
          >{{ artifact.name }}</a>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { webApi } from '@/services/webApi'
import type { ArtifactSummary, TaskStatus, TaskSummary } from '@/types'

const tasks = ref<TaskSummary[]>([])
const artifacts = ref<Record<string, ArtifactSummary[]>>({})
const loading = ref(false)
let timer: number | undefined
const TASK_REFRESH_INTERVAL_MS = 15_000

async function loadTasks() {
  if (loading.value) return
  loading.value = true
  try {
    tasks.value = await webApi.listTasks()
    const completed = tasks.value.filter((item) => item.status === 'success').slice(0, 10)
    for (const task of completed) {
      if (artifacts.value[task.taskId]) continue
      const detail = await webApi.getTask(task.taskId)
      artifacts.value[task.taskId] = detail.artifacts
    }
  } finally {
    loading.value = false
  }
}

async function cancel(taskId: string) {
  await webApi.cancelTask(taskId)
  await loadTasks()
}

function statusLabel(status: TaskStatus) {
  return ({ queued: '等待中', preparing: '准备工作区', running: '构建中', success: '已完成', failed: '失败', cancelled: '已取消', interrupted: '服务中断' })[status]
}

function statusDot(status: TaskStatus) {
  if (status === 'success') return 'bg-emerald-500'
  if (status === 'failed' || status === 'interrupted') return 'bg-red-500'
  if (status === 'cancelled') return 'bg-slate-400'
  if (status === 'queued') return 'bg-amber-500'
  return 'bg-blue-500 animate-pulse'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  loadTasks().catch(() => {})
  timer = window.setInterval(() => loadTasks().catch(() => {}), TASK_REFRESH_INTERVAL_MS)
})
onBeforeUnmount(() => window.clearInterval(timer))
</script>
