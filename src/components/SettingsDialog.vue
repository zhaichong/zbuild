<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        @click="visible = false"
      />

      <!-- Dialog Box -->
      <div
        class="relative bg-white rounded-2xl shadow-2xl w-full max-w-4xl z-10 flex flex-col overflow-hidden border border-slate-200/80 animate-in fade-in zoom-in-95 duration-150"
        style="height: 85vh; max-height: 780px;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/25">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h2 class="text-base font-bold text-slate-800 tracking-tight leading-tight">系统设置</h2>
              <p class="text-xs text-slate-400">自定义路径、打包构建命令、多目标发布与运行环境</p>
            </div>
          </div>
          <button
            class="text-slate-400 hover:text-slate-600 transition-colors p-1.5 rounded-lg hover:bg-slate-100"
            title="关闭 (Esc)"
            @click="visible = false"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Main Body: Sidebar Tabs + Content Area -->
        <div v-if="store.config" class="flex-1 min-h-0 flex overflow-hidden">
          <!-- Left Navigation Sidebar -->
          <nav class="w-48 sm:w-52 bg-slate-50/80 border-r border-slate-100 p-3 flex flex-col gap-1.5 shrink-0 select-none overflow-y-auto">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all text-left group relative"
              :class="activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm font-semibold border border-slate-200/70'
                : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900 border border-transparent'"
              @click="activeTab = tab.id"
            >
              <!-- Icon Container -->
              <div
                class="w-6 h-6 rounded-lg flex items-center justify-center transition-colors shrink-0"
                :class="activeTab === tab.id ? 'text-blue-600 bg-blue-50' : 'text-slate-400 group-hover:text-slate-600'"
              >
                <!-- Tab Icons -->
                <svg v-if="tab.id === 'basic'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <svg v-else-if="tab.id === 'build'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <svg v-else-if="tab.id === 'publish'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <svg v-else-if="tab.id === 'env'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <svg v-else-if="tab.id === 'preference'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                <svg v-else-if="tab.id === 'about'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <span class="flex-1 truncate">{{ tab.label }}</span>

              <!-- Active right bar -->
              <div
                v-if="activeTab === tab.id"
                class="w-1.5 h-4 rounded-full bg-blue-600"
              />
            </button>
          </nav>

          <!-- Right Content Panel -->
          <div class="flex-1 min-w-0 overflow-y-auto p-6 space-y-6 bg-slate-50/40">
            <!-- ==================== Tab 1: 路径与基础 (basic) ==================== -->
            <div v-show="activeTab === 'basic'" class="space-y-5">
              <div class="border-b border-slate-200/60 pb-3">
                <h3 class="text-sm font-bold text-slate-800">基础路径配置</h3>
                <p class="text-xs text-slate-400 mt-0.5">配置工作空间根目录以及本地构建产物输出目录</p>
              </div>

              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">工作目录 (Root Path)</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.rootPath"
                      type="text"
                      class="flex-1 form-input min-w-0 text-xs font-mono"
                      placeholder="例如: D:\build"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors shrink-0 shadow-2xs cursor-pointer"
                      @click="onChooseDir('rootPath')"
                    >
                      浏览...
                    </button>
                  </div>
                  <p class="mt-1.5 text-[11px] text-slate-400">系统将自动扫描此目录及其子目录下的所有 Git 仓库项目。</p>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">本地输出目录 (Local Output)</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.localOutputDir"
                      type="text"
                      class="flex-1 form-input min-w-0 text-xs font-mono"
                      placeholder="例如: D:\output"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors shrink-0 shadow-2xs cursor-pointer"
                      @click="onChooseDir('localOutputDir')"
                    >
                      浏览...
                    </button>
                  </div>
                  <p class="mt-1.5 text-[11px] text-slate-400">本地构建产物存档与打包 zip 文件的目标路径。</p>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">提测单目录 / 创建目录位置</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.orderDirPath"
                      type="text"
                      class="flex-1 form-input min-w-0 font-mono text-xs"
                      placeholder="例如: D:\yh\特殊订单\2026"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors shrink-0 shadow-2xs cursor-pointer"
                      @click="onChooseDir('orderDirPath')"
                    >
                      浏览...
                    </button>
                  </div>
                  <p class="mt-1.5 text-[11px] text-slate-400 leading-relaxed">
                    配置后在主界面输入订单号后可勾选「自动创建提测目录」，系统将自动创建订单同名文件夹并生成 Excel 提测单。
                  </p>
                </div>
              </div>
            </div>

            <!-- ==================== Tab 2: 打包构建 (build) ==================== -->
            <div v-show="activeTab === 'build'" class="space-y-5">
              <div class="border-b border-slate-200/60 pb-3">
                <h3 class="text-sm font-bold text-slate-800">打包构建设置</h3>
                <p class="text-xs text-slate-400 mt-0.5">配置默认打包命令与项目独立命令，支持 npm / pnpm / yarn / 脚本智能识别</p>
              </div>

              <!-- 全局默认打包命令 -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-3.5">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <label class="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-blue-600" />
                    默认全局打包命令 / 脚本
                  </label>
                  <div class="flex items-center gap-1.5">
                    <span class="text-[11px] text-slate-400">快捷填入:</span>
                    <button
                      type="button"
                      class="px-2.5 py-0.5 text-[11px] font-mono rounded-md bg-slate-50 border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 transition-all shadow-2xs cursor-pointer"
                      @click="store.config.buildCommand = 'deploy.sh'"
                    >
                      deploy.sh
                    </button>
                    <button
                      type="button"
                      class="px-2.5 py-0.5 text-[11px] font-mono rounded-md bg-slate-50 border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 transition-all shadow-2xs cursor-pointer"
                      @click="store.config.buildCommand = 'npm run build'"
                    >
                      npm run build
                    </button>
                    <button
                      type="button"
                      class="px-2.5 py-0.5 text-[11px] font-mono rounded-md bg-slate-50 border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/50 transition-all shadow-2xs cursor-pointer"
                      @click="store.config.buildCommand = 'npm run build:prod'"
                    >
                      npm run build:prod
                    </button>
                  </div>
                </div>

                <div>
                  <input
                    v-model="store.config.buildCommand"
                    type="text"
                    class="w-full form-input font-mono text-xs text-slate-800 bg-slate-50/50 focus:bg-white"
                    placeholder="例如: deploy.sh 或 npm run build"
                  >
                </div>

                <div class="bg-blue-50/60 border border-blue-100/80 rounded-lg p-3 text-[11px] text-slate-600 flex items-start gap-2.5 leading-relaxed">
                  <svg class="w-4 h-4 text-blue-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <span class="font-semibold text-slate-800">智能免配支持：</span>
                    若项目设置为 <code class="px-1.5 py-0.5 rounded bg-white border border-blue-200/60 font-mono text-blue-700 text-[11px]">deploy.sh</code> 但项目目录中未找到该脚本，系统会自动读取 <code class="px-1.5 py-0.5 rounded bg-white border border-blue-200/60 font-mono text-blue-700 text-[11px]">package.json</code> 自动调用内置打包命令（如 <code class="px-1.5 py-0.5 rounded bg-white border border-blue-200/60 font-mono text-blue-700 text-[11px]">npm run build</code>）。
                  </div>
                </div>
              </div>

              <!-- 各项目独立打包命令 -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <h4 class="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                      各项目独立打包命令
                    </h4>
                    <p class="text-[11px] text-slate-400 mt-0.5">针对需要特殊打包指令的项目进行覆盖配置</p>
                  </div>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100/80 active:bg-blue-200/70 rounded-lg transition-colors border border-blue-200/60 shadow-2xs cursor-pointer"
                    @click="showAddBuildCmdModal = !showAddBuildCmdModal"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    添加项目命令
                  </button>
                </div>

                <!-- Inline Add Build Command -->
                <div
                  v-if="showAddBuildCmdModal"
                  class="flex flex-wrap items-center gap-2 bg-gradient-to-r from-blue-50/90 to-indigo-50/70 p-3.5 rounded-xl border border-blue-200/80 shadow-2xs"
                >
                  <input
                    v-model="newBuildCmdProjectName"
                    type="text"
                    class="w-40 px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none"
                    placeholder="项目名称"
                    @keyup.enter="confirmAddBuildCmdProject"
                  >
                  <input
                    v-model="newBuildCmdValue"
                    type="text"
                    class="flex-1 min-w-[10rem] px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none"
                    placeholder="打包命令 (如 npm run build:prod)"
                    @keyup.enter="confirmAddBuildCmdProject"
                  >
                  <button
                    type="button"
                    class="px-3.5 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-2xs cursor-pointer"
                    @click="confirmAddBuildCmdProject"
                  >
                    添加
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1.5 text-xs border border-slate-200 bg-white text-slate-500 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                    @click="showAddBuildCmdModal = false"
                  >
                    取消
                  </button>
                </div>

                <!-- Project Build Commands List -->
                <div class="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                  <div
                    v-for="projName in allConfiguredBuildCommandProjects"
                    :key="projName"
                    class="bg-slate-50/60 rounded-xl border border-slate-200/80 shadow-2xs overflow-hidden transition-all hover:border-slate-300"
                  >
                    <!-- Project default command bar -->
                    <div class="flex items-center gap-2.5 px-3.5 py-2.5 bg-white">
                      <!-- Project Name Tag -->
                      <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-semibold text-xs w-36 sm:w-44 shrink-0 truncate border border-slate-200/60" :title="projName">
                        <svg class="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                        <span class="truncate">{{ projName }}</span>
                      </div>

                      <!-- Command Input -->
                      <input
                        v-if="store.config.buildCommands"
                        v-model="store.config.buildCommands[projName]"
                        type="text"
                        class="flex-1 min-w-0 px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-slate-50/50 text-slate-800 focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition-colors"
                        :placeholder="store.config.buildCommand || 'deploy.sh'"
                        title="项目默认打包命令"
                      >

                      <!-- Toggle branch rules button -->
                      <button
                        type="button"
                        class="px-2.5 py-1.5 text-[11px] rounded-lg font-medium flex items-center gap-1.5 border transition-all shrink-0 cursor-pointer"
                        :class="getBranchCmdRuleCount(projName) > 0
                          ? 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 shadow-2xs'
                          : 'bg-white border-slate-200 text-slate-500 hover:text-slate-700 hover:bg-slate-50'"
                        :title="`管理 ${projName} 的分支特定打包命令`"
                        @click="toggleExpandBranchCmd(projName)"
                      >
                        <svg class="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                        </svg>
                        <span>分支规则</span>
                        <span
                          v-if="getBranchCmdRuleCount(projName) > 0"
                          class="px-1.5 py-0.2 rounded-full bg-blue-600 text-white text-[10px] leading-tight font-bold"
                        >
                          {{ getBranchCmdRuleCount(projName) }}
                        </span>
                        <svg
                          class="w-3.5 h-3.5 transition-transform text-slate-400"
                          :class="{ 'rotate-180': expandedBranchCmdProjects.has(projName) }"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      <!-- Delete Button -->
                      <button
                        type="button"
                        class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors shrink-0 cursor-pointer"
                        title="删除此项目全部打包命令配置"
                        @click="removeProjectBuildCommand(projName)"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>

                    <!-- Expandable Branch Command Rules Panel -->
                    <div
                      v-if="expandedBranchCmdProjects.has(projName)"
                      class="border-t border-slate-200/70 bg-slate-50/80 p-3.5 space-y-3"
                    >
                      <div class="flex items-center justify-between text-[11px]">
                        <span class="font-semibold text-slate-700 flex items-center gap-1.5">
                          <span class="w-1.5 h-1.5 rounded-full bg-blue-600" />
                          分支专属打包命令 (优先级高于项目默认)
                        </span>
                        <span class="text-slate-400 text-[10px]">支持精确分支名或通配符 (如 release/*)</span>
                      </div>

                      <!-- Existing branch rules -->
                      <div v-if="getBranchRules(projName).length > 0" class="space-y-2">
                        <div
                          v-for="rule in getBranchRules(projName)"
                          :key="rule.branch"
                          class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-slate-200/80 text-xs shadow-2xs"
                        >
                          <span class="font-mono font-semibold text-blue-700 px-2 py-0.5 rounded-md bg-blue-50 border border-blue-200/60 max-w-[12rem] truncate shrink-0" :title="rule.branch">
                            {{ rule.branch }}
                          </span>
                          <span class="text-slate-300 text-xs shrink-0">→</span>
                          <input
                            v-if="store.config?.branchBuildCommands?.[projName]"
                            v-model="store.config.branchBuildCommands[projName][rule.branch]"
                            type="text"
                            class="flex-1 min-w-0 px-2.5 py-1 font-mono text-xs border border-slate-200 rounded-md bg-slate-50/40 text-slate-800 focus:bg-white focus:border-blue-500 outline-none"
                            placeholder="打包命令"
                          >
                          <button
                            type="button"
                            class="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors shrink-0 cursor-pointer"
                            title="删除此分支打包命令规则"
                            @click="removeBranchRule(projName, rule.branch)"
                          >
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      </div>
                      <div v-else class="text-[11px] text-slate-400 bg-white rounded-lg p-2.5 text-center border border-dashed border-slate-200">
                        当前项目尚未配置分支专属命令，所有分支默认执行项目命令
                      </div>

                      <!-- Add new branch rule inline -->
                      <div class="flex items-center gap-2 pt-0.5">
                        <div class="relative w-40 sm:w-48 shrink-0">
                          <input
                            v-model="newBranchNameMap[projName]"
                            :list="`branches-list-${projName}`"
                            type="text"
                            class="w-full px-2.5 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                            placeholder="分支 (如 master 或 release/*)"
                            @keyup.enter="addBranchRule(projName)"
                          >
                          <datalist :id="`branches-list-${projName}`">
                            <option
                              v-for="b in getProjectKnownBranches(projName)"
                              :key="b"
                              :value="b"
                            />
                          </datalist>
                        </div>
                        <input
                          v-model="newBranchCmdMap[projName]"
                          type="text"
                          class="flex-1 min-w-0 px-2.5 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                          placeholder="该分支打包命令 (如 pnpm run build:prod)"
                          @keyup.enter="addBranchRule(projName)"
                        >
                        <button
                          type="button"
                          class="px-3 py-1.5 text-xs bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors shrink-0 flex items-center gap-1 cursor-pointer shadow-2xs"
                          @click="addBranchRule(projName)"
                        >
                          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                          </svg>
                          添加规则
                        </button>
                      </div>
                    </div>
                  </div>
                  <div v-if="allConfiguredBuildCommandProjects.length === 0" class="text-center py-6 text-xs text-slate-400 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                    未配置独立打包命令，所有项目将默认使用全局命令
                  </div>
                </div>
              </div>

              <!-- 打包产物目录配置 -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <h4 class="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      打包产物获取目录
                    </h4>
                    <p class="text-[11px] text-slate-400 mt-0.5">多分支与多产物目录匹配（支持逗号分隔多个候选）</p>
                  </div>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100/80 active:bg-blue-200/70 rounded-lg transition-colors border border-blue-200/60 shadow-2xs cursor-pointer"
                    @click="showAddArtifactPathModal = !showAddArtifactPathModal"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    项目独立产物目录
                  </button>
                </div>

                <div>
                  <label class="block text-[11px] text-slate-500 font-medium mb-1.5">默认全局产物目录候选</label>
                  <input
                    v-model="globalArtifactPathsInput"
                    type="text"
                    class="w-full form-input font-mono text-xs"
                    placeholder="例如: dist, release, output, build, target, ."
                  >
                </div>

                <!-- Inline Add Artifact Path -->
                <div
                  v-if="showAddArtifactPathModal"
                  class="flex flex-wrap items-center gap-2 bg-gradient-to-r from-blue-50/90 to-indigo-50/70 p-3.5 rounded-xl border border-blue-200/80 shadow-2xs"
                >
                  <input
                    v-model="newArtifactProjectName"
                    type="text"
                    class="w-40 px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                    placeholder="项目名称"
                    @keyup.enter="confirmAddArtifactProject"
                  >
                  <input
                    v-model="newArtifactPathValue"
                    type="text"
                    class="flex-1 min-w-[10rem] px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                    placeholder="产物目录 (如 dist, release)"
                    @keyup.enter="confirmAddArtifactProject"
                  >
                  <button
                    type="button"
                    class="px-3.5 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
                    @click="confirmAddArtifactProject"
                  >
                    添加
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1.5 text-xs border border-slate-200 bg-white text-slate-500 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                    @click="showAddArtifactPathModal = false"
                  >
                    取消
                  </button>
                </div>

                <!-- Artifact project list -->
                <div v-if="allConfiguredArtifactPathProjects.length > 0" class="space-y-2 max-h-48 overflow-y-auto pr-1 pt-1">
                  <div
                    v-for="projName in allConfiguredArtifactPathProjects"
                    :key="projName"
                    class="flex items-center gap-2.5 bg-slate-50/60 px-3.5 py-2 rounded-xl border border-slate-200/80 shadow-2xs hover:border-blue-300 transition-colors"
                  >
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white text-slate-700 font-semibold text-xs w-36 sm:w-44 shrink-0 truncate border border-slate-200/60" :title="projName">
                      <svg class="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                      <span class="truncate">{{ projName }}</span>
                    </div>
                    <input
                      v-if="store.config.projectArtifactPaths"
                      v-model="store.config.projectArtifactPaths[projName]"
                      type="text"
                      class="flex-1 min-w-0 px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition-colors"
                      placeholder="留空继承全局默认"
                    >
                    <button
                      type="button"
                      class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors shrink-0 cursor-pointer"
                      title="删除此项目配置"
                      @click="removeProjectArtifactPath(projName)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ==================== Tab 3: 发布与上传 (publish) ==================== -->
            <div v-show="activeTab === 'publish'" class="space-y-5">
              <div class="border-b border-slate-200/60 pb-3">
                <h3 class="text-sm font-bold text-slate-800">发布与上传配置</h3>
                <p class="text-xs text-slate-400 mt-0.5">管理 SVN 根仓库、项目专属 SVN 仓库以及服务器远程部署目录</p>
              </div>

              <!-- SVN 仓库设置 -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-blue-500" />
                    <h4 class="text-xs font-semibold text-slate-800">SVN 仓库配置</h4>
                  </div>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100/80 rounded-lg transition-colors border border-blue-200/60 shadow-2xs cursor-pointer"
                    @click="showAddSvnRootModal = !showAddSvnRootModal"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    项目独立 SVN 仓库
                  </button>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">默认全局 SVN 根 URL</label>
                  <input
                    v-model="store.config.svnRootUrl"
                    type="text"
                    class="w-full form-input font-mono text-xs"
                    placeholder="https://10.1.1.120/svn/智慧病房特殊订单"
                  >
                </div>

                <!-- 常用 SVN 目录源列表 (支持多源切换) -->
                <div class="pt-3 border-t border-slate-100 space-y-3">
                  <div class="flex items-center justify-between">
                    <div>
                      <label class="block text-xs font-semibold text-slate-700">常用 SVN 目录源列表 (多源配置)</label>
                      <p class="text-[11px] text-slate-400">配置多个常用的 SVN 订单或版本目录位置，在订单部署时可快捷切换</p>
                    </div>
                    <button
                      type="button"
                      class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100/80 rounded-lg transition-colors border border-blue-200/60 cursor-pointer"
                      @click="showAddSvnLocModal = !showAddSvnLocModal"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                      </svg>
                      添加 SVN 目录源
                    </button>
                  </div>

                  <!-- Inline Add SVN Location -->
                  <div
                    v-if="showAddSvnLocModal"
                    class="flex flex-wrap items-center gap-2 bg-gradient-to-r from-blue-50/90 to-indigo-50/70 p-3.5 rounded-xl border border-blue-200/80 shadow-2xs"
                  >
                    <input
                      v-model="newSvnLocName"
                      type="text"
                      class="w-40 px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                      placeholder="源名称 (如 特殊订单)"
                      @keyup.enter="confirmAddSvnLocation"
                    >
                    <input
                      v-model="newSvnLocUrl"
                      type="text"
                      class="flex-1 min-w-[12rem] px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                      placeholder="https://10.1.1.120/svn/..."
                      @keyup.enter="confirmAddSvnLocation"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-opacity cursor-pointer"
                      @click="confirmAddSvnLocation"
                    >
                      添加
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 text-xs border border-slate-200 bg-white text-slate-500 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                      @click="showAddSvnLocModal = false"
                    >
                      取消
                    </button>
                  </div>

                  <!-- SVN Locations List -->
                  <div class="space-y-2 max-h-40 overflow-y-auto pr-1">
                    <div
                      v-for="(loc, idx) in configuredSvnLocations"
                      :key="loc.id || idx"
                      class="flex items-center gap-2.5 bg-slate-50/60 px-3.5 py-2 rounded-xl border border-slate-200/80 shadow-2xs hover:border-blue-300 transition-colors"
                    >
                      <input
                        v-model="loc.name"
                        type="text"
                        class="w-36 px-2.5 py-1 text-xs font-semibold border border-transparent hover:border-slate-200 focus:border-blue-500 rounded-lg bg-transparent outline-none text-slate-800"
                        placeholder="源名称"
                      >
                      <input
                        v-model="loc.url"
                        type="text"
                        class="flex-1 min-w-0 px-2.5 py-1 text-xs font-mono border border-transparent hover:border-slate-200 focus:border-blue-500 rounded-lg bg-white/70 outline-none text-slate-700"
                        placeholder="SVN URL"
                      >
                      <button
                        type="button"
                        class="px-2.5 py-1 text-[11px] rounded-lg transition-colors cursor-pointer"
                        :class="store.config.svnRootUrl === loc.url ? 'bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200' : 'bg-white text-slate-600 border border-slate-200 hover:bg-blue-50 hover:text-blue-600'"
                        :title="store.config.svnRootUrl === loc.url ? '当前默认根目录' : '设为默认根目录'"
                        @click="setDefaultSvnLocation(loc)"
                      >
                        {{ store.config.svnRootUrl === loc.url ? '默认' : '设为默认' }}
                      </button>
                      <button
                        type="button"
                        class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors shrink-0 cursor-pointer"
                        title="删除此目录源"
                        @click="removeSvnLocation(idx)"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    <div v-if="configuredSvnLocations.length === 0" class="text-center py-3 text-xs text-slate-400">
                      暂无自定义目录源，默认使用全局 SVN 根 URL
                    </div>
                  </div>
                </div>

                <!-- SVN 凭据 -->
                <div class="grid grid-cols-2 gap-4 pt-3 border-t border-slate-100">
                  <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1.5">SVN 账号</label>
                    <input
                      v-model="store.config.form.svnUsername"
                      type="text"
                      class="w-full form-input text-xs"
                      placeholder="SVN 用户名"
                    >
                  </div>
                  <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1.5">SVN 密码</label>
                    <input
                      v-model="store.config.form.svnPassword"
                      type="password"
                      class="w-full form-input text-xs"
                      placeholder="SVN 密码"
                    >
                  </div>
                </div>

                <!-- 各项目独立 SVN 仓库列表 -->
                <div class="pt-3 border-t border-slate-100 space-y-3">
                  <label class="block text-xs font-semibold text-slate-700">各项目独立 SVN 仓库列表</label>

                  <!-- Inline Add Form -->
                  <div
                    v-if="showAddSvnRootModal"
                    class="flex flex-wrap items-center gap-2 bg-gradient-to-r from-blue-50/90 to-indigo-50/70 p-3.5 rounded-xl border border-blue-200/80 shadow-2xs mb-2"
                  >
                    <input
                      v-model="newSvnRootProjectName"
                      type="text"
                      class="w-40 px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                      placeholder="项目名称"
                      @keyup.enter="confirmAddSvnRootProject"
                    >
                    <input
                      v-model="newSvnRootValue"
                      type="text"
                      class="flex-1 min-w-[12rem] px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                      placeholder="https://10.1.1.120/svn/项目仓库"
                      @keyup.enter="confirmAddSvnRootProject"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-opacity cursor-pointer"
                      @click="confirmAddSvnRootProject"
                    >
                      添加
                    </button>
                    <button
                      type="button"
                      class="px-3 py-1.5 text-xs border border-slate-200 bg-white text-slate-500 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                      @click="showAddSvnRootModal = false"
                    >
                      取消
                    </button>
                  </div>

                  <div class="space-y-2 max-h-40 overflow-y-auto pr-1">
                    <div
                      v-for="projName in allConfiguredSvnRootProjects"
                      :key="projName"
                      class="flex items-center gap-2.5 bg-slate-50/60 px-3.5 py-2 rounded-xl border border-slate-200/80 shadow-2xs hover:border-blue-300 transition-colors"
                    >
                      <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white text-slate-700 font-semibold text-xs w-36 sm:w-44 shrink-0 truncate border border-slate-200/60" :title="projName">
                        <svg class="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                        <span class="truncate">{{ projName }}</span>
                      </div>
                      <input
                        v-if="store.config.projectSvnRoots"
                        v-model="store.config.projectSvnRoots[projName]"
                        type="text"
                        class="flex-1 min-w-0 px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition-colors"
                        placeholder="留空继承全局默认 SVN 根 URL"
                      >
                      <button
                        type="button"
                        class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors shrink-0 cursor-pointer"
                        title="删除此项目独立配置"
                        @click="removeProjectSvnRoot(projName)"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    <div v-if="allConfiguredSvnRootProjects.length === 0" class="text-center py-4 text-xs text-slate-400">
                      未配置项目独立 SVN 仓库，所有项目统一上传至默认 SVN 根 URL
                    </div>
                  </div>
                </div>
              </div>

              <!-- 服务器上传路径配置 -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500" />
                    <div>
                      <h4 class="text-xs font-semibold text-slate-800">远程服务器上传路径</h4>
                      <p class="text-[11px] text-slate-400">配置各项目打包后上传到远程 Linux 服务器的部署目录</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100/80 rounded-lg transition-colors border border-blue-200/60 shadow-2xs cursor-pointer"
                    @click="showAddProjectModal = !showAddProjectModal"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    添加项目
                  </button>
                </div>

                <!-- Inline Add Form -->
                <div
                  v-if="showAddProjectModal"
                  class="flex items-center gap-2 bg-gradient-to-r from-blue-50/90 to-indigo-50/70 p-3.5 rounded-xl border border-blue-200/80 shadow-2xs mb-2"
                >
                  <input
                    v-model="newProjectName"
                    type="text"
                    class="w-44 px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                    placeholder="项目名称"
                    @keyup.enter="confirmAddProject"
                  >
                  <input
                    v-model="newProjectPath"
                    type="text"
                    class="flex-1 px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 outline-none"
                    placeholder="服务器路径 (如 /home/data/web)"
                    @keyup.enter="confirmAddProject"
                  >
                  <button
                    type="button"
                    class="px-3.5 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-opacity cursor-pointer"
                    @click="confirmAddProject"
                  >
                    添加
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1.5 text-xs border border-slate-200 bg-white text-slate-500 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                    @click="showAddProjectModal = false"
                  >
                    取消
                  </button>
                </div>

                <div class="space-y-2 max-h-52 overflow-y-auto pr-1">
                  <div
                    v-for="projName in allConfiguredProjectNames"
                    :key="projName"
                    class="flex items-center gap-2.5 bg-slate-50/60 px-3.5 py-2 rounded-xl border border-slate-200/80 shadow-2xs hover:border-blue-300 transition-colors"
                  >
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white text-slate-700 font-semibold text-xs w-36 sm:w-44 shrink-0 truncate border border-slate-200/60" :title="projName">
                      <svg class="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                      <span class="truncate">{{ projName }}</span>
                    </div>
                    <input
                      v-model="store.config.serverUploadPaths[projName]"
                      type="text"
                      class="flex-1 px-3 py-1.5 text-xs font-mono border border-slate-200 rounded-lg bg-white text-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 outline-none transition-colors"
                      placeholder="/home/data/web"
                    >
                    <button
                      type="button"
                      class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors shrink-0 cursor-pointer"
                      title="删除此项目配置"
                      @click="removeProjectUploadPath(projName)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ==================== Tab 4: 工具环境 (env) ==================== -->
            <div v-show="activeTab === 'env'" class="space-y-5">
              <div class="border-b border-slate-200/60 pb-3">
                <h3 class="text-sm font-bold text-slate-800">运行工具与环境变量</h3>
                <p class="text-xs text-slate-400 mt-0.5">系统依赖的 Git, Bash, SVN, Node 与 npm 可执行文件路径</p>
              </div>

              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">Git 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.git"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="留空自动检测系统环境 (如 git.exe)"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors whitespace-nowrap shadow-2xs cursor-pointer"
                      @click="onChooseExe('git')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">Bash 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.bash"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\Git\bin\bash.exe"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors whitespace-nowrap shadow-2xs cursor-pointer"
                      @click="onChooseExe('bash')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">SVN 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.svn"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\TortoiseSVN\bin\svn.exe"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors whitespace-nowrap shadow-2xs cursor-pointer"
                      @click="onChooseExe('svn')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">Node 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.node"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\nodejs\node.exe"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors whitespace-nowrap shadow-2xs cursor-pointer"
                      @click="onChooseExe('node')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  <label class="block text-xs font-semibold text-slate-700 mb-1.5">npm 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.npm"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\nodejs\npm.cmd"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors whitespace-nowrap shadow-2xs cursor-pointer"
                      @click="onChooseExe('npm')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ==================== Tab 5: 个性偏好 (preference) ==================== -->
            <div v-show="activeTab === 'preference'" class="space-y-5">
              <div class="border-b border-slate-200/60 pb-3">
                <h3 class="text-sm font-bold text-slate-800">个性化偏好</h3>
                <p class="text-xs text-slate-400 mt-0.5">设置构建桌宠进度提示与界面交互行为</p>
              </div>

              <div class="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs space-y-4">
                <div class="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div>
                    <div class="text-xs font-semibold text-slate-800">启用打包桌宠进度提示</div>
                    <div class="text-[11px] text-slate-400 mt-0.5">在点击打包构建时，桌宠将在桌面实时同步展示当前打包阶段与进度气泡</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      v-model="deskPetEnabled"
                      type="checkbox"
                      class="sr-only peer"
                    >
                    <div class="w-10 h-5.5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4.5 after:w-4.5 after:transition-all peer-checked:bg-blue-600 shadow-inner" />
                  </label>
                </div>

                <fieldset class="space-y-3" :disabled="!deskPetEnabled">
                  <legend class="text-xs font-semibold text-slate-700">桌宠外观形象</legend>
                  <div class="grid grid-cols-2 gap-3.5">
                    <label
                      class="cursor-pointer rounded-xl border p-3.5 transition-all relative overflow-hidden flex items-center gap-3.5"
                      :class="deskPetStyle === 'pixel' ? 'border-blue-500 bg-blue-50/50 ring-2 ring-blue-500/20 shadow-2xs' : 'border-slate-200 bg-white hover:bg-slate-50'"
                    >
                      <input
                        v-model="deskPetStyle"
                        value="pixel"
                        type="radio"
                        class="sr-only"
                      >
                      <span class="text-2xl leading-none select-none" aria-hidden="true">🕺</span>
                      <div>
                        <span class="block text-xs font-bold text-slate-800">像素助手</span>
                        <span class="block text-[11px] text-slate-400 mt-0.5">经典生动动效与跳舞姿态</span>
                      </div>
                      <div v-if="deskPetStyle === 'pixel'" class="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-blue-600" />
                    </label>

                    <label
                      class="cursor-pointer rounded-xl border p-3.5 transition-all relative overflow-hidden flex items-center gap-3.5"
                      :class="deskPetStyle === 'blob' ? 'border-blue-500 bg-blue-50/50 ring-2 ring-blue-500/20 shadow-2xs' : 'border-slate-200 bg-white hover:bg-slate-50'"
                    >
                      <input
                        v-model="deskPetStyle"
                        value="blob"
                        type="radio"
                        class="sr-only"
                      >
                      <span class="inline-flex h-7 w-7 items-center justify-center rounded-[45%] bg-slate-900 text-[10px] tracking-[-2px] text-white font-bold select-none shadow-sm" aria-hidden="true">••</span>
                      <div>
                        <span class="block text-xs font-bold text-slate-800">黑团子</span>
                        <span class="block text-[11px] text-slate-400 mt-0.5">极简安静悬浮陪伴</span>
                      </div>
                      <div v-if="deskPetStyle === 'blob'" class="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-blue-600" />
                    </label>
                  </div>
                </fieldset>
              </div>
            </div>

            <!-- ==================== Tab 6: 关于软件 (about) ==================== -->
            <div v-show="activeTab === 'about'" class="space-y-5">
              <div class="border-b border-slate-200/60 pb-3">
                <h3 class="text-sm font-bold text-slate-800">关于软件</h3>
                <p class="text-xs text-slate-400 mt-0.5">软件版本信息、更新检查与团队致谢</p>
              </div>

              <!-- Brand & Version Hero Card -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-6 shadow-2xs flex flex-col sm:flex-row items-center sm:items-start gap-5">
                <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
                  <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div class="flex-1 text-center sm:text-left space-y-1.5">
                  <div class="flex items-center justify-center sm:justify-start gap-2.5 flex-wrap">
                    <h4 class="text-base font-bold text-slate-800">智慧病房系统构建与调试工具</h4>
                    <span class="px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200/70 text-blue-700 text-xs font-mono font-bold">
                      v{{ appVersion }}
                    </span>
                    <span class="px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200/70 text-emerald-700 text-[10px] font-semibold">
                      正式版 (Release)
                    </span>
                  </div>
                  <p class="text-xs text-slate-500 leading-relaxed">
                    专为智慧病房前端工程研发与医院定制化特殊订单交付打造的统一构建、测试与部署工作台。
                  </p>
                  <div class="pt-2 flex items-center justify-center sm:justify-start gap-3">
                    <button
                      type="button"
                      class="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg transition-colors shadow-2xs cursor-pointer disabled:opacity-60"
                      :disabled="checkingUpdate"
                      @click="checkUpdateManual"
                    >
                      <svg v-if="checkingUpdate" class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {{ checkingUpdate ? '正在检查更新...' : '检查新版本' }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Feature Highlights & Specs -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div class="bg-white border border-slate-200/80 rounded-xl p-4 shadow-2xs space-y-2">
                  <div class="flex items-center gap-2 text-xs font-bold text-slate-800">
                    <span class="w-2 h-2 rounded-full bg-blue-500" />
                    多项目构建与命令智能匹配
                  </div>
                  <p class="text-[11px] text-slate-500 leading-relaxed">
                    支持按项目与 Git 分支独立配置打包指令，智能识别 npm / pnpm / yarn / 脚本免配自动执行。
                  </p>
                </div>

                <div class="bg-white border border-slate-200/80 rounded-xl p-4 shadow-2xs space-y-2">
                  <div class="flex items-center gap-2 text-xs font-bold text-slate-800">
                    <span class="w-2 h-2 rounded-full bg-indigo-500" />
                    特殊订单发布与提测提效
                  </div>
                  <p class="text-[11px] text-slate-500 leading-relaxed">
                    一键创建订单目录与生成 Excel 提测单，支持多源 SVN 目录直连及远程 Linux 服务器部署。
                  </p>
                </div>

                <div class="bg-white border border-slate-200/80 rounded-xl p-4 shadow-2xs space-y-2">
                  <div class="flex items-center gap-2 text-xs font-bold text-slate-800">
                    <span class="w-2 h-2 rounded-full bg-purple-500" />
                    Native Mock 与数据库助手
                  </div>
                  <p class="text-[11px] text-slate-500 leading-relaxed">
                    内置原生 HTTP 请求模拟、MySQL 连通性测试与快速 SQL 执行助手，加速本地联调。
                  </p>
                </div>

                <div class="bg-white border border-slate-200/80 rounded-xl p-4 shadow-2xs space-y-2">
                  <div class="flex items-center gap-2 text-xs font-bold text-slate-800">
                    <span class="w-2 h-2 rounded-full bg-emerald-500" />
                    桌面宠物进度实时反馈
                  </div>
                  <p class="text-[11px] text-slate-500 leading-relaxed">
                    像素助手与黑团子桌面悬浮伴侣，构建与发布各个阶段状态可视化提示。
                  </p>
                </div>
              </div>

              <!-- Technology Stack & Info -->
              <div class="bg-white border border-slate-200/80 rounded-xl p-4 shadow-2xs">
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center sm:text-left">
                  <div class="p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div class="text-[10px] text-slate-400">核心架构</div>
                    <div class="text-xs font-semibold text-slate-700 mt-0.5">Electron + Vue 3</div>
                  </div>
                  <div class="p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div class="text-[10px] text-slate-400">构建工具</div>
                    <div class="text-xs font-semibold text-slate-700 mt-0.5">Vite + TypeScript</div>
                  </div>
                  <div class="p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div class="text-[10px] text-slate-400">运行平台</div>
                    <div class="text-xs font-semibold text-slate-700 mt-0.5">Windows 64-bit</div>
                  </div>
                  <div class="p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <div class="text-[10px] text-slate-400">状态</div>
                    <div class="text-xs font-semibold text-emerald-600 mt-0.5">运行正常</div>
                  </div>
                </div>

                <div class="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between flex-wrap gap-2 text-[11px] text-slate-400">
                  <span>智慧病房前端工程研发团队</span>
                  <span>Copyright © 2026 Yarward Electronics Co., Ltd.</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sticky Footer -->
        <div class="flex items-center justify-between px-6 py-3.5 border-t border-slate-100 bg-slate-50/60 shrink-0">
          <div class="text-[11px] text-slate-400 flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            修改后点击「保存设置」将同步应用至本地配置与当前运行环境
          </div>
          <div class="flex items-center gap-2.5">
            <button
              class="px-4 py-2 text-xs font-medium border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-800 transition-colors shadow-2xs cursor-pointer"
              @click="visible = false"
            >
              取消
            </button>
            <button
              class="px-5 py-2 text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg transition-all shadow-sm shadow-blue-500/25 flex items-center gap-1.5 cursor-pointer active:scale-98"
              @click="onSave"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              保存设置
            </button>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { saveConfig } from '@/composables/useConfig'
import { refreshProjects } from '@/composables/useProjects'
import { ipc } from '@/services/ipc'

const store = useAppStore()
const visible = ref(false)

type TabType = 'basic' | 'build' | 'publish' | 'env' | 'preference' | 'about'
const activeTab = ref<TabType>('basic')

const tabs: { id: TabType; label: string }[] = [
  { id: 'basic', label: '路径与基础' },
  { id: 'build', label: '打包构建' },
  { id: 'publish', label: '发布与上传' },
  { id: 'env', label: '工具环境' },
  { id: 'preference', label: '个性偏好' },
  { id: 'about', label: '关于软件' },
]

const appVersion = computed(() => ipc.version || '1.0.4')
const checkingUpdate = ref(false)

async function checkUpdateManual() {
  checkingUpdate.value = true
  try {
    const res = await ipc.checkForUpdates()
    if (res.state === 'not-available' || res.state === 'idle') {
      store.showToast(`当前已是最新版本 (v${appVersion.value})`, 'info')
    } else if (res.state === 'available') {
      store.showToast(`发现新版本 v${res.version || ''}，可前往更新`, 'success')
    }
  } catch (e: unknown) {
    store.showToast('检查更新失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  } finally {
    checkingUpdate.value = false
  }
}

const showAddProjectModal = ref(false)
const newProjectName = ref('')
const newProjectPath = ref('/home/data/web')

const showAddSvnLocModal = ref(false)
const newSvnLocName = ref('')
const newSvnLocUrl = ref('')

const showAddSvnRootModal = ref(false)
const newSvnRootProjectName = ref('')
const newSvnRootValue = ref('')

const showAddBuildCmdModal = ref(false)
const newBuildCmdProjectName = ref('')
const newBuildCmdValue = ref('deploy.sh')

const showAddArtifactPathModal = ref(false)
const newArtifactProjectName = ref('')
const newArtifactPathValue = ref('dist')

const configuredSvnLocations = computed(() => {
  if (!store.config) return []
  return store.config.svnLocations || []
})

const globalArtifactPathsInput = computed({
  get() {
    return (store.config?.artifactPaths || ['dist', 'release', 'build', 'output', 'target']).join(', ')
  },
  set(val: string) {
    if (!store.config) return
    store.config.artifactPaths = val
      .split(/[,;\n]+/)
      .map((s) => s.trim())
      .filter(Boolean)
  },
})

const deskPetEnabled = computed({
  get() {
    return store.config?.enableDeskPet !== false
  },
  set(val: boolean) {
    if (store.config) {
      store.config.enableDeskPet = val
    }
  },
})

const deskPetStyle = computed({
  get() {
    return store.config?.deskPetStyle === 'blob' ? 'blob' : 'pixel'
  },
  set(val: 'pixel' | 'blob') {
    if (store.config) {
      store.config.deskPetStyle = val
    }
  },
})

const DEFAULT_SERVER_UPLOAD_PATHS: Record<string, string> = {
  'yarward-ntv-frontend': '/home/data/web',
  'yarward-web-frontend': '/home/data/web',
  'zbuild': '/home/data/web',
  'zhbf-bedhead-frontend': '/home/data/web/a10',
  'zhbf-fontend': '/home/data/web/a10',
  'zhbf-web': '/home/data/web',
}

const DEFAULT_BUILD_COMMANDS: Record<string, string> = {
  'yarward-ntv-frontend': 'deploy.sh',
  'yarward-web-frontend': 'deploy.sh',
  'zbuild': 'deploy.sh',
  'zhbf-bedhead-frontend': 'deploy.sh',
  'zhbf-fontend': 'deploy.sh',
  'zhbf-web': 'deploy.sh',
}

function initConfigDefaults() {
  if (!store.config) return
  if (!store.config.buildCommand) {
    store.config.buildCommand = 'deploy.sh'
  }
  if (!store.config.buildCommands) {
    store.config.buildCommands = {}
  }
  if (!store.config.artifactPaths || !store.config.artifactPaths.length) {
    store.config.artifactPaths = ['dist', 'release', 'build', 'output', 'target']
  }
  if (!store.config.projectArtifactPaths) {
    store.config.projectArtifactPaths = {}
  }
  if (!store.config.projectSvnRoots) {
    store.config.projectSvnRoots = {}
  }
  if (!store.config.svnLocations || store.config.svnLocations.length === 0) {
    if (store.config.svnRootUrl) {
      store.config.svnLocations = [
        {
          id: 'default-loc',
          name: '默认特殊订单库',
          url: store.config.svnRootUrl,
          isDefault: true,
        },
      ]
    } else {
      store.config.svnLocations = []
    }
  }
  if (!store.config.branchBuildCommands) {
    store.config.branchBuildCommands = {}
  }
  for (const [key, val] of Object.entries(DEFAULT_BUILD_COMMANDS)) {
    if (!(key in store.config.buildCommands)) {
      store.config.buildCommands[key] = val
    }
  }
  if (!store.config.serverUploadPaths) {
    store.config.serverUploadPaths = {}
  }
  for (const [key, val] of Object.entries(DEFAULT_SERVER_UPLOAD_PATHS)) {
    if (!(key in store.config.serverUploadPaths)) {
      store.config.serverUploadPaths[key] = val
    }
  }
  if (store.projects) {
    for (const proj of store.projects) {
      if (!(proj.projectName in store.config.serverUploadPaths)) {
        store.config.serverUploadPaths[proj.projectName] =
          proj.serverUploadPath || DEFAULT_SERVER_UPLOAD_PATHS[proj.projectName] || '/home/data/web'
      }
      if (!(proj.projectName in store.config.buildCommands)) {
        store.config.buildCommands[proj.projectName] =
          proj.buildCommand || DEFAULT_BUILD_COMMANDS[proj.projectName] || store.config.buildCommand || 'deploy.sh'
      }
      if (proj.svnRoot && !(proj.projectName in store.config.projectSvnRoots)) {
        store.config.projectSvnRoots[proj.projectName] = proj.svnRoot
      }
    }
  }
}

watch(visible, (val) => {
  if (val) {
    initConfigDefaults()
  }
})

const allConfiguredProjectNames = computed(() => {
  if (!store.config?.serverUploadPaths) return []
  return Object.keys(store.config.serverUploadPaths)
})

const allConfiguredBuildCommandProjects = computed(() => {
  const set = new Set<string>()
  if (store.config?.buildCommands) {
    Object.keys(store.config.buildCommands).forEach((k) => set.add(k))
  }
  if (store.config?.branchBuildCommands) {
    Object.keys(store.config.branchBuildCommands).forEach((k) => set.add(k))
  }
  return Array.from(set)
})

const expandedBranchCmdProjects = ref<Set<string>>(new Set())
const newBranchNameMap = ref<Record<string, string>>({})
const newBranchCmdMap = ref<Record<string, string>>({})

function toggleExpandBranchCmd(projName: string) {
  const next = new Set(expandedBranchCmdProjects.value)
  if (next.has(projName)) {
    next.delete(projName)
  } else {
    next.add(projName)
  }
  expandedBranchCmdProjects.value = next
}

function getBranchRules(projName: string): Array<{ branch: string; command: string }> {
  const map = store.config?.branchBuildCommands?.[projName] || {}
  return Object.entries(map).map(([branch, command]) => ({ branch, command }))
}

function getBranchCmdRuleCount(projName: string): number {
  const map = store.config?.branchBuildCommands?.[projName]
  return map ? Object.keys(map).length : 0
}

function getProjectKnownBranches(projName: string): string[] {
  const proj = store.projects?.find((p) => p.projectName === projName)
  return proj?.branches || []
}

function addBranchRule(projName: string) {
  const branch = (newBranchNameMap.value[projName] || '').trim()
  const cmd = (newBranchCmdMap.value[projName] || '').trim()
  if (!branch) {
    store.showToast('请输入或选择分支名称', 'warning')
    return
  }
  if (!cmd) {
    store.showToast('请输入该分支的打包命令', 'warning')
    return
  }
  if (!store.config) return
  if (!store.config.branchBuildCommands) {
    store.config.branchBuildCommands = {}
  }
  if (!store.config.branchBuildCommands[projName]) {
    store.config.branchBuildCommands[projName] = {}
  }
  store.config.branchBuildCommands[projName][branch] = cmd
  newBranchNameMap.value[projName] = ''
  newBranchCmdMap.value[projName] = ''
  store.showToast(`已为 ${projName} 分支 ${branch} 添加打包命令`, 'success')
}

function removeBranchRule(projName: string, branchName: string) {
  if (store.config?.branchBuildCommands?.[projName]) {
    delete store.config.branchBuildCommands[projName][branchName]
    if (Object.keys(store.config.branchBuildCommands[projName]).length === 0) {
      delete store.config.branchBuildCommands[projName]
    }
  }
}

const allConfiguredArtifactPathProjects = computed(() => {
  if (!store.config?.projectArtifactPaths) return []
  return Object.keys(store.config.projectArtifactPaths)
})

const allConfiguredSvnRootProjects = computed(() => {
  if (!store.config?.projectSvnRoots) return []
  return Object.keys(store.config.projectSvnRoots)
})

function removeProjectUploadPath(name: string) {
  if (store.config?.serverUploadPaths) {
    delete store.config.serverUploadPaths[name]
  }
}

function removeProjectBuildCommand(name: string) {
  if (store.config?.buildCommands) {
    delete store.config.buildCommands[name]
  }
  if (store.config?.branchBuildCommands) {
    delete store.config.branchBuildCommands[name]
  }
}

function removeProjectArtifactPath(name: string) {
  if (store.config?.projectArtifactPaths) {
    delete store.config.projectArtifactPaths[name]
  }
}

function removeProjectSvnRoot(name: string) {
  if (store.config?.projectSvnRoots) {
    delete store.config.projectSvnRoots[name]
  }
}

function confirmAddSvnLocation() {
  const name = newSvnLocName.value.trim()
  const url = newSvnLocUrl.value.trim()
  if (!name) {
    store.showToast('请输入目录源名称', 'warning')
    return
  }
  if (!url) {
    store.showToast('请输入 SVN 目录 URL', 'warning')
    return
  }
  if (store.config) {
    if (!store.config.svnLocations) store.config.svnLocations = []
    store.config.svnLocations.push({
      id: 'loc-' + Date.now(),
      name,
      url,
      isDefault: store.config.svnLocations.length === 0,
    })
    if (store.config.svnLocations.length === 1 && !store.config.svnRootUrl) {
      store.config.svnRootUrl = url
    }
    newSvnLocName.value = ''
    newSvnLocUrl.value = ''
    showAddSvnLocModal.value = false
    store.showToast('已添加 SVN 目录源', 'success')
  }
}

function removeSvnLocation(idx: number) {
  if (store.config?.svnLocations) {
    store.config.svnLocations.splice(idx, 1)
  }
}

function setDefaultSvnLocation(loc: { name: string; url: string }) {
  if (store.config) {
    store.config.svnRootUrl = loc.url
    if (store.config.svnLocations) {
      store.config.svnLocations.forEach((item) => {
        item.isDefault = item.url === loc.url
      })
    }
    store.showToast(`已将「${loc.name}」设为默认 SVN 根目录`, 'success')
  }
}

function confirmAddSvnRootProject() {
  const name = newSvnRootProjectName.value.trim()
  const val = newSvnRootValue.value.trim()
  if (!name) {
    store.showToast('请输入项目名称', 'warning')
    return
  }
  if (!val) {
    store.showToast('请输入 SVN 仓库地址', 'warning')
    return
  }
  if (store.config) {
    if (!store.config.projectSvnRoots) store.config.projectSvnRoots = {}
    store.config.projectSvnRoots[name] = val
    newSvnRootProjectName.value = ''
    newSvnRootValue.value = ''
    showAddSvnRootModal.value = false
  }
}

function confirmAddProject() {
  const name = newProjectName.value.trim()
  const path = newProjectPath.value.trim() || '/home/data/web'
  if (!name) {
    store.showToast('请输入项目名称', 'warning')
    return
  }
  if (store.config) {
    if (!store.config.serverUploadPaths) store.config.serverUploadPaths = {}
    store.config.serverUploadPaths[name] = path
    newProjectName.value = ''
    newProjectPath.value = '/home/data/web'
    showAddProjectModal.value = false
  }
}

function confirmAddBuildCmdProject() {
  const name = newBuildCmdProjectName.value.trim()
  const cmd = newBuildCmdValue.value.trim() || 'deploy.sh'
  if (!name) {
    store.showToast('请输入项目名称', 'warning')
    return
  }
  if (store.config) {
    if (!store.config.buildCommands) store.config.buildCommands = {}
    store.config.buildCommands[name] = cmd
    newBuildCmdProjectName.value = ''
    newBuildCmdValue.value = 'deploy.sh'
    showAddBuildCmdModal.value = false
  }
}

function confirmAddArtifactProject() {
  const name = newArtifactProjectName.value.trim()
  const path = newArtifactPathValue.value.trim() || 'dist'
  if (!name) {
    store.showToast('请输入项目名称', 'warning')
    return
  }
  if (store.config) {
    if (!store.config.projectArtifactPaths) store.config.projectArtifactPaths = {}
    store.config.projectArtifactPaths[name] = path
    newArtifactProjectName.value = ''
    newArtifactPathValue.value = 'dist'
    showAddArtifactPathModal.value = false
  }
}

async function onChooseDir(field: 'rootPath' | 'localOutputDir' | 'orderDirPath') {
  if (!store.config) return
  const current = store.config[field] || ''
  const result = await ipc.chooseDirectory(current)
  if (result) {
    store.config[field] = result
  }
}

async function onChooseExe(tool: 'git' | 'bash' | 'svn' | 'node' | 'npm') {
  if (!store.config) return
  const current = store.config.tools[tool] || ''
  const result = await ipc.chooseExecutable(current)
  if (result) {
    store.config.tools[tool] = result
  }
}

async function onSave() {
  if (!store.config) return
  try {
    if (store.config.buildCommands) {
      for (const [name, cmd] of Object.entries(store.config.buildCommands)) {
        store.projectBuildCommands[name] = cmd
      }
    }
    await saveConfig(store.config)
    await refreshProjects()
    visible.value = false
    store.showToast('设置保存成功', 'success')
  } catch (e: unknown) {
    store.showToast('保存设置失败: ' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}

defineExpose({ visible })
</script>
