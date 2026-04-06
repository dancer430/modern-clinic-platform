<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/utils/apiClient'
import { useAuthStore } from '@/stores/auth'

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

const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const monthLabel = computed(() => new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(monthCursor.value))
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
  const response = await apiClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const fetchPatients = async () => {
  const response = await apiClient.get('/api/auth/patients/')
  patients.value = response.data
}

const fetchSlots = async () => {
  const response = await apiClient.get('/api/schedule-slots/')
  scheduleSlots.value = response.data
}

const fetchAppointments = async () => {
  const response = await apiClient.get('/api/appointments/')
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
    ElMessage.error(error.response?.data?.detail || 'Failed to load schedule data')
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
              apiClient.patch(`/api/schedule-slots/${row.slotId}/`, {
                is_available: false,
              })
            )
          }
          return
        }

        requests.push(
          apiClient.post('/api/schedule-slots/', {
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
          apiClient.patch(`/api/schedule-slots/${row.slotId}/`, {
            is_available: true,
          })
        )
      }
    })

    await Promise.all(requests)
    selectedSlotTimes.value = []
    await fetchSlots()
    ElMessage.success('Slot availability updated successfully')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to update selected slot availability')
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
        <h2>My Schedule</h2>
        <p>Doctors can mark time slots unavailable to prevent new appointments.</p>
      </div>
      <el-button-group>
        <el-button @click="goPrevMonth">Prev</el-button>
        <el-button @click="jumpToday">Today</el-button>
        <el-button @click="goNextMonth">Next</el-button>
      </el-button-group>
    </section>

    <section class="filters" v-if="isAdminRole">
      <el-select v-model="selectedDoctorId" placeholder="Select doctor" style="width: 240px">
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
              {{ blockedCountByDate[cell.date] }} blocked
            </span>
            <div v-if="cell.date && appointmentStatsByDate[cell.date]" class="appointment-stats">
              <span class="stats-total">{{ appointmentStatsByDate[cell.date].total }} appt</span>
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
          <h4>Current day appointments</h4>
          <el-radio-group v-model="dayFilterStatus" size="small" class="day-summary-row">
            <el-radio-button value="all">
              Total {{ dayAppointmentSummary.total }}
            </el-radio-button>
            <el-radio-button value="pending">
              Pending {{ dayAppointmentSummary.pending }}
            </el-radio-button>
            <el-radio-button value="confirmed">
              Confirmed {{ dayAppointmentSummary.confirmed }}
            </el-radio-button>
            <el-radio-button value="completed">
              Completed {{ dayAppointmentSummary.completed }}
            </el-radio-button>
          </el-radio-group>

          <el-empty
            v-if="filteredActiveAppointments.length === 0"
            :description="dayFilterStatus === 'all' ? 'No appointments yet.' : `No ${dayFilterStatus} appointments.`"
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
                  {{ item.status }}
                </el-tag>
              </header>
              <p class="appointment-card-reason">{{ item.reason || 'No reason provided' }}</p>
            </article>
          </div>
        </div>

        <section class="slot-card-section">
          <header class="slot-card-header">
            <h4>Availability Slots</h4>
            <el-tag size="small" type="info">{{ selectedSlotTimes.length }} selected</el-tag>
          </header>

          <div class="slot-card-toolbar" v-if="canEditSchedule">
            <el-button
              type="danger"
              size="small"
              :disabled="selectedSlotTimes.length === 0"
              @click="applySelectedSlots('unavailable')"
            >
              Set Selected Unavailable
            </el-button>
            <el-button
              type="success"
              size="small"
              :disabled="selectedSlotTimes.length === 0"
              @click="applySelectedSlots('available')"
            >
              Set Selected Available
            </el-button>
            <el-button
              size="small"
              :disabled="selectedSlotTimes.length === 0"
              @click="clearSlotSelection"
            >
              Clear Selection
            </el-button>
          </div>

          <el-empty
            v-if="slotRows.length === 0"
            description="Select a doctor to view slots."
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
              <small>{{ row.blocked ? 'unavailable' : 'available' }} · {{ row.booked }} booked</small>
            </button>
          </div>
        </section>
      </article>
    </section>
  </div>
</template>

<style scoped>
.day-summary-row {
  margin-bottom: 12px;
}
.slot-card-toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
</style>
