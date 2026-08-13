<template>
  <div
    class="pixel-pet-container"
    :class="[currentState, sizeClass, `variant-${variant}`, { interactive: isInteractive }]"
    @click="handleClick"
    :title="titleText"
    :style="cssVars"
  >
    <div class="pixel-pet-sprite" :style="spriteStyle">
      <div v-if="variant === 'blob'" class="blob-face" aria-hidden="true">
        <span class="blob-eye blob-eye-left" />
        <span class="blob-eye blob-eye-right" />
        <span class="blob-cheek blob-cheek-left" />
        <span class="blob-cheek blob-cheek-right" />
        <span class="blob-mouth" />
      </div>
    </div>
    <div v-if="sparkle" class="sparkle-particle" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import animIdle from '@/assets/pet/anim_idle.png'
import animWalk from '@/assets/pet/anim_walk.png'
import animWave from '@/assets/pet/anim_wave.png'
import animGestures from '@/assets/pet/anim_gestures.png'

const props = withDefaults(
  defineProps<{
    state?: 'idle' | 'running' | 'complete' | 'error' | 'wave' | 'gestures'
    size?: 'sm' | 'md' | 'lg' | 'mini'
    scale?: number
    interactive?: boolean
    variant?: 'pixel' | 'blob'
    tooltip?: string
  }>(),
  {
    state: 'idle',
    size: 'md',
    interactive: true,
    variant: 'pixel',
    tooltip: '点击与桌宠互动',
  }
)

const tempState = ref<string | null>(null)
const sparkle = ref(false)

const currentState = computed(() => tempState.value || props.state)

const isInteractive = computed(() => props.interactive)
const variant = computed(() => props.variant)

const titleText = computed(() => {
  if (props.tooltip) return props.tooltip
  if (props.state === 'running') return '正在努力打包中...'
  if (props.state === 'complete') return '太棒了，全部打包完成！'
  if (props.state === 'error') return '遇到了一点小问题'
  return '桌宠助手待命'
})

const sizeClass = computed(() => `size-${props.size}`)

const cssVars = computed(() => ({
  '--bg-idle': `url(${animIdle})`,
  '--bg-walk': `url(${animWalk})`,
  '--bg-wave': `url(${animWave})`,
  '--bg-gestures': `url(${animGestures})`,
}))

const spriteStyle = computed(() => {
  if (props.scale) {
    return {
      transform: `scale(${props.scale})`,
    }
  }
  return {}
})

function handleClick() {
  if (!props.interactive) return
  sparkle.value = true
  if (currentState.value === 'idle') {
    tempState.value = 'wave'
    setTimeout(() => {
      tempState.value = null
      sparkle.value = false
    }, 2000)
  } else if (currentState.value === 'running') {
    tempState.value = 'gestures'
    setTimeout(() => {
      tempState.value = null
      sparkle.value = false
    }, 1800)
  } else {
    setTimeout(() => {
      sparkle.value = false
    }, 1500)
  }
}

watch(
  () => props.state,
  (newVal) => {
    if (newVal === 'complete') {
      sparkle.value = true
      setTimeout(() => {
        sparkle.value = false
      }, 3000)
    }
  }
)
</script>

<style scoped>
.pixel-pet-container {
  display: inline-flex;
  align-items: flex-end;
  justify-content: center;
  position: relative;
  user-select: none;
  flex-shrink: 0;
}

.pixel-pet-container.interactive {
  cursor: pointer;
  transition: transform 0.15s ease;
}
.pixel-pet-container.interactive:hover {
  transform: translateY(-2px);
}
.pixel-pet-container.interactive:active {
  transform: translateY(1px);
}

/* Sizes */
.size-mini {
  width: 42px;
  height: 48px;
}
.size-mini .pixel-pet-sprite {
  transform: scale(0.6);
  transform-origin: bottom center;
}

.size-sm {
  width: 52px;
  height: 60px;
}
.size-sm .pixel-pet-sprite {
  transform: scale(0.75);
  transform-origin: bottom center;
}

.size-md {
  width: 72px;
  height: 80px;
}
.size-md .pixel-pet-sprite {
  transform: scale(1);
  transform-origin: bottom center;
}

.size-lg {
  width: 90px;
  height: 100px;
}
.size-lg .pixel-pet-sprite {
  transform: scale(1.25);
  transform-origin: bottom center;
}

/* Base Sprite */
.pixel-pet-sprite {
  width: 72px;
  height: 80px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  background-repeat: no-repeat;
  flex-shrink: 0;
}

/* Idle (7 frames, width 504px) */
.pixel-pet-container.idle .pixel-pet-sprite {
  background-image: var(--bg-idle);
  background-size: 504px 80px;
  animation: petIdleSteps 1.8s steps(7) infinite;
}
@keyframes petIdleSteps {
  0% { background-position: 0 0; }
  100% { background-position: -504px 0; }
}

/* Running / Walk (8 frames, width 576px) */
.pixel-pet-container.running .pixel-pet-sprite,
.pixel-pet-container.walk .pixel-pet-sprite {
  background-image: var(--bg-walk);
  background-size: 576px 80px;
  animation: petWalkSteps 0.75s steps(8) infinite;
}
@keyframes petWalkSteps {
  0% { background-position: 0 0; }
  100% { background-position: -576px 0; }
}

/* Wave (4 frames, width 288px) */
.pixel-pet-container.wave .pixel-pet-sprite {
  background-image: var(--bg-wave);
  background-size: 288px 80px;
  animation: petWaveSteps 0.9s steps(4) infinite;
}
@keyframes petWaveSteps {
  0% { background-position: 0 0; }
  100% { background-position: -288px 0; }
}

/* Complete / Gestures (7 frames, width 504px) */
.pixel-pet-container.complete .pixel-pet-sprite,
.pixel-pet-container.gestures .pixel-pet-sprite {
  background-image: var(--bg-gestures);
  background-size: 504px 80px;
  animation: petGesturesSteps 1.1s steps(7) infinite;
}
@keyframes petGesturesSteps {
  0% { background-position: 0 0; }
  100% { background-position: -504px 0; }
}

/* Error */
.pixel-pet-container.error .pixel-pet-sprite {
  background-image: var(--bg-gestures);
  background-size: 504px 80px;
  background-position: 0 0;
  animation: petErrorVibrate 0.4s ease-in-out infinite alternate;
}

/* Black blob companion, drawn in CSS to remain crisp at every component size. */
.pixel-pet-container.variant-blob { --blob-scale: 1; }
.pixel-pet-container.size-mini.variant-blob { --blob-scale: .62; }
.pixel-pet-container.size-sm.variant-blob { --blob-scale: .75; }
.pixel-pet-container.size-lg.variant-blob { --blob-scale: 1.25; }
.pixel-pet-container.variant-blob .pixel-pet-sprite {
  width: 64px;
  height: 61px;
  margin-bottom: 2px;
  border-radius: 50% 50% 45% 45% / 54% 54% 39% 39%;
  background: radial-gradient(circle at 32% 21%, #41444d 0 2%, transparent 7%), #15171b !important;
  box-shadow: inset -5px -7px 10px rgba(255,255,255,.07), inset 5px 3px 9px rgba(0,0,0,.28), 0 5px 9px rgba(15,23,42,.16);
  image-rendering: auto;
  position: relative;
  overflow: visible;
  animation: blobIdle 2.5s ease-in-out infinite !important;
}
.blob-face {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.blob-eye {
  position: absolute;
  top: 18px;
  width: 14px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transform-origin: center;
  animation: blobBlink 4.6s ease-in-out infinite;
}
.blob-eye::before {
  content: '';
  position: absolute;
  width: 6px;
  height: 9px;
  right: 2px;
  bottom: 2px;
  border-radius: 50%;
  background: #2b2b31;
}
.blob-eye::after {
  content: '';
  position: absolute;
  width: 2px;
  height: 3px;
  right: 4px;
  bottom: 7px;
  border-radius: 50%;
  background: #fff;
}
.blob-eye-left { left: 15px; transform: rotate(5deg); }
.blob-eye-right { right: 15px; transform: rotate(-5deg); animation-delay: .04s; }
.blob-cheek {
  position: absolute;
  top: 39px;
  width: 9px;
  height: 4px;
  border-radius: 50%;
  background: rgba(251,113,133,.58);
  filter: blur(.15px);
  animation: blobCheekPop 2.5s ease-in-out infinite;
}
.blob-cheek-left { left: 12px; transform: rotate(-10deg); }
.blob-cheek-right { right: 12px; transform: rotate(10deg); }
.blob-mouth {
  position: absolute;
  left: 50%;
  top: 40px;
  width: 13px;
  height: 7px;
  border-bottom: 2px solid #fb7185;
  border-radius: 0 0 50% 50%;
  transform: translateX(-50%);
  animation: blobSmile 2.5s ease-in-out infinite;
}
.pixel-pet-container.variant-blob.running .pixel-pet-sprite { animation: blobWorking 1.4s ease-in-out infinite !important; }
.pixel-pet-container.variant-blob.wave .pixel-pet-sprite { animation: blobHello .9s ease-in-out infinite !important; }
.pixel-pet-container.variant-blob.complete .pixel-pet-sprite,
.pixel-pet-container.variant-blob.gestures .pixel-pet-sprite { animation: blobCelebrate 1.1s ease-in-out infinite !important; }
.pixel-pet-container.variant-blob.error .pixel-pet-sprite { animation: blobWobble .45s ease-in-out infinite alternate !important; }
@keyframes blobIdle { 0%,100% { transform: translateY(0) scale(var(--blob-scale)); } 50% { transform: translateY(-2px) scale(calc(var(--blob-scale) * 1.015),calc(var(--blob-scale) * .985)); } }
@keyframes blobBlink { 0%, 88%, 100% { transform: scaleY(1); } 92%, 96% { transform: scaleY(.12); } }
@keyframes blobCheekPop { 0%,100% { opacity: .55; transform: scale(1); } 50% { opacity: .9; transform: scale(1.16); } }
@keyframes blobSmile { 0%,100% { height: 7px; } 50% { height: 9px; } }
@keyframes blobWorking { 0%,100% { transform: translateY(0) scale(var(--blob-scale)); } 30% { transform: translateY(-3px) scale(calc(var(--blob-scale) * 1.025),calc(var(--blob-scale) * .975)); } 60% { transform: translateY(1px) scale(calc(var(--blob-scale) * .99),calc(var(--blob-scale) * 1.01)); } }
@keyframes blobHello { 0%,100% { transform: translateY(0) scale(var(--blob-scale)); } 50% { transform: translateY(-3px) scale(calc(var(--blob-scale) * 1.02),calc(var(--blob-scale) * .98)); } }
@keyframes blobCelebrate { 0%,100% { transform: translateY(0) scale(var(--blob-scale)); } 45% { transform: translateY(-5px) scale(calc(var(--blob-scale) * 1.06),calc(var(--blob-scale) * .94)); } 70% { transform: translateY(0) scale(calc(var(--blob-scale) * .98),calc(var(--blob-scale) * 1.02)); } }
@keyframes blobWobble { from { transform: translateY(0) scale(var(--blob-scale)); } to { transform: translateY(2px) scale(calc(var(--blob-scale) * 1.02),calc(var(--blob-scale) * .98)); } }
@keyframes petErrorVibrate {
  0% { transform: translateY(0); }
  100% { transform: translateY(-3px) rotate(1.5deg); }
}

/* Sparkle */
.sparkle-particle {
  position: absolute;
  top: 0;
  right: 0;
  width: 14px;
  height: 14px;
  pointer-events: none;
}
.sparkle-particle::before {
  content: '✨';
  font-size: 13px;
  animation: sparklePop 0.8s ease-out forwards;
  display: block;
}
@keyframes sparklePop {
  0% { transform: scale(0.5) translateY(0); opacity: 1; }
  100% { transform: scale(1.3) translateY(-14px); opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .pixel-pet-container.variant-blob .pixel-pet-sprite { animation: none !important; }
}
</style>
