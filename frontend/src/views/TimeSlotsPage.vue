<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
const errorMessage = ref('')

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
  errorMessage.value = ''
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
    errorMessage.value = error.response?.data?.detail || 'Failed to load schedule data'
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
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to update selected slot availability'
  }
}

onMounted(async () => {
  await loadPageData()
})
</script>

<template>
  <div class="page schedule-page">
    <section class="toolbar">
      <div>
        <h2>My Schedule</h2>
        <p>Doctors can mark time slots unavailable to prevent new appointments.</p>
      </div>
      <div class="calendar-actions">
        <button class="ghost" @click="goPrevMonth">Prev</button>
        <button class="ghost" @click="jumpToday">Today</button>
        <button class="ghost" @click="goNextMonth">Next</button>
      </div>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>

    <section class="filters" v-if="isAdminRole">
      <input :value="activeDoctor ? displayDoctorName(activeDoctor) : '-'" readonly />
      <select v-model.number="selectedDoctorId">
        <option v-for="doctor in doctors" :key="doctor.id" :value="doctor.id">{{ displayDoctorName(doctor) }}</option>
      </select>
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
          <div class="day-summary-row">
            <button
              type="button"
              class="day-stat day-stat-total"
              :class="{ active: dayFilterStatus === 'all' }"
              @click="dayFilterStatus = 'all'"
            >
              Total {{ dayAppointmentSummary.total }}
            </button>
            <button
              type="button"
              class="day-stat day-stat-pending"
              :class="{ active: dayFilterStatus === 'pending' }"
              @click="dayFilterStatus = 'pending'"
            >
              Pending {{ dayAppointmentSummary.pending }}
            </button>
            <button
              type="button"
              class="day-stat day-stat-confirmed"
              :class="{ active: dayFilterStatus === 'confirmed' }"
              @click="dayFilterStatus = 'confirmed'"
            >
              Confirmed {{ dayAppointmentSummary.confirmed }}
            </button>
            <button
              type="button"
              class="day-stat day-stat-completed"
              :class="{ active: dayFilterStatus === 'completed' }"
              @click="dayFilterStatus = 'completed'"
            >
              Completed {{ dayAppointmentSummary.completed }}
            </button>
          </div>
          <p v-if="filteredActiveAppointments.length === 0">
            {{ dayFilterStatus === 'all' ? 'No appointments yet.' : `No ${dayFilterStatus} appointments.` }}
          </p>
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
                <span class="badge" :class="item.status">{{ item.status }}</span>
              </header>
              <p class="appointment-card-reason">{{ item.reason || 'No reason provided' }}</p>
            </article>
          </div>
        </div>

        <section class="slot-card-section">
          <header class="slot-card-header">
            <h4>Availability Slots</h4>
            <span>{{ selectedSlotTimes.length }} selected</span>
          </header>

          <div class="slot-card-toolbar" v-if="canEditSchedule">
            <button class="ghost slot-action-btn action-unavailable" :disabled="selectedSlotTimes.length === 0" @click="applySelectedSlots('unavailable')">
              Set Selected Unavailable
            </button>
            <button class="ghost slot-action-btn action-available" :disabled="selectedSlotTimes.length === 0" @click="applySelectedSlots('available')">
              Set Selected Available
            </button>
            <button class="ghost slot-action-btn action-clear" :disabled="selectedSlotTimes.length === 0" @click="clearSlotSelection">
              Clear Selection
            </button>
          </div>

          <div class="time-chip-grid">
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
