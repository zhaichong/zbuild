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
  // 优先使用 Electron IPC 绕过跨域 (CORS) 限制
  if (typeof window !== 'undefined' && (window as unknown as { tool?: { mockQueryRequest?: unknown } }).tool?.mockQueryRequest) {
    try {
      const data = await ipc.mockQueryRequest(url, method, body)
      return data as T
    } catch (e: unknown) {
      throw new Error(e instanceof Error ? e.message : String(e))
    }
  }

  // 网页端降级使用原生 fetch
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const options: RequestInit = {
    method,
    headers,
  }
  if (body) {
    options.body = typeof body === 'string' ? body : JSON.stringify(body)
  }

  const res = await fetch(url, options)
  const text = await res.text()

  if (!res.ok) {
    throw new Error(`远程服务器返回错误 ${res.status}: ${text.substring(0, 200)}`)
  }

  try {
    const json = JSON.parse(text)
    return (json.data !== undefined ? json.data : json) as T
  } catch {
    return text as unknown as T
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

export async function fetchDepts(baseUrl: string, orgId: string): Promise<DeptItem[]> {
  const host = cleanBaseUrl(baseUrl)
  const targetUrl = `${host}/omms/app-org/depts?orgId=${encodeURIComponent(orgId)}`
  const res = await requestApi<unknown>(targetUrl)
  if (Array.isArray(res)) return res as DeptItem[]
  if (res && typeof res === 'object' && Array.isArray((res as { list?: DeptItem[] }).list)) {
    return (res as { list: DeptItem[] }).list
  }
  return []
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
