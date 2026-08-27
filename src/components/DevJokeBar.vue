<template>
  <div
    class="flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl border border-amber-200/70 bg-gradient-to-r from-amber-50/80 via-orange-50/50 to-amber-50/70 shadow-2xs transition-all hover:border-amber-300 select-none group"
  >
    <!-- Joke Icon & Content -->
    <div class="flex items-center gap-2.5 min-w-0 flex-1">
      <div
        class="w-7 h-7 rounded-lg bg-amber-100/90 text-amber-700 flex items-center justify-center text-sm shrink-0 border border-amber-200/80 shadow-2xs group-hover:scale-105 transition-transform"
        :title="'摸鱼驿站 · 第 ' + currentJoke.id + ' 条段子'"
      >
        <span>{{ currentJoke.emoji || '💡' }}</span>
      </div>

      <div class="min-w-0 flex-1 flex flex-col sm:flex-row sm:items-center sm:gap-2">
        <span class="text-[11px] font-bold text-amber-800/90 shrink-0 bg-amber-200/60 px-1.5 py-0.5 rounded text-center w-fit">
          {{ currentJoke.tag || '极客段子' }}
        </span>
        <p
          class="text-xs text-slate-800 font-medium truncate tracking-tight transition-all"
          :title="currentJoke.punchline ? `${currentJoke.setup} —— ${currentJoke.punchline}` : currentJoke.setup"
        >
          <span class="font-semibold text-slate-900">{{ currentJoke.setup }}</span>
          <span v-if="currentJoke.punchline" class="text-amber-900 font-bold ml-1.5">
            {{ currentJoke.punchline }}
          </span>
        </p>
      </div>
    </div>

    <!-- Actions / Next Joke Button -->
    <div class="flex items-center gap-1.5 shrink-0">
      <span class="text-[10px] text-amber-700/60 font-mono hidden md:inline-block">
        已看 {{ seenCount }}/{{ jokePool.length }}
      </span>

      <button
        type="button"
        class="flex items-center gap-1 px-2 py-1 text-xs font-bold text-amber-800 bg-white/90 border border-amber-200/80 rounded-lg hover:bg-amber-100/80 hover:text-amber-950 transition-all cursor-pointer shadow-2xs active:scale-95"
        title="换一个段子 (每次打包也会自动切换且不重复)"
        @click="nextJoke(true)"
      >
        <span class="text-xs">🎲</span>
        <span class="text-[11px]">换一个</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'

export interface DevJoke {
  id: number
  emoji: string
  tag: string
  setup: string
  punchline?: string
}

const jokePool: DevJoke[] = [
  { id: 1, emoji: '☕', tag: '程序员日常', setup: '为什么程序员总是分不清万圣节和圣诞节？', punchline: '因为 Oct 31 == Dec 25。' },
  { id: 2, emoji: '🐛', tag: 'Bug哲学', setup: '代码能跑就千万别动，', punchline: '哪怕它看起来像依托答辩。' },
  { id: 3, emoji: '🚀', tag: '上线玄学', setup: '周五下午四点半，', punchline: '是任何勇士都不敢点「部署上线」的神圣时刻。' },
  { id: 4, emoji: '🦆', tag: '代码调试', setup: '最快的 Debug 方法：', punchline: '在工位上放一只小黄鸭，给它讲一遍代码逻辑。' },
  { id: 5, emoji: '💤', tag: '睡眠法则', setup: '世界上只有 10 种人：', punchline: '懂二进制的，和不懂二进制的。' },
  { id: 6, emoji: '🔥', tag: '打包时刻', setup: '构建进度走到 99% 时，', punchline: '才是检验开发人员心理承受能力的真正开始。' },
  { id: 7, emoji: '⌨️', tag: '键盘哲学', setup: '只要我把键盘敲得足够响，', punchline: '产品经理就以为我在写核心架构。' },
  { id: 8, emoji: '📦', tag: '依赖黑洞', setup: '黑洞是宇宙中质量最大的天体，', punchline: '直到它遇到了 node_modules 文件夹。' },
  { id: 9, emoji: '☕', tag: '极客语录', setup: '问：如何让一个程序员闭嘴？', punchline: '答：问他 Vim 怎么退出。' },
  { id: 10, emoji: '🎯', tag: '需求变更', setup: '产品经理：这个需求很简单，怎么实现我不管，', punchline: '明天上线！' },
  { id: 11, emoji: '🔮', tag: '玄学修复', setup: '重启、重新安装依赖、git clean -fdx，', punchline: '程序员的三板斧能解决 90% 的宇宙难题。' },
  { id: 12, emoji: '🍜', tag: '深夜加班', setup: '一入前端深似海，', punchline: '从此框架天天改。昨天 Vue 3，今天全栈跑。' },
  { id: 13, emoji: '🛡️', tag: '防御编程', setup: '一个优秀的程序员过马路时，', punchline: '会先看左边，再看右边，然后再看一次左边。' },
  { id: 14, emoji: '🧪', tag: '单元测试', setup: '一个测试工程师走进一家酒吧，要了一杯啤酒，要了 0 杯啤酒，', punchline: '要了 9999999 杯啤酒，要了一只蜥蜴。' },
  { id: 15, emoji: '☕', tag: '生活真相', setup: '代码里没有注释，只有上帝和我懂它；', punchline: '一个月后，就只有上帝懂了。' },
  { id: 16, emoji: '🧙‍♂️', tag: '架构大师', setup: '所谓的微服务，', punchline: '就是把一个大 Bug 拆解成二十个分布式调用小 Bug。' },
  { id: 17, emoji: '🤖', tag: 'AI时代', setup: '以前写代码：复制粘贴 StackOverflow；', punchline: '现在写代码：静静等待 Copilot 帮我编完。' },
  { id: 18, emoji: '🐱', tag: '摸鱼技巧', setup: '摸鱼不是偷懒，', punchline: '是给 CPU 和内存释放碎片整理缓存的高尚行为。' },
  { id: 19, emoji: '⚡', tag: '快如闪电', setup: '编译速度决定了程序员的喝咖啡频率，', punchline: '现在 Vite 这么快，咖啡都来不及泡了！' },
  { id: 20, emoji: '🌟', tag: '极客浪漫', setup: 'printf("Hello World");', punchline: '是每一个数字宇宙诞生的第一声啼鸣。' },
  { id: 21, emoji: '🛠️', tag: '排错日常', setup: '在代码里写 // TODO: 临时修复，稍后重构', punchline: '该注释往往存活时间比公司寿命还长。' },
  { id: 22, emoji: '🍺', tag: '周末时光', setup: '千万不要问程序员周末有什么计划，', punchline: '他们通常在计划怎样不写 Bug。' },
  { id: 23, emoji: '🍕', tag: '极客冷笑话', setup: '为什么程序员戴眼镜？', punchline: '因为他们不能 C# (see sharp)。' },
  { id: 24, emoji: '🕹️', tag: '版本控制', setup: '最恐怖的三个词不是我爱你，', punchline: '而是 git push --force origin master。' },
  { id: 25, emoji: '🎪', tag: '前端日常', setup: 'CSS 居中到底有多少种写法？', punchline: '没人知道全部，但 flex: 1 永远是你最好的朋友。' },
  { id: 26, emoji: '🎉', tag: '终极解法', setup: '“在我的机器上是好的！”', punchline: '—— 那我们就把你的电脑打包送给客户吧。' },
]

const STORAGE_KEY_SEEN = 'zbuild_joke_seen_ids'
const STORAGE_KEY_CURRENT = 'zbuild_joke_current_id'

const store = useAppStore()
const currentJoke = ref<DevJoke>(jokePool[0])
const seenCount = ref(0)

function loadSeenIds(): number[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_SEEN)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveSeenIds(ids: number[]) {
  try {
    localStorage.setItem(STORAGE_KEY_SEEN, JSON.stringify(ids))
    seenCount.value = ids.length
  } catch {
    // ignore
  }
}

// Pick a joke that hasn't been shown recently
function nextJoke(manual = false) {
  let seenIds = loadSeenIds()
  
  // If all jokes have been seen, reset the history pool
  if (seenIds.length >= jokePool.length) {
    seenIds = []
  }

  const unSeenJokes = jokePool.filter((j) => !seenIds.includes(j.id) && j.id !== currentJoke.value.id)
  const candidates = unSeenJokes.length > 0 ? unSeenJokes : jokePool.filter((j) => j.id !== currentJoke.value.id)

  const randomIndex = Math.floor(Math.random() * candidates.length)
  const picked = candidates[randomIndex] || jokePool[0]

  currentJoke.value = picked
  seenIds.push(picked.id)
  saveSeenIds(seenIds)
  try {
    localStorage.setItem(STORAGE_KEY_CURRENT, String(picked.id))
  } catch {
    // ignore
  }

  if (manual) {
    store.showToast('已切换至新段子 🎲', 'info')
  }
}

onMounted(() => {
  const seenIds = loadSeenIds()
  seenCount.value = seenIds.length

  const savedCurrentId = Number(localStorage.getItem(STORAGE_KEY_CURRENT))
  if (savedCurrentId) {
    const found = jokePool.find((j) => j.id === savedCurrentId)
    if (found) {
      currentJoke.value = found
      return
    }
  }
  nextJoke(false)
})

// Listen to execution/task state changes: automatically rotate to a fresh unrepeated joke on each build!
watch(
  () => store.isExecuting,
  (isExecuting, oldVal) => {
    if (isExecuting && !oldVal) {
      // Build just started -> switch to a brand new joke to entertain the user!
      nextJoke(false)
    }
  }
)
</script>
