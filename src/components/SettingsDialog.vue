<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="visible = false"
      />
      <div
        class="relative bg-surface rounded-2xl shadow-2xl w-full max-w-4xl z-10 flex flex-col overflow-hidden"
        style="max-height: 88vh;"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-border-light">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-bold text-text-1">
              系统设置
            </h2>
            <span class="text-xs text-text-3 bg-border-light px-2 py-0.5 rounded-full font-medium">全局配置</span>
          </div>
          <button
            class="text-text-3 hover:text-text-2 transition-colors p-1 rounded-lg hover:bg-border-light"
            @click="visible = false"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Scrollable body -->
        <div
          v-if="store.config"
          class="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-5"
        >
          <!-- 路径配置 + 打包配置：左右并排 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
            <!-- 路径配置 -->
            <section class="min-w-0">
              <div class="flex items-center gap-2 mb-3">
                <div class="w-1 h-4 rounded-full bg-primary" />
                <span class="text-sm font-semibold text-text-1">路径配置</span>
              </div>
              <div class="space-y-3">
                <div>
                  <label class="block text-xs text-text-3 mb-1.5">工作目录</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.rootPath"
                      type="text"
                      class="flex-1 form-input min-w-0"
                      placeholder="选择工作目录"
                    >
                    <button
                      class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                      @click="onChooseDir('rootPath')"
                    >
                      浏览
                    </button>
                  </div>
                </div>
                <div>
                  <label class="block text-xs text-text-3 mb-1.5">SVN 根 URL</label>
                  <input
                    v-model="store.config.svnRootUrl"
                    type="text"
                    class="w-full form-input"
                    placeholder="SVN 根 URL"
                  >
                </div>
                <div>
                  <label class="block text-xs text-text-3 mb-1.5">本地输出目录</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.localOutputDir"
                      type="text"
                      class="flex-1 form-input min-w-0"
                    >
                    <button
                      class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                      @click="onChooseDir('localOutputDir')"
                    >
                      浏览
                    </button>
                  </div>
                </div>
                <div>
                  <label class="block text-xs text-text-3 mb-1.5">提测目录地址 / 创建目录位置</label>
                  <div class="flex gap-2">
                    <input
                      v-model="store.config.orderDirPath"
                      type="text"
                      class="flex-1 form-input min-w-0 font-mono text-xs"
                      placeholder="例如: D:\yh\特殊订单\2026"
                    >
                    <button
                      class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                      @click="onChooseDir('orderDirPath')"
                    >
                      浏览
                    </button>
                  </div>
                  <p class="mt-1 text-[11px] text-text-3 leading-relaxed">
                    配置后在订单号右侧可勾选「自动创建提测目录」，自动创建订单同名文件夹并生成 Excel 提测单。
                  </p>
                </div>
              </div>
            </section>

            <!-- 打包配置 -->
            <section class="min-w-0">
              <div class="flex items-center justify-between mb-3 gap-2">
                <div class="flex items-center gap-2 min-w-0">
                  <div class="w-1 h-4 rounded-full bg-primary shrink-0" />
                  <span class="text-sm font-semibold text-text-1">打包配置</span>
                </div>
                <button
                  type="button"
                  class="text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1 transition-colors shrink-0"
                  @click="showAddBuildCmdModal = !showAddBuildCmdModal"
                >
                  <svg
                    class="w-3.5 h-3.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 4v16m8-8H4"
                    />
                  </svg>
                  添加项目命令
                </button>
              </div>
              <div class="space-y-3">
                <div>
                  <label class="block text-xs text-text-3 mb-1.5">默认全局打包命令 / 脚本</label>
                  <input
                    v-model="store.config.buildCommand"
                    type="text"
                    class="w-full form-input font-mono text-xs"
                    placeholder="deploy.sh 或 ./deploy.sh 或 npm run build"
                  >
                  <p class="mt-1.5 text-[11px] text-text-3 leading-relaxed">
                    未单独配置的项目将默认使用此命令。默认执行 <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">deploy.sh</code>。
                  </p>
                </div>

                <!-- 各项目打包命令列表 -->
                <div>
                  <label class="block text-xs text-text-3 mb-1.5">各项目独立打包命令</label>
                  <div class="border border-border/80 rounded-xl bg-slate-50/60 p-3 space-y-2 max-h-52 overflow-y-auto">
                    <div
                      v-for="projName in allConfiguredBuildCommandProjects"
                      :key="projName"
                      class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                    >
                      <span
                        class="text-xs font-semibold text-text-1 w-28 sm:w-36 truncate shrink-0"
                        :title="projName"
                      >
                        {{ projName }}
                      </span>
                      <input
                        v-if="store.config && store.config.buildCommands"
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
                        <svg
                          class="w-3.5 h-3.5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>

                    <!-- Inline Add Build Command Form -->
                    <div
                      v-if="showAddBuildCmdModal"
                      class="flex flex-wrap items-center gap-2 bg-blue-50/60 p-2.5 rounded-lg border border-primary/30 mt-2"
                    >
                      <input
                        v-model="newBuildCmdProjectName"
                        type="text"
                        class="w-28 sm:w-32 px-2.5 py-1 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                        placeholder="项目名称"
                        @keyup.enter="confirmAddBuildCmdProject"
                      >
                      <input
                        v-model="newBuildCmdValue"
                        type="text"
                        class="flex-1 min-w-[6rem] px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                        placeholder="打包命令 (如 deploy.sh)"
                        @keyup.enter="confirmAddBuildCmdProject"
                      >
                      <button
                        type="button"
                        class="px-2.5 py-1 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity shrink-0"
                        @click="confirmAddBuildCmdProject"
                      >
                        添加
                      </button>
                      <button
                        type="button"
                        class="px-2 py-1 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors shrink-0"
                        @click="showAddBuildCmdModal = false"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </div>

                <!-- 打包产物获取目录 -->
                <div class="pt-2 border-t border-border/60">
                  <div class="flex items-center justify-between mb-1.5 gap-2">
                    <label class="block text-xs text-text-3 font-medium">默认全局打包产物目录（支持多个，用逗号分隔）</label>
                    <button
                      type="button"
                      class="text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1 transition-colors shrink-0"
                      @click="showAddArtifactPathModal = !showAddArtifactPathModal"
                    >
                      <svg
                        class="w-3.5 h-3.5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M12 4v16m8-8H4"
                        />
                      </svg>
                      项目独立产物目录
                    </button>
                  </div>
                  <input
                    v-model="globalArtifactPathsInput"
                    type="text"
                    class="w-full form-input font-mono text-xs"
                    placeholder="例如: dist, release, output, build, target, ."
                  >
                  <p class="mt-1.5 text-[11px] text-text-3 leading-relaxed">
                    💡 <strong>多分支与多产物路径匹配</strong>：针对不同 Git 分支打包产物位置不同的情况（如有的分支产物在 <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">dist</code>，有的在 <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">release</code> / <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">output</code> 或分支子目录），支持在此配置多个候选目录（用逗号分隔）。构建后系统将自动按配置目录及各分支子目录自动抓取最新的产物压缩包（<code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">.tar.gz</code> / <code class="px-1 py-0.5 rounded bg-slate-100 font-mono text-text-2">.zip</code>）。
                  </p>

                  <!-- 各项目独立产物目录列表 -->
                  <div
                    v-if="allConfiguredArtifactPathProjects.length > 0 || showAddArtifactPathModal"
                    class="mt-2.5 border border-border/80 rounded-xl bg-slate-50/60 p-3 space-y-2 max-h-40 overflow-y-auto"
                  >
                    <div
                      v-for="projName in allConfiguredArtifactPathProjects"
                      :key="projName"
                      class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
                    >
                      <span
                        class="text-xs font-semibold text-text-1 w-28 sm:w-36 truncate shrink-0"
                        :title="projName"
                      >
                        {{ projName }}
                      </span>
                      <input
                        v-if="store.config && store.config.projectArtifactPaths"
                        v-model="store.config.projectArtifactPaths[projName]"
                        type="text"
                        class="flex-1 min-w-0 px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-slate-50/50 text-text-2 focus:bg-white focus:border-primary/50 focus:ring-1 focus:ring-primary/20 outline-none transition-colors"
                        placeholder="留空继承全局默认；根目录填 ."
                      >
                      <button
                        type="button"
                        class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors shrink-0"
                        title="删除此项目配置"
                        @click="removeProjectArtifactPath(projName)"
                      >
                        <svg
                          class="w-3.5 h-3.5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>

                    <!-- Inline Add Form -->
                    <div
                      v-if="showAddArtifactPathModal"
                      class="flex flex-wrap items-center gap-2 bg-blue-50/60 p-2.5 rounded-lg border border-primary/30 mt-2"
                    >
                      <input
                        v-model="newArtifactProjectName"
                        type="text"
                        class="w-28 sm:w-32 px-2.5 py-1 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                        placeholder="项目名称"
                        @keyup.enter="confirmAddArtifactProject"
                      >
                      <input
                        v-model="newArtifactPathValue"
                        type="text"
                        class="flex-1 min-w-[6rem] px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                        placeholder="留空继承全局默认；根目录填 ."
                        @keyup.enter="confirmAddArtifactProject"
                      >
                      <button
                        type="button"
                        class="px-2.5 py-1 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity shrink-0"
                        @click="confirmAddArtifactProject"
                      >
                        添加
                      </button>
                      <button
                        type="button"
                        class="px-2 py-1 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors shrink-0"
                        @click="showAddArtifactPathModal = false"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <!-- 服务器上传路径 -->
          <section>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <div class="w-1 h-4 rounded-full bg-primary" />
                <span class="text-sm font-semibold text-text-1">服务器上传路径</span>
              </div>
              <button
                type="button"
                class="text-xs text-primary hover:text-primary-dark font-medium flex items-center gap-1 transition-colors"
                @click="showAddProjectModal = !showAddProjectModal"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                添加项目
              </button>
            </div>

            <p class="text-xs text-text-3 mb-2.5">
              配置各项目打包后上传到远程服务器的默认部署目录：
            </p>

            <div class="border border-border/80 rounded-xl bg-slate-50/60 p-3 space-y-2 max-h-60 overflow-y-auto">
              <div
                v-for="projName in allConfiguredProjectNames"
                :key="projName"
                class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-border/60 shadow-2xs hover:border-primary/40 transition-colors"
              >
                <span
                  class="text-xs font-semibold text-text-1 w-44 truncate shrink-0"
                  :title="projName"
                >
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
                  class="p-1 text-text-3 hover:text-danger hover:bg-danger/10 rounded transition-colors"
                  title="删除此项目配置"
                  @click="removeProjectUploadPath(projName)"
                >
                  <svg
                    class="w-3.5 h-3.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>

              <!-- Inline Add Form -->
              <div
                v-if="showAddProjectModal"
                class="flex items-center gap-2 bg-blue-50/60 p-2.5 rounded-lg border border-primary/30 mt-2"
              >
                <input
                  v-model="newProjectName"
                  type="text"
                  class="w-40 px-2.5 py-1 text-xs border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                  placeholder="项目名称"
                  @keyup.enter="confirmAddProject"
                >
                <input
                  v-model="newProjectPath"
                  type="text"
                  class="flex-1 px-2.5 py-1 text-xs font-mono border border-border rounded-md bg-white text-text-1 focus:border-primary/50 outline-none"
                  placeholder="服务器路径 (如 /home/data/web)"
                  @keyup.enter="confirmAddProject"
                >
                <button
                  type="button"
                  class="px-2.5 py-1 text-xs bg-primary text-white rounded-md hover:opacity-90 transition-opacity shrink-0"
                  @click="confirmAddProject"
                >
                  添加
                </button>
                <button
                  type="button"
                  class="px-2 py-1 text-xs border border-border bg-white text-text-3 rounded-md hover:bg-slate-100 transition-colors shrink-0"
                  @click="showAddProjectModal = false"
                >
                  取消
                </button>
              </div>
            </div>
          </section>

          <!-- 工具路径 -->
          <section>
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 rounded-full bg-primary" />
              <span class="text-sm font-semibold text-text-1">工具路径</span>
            </div>
            <div class="space-y-3">
              <div>
                <label class="block text-xs text-text-3 mb-1.5">Git 路径</label>
                <div class="flex gap-2">
                  <input
                    v-model="store.config.tools.git"
                    type="text"
                    class="flex-1 form-input"
                  >
                  <button
                    class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                    @click="onChooseExe('git')"
                  >
                    浏览
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-xs text-text-3 mb-1.5">Bash 路径</label>
                <div class="flex gap-2">
                  <input
                    v-model="store.config.tools.bash"
                    type="text"
                    class="flex-1 form-input"
                  >
                  <button
                    class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                    @click="onChooseExe('bash')"
                  >
                    浏览
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-xs text-text-3 mb-1.5">SVN 路径</label>
                <div class="flex gap-2">
                  <input
                    v-model="store.config.tools.svn"
                    type="text"
                    class="flex-1 form-input"
                  >
                  <button
                    class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                    @click="onChooseExe('svn')"
                  >
                    浏览
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-xs text-text-3 mb-1.5">Node 路径</label>
                <div class="flex gap-2">
                  <input
                    v-model="store.config.tools.node"
                    type="text"
                    class="flex-1 form-input"
                    placeholder="例如 C:\Program Files\nodejs\node.exe"
                  >
                  <button
                    class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                    @click="onChooseExe('node')"
                  >
                    浏览
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-xs text-text-3 mb-1.5">npm 路径</label>
                <div class="flex gap-2">
                  <input
                    v-model="store.config.tools.npm"
                    type="text"
                    class="flex-1 form-input"
                    placeholder="例如 C:\Program Files\nodejs\npm.cmd"
                  >
                  <button
                    class="px-3 py-2 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors whitespace-nowrap"
                    @click="onChooseExe('npm')"
                  >
                    浏览
                  </button>
                </div>
              </div>
            </div>
          </section>

          <!-- SVN 配置 -->
          <section>
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 rounded-full bg-primary" />
              <span class="text-sm font-semibold text-text-1">SVN 配置</span>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-text-3 mb-1.5">SVN 用户名</label>
                <input
                  v-model="store.config.form.svnUsername"
                  type="text"
                  class="w-full form-input"
                  placeholder="SVN 用户名"
                >
              </div>
              <div>
                <label class="block text-xs text-text-3 mb-1.5">SVN 密码</label>
                <input
                  v-model="store.config.form.svnPassword"
                  type="password"
                  class="w-full form-input"
                  placeholder="SVN 密码"
                >
              </div>
            </div>
          </section>

          <!-- 桌宠与悬浮助手 -->
          <section>
            <div class="flex items-center gap-2 mb-3">
              <div class="w-1 h-4 rounded-full bg-primary" />
              <span class="text-sm font-semibold text-text-1">桌宠助手 (悬浮进度)</span>
            </div>
            <div class="bg-slate-50/70 border border-border/80 rounded-xl p-4 space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-xs font-semibold text-text-1">启用打包桌宠进度提示</div>
                  <div class="text-[11px] text-text-3">在点击打包构建时，桌宠将在桌面实时同步展示当前打包阶段与进度气泡</div>
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
              <fieldset class="space-y-2" :disabled="!deskPetEnabled">
                <legend class="text-xs font-semibold text-text-1">桌宠外观</legend>
                <div class="grid grid-cols-2 gap-2">
                  <label
                    class="cursor-pointer rounded-lg border px-3 py-2.5 transition-colors"
                    :class="deskPetStyle === 'pixel' ? 'border-primary bg-primary-light' : 'border-border bg-white hover:bg-slate-50'"
                  >
                    <input
                      v-model="deskPetStyle"
                      value="pixel"
                      type="radio"
                      class="h-3.5 w-3.5 shrink-0 accent-primary"
                    >
                    <span class="flex items-center gap-2">
                      <span class="text-base leading-none" aria-hidden="true">🕺</span>
                      <span>
                        <span class="block text-xs font-semibold text-text-1">像素助手</span>
                        <span class="block text-[11px] text-text-3 mt-0.5">经典动效</span>
                      </span>
                    </span>
                  </label>
                  <label
                    class="cursor-pointer rounded-lg border px-3 py-2.5 transition-colors"
                    :class="deskPetStyle === 'blob' ? 'border-primary bg-primary-light' : 'border-border bg-white hover:bg-slate-50'"
                  >
                    <input
                      v-model="deskPetStyle"
                      value="blob"
                      type="radio"
                      class="h-3.5 w-3.5 shrink-0 accent-primary"
                    >
                    <span class="flex items-center gap-2">
                      <span class="inline-flex h-4 w-4 items-center justify-center rounded-[45%] bg-slate-950 text-[8px] tracking-[-2px] text-white" aria-hidden="true">••</span>
                      <span>
                        <span class="block text-xs font-semibold text-text-1">黑团子</span>
                        <span class="block text-[11px] text-text-3 mt-0.5">安静陪伴</span>
                      </span>
                    </span>
                  </label>
                </div>
              </fieldset>
            </div>
          </section>
        </div>

        <!-- Sticky footer -->
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-border-light bg-surface rounded-b-2xl">
          <button
            class="px-5 py-2.5 text-sm border border-border rounded-lg bg-white text-text-2 hover:bg-border-light transition-colors"
            @click="visible = false"
          >
            取消
          </button>
          <button
            class="px-5 py-2.5 text-sm bg-primary text-white rounded-lg hover:opacity-90 transition-opacity shadow-sm"
            @click="onSave"
          >
            保存
          </button>
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

const showAddProjectModal = ref(false)
const newProjectName = ref('')
const newProjectPath = ref('/home/data/web')

const showAddBuildCmdModal = ref(false)
const newBuildCmdProjectName = ref('')
const newBuildCmdValue = ref('deploy.sh')

const showAddArtifactPathModal = ref(false)
const newArtifactProjectName = ref('')
const newArtifactPathValue = ref('dist')

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
