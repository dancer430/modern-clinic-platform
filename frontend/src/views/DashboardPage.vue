<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/utils/apiClient'

type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled'

interface DashboardAppointment {
  id: number
  patient_name: string
  doctor_name: string
  appointment_date: string
  appointment_time: string
  status: AppointmentStatus
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const appointments = ref<DashboardAppointment[]>([])

const today = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
})

const todayAppointments = computed(() =>
  appointments.value.filter((item) => item.appointment_date === today.value)
)

const pendingCount = computed(() => todayAppointments.value.filter((item) => item.status === 'pending').length)
const confirmedCount = computed(() => todayAppointments.value.filter((item) => item.status === 'confirmed').length)
const completedCount = computed(() => todayAppointments.value.filter((item) => item.status === 'completed').length)
const cancelledCount = computed(() => todayAppointments.value.filter((item) => item.status === 'cancelled').length)

const stats = computed(() => [
  { label: "Today's Appointments", value: todayAppointments.value.length, trend: `${today.value}`, tone: 'blue' },
  { label: 'Pending Today', value: pendingCount.value, trend: 'Need doctor confirmation', tone: 'orange' },
  { label: 'Confirmed Today', value: confirmedCount.value, trend: 'Ready for visit', tone: 'cyan' },
  {
    label: 'Completed Today',
    value: completedCount.value,
    trend: `${cancelledCount.value} cancelled`,
    tone: 'green',
  },
])

const todaySchedule = computed(() => {
  return todayAppointments.value
    .filter((item) => item.status !== 'cancelled')
    .sort((a, b) => `${a.appointment_date} ${a.appointment_time}`.localeCompare(`${b.appointment_date} ${b.appointment_time}`))
    .slice(0, 6)
})

const statusSegments = computed(() => {
  const total = todayAppointments.value.length || 1
  const p = (pendingCount.value / total) * 100
  const c = (confirmedCount.value / total) * 100
  const d = (completedCount.value / total) * 100
  const x = (cancelledCount.value / total) * 100
  return {
    pending: p,
    confirmed: c,
    completed: d,
    cancelled: x,
  }
})

const statusPieStyle = computed(() => ({
  background: `conic-gradient(
    #ed8936 0% ${statusSegments.value.pending}%,
    #3182ce ${statusSegments.value.pending}% ${statusSegments.value.pending + statusSegments.value.confirmed}%,
    #48bb78 ${statusSegments.value.pending + statusSegments.value.confirmed}% ${statusSegments.value.pending + statusSegments.value.confirmed + statusSegments.value.completed}%,
    #c2334a ${statusSegments.value.pending + statusSegments.value.confirmed + statusSegments.value.completed}% 100%
  )`,
}))

const statusLegend = computed(() => [
  { label: 'Pending', value: pendingCount.value, tone: 'pending' },
  { label: 'Confirmed', value: confirmedCount.value, tone: 'confirmed' },
  { label: 'Completed', value: completedCount.value, tone: 'completed' },
  { label: 'Cancelled', value: cancelledCount.value, tone: 'cancelled' },
])

const quickActions = computed(() => [
  {
    key: 'doctors',
    title: 'Manage Doctors',
    description: 'Update doctor accounts and profile data.',
    note: 'Accounts',
    icon: 'DR',
    path: '/doctors',
  },
  {
    key: 'patients',
    title: 'Manage Patients',
    description: 'Create and maintain patient account records.',
    note: 'Profiles',
    icon: 'PT',
    path: '/patients',
  },
  {
    key: 'schedule',
    title: 'Open Schedule',
    description: 'Adjust slot availability for upcoming sessions.',
    note: `${pendingCount.value} pending`,
    icon: 'SC',
    path: '/timeslots',
  },
])

const fetchDashboardData = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const appointmentsResp = await apiClient.get('/api/appointments/', {
      params: { date: today.value, page_size: 50 },
    })
    const appointmentData = appointmentsResp.data as
      | PaginatedResponse<DashboardAppointment>
      | DashboardAppointment[]
    appointments.value = Array.isArray(appointmentData)
      ? appointmentData
      : appointmentData.results
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to load dashboard data'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchDashboardData()
})
</script>

<template>
  <div class="page dashboard-page">
    <section class="hero-row">
      <div>
        <h2>Today Operations</h2>
        <p>Focus on today appointments and status distribution.</p>
      </div>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>

    <section class="stats-grid">
      <article v-for="item in stats" :key="item.label" class="stat-card" :class="`tone-${item.tone}`">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.trend }}</small>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel appointments-panel">
        <header>
          <h3>Today Schedule</h3>
          <a href="#" @click.prevent="router.push('/appointments')">View all</a>
        </header>
        <ul v-if="todaySchedule.length > 0">
          <li v-for="item in todaySchedule" :key="item.id" :class="`row-${item.status}`">
            <div>
              <strong>{{ item.patient_name }}</strong>
              <span>{{ item.doctor_name }} · {{ item.appointment_time.slice(0, 5) }}</span>
            </div>
            <span class="badge" :class="item.status">{{ item.status }}</span>
          </li>
        </ul>
        <p v-else style="margin: 0; color: #7f849a;">No upcoming appointments.</p>
      </article>

      <article class="panel side-panel">
        <section>
          <h3>Today Status Distribution</h3>
          <div class="status-pie-wrap">
            <div class="status-pie" :style="statusPieStyle"></div>
            <div class="status-legend">
              <div v-for="item in statusLegend" :key="item.label" class="status-legend-row">
                <span class="legend-dot" :class="`tone-${item.tone}`"></span>
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h3>Quick Actions</h3>
          <div class="quick-actions">
            <button
              v-for="action in quickActions"
              :key="action.key"
              type="button"
              class="quick-action-card"
              @click="router.push(action.path)"
            >
              <span class="quick-action-icon">{{ action.icon }}</span>
              <span class="quick-action-body">
                <strong>{{ action.title }}</strong>
                <small>{{ action.description }}</small>
              </span>
              <span class="quick-action-note">{{ action.note }}</span>
            </button>
          </div>
          <p class="pending-tip">{{ pendingCount }} appointments are waiting for confirmation today.</p>
          <p v-if="loading" class="pending-tip" style="margin-top: 4px;">Refreshing dashboard data...</p>
        </section>
      </article>
    </section>
  </div>
</template>
