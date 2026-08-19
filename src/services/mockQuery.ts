import { ipc } from '@/services/ipc'

export interface OrgItem {
  orgId: string
  orgName?: string
  [key: string]: unknown
}

export interface DeptItem {
  deptId: string
  deptName?: string
  deptKey?: string
  parentId?: string
  deptType?: string
  level?: number
  pathNames?: string[]
  fullPathName?: string
  children?: DeptItem[]
  [key: string]: unknown
}

export interface DeviceItem {
  deviceId: string
  deviceName?: string
  deviceNum?: string
  deviceType?: string
  deptId?: string
  deptName?: string
  deptKey?: string
  bedId?: string
  bedName?: string
  roomId?: string
  roomName?: string
  orgId?: string
  [key: string]: unknown
}

export interface PatientItem {
  bedName?: string
  birthday?: string
  doctorName?: string
  inTime?: string
  inpNo?: string
  nurseLevel?: string
  nurseLevelId?: string
  nurseName?: string
  patientAge?: string
  patientId?: string
  patientName?: string
  personIdNo?: string
  sex?: string
  [key: string]: unknown
}

export interface ExtractionResult {
  deviceData: Record<string, string>
  orgData: Record<string, string>
  patientData: Record<string, string>
  formattedText: string
}

async function requestApi<T>(url: string, method = 'GET', body: unknown = null): Promise<T> {
  // 统一通过 ipc.mockQueryRequest 请求（Electron走原生IPC，Web模式走服务端代理，彻底解决浏览器跨域CORS限制）
  try {
    const data = await ipc.mockQueryRequest(url, method, body)
    if (data && typeof data === 'object' && 'data' in (data as Record<string, unknown>)) {
      return (data as Record<string, unknown>).data as T
    }
    return data as T
  } catch (e: unknown) {
    throw new Error(e instanceof Error ? e.message : String(e))
  }
}

function cleanBaseUrl(url: string): string {
  let cleaned = url.trim()
  if (!cleaned.startsWith('http://') && !cleaned.startsWith('https://')) {
    cleaned = 'http://' + cleaned
  }
  return cleaned.replace(/\/$/, '')
}

export async function fetchOrgs(baseUrl: string): Promise<OrgItem[]> {
  const host = cleanBaseUrl(baseUrl)
  const targetUrl = `${host}/omms/app-rbac/orgs`
  const res = await requestApi<unknown>(targetUrl)
  if (Array.isArray(res)) return res as OrgItem[]
  if (res && typeof res === 'object' && Array.isArray((res as { list?: OrgItem[] }).list)) {
    return (res as { list: OrgItem[] }).list
  }
  return []
}

/**
 * 递归解析并标准化部门/护理单元树
 */
export function parseDeptTree(rawList: unknown[]): DeptItem[] {
  if (!Array.isArray(rawList) || rawList.length === 0) return []

  const extractChildren = (item: Record<string, unknown>): unknown[] => {
    if (Array.isArray(item.children)) return item.children
    if (Array.isArray(item.childList)) return item.childList
    if (Array.isArray(item.childs)) return item.childs
    if (Array.isArray(item.subDepts)) return item.subDepts
    if (Array.isArray(item.depts)) return item.depts
    if (Array.isArray(item.nodes)) return item.nodes
    if (Array.isArray(item.treeList)) return item.treeList
    return []
  }

  const hasNestedChildren = rawList.some(
    (item) => item && typeof item === 'object' && extractChildren(item as Record<string, unknown>).length > 0,
  )

  if (!hasNestedChildren) {
    const hasParentField = rawList.some(
      (item) =>
        item &&
        typeof item === 'object' &&
        ('parentId' in item || 'pId' in item || 'parentDeptId' in item || 'pid' in item),
    )

    if (hasParentField) {
      return buildTreeFromFlatList(rawList as Record<string, unknown>[])
    }
  }

  function normalizeNode(raw: Record<string, unknown>, level = 1, parentPath: string[] = []): DeptItem {
    const deptId = String(raw.deptId || raw.id || '')
    const deptName = String(raw.deptName || raw.name || raw.title || deptId)
    const deptKey = String(raw.deptKey || raw.key || raw.code || deptId)
    const currentPath = [...parentPath, deptName]
    const rawKids = extractChildren(raw)

    const node: DeptItem = {
      ...raw,
      deptId,
      deptName,
      deptKey,
      level,
      pathNames: currentPath,
      fullPathName: currentPath.join(' / '),
      children: [],
    }

    if (rawKids.length > 0) {
      node.children = rawKids
        .filter((c): c is Record<string, unknown> => !!c && typeof c === 'object')
        .map((c) => normalizeNode(c, level + 1, currentPath))
    }

    return node
  }

  return rawList
    .filter((item): item is Record<string, unknown> => !!item && typeof item === 'object')
    .map((item) => normalizeNode(item, 1, []))
}

function buildTreeFromFlatList(flatList: Record<string, unknown>[]): DeptItem[] {
  const nodeMap = new Map<string, DeptItem>()
  const roots: DeptItem[] = []

  for (const raw of flatList) {
    const deptId = String(raw.deptId || raw.id || '')
    if (!deptId) continue
    const deptName = String(raw.deptName || raw.name || raw.title || deptId)
    const deptKey = String(raw.deptKey || raw.key || raw.code || deptId)
    const parentId = String(raw.parentId || raw.pId || raw.parentDeptId || raw.pid || '')

    nodeMap.set(deptId, {
      ...raw,
      deptId,
      deptName,
      deptKey,
      parentId,
      level: 1,
      pathNames: [deptName],
      fullPathName: deptName,
      children: [],
    })
  }

  for (const node of nodeMap.values()) {
    const pId = node.parentId
    if (pId && nodeMap.has(pId) && pId !== node.deptId) {
      nodeMap.get(pId)!.children!.push(node)
    } else {
      roots.push(node)
    }
  }

  function updatePaths(nodes: DeptItem[], level = 1, parentPath: string[] = []) {
    for (const n of nodes) {
      n.level = level
      n.pathNames = [...parentPath, n.deptName || n.deptId]
      n.fullPathName = n.pathNames.join(' / ')
      if (n.children && n.children.length > 0) {
        updatePaths(n.children, level + 1, n.pathNames)
      }
    }
  }

  updatePaths(roots, 1, [])
  return roots
}

/**
 * 展平部门树为带有层级缩进或路径的一维数组
 */
export function flattenDeptTree(tree: DeptItem[]): DeptItem[] {
  const result: DeptItem[] = []
  function traverse(nodes: DeptItem[]) {
    for (const node of nodes) {
      result.push(node)
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    }
  }
  traverse(tree)
  return result
}

export async function fetchDepts(baseUrl: string, orgId: string): Promise<DeptItem[]> {
  const host = cleanBaseUrl(baseUrl)
  const targetUrl = `${host}/omms/app-org/depts?orgId=${encodeURIComponent(orgId)}`
  const res = await requestApi<unknown>(targetUrl)

  let rawList: unknown[] = []
  if (Array.isArray(res)) {
    rawList = res
  } else if (res && typeof res === 'object') {
    const obj = res as Record<string, unknown>
    if (Array.isArray(obj.list)) {
      rawList = obj.list
    } else if (Array.isArray(obj.depts)) {
      rawList = obj.depts
    } else if (Array.isArray(obj.data)) {
      rawList = obj.data
    } else if (Array.isArray(obj.children)) {
      rawList = obj.children
    }
  }

  return parseDeptTree(rawList)
}

export async function fetchDevices(baseUrl: string, deptId: string): Promise<DeviceItem[]> {
  const host = cleanBaseUrl(baseUrl)
  const targetUrl = `${host}/tdms/app-td/device/${encodeURIComponent(deptId)}`
  const res = await requestApi<unknown>(targetUrl)

  let list: DeviceItem[] = []
  if (Array.isArray(res)) {
    list = res as DeviceItem[]
  } else if (res && typeof res === 'object') {
    const obj = res as { list?: DeviceItem[] }
    if (Array.isArray(obj.list)) {
      list = obj.list
    } else if ('deviceId' in obj) {
      list = [obj as DeviceItem]
    }
  }

  // Filter device types wnBedHeadExtension and wnBedSideExtension
  return list.filter(
    (item) => item.deviceType === 'wnBedHeadExtension' || item.deviceType === 'wnBedSideExtension',
  )
}

export async function extractLinkData(
  baseUrl: string,
  deviceId: string,
  defaultDeptId?: string,
  bedName?: string,
): Promise<ExtractionResult> {
  const host = cleanBaseUrl(baseUrl)

  // 1. Fetch device detail info
  const detailUrl = `${host}/tdms/app-td/device?deviceId=${encodeURIComponent(deviceId)}`
  const dinfo = (await requestApi<DeviceItem>(detailUrl)) || ({} as DeviceItem)

  const targetDeptId = dinfo.deptId || defaultDeptId
  const targetBedName = dinfo.bedName || bedName

  if (!targetDeptId) {
    throw new Error('未能从终端数据中读取到所属护理单元 (deptId)')
  }

  // 2. Fetch patient list
  const patientUrl = `${host}/bnms/app-bn/patient-in-list/list`
  const patientInfo = await requestApi<unknown>(patientUrl, 'POST', { deptId: targetDeptId })

  // 3. Construct device and org info objects
  const deviceData: Record<string, string> = {
    BED_ID: String(dinfo.bedId || ''),
    BED_NAME: String(dinfo.bedName || ''),
    DEPT_ID: String(dinfo.deptId || ''),
    DEPT_KEY: String(dinfo.deptKey || ''),
    DEPT_NAME: String(dinfo.deptName || ''),
    DEVICE_ID: String(dinfo.deviceId || ''),
    DEVICE_NAME: String(dinfo.deviceName || ''),
    DEVICE_NUM: String(dinfo.deviceNum || ''),
    ROOM_ID: String(dinfo.roomId || ''),
    ROOM_NAME: String(dinfo.roomName || ''),
  }

  const orgData: Record<string, string> = {
    orgId: String(dinfo.orgId || ''),
  }

  // 4. Match patient info
  let patientList: Array<{ patientIn?: PatientItem; [key: string]: unknown }> = []
  if (Array.isArray(patientInfo)) {
    patientList = patientInfo
  } else if (patientInfo && typeof patientInfo === 'object') {
    const obj = patientInfo as Record<string, unknown>
    if (Array.isArray(obj.patientSelectDtos)) {
      patientList = obj.patientSelectDtos as Array<{ patientIn?: PatientItem }>
    } else if (Array.isArray(obj.list)) {
      patientList = obj.list as Array<{ patientIn?: PatientItem }>
    }
  }

  let targetPatient: PatientItem = {}
  if (targetBedName) {
    const found = patientList.find((item) => {
      const pIn = item.patientIn || (item as PatientItem)
      return (pIn && String(pIn.bedName) === String(targetBedName)) || String(item.bedName) === String(targetBedName)
    })
    if (found) {
      targetPatient = (found.patientIn || found) as PatientItem
    }
  }

  // Fallback to first patient if no match by bed name
  if (Object.keys(targetPatient).length === 0 && patientList.length > 0) {
    const first = patientList[0]
    targetPatient = (first.patientIn || first) as PatientItem
  }

  const patientData: Record<string, string> = {
    bedName: String(targetPatient.bedName || ''),
    birthday: String(targetPatient.birthday || ''),
    doctorName: String(targetPatient.doctorName || ''),
    inTime: String(targetPatient.inTime || ''),
    inpNo: String(targetPatient.inpNo || ''),
    nurseLevel: String(targetPatient.nurseLevel || ''),
    nurseLevelId: String(targetPatient.nurseLevelId || ''),
    nurseName: String(targetPatient.nurseName || ''),
    patientAge: String(targetPatient.patientAge || ''),
    patientId: String(targetPatient.patientId || ''),
    patientName: String(targetPatient.patientName || ''),
    personIdNo: String(targetPatient.personIdNo || ''),
    sex: String(targetPatient.sex || ''),
  }

  const formattedText = `===== 设备信息 =====
${JSON.stringify(deviceData, null, 2)}

===== 机构信息 =====
${JSON.stringify(orgData, null, 2)}

===== 患者信息 =====
${JSON.stringify(patientData, null, 2)}`

  return {
    deviceData,
    orgData,
    patientData,
    formattedText,
  }
}
