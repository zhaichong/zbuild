<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="visible = false"
      />
      <div
        class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-4xl z-10 flex flex-col overflow-hidden border border-border/60"
        style="height: 84vh; max-height: 760px;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-border-light bg-surface shrink-0">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h2 class="text-base font-bold text-text-1 leading-tight">系统设置</h2>
              <p class="text-xs text-text-3">自定义路径、打包构建命令、多目标发布与运行环境</p>
            </div>
          </div>
          <button
            class="text-text-3 hover:text-text-2 transition-colors p-1.5 rounded-lg hover:bg-border-light"
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
          <nav class="w-48 sm:w-52 bg-slate-50/80 border-r border-border-light p-3 flex flex-col gap-1 shrink-0 select-none overflow-y-auto">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all text-left group"
              :class="activeTab === tab.id
                ? 'bg-white text-primary shadow-2xs font-semibold border border-border/60'
                : 'text-text-2 hover:bg-slate-200/50 hover:text-text-1'"
              @click="activeTab = tab.id"
            >
              <span class="text-sm leading-none" :class="activeTab === tab.id ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'">{{ tab.icon }}</span>
              <div class="flex-1 min-w-0">
                <div class="truncate">{{ tab.label }}</div>
              </div>
              <div
                v-if="activeTab === tab.id"
                class="w-1.5 h-1.5 rounded-full bg-primary"
              />
            </button>
          </nav>

          <!-- Right Content Panel -->
          <div class="flex-1 min-w-0 overflow-y-auto p-6 space-y-6 bg-surface">
            <!-- Tab 1: 路径与基础 (basic) -->
            <div v-show="activeTab === 'basic'" class="space-y-5">
              <div>
                <h3 class="text-sm font-bold text-text-1 mb-1">基础路径配置</h3>
                <p class="text-xs text-text-3">配置工作空间根目录以及本地输出目录</p>
              </div>

              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-4">
                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1.5">工作目录 (Root Path)</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.rootPath"
                      type="text"
                      class="flex-1 form-input min-w-0 text-xs font-mono"
                      placeholder="例如: D:\build"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors shrink-0 shadow-2xs"
                      @click="onChooseDir('rootPath')"
                    >
                      浏览...
                    </button>
                  </div>
                  <p class="mt-1 text-[11px] text-text-3">系统将自动扫描此目录及其子目录下的所有 Git 仓库项目。</p>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1.5">本地输出目录 (Local Output)</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.localOutputDir"
                      type="text"
                      class="flex-1 form-input min-w-0 text-xs font-mono"
                      placeholder="例如: D:\output"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors shrink-0 shadow-2xs"
                      @click="onChooseDir('localOutputDir')"
                    >
                      浏览...
                    </button>
                  </div>
                  <p class="mt-1 text-[11px] text-text-3">本地构建产物存档的目标路径。</p>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1.5">提测单目录 / 创建目录位置</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.orderDirPath"
                      type="text"
                      class="flex-1 form-input min-w-0 font-mono text-xs"
                      placeholder="例如: D:\yh\特殊订单\2026"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors shrink-0 shadow-2xs"
                      @click="onChooseDir('orderDirPath')"
                    >
                      浏览...
                    </button>
                  </div>
                  <p class="mt-1 text-[11px] text-text-3 leading-relaxed">
                    配置后在主界面输入订单号后可勾选「自动创建提测目录」，系统将自动创建订单同名文件夹并生成 Excel 提测单。
                  </p>
                </div>
              </div>
            </div>

            <!-- Tab 2: 打包构建 (build) -->
            <div v-show="activeTab === 'build'" class="space-y-5">
              <div>
                <h3 class="text-sm font-bold text-text-1 mb-1">打包构建设置</h3>
                <p class="text-xs text-text-3">配置默认打包命令与项目独立命令，支持 npm / pnpm / yarn / 脚本智能识别</p>
              </div>

              <!-- 全局默认打包命令 -->
              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-3">
                <div class="flex items-center justify-between">
                  <label class="block text-xs font-semibold text-text-2">默认全局打包命令 / 脚本</label>
                  <div class="flex items-center gap-1">
                    <span class="text-[11px] text-text-3 mr-1">快捷填入:</span>
                    <button
                      type="button"
                      class="px-2 py-0.5 text-[11px] rounded bg-white border border-border text-text-2 hover:text-primary hover:border-primary/40 transition-colors"
                      @click="store.config.buildCommand = 'deploy.sh'"
                    >
                      deploy.sh
                    </button>
                    <button
                      type="button"
                      class="px-2 py-0.5 text-[11px] rounded bg-white border border-border text-text-2 hover:text-primary hover:border-primary/40 transition-colors"
                      @click="store.config.buildCommand = 'npm run build'"
                    >
                      npm run build
                    </button>
                    <button
                      type="button"
                      class="px-2 py-0.5 text-[11px] rounded bg-white border border-border text-text-2 hover:text-primary hover:border-primary/40 transition-colors"
                      @click="store.config.buildCommand = 'npm run build:prod'"
                    >
                      npm run build:prod
                    </button>
                  </div>
                </div>
                <input
                  v-model="store.config.buildCommand"
                  type="text"
                  class="w-full form-input font-mono text-xs"
                  placeholder="deploy.sh 或 npm run build"
                >
                <p class="text-[11px] text-text-3 leading-relaxed">
                  💡 <strong>智能免配支持</strong>：若项目设置为 <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">deploy.sh</code> 但项目目录中未找到该脚本，系统会自动读取 <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">package.json</code> 自动调用内置打包命令（如 <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">npm run build</code>）。
                </p>
              </div>

              <!-- 各项目独立打包命令 -->
              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-3">
                <div class="flex items-center justify-between">
                  <div>
                    <h4 class="text-xs font-semibold text-text-1">各项目独立打包命令</h4>
                    <p class="text-[11px] text-text-3">针对需要特殊打包指令的项目进行覆盖配置</p>
                  </div>
                  <button
                    type="button"
                    class="px-2.5 py-1 text-xs text-primary bg-primary/10 hover:bg-primary/20 rounded-lg font-medium flex items-center gap-1 transition-colors"
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
                  class="flex flex-wrap items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-primary/30"
                >
                  <input
                    v-model="newBuildCmdProjectName"
                    type="text"
                    class="w-36 px-2.5 py-1.5 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                    placeholder="项目名称"
                    @keyup.enter="confirmAddBuildCmdProject"
                  >
                  <input
                    v-model="newBuildCmdValue"
                    type="text"
                    class="flex-1 min-w-[8rem] px-2.5 py-1.5 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                    placeholder="打包命令 (如 npm run build:prod)"
                    @keyup.enter="confirmAddBuildCmdProject"
                  >
                  <button
                    type="button"
                    class="px-3 py-1.5 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity"
                    @click="confirmAddBuildCmdProject"
                  >
                    添加
                  </button>
                  <button
                    type="button"
                    class="px-2.5 py-1.5 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors"
                    @click="showAddBuildCmdModal = false"
                  >
                    取消
                  </button>
                </div>

                <!-- List -->
                <div class="space-y-2 max-h-56 overflow-y-auto pr-1">
                  <div
                    v-for="projName in allConfiguredBuildCommandProjects"
                    :key="projName"
                    class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                  >
                    <span class="text-xs font-semibold text-text-1 w-36 sm:w-44 truncate shrink-0" :title="projName">
                      {{ projName }}
                    </span>
                    <input
                      v-if="store.config.buildCommands"
                      v-model="store.config.buildCommands[projName]"
                      type="text"
                      class="flex-1 min-w-0 px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-slate-50/50 text-text-2 focus:bg-white focus:border-primary/50 focus:ring-1 focus:ring-primary/20 outline-none transition-colors"
                      :placeholder="store.config.buildCommand || 'deploy.sh'"
                    >
                    <button
                      type="button"
                      class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors shrink-0"
                      title="删除此项目打包命令配置"
                      @click="removeProjectBuildCommand(projName)"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                  <div v-if="allConfiguredBuildCommandProjects.length === 0" class="text-center py-4 text-xs text-text-3">
                    未配置独立打包命令，所有项目将默认使用全局命令
                  </div>
                </div>
              </div>

              <!-- 打包产物目录配置 -->
              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-3">
                <div class="flex items-center justify-between">
                  <div>
                    <h4 class="text-xs font-semibold text-text-1">打包产物获取目录</h4>
                    <p class="text-[11px] text-text-3">多分支与多产物目录匹配（支持逗号分隔多个候选）</p>
                  </div>
                  <button
                    type="button"
                    class="px-2.5 py-1 text-xs text-primary bg-primary/10 hover:bg-primary/20 rounded-lg font-medium flex items-center gap-1 transition-colors"
                    @click="showAddArtifactPathModal = !showAddArtifactPathModal"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    项目独立产物目录
                  </button>
                </div>

                <div>
                  <label class="block text-[11px] text-text-3 mb-1">默认全局产物目录候选</label>
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
                  class="flex flex-wrap items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-primary/30"
                >
                  <input
                    v-model="newArtifactProjectName"
                    type="text"
                    class="w-36 px-2.5 py-1.5 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                    placeholder="项目名称"
                    @keyup.enter="confirmAddArtifactProject"
                  >
                  <input
                    v-model="newArtifactPathValue"
                    type="text"
                    class="flex-1 min-w-[8rem] px-2.5 py-1.5 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                    placeholder="产物目录 (如 dist, release)"
                    @keyup.enter="confirmAddArtifactProject"
                  >
                  <button
                    type="button"
                    class="px-3 py-1.5 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity"
                    @click="confirmAddArtifactProject"
                  >
                    添加
                  </button>
                  <button
                    type="button"
                    class="px-2.5 py-1.5 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors"
                    @click="showAddArtifactPathModal = false"
                  >
                    取消
                  </button>
                </div>

                <!-- Artifact project list -->
                <div v-if="allConfiguredArtifactPathProjects.length > 0" class="space-y-2 max-h-40 overflow-y-auto pr-1 pt-1">
                  <div
                    v-for="projName in allConfiguredArtifactPathProjects"
                    :key="projName"
                    class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                  >
                    <span class="text-xs font-semibold text-text-1 w-36 sm:w-44 truncate shrink-0" :title="projName">
                      {{ projName }}
                    </span>
                    <input
                      v-if="store.config.projectArtifactPaths"
                      v-model="store.config.projectArtifactPaths[projName]"
                      type="text"
                      class="flex-1 min-w-0 px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-slate-50/50 text-text-2 focus:bg-white focus:border-primary/50 focus:ring-1 focus:ring-primary/20 outline-none transition-colors"
                      placeholder="留空继承全局默认"
                    >
                    <button
                      type="button"
                      class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors shrink-0"
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

            <!-- Tab 3: 发布与上传 (publish) -->
            <div v-show="activeTab === 'publish'" class="space-y-5">
              <div>
                <h3 class="text-sm font-bold text-text-1 mb-1">发布与上传配置</h3>
                <p class="text-xs text-text-3">管理 SVN 根仓库、项目专属 SVN 仓库以及服务器远程部署目录</p>
              </div>

              <!-- SVN 仓库设置 -->
              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-blue-500" />
                    <h4 class="text-xs font-semibold text-text-1">SVN 仓库配置</h4>
                  </div>
                  <button
                    type="button"
                    class="px-2.5 py-1 text-xs text-primary bg-primary/10 hover:bg-primary/20 rounded-lg font-medium flex items-center gap-1 transition-colors"
                    @click="showAddSvnRootModal = !showAddSvnRootModal"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    项目独立 SVN 仓库
                  </button>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1.5">默认全局 SVN 根 URL</label>
                  <input
                    v-model="store.config.svnRootUrl"
                    type="text"
                    class="w-full form-input font-mono text-xs"
                    placeholder="https://10.1.1.120/svn/智慧病房特殊订单"
                  >
                </div>

                <!-- 常用 SVN 目录源列表 (支持多源切换) -->
                <div class="pt-2 border-t border-border/60 space-y-2.5">
                  <div class="flex items-center justify-between">
                    <div>
                      <label class="block text-xs font-semibold text-text-2">常用 SVN 目录源列表 (多源配置)</label>
                      <p class="text-[11px] text-text-3">配置多个常用的 SVN 订单或版本目录位置，在订单部署时可快捷切换</p>
                    </div>
                    <button
                      type="button"
                      class="px-2.5 py-1 text-xs text-primary bg-primary/10 hover:bg-primary/20 rounded-lg font-medium flex items-center gap-1 transition-colors"
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
                    class="flex flex-wrap items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-primary/30"
                  >
                    <input
                      v-model="newSvnLocName"
                      type="text"
                      class="w-36 px-2.5 py-1.5 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                      placeholder="源名称 (如 特殊订单)"
                      @keyup.enter="confirmAddSvnLocation"
                    >
                    <input
                      v-model="newSvnLocUrl"
                      type="text"
                      class="flex-1 min-w-[10rem] px-2.5 py-1.5 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                      placeholder="https://10.1.1.120/svn/..."
                      @keyup.enter="confirmAddSvnLocation"
                    >
                    <button
                      type="button"
                      class="px-3 py-1.5 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity cursor-pointer"
                      @click="confirmAddSvnLocation"
                    >
                      添加
                    </button>
                    <button
                      type="button"
                      class="px-2.5 py-1.5 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors cursor-pointer"
                      @click="showAddSvnLocModal = false"
                    >
                      取消
                    </button>
                  </div>

                  <!-- SVN Locations List -->
                  <div class="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                    <div
                      v-for="(loc, idx) in configuredSvnLocations"
                      :key="loc.id || idx"
                      class="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                    >
                      <input
                        v-model="loc.name"
                        type="text"
                        class="w-32 px-2 py-0.5 text-xs font-semibold border border-transparent hover:border-border focus:border-primary rounded bg-transparent outline-none"
                        placeholder="源名称"
                      >
                      <input
                        v-model="loc.url"
                        type="text"
                        class="flex-1 min-w-0 px-2 py-0.5 text-xs font-mono border border-transparent hover:border-border focus:border-primary rounded bg-slate-50/50 outline-none"
                        placeholder="SVN URL"
                      >
                      <button
                        type="button"
                        class="px-2 py-0.5 text-[11px] rounded transition-colors"
                        :class="store.config.svnRootUrl === loc.url ? 'bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200' : 'bg-slate-100 text-slate-600 hover:bg-blue-50 hover:text-blue-600'"
                        :title="store.config.svnRootUrl === loc.url ? '当前默认根目录' : '设为默认根目录'"
                        @click="setDefaultSvnLocation(loc)"
                      >
                        {{ store.config.svnRootUrl === loc.url ? '默认' : '设为默认' }}
                      </button>
                      <button
                        type="button"
                        class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors shrink-0"
                        title="删除此目录源"
                        @click="removeSvnLocation(idx)"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    <div v-if="configuredSvnLocations.length === 0" class="text-center py-2 text-xs text-text-3">
                      暂无自定义目录源，默认使用全局 SVN 根 URL
                    </div>
                  </div>
                </div>

                <!-- SVN 凭据 -->
                <div class="grid grid-cols-2 gap-3 pt-2 border-t border-border/60">
                  <div>
                    <label class="block text-xs text-text-3 mb-1">SVN 账号</label>
                    <input
                      v-model="store.config.form.svnUsername"
                      type="text"
                      class="w-full form-input text-xs"
                      placeholder="SVN 用户名"
                    >
                  </div>
                  <div>
                    <label class="block text-xs text-text-3 mb-1">SVN 密码</label>
                    <input
                      v-model="store.config.form.svnPassword"
                      type="password"
                      class="w-full form-input text-xs"
                      placeholder="SVN 密码"
                    >
                  </div>
                </div>

                <!-- 各项目独立 SVN 仓库列表 -->
                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1.5">各项目独立 SVN 仓库列表</label>

                  <!-- Inline Add Form -->
                  <div
                    v-if="showAddSvnRootModal"
                    class="flex flex-wrap items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-primary/30 mb-2"
                  >
                    <input
                      v-model="newSvnRootProjectName"
                      type="text"
                      class="w-36 px-2.5 py-1.5 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                      placeholder="项目名称"
                      @keyup.enter="confirmAddSvnRootProject"
                    >
                    <input
                      v-model="newSvnRootValue"
                      type="text"
                      class="flex-1 min-w-[10rem] px-2.5 py-1.5 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                      placeholder="https://10.1.1.120/svn/项目仓库"
                      @keyup.enter="confirmAddSvnRootProject"
                    >
                    <button
                      type="button"
                      class="px-3 py-1.5 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity"
                      @click="confirmAddSvnRootProject"
                    >
                      添加
                    </button>
                    <button
                      type="button"
                      class="px-2.5 py-1.5 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors"
                      @click="showAddSvnRootModal = false"
                    >
                      取消
                    </button>
                  </div>

                  <div class="space-y-2 max-h-40 overflow-y-auto pr-1">
                    <div
                      v-for="projName in allConfiguredSvnRootProjects"
                      :key="projName"
                      class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                    >
                      <span class="text-xs font-semibold text-text-1 w-36 sm:w-44 truncate shrink-0" :title="projName">
                        {{ projName }}
                      </span>
                      <input
                        v-if="store.config.projectSvnRoots"
                        v-model="store.config.projectSvnRoots[projName]"
                        type="text"
                        class="flex-1 min-w-0 px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-slate-50/50 text-text-2 focus:bg-white focus:border-primary/50 focus:ring-1 focus:ring-primary/20 outline-none transition-colors"
                        placeholder="留空继承全局默认 SVN 根 URL"
                      >
                      <button
                        type="button"
                        class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors shrink-0"
                        title="删除此项目独立配置"
                        @click="removeProjectSvnRoot(projName)"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    <div v-if="allConfiguredSvnRootProjects.length === 0" class="text-center py-3 text-xs text-text-3">
                      未配置项目独立 SVN 仓库，所有项目统一上传至默认 SVN 根 URL
                    </div>
                  </div>
                </div>
              </div>

              <!-- 服务器上传路径配置 -->
              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-500" />
                    <div>
                      <h4 class="text-xs font-semibold text-text-1">远程服务器上传路径</h4>
                      <p class="text-[11px] text-text-3">配置各项目打包后上传到远程 Linux 服务器的部署目录</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    class="px-2.5 py-1 text-xs text-primary bg-primary/10 hover:bg-primary/20 rounded-lg font-medium flex items-center gap-1 transition-colors"
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
                  class="flex items-center gap-2 bg-blue-50/80 p-3 rounded-lg border border-primary/30 mb-2"
                >
                  <input
                    v-model="newProjectName"
                    type="text"
                    class="w-40 px-2.5 py-1.5 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                    placeholder="项目名称"
                    @keyup.enter="confirmAddProject"
                  >
                  <input
                    v-model="newProjectPath"
                    type="text"
                    class="flex-1 px-2.5 py-1.5 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                    placeholder="服务器路径 (如 /home/data/web)"
                    @keyup.enter="confirmAddProject"
                  >
                  <button
                    type="button"
                    class="px-3 py-1.5 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity"
                    @click="confirmAddProject"
                  >
                    添加
                  </button>
                  <button
                    type="button"
                    class="px-2.5 py-1.5 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors"
                    @click="showAddProjectModal = false"
                  >
                    取消
                  </button>
                </div>

                <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
                  <div
                    v-for="projName in allConfiguredProjectNames"
                    :key="projName"
                    class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                  >
                    <span class="text-xs font-semibold text-text-1 w-36 sm:w-44 truncate shrink-0" :title="projName">
                      {{ projName }}
                    </span>
                    <input
                      v-model="store.config.serverUploadPaths[projName]"
                      type="text"
                      class="flex-1 px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-slate-50/50 text-text-2 focus:bg-white focus:border-primary/50 focus:ring-1 focus:ring-primary/20 outline-none transition-colors"
                      placeholder="/home/data/web"
                    >
                    <button
                      type="button"
                      class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors shrink-0"
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

            <!-- Tab 4: 工具环境 (env) -->
            <div v-show="activeTab === 'env'" class="space-y-5">
              <div>
                <h3 class="text-sm font-bold text-text-1 mb-1">运行工具与环境变量</h3>
                <p class="text-xs text-text-3">系统依赖的 Git, Bash, SVN, Node 与 npm 可执行文件路径</p>
              </div>

              <div class="bg-slate-50/70 border border-border/70 rounded-xl p-4 space-y-3.5">
                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1">Git 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.git"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="留空自动检测系统环境 (如 git.exe)"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors whitespace-nowrap"
                      @click="onChooseExe('git')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1">Bash 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.bash"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\Git\bin\bash.exe"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors whitespace-nowrap"
                      @click="onChooseExe('bash')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1">SVN 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.svn"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\TortoiseSVN\bin\svn.exe"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors whitespace-nowrap"
                      @click="onChooseExe('svn')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1">Node 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.node"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\nodejs\node.exe"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors whitespace-nowrap"
                      @click="onChooseExe('node')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-semibold text-text-2 mb-1">npm 路径</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.tools.npm"
                      type="text"
                      class="flex-1 form-input text-xs font-mono"
                      placeholder="例如 C:\Program Files\nodejs\npm.cmd"
                    >
                    <button
                      type="button"
                      class="px-3.5 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors whitespace-nowrap"
                      @click="onChooseExe('npm')"
                    >
                      浏览...
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tab 5: 个性偏好 (preference) -->
            <div v-show="activeTab === 'preference'" class="space-y-5">
              <div>
                <h3 class="text-sm font-bold text-text-1 mb-1">个性化偏好</h3>
                <p class="text-xs text-text-3">设置构建桌宠进度提示与界面交互行为</p>
              </div>

              <div class="bg-slate-50/70 border border-border/80 rounded-xl p-4 space-y-4">
                <div class="flex items-center justify-between pb-3 border-b border-border/60">
                  <div>
                    <div class="text-xs font-semibold text-text-1">启用打包桌宠进度提示</div>
                    <div class="text-[11px] text-text-3 mt-0.5">在点击打包构建时，桌宠将在桌面实时同步展示当前打包阶段与进度气泡</div>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      v-model="deskPetEnabled"
                      type="checkbox"
                      class="sr-only peer"
                    >
                    <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary" />
                  </label>
                </div>

                <fieldset class="space-y-2.5" :disabled="!deskPetEnabled">
                  <legend class="text-xs font-semibold text-text-1">桌宠外观形象</legend>
                  <div class="grid grid-cols-2 gap-3">
                    <label
                      class="cursor-pointer rounded-xl border p-3 transition-all relative overflow-hidden"
                      :class="deskPetStyle === 'pixel' ? 'border-primary bg-primary-light/50 ring-1 ring-primary/30' : 'border-border bg-white hover:bg-slate-50'"
                    >
                      <input
                        v-model="deskPetStyle"
                        value="pixel"
                        type="radio"
                        class="sr-only"
                      >
                      <div class="flex items-center gap-3">
                        <span class="text-2xl leading-none" aria-hidden="true">🕺</span>
                        <div>
                          <span class="block text-xs font-bold text-text-1">像素助手</span>
                          <span class="block text-[11px] text-text-3 mt-0.5">经典生动动效与跳舞姿态</span>
                        </div>
                      </div>
                      <div v-if="deskPetStyle === 'pixel'" class="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary" />
                    </label>

                    <label
                      class="cursor-pointer rounded-xl border p-3 transition-all relative overflow-hidden"
                      :class="deskPetStyle === 'blob' ? 'border-primary bg-primary-light/50 ring-1 ring-primary/30' : 'border-border bg-white hover:bg-slate-50'"
                    >
                      <input
                        v-model="deskPetStyle"
                        value="blob"
                        type="radio"
                        class="sr-only"
                      >
                      <div class="flex items-center gap-3">
                        <span class="inline-flex h-6 w-6 items-center justify-center rounded-[45%] bg-slate-950 text-[9px] tracking-[-2px] text-white font-bold" aria-hidden="true">••</span>
                        <div>
                          <span class="block text-xs font-bold text-text-1">黑团子</span>
                          <span class="block text-[11px] text-text-3 mt-0.5">极简安静悬浮陪伴</span>
                        </div>
                      </div>
                      <div v-if="deskPetStyle === 'blob'" class="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary" />
                    </label>
                  </div>
                </fieldset>
              </div>
            </div>
          </div>
        </div>

        <!-- Sticky Footer -->
        <div class="flex items-center justify-between px-6 py-3.5 border-t border-border-light bg-surface shrink-0">
          <div class="text-[11px] text-text-3">
            💡 修改后点击「保存」将同步应用至本地配置与当前运行环境
          </div>
          <div class="flex items-center gap-2.5">
            <button
              class="px-4 py-2 text-xs border border-border rounded-lg bg-white text-text-2 hover:bg-slate-100 transition-colors"
              @click="visible = false"
            >
              取消
            </button>
            <button
              class="px-5 py-2 text-xs font-medium bg-primary text-white rounded-lg hover:opacity-90 transition-opacity shadow-sm flex items-center gap-1.5"
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

type TabType = 'basic' | 'build' | 'publish' | 'env' | 'preference'
const activeTab = ref<TabType>('basic')

const tabs: { id: TabType; label: string; icon: string }[] = [
  { id: 'basic', label: '路径与基础', icon: '📁' },
  { id: 'build', label: '打包构建', icon: '🔨' },
  { id: 'publish', label: '发布与上传', icon: '🚀' },
  { id: 'env', label: '工具环境', icon: '🛠️' },
  { id: 'preference', label: '个性偏好', icon: '🎮' },
]

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
  if (!store.config.svnLocations) {
    store.config.svnLocations = []
  }
  return store.config.svnLocations
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
  if (!store.config?.buildCommands) return []
  return Object.keys(store.config.buildCommands)
})

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
