<template>
  <div class="flex-1 min-h-0 overflow-y-auto bg-[#f8fafc] p-5 sm:p-7 text-slate-800 font-sans">
    <div class="max-w-6xl mx-auto space-y-6">
      
      <!-- Spotlight Recommendation Banner: ztools Debugging Suite (常驻推荐，不可关闭) -->
      <div
        class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-rose-500/10 border border-amber-200/90 p-4 sm:p-5 shadow-[0_4px_16px_-4px_rgba(245,158,11,0.15)] transition-all duration-300"
      >
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <!-- Banner Left: Icon & Description -->
          <div class="flex items-start gap-3.5 min-w-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 text-white flex items-center justify-center text-xl shadow-md shadow-orange-500/25 shrink-0">
              🛠️
            </div>
            <div class="space-y-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                  <span>推荐神器：ztools 超级调试工具箱</span>
                  <span class="px-2 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-bold shadow-xs">很强 · 必备</span>
                </h3>
                <span class="text-[11px] font-mono text-amber-700 bg-amber-100/80 px-2 py-0.5 rounded-md font-semibold border border-amber-200/60">
                  v1.0.3
                </span>
                <span class="text-[11px] text-slate-400 font-mono">
                  (D:\build\ztools)
                </span>
              </div>
              <p class="text-xs text-slate-600 leading-relaxed">
                包含强大的多功能终端嗅探、串口通讯、TCP抓包、接口联调、日志分析等超强全能调试套件，是智慧病房现场与本地联调的核心利器！
              </p>
            </div>
          </div>

          <!-- Banner Right: Download & Action Buttons -->
          <div class="flex items-center gap-2.5 shrink-0 self-end md:self-center">
            <button
              type="button"
              class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold text-xs shadow-sm hover:shadow-md hover:shadow-orange-500/25 transition-all duration-200 cursor-pointer active:scale-98"
              title="点击下载 ztools.Setup.1.0.3.exe 安装包"
              @click="downloadZtoolsInstaller"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>立即下载安装包</span>
            </button>

            <button
              v-if="ipc.isElectron()"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-amber-300/80 text-amber-900 hover:bg-amber-50 font-semibold text-xs shadow-2xs transition-colors cursor-pointer"
              title="在系统文件管理器中打开 D:\build\ztools"
              @click="openZtoolsFolder"
            >
              <svg class="w-3.5 h-3.5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              <span>打开目录</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Filter Controls & Search Toolbar -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <!-- Category Segmented Buttons -->
        <div class="flex items-center gap-1 bg-slate-200/60 p-1 rounded-xl border border-slate-200/50">
          <button
            v-for="cat in categories"
            :key="cat.value"
            type="button"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer select-none"
            :class="selectedCategory === cat.value
              ? 'bg-white text-blue-600 font-semibold shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'"
            @click="selectedCategory = cat.value"
          >
            <span>{{ cat.label }}</span>
            <span
              class="px-1.5 py-0.2 rounded-full text-[10px]"
              :class="selectedCategory === cat.value ? 'bg-blue-50 text-blue-600 font-semibold' : 'bg-slate-300/50 text-slate-500'"
            >
              {{ getCategoryCount(cat.value) }}
            </span>
          </button>
        </div>

        <!-- Right: Search Input + Add App Button -->
        <div class="flex items-center gap-2.5">
          <div class="relative w-full sm:w-64">
            <div class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none flex items-center">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              id="portal-app-search"
              v-model="searchQuery"
              type="text"
              name="portal-app-search"
              placeholder="搜索套件、功能或标签..."
              class="w-full pl-8 pr-7 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all shadow-2xs"
            >
            <button
              v-if="searchQuery"
              type="button"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs w-4 h-4 flex items-center justify-center rounded-full hover:bg-slate-100 cursor-pointer"
              @click="searchQuery = ''"
            >
              ✕
            </button>
          </div>

          <button
            type="button"
            class="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-xs hover:shadow-md hover:shadow-blue-500/20 transition-all duration-200 cursor-pointer shrink-0 active:scale-98"
            @click="openAddAppModal"
          >
            <svg class="w-3.5 h-3.5 text-white transition-transform group-hover:rotate-90 duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
            </svg>
            <span>添加扩展</span>
          </button>
        </div>
      </div>

      <!-- Delicate Poster Cards Grid (细腻质感高卡片) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        
        <!-- Individual App Card -->
        <div
          v-for="app in filteredApps"
          :key="app.id"
          class="relative rounded-2xl bg-white border border-slate-200/80 shadow-[0_2px_12px_-4px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_24px_-6px_rgba(37,99,235,0.12)] hover:border-blue-300/80 transition-all duration-300 flex flex-col justify-between group overflow-hidden cursor-pointer"
          @click="onLaunchApp(app)"
        >
          <!-- Top Visual / Art Banner Showcase -->
          <div class="relative h-36 w-full overflow-hidden flex items-center justify-center p-4 border-b border-slate-100" :class="getCardBannerBg(app)">
            
            <!-- Category & Status Badges Floating on Banner -->
            <div class="absolute top-2.5 left-3 right-3 flex items-center justify-between z-10">
              <span class="text-[11px] font-semibold text-slate-600/90 bg-white/80 backdrop-blur-md px-2 py-0.5 rounded-md border border-white/60 shadow-2xs">
                {{ app.category }}
              </span>

              <div class="flex items-center gap-1">
                <span
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border backdrop-blur-md shadow-2xs"
                  :class="getStatusBadgeClass(app)"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="getStatusDotClass(app)" />
                  {{ app.statusLabel || (app.status === 'active' ? '内置' : '扩展') }}
                </span>

                <!-- Custom Edit/Delete on Hover -->
                <div v-if="app.id.startsWith('custom-')" class="flex items-center gap-0.5 ml-0.5">
                  <button
                    type="button"
                    title="编辑"
                    class="w-5 h-5 rounded-md flex items-center justify-center bg-white/90 text-slate-500 hover:text-blue-600 hover:bg-white shadow-2xs transition-colors cursor-pointer text-xs"
                    @click.stop="openEditAppModal(app)"
                  >
                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>

                  <button
                    type="button"
                    title="删除"
                    class="w-5 h-5 rounded-md flex items-center justify-center bg-white/90 text-slate-500 hover:text-red-600 hover:bg-white shadow-2xs transition-colors cursor-pointer text-xs"
                    @click.stop="deleteApp(app.id)"
                  >
                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Detailed Delicate Vector Artwork Scene -->
            <div class="relative z-0 mt-3 transition-transform duration-300 group-hover:scale-105">
              
              <!-- 1. ZBuild Visual Artwork: Isometric Build Architecture -->
              <div v-if="app.id === 'zbuild'" class="relative flex items-center justify-center">
                <!-- Soft Glow Backdrop -->
                <div class="w-20 h-20 rounded-full bg-blue-400/20 blur-xl absolute" />
                
                <!-- Main Layered Cube Graphic -->
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/25 border border-white/30">
                  <svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
                <!-- Mini Satellite Badges -->
                <span class="absolute -top-1 -right-2 px-1.5 py-0.2 rounded-full bg-blue-100 text-blue-700 text-[9px] font-bold border border-blue-200 shadow-xs">
                  SVN
                </span>
                <span class="absolute -bottom-1 -left-2 px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-700 text-[9px] font-bold border border-indigo-200 shadow-xs">
                  BUILD
                </span>
              </div>

              <!-- 2. Order Deploy Visual Artwork: Rocket Launch Pipeline -->
              <div v-else-if="app.id === 'order-deploy'" class="relative flex items-center justify-center">
                <!-- Soft Glow Backdrop -->
                <div class="w-20 h-20 rounded-full bg-emerald-400/20 blur-xl absolute" />
                
                <!-- Main Rocket Graphic -->
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/25 border border-white/30">
                  <svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.63 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m0 0a6 6 0 015.84-7.38m-5.84 7.38v4.8" />
                  </svg>
                </div>
                <!-- Mini Satellite Badges -->
                <span class="absolute -top-1 -right-2 px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-700 text-[9px] font-bold border border-emerald-200 shadow-xs">
                  SSH
                </span>
                <span class="absolute -bottom-1 -left-2 px-1.5 py-0.2 rounded-full bg-teal-100 text-teal-700 text-[9px] font-bold border border-teal-200 shadow-xs">
                  DEPLOY
                </span>
              </div>

              <!-- 3. Mock Query Visual Artwork: Lightning Data Stream -->
              <div v-else-if="app.id === 'mock-query'" class="relative flex items-center justify-center">
                <!-- Soft Glow Backdrop -->
                <div class="w-20 h-20 rounded-full bg-amber-400/20 blur-xl absolute" />
                
                <!-- Main Energy Graphic -->
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-white shadow-lg shadow-amber-500/25 border border-white/30">
                  <svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <!-- Mini Satellite Badges -->
                <span class="absolute -top-1 -right-2 px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-700 text-[9px] font-bold border border-amber-200 shadow-xs">
                  SQL
                </span>
                <span class="absolute -bottom-1 -left-2 px-1.5 py-0.2 rounded-full bg-orange-100 text-orange-700 text-[9px] font-bold border border-orange-200 shadow-xs">
                  PROXY
                </span>
              </div>

              <!-- 4. Custom URL / Web App Artwork -->
              <div v-else-if="app.launchType === 'url'" class="relative flex items-center justify-center">
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-500 to-blue-500 flex items-center justify-center text-white shadow-lg shadow-sky-500/25 border border-white/30">
                  <svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                </div>
                <span class="absolute -bottom-1 -right-1 px-1.5 py-0.2 rounded-full bg-sky-100 text-sky-700 text-[9px] font-bold border border-sky-200 shadow-xs">
                  WEB
                </span>
              </div>

              <!-- 5. Custom Local App Artwork -->
              <div v-else-if="app.launchType === 'file'" class="relative flex items-center justify-center">
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-purple-500/25 border border-white/30">
                  <svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <span class="absolute -bottom-1 -right-1 px-1.5 py-0.2 rounded-full bg-purple-100 text-purple-700 text-[9px] font-bold border border-purple-200 shadow-xs">
                  EXE
                </span>
              </div>

              <!-- 6. Custom Command Artwork -->
              <div v-else class="relative flex items-center justify-center">
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-slate-700 to-slate-900 flex items-center justify-center text-white shadow-lg shadow-slate-900/25 border border-white/20">
                  <svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <span class="absolute -bottom-1 -right-1 px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-700 text-[9px] font-bold border border-slate-300 shadow-xs">
                  CMD
                </span>
              </div>

            </div>
          </div>

          <!-- Bottom Information Content Area -->
          <div class="p-4 flex flex-col justify-between flex-1 space-y-3">
            
            <div class="space-y-1.5">
              <!-- Title -->
              <h2 class="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                {{ app.name }}
              </h2>

              <!-- Description -->
              <p class="text-xs text-slate-500 leading-relaxed line-clamp-2 min-h-[32px]">
                {{ app.description }}
              </p>

              <!-- Tags (Soft Tinted Pills) -->
              <div class="flex flex-wrap gap-1 pt-1">
                <span
                  v-for="tag in (app.tags || []).slice(0, 3)"
                  :key="tag"
                  class="px-2 py-0.5 rounded-md text-[10px] font-medium"
                  :class="getTagClass(app)"
                >
                  {{ tag }}
                </span>
              </div>
            </div>

            <!-- Card Bottom Button -->
            <div class="pt-2">
              <button
                type="button"
                class="w-full py-2 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100/80 group-hover:bg-blue-600 group-hover:text-white transition-all duration-200 cursor-pointer flex items-center justify-center gap-1.5 active:scale-98"
                @click.stop="onLaunchApp(app)"
              >
                <span>进入应用</span>
                <svg class="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Add Custom App Card (Matching Delicate Poster Layout) -->
        <div
          class="rounded-2xl border-2 border-dashed border-slate-300/70 hover:border-blue-400 bg-white/50 hover:bg-blue-50/20 p-5 flex flex-col items-center justify-between text-center cursor-pointer min-h-[300px] group transition-all duration-300 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.03)] hover:shadow-md"
          @click="openAddAppModal"
        >
          <div class="w-full flex justify-end">
            <span class="text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200/60">
              自定义扩展
            </span>
          </div>

          <div class="flex flex-col items-center my-auto">
            <div class="w-14 h-14 rounded-2xl bg-white text-slate-400 group-hover:bg-blue-600 group-hover:text-white border border-slate-200 group-hover:border-blue-600 flex items-center justify-center mb-3 transition-all duration-300 group-hover:scale-110 shadow-xs">
              <svg class="w-6 h-6 transform group-hover:rotate-90 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <span class="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors mb-1">
              添加第三方应用入口
            </span>
            <span class="text-xs text-slate-400 max-w-[170px] leading-relaxed">
              关联本地可执行程序、网页链接或自动化脚本
            </span>
          </div>

          <div class="w-full pt-3 border-t border-slate-200/50">
            <span class="text-xs font-semibold text-blue-600 flex items-center justify-center gap-1 group-hover:gap-1.5 transition-all">
              <span>立即添加</span>
              <span>→</span>
            </span>
          </div>
        </div>

      </div>

      <!-- Empty State -->
      <div
        v-if="filteredApps.length === 0"
        class="rounded-2xl bg-white border border-slate-200/80 min-h-[240px] flex flex-col items-center justify-center text-center p-6 shadow-xs"
      >
        <div class="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <h3 class="text-sm font-bold text-slate-900">未找到匹配的工具套件</h3>
        <p class="mt-1 text-xs text-slate-500 max-w-sm">没有找到与 "{{ searchQuery }}" 相关的应用，请尝试调整搜索词或切换分类。</p>
        <button
          type="button"
          class="mt-3.5 px-4 py-2 rounded-xl text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100/80 transition-colors cursor-pointer"
          @click="clearFilters"
        >
          清除搜索与筛选
        </button>
      </div>

    </div>

    <!-- Add / Edit Custom App Modal -->
    <teleport to="body">
      <div
        v-if="showAddAppModal"
        class="fixed inset-0 z-[9999] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4"
        @click.self="showAddAppModal = false"
      >
        <div class="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-5 sm:p-6 shadow-2xl space-y-4 text-slate-800 transform transition-all animate-in fade-in zoom-in-95 duration-150">
          <!-- Modal Header -->
          <div class="flex items-center justify-between border-b border-slate-100 pb-3">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 class="text-sm font-bold text-slate-900">
                {{ isEditing ? '编辑自定义扩展应用' : '添加自定义扩展应用' }}
              </h3>
            </div>
            <button
              class="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center cursor-pointer transition-colors"
              @click="showAddAppModal = false"
            >
              ✕
            </button>
          </div>

          <!-- Modal Body Form -->
          <div class="space-y-3.5 text-xs">
            <div>
              <label class="block text-slate-700 mb-1 font-semibold">应用名称</label>
              <input
                v-model="newApp.name"
                type="text"
                aria-label="应用名称"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all"
                placeholder="例如: 接口 Mock 抓包工具 / Swagger 调试台"
              >
            </div>

            <div>
              <label class="block text-slate-700 mb-1 font-semibold">应用类别</label>
              <select
                v-model="newApp.category"
                aria-label="应用类别"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all cursor-pointer"
              >
                <option value="核心构建">核心构建</option>
                <option value="调试造数">调试造数</option>
                <option value="扩展应用">扩展应用</option>
              </select>
            </div>
            
            <!-- Launch Type Selector Cards -->
            <div>
              <label class="block text-slate-700 mb-1.5 font-semibold">启动方式</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  class="flex flex-col items-center justify-center p-2 rounded-xl border transition-all cursor-pointer text-center"
                  :class="newApp.launchType === 'url'
                    ? 'border-blue-500 bg-blue-50/60 text-blue-700 font-bold shadow-2xs'
                    : 'border-slate-200 bg-slate-50/60 text-slate-600 hover:bg-slate-100'"
                  @click="newApp.launchType = 'url'"
                >
                  <svg class="w-4 h-4 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                  <span>网页链接</span>
                </button>

                <button
                  type="button"
                  class="flex flex-col items-center justify-center p-2 rounded-xl border transition-all cursor-pointer text-center"
                  :class="newApp.launchType === 'file'
                    ? 'border-blue-500 bg-blue-50/60 text-blue-700 font-bold shadow-2xs'
                    : 'border-slate-200 bg-slate-50/60 text-slate-600 hover:bg-slate-100'"
                  @click="newApp.launchType = 'file'"
                >
                  <svg class="w-4 h-4 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span>本地程序</span>
                </button>

                <button
                  type="button"
                  class="flex flex-col items-center justify-center p-2 rounded-xl border transition-all cursor-pointer text-center"
                  :class="newApp.launchType === 'cmd'
                    ? 'border-blue-500 bg-blue-50/60 text-blue-700 font-bold shadow-2xs'
                    : 'border-slate-200 bg-slate-50/60 text-slate-600 hover:bg-slate-100'"
                  @click="newApp.launchType = 'cmd'"
                >
                  <svg class="w-4 h-4 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>命令行脚本</span>
                </button>
              </div>
            </div>

            <!-- Path / URL Input with Choosers -->
            <div>
              <label class="block text-slate-700 mb-1 font-semibold">
                {{ newApp.launchType === 'url' ? '网页链接 (URL)' : newApp.launchType === 'file' ? '本地程序或目录路径' : '执行命令 (Cmd / Powershell指令)' }}
              </label>
              <div class="flex gap-2">
                <input
                  v-model="newApp.pathOrUrl"
                  type="text"
                  aria-label="启动方式的地址、路径或命令"
                  class="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all"
                  :placeholder="newApp.launchType === 'url' ? 'https://example.com' : newApp.launchType === 'file' ? 'C:\\Tools\\app.exe 或 D:\\Projects' : 'npm run dev 或 ping 127.0.0.1'"
                >
                <button
                  v-if="newApp.launchType === 'file'"
                  type="button"
                  class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium border border-slate-200 transition-colors cursor-pointer flex items-center gap-1 shrink-0"
                  @click="chooseFileForPath"
                >
                  文件
                </button>
                <button
                  v-if="newApp.launchType === 'file'"
                  type="button"
                  class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium border border-slate-200 transition-colors cursor-pointer flex items-center gap-1 shrink-0"
                  @click="chooseDirForPath"
                >
                  目录
                </button>
              </div>
            </div>

            <!-- Script Work Dir (Optional) -->
            <div v-if="newApp.launchType === 'cmd'">
              <label class="block text-slate-700 mb-1 font-semibold">脚本工作目录 (CMD Cwd - 可选)</label>
              <div class="flex gap-2">
                <input
                  v-model="newApp.cmdWorkDir"
                  type="text"
                  aria-label="命令工作目录"
                  class="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all"
                  placeholder="留空则默认为软件根目录..."
                >
                <button
                  type="button"
                  class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium border border-slate-200 transition-colors cursor-pointer flex items-center gap-1 shrink-0"
                  @click="chooseDirForCwd"
                >
                  选择
                </button>
              </div>
            </div>

            <!-- Description -->
            <div>
              <label class="block text-slate-700 mb-1 font-semibold">功能说明描述</label>
              <textarea
                v-model="newApp.description"
                rows="2"
                aria-label="功能说明描述"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/15 transition-all"
                placeholder="简要说明该扩展工具的具体功用或使用说明..."
              />
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="flex justify-end gap-2.5 pt-3 border-t border-slate-100">
            <button
              type="button"
              class="px-4 py-2 text-xs font-medium rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors"
              @click="showAddAppModal = false"
            >
              取消
            </button>
            <button
              type="button"
              class="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl cursor-pointer shadow-xs shadow-blue-500/30 transition-all active:scale-98"
              @click="confirmAddApp"
            >
              {{ isEditing ? '保存修改' : '确认添加' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- SVN Account Setup Modal -->
    <SvnAccountModal
      ref="svnModalRef"
      @success="onSvnModalSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import SvnAccountModal from '@/components/SvnAccountModal.vue'

export interface PortalApp {
  id: string
  name: string
  description: string
  icon: string
  iconType?: 'build' | 'data' | 'custom'
  category: string
  tags?: string[]
  status: 'active' | 'extension'
  statusLabel?: string
  iconBg?: string
  launchType?: 'url' | 'file' | 'cmd'
  pathOrUrl?: string
  cmdWorkDir?: string
}

const emit = defineEmits<{
  'launch-app': [appId: string]
}>()

const store = useAppStore()
const appVersion = computed(() => (ipc.version ? `v${ipc.version}` : 'v1.0.4'))
const showAddAppModal = ref(false)
const isEditing = ref(false)
const editingAppId = ref<string | null>(null)

function downloadZtoolsInstaller() {
  if (typeof window !== 'undefined') {
    const a = document.createElement('a')
    // 使用已在服务端稳定就绪的流式下载接口，保证即刻下载完整 97.3 MB 安装包
    a.href = '/api/order-dir/download-file?path=' + encodeURIComponent('D:\\build\\ztools\\ztools.Setup.1.0.3.exe')
    a.download = 'ztools.Setup.1.0.3.exe'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    store.showToast('已开始下载 ztools.Setup.1.0.3.exe (约 97.3 MB)', 'success')
  }
}

async function openZtoolsFolder() {
  const res = await ipc.openPath('D:\\build\\ztools')
  if (res.success) {
    store.showToast('已在文件管理器中打开 D:\\build\\ztools', 'success')
  } else {
    store.showToast('打开文件夹失败: ' + (res.error || '未知错误'), 'error')
  }
}
const selectedCategory = ref<string>('all')
const searchQuery = ref<string>('')

const categories = [
  { label: '全部套件', value: 'all' },
  { label: '核心构建', value: '核心构建' },
  { label: '调试造数', value: '调试造数' },
  { label: '扩展应用', value: '扩展应用' },
]

const newApp = ref({
  name: '',
  icon: '🛠️',
  category: '扩展应用',
  description: '',
  launchType: 'url' as 'url' | 'file' | 'cmd',
  pathOrUrl: '',
  cmdWorkDir: '',
})

const defaultApps: PortalApp[] = [
  {
    id: 'zbuild',
    name: '智慧病房系统构建与调试工具',
    description: '支持多医疗子系统自动化编译打包、多目录产物匹配、SVN 需求清单生成、远程服务器部署与提测发布。',
    icon: '📦',
    iconType: 'build',
    category: '核心构建',
    tags: ['Electron', 'SVN', 'SSH 部署', '多工程模版'],
    status: 'active',
    statusLabel: '核心内置',
  },
  {
    id: 'order-deploy',
    name: '测试订单部署解决方案',
    description: '快速浏览与解析 SVN 测试订单包目录树，支持按需选包，一键下载、上传并自动解压部署到目标 Linux 服务器。',
    icon: '🚀',
    category: '核心构建',
    tags: ['SVN 目录树', '按需选包', 'SSH 部署', '前端解压覆盖'],
    status: 'active',
    statusLabel: '核心内置',
  },
  // {
  //   id: 'order-build-upload',
  //   name: '订单打包上传 SVN',
  //   description: '选择医院和订单，为每个本地项目确认对应分支，按队列完成打包并上传至 SVN。',
  //   icon: '📦',
  //   iconType: 'build',
  //   category: '核心构建',
  //   tags: ['项目分支配对', '构建队列', 'SVN 上传'],
  //   status: 'active',
  //   statusLabel: '核心内置',
  // },
  {
    id: 'mock-query',
    name: '终端数据链路提取控制台',
    description: '跨接口终端设备链路数据代理提取，自动抓取机构、护理单元与患者数据，支持数据库全类型增量造数。',
    icon: '⚡',
    iconType: 'data',
    category: '调试造数',
    tags: ['MySQL 直连', '跨域代理', '自动组装', '6 大数据模版'],
    status: 'active',
    statusLabel: '核心内置',
  },
]

// Load custom apps from localStorage
const storedCustom = localStorage.getItem('zbuild_custom_apps')
const initialCustomApps = storedCustom ? JSON.parse(storedCustom) : []

const apps = ref<PortalApp[]>([
  ...defaultApps,
  ...initialCustomApps,
])

const filteredApps = computed(() => {
  return apps.value.filter((app) => {
    const matchesCategory =
      selectedCategory.value === 'all' ||
      (selectedCategory.value === '扩展应用' ? (app.status === 'extension' || app.category === '扩展应用') : app.category === selectedCategory.value)

    const matchesSearch =
      !searchQuery.value.trim() ||
      app.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (app.tags && app.tags.some(t => t.toLowerCase().includes(searchQuery.value.toLowerCase())))

    return matchesCategory && matchesSearch
  })
})

function getCategoryCount(catVal: string): number {
  if (catVal === 'all') return apps.value.length
  if (catVal === '扩展应用') {
    return apps.value.filter(a => a.status === 'extension' || a.category === '扩展应用').length
  }
  return apps.value.filter(a => a.category === catVal).length
}

function getCardBannerBg(app: PortalApp): string {
  if (app.id === 'zbuild') {
    return 'bg-gradient-to-b from-blue-50/80 via-blue-50/30 to-white'
  }
  if (app.id === 'order-deploy') {
    return 'bg-gradient-to-b from-emerald-50/80 via-emerald-50/30 to-white'
  }
  if (app.id === 'mock-query') {
    return 'bg-gradient-to-b from-amber-50/80 via-amber-50/30 to-white'
  }
  if (app.launchType === 'url') {
    return 'bg-gradient-to-b from-sky-50/80 via-sky-50/30 to-white'
  }
  if (app.launchType === 'file') {
    return 'bg-gradient-to-b from-purple-50/80 via-purple-50/30 to-white'
  }
  return 'bg-gradient-to-b from-slate-50 via-slate-50/30 to-white'
}

function getStatusBadgeClass(app: PortalApp): string {
  if (app.status === 'active') {
    return 'bg-emerald-50/90 text-emerald-700 border-emerald-200/80'
  }
  if (app.launchType === 'url') {
    return 'bg-sky-50/90 text-sky-700 border-sky-200/80'
  }
  if (app.launchType === 'file') {
    return 'bg-purple-50/90 text-purple-700 border-purple-200/80'
  }
  return 'bg-slate-100/90 text-slate-700 border-slate-200'
}

function getStatusDotClass(app: PortalApp): string {
  if (app.status === 'active') {
    return 'bg-emerald-500'
  }
  if (app.launchType === 'url') {
    return 'bg-sky-500'
  }
  if (app.launchType === 'file') {
    return 'bg-purple-500'
  }
  return 'bg-slate-500'
}

function getTagClass(app: PortalApp): string {
  if (app.id === 'zbuild') {
    return 'bg-blue-50/80 text-blue-700 border border-blue-200/50'
  }
  if (app.id === 'order-deploy') {
    return 'bg-emerald-50/80 text-emerald-700 border border-emerald-200/50'
  }
  if (app.id === 'mock-query') {
    return 'bg-amber-50/80 text-amber-700 border border-amber-200/50'
  }
  return 'bg-purple-50/80 text-purple-700 border border-purple-200/50'
}

function clearFilters() {
  selectedCategory.value = 'all'
  searchQuery.value = ''
}

const svnModalRef = ref<InstanceType<typeof SvnAccountModal> | null>(null)

function hasSvnAccount(): boolean {
  const form = store.config?.form
  const username = form?.svnUsername?.trim() || ''
  const password = form?.svnPassword?.trim() || ''
  return Boolean(username && password)
}

function onSvnModalSuccess(appId: string) {
  if (appId) {
    emit('launch-app', appId)
  }
}

async function onLaunchApp(app: PortalApp) {
  // SVN 核心应用校验 SVN 账户
  const svnRequiredApps = ['zbuild', 'order-deploy', 'order-build-upload']
  if (svnRequiredApps.includes(app.id)) {
    if (!hasSvnAccount()) {
      svnModalRef.value?.show({
        targetAppId: app.id,
        targetAppName: app.name,
      })
      return
    }
  }

  if (app.id === 'zbuild') {
    emit('launch-app', 'zbuild')
  } else if (app.id === 'order-deploy') {
    emit('launch-app', 'order-deploy')
  } else if (app.id === 'order-build-upload') {
    emit('launch-app', 'order-build-upload')
  } else if (app.id === 'mock-query') {
    emit('launch-app', 'mock-query')
  } else if (app.id.startsWith('custom-')) {
    try {
      store.showToast(`正在拉起「${app.name}」...`, 'info')
      await ipc.launchTool({
        pathOrUrl: app.pathOrUrl || '',
        launchType: app.launchType,
        cmdWorkDir: app.cmdWorkDir,
      })
    } catch (err: any) {
      store.showToast(`拉起失败: ${err.message}`, 'error')
    }
  } else {
    store.showToast(`已拉起「${app.name}」扩展环境`, 'info')
  }
}

async function chooseFileForPath() {
  try {
    const file = await ipc.chooseExecutable()
    if (file) {
      newApp.value.pathOrUrl = file
    }
  } catch (err: any) {
    store.showToast(`选择文件失败: ${err.message}`, 'error')
  }
}

async function chooseDirForPath() {
  try {
    const dir = await ipc.chooseDirectory()
    if (dir) {
      newApp.value.pathOrUrl = dir
    }
  } catch (err: any) {
    store.showToast(`选择目录失败: ${err.message}`, 'error')
  }
}

async function chooseDirForCwd() {
  try {
    const dir = await ipc.chooseDirectory()
    if (dir) {
      newApp.value.cmdWorkDir = dir
    }
  } catch (err: any) {
    store.showToast(`选择目录失败: ${err.message}`, 'error')
  }
}

function saveCustomApps() {
  const customList = apps.value.filter((app) => app.id.startsWith('custom-'))
  localStorage.setItem('zbuild_custom_apps', JSON.stringify(customList))
}

function deleteApp(appId: string) {
  if (confirm('确认要删除这个自定义扩展应用吗？')) {
    apps.value = apps.value.filter((app) => app.id !== appId)
    saveCustomApps()
    store.showToast('已成功删除该扩展应用', 'success')
  }
}

function openAddAppModal() {
  isEditing.value = false
  editingAppId.value = null
  newApp.value = {
    name: '',
    icon: '🛠️',
    category: '扩展应用',
    description: '',
    launchType: 'url',
    pathOrUrl: '',
    cmdWorkDir: '',
  }
  showAddAppModal.value = true
}

function openEditAppModal(app: PortalApp) {
  isEditing.value = true
  editingAppId.value = app.id
  newApp.value = {
    name: app.name,
    icon: app.icon || '🛠️',
    category: app.category || '扩展应用',
    description: app.description || '',
    launchType: app.launchType || 'url',
    pathOrUrl: app.pathOrUrl || '',
    cmdWorkDir: app.cmdWorkDir || '',
  }
  showAddAppModal.value = true
}

function confirmAddApp() {
  if (!newApp.value.name.trim()) {
    store.showToast('请输入应用名称', 'warning')
    return
  }
  if (!newApp.value.pathOrUrl.trim()) {
    store.showToast('请输入链接、路径或指令', 'warning')
    return
  }

  if (isEditing.value && editingAppId.value) {
    const idx = apps.value.findIndex((app) => app.id === editingAppId.value)
    if (idx !== -1) {
      apps.value[idx] = {
        ...apps.value[idx],
        name: newApp.value.name.trim(),
        description: newApp.value.description.trim() || '自定义扩展工具入口',
        icon: newApp.value.icon || '🛠️',
        category: newApp.value.category || '扩展应用',
        tags: [
          newApp.value.launchType === 'url' ? '网页链接' : newApp.value.launchType === 'file' ? '本地程序' : '终端命令',
          '自定义扩展',
        ],
        launchType: newApp.value.launchType,
        pathOrUrl: newApp.value.pathOrUrl.trim(),
        cmdWorkDir: newApp.value.launchType === 'cmd' ? newApp.value.cmdWorkDir.trim() : undefined,
      }
      saveCustomApps()
      store.showToast('保存修改成功', 'success')
    }
  } else {
    const customApp: PortalApp = {
      id: 'custom-' + Date.now(),
      name: newApp.value.name.trim(),
      description: newApp.value.description.trim() || '自定义扩展工具入口',
      icon: newApp.value.icon || '🛠️',
      iconType: 'custom',
      category: newApp.value.category || '扩展应用',
      tags: [
        newApp.value.launchType === 'url' ? '网页链接' : newApp.value.launchType === 'file' ? '本地程序' : '终端命令',
        '自定义扩展',
      ],
      status: 'extension',
      statusLabel: newApp.value.launchType === 'url' ? '网页扩展' : newApp.value.launchType === 'file' ? '本地扩展' : '脚本扩展',
      iconBg: 'bg-purple-50 text-purple-600 border-purple-100',
      launchType: newApp.value.launchType,
      pathOrUrl: newApp.value.pathOrUrl.trim(),
      cmdWorkDir: newApp.value.launchType === 'cmd' ? newApp.value.cmdWorkDir.trim() : undefined,
    }

    apps.value.push(customApp)
    saveCustomApps()
    store.showToast('成功添加自定义应用入口', 'success')
  }

  // Reset
  newApp.value = {
    name: '',
    icon: '🛠️',
    category: '扩展应用',
    description: '',
    launchType: 'url',
    pathOrUrl: '',
    cmdWorkDir: '',
  }
  isEditing.value = false
  editingAppId.value = null
  showAddAppModal.value = false
}
</script>
