function generateUUID(): string {
  return 'xxxxxxxxxxxx4xxxYxxxxxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function generateNumericId(length = 15): string {
  const ts = Date.now().toString()
  const rnd = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  return (ts + rnd).slice(0, length)
}

// 45条示例患者数据
const PATIENT_TEMPLATES = [
  { bedName: '16', sex: '男', patientName: '王志水', illnessStatus: '一般', insuranceType: '住院自费', diagnose: '腹痛', diet: '| 低盐低脂饮食', allergy: null, nurseLevel: '一级护理', doctorName: '7c5d64d390b3454ebe9b9fb1fc87df32' },
  { bedName: '03', sex: '男', patientName: '方杨', illnessStatus: '一般', insuranceType: '市在职(住院省医保)', diagnose: '急性下壁侧壁心肌梗死', diet: '| 低盐低脂饮食', allergy: null, nurseLevel: '二级护理', doctorName: '4d9470ea848311f0b54f005056b57f69' },
  { bedName: '19', sex: '女', patientName: '余凤凤', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '腹痛', diet: '| 禁食水', allergy: null, nurseLevel: '一级护理', doctorName: '7c5d64d390b3454ebe9b9fb1fc87df32' },
  { bedName: '06', sex: '男', patientName: '程学宏', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '直肠恶性肿瘤', diet: '| 低盐低脂饮食', allergy: null, nurseLevel: '未知护理', doctorName: '5135761877f911f0b536005056b57f69' },
  { bedName: '28', sex: '男', patientName: '余维洋', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '前列腺恶性肿瘤', diet: '| 低盐低脂饮食', allergy: null, nurseLevel: '二级护理', doctorName: '513566d277f911f0b536005056b57f69' },
  { bedName: '06', sex: '男', patientName: '王纲仁', illnessStatus: '一般', insuranceType: '区退休(住院省医保)', diagnose: '胃肿物', diet: null, allergy: null, nurseLevel: '未知护理', doctorName: '3a3d0ad26f224e1997d81fdced360d21' },
  { bedName: '38', sex: '女', patientName: '孙秀云', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '急性胃肠炎', diet: null, allergy: null, nurseLevel: '未知护理', doctorName: '8852aa455392451280142e08c013f45d' },
  { bedName: '25', sex: '男', patientName: '周仲水', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '肺恶性肿瘤', diet: '| 低盐、低脂、糖尿病饮食', allergy: null, nurseLevel: '二级护理', doctorName: '513553e077f911f0b536005056b57f69' },
  { bedName: '13', sex: '男', patientName: '匡振以', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '反流性食管炎', diet: '| 低盐低脂、半流质饮食', allergy: null, nurseLevel: '二级护理', doctorName: 'c354280632a54f3da420fc24f1cd7e53' },
  { bedName: '30', sex: '男', patientName: '周加虎', illnessStatus: '一般', insuranceType: '异地医保(省)', diagnose: '冠状动脉粥样硬化性心脏病', diet: '| 低盐低脂饮食', allergy: null, nurseLevel: '一级护理', doctorName: '4d948ef4848311f0b54f005056b57f69' },
  { bedName: '05', sex: '男', patientName: '刘启宏', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '结肠息肉', diet: '| 低盐低脂、少渣饮食', allergy: null, nurseLevel: '二级护理', doctorName: 'c354280632a54f3da420fc24f1cd7e53' },
  { bedName: 'C03', sex: '男', patientName: '管成兴', illnessStatus: '一般', insuranceType: '郎溪县城乡居民(住院省医保)', diagnose: '急性心肌梗死', diet: '| 低盐低脂糖尿病饮食', allergy: null, nurseLevel: '一级护理', doctorName: '9bf0422951454da890b0d4613eb2bf86' },
  { bedName: '41', sex: '男', patientName: '陈永龙', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '肺恶性肿瘤', diet: '| 软食', allergy: null, nurseLevel: '二级护理', doctorName: '51356e5277f911f0b536005056b57f69' },
  { bedName: '17', sex: '女', patientName: '笪桂兰', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '中度贫血', diet: '| 温凉流食', allergy: null, nurseLevel: '二级护理', doctorName: '90772c4e4d3342018b549a7f10a50f1e' },
  { bedName: '08', sex: '女', patientName: '盛秀兰', illnessStatus: '一般', insuranceType: '区退休(住院省医保)', diagnose: '脑梗死后遗症', diet: '| 低盐低脂糖尿病饮食', allergy: '| 无', nurseLevel: '二级护理', doctorName: '54e9dcb271ce11f09601005056b57f69' },
  { bedName: '03', sex: '女', patientName: '李小九', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '肺恶性肿瘤', diet: '| 低优蛋白饮食', allergy: null, nurseLevel: '二级护理', doctorName: '5135761877f911f0b536005056b57f69' },
  { bedName: '32', sex: '男', patientName: '贺文革', illnessStatus: '一般', insuranceType: '区退休(住院省医保)', diagnose: '舌恶性肿瘤', diet: null, allergy: null, nurseLevel: '二级护理', doctorName: '51355f3e77f911f0b536005056b57f69' },
  { bedName: '28', sex: '男', patientName: '王来木', illnessStatus: '一般', insuranceType: '旌德县城乡居民(住院省医保)', diagnose: '肝恶性肿瘤', diet: '| 低盐低脂饮食', allergy: null, nurseLevel: '二级护理', doctorName: '51356e5277f911f0b536005056b57f69' },
  { bedName: '10', sex: '男', patientName: '王杰', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '髌骨骨折', diet: '| 清淡饮食', allergy: null, nurseLevel: '二级护理', doctorName: '6061569ce12e445d9e7ab953be0004e7' },
  { bedName: '36', sex: '男', patientName: '沈瑞发', illnessStatus: '一般', insuranceType: '宣州区城乡居民(住院省医保)', diagnose: '腹痛', diet: '| 半流质饮食', allergy: null, nurseLevel: '一级护理', doctorName: 'c354280632a54f3da420fc24f1cd7e53' },
]

// 费用相关模板
const ADVANCE_PAYMENT_TEMPLATES = [
  { mode: '刷卡支付', operator: '代玲', status: '未结算', amount: 500.00 },
  { mode: '支付宝支付', operator: '刘毅', status: '已结算', amount: 8000.00 },
  { mode: '微信支付', operator: '刘毅', status: '已结算', amount: 500.00 },
  { mode: '支付宝支付', operator: '马思文', status: '未结算', amount: 2000.00 },
]

const COST_CENTRE_TEMPLATES = [
  { mode: '西药费', name: '碘海醇注射液(联盟)/35g*100ml/瓶', price: 84.53, count: 1, total: 84.53 },
  { mode: '化验费', name: '糖类抗原测定CA125/原', price: 65.00, count: 1, total: 65.00 },
  { mode: '化验费', name: '糖类抗原测定CA153/项', price: 65.00, count: 1, total: 65.00 },
  { mode: '化验费', name: '糖类抗原测定CA199/项', price: 65.00, count: 1, total: 65.00 },
  { mode: '化验费', name: '大生化检验组合/组', price: 195.00, count: 1, total: 195.00 },
  { mode: '化验费', name: '淋巴亚群相对计数/项', price: 45.00, count: 7, total: 315.00 },
  { mode: '材料费', name: '采血器(检验）/根', price: 1.40, count: 1, total: 1.40 },
  { mode: '放免费', name: '癌胚抗原测定(CEA)/项', price: 45.00, count: 1, total: 45.00 },
]

const COST_SETTLEMENT_TEMPLATES = [
  { advance: 4157.16, total: 2342.65, balance: 432.45, own: 6862.11, returnAmt: 342.54, supp: 32.45, status: '结算出院' },
  { advance: 2261.44, total: 5645.45, balance: 69.69, own: 2116.78, returnAmt: 564.35, supp: 54.75, status: '结算出院' },
  { advance: 3695.29, total: 6521.42, balance: 88.39, own: 3111.23, returnAmt: 263.53, supp: 61.61, status: '结算出院' },
]

const COST_SUMMARY_TEMPLATES = [
  { code: '1', mode: '西药费', amount: 981.54, status: '0' },
  { code: '10', mode: '化验费', amount: 863.00, status: '0' },
  { code: '13', mode: '护理费', amount: 50.00, status: '0' },
  { code: '21', mode: '放免费', amount: 45.00, status: '0' },
  { code: '41', mode: 'CT费', amount: 1890.00, status: '0' },
  { code: '44', mode: '心电图费', amount: 38.40, status: '0' },
  { code: '5', mode: '床位费', amount: 40.00, status: '0' },
  { code: '6', mode: '诊疗费', amount: 18.00, status: '0' },
  { code: '76', mode: '注射费', amount: 21.00, status: '0' },
  { code: '77', mode: '材料费', amount: 107.59, status: '0' },
]

// 检查检验模板
const EXAMINE_REPORT_TEMPLATES = [
  { content: '红细胞分布宽度变异系数', adviceName: '血细胞分析(五分类)', applyDoctor: '谷锦', checkDoctor: '武双星', checkDept: '门诊化验室', sampleType: '全血' },
  { content: '胆红素', adviceName: '尿常规化学检测', applyDoctor: '谷锦', checkDoctor: '刘玲', checkDept: '门诊化验室', sampleType: '尿液' },
  { content: '酮体', adviceName: '尿常规化学检测', applyDoctor: '谷锦', checkDoctor: '刘玲', checkDept: '门诊化验室', sampleType: '尿液' },
  { content: '亚硝酸盐', adviceName: '尿常规化学检测', applyDoctor: '谷锦', checkDoctor: '刘玲', checkDept: '门诊化验室', sampleType: '尿液' },
  { content: '酸碱度', adviceName: '尿常规化学检测', applyDoctor: '谷锦', checkDoctor: '刘玲', checkDept: '门诊化验室', sampleType: '尿液' },
  { content: '尿蛋白', adviceName: '尿常规化学检测', applyDoctor: '谷锦', checkDoctor: '刘玲', checkDept: '门诊化验室', sampleType: '尿液' },
]

const EXAMINE_DETAILS_TEMPLATES = [
  { name: '血红蛋白', result: '92', abnormal: '1', unit: 'g/L' },
  { name: '钾', result: '5.17', abnormal: '0', unit: 'mmol/L' },
  { name: '钠', result: '139.7', abnormal: '0', unit: 'mmol/L' },
  { name: '氯', result: '105.7', abnormal: '0', unit: 'mmol/L' },
  { name: '二氧化碳', result: '23', abnormal: '0', unit: 'mmol/L' },
  { name: '钙', result: '2.60', abnormal: '0', unit: 'mmol/L' },
]

const INSPECTION_REPORT_TEMPLATES = [
  { content: 'CT-肋骨成像 胸部平扫', applyDoctor: '杨扬', checkDoctor: '沈潮', checkDept: 'CT', details: '两肺肺纹理清晰，右肺下叶见斑片状影，边缘欠光整，密度不均。', result: '1.右肺斑片状影，请结合临床抗炎治疗后复查。\n2.两肺索条灶。' },
  { content: 'CT-头颅+面颅骨重建', applyDoctor: '杨扬', checkDoctor: '沈潮', checkDept: 'CT', details: '左侧颞顶部颅板下见梭形密度增高影，左侧脑室受压变形。', result: '1.左侧顶颞部硬膜外血肿；右侧颞叶脑挫伤。\n2.两侧上颌骨骨折。' },
  { content: 'CT-胫腓骨重建', applyDoctor: '高从良', checkDoctor: '李婷', checkDept: 'CT', details: '左胫腓骨中下段骨质断裂，可见骨折线影。', result: '左胫腓骨中下段骨折外固定术后改变，请结合临床。' },
  { content: '肘关节正侧位（左）', applyDoctor: '杨扬', checkDoctor: '王青怀', checkDept: '普放', details: '左肘关节在位，各组成骨骨质形态、结构正常。', result: '左肘关节未见明显外伤性骨性病变。' },
]

// 简版医嘱模板
const DOCTOR_ADVICE_TEMPLATES = [
  { field1: '肿瘤科护理常规', field3: '0', field4: '4', field5: '1.0', field6: '1.0', field7: null, field8: null, field9: 'qd', creator: '王玮' },
  { field1: 'Ⅱ级护理', field3: '0', field4: '4', field5: '1.0', field6: '1.0', field7: null, field8: null, field9: 'qd', creator: '王玮' },
  { field1: '软食', field3: '0', field4: '99', field5: '1.0', field6: '1.0', field7: null, field8: null, field9: 'qd', creator: '王玮' },
  { field1: '陪客一人', field3: '0', field4: '99', field5: '1.0', field6: '1.0', field7: null, field8: null, field9: 'qd', creator: '王玮' },
  { field1: '地榆升白片(薄膜衣)', field3: '0', field4: '3', field5: '0.2', field6: '2.0', field7: 'g', field8: '口服', field9: 'tid', creator: '王娓娓' },
  { field1: '测血压', field3: '0', field4: '99', field5: '1.0', field6: '1.0', field7: null, field8: null, field9: 'qd', creator: '王玮' },
  { field1: '琥珀酸美托洛尔缓释片(联盟)', field3: '0', field4: '3', field5: '47.5', field6: '1.0', field7: 'mg', field8: '口服', field9: 'qd', creator: '王玮' },
  { field1: '0.9%氯化钠注射液(直立输液袋)', field3: '0', field4: '1', field5: '250.0', field6: '1.0', field7: 'ml', field8: '静滴', field9: 'qd', creator: '王玮' },
  { field1: '鸦胆子油乳注射液', field3: '0', field4: '1', field5: '30.0', field6: '3.0', field7: 'ml', field8: '静滴', field9: 'qd', creator: '王玮' },
]

// 手术模板
const OPERATION_TEMPLATES = [
  { diagnosis: '阑尾炎', project: '阑尾炎切除术', status: '已结束' },
  { diagnosis: '阑尾炎', project: '结膜炎治疗术', status: '进行中' },
  { diagnosis: '冠心病', project: '心脏搭桥术', status: '未开始' },
  { diagnosis: '右腿骨折', project: '右腿骨折复位内固定术', status: '未开始' },
  { diagnosis: '左腿骨折', project: '左腿骨折切开复位术', status: '未开始' },
  { diagnosis: '颅骨骨瘤', project: '颅骨骨瘤切除术', status: '已结束' },
  { diagnosis: '胆囊炎', project: '胆囊造口术', status: '未开始' },
]

export interface MockDataOptions {
  orgId: string
  deptId: string
  deptKey?: string
  deptName?: string
  useDeptKey?: boolean
  createPatient: boolean
  patientCount: number
  createBoard: boolean
  boardTouchMode?: number // 0 非触屏 1 触屏
  // 费用相关
  createFee?: boolean
  feeCount?: number
  feePatientId?: string
  // 检查检验
  createExamine?: boolean
  examineCount?: number
  examinePatientId?: string
  // 简版医嘱
  createAdvice?: boolean
  adviceCount?: number
  advicePatientId?: string
  // 手术部分
  createOperation?: boolean
  operationCount?: number
  operationPatientId?: string

  useIgnore?: boolean
}

export interface MockDataResult {
  sqlText: string
  rawStatements: string[]
  summaryText: string
  patientCountGenerated: number
  boardCountGenerated: number
  feeCountGenerated: number
  examineCountGenerated: number
  adviceCountGenerated: number
  operationCountGenerated: number
}

function escapeSqlVal(val: string | number | null | undefined): string {
  if (val === null || val === undefined) return 'NULL'
  if (typeof val === 'number') return String(val)
  const escaped = String(val).replace(/'/g, "''")
  return `'${escaped}'`
}

export function generateMockDataSQL(options: MockDataOptions): MockDataResult {
  const {
    orgId,
    deptId,
    deptKey = '',
    deptName = '',
    useDeptKey = false,
    createPatient,
    patientCount,
    createBoard,
    boardTouchMode = 0,
    createFee = false,
    feeCount = 10,
    feePatientId = '',
    createExamine = false,
    examineCount = 10,
    examinePatientId = '',
    createAdvice = false,
    adviceCount = 10,
    advicePatientId = '',
    createOperation = false,
    operationCount = 10,
    operationPatientId = '',
    useIgnore = true,
  } = options

  // 根据配置决定写入数据库字段的科室标识（默认使用部门 deptId）
  const effectiveDeptId = (useDeptKey && deptKey ? deptKey : deptId).trim()
  const effectiveDeptName = (deptName || '护理单元').trim()

  const insertCmd = useIgnore ? 'INSERT IGNORE INTO' : 'INSERT INTO'
  const sqlLines: string[] = []
  const rawStatements: string[] = []

  sqlLines.push(`-- ===================================================`)
  sqlLines.push(`-- 智能造数据 SQL 脚本`)
  sqlLines.push(`-- 目标机构 (org_id): ${orgId}`)
  sqlLines.push(`-- 目标护理单元名称: ${effectiveDeptName}`)
  sqlLines.push(`-- 目标护理单元写入标识 (dept_id): ${effectiveDeptId} (${useDeptKey && deptKey ? '使用科室Key' : '使用部门deptId'})`)
  sqlLines.push(`-- 部门 deptId: ${deptId}`)
  if (deptKey) sqlLines.push(`-- 业务 Key: ${deptKey}`)
  sqlLines.push(`-- 生成时间: ${new Date().toLocaleString()}`)
  sqlLines.push(`-- 增量防护: 启用 (自增床号/单号/主键UUID)`)
  sqlLines.push(`-- 遇重跳过: ${useIgnore ? '开启 (INSERT IGNORE)' : '关闭'}`)
  sqlLines.push(`-- ===================================================\n`)

  let generatedPatients = 0
  let generatedBoards = 0
  let generatedFees = 0
  let generatedExamines = 0
  let generatedAdvices = 0
  let generatedOperations = 0

  const generatedPatientIdsList: string[] = []

  // 1. 生成患者数据
  if (createPatient && patientCount > 0) {
    sqlLines.push(`-- 1. 患者数据 (bn_patient_in) 共 ${patientCount} 条 --`)

    // 基于时间戳动态生成基础ID，确保不同科室/多次生成互不撞重
    const timestampSeed = Date.now().toString().slice(-6)
    const baseInpNo = 2000000 + Math.floor(Math.random() * 7000000)
    const nowStr = '2025-09-01 09:00:00'

    for (let i = 0; i < patientCount; i++) {
      const tpl = PATIENT_TEMPLATES[i % PATIENT_TEMPLATES.length]

      const recordId = generateUUID()
      const patientId = `${timestampSeed}${String(i).padStart(3, '0')}`
      generatedPatientIdsList.push(patientId)
      const inpNo = `${baseInpNo + i}`
      const bedName = `${i + 1}`

      const sql = `${insertCmd} \`YHDB\`.\`bn_patient_in\`(` +
        `\`patient_id\`, \`id\`, \`person_id_no\`, \`dept_id\`, \`bed_name\`, ` +
        `\`in_fqcy\`, \`sex\`, \`inp_no\`, \`doctor_name\`, \`nurse_name\`, ` +
        `\`birthday\`, \`in_time\`, \`nurse_level\`, \`org_id\`, \`create_time\`, ` +
        `\`create_user\`, \`patient_name\`, \`illness_status\`, \`insurance_type\`, \`diagnose\`, ` +
        `\`diet\`, \`allergy\`, \`operation_time\`, \`in_dept_time\`, \`wristband\`, ` +
        `\`if_settlement\`, \`patient_in_qrcode\`` +
        `) VALUES (` +
        `${escapeSqlVal(patientId)}, ${escapeSqlVal(recordId)}, NULL, ${escapeSqlVal(effectiveDeptId)}, ${escapeSqlVal(bedName)}, ` +
        `1, ${escapeSqlVal(tpl.sex)}, ${escapeSqlVal(inpNo)}, ${escapeSqlVal(tpl.doctorName)}, NULL, ` +
        `'1970-01-01 00:00:00', ${escapeSqlVal(nowStr)}, ${escapeSqlVal(tpl.nurseLevel)}, ${escapeSqlVal(orgId)}, ${escapeSqlVal(nowStr)}, ` +
        `'his', ${escapeSqlVal(tpl.patientName)}, ${escapeSqlVal(tpl.illnessStatus)}, ${escapeSqlVal(tpl.insuranceType)}, ${escapeSqlVal(tpl.diagnose)}, ` +
        `${escapeSqlVal(tpl.diet)}, ${escapeSqlVal(tpl.allergy)}, NULL, ${escapeSqlVal(nowStr)}, NULL, ` +
        `NULL, NULL);`

      sqlLines.push(sql)
      rawStatements.push(sql)
      generatedPatients++
    }
    sqlLines.push('')
  }

  // 辅助方法：获取生效的目标患者 ID
  const getTargetPatientId = (specifiedId: string | undefined, index: number): string => {
    if (specifiedId && specifiedId.trim()) {
      return specifiedId.trim()
    }
    if (generatedPatientIdsList.length > 0) {
      return generatedPatientIdsList[index % generatedPatientIdsList.length]
    }
    return `GK7Q347${866 + (index % 100)}`
  }

  // 2. 生成看板数据 (bo_switch & td_device)
  if (createBoard) {
    sqlLines.push(`-- 2. 看板配置数据 (bo_switch & td_device) [touch_mode: ${boardTouchMode}] --`)

    const switchId = generateUUID()
    const devId = generateUUID()
    const templateId = generateUUID()
    const createTime = '2024-07-26 13:11:13'
    const updateTime = '2025-10-20 09:41:53'

    const randomMac = `30:1f:9a:${Array.from({ length: 3 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, '0')).join(':')}`
    const randomAppId = generateUUID().replace(/-/g, '').slice(0, 16)

    const boSwitchSql = `${insertCmd} \`YHDB\`.\`bo_switch\` (` +
      `\`switch_id\`, \`dept_id\`, \`dev_id\`, \`is_switch\`, \`switch_seconds\`, ` +
      `\`bed_mode\`, \`touch_mode\`, \`bed_switch_seconds\`, \`template_id\`, \`template_name\`, ` +
      `\`allow_pwd\`, \`effective_times\`, \`page_ids\`, \`if_shift\`, \`shift_duration\`, ` +
      `\`if_restart\`, \`restart_duration\`, \`closeScreenTime\`, \`isCloseScreen\`, \`suspend\` ` +
      `) VALUES (` +
      `${escapeSqlVal(switchId)}, ${escapeSqlVal(effectiveDeptId)}, ${escapeSqlVal(devId)}, 1, 600, ` +
      `NULL, ${boardTouchMode}, 30, ${escapeSqlVal(templateId)}, 'zc', b'0', NULL, ` +
      `'[]', 0, NULL, 0, '23:00', '{"endTime": "05:00", "beginTime": "23:00"}', 0, 0);`

    const tdDeviceSql = `${insertCmd} \`YHDB\`.\`td_device\` (` +
      `\`deviceId\`, \`ip\`, \`macAddress\`, \`icCardNum\`, \`sceneType\`, ` +
      `\`broadcast\`, \`deviceNum\`, \`deviceAppId\`, \`lastUpTime\`, \`lastUpStatus\`, ` +
      `\`lastOtaUpTime\`, \`lastOtaUpStatus\`, \`singleStatus\`, \`deviceName\`, \`deviceType\`, ` +
      `\`deptId\`, \`deviceModel\`, \`callCode\`, \`status\`, \`params\`, ` +
      `\`versions\`, \`positions\`, \`onOffRule\`, \`orgId\`, \`isEnable\`, ` +
      `\`remark\`, \`createTime\`, \`createUser\`, \`updateTime\`, \`updateUser\` ` +
      `) VALUES (` +
      `${escapeSqlVal(devId)}, '192.168.224.183', ${escapeSqlVal(randomMac)}, NULL, 1, ` +
      `0, '1', ${escapeSqlVal(randomAppId)}, NULL, 2, ` +
      `NULL, NULL, 0, '1', 'bnNursingTV', ` +
      `${escapeSqlVal(effectiveDeptId)}, 't972', 1, '{"onLineStatus": 0}', '{"rotate": "0", "volume": "94", "brighter": "0", "resolution": "10801920"}', ` +
      `'{"appVersion": "3.1.400007-20231205", "authVersion": "", "callVersion": "", "upbsVersion": "3.1.400001-20230602", "systemVersion": "9", "hardwareVersion": "amlogic"}', ` +
      `'{"bedId": null, "roomId": null, "positionStr": null}', NULL, ${escapeSqlVal(orgId)}, 1, ` +
      `NULL, ${escapeSqlVal(createTime)}, NULL, ${escapeSqlVal(updateTime)}, ${escapeSqlVal(devId)});`

    sqlLines.push(boSwitchSql)
    sqlLines.push(tdDeviceSql)
    rawStatements.push(boSwitchSql)
    rawStatements.push(tdDeviceSql)
    sqlLines.push('')
    generatedBoards = 2
  }

  // 3. 生成费用相关数据
  if (createFee && feeCount > 0) {
    sqlLines.push(`-- 3. 费用相关数据 共 ${feeCount} 条 --`)

    for (let i = 0; i < feeCount; i++) {
      const pid = getTargetPatientId(feePatientId, i)

      // (a) 预交金 hc_advance_payment
      const advTpl = ADVANCE_PAYMENT_TEMPLATES[i % ADVANCE_PAYMENT_TEMPLATES.length]
      const advId = `2026${String(Date.now() + i).slice(-6)}`
      const sqlAdv = `${insertCmd} \`YHDB\`.\`hc_advance_payment\`(` +
        `\`advance_payment_id\`, \`patient_id\`, \`payment_negotiable\`, \`advance_amount\`, ` +
        `\`payment_mode\`, \`operator_id\`, \`operator_name\`, \`operation_time\`, \`dept_id\`, ` +
        `\`dept_name\`, \`settlement_status\`, \`org_id\`` +
        `) VALUES (` +
        `${escapeSqlVal(advId)}, ${escapeSqlVal(pid)}, '2023050803', ${advTpl.amount}, ` +
        `${escapeSqlVal(advTpl.mode)}, '2023050803', ${escapeSqlVal(advTpl.operator)}, '2025-09-01 10:00:00', ${escapeSqlVal(effectiveDeptId)}, ` +
        `${escapeSqlVal(effectiveDeptName)}, ${escapeSqlVal(advTpl.status)}, ${escapeSqlVal(orgId)});`

      // (b) 费用明细 hc_cost_centre
      const costTpl = COST_CENTRE_TEMPLATES[i % COST_CENTRE_TEMPLATES.length]
      const costCentreId = `2026${generateNumericId(15)}`
      const sqlCost = `${insertCmd} \`YHDB\`.\`hc_cost_centre\`(` +
        `\`cost_centre_id\`, \`patient_id\`, \`cost_mode\`, \`cost_item_name\`, ` +
        `\`cost_item_specs\`, \`cost_item_price\`, \`cost_item_count\`, \`cost_item_unit\`, ` +
        `\`cost_item_total\`, \`charge_time\`, \`dept_id\`, \`org_id\`` +
        `) VALUES (` +
        `${escapeSqlVal(costCentreId)}, ${escapeSqlVal(pid)}, ${escapeSqlVal(costTpl.mode)}, ${escapeSqlVal(costTpl.name)}, ` +
        `NULL, ${costTpl.price}, ${costTpl.count}, NULL, ` +
        `${costTpl.total}, '2025-09-01 10:30:00', ${escapeSqlVal(effectiveDeptId)}, ${escapeSqlVal(orgId)});`

      // (c) 费用汇总 hc_cost_summary
      const sumTpl = COST_SUMMARY_TEMPLATES[i % COST_SUMMARY_TEMPLATES.length]
      const costSumId = `${pid}-${300 + i}-${sumTpl.code}-0`
      const sqlSum = `${insertCmd} \`YHDB\`.\`hc_cost_summary\`(` +
        `\`cost_summary_id\`, \`patient_id\`, \`cost_code\`, \`cost_mode\`, ` +
        `\`cost_amount\`, \`settlement_status\`, \`dept_id\`, \`org_id\`` +
        `) VALUES (` +
        `${escapeSqlVal(costSumId)}, ${escapeSqlVal(pid)}, ${escapeSqlVal(sumTpl.code)}, ${escapeSqlVal(sumTpl.mode)}, ` +
        `${sumTpl.amount}, ${escapeSqlVal(sumTpl.status)}, ${escapeSqlVal(effectiveDeptId)}, ${escapeSqlVal(orgId)});`

      sqlLines.push(sqlAdv)
      sqlLines.push(sqlCost)
      sqlLines.push(sqlSum)
      rawStatements.push(sqlAdv)
      rawStatements.push(sqlCost)
      rawStatements.push(sqlSum)
      generatedFees++
    }

    // 可选生成 1 条结算主记录 hc_cost_settlement
    const setTpl = COST_SETTLEMENT_TEMPLATES[0]
    const firstPid = getTargetPatientId(feePatientId, 0)
    const setlId = `2026${generateNumericId(10)}`
    const sqlSetl = `${insertCmd} \`YHDB\`.\`hc_cost_settlement\`(` +
      `\`cost_settlement_id\`, \`patient_id\`, \`advance_amount\`, \`amount_total\`, ` +
      `\`cost_balance\`, \`own_expense_amount\`, \`return_amount\`, \`supplement_amount\`, ` +
      `\`settlement_status\`, \`settlement_time\`, \`dept_id\`, \`org_id\`` +
      `) VALUES (` +
      `${escapeSqlVal(setlId)}, ${escapeSqlVal(firstPid)}, ${setTpl.advance}, ${setTpl.total}, ` +
      `${setTpl.balance}, ${setTpl.own}, ${setTpl.returnAmt}, ${setTpl.supp}, ` +
      `${escapeSqlVal(setTpl.status)}, '2025-09-01 11:00:00', ${escapeSqlVal(effectiveDeptId)}, ${escapeSqlVal(orgId)});`

    sqlLines.push(sqlSetl)
    rawStatements.push(sqlSetl)
    sqlLines.push('')
  }

  // 4. 检查检验数据
  if (createExamine && examineCount > 0) {
    sqlLines.push(`-- 4. 检查检验数据 共 ${examineCount} 条 --`)

    for (let i = 0; i < examineCount; i++) {
      const pid = getTargetPatientId(examinePatientId, i)

      // (a) 检验报告 nr_examine_report
      const exTpl = EXAMINE_REPORT_TEMPLATES[i % EXAMINE_REPORT_TEMPLATES.length]
      const examineId = `2026EX${generateNumericId(12)}`
      const sampleId = `2026SMP${generateNumericId(8)}`

      const sqlExamine = `${insertCmd} \`YHDB\`.\`nr_examine_report\`(` +
        `\`examine_id\`, \`examine_content\`, \`patient_id\`, \`doctor_advice_time\`, ` +
        `\`doctor_advice_name\`, \`apply_doctor_name\`, \`check_doctor_name\`, \`check_dept_name\`, ` +
        `\`confirm_doctor_name\`, \`sample_id\`, \`sample_type\`, \`sample_get_time\`, ` +
        `\`sample_gatherer_name\`, \`sample_receive_time\`, \`sample_sender_name\`, \`report_time\`, ` +
        `\`report_status\`, \`remark_json\`, \`create_time\`, \`create_user\`, ` +
        `\`update_time\`, \`update_user\`, \`org_id\`, \`switch_setting\`` +
        `) VALUES (` +
        `${escapeSqlVal(examineId)}, ${escapeSqlVal(exTpl.content)}, ${escapeSqlVal(pid)}, '2025-09-01 08:30:00', ` +
        `${escapeSqlVal(exTpl.adviceName)}, ${escapeSqlVal(exTpl.applyDoctor)}, ${escapeSqlVal(exTpl.checkDoctor)}, ${escapeSqlVal(exTpl.checkDept)}, ` +
        `${escapeSqlVal(exTpl.checkDoctor)}, ${escapeSqlVal(sampleId)}, ${escapeSqlVal(exTpl.sampleType)}, '2025-09-01 09:00:00', ` +
        `${escapeSqlVal(exTpl.checkDoctor)}, '2025-09-01 09:15:00', NULL, '2025-09-01 09:45:00', ` +
        `'1', NULL, '2025-09-01 09:45:00', 'his', ` +
        `NULL, NULL, ${escapeSqlVal(orgId)}, 1);`

      // (b) 检验明细 nr_examine_report_details
      const dtTpl = EXAMINE_DETAILS_TEMPLATES[i % EXAMINE_DETAILS_TEMPLATES.length]
      const itemId = `2026ITEM${generateNumericId(20)}`
      const sqlExamineDetail = `${insertCmd} \`YHDB\`.\`nr_examine_report_details\`(` +
        `\`examine_item_id\`, \`examine_item_name\`, \`examine_id\`, \`examine_item_result\`, ` +
        `\`examine_item_abnormal\`, \`examine_item_unit\`, \`examine_item_reference_range\`, \`examine_item_crisis_value\`, \`remark_json\`` +
        `) VALUES (` +
        `${escapeSqlVal(itemId)}, ${escapeSqlVal(dtTpl.name)}, ${escapeSqlVal(examineId)}, ${escapeSqlVal(dtTpl.result)}, ` +
        `${escapeSqlVal(dtTpl.abnormal)}, ${escapeSqlVal(dtTpl.unit)}, NULL, NULL, NULL);`

      // (c) 检查报告 nr_inspection_report
      const insTpl = INSPECTION_REPORT_TEMPLATES[i % INSPECTION_REPORT_TEMPLATES.length]
      const inspectionId = `2026INS${generateNumericId(10)}`
      const sqlInspection = `${insertCmd} \`YHDB\`.\`nr_inspection_report\`(` +
        `\`inspection_id\`, \`inspection_content\`, \`patient_id\`, \`doctor_advice_time\`, ` +
        `\`doctor_advice_name\`, \`apply_doctor_name\`, \`check_doctor_name\`, \`confirm_doctor_name\`, ` +
        `\`check_dept_name\`, \`report_time\`, \`report_status\`, \`create_time\`, ` +
        `\`create_user\`, \`update_time\`, \`update_user\`, \`org_id\`, ` +
        `\`remark_json\`, \`img_url\`, \`inspection_body_part\`, \`inspection_details\`, ` +
        `\`inspection_result\`, \`check_doctor_name_picture\`, \`pdf_path\`, \`switch_setting\`, \`appointment_time\`` +
        `) VALUES (` +
        `${escapeSqlVal(inspectionId)}, ${escapeSqlVal(insTpl.content)}, ${escapeSqlVal(pid)}, '2025-09-01 10:00:00', ` +
        `${escapeSqlVal(insTpl.content)}, ${escapeSqlVal(insTpl.applyDoctor)}, ${escapeSqlVal(insTpl.checkDoctor)}, ${escapeSqlVal(insTpl.checkDept)}, ` +
        `NULL, '2025-09-01 11:30:00', '1', '2025-09-01 11:30:00', ` +
        `'his', NULL, NULL, ${escapeSqlVal(orgId)}, ` +
        `NULL, '', NULL, ${escapeSqlVal(insTpl.details)}, ` +
        `${escapeSqlVal(insTpl.result)}, NULL, '', 1, '2025-09-01 11:30:00');`

      sqlLines.push(sqlExamine)
      sqlLines.push(sqlExamineDetail)
      sqlLines.push(sqlInspection)
      rawStatements.push(sqlExamine)
      rawStatements.push(sqlExamineDetail)
      rawStatements.push(sqlInspection)
      generatedExamines++
    }
    sqlLines.push('')
  }

  // 5. 生成简版医嘱数据
  if (createAdvice && adviceCount > 0) {
    sqlLines.push(`-- 5. 简版医嘱表数据 (nr_simple_doctor_advice_info) 共 ${adviceCount} 条 --`)

    for (let i = 0; i < adviceCount; i++) {
      const pid = getTargetPatientId(advicePatientId, i)
      const advTpl = DOCTOR_ADVICE_TEMPLATES[i % DOCTOR_ADVICE_TEMPLATES.length]

      const recordId = `2026${generateNumericId(9)}`
      const doctorAdviceId = `${Date.now().toString().slice(-6)}${String(i).padStart(3, '0')}`

      const sqlAdvice = `${insertCmd} \`YHDB\`.\`nr_simple_doctor_advice_info\`(` +
        `\`id\`, \`doctor_advice_id\`, \`patient_id\`, \`org_id\`, \`dept_id\`, ` +
        `\`field1\`, \`field2\`, \`field3\`, \`field4\`, \`field5\`, \`field6\`, \`field7\`, \`field8\`, \`field9\`, \`field10\`, ` +
        `\`execute_status\`, \`remark\`, \`ext_json\`, \`status\`, \`creator\`, \`create_time\`, \`modify\`, \`update_time\`` +
        `) VALUES (` +
        `${escapeSqlVal(recordId)}, ${escapeSqlVal(doctorAdviceId)}, ${escapeSqlVal(pid)}, ${escapeSqlVal(orgId)}, ${escapeSqlVal(effectiveDeptId)}, ` +
        `${escapeSqlVal(advTpl.field1)}, NULL, ${escapeSqlVal(advTpl.field3)}, ${escapeSqlVal(advTpl.field4)}, ${escapeSqlVal(advTpl.field5)}, ${escapeSqlVal(advTpl.field6)}, ${escapeSqlVal(advTpl.field7)}, ${escapeSqlVal(advTpl.field8)}, ${escapeSqlVal(advTpl.field9)}, '2025-09-01 09:00:00', ` +
        `0, NULL, NULL, 0, ${escapeSqlVal(advTpl.creator)}, '2025-09-01 09:00:00', NULL, NULL);`

      sqlLines.push(sqlAdvice)
      rawStatements.push(sqlAdvice)
      generatedAdvices++
    }
    sqlLines.push('')
  }

  // 6. 生成手术部分数据
  if (createOperation && operationCount > 0) {
    sqlLines.push(`-- 6. 手术数据 (bn_operation) 共 ${operationCount} 条 --`)

    for (let i = 0; i < operationCount; i++) {
      const pid = getTargetPatientId(operationPatientId, i)
      const opTpl = OPERATION_TEMPLATES[i % OPERATION_TEMPLATES.length]

      const operationId = generateUUID()

      const sqlOp = `${insertCmd} \`YHDB\`.\`bn_operation\`(` +
        `\`operation_id\`, \`patient_id\`, \`operation_time\`, \`preoperative_diagnosis\`, ` +
        `\`operation_project\`, \`operation_dept\`, \`operation_dept_name\`, \`operation_level\`, ` +
        `\`anesthesia_mode\`, \`operation_surgeon\`, \`operation_surgeon_name\`, \`anesthesia_surgeon\`, ` +
        `\`anesthesia_surgeon_name\`, \`first_mate\`, \`first_mate_name\`, \`operation_status\`, ` +
        `\`dept_id\`, \`org_id\`, \`desc\`` +
        `) VALUES (` +
        `${escapeSqlVal(operationId)}, ${escapeSqlVal(pid)}, '2025-09-01 14:00:00', ${escapeSqlVal(opTpl.diagnosis)}, ` +
        `${escapeSqlVal(opTpl.project)}, NULL, NULL, NULL, ` +
        `NULL, NULL, NULL, NULL, ` +
        `NULL, NULL, NULL, ${escapeSqlVal(opTpl.status)}, ` +
        `${escapeSqlVal(effectiveDeptId)}, ${escapeSqlVal(orgId)}, NULL);`

      sqlLines.push(sqlOp)
      rawStatements.push(sqlOp)
      generatedOperations++
    }
    sqlLines.push('')
  }

  const sqlText = sqlLines.join('\n')
  const summaryText = `===== 造数生成成功摘要 =====
目标机构 (orgId): ${orgId}
目标护理单元名称: ${effectiveDeptName}
目标护理单元写入字段 (dept_id): ${effectiveDeptId} (${useDeptKey && deptKey ? '科室Key模式' : '部门deptId模式'})
患者数据生成: ${generatedPatients} 条 (床号: 1, 2, 3...)
看板数据生成: ${generatedBoards > 0 ? `已生成 (bo_switch & td_device | touch_mode=${boardTouchMode}: ${boardTouchMode === 1 ? '触屏' : '非触屏'})` : '未勾选'}
费用相关生成: ${generatedFees > 0 ? `已生成 (${generatedFees} 组)` : '未勾选'}
检查检验生成: ${generatedExamines > 0 ? `已生成 (${generatedExamines} 组)` : '未勾选'}
简版医嘱生成: ${generatedAdvices > 0 ? `已生成 (${generatedAdvices} 条)` : '未勾选'}
手术数据生成: ${generatedOperations > 0 ? `已生成 (${generatedOperations} 条)` : '未勾选'}
遇重防护: ${useIgnore ? '已开启 (INSERT IGNORE)' : '关闭'}
SQL 总行数: ${sqlLines.length} 行`

  return {
    sqlText,
    rawStatements,
    summaryText,
    patientCountGenerated: generatedPatients,
    boardCountGenerated: generatedBoards,
    feeCountGenerated: generatedFees,
    examineCountGenerated: generatedExamines,
    adviceCountGenerated: generatedAdvices,
    operationCountGenerated: generatedOperations,
  }
}
