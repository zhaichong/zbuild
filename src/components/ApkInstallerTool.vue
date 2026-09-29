<template>
  <div class="app-shell flex-1 min-h-0 flex flex-col overflow-hidden bg-slate-50">
    <!-- Top Header Bar -->
    <div class="bg-white border-b border-slate-200 px-5 py-3 shrink-0 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-600 flex items-center justify-center text-xl shrink-0">
          🤖
        </div>
        <div>
          <h2 class="text-base font-bold text-slate-800 leading-tight">SVN APK 在线设备安装助手</h2>
          <p class="text-xs text-slate-500 mt-0.5">从 SVN 检索应用 APK，支持无线 Wi-Fi / USB ADB 连接真机并在线一键安装与启动</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-400">当前已选设备:</span>
        <span
          v-if="selectedDevice"
          class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200"
        >
          {{ selectedDevice }}
        </span>
        <span
          v-else
          class="text-xs text-slate-400 font-medium px-2 py-0.5 rounded-full bg-slate-100"
        >
          未选择
        </span>
      </div>
    </div>

    <!-- Main Content Area: Left (SVN APK Browser) + Right (ADB Devices & Install Panel) -->
    <div class="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 overflow-hidden">
      <!-- Left Column: SVN APK Browser & Search (7 cols) -->
      <div class="lg:col-span-7 flex flex-col min-h-0 bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <!-- SVN Config & Search Input Header -->
        <div class="p-3.5 border-b border-slate-100 bg-slate-50/70 flex flex-col gap-2.5 shrink-0">
          <!-- SVN Location Selector / URL -->
          <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center">
            <label class="sm:col-span-3 text-xs font-semibold text-slate-600">SVN 仓库源</label>
            <div class="sm:col-span-9 flex gap-2">
              <select
                v-model="selectedSvnUrl"
                class="form-select text-xs py-1.5 px-2.5 rounded-lg border border-slate-200 bg-white flex-1 min-w-0"
              >
                <option :value="cleanSvnUrl(store.config?.svnRootUrl || '')">
                  默认 SVN 根路径 ({{ cleanSvnUrl(store.config?.svnRootUrl) || '未配置' }})
                </option>
                <option
                  v-for="loc in svnLocations"
                  :key="loc.id || loc.url"
                  :value="cleanSvnUrl(loc.url)"
                >
                  {{ loc.name }} ({{ cleanSvnUrl(loc.url) }})
                </option>
              </select>
            </div>
          </div>

          <!-- Search Keyword / Subpath Search -->
          <div class="flex gap-2 items-center">
            <div class="relative flex-1 min-w-0">
              <input
                v-model.trim="searchKeyword"
                type="text"
                class="form-input w-full text-xs py-1.5 pl-8 pr-3 rounded-lg border border-slate-200 bg-white"
                placeholder="搜索 APK 名称或子目录 (例如: bedhead, hospital, 2026)..."
                @keyup.enter="handleSearch"
              >
              <svg class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              class="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shrink-0 cursor-pointer transition-colors shadow-2xs disabled:opacity-50"
              :disabled="searching || !selectedSvnUrl"
              @click="handleSearch"
            >
              {{ searching ? '检索中...' : '搜索 APK' }}
            </button>
            <button
              class="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-medium shrink-0 cursor-pointer transition-colors disabled:opacity-50"
              :disabled="searching || !selectedSvnUrl"
              @click="handleBrowseRoot"
            >
              浏览目录
            </button>
          </div>
        </div>

        <!-- Subdirectory Navigation Bar -->
        <div class="px-3.5 py-2 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between text-xs gap-2 shrink-0">
          <!-- Breadcrumbs -->
          <div class="flex items-center gap-1.5 overflow-hidden text-slate-600 min-w-0">
            <button
              type="button"
              class="font-semibold text-teal-700 hover:text-teal-800 hover:underline cursor-pointer flex items-center gap-1 shrink-0"
              @click="handleBrowse('')"
            >
              <span>🏠</span>
              <span>根目录</span>
            </button>
            <template v-for="(seg, idx) in pathSegments" :key="idx">
              <span class="text-slate-400 shrink-0">/</span>
              <button
                type="button"
                class="hover:underline cursor-pointer truncate max-w-[10rem] shrink-0"
                :class="idx === pathSegments.length - 1 ? 'font-bold text-slate-800' : 'text-slate-600'"
                @click="handleBrowse(pathSegments.slice(0, idx + 1).join('/'))"
              >
                {{ seg }}
              </button>
            </template>
          </div>

          <!-- Right side actions: In-directory filter & Parent Button -->
          <div class="flex items-center gap-2 shrink-0">
            <div v-if="directoryList.length > 3 || apkList.length > 3" class="relative">
              <input
                v-model.trim="localFilterKeyword"
                type="text"
                class="w-36 pl-6 pr-2 py-0.5 text-[11px] rounded-md border border-slate-200 bg-white placeholder-slate-400 focus:outline-none focus:border-teal-500"
                placeholder="快速过滤列表..."
              >
              <svg class="w-3 h-3 text-slate-400 absolute left-1.5 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              v-if="currentSubpath"
              type="button"
              class="px-2 py-0.5 text-[11px] font-medium text-teal-700 bg-teal-50 hover:bg-teal-100 rounded border border-teal-200 cursor-pointer shrink-0 transition-colors flex items-center gap-1"
              @click="handleBrowseParent"
            >
              <span>↑</span>
              <span>返回上级</span>
            </button>
          </div>
        </div>

        <!-- Table / Column List Header -->
        <div class="px-3 py-1.5 border-b border-slate-200 bg-slate-100/70 text-[11px] font-semibold text-slate-500 flex items-center justify-between shrink-0 select-none">
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <span class="w-6 text-center">#</span>
            <span>名称</span>
          </div>
          <div class="flex items-center gap-6 shrink-0 text-right">
            <span class="w-20 text-center">类型 / 大小</span>
            <span class="w-28 text-center">提交版本 / 日期</span>
            <span class="w-12 text-center">操作</span>
          </div>
        </div>

        <!-- Main Column View Area (列展示) -->
        <div class="flex-1 min-h-0 overflow-y-auto">
          <!-- Loading State -->
          <div v-if="searching" class="h-64 flex flex-col items-center justify-center text-slate-400 gap-2">
            <svg class="w-6 h-6 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span class="text-xs">正在从 SVN 检索目录与文件...</span>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="filteredDirectories.length === 0 && filteredApks.length === 0"
            class="h-64 flex flex-col items-center justify-center text-slate-400 gap-1.5"
          >
            <span class="text-3xl">📂</span>
            <span class="text-xs font-medium text-slate-600">当前目录为空或无匹配项</span>
            <span class="text-[11px] text-slate-400">
              {{ localFilterKeyword ? '未检索到包含过滤词的内容' : '可点击上方“返回上级”或使用“搜索 APK”全库检索' }}
            </span>
          </div>

          <!-- Rows List (列展示) -->
          <div v-else class="divide-y divide-slate-100 text-xs">
            <!-- Row: Go to parent directory if in subpath -->
            <div
              v-if="currentSubpath"
              class="flex items-center justify-between px-3 py-2 hover:bg-slate-50 cursor-pointer transition-colors text-slate-600 border-b border-slate-100 group"
              @click="handleBrowseParent"
            >
              <div class="flex items-center gap-2.5 flex-1 min-w-0">
                <span class="w-6 text-center text-slate-400">..</span>
                <span class="text-base text-amber-500">📁</span>
                <span class="font-bold text-teal-700 group-hover:underline">.. (返回上一级目录)</span>
              </div>
              <div class="text-[11px] text-slate-400 shrink-0">返回上层</div>
            </div>

            <!-- Directory Rows (列展示) -->
            <div
              v-for="dir in filteredDirectories"
              :key="dir.path"
              class="flex items-center justify-between px-3 py-2 hover:bg-teal-50/40 cursor-pointer transition-colors group"
              @click="handleBrowse(dir.path)"
            >
              <div class="flex items-center gap-2.5 flex-1 min-w-0 pr-2">
                <span class="w-6 text-center text-slate-300 group-hover:text-teal-600">📁</span>
                <div class="min-w-0 flex-1">
                  <p class="font-semibold text-slate-800 group-hover:text-teal-700 truncate text-xs" :title="dir.name">
                    {{ dir.name }}
                  </p>
                  <p v-if="dir.author" class="text-[10px] text-slate-400 truncate">
                    提交人: {{ dir.author }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-6 shrink-0 text-right">
                <span class="w-20 text-center">
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200/60">
                    子目录
                  </span>
                </span>
                <span class="w-28 text-center text-[11px] text-slate-400 font-mono">
                  <span v-if="dir.revision" class="mr-1">r{{ dir.revision }}</span>
                  <span>{{ formatDate(dir.date) || '-' }}</span>
                </span>
                <span class="w-12 text-center text-teal-600 font-bold group-hover:translate-x-1 transition-transform inline-block">
                  ➔
                </span>
              </div>
            </div>

            <!-- APK File Rows (列展示) -->
            <div
              v-for="apk in filteredApks"
              :key="apk.path"
              class="flex items-center justify-between px-3 py-2.5 hover:bg-teal-50/60 cursor-pointer transition-colors"
              :class="{ '!bg-teal-50/90 !border-l-4 !border-l-teal-600 shadow-2xs': selectedApk?.path === apk.path }"
              @click="selectedApk = apk"
            >
              <div class="flex items-center gap-2.5 flex-1 min-w-0 pr-2">
                <span class="w-6 text-center flex items-center justify-center">
                  <input
                    type="radio"
                    name="selectedApk"
                    :checked="selectedApk?.path === apk.path"
                    class="accent-teal-600 w-3.5 h-3.5 cursor-pointer"
                  >
                </span>
                <span class="text-base text-emerald-600">📦</span>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <p class="font-bold text-slate-800 truncate text-xs" :title="apk.name">
                      {{ apk.name }}
                    </p>
                    <span v-if="selectedApk?.path === apk.path" class="text-[9px] px-1 py-0.2 rounded bg-teal-600 text-white font-bold">
                      已选
                    </span>
                  </div>
                  <p class="text-[10px] text-slate-400 truncate mt-0.5" :title="apk.path">
                    {{ apk.path }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-6 shrink-0 text-right">
                <span class="w-20 text-center">
                  <span
                    v-if="apk.sizeDisplay"
                    class="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"
                  >
                    {{ apk.sizeDisplay }}
                  </span>
                  <span v-else class="text-[11px] text-slate-300">-</span>
                </span>
                <span class="w-28 text-center text-[11px] text-slate-400 font-mono">
                  <span v-if="apk.revision" class="mr-1">r{{ apk.revision }}</span>
                  <span>{{ formatDate(apk.date) || '-' }}</span>
                </span>
                <span class="w-12 text-center">
                  <button
                    type="button"
                    class="px-2 py-0.5 rounded text-[10px] font-medium transition-colors"
                    :class="selectedApk?.path === apk.path ? 'bg-teal-600 text-white' : 'bg-slate-100 hover:bg-teal-100 text-slate-600 hover:text-teal-700'"
                  >
                    {{ selectedApk?.path === apk.path ? '选中' : '选择' }}
                  </button>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Left Column Footer Status -->
        <div class="px-3.5 py-2 border-t border-slate-100 bg-slate-50/60 text-xs text-slate-500 flex items-center justify-between shrink-0">
          <span>共找到 <b class="text-slate-700">{{ filteredDirectories.length }}</b> 个子目录，<b class="text-slate-700">{{ filteredApks.length }}</b> 个 APK 文件</span>
          <span v-if="selectedApk" class="text-teal-700 font-medium truncate max-w-[50%]">已选中: {{ selectedApk.name }}</span>
        </div>
      </div>

      <!-- Right Column: ADB Devices + Install Controls + Logs (5 cols) -->
      <div class="lg:col-span-5 flex flex-col min-h-0 gap-4 overflow-hidden">
        <!-- ADB Devices Card -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden flex flex-col shrink-0">
          <div class="p-3 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-800">ADB 设备列表</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200 text-slate-700 font-mono">{{ devices.length }}</span>
            </div>
            <button
              class="text-xs font-medium text-teal-600 hover:text-teal-800 cursor-pointer flex items-center gap-1"
              :disabled="loadingDevices"
              @click="refreshDevices"
            >
              <svg class="w-3 h-3" :class="{ 'animate-spin': loadingDevices }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新设备
            </button>
          </div>

          <!-- Wireless ADB Connect Bar -->
          <div class="p-3 border-b border-slate-100 flex flex-col gap-2">
            <div class="flex gap-2">
              <input
                v-model.trim="connectTarget"
                type="text"
                class="form-input flex-1 text-xs py-1.5 px-2.5 rounded-lg border border-slate-200"
                placeholder="无线调试 IP[:端口]，如 192.168.77.42:5555"
                @keyup.enter="handleConnectAdb()"
              >
              <button
                class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-medium shrink-0 cursor-pointer transition-colors disabled:opacity-50 flex items-center gap-1"
                :disabled="connectingAdb || !connectTarget"
                @click="handleConnectAdb()"
              >
                <svg v-if="connectingAdb" class="w-3 h-3 animate-spin text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>{{ connectingAdb ? '连接中...' : '连接' }}</span>
              </button>
            </div>

            <!-- Recent Devices Quick Connect Chips -->
            <div v-if="adbHistory.length > 0" class="flex items-center gap-1.5 flex-wrap text-[11px]">
              <span class="text-slate-400 shrink-0">历史设备:</span>
              <div
                v-for="target in adbHistory"
                :key="target"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 hover:bg-teal-50 hover:text-teal-700 text-slate-600 border border-slate-200 hover:border-teal-300 cursor-pointer transition-colors"
                @click="handleConnectAdb(target)"
              >
                <span>⚡</span>
                <span class="font-mono">{{ target }}</span>
                <button
                  type="button"
                  class="ml-0.5 text-slate-400 hover:text-rose-500 cursor-pointer"
                  title="移除此记录"
                  @click.stop="removeAdbHistory(target)"
                >
                  &times;
                </button>
              </div>
            </div>
          </div>

          <!-- Devices List -->
          <div class="max-h-40 overflow-auto p-2 divide-y divide-slate-100">
            <div v-if="loadingDevices" class="py-4 text-center text-xs text-slate-400 flex items-center justify-center gap-1.5">
              <svg class="w-3.5 h-3.5 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>正在检测 ADB 设备...</span>
            </div>
            <div v-else-if="devices.length === 0" class="py-4 text-center text-xs text-slate-400">
              暂无已连接设备（支持 USB 数据线直连 或 上方输入 IP 无线连接）
            </div>
            <div
              v-for="d in devices"
              :key="d.serial"
              class="p-2 rounded-lg hover:bg-slate-50 cursor-pointer flex items-center justify-between gap-2"
              :class="{ '!bg-teal-50 border border-teal-200': selectedDevice === d.serial }"
              @click="selectedDevice = d.serial"
            >
              <div class="flex items-center gap-2 min-w-0">
                <input
                  type="radio"
                  name="selectedDevice"
                  :checked="selectedDevice === d.serial"
                  class="accent-teal-600 w-3.5 h-3.5 cursor-pointer"
                >
                <div class="min-w-0">
                  <div class="flex items-center gap-1.5">
                    <span class="text-xs font-semibold text-slate-800 truncate">{{ d.serial }}</span>
                    <span
                      class="text-[10px] px-1 py-0.2 rounded font-medium"
                      :class="d.status === 'device' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'"
                    >
                      {{ d.status === 'device' ? '在线' : d.status }}
                    </span>
                    <span class="text-[9px] px-1 py-0.2 rounded bg-slate-100 text-slate-500 font-mono">
                      {{ d.serial.includes(':') ? '无线网络' : 'USB直连' }}
                    </span>
                  </div>
                  <p v-if="d.model || d.product" class="text-[10px] text-slate-400 truncate">
                    {{ [d.model, d.product].filter(Boolean).join(' · ') }}
                  </p>
                </div>
              </div>

              <button
                v-if="d.serial.includes(':')"
                class="text-[11px] text-slate-400 hover:text-rose-600 px-1.5 py-0.5 rounded cursor-pointer"
                title="断开无线连接"
                @click.stop="handleDisconnectAdb(d.serial)"
              >
                断开
              </button>
            </div>
          </div>
        </div>

        <!-- Installation Action & Options Card -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-2xs p-3.5 shrink-0 flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-800">安装设置与执行</span>
            <span
              v-if="deskPetEnabled"
              class="text-[10px] text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200/60 flex items-center gap-1 font-medium select-none"
            >
              <span>🐾</span>
              <span>桌宠监工</span>
            </span>
          </div>

          <div class="space-y-1.5">
            <label class="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input v-model="optReinstall" type="checkbox" class="accent-teal-600 rounded">
              <span>覆盖安装已有应用 (-r)</span>
            </label>
            <label class="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input v-model="optAutoReinstallOnIncompatible" type="checkbox" class="accent-teal-600 rounded">
              <span>签名或版本冲突时自动卸载重装</span>
            </label>
            <label class="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input v-model="optLaunchAfterInstall" type="checkbox" class="accent-teal-600 rounded">
              <span>安装完成后自动启动应用</span>
            </label>
          </div>

          <!-- Desk Pet Companion Banner -->
          <div
            v-if="deskPetEnabled"
            class="p-2.5 rounded-lg border transition-all flex items-center gap-3 select-none"
            :class="petBannerBgClass"
          >
            <div class="shrink-0 flex items-center justify-center">
              <PixelPet
                :state="petState"
                :variant="deskPetStyle"
                size="sm"
                tooltip="点击与桌宠互动"
              />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-bold" :class="petTitleClass">{{ petBannerTitle }}</span>
                <span
                  v-if="installing"
                  class="inline-block w-1.5 h-1.5 rounded-full bg-teal-500 animate-ping"
                />
              </div>
              <p class="text-[11px] truncate mt-0.5" :class="petMessageClass" :title="petBannerMessage">
                {{ petBannerMessage }}
              </p>
            </div>
          </div>

          <button
            class="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-sm transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            :disabled="installing || !selectedApk || !selectedDevice"
            @click="handleInstall"
          >
            <svg v-if="installing" class="w-4 h-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>{{ installing ? '桌宠正在安装 APK，请稍候...' : '一键安装选中的 APK' }}</span>
          </button>
        </div>

        <!-- Install Logs Panel -->
        <div class="flex-1 min-h-0 bg-[#0d1522] rounded-xl border border-slate-800 shadow-sm flex flex-col overflow-hidden">
          <div class="px-3 py-2 border-b border-slate-700/80 bg-[#090f19] flex items-center justify-between shrink-0">
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono font-bold text-sky-400">INSTALL LOGS</span>
              <span v-if="installing" class="text-[10px] text-teal-400 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-teal-400 animate-ping"></span>
                <span>执行中...</span>
              </span>
            </div>
            <button
              class="text-[11px] text-slate-400 hover:text-slate-200 cursor-pointer"
              @click="installLogs = []"
            >
              清空日志
            </button>
          </div>

          <div ref="logContainerRef" class="flex-1 min-h-0 overflow-auto p-3 font-mono text-[11px] leading-5 space-y-1">
            <div v-for="(log, idx) in installLogs" :key="idx" class="text-slate-300">
              <span class="text-slate-500 mr-1.5">&gt;</span>
              <span :class="getLogClass(log)">{{ log }}</span>
            </div>
            <div v-if="installLogs.length === 0" class="h-full min-h-[100px] flex flex-col items-center justify-center text-slate-500 gap-1.5 py-4">
              <PixelPet v-if="deskPetEnabled" state="idle" :variant="deskPetStyle" size="mini" tooltip="点击与桌宠打招呼！" />
              <span class="text-xs text-slate-400">等待开始安装任务...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import PixelPet from '@/components/PixelPet.vue'

interface SvnApkItem {
  name: string
  path: string
  fullUrl?: string
  size?: number | null
  sizeDisplay?: string
  revision?: string
  date?: string
  author?: string
}

interface SvnDirItem {
  name: string
  path: string
}

interface AdbDeviceItem {
  serial: string
  status: string
  model?: string
  product?: string
  device?: string
  isOnline?: boolean
}

function cleanSvnUrl(url?: string): string {
  if (!url) return ''
  let raw = url.trim()
  if (raw.includes('#')) {
    try {
      const u = new URL(raw)
      const frag = decodeURIComponent(u.hash.replace(/^#/, '')).trim().replace(/^\/+/, '')
      const parts = frag.split('/').filter(Boolean)
      if (parts.length > 0) {
        const repo = parts[0]
        let subparts = parts.slice(1)
        if (subparts.length >= 2 && subparts[0] === 'view') {
          subparts = subparts.slice(2)
        }
        return `${u.origin}/svn/${repo}${subparts.length ? '/' + subparts.join('/') : ''}`
      }
    } catch {
      // fallback
    }
  }
  return raw.replace(/\/!\/?$/, '')
}

const store = useAppStore()

// SVN State
const svnLocations = computed(() => store.config?.svnLocations || [])
const selectedSvnUrl = ref(cleanSvnUrl(store.config?.svnRootUrl || ''))
const searchKeyword = ref('')
const searching = ref(false)
const currentSubpath = ref('')
const localFilterKeyword = ref('')
const directoryList = ref<SvnDirItem[]>([])
const apkList = ref<SvnApkItem[]>([])
const selectedApk = ref<SvnApkItem | null>(null)

const pathSegments = computed(() => {
  if (!currentSubpath.value) return []
  return currentSubpath.value.replace(/\\/g, '/').split('/').filter(Boolean)
})

const filteredDirectories = computed(() => {
  if (!localFilterKeyword.value) return directoryList.value
  const kw = localFilterKeyword.value.toLowerCase()
  return directoryList.value.filter((d) => d.name.toLowerCase().includes(kw))
})

const filteredApks = computed(() => {
  if (!localFilterKeyword.value) return apkList.value
  const kw = localFilterKeyword.value.toLowerCase()
  return apkList.value.filter((a) => a.name.toLowerCase().includes(kw) || a.path.toLowerCase().includes(kw))
})

// ADB State
const devices = ref<AdbDeviceItem[]>([])
const loadingDevices = ref(false)
const selectedDevice = ref('')
const connectTarget = ref('')
const connectingAdb = ref(false)
const ADB_HISTORY_KEY = 'zbuild_adb_history_devices'
const adbHistory = ref<string[]>([])

function loadAdbHistory() {
  try {
    const raw = localStorage.getItem(ADB_HISTORY_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length > 0) {
        adbHistory.value = parsed
        return
      }
    }
  } catch {
    // ignore
  }
  // Default fallback if no history stored yet
  adbHistory.value = ['192.168.77.42:5555']
}

function saveAdbHistory(target: string) {
  if (!target) return
  const clean = target.includes(':') ? target : `${target}:5555`
  const set = new Set([clean, ...adbHistory.value])
  adbHistory.value = Array.from(set).slice(0, 5)
  try {
    localStorage.setItem(ADB_HISTORY_KEY, JSON.stringify(adbHistory.value))
  } catch {
    // ignore
  }
}

function removeAdbHistory(target: string) {
  adbHistory.value = adbHistory.value.filter((t) => t !== target)
  try {
    localStorage.setItem(ADB_HISTORY_KEY, JSON.stringify(adbHistory.value))
  } catch {
    // ignore
  }
}

// Install Options & Pet State
const optReinstall = ref(true)
const optAutoReinstallOnIncompatible = ref(true)
const optLaunchAfterInstall = ref(true)
const installing = ref(false)
const lastInstallStatus = ref<'idle' | 'success' | 'error'>('idle')
const lastInstallMessage = ref('')
const installLogs = ref<string[]>([])
const logContainerRef = ref<HTMLDivElement | null>(null)

const deskPetEnabled = computed(() => store.config?.enableDeskPet !== false)
const deskPetStyle = computed<'pixel' | 'blob'>(() =>
  store.config?.deskPetStyle === 'blob' ? 'blob' : 'pixel'
)

const petState = computed<'idle' | 'running' | 'complete' | 'error'>(() => {
  if (installing.value) return 'running'
  if (lastInstallStatus.value === 'success') return 'complete'
  if (lastInstallStatus.value === 'error') return 'error'
  return 'idle'
})

const petBannerBgClass = computed(() => {
  if (installing.value) return 'bg-teal-50/90 border-teal-300 ring-2 ring-teal-500/10 shadow-2xs'
  if (lastInstallStatus.value === 'success') return 'bg-emerald-50/90 border-emerald-300 shadow-2xs'
  if (lastInstallStatus.value === 'error') return 'bg-rose-50/90 border-rose-300 shadow-2xs'
  return 'bg-slate-50/80 border-slate-200/80'
})

const petTitleClass = computed(() => {
  if (installing.value) return 'text-teal-900'
  if (lastInstallStatus.value === 'success') return 'text-emerald-900'
  if (lastInstallStatus.value === 'error') return 'text-rose-900'
  return 'text-slate-800'
})

const petMessageClass = computed(() => {
  if (installing.value) return 'text-teal-700 font-medium'
  if (lastInstallStatus.value === 'success') return 'text-emerald-700 font-medium'
  if (lastInstallStatus.value === 'error') return 'text-rose-700'
  return 'text-slate-500'
})

const petBannerTitle = computed(() => {
  if (installing.value) return '桌宠正在监工安装应用...'
  if (lastInstallStatus.value === 'success') return '太棒了，APK 安装成功！🎉'
  if (lastInstallStatus.value === 'error') return '安装遇到异常'
  return '桌宠助手待命中 🐾'
})

const petBannerMessage = computed(() => {
  if (installing.value) {
    if (lastInstallMessage.value) return lastInstallMessage.value
    return `正在将 ${selectedApk.value?.name || 'APK'} 推送到设备 [${selectedDevice.value}]...`
  }
  if (lastInstallStatus.value === 'success') {
    return `${selectedApk.value?.name || '应用'} 已顺利安装并部署至设备 [${selectedDevice.value}]`
  }
  if (lastInstallStatus.value === 'error') {
    return lastInstallMessage.value || '请查看下方控制台日志排查原因'
  }
  if (!selectedApk.value && !selectedDevice.value) {
    return '请先在左侧选择 APK，并在上方选择目标设备'
  }
  if (!selectedApk.value) {
    return '已选目标设备，请在左侧列表选择要安装的 APK'
  }
  if (!selectedDevice.value) {
    return '已选 APK，请在上方设备列表中选择目标设备'
  }
  return '准备就绪！点击下方按钮唤醒桌宠开始推送安装'
})

function appendLog(msg: string) {
  installLogs.value.push(msg)
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}

function getLogClass(log: string): string {
  if (log.includes('成功') || log.includes('Success')) return 'text-emerald-400 font-semibold'
  if (log.includes('失败') || log.includes('Error') || log.includes('Exception')) return 'text-rose-400 font-semibold'
  if (log.includes('警告') || log.includes('Warn')) return 'text-amber-300'
  return 'text-slate-200'
}

function formatDate(isoStr?: string): string {
  if (!isoStr) return ''
  try {
    return new Date(isoStr).toLocaleDateString('zh-CN')
  } catch {
    return isoStr.slice(0, 10)
  }
}

// ---------------------------------------------------------------------------
// SVN Actions
// ---------------------------------------------------------------------------

async function handleSearch() {
  const url = cleanSvnUrl(selectedSvnUrl.value)
  if (!url) {
    store.showToast('请先选择 SVN 仓库源', 'warning')
    return
  }
  searching.value = true
  apkList.value = []
  directoryList.value = []
  currentSubpath.value = ''
  localFilterKeyword.value = ''
  selectedApk.value = null
  try {
    const res = await ipc.searchSvnApk({
      url,
      keyword: searchKeyword.value,
      username: store.config?.form.svnUsername,
      password: store.config?.form.svnPassword,
    })
    if (res.success) {
      apkList.value = res.apks || []
      if (apkList.value.length === 0) {
        store.showToast('未检索到匹配的 APK 文件', 'info')
      }
    } else {
      store.showToast(`检索失败: ${res.error || '未知错误'}`, 'error')
    }
  } catch (err: unknown) {
    store.showToast(`检索异常: ${err instanceof Error ? err.message : String(err)}`, 'error')
  } finally {
    searching.value = false
  }
}

async function handleBrowse(subpath: string = '') {
  const url = cleanSvnUrl(selectedSvnUrl.value)
  if (!url) {
    store.showToast('请先选择 SVN 仓库源', 'warning')
    return
  }
  searching.value = true
  apkList.value = []
  directoryList.value = []
  selectedApk.value = null
  currentSubpath.value = subpath
  localFilterKeyword.value = ''
  try {
    const res = await ipc.browseSvn({
      url,
      subpath,
      username: store.config?.form.svnUsername,
      password: store.config?.form.svnPassword,
    })
    if (res.success) {
      apkList.value = res.apks || []
      directoryList.value = res.directories || []
      if (apkList.value.length === 0 && directoryList.value.length === 0) {
        store.showToast('该目录下未找到 APK 或子目录', 'info')
      }
    } else {
      store.showToast(`浏览失败: ${res.error || '未知错误'}`, 'error')
    }
  } catch (err: unknown) {
    store.showToast(`浏览异常: ${err instanceof Error ? err.message : String(err)}`, 'error')
  } finally {
    searching.value = false
  }
}

function handleBrowseRoot() {
  handleBrowse('')
}

function handleBrowseParent() {
  if (!currentSubpath.value) return
  const parts = currentSubpath.value.replace(/\\/g, '/').split('/').filter(Boolean)
  parts.pop()
  handleBrowse(parts.join('/'))
}

// ---------------------------------------------------------------------------
// ADB Actions
// ---------------------------------------------------------------------------

async function refreshDevices() {
  loadingDevices.value = true
  try {
    const res = await ipc.getAdbDevices()
    if (res.success) {
      devices.value = res.devices || []
      if (devices.value.length > 0 && !selectedDevice.value) {
        const firstOnline = devices.value.find((d) => d.status === 'device')
        if (firstOnline) {
          selectedDevice.value = firstOnline.serial
        }
      }
    }
  } catch (err: unknown) {
    store.showToast(`读取设备失败: ${err instanceof Error ? err.message : String(err)}`, 'error')
  } finally {
    loadingDevices.value = false
  }
}

async function handleConnectAdb(targetToConnect?: string, silent = false) {
  const target = (targetToConnect || connectTarget.value || '').trim()
  if (!target) return
  connectingAdb.value = true
  try {
    const res = await ipc.connectAdb(target)
    if (res.success) {
      if (!silent) {
        store.showToast(`成功连接到设备 ${res.target}`, 'success')
      }
      saveAdbHistory(res.target)
      connectTarget.value = ''
      await refreshDevices()
      selectedDevice.value = res.target
    } else {
      if (!silent) {
        store.showToast(`连接失败: ${res.output || '未知原因'}`, 'error')
      }
    }
  } catch (err: unknown) {
    if (!silent) {
      store.showToast(`连接异常: ${err instanceof Error ? err.message : String(err)}`, 'error')
    }
  } finally {
    connectingAdb.value = false
  }
}

async function handleDisconnectAdb(serial: string) {
  try {
    const res = await ipc.disconnectAdb(serial)
    if (res.success) {
      store.showToast(`已断开连接: ${serial}`, 'info')
      if (selectedDevice.value === serial) {
        selectedDevice.value = ''
      }
      await refreshDevices()
    }
  } catch (err: unknown) {
    store.showToast(`断开连接失败: ${err instanceof Error ? err.message : String(err)}`, 'error')
  }
}

// ---------------------------------------------------------------------------
// Install Action
// ---------------------------------------------------------------------------

async function handleInstall() {
  if (!selectedApk.value) {
    store.showToast('请先选择要安装的 APK', 'warning')
    return
  }
  if (!selectedDevice.value) {
    store.showToast('请先选择目标设备', 'warning')
    return
  }

  installing.value = true
  lastInstallStatus.value = 'idle'
  lastInstallMessage.value = `开始将 ${selectedApk.value.name} 推送至设备...`
  appendLog(`=== 开始安装任务: ${selectedApk.value.name} -> 设备 [${selectedDevice.value}] ===`)

  try {
    const res = await ipc.installAdbApk({
      url: cleanSvnUrl(selectedSvnUrl.value),
      apkPath: selectedApk.value.path,
      serial: selectedDevice.value,
      reinstall: optReinstall.value,
      autoReinstallOnIncompatible: optAutoReinstallOnIncompatible.value,
      launchAfterInstall: optLaunchAfterInstall.value,
      username: store.config?.form.svnUsername,
      password: store.config?.form.svnPassword,
    })

    if (res.logs && Array.isArray(res.logs)) {
      res.logs.forEach((line: string) => {
        appendLog(line)
        if (line.includes('正在') || line.includes('推送') || line.includes('导出') || line.includes('启动')) {
          lastInstallMessage.value = line.replace(/^[>\s*=]+/, '').trim()
        }
      })
    }

    if (res.success) {
      lastInstallStatus.value = 'success'
      lastInstallMessage.value = 'APK 安装成功！'
      store.showToast(`APK 安装成功！`, 'success')
      appendLog(`=== 任务圆满完成 ===`)
    } else {
      lastInstallStatus.value = 'error'
      lastInstallMessage.value = res.error || '安装失败'
      store.showToast(`安装失败: ${res.error || '详见控制台日志'}`, 'error')
      appendLog(`=== 任务失败: ${res.error || ''} ===`)
    }
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err)
    lastInstallStatus.value = 'error'
    lastInstallMessage.value = errMsg
    appendLog(`任务异常中断: ${errMsg}`)
    store.showToast(`安装异常: ${errMsg}`, 'error')
  } finally {
    installing.value = false
  }
}

onMounted(async () => {
  loadAdbHistory()
  if (!selectedSvnUrl.value && store.config?.svnRootUrl) {
    selectedSvnUrl.value = cleanSvnUrl(store.config.svnRootUrl)
  } else if (selectedSvnUrl.value) {
    selectedSvnUrl.value = cleanSvnUrl(selectedSvnUrl.value)
  }
  await refreshDevices()
})
</script>

<style scoped>
.shadow-2xs {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}
</style>
