<template>
  <div class="flex-1 min-h-0 bg-slate-50 p-6 flex flex-col overflow-hidden">
    <div class="max-w-6xl mx-auto w-full flex-1 min-h-0 flex flex-col overflow-hidden">
      <!-- Main Grid Section -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">
        <!-- Left Panel: Configuration (5 cols) -->
        <div class="lg:col-span-5 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs flex flex-col justify-between overflow-y-auto space-y-4">
          <div class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-blue-600" />
                <span>提取配置与参数组装</span>
              </h3>
              <span class="text-xs text-slate-400 font-mono">Step 1-4</span>
            </div>

            <!-- Step 1: Base URL -->
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-slate-700">
                1. 目标服务器 Base URL
              </label>
              <div class="flex gap-2">
                <input
                  v-model="baseUrl"
                  type="text"
                  class="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 focus:border-blue-500 focus:bg-white rounded-xl text-xs text-slate-800 placeholder-slate-400 outline-none transition-all font-mono"
                  placeholder="http://192.168.xxx.xxx"
                >
                <button
                  type="button"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-2xs transition-all flex items-center gap-1 shrink-0 cursor-pointer disabled:opacity-50"
                  :disabled="connecting || !baseUrl.trim()"
                  @click="onConnect"
                >
                  <svg v-if="connecting" class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>{{ connecting ? '连接中...' : '连接' }}</span>
                </button>
              </div>
            </div>

            <!-- Step 2: Org Select -->
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-slate-700">
                2. 选择机构 (Org)
              </label>
              <select
                v-model="selectedOrgId"
                class="w-full px-3 py-2.5 bg-white border border-slate-300 hover:border-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 rounded-xl text-[13px] font-medium text-slate-800 outline-none transition-all disabled:opacity-50 cursor-pointer shadow-xs leading-normal"
                :disabled="orgs.length === 0"
                @change="onOrgChange"
              >
                <option value="" disabled class="py-2 text-[13px]">
                  {{ orgs.length > 0 ? '-- 请选择机构 --' : '尚未获取机构列表' }}
                </option>
                <option v-for="org in orgs" :key="org.orgId" :value="org.orgId" class="py-2 text-[13px]">
                  {{ org.orgName || org.orgId }} (ID: {{ org.orgId }})
                </option>
              </select>
            </div>

            <!-- Step 3: Dept Select (Multi-level cascading & search) -->
            <div class="space-y-2 bg-slate-50/70 border border-slate-200/80 rounded-xl p-3">
              <div class="flex items-center justify-between">
                <label class="block text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <span>3. 选择护理单元 (Department)</span>
                  <span v-if="cascadeLevels.length > 1" class="px-1.5 py-0.2 bg-blue-100 text-blue-700 text-[10px] rounded font-bold">
                    {{ cascadeLevels.length }} 级架构
                  </span>
                </label>
                <div v-if="flatDepts.length > 1" class="flex items-center gap-1 text-[11px]">
                  <button
                    type="button"
                    class="px-2 py-0.5 rounded transition-all cursor-pointer font-medium"
                    :class="deptSelectMode === 'cascade' ? 'bg-white text-blue-600 shadow-2xs font-bold border border-slate-200' : 'text-slate-500 hover:text-slate-800'"
                    @click="deptSelectMode = 'cascade'"
                  >
                    分级选择
                  </button>
                  <button
                    type="button"
                    class="px-2 py-0.5 rounded transition-all cursor-pointer font-medium"
                    :class="deptSelectMode === 'flat' ? 'bg-white text-blue-600 shadow-2xs font-bold border border-slate-200' : 'text-slate-500 hover:text-slate-800'"
                    @click="deptSelectMode = 'flat'"
                  >
                    全路径/搜索
                  </button>
                </div>
              </div>

              <!-- Mode 1: Cascading selects for each level -->
              <div v-if="deptSelectMode === 'cascade'" class="space-y-2">
                <div v-if="cascadeLevels.length === 0" class="text-xs text-slate-400 py-1.5">
                  {{ selectedOrgId ? '当前机构下无可用科室/护理单元' : '请先选择机构' }}
                </div>
                <div
                  v-for="(level, idx) in cascadeLevels"
                  :key="level.levelIndex"
                  class="space-y-1"
                >
                  <div class="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span class="flex items-center gap-1">
                      <span class="w-1.5 h-1.5 rounded-full" :class="idx === cascadeLevels.length - 1 ? 'bg-blue-600' : 'bg-slate-400'" />
                      <span>{{ level.label }}</span>
                    </span>
                    <span v-if="idx === cascadeLevels.length - 1" class="text-[10px] text-blue-600 font-bold">最终匹配单元</span>
                  </div>
                  <select
                    :value="cascadeDeptIds[idx]"
                    class="w-full px-3 py-2.5 bg-white border border-slate-300 hover:border-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 rounded-xl text-[13px] font-medium text-slate-800 outline-none transition-all cursor-pointer shadow-xs leading-normal"
                    @change="(e) => onCascadeChange(idx, (e.target as HTMLSelectElement).value)"
                  >
                    <option v-for="dept in level.options" :key="dept.deptId" :value="dept.deptId" class="py-2 text-[13px]">
                      {{ dept.deptName || dept.deptId }} (Key: {{ dept.deptKey || dept.deptId }})
                    </option>
                  </select>
                </div>
              </div>

              <!-- Mode 2: Flat search & full path select -->
              <div v-else class="space-y-2">
                <input
                  v-model="deptSearchQuery"
                  type="text"
                  placeholder="输入科室/病区名称或 Key 快速搜索..."
                  class="w-full px-3 py-2 bg-white border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 rounded-xl text-xs outline-none transition-all shadow-2xs"
                >
                <select
                  :value="selectedDeptId"
                  class="w-full px-3 py-2.5 bg-white border border-slate-300 hover:border-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 rounded-xl text-[13px] font-medium text-slate-800 outline-none transition-all cursor-pointer shadow-xs leading-normal"
                  @change="(e) => onFlatDeptChange((e.target as HTMLSelectElement).value)"
                >
                  <option value="" disabled class="py-2 text-[13px]">-- 请选择护理单元 --</option>
                  <option
                    v-for="dept in filteredFlatDepts"
                    :key="dept.deptId"
                    :value="dept.deptId"
                    class="py-2 text-[13px]"
                  >
                    {{ dept.fullPathName || dept.deptName }} (Key: {{ dept.deptKey || dept.deptId }})
                  </option>
                </select>
              </div>

              <!-- Selected dept breadcrumb footer -->
              <div v-if="selectedDeptInfo" class="pt-1.5 border-t border-slate-200/60 flex flex-col gap-1 text-[11px]">
                <div class="text-slate-600 flex items-center gap-1.5 flex-wrap">
                  <span class="text-slate-400 font-medium shrink-0">当前选中:</span>
                  <span class="font-bold text-blue-700 bg-blue-50/80 px-1.5 py-0.5 rounded border border-blue-100/80 font-mono">
                    {{ selectedDeptInfo.fullPathName || selectedDeptInfo.deptName }}
                  </span>
                  <span class="text-slate-400 text-[10px] font-mono">ID: {{ selectedDeptInfo.deptId }}</span>
                </div>
                <div v-if="selectedDeptInfo.children && selectedDeptInfo.children.length > 0" class="text-amber-600 bg-amber-50/80 px-2 py-1 rounded text-[10px] border border-amber-200/60 flex items-center gap-1">
                  <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>提示：当前所选部门包含 {{ selectedDeptInfo.children.length }} 个子级病区，若未匹配到设备请选择下级护理单元</span>
                </div>
              </div>
            </div>

            <!-- Mode Selector Tabs -->
            <div class="pt-1">
              <label class="block text-xs font-semibold text-slate-700 mb-1.5">
                4. 选择功能模式
              </label>
              <div class="grid grid-cols-2 gap-2 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
                <button
                  type="button"
                  class="py-1.5 rounded-lg transition-all cursor-pointer"
                  :class="activeMode === 'device' ? 'bg-white text-blue-600 shadow-2xs font-bold' : 'text-slate-500 hover:text-slate-700'"
                  @click="activeMode = 'device'"
                >
                  匹配终端设备
                </button>
                <button
                  type="button"
                  class="py-1.5 rounded-lg transition-all cursor-pointer"
                  :class="activeMode === 'generateData' ? 'bg-white text-blue-600 shadow-2xs font-bold' : 'text-slate-500 hover:text-slate-700'"
                  @click="activeMode = 'generateData'"
                >
                  创建数据库数据
                </button>
              </div>
            </div>

            <!-- Mode 1: Device Matching -->
            <div v-if="activeMode === 'device'" class="space-y-4">
              <div class="space-y-1.5">
                <label class="block text-xs font-semibold text-slate-700">
                  匹配终端设备 (wnBedHead/wnBedSide)
                </label>
                <select
                  v-model="selectedDeviceId"
                  class="w-full px-3 py-2.5 bg-white border border-slate-300 hover:border-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 rounded-xl text-[13px] font-medium text-slate-800 outline-none transition-all disabled:opacity-50 cursor-pointer shadow-xs leading-normal"
                  :disabled="devices.length === 0"
                >
                  <option value="" disabled class="py-2 text-[13px]">
                    {{ devices.length > 0 ? '-- 请选择终端设备 --' : '请先选择护理单元' }}
                  </option>
                  <option v-for="dev in devices" :key="dev.deviceId" :value="dev.deviceId" class="py-2 text-[13px]">
                    {{ dev.deviceName || dev.deviceId }} [床号: {{ dev.bedName || '未指定' }}]
                  </option>
                </select>
              </div>

              <div class="pt-2">
                <button
                  type="button"
                  class="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  :disabled="extracting || !selectedDeviceId"
                  @click="onStartExtract"
                >
                  <svg v-if="extracting" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>{{ extracting ? '数据提取与匹配中...' : '🚀 开始智能提取数据链路' }}</span>
                </button>
              </div>
            </div>

            <!-- Mode 2: Generate DB Mock Data -->
            <div v-else class="space-y-3 bg-slate-50/80 border border-slate-200/60 rounded-xl p-3.5">
              <div class="border-b border-slate-200 pb-2 flex items-center justify-between">
                <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                  </svg>
                  数据库账户及目标配置
                </span>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="px-2 py-0.5 bg-blue-50 hover:bg-blue-100 text-blue-600 border border-blue-200 rounded-md text-[11px] font-bold transition-all flex items-center gap-1 cursor-pointer disabled:opacity-50"
                    :disabled="testingDbConn || !dbHost.trim()"
                    @click="onTestDbConnection"
                  >
                    <svg v-if="testingDbConn" class="w-3 h-3 animate-spin text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>{{ testingDbConn ? '验证中...' : '测试数据库连接' }}</span>
                  </button>
                  <span class="text-[10px] text-slate-400 font-mono">YHDB</span>
                </div>
              </div>

              <!-- DB Host & Port -->
              <div class="grid grid-cols-3 gap-2">
                <div class="col-span-2 space-y-1">
                  <label class="block text-[11px] font-semibold text-slate-600">目标 Host</label>
                  <input
                    v-model="dbHost"
                    type="text"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono outline-none focus:border-blue-500"
                    placeholder="192.168.78.63"
                  >
                </div>
                <div class="space-y-1">
                  <label class="block text-[11px] font-semibold text-slate-600">端口</label>
                  <input
                    v-model="dbPort"
                    type="text"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono outline-none focus:border-blue-500"
                    placeholder="3306"
                  >
                </div>
              </div>

              <!-- DB User & Pwd -->
              <div class="grid grid-cols-2 gap-2">
                <div class="space-y-1">
                  <label class="block text-[11px] font-semibold text-slate-600">数据库账户</label>
                  <input
                    v-model="dbUser"
                    type="text"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono outline-none focus:border-blue-500"
                    placeholder="root"
                  >
                </div>
                <div class="space-y-1">
                  <label class="block text-[11px] font-semibold text-slate-600">数据库密码</label>
                  <input
                    v-model="dbPass"
                    type="password"
                    class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono outline-none focus:border-blue-500"
                    placeholder="密码"
                  >
                </div>
              </div>

              <!-- Task Options -->
              <div class="space-y-2 pt-1 border-t border-slate-200">
                <span class="block text-[11px] font-bold text-slate-700">造数选项配置</span>

                <!-- Option 1: Patient Data -->
                <div class="flex items-center justify-between bg-white border border-slate-200 rounded-lg p-2 text-xs">
                  <label class="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                    <input
                      v-model="createPatient"
                      type="checkbox"
                      class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    >
                    <span>1. 创建患者数据</span>
                  </label>
                  <div v-if="createPatient" class="flex items-center gap-1">
                    <span class="text-[11px] text-slate-500">数量:</span>
                    <input
                      v-model.number="patientCount"
                      type="number"
                      min="1"
                      max="45"
                      class="w-14 px-1.5 py-0.5 border border-slate-300 rounded text-center text-xs outline-none focus:border-blue-500 font-mono"
                    >
                    <span class="text-[11px] text-slate-500">条</span>
                  </div>
                </div>

                <!-- Option 2: Board Data -->
                <div class="flex items-center justify-between bg-white border border-slate-200 rounded-lg p-2 text-xs">
                  <label class="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                    <input
                      v-model="createBoard"
                      type="checkbox"
                      class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    >
                    <span>2. 创建看板数据 (bo_switch/td_device)</span>
                  </label>

                  <div v-if="createBoard" class="flex items-center gap-1.5 shrink-0">
                    <span class="text-[11px] text-slate-500">模式:</span>
                    <select
                      v-model.number="boardTouchMode"
                      class="px-1.5 py-0.5 border border-slate-300 rounded text-xs outline-none focus:border-blue-500 bg-slate-50 cursor-pointer font-semibold"
                    >
                      <option :value="0">0 非触屏</option>
                      <option :value="1">1 触屏</option>
                    </select>
                  </div>
                </div>

                <!-- Option 3: Fee Data -->
                <div class="bg-white border border-slate-200 rounded-lg p-2 text-xs space-y-1.5">
                  <div class="flex items-center justify-between">
                    <label class="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                      <input
                        v-model="createFee"
                        type="checkbox"
                        class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      >
                      <span>3. 创建费用相关数据</span>
                    </label>
                    <div v-if="createFee" class="flex items-center gap-1">
                      <span class="text-[11px] text-slate-500">数量:</span>
                      <input
                        v-model.number="feeCount"
                        type="number"
                        min="1"
                        max="100"
                        class="w-14 px-1.5 py-0.5 border border-slate-300 rounded text-center text-xs outline-none focus:border-blue-500 font-mono"
                      >
                      <span class="text-[11px] text-slate-500">条</span>
                    </div>
                  </div>
                  <div v-if="createFee" class="flex items-center gap-2 pt-1 border-t border-slate-100">
                    <span class="text-[11px] text-slate-500 shrink-0">指定患者ID:</span>
                    <input
                      v-model="feePatientId"
                      type="text"
                      placeholder="留空自动关联生成的患者"
                      class="w-full px-2 py-0.5 bg-slate-50 border border-slate-200 rounded text-xs outline-none focus:border-blue-500 font-mono"
                    >
                  </div>
                </div>

                <!-- Option 4: Examine Data -->
                <div class="bg-white border border-slate-200 rounded-lg p-2 text-xs space-y-1.5">
                  <div class="flex items-center justify-between">
                    <label class="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                      <input
                        v-model="createExamine"
                        type="checkbox"
                        class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      >
                      <span>4. 创建检查检验数据</span>
                    </label>
                    <div v-if="createExamine" class="flex items-center gap-1">
                      <span class="text-[11px] text-slate-500">数量:</span>
                      <input
                        v-model.number="examineCount"
                        type="number"
                        min="1"
                        max="100"
                        class="w-14 px-1.5 py-0.5 border border-slate-300 rounded text-center text-xs outline-none focus:border-blue-500 font-mono"
                      >
                      <span class="text-[11px] text-slate-500">条</span>
                    </div>
                  </div>
                  <div v-if="createExamine" class="flex items-center gap-2 pt-1 border-t border-slate-100">
                    <span class="text-[11px] text-slate-500 shrink-0">指定患者ID:</span>
                    <input
                      v-model="examinePatientId"
                      type="text"
                      placeholder="留空自动关联生成的患者"
                      class="w-full px-2 py-0.5 bg-slate-50 border border-slate-200 rounded text-xs outline-none focus:border-blue-500 font-mono"
                    >
                  </div>
                </div>

                <!-- Option 5: Simple Doctor Advice Data -->
                <div class="bg-white border border-slate-200 rounded-lg p-2 text-xs space-y-1.5">
                  <div class="flex items-center justify-between">
                    <label class="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                      <input
                        v-model="createAdvice"
                        type="checkbox"
                        class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      >
                      <span>5. 创建简版医嘱数据</span>
                    </label>
                    <div v-if="createAdvice" class="flex items-center gap-1">
                      <span class="text-[11px] text-slate-500">数量:</span>
                      <input
                        v-model.number="adviceCount"
                        type="number"
                        min="1"
                        max="100"
                        class="w-14 px-1.5 py-0.5 border border-slate-300 rounded text-center text-xs outline-none focus:border-blue-500 font-mono"
                      >
                      <span class="text-[11px] text-slate-500">条</span>
                    </div>
                  </div>
                  <div v-if="createAdvice" class="flex items-center gap-2 pt-1 border-t border-slate-100">
                    <span class="text-[11px] text-slate-500 shrink-0">指定患者ID:</span>
                    <input
                      v-model="advicePatientId"
                      type="text"
                      placeholder="留空自动关联生成的患者"
                      class="w-full px-2 py-0.5 bg-slate-50 border border-slate-200 rounded text-xs outline-none focus:border-blue-500 font-mono"
                    >
                  </div>
                </div>

                <!-- Option 6: Operation Data -->
                <div class="bg-white border border-slate-200 rounded-lg p-2 text-xs space-y-1.5">
                  <div class="flex items-center justify-between">
                    <label class="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                      <input
                        v-model="createOperation"
                        type="checkbox"
                        class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      >
                      <span>6. 创建手术部分数据</span>
                    </label>
                    <div v-if="createOperation" class="flex items-center gap-1">
                      <span class="text-[11px] text-slate-500">数量:</span>
                      <input
                        v-model.number="operationCount"
                        type="number"
                        min="1"
                        max="100"
                        class="w-14 px-1.5 py-0.5 border border-slate-300 rounded text-center text-xs outline-none focus:border-blue-500 font-mono"
                      >
                      <span class="text-[11px] text-slate-500">条</span>
                    </div>
                  </div>
                  <div v-if="createOperation" class="flex items-center gap-2 pt-1 border-t border-slate-100">
                    <span class="text-[11px] text-slate-500 shrink-0">指定患者ID:</span>
                    <input
                      v-model="operationPatientId"
                      type="text"
                      placeholder="留空自动关联生成的患者"
                      class="w-full px-2 py-0.5 bg-slate-50 border border-slate-200 rounded text-xs outline-none focus:border-blue-500 font-mono"
                    >
                  </div>
                </div>

                <!-- Option 7: Incremental & Ignore -->
                <div class="flex items-center justify-between bg-emerald-50/60 border border-emerald-200/80 rounded-lg p-2 text-xs">
                  <label class="flex items-center gap-2 cursor-pointer font-medium text-emerald-900">
                    <input
                      v-model="useIgnore"
                      type="checkbox"
                      class="rounded border-emerald-400 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                    >
                    <span>增量防护与冲突跳过 (INSERT IGNORE)</span>
                  </label>
                </div>
              </div>

              <!-- Dual Submit Action Buttons -->
              <div class="pt-1 space-y-2">
                <button
                  type="button"
                  class="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  :disabled="executingDb || !selectedOrgId || !selectedDeptId || (!createPatient && !createBoard && !createFee && !createExamine && !createAdvice && !createOperation)"
                  @click="onDirectExecuteDb"
                >
                  <svg v-if="executingDb" class="w-4 h-4 animate-spin text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>{{ executingDb ? '正在写入数据库中...' : '🚀 直接连接数据库并写入数据' }}</span>
                </button>

                <button
                  type="button"
                  class="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed border border-slate-200"
                  :disabled="!selectedOrgId || !selectedDeptId || (!createPatient && !createBoard && !createFee && !createExamine && !createAdvice && !createOperation)"
                  @click="onGenerateMockData"
                >
                  <svg class="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>📋 仅生成 SQL 脚本 (供手动复制)</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Description Footer -->
          <div class="bg-blue-50/60 border border-blue-100 rounded-xl p-3 text-xs text-slate-600 space-y-1">
            <div class="font-bold text-blue-900 flex items-center gap-1.5">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>内置连接引擎</span>
            </div>
            <p class="leading-relaxed text-[11px]">
              支持自动跨域代理连接，直连测试目标服务，提取设备、机构与患者信息。
            </p>
          </div>
        </div>

        <!-- Right Panel: Result Console (7 cols) -->
        <div class="lg:col-span-7 bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs flex flex-col min-h-0 overflow-hidden space-y-3">
          <div class="flex items-center justify-between border-b border-slate-100 pb-3 shrink-0">
            <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
              <span>提取结果与数据组装</span>
            </h3>

            <button
              v-if="formattedResult"
              type="button"
              class="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
              @click="copyResult"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
              </svg>
              <span>一键复制结果</span>
            </button>
          </div>

          <!-- Code Display Terminal with Auto Flex Height & Internal Scrollbar -->
          <div class="flex-1 min-h-0 bg-slate-900 border border-slate-800 rounded-xl p-4 font-mono text-xs text-emerald-400 leading-relaxed overflow-y-auto shadow-inner custom-result-scrollbar">
            <pre v-if="formattedResult" class="whitespace-pre-wrap font-mono">{{ formattedResult }}</pre>
            <div v-else-if="extracting" class="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
              <svg class="w-8 h-8 animate-spin text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>正在向目标服务器提取数据...</span>
            </div>
            <div v-else class="h-full flex flex-col items-center justify-center text-slate-500 space-y-2">
              <svg class="w-10 h-10 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>请在左侧配置目标 URL 并选择终端设备后点击「智能提取数据链路」</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { ipc } from '@/services/ipc'
import {
  fetchOrgs,
  fetchDepts,
  fetchDevices,
  extractLinkData,
  flattenDeptTree,
  type OrgItem,
  type DeptItem,
  type DeviceItem,
} from '@/services/mockQuery'
import { generateMockDataSQL } from '@/services/mockDataGenerator'

const store = useAppStore()

const baseUrl = ref('http://192.168.78.63')
const connecting = ref(false)
const extracting = ref(false)

const activeMode = ref<'device' | 'generateData'>('device')

// DB Connection Config
const dbHost = ref('192.168.78.63')
const dbPort = ref('3306')
const dbUser = ref('root')
const dbPass = ref('')
const testingDbConn = ref(false)
const executingDb = ref(false)

// Mock Data Options
const createPatient = ref(true)
const patientCount = ref(10)
const createBoard = ref(true)
const boardTouchMode = ref(0)

const createFee = ref(false)
const feeCount = ref(10)
const feePatientId = ref('')

const createExamine = ref(false)
const examineCount = ref(10)
const examinePatientId = ref('')

const createAdvice = ref(false)
const adviceCount = ref(10)
const advicePatientId = ref('')

const createOperation = ref(false)
const operationCount = ref(10)
const operationPatientId = ref('')

const useIgnore = ref(true)

// Sync dbHost automatically when baseUrl changes
watch(
  baseUrl,
  (newVal) => {
    try {
      const u = new URL(newVal.startsWith('http') ? newVal : `http://${newVal}`)
      if (u.hostname) {
        dbHost.value = u.hostname
      }
    } catch {
      // fallback if invalid URL format
      dbHost.value = newVal.replace(/https?:\/\//, '').split(':')[0].split('/')[0]
    }
  },
  { immediate: true },
)

const orgs = ref<OrgItem[]>([])
const deptTree = ref<DeptItem[]>([])
const flatDepts = computed(() => flattenDeptTree(deptTree.value))
const devices = ref<DeviceItem[]>([])

const selectedOrgId = ref('')
const selectedDeptId = ref('')
const selectedDeviceId = ref('')

// Cascader & Search state for multi-level departments
const cascadeDeptIds = ref<string[]>([])
const deptSearchQuery = ref('')
const deptSelectMode = ref<'cascade' | 'flat'>('cascade')

const formattedResult = ref('')

// Recursively find the path IDs from tree for a given deptId
function findPathIds(nodes: DeptItem[], targetId: string): string[] | null {
  for (const node of nodes) {
    if (node.deptId === targetId) {
      return [node.deptId]
    }
    if (node.children && node.children.length > 0) {
      const sub = findPathIds(node.children, targetId)
      if (sub) {
        return [node.deptId, ...sub]
      }
    }
  }
  return null
}

// Compute the cascading level selects
const cascadeLevels = computed(() => {
  const levels: {
    levelIndex: number
    label: string
    options: DeptItem[]
    selectedId: string
  }[] = []
  if (deptTree.value.length === 0) return levels

  let currentOptions = deptTree.value
  let levelIndex = 0

  while (currentOptions && currentOptions.length > 0) {
    const selId = cascadeDeptIds.value[levelIndex] || ''
    const currentLevel = levelIndex + 1
    const levelLabel =
      currentLevel === 1
        ? '一级 (楼栋/大科室)'
        : currentLevel === 2
          ? '二级 (楼层/科室)'
          : currentLevel === 3
            ? '三级 (护理单元/病区)'
            : `${currentLevel}级部门`

    levels.push({
      levelIndex,
      label: levelLabel,
      options: currentOptions,
      selectedId: selId,
    })

    const foundNode = currentOptions.find((item) => item.deptId === selId) || currentOptions[0]
    if (foundNode && foundNode.children && foundNode.children.length > 0) {
      currentOptions = foundNode.children
      levelIndex++
    } else {
      break
    }
  }

  return levels
})

// Current selected dept info node
const selectedDeptInfo = computed(() => {
  if (!selectedDeptId.value) return null
  return flatDepts.value.find((d) => d.deptId === selectedDeptId.value) || null
})

// Filtered flat departments for search
const filteredFlatDepts = computed(() => {
  if (!deptSearchQuery.value.trim()) return flatDepts.value
  const q = deptSearchQuery.value.trim().toLowerCase()
  return flatDepts.value.filter((d) => {
    return (
      (d.deptName && d.deptName.toLowerCase().includes(q)) ||
      (d.deptKey && d.deptKey.toLowerCase().includes(q)) ||
      (d.fullPathName && d.fullPathName.toLowerCase().includes(q)) ||
      (d.deptId && d.deptId.toLowerCase().includes(q))
    )
  })
})

function onCascadeChange(levelIndex: number, newDeptId: string) {
  const newIds = cascadeDeptIds.value.slice(0, levelIndex)
  newIds.push(newDeptId)

  // Traverse down and pick the first child at each subsequent level
  let currentNodes = deptTree.value
  for (let i = 0; i <= levelIndex; i++) {
    const targetId = newIds[i]
    const node = currentNodes.find((item) => item.deptId === targetId)
    if (node && node.children && node.children.length > 0) {
      currentNodes = node.children
    } else {
      currentNodes = []
    }
  }

  while (currentNodes.length > 0) {
    const first = currentNodes[0]
    newIds.push(first.deptId)
    currentNodes = first.children || []
  }

  cascadeDeptIds.value = newIds
  const finalDeptId = newIds[newIds.length - 1]
  if (finalDeptId !== selectedDeptId.value) {
    selectedDeptId.value = finalDeptId
    onDeptChange()
  }
}

function onFlatDeptChange(deptId: string) {
  if (!deptId) return
  selectedDeptId.value = deptId
  const path = findPathIds(deptTree.value, deptId)
  if (path) {
    cascadeDeptIds.value = path
  }
  onDeptChange()
}

async function onConnect() {
  if (!baseUrl.value.trim()) return
  connecting.value = true
  orgs.value = []
  deptTree.value = []
  devices.value = []
  selectedOrgId.value = ''
  selectedDeptId.value = ''
  selectedDeviceId.value = ''
  cascadeDeptIds.value = []
  formattedResult.value = ''

  try {
    const list = await fetchOrgs(baseUrl.value)
    orgs.value = list
    if (list.length > 0) {
      selectedOrgId.value = list[0].orgId
      await onOrgChange()
    }
    store.showToast(`成功获取 ${list.length} 个机构`, 'success')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`连接失败: ${msg}`, 'error')
  } finally {
    connecting.value = false
  }
}

async function onOrgChange() {
  if (!selectedOrgId.value) return
  deptTree.value = []
  devices.value = []
  selectedDeptId.value = ''
  selectedDeviceId.value = ''
  cascadeDeptIds.value = []

  try {
    const list = await fetchDepts(baseUrl.value, selectedOrgId.value)
    deptTree.value = list
    if (list.length > 0) {
      const defaultIds: string[] = []
      let curr = list
      while (curr && curr.length > 0) {
        const first = curr[0]
        defaultIds.push(first.deptId)
        curr = first.children || []
      }
      cascadeDeptIds.value = defaultIds
      selectedDeptId.value = defaultIds[defaultIds.length - 1]
      await onDeptChange()
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`获取护理单元失败: ${msg}`, 'error')
  }
}

async function onDeptChange() {
  if (!selectedDeptId.value) return
  devices.value = []
  selectedDeviceId.value = ''

  try {
    const list = await fetchDevices(baseUrl.value, selectedDeptId.value)
    devices.value = list
    if (list.length > 0) {
      selectedDeviceId.value = list[0].deviceId
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`获取终端设备失败: ${msg}`, 'error')
  }
}

async function onStartExtract() {
  if (!selectedDeviceId.value) return
  extracting.value = true
  formattedResult.value = ''

  try {
    const selectedDev = devices.value.find((d) => d.deviceId === selectedDeviceId.value)
    const result = await extractLinkData(
      baseUrl.value,
      selectedDeviceId.value,
      selectedDeptId.value,
      selectedDev?.bedName,
    )
    formattedResult.value = result.formattedText
    store.showToast('数据链路提取与患者匹配成功', 'success')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`提取数据失败: ${msg}`, 'error')
  } finally {
    extracting.value = false
  }
}

async function onTestDbConnection() {
  if (!dbHost.value.trim()) {
    store.showToast('请输入数据库 Host', 'error')
    return
  }
  if (!dbUser.value.trim()) {
    store.showToast('请输入数据库账户', 'error')
    return
  }
  if (!dbPass.value) {
    store.showToast('请输入数据库密码后再验证', 'error')
    return
  }
  testingDbConn.value = true

  try {
    const host = dbHost.value.trim()
    const port = dbPort.value || 3306
    const user = dbUser.value.trim()
    const res = await ipc.testDbConnection({
      host,
      port,
      user,
      password: dbPass.value,
      database: 'YHDB',
    })
    if (res.success) {
      store.showToast(res.message || `数据库 [${host}:${port}/YHDB] 认证成功！`, 'success')
      formattedResult.value = `[${new Date().toLocaleTimeString()}] ✅ 数据库连接成功！\n目标数据库 [${host}:${port}/YHDB] 认证通过，可以执行造数操作。\n账户: ${user}`
    } else {
      store.showToast(res.error || '数据库认证失败，请检查 Host、账户和密码', 'error')
      formattedResult.value = `[${new Date().toLocaleTimeString()}] ❌ 数据库连接失败！\n原因: ${res.error || '请检查数据库地址、账户和密码'}`
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`测试失败: ${msg}`, 'error')
  } finally {
    testingDbConn.value = false
  }
}

async function onDirectExecuteDb() {
  if (!selectedOrgId.value || !selectedDeptId.value) {
    store.showToast('请先选择机构和护理单元', 'error')
    return
  }
  if (!createPatient.value && !createBoard.value && !createFee.value && !createExamine.value && !createAdvice.value && !createOperation.value) {
    store.showToast('请至少勾选一个造数选项', 'error')
    return
  }
  if (!dbHost.value.trim()) {
    store.showToast('请输入目标数据库 Host', 'error')
    return
  }

  executingDb.value = true
  formattedResult.value = `[${new Date().toLocaleTimeString()}] 正在建立 MySQL 数据库连接并批量执行数据插入...\n`

  try {
    const resMock = generateMockDataSQL({
      orgId: selectedOrgId.value,
      deptId: selectedDeptId.value,
      createPatient: createPatient.value,
      patientCount: patientCount.value || 10,
      createBoard: createBoard.value,
      boardTouchMode: boardTouchMode.value,
      createFee: createFee.value,
      feeCount: feeCount.value || 10,
      feePatientId: feePatientId.value,
      createExamine: createExamine.value,
      examineCount: examineCount.value || 10,
      examinePatientId: examinePatientId.value,
      createAdvice: createAdvice.value,
      adviceCount: adviceCount.value || 10,
      advicePatientId: advicePatientId.value,
      createOperation: createOperation.value,
      operationCount: operationCount.value || 10,
      operationPatientId: operationPatientId.value,
      useIgnore: useIgnore.value,
    })

    const execRes = await ipc.executeDbSql({
      host: dbHost.value.trim(),
      port: dbPort.value || 3306,
      user: dbUser.value || 'root',
      password: dbPass.value || '',
      database: 'YHDB',
      sqlStatements: resMock.rawStatements,
    })

    if (execRes.success) {
      formattedResult.value = `${resMock.summaryText}\n\n===== 直连数据库执行结果日志 =====\n${execRes.logs}`
      store.showToast(`数据已成功真正写入数据库！(写入 ${execRes.successCount || 0} 条，跳过 ${execRes.skippedCount || 0} 条)`, 'success')
    } else {
      formattedResult.value = `[${new Date().toLocaleTimeString()}] ❌ 数据库写入失败！\n${execRes.logs || execRes.error}\n\n-- 您可以拷贝下方生成的 SQL 语句尝试手动在 Navicat 中执行：\n\n${resMock.sqlText}`
      store.showToast(`写入数据库失败: ${execRes.error}`, 'error')
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`执行异常: ${msg}`, 'error')
  } finally {
    executingDb.value = false
  }
}

function onGenerateMockData() {
  if (!selectedOrgId.value || !selectedDeptId.value) {
    store.showToast('请先选择机构和护理单元', 'error')
    return
  }
  if (!createPatient.value && !createBoard.value && !createFee.value && !createExamine.value && !createAdvice.value && !createOperation.value) {
    store.showToast('请至少勾选一个造数选项', 'error')
    return
  }

  try {
    const res = generateMockDataSQL({
      orgId: selectedOrgId.value,
      deptId: selectedDeptId.value,
      createPatient: createPatient.value,
      patientCount: patientCount.value || 10,
      createBoard: createBoard.value,
      boardTouchMode: boardTouchMode.value,
      createFee: createFee.value,
      feeCount: feeCount.value || 10,
      feePatientId: feePatientId.value,
      createExamine: createExamine.value,
      examineCount: examineCount.value || 10,
      examinePatientId: examinePatientId.value,
      createAdvice: createAdvice.value,
      adviceCount: adviceCount.value || 10,
      advicePatientId: advicePatientId.value,
      createOperation: createOperation.value,
      operationCount: operationCount.value || 10,
      operationPatientId: operationPatientId.value,
      useIgnore: useIgnore.value,
    })

    formattedResult.value = `${res.summaryText}\n\n-- ===================================================\n-- 以下为生成的 SQL 语句脚本（可直接复制在数据库中执行）\n-- ===================================================\n\n${res.sqlText}`
    store.showToast('造数 SQL 脚本成功生成！', 'success')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    store.showToast(`造数失败: ${msg}`, 'error')
  }
}

function copyResult() {
  if (!formattedResult.value) return
  navigator.clipboard.writeText(formattedResult.value)
  store.showToast('结果已复制到剪贴板', 'success')
}
</script>

<style scoped>
.custom-result-scrollbar {
  overflow-y: auto !important;
}
.custom-result-scrollbar::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
.custom-result-scrollbar::-webkit-scrollbar-track {
  background: #0f172a;
  border-radius: 6px;
}
.custom-result-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 6px;
  border: 2px solid #0f172a;
}
.custom-result-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
