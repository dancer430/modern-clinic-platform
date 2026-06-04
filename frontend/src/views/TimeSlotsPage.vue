<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import httpClient from '@/shared/http'
import { useAuthStore } from '@/features/auth'
import { currentLocale } from '@/i18n'

const { t } = useI18n()

const intlLocale = computed(() => (currentLocale.value === 'zh' ? 'zh-CN' : 'en-US'))

const SLOT_TIMES = [
  '08:00',
  '08:30',
  '09:00',
  '09:30',
  '10:00',
  '10:30',
  '11:00',
  '11:30',
  '14:00',
  '14:30',
  '15:00',
  '15:30',
  '16:00',
  '16:30',
  '17:00',
]

interface UserOption {
  id: number
  username: string
  name: string
}

interface ScheduleSlot {
  id: number
  doctor: number
  doctor_name: string
  slot_date: string
  slot_time: string
  is_available: boolean
}

interface AppointmentItem {
  id: number
  patient: number
  patient_name: string
  doctor: number
  appointment_date: string
  appointment_time: string
  status: string
  reason: string
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

type DayFilterStatus = 'all' | 'pending' | 'confirmed' | 'completed'

const authStore = useAuthStore()
const loading = ref(false)

const toLocalDateString = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const monthCursor = ref(new Date())
const selectedDate = ref(toLocalDateString(new Date()))
const selectedDoctorId = ref<number | null>(null)

const doctors = ref<UserOption[]>([])
const patients = ref<UserOption[]>([])
const scheduleSlots = ref<ScheduleSlot[]>([])
const appointments = ref<AppointmentItem[]>([])

// Monday-first localized weekday short names (Jan 2 2023 is a Monday).
const weekdayLabels = computed(() => {
  const fmt = new Intl.DateTimeFormat(intlLocale.value, { weekday: 'short' })
  return Array.from({ length: 7 }, (_, i) => fmt.format(new Date(2023, 0, 2 + i)))
})

const monthLabel = computed(() => new Intl.DateTimeFormat(intlLocale.value, { month: 'long', year: 'numeric' }).format(monthCursor.value))
const isAdminRole = computed(() => authStore.isAdmin)

const displayDoctorName = (doctor: UserOption) => doctor.name?.trim() || doctor.username

const activeDoctor = computed(() => {
  if (!selectedDoctorId.value) return null
  return doctors.value.find((doctor) => doctor.id === selectedDoctorId.value) || null
})

const displayUserName = (user: UserOption | null | undefined) => {
  if (!user) return '-'
  return user.name?.trim() || user.username
}

const patientNameMap = computed(() => {
  const map: Record<number, string> = {}
  patients.value.forEach((user) => {
    map[user.id] = displayUserName(user)
  })
  return map
})

const displayPatientName = (item: AppointmentItem) => patientNameMap.value[item.patient] || item.patient_name

const calendarCells = computed(() => {
  const year = monthCursor.value.getFullYear()
  const month = monthCursor.value.getMonth()
  const firstDay = (new Date(year, month, 1).getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7
  const cells: Array<{ date: string | null; day: number | null }> = []

  for (let i = 0; i < totalCells; i += 1) {
    const day = i - firstDay + 1
    if (day < 1 || day > daysInMonth) {
      cells.push({ date: null, day: null })
      continue
    }
    cells.push({ date: toLocalDateString(new Date(year, month, day)), day })
  }

  return cells
})

const blockedCountByDate = computed(() => {
  const map: Record<string, number> = {}
  if (!selectedDoctorId.value) return map
  SLOT_TIMES.forEach((time) => {
    calendarCells.value.forEach((cell) => {
      if (!cell.date) return
      const blocked = scheduleSlots.value.some(
        (slot) =>
          slot.doctor === selectedDoctorId.value &&
          slot.slot_date === cell.date &&
          slot.slot_time.slice(0, 5) === time &&
          slot.is_available === false
      )
      if (blocked) map[cell.date] = (map[cell.date] || 0) + 1
    })
  })
  return map
})

const appointmentStatsByDate = computed(() => {
  const map: Record<
    string,
    {
      total: number
      pending: number
      confirmed: number
      completed: number
    }
  > = {}

  if (!selectedDoctorId.value) return map

  appointments.value.forEach((item) => {
    if (item.doctor !== selectedDoctorId.value) return
    if (item.status === 'cancelled') return

    if (!map[item.appointment_date]) {
      map[item.appointment_date] = {
        total: 0,
        pending: 0,
        confirmed: 0,
        completed: 0,
      }
    }

    map[item.appointment_date].total += 1
    if (item.status === 'pending') map[item.appointment_date].pending += 1
    if (item.status === 'confirmed') map[item.appointment_date].confirmed += 1
    if (item.status === 'completed') map[item.appointment_date].completed += 1
  })

  return map
})

const slotRows = computed(() => {
  if (!selectedDoctorId.value) return []

  return SLOT_TIMES.map((time) => {
    const slot = scheduleSlots.value.find(
      (item) =>
        item.doctor === selectedDoctorId.value &&
        item.slot_date === selectedDate.value &&
        item.slot_time.slice(0, 5) === time
    )
    const blocked = slot ? !slot.is_available : false
    const booked = appointments.value.filter(
      (item) =>
        item.doctor === selectedDoctorId.value &&
        item.appointment_date === selectedDate.value &&
        item.appointment_time.slice(0, 5) === time &&
        item.status !== 'cancelled'
    ).length

    return { time, blocked, booked, slotId: slot?.id || null }
  })
})

const activeAppointments = computed(() => {
  if (!selectedDoctorId.value) return []
  return appointments.value.filter(
    (item) =>
      item.doctor === selectedDoctorId.value &&
      item.appointment_date === selectedDate.value &&
      item.status !== 'cancelled'
  )
})

const dayAppointmentSummary = computed(() => {
  const summary = {
    total: activeAppointments.value.length,
    pending: 0,
    confirmed: 0,
    completed: 0,
  }

  activeAppointments.value.forEach((item) => {
    if (item.status === 'pending') summary.pending += 1
    if (item.status === 'confirmed') summary.confirmed += 1
    if (item.status === 'completed') summary.completed += 1
  })

  return summary
})

const dayFilterStatus = ref<DayFilterStatus>('all')

const filteredActiveAppointments = computed(() => {
  if (dayFilterStatus.value === 'all') return activeAppointments.value
  return activeAppointments.value.filter((item) => item.status === dayFilterStatus.value)
})

const canEditSchedule = computed(() => authStore.isAdmin || authStore.isDoctor)
const selectedSlotTimes = ref<string[]>([])

const fetchDoctors = async () => {
  const response = await httpClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const fetchPatients = async () => {
  const response = await httpClient.get('/api/auth/patients/')
  patients.value = response.data
}

const fetchSlots = async () => {
  const response = await httpClient.get('/api/schedule-slots/')
  scheduleSlots.value = response.data
}

const fetchAppointments = async () => {
  const response = await httpClient.get('/api/appointments/')
  const data = response.data as PaginatedResponse<AppointmentItem> | AppointmentItem[]
  appointments.value = Array.isArray(data) ? data : data.results
}

const loadPageData = async () => {
  loading.value = true
  try {
    await Promise.all([fetchDoctors(), fetchPatients(), fetchSlots(), fetchAppointments()])
    if (!selectedDoctorId.value) {
      if (authStore.isDoctor) {
        selectedDoctorId.value = authStore.user?.id || doctors.value[0]?.id || null
      } else {
        selectedDoctorId.value = doctors.value[0]?.id || null
      }
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('schedule.loadFailed'))
  } finally {
    loading.value = false
  }
}

const goPrevMonth = () => {
  monthCursor.value = new Date(monthCursor.value.getFullYear(), monthCursor.value.getMonth() - 1, 1)
}

const goNextMonth = () => {
  monthCursor.value = new Date(monthCursor.value.getFullYear(), monthCursor.value.getMonth() + 1, 1)
}

const jumpToday = () => {
  const today = new Date()
  monthCursor.value = new Date(today.getFullYear(), today.getMonth(), 1)
  selectedDate.value = toLocalDateString(today)
}

const selectDate = (date: string | null) => {
  if (!date) return
  selectedDate.value = date
  selectedSlotTimes.value = []
  dayFilterStatus.value = 'all'
}

const toApiTime = (time: string) => `${time}:00`

const isSlotSelected = (time: string) => selectedSlotTimes.value.includes(time)

const toggleSlotSelection = (time: string) => {
  if (!canEditSchedule.value) return
  if (selectedSlotTimes.value.includes(time)) {
    selectedSlotTimes.value = selectedSlotTimes.value.filter((item) => item !== time)
    return
  }
  selectedSlotTimes.value = [...selectedSlotTimes.value, time]
}

const clearSlotSelection = () => {
  selectedSlotTimes.value = []
}

const applySelectedSlots = async (mode: 'available' | 'unavailable') => {
  if (!canEditSchedule.value || !selectedDoctorId.value || selectedSlotTimes.value.length === 0) return

  try {
    const requests: Array<Promise<unknown>> = []

    selectedSlotTimes.value.forEach((time) => {
      const row = slotRows.value.find((item) => item.time === time)
      if (!row) return

      if (mode === 'unavailable') {
        if (row.slotId) {
          if (!row.blocked) {
            requests.push(
              httpClient.patch(`/api/schedule-slots/${row.slotId}/`, {
                is_available: false,
              })
            )
          }
          return
        }

        requests.push(
          httpClient.post('/api/schedule-slots/', {
            doctor: selectedDoctorId.value,
            slot_date: selectedDate.value,
            slot_time: toApiTime(time),
            is_available: false,
          })
        )
        return
      }

      if (row.slotId && row.blocked) {
        requests.push(
          httpClient.patch(`/api/schedule-slots/${row.slotId}/`, {
            is_available: true,
          })
        )
      }
    })

    await Promise.all(requests)
    selectedSlotTimes.value = []
    await fetchSlots()
    ElMessage.success(t('schedule.slotsUpdated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('schedule.slotsUpdateFailed'))
  }
}

const statusTagType = (status: string) => {
  switch (status) {
    case 'pending': return 'warning'
    case 'confirmed': return ''
    case 'completed': return 'success'
    default: return 'info'
  }
}

onMounted(async () => {
  await loadPageData()
})
</script>

<template>
  <div class="page schedule-page" v-loading="loading">
    <section class="toolbar">
      <div>
        <h2>{{ t('schedule.title') }}</h2>
        <p>{{ t('schedule.subtitle') }}</p>
      </div>
      <el-button-group>
        <el-button @click="goPrevMonth">{{ t('schedule.prev') }}</el-button>
        <el-button @click="jumpToday">{{ t('schedule.today') }}</el-button>
        <el-button @click="goNextMonth">{{ t('schedule.next') }}</el-button>
      </el-button-group>
    </section>

    <section class="filters" v-if="isAdminRole">
      <el-select v-model="selectedDoctorId" :placeholder="t('schedule.selectDoctor')" style="width: 240px">
        <el-option
          v-for="doctor in doctors"
          :key="doctor.id"
          :label="displayDoctorName(doctor)"
          :value="doctor.id"
        />
      </el-select>
    </section>

    <section class="schedule-layout">
      <article class="table-card calendar-card">
        <header class="calendar-header">
          <h3>{{ monthLabel }}</h3>
        </header>

        <div class="calendar-weekdays">
          <span v-for="day in weekdayLabels" :key="day">{{ day }}</span>
        </div>

        <div class="calendar-grid">
          <button
            v-for="(cell, index) in calendarCells"
            :key="index"
            class="calendar-cell"
            :class="{ empty: !cell.date, active: cell.date === selectedDate }"
            @click="selectDate(cell.date)"
          >
            <span v-if="cell.day" class="day-label">{{ cell.day }}</span>
            <span v-if="cell.date && blockedCountByDate[cell.date]" class="slot-count">
              {{ t('schedule.blockedCount', { count: blockedCountByDate[cell.date] }) }}
            </span>
            <div v-if="cell.date && appointmentStatsByDate[cell.date]" class="appointment-stats">
              <span class="stats-total">{{ t('schedule.apptCount', { count: appointmentStatsByDate[cell.date].total }) }}</span>
              <span class="stats-split">
                <span class="stats-pending">P{{ appointmentStatsByDate[cell.date].pending }}</span>
                <span class="stats-confirmed">C{{ appointmentStatsByDate[cell.date].confirmed }}</span>
                <span class="stats-completed">D{{ appointmentStatsByDate[cell.date].completed }}</span>
              </span>
            </div>
          </button>
        </div>
      </article>

      <article class="table-card day-panel">
        <header>
          <h3>{{ activeDoctor ? displayDoctorName(activeDoctor) : '-' }}</h3>
          <div class="day-panel-header-right">
            <span>{{ selectedDate }}</span>
          </div>
        </header>

        <div class="day-appointments">
          <h4>{{ t('schedule.currentDayAppointments') }}</h4>
          <el-radio-group v-model="dayFilterStatus" size="small" class="day-summary-row">
            <el-radio-button value="all">
              {{ t('schedule.summaryTotal', { count: dayAppointmentSummary.total }) }}
            </el-radio-button>
            <el-radio-button value="pending">
              {{ t('schedule.summaryPending', { count: dayAppointmentSummary.pending }) }}
            </el-radio-button>
            <el-radio-button value="confirmed">
              {{ t('schedule.summaryConfirmed', { count: dayAppointmentSummary.confirmed }) }}
            </el-radio-button>
            <el-radio-button value="completed">
              {{ t('schedule.summaryCompleted', { count: dayAppointmentSummary.completed }) }}
            </el-radio-button>
          </el-radio-group>

          <el-empty
            v-if="filteredActiveAppointments.length === 0"
            :description="dayFilterStatus === 'all' ? t('schedule.noAppointments') : t('schedule.noStatusAppointments', { status: t('status.' + dayFilterStatus) })"
            :image-size="60"
          />
          <div v-else class="appointment-card-list">
            <article
              v-for="item in filteredActiveAppointments"
              :key="item.id"
              class="appointment-card"
              :class="`status-${item.status}`"
            >
              <header class="appointment-card-head">
                <div class="appointment-card-meta">
                  <span>{{ item.appointment_time.slice(0, 5) }}</span>
                  <span>·</span>
                  <span>{{ displayPatientName(item) }}</span>
                </div>
                <el-tag :type="statusTagType(item.status)" size="small" effect="dark">
                  {{ t('status.' + item.status) }}
                </el-tag>
              </header>
              <p class="appointment-card-reason">{{ item.reason || t('schedule.noReasonProvided') }}</p>
            </article>
          </div>
        </div>

        <section class="slot-card-section">
          <header class="slot-card-header">
            <h4>{{ t('schedule.availabilitySlots') }}</h4>
            <el-tag size="small" type="info">{{ t('schedule.selectedCount', { count: selectedSlotTimes.length }) }}</el-tag>
          </header>

          <div class="slot-card-toolbar" v-if="canEditSchedule">
            <button
              type="button"
              class="slot-action-btn action-unavailable"
              :disabled="selectedSlotTimes.length === 0"
              @click="applySelectedSlots('unavailable')"
            >
              {{ t('schedule.markUnavailable') }}
            </button>
            <button
              type="button"
              class="slot-action-btn action-available"
              :disabled="selectedSlotTimes.length === 0"
              @click="applySelectedSlots('available')"
            >
              {{ t('schedule.markAvailable') }}
            </button>
            <button
              type="button"
              class="slot-action-btn action-clear"
              :disabled="selectedSlotTimes.length === 0"
              @click="clearSlotSelection"
            >
              {{ t('schedule.clear') }}
            </button>
          </div>

          <el-empty
            v-if="slotRows.length === 0"
            :description="t('schedule.selectDoctorToViewSlots')"
            :image-size="60"
          />
          <div v-else class="time-chip-grid">
            <button
              v-for="row in slotRows"
              :key="row.time"
              type="button"
              class="time-chip"
              :class="{ selected: isSlotSelected(row.time), blocked: row.blocked }"
              :disabled="!canEditSchedule"
              @click="toggleSlotSelection(row.time)"
            >
              <strong>{{ row.time }}</strong>
              <small>{{ row.blocked ? t('schedule.slotUnavailable') : t('schedule.slotAvailable') }} · {{ t('schedule.slotBooked', { count: row.booked }) }}</small>
            </button>
          </div>
        </section>
      </article>
    </section>
  </div>
</template>

<style scoped>
.day-summary-row {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  margin-bottom: 14px;
}

.day-summary-row :deep(.el-radio-button) {
  width: 100%;
  min-width: 0;
  margin: 0;
}

.day-summary-row :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-width: 0;
  padding: 7px 10px !important;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1px;
  border-radius: 999px !important;
  border: 1px solid #d5dfef !important;
  background: #f7f9fd !important;
  color: #4a587c !important;
  box-shadow: none !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.day-summary-row :deep(.el-radio-button__inner:hover) {
  border-color: #b8c7e3 !important;
  background: #eef3fb !important;
  color: #2e3a59 !important;
}

.day-summary-row :deep(.el-radio-button.is-active .el-radio-button__inner),
.day-summary-row :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #3e66e9 0%, #3058d9 100%) !important;
  border-color: #3058d9 !important;
  color: #ffffff !important;
  box-shadow: 0 6px 14px rgba(48, 88, 217, 0.22) !important;
}

@media (min-width: 1480px) {
  .day-summary-row {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.slot-card-toolbar {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 8px;
  margin-bottom: 14px;
}

.slot-action-btn {
  border: 1px solid transparent;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1px;
  white-space: nowrap;
}

.slot-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
  filter: grayscale(0.2);
}

.slot-action-btn:disabled:hover {
  transform: none;
  box-shadow: none;
}

@media (max-width: 1180px) {
  .slot-card-toolbar {
    grid-template-columns: 1fr 1fr;
  }
  .slot-action-btn.action-clear {
    grid-column: 1 / -1;
  }
}
</style>
