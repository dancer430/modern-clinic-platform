export const en = {
  appointments: {
    // Page header
    title: 'Appointments',
    titleManage: 'Appointments',
    titleMine: 'My Appointments',
    slotsHint: 'Limited slots: 08:00-11:30 and 14:00-17:00 (every 30 minutes).',
    newAppointment: '+ New Appointment',

    // Filters
    allStatus: 'All status',

    // Table columns
    colPatient: 'Patient',
    colDoctor: 'Doctor',
    colDate: 'Date',
    colStatus: 'Status',

    // Table row actions
    confirm: 'Confirm',
    complete: 'Complete',
    onlyResponsibleConfirm: 'Only responsible doctor can confirm',
    onlyResponsibleComplete: 'Only responsible doctor can complete',
    noAppointments: 'No appointments found',

    // Cancel dialog
    cancelTitle: 'Cancel Appointment',
    keepAppointment: 'Keep Appointment',
    confirmCancel: 'Confirm Cancel',

    // Confirm dialog
    confirmTitle: 'Confirm Appointment',
    confirmInfoHint: 'Record preliminary diagnosis as Confirm Info (max 500 chars).',
    confirmInfoPlaceholder: 'Enter preliminary diagnosis...',
    submitConfirm: 'Submit Confirm',

    // Complete dialog
    completeTitle: 'Complete Appointment',
    completeHint: 'Diagnosis Result and Treatment Plan are required.',
    diagnosisResult: 'Diagnosis Result',
    diagnosisResultPlaceholder: 'Enter diagnosis result',
    treatmentPlan: 'Treatment Plan',
    treatmentPlanPlaceholder: 'Enter treatment plan',
    medicalAdvice: 'Medical Advice',
    medicalAdvicePlaceholder: 'Enter medical advice',
    attachmentsImage: 'Attachments (image)',
    uploadAttachments: 'Upload attachments',
    uploadAttachmentsHint: 'Images only, auto-compressed before submit',
    sqliteAttachmentHint: 'Current environment is development (SQLite). Attachment submission will not take effect.',
    removeAttachment: 'Remove',
    createNextAppointment: 'Create next appointment after submit',
    submitComplete: 'Submit Complete',

    // Create dialog
    newAppointmentTitle: 'New Appointment',
    selectPatient: 'Select patient',
    selectDoctor: 'Select doctor',
    pickDate: 'Pick a date',
    timeSlot: 'Time Slot',
    selectTimeSlot: 'Select time slot',
    reason: 'Reason',
    bookedCountHint: 'Booked count by time for selected doctor/date',
    unavailableBySchedule: 'Unavailable by schedule',
    bookedCount: '{count} booked',
    create: 'Create',

    // Slot grid
    slotBooked: 'Booked',
    slotOff: 'Off',
    pickSlot: 'Pick a time slot',
    noSlotsForDay: 'No bookable slots for this day — open slots in the schedule first.',
    selectDoctorFirst: 'Select a doctor and date to see available slots.',

    // Drawer / filter
    detailTitle: 'Appointment detail',
    sectionPatient: 'Patient',
    sectionDoctor: 'Doctor',
    contactPhone: 'Phone',
    contactEmail: 'Email',
    fieldDateTime: 'Date & time',
    notProvided: 'Not provided',
    viewDetail: 'Detail',
    todayFilter: 'Today',
    dateFilter: 'Date',
    filterDoctor: 'Filter by doctor',
    filterPatient: 'Filter by patient',
  },
}

export const zh = {
  appointments: {
    // Page header
    title: '预约管理',
    titleManage: '预约管理',
    titleMine: '我的预约',
    slotsHint: '可预约时段有限：08:00-11:30 与 14:00-17:00（每 30 分钟一个时段）。',
    newAppointment: '+ 新建预约',

    // Filters
    allStatus: '全部状态',

    // Table columns
    colPatient: '患者',
    colDoctor: '医生',
    colDate: '日期',
    colStatus: '状态',

    // Table row actions
    confirm: '确认',
    complete: '完成就诊',
    onlyResponsibleConfirm: '仅接诊医生可确认',
    onlyResponsibleComplete: '仅接诊医生可完成',
    noAppointments: '暂无预约记录',

    // Cancel dialog
    cancelTitle: '取消预约',
    keepAppointment: '保留预约',
    confirmCancel: '确认取消',

    // Confirm dialog
    confirmTitle: '确认预约',
    confirmInfoHint: '将初步诊断记录为确认信息（最多 500 字）。',
    confirmInfoPlaceholder: '请输入初步诊断……',
    submitConfirm: '提交确认',

    // Complete dialog
    completeTitle: '完成就诊',
    completeHint: '诊断结果和治疗方案为必填项。',
    diagnosisResult: '诊断结果',
    diagnosisResultPlaceholder: '请输入诊断结果',
    treatmentPlan: '治疗方案',
    treatmentPlanPlaceholder: '请输入治疗方案',
    medicalAdvice: '医嘱',
    medicalAdvicePlaceholder: '请输入医嘱',
    attachmentsImage: '附件（图片）',
    uploadAttachments: '上传附件',
    uploadAttachmentsHint: '仅支持图片，提交前将自动压缩',
    sqliteAttachmentHint: '当前为开发环境（SQLite），附件提交不会实际生效。',
    removeAttachment: '移除',
    createNextAppointment: '提交后创建下一次预约',
    submitComplete: '提交完成',

    // Create dialog
    newAppointmentTitle: '新建预约',
    selectPatient: '选择患者',
    selectDoctor: '选择医生',
    pickDate: '选择日期',
    timeSlot: '就诊时段',
    selectTimeSlot: '选择就诊时段',
    reason: '就诊原因',
    bookedCountHint: '所选医生/日期各时段已预约数量',
    unavailableBySchedule: '排班不可约',
    bookedCount: '已约 {count} 人',
    create: '创建',

    // Slot grid
    slotBooked: '已约',
    slotOff: '停诊',
    pickSlot: '选择时段',
    noSlotsForDay: '该日无可约时段,请先在排班开放时段。',
    selectDoctorFirst: '请先选择医生和日期以查看可约时段。',

    // Drawer / filter
    detailTitle: '预约详情',
    sectionPatient: '患者',
    sectionDoctor: '医生',
    contactPhone: '电话',
    contactEmail: '邮箱',
    fieldDateTime: '日期时间',
    notProvided: '未填写',
    viewDetail: '详情',
    todayFilter: '今日',
    dateFilter: '日期',
    filterDoctor: '筛选医生',
    filterPatient: '筛选患者',
  },
}
