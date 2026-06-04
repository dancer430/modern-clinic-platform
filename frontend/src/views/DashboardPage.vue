<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import httpClient from '@/shared/http'
import StatusBadge from '@/shared/components/StatusBadge.vue'

const { t } = useI18n()

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
  { label: t('dashboard.todaysAppointments'), value: todayAppointments.value.length, trend: `${today.value}`, tone: 'blue' },
  { label: t('dashboard.pendingToday'), value: pendingCount.value, trend: t('dashboard.needConfirmation'), tone: 'orange' },
  { label: t('dashboard.confirmedToday'), value: confirmedCount.value, trend: t('dashboard.readyForVisit'), tone: 'cyan' },
  {
    label: t('dashboard.completedToday'),
    value: completedCount.value,
    trend: t('dashboard.cancelledSuffix', { count: cancelledCount.value }),
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
    var(--status-pending-text) 0% ${statusSegments.value.pending}%,
    var(--status-confirmed-text) ${statusSegments.value.pending}% ${statusSegments.value.pending + statusSegments.value.confirmed}%,
    var(--status-completed-text) ${statusSegments.value.pending + statusSegments.value.confirmed}% ${statusSegments.value.pending + statusSegments.value.confirmed + statusSegments.value.completed}%,
    var(--status-cancelled-text) ${statusSegments.value.pending + statusSegments.value.confirmed + statusSegments.value.completed}% 100%
  )`,
}))

const statusLegend = computed(() => [
  { label: t('status.pending'), value: pendingCount.value, tone: 'pending' },
  { label: t('status.confirmed'), value: confirmedCount.value, tone: 'confirmed' },
  { label: t('status.completed'), value: completedCount.value, tone: 'completed' },
  { label: t('status.cancelled'), value: cancelledCount.value, tone: 'cancelled' },
])

const quickActions = computed(() => [
  {
    key: 'doctors',
    title: t('dashboard.manageDoctors'),
    description: t('dashboard.manageDoctorsDesc'),
    note: t('dashboard.accounts'),
    icon: 'DR',
    path: '/doctors',
  },
  {
    key: 'patients',
    title: t('dashboard.managePatients'),
    description: t('dashboard.managePatientsDesc'),
    note: t('dashboard.profiles'),
    icon: 'PT',
    path: '/patients',
  },
  {
    key: 'schedule',
    title: t('dashboard.openSchedule'),
    description: t('dashboard.openScheduleDesc'),
    note: t('dashboard.pendingNote', { count: pendingCount.value }),
    icon: 'SC',
    path: '/timeslots',
  },
])

const fetchDashboardData = async () => {
  loading.value = true
  try {
    const appointmentsResp = await httpClient.get('/api/appointments/', {
      params: { date: today.value, page_size: 50 },
    })
    const appointmentData = appointmentsResp.data as
      | PaginatedResponse<DashboardAppointment>
      | DashboardAppointment[]
    appointments.value = Array.isArray(appointmentData)
      ? appointmentData
      : appointmentData.results
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('dashboard.loadFailed'))
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
        <h2>{{ t('dashboard.title') }}</h2>
        <p>{{ t('dashboard.subtitle') }}</p>
      </div>
    </section>

    <template v-if="loading">
      <section class="stats-grid">
        <el-skeleton v-for="n in 4" :key="n" animated>
          <template #template>
            <div class="stat-card">
              <el-skeleton-item variant="text" style="width: 60%" />
              <el-skeleton-item variant="h1" style="width: 30%; margin-top: 12px" />
              <el-skeleton-item variant="text" style="width: 50%; margin-top: 8px" />
            </div>
          </template>
        </el-skeleton>
      </section>
      <section class="content-grid">
        <el-skeleton animated :rows="6" />
        <el-skeleton animated :rows="6" />
      </section>
    </template>

    <template v-else>
      <section class="stats-grid">
        <el-card
          v-for="item in stats"
          :key="item.label"
          class="stat-card"
          :class="`tone-${item.tone}`"
          shadow="hover"
          :body-style="{ padding: '20px' }"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.trend }}</small>
        </el-card>
      </section>

      <section class="content-grid">
        <el-card class="panel appointments-panel" shadow="never">
          <template #header>
            <div class="panel-header">
              <h3>{{ t('dashboard.todaySchedule') }}</h3>
              <el-button type="primary" link @click="router.push('/appointments')">{{ t('common.viewAll') }}</el-button>
            </div>
          </template>
          <ul v-if="todaySchedule.length > 0">
            <li v-for="item in todaySchedule" :key="item.id" :class="`row-${item.status}`">
              <div>
                <strong>{{ item.patient_name }}</strong>
                <span>{{ item.doctor_name }} · {{ item.appointment_time.slice(0, 5) }}</span>
              </div>
              <StatusBadge kind="appointment" :status="item.status" />
            </li>
          </ul>
          <el-empty v-else :description="t('dashboard.noUpcoming')" :image-size="80" />
        </el-card>

        <el-card class="panel side-panel" shadow="never">
          <section>
            <h3>{{ t('dashboard.statusDistribution') }}</h3>
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
            <h3>{{ t('dashboard.quickActions') }}</h3>
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
            <p class="pending-tip">{{ t('dashboard.waitingForConfirmation', { count: pendingCount }) }}</p>
          </section>
        </el-card>
      </section>
    </template>
  </div>
</template>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-card {
  border-radius: 14px;
  border: 1px solid var(--line);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(36, 60, 120, 0.1);
}

.stat-card :deep(.el-card__body) {
  display: grid;
  grid-template-rows: auto auto auto;
  gap: 8px;
  padding: 20px !important;
}

.stat-card :deep(.el-card__body) > span {
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.1px;
}

.stat-card :deep(.el-card__body) > strong {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.5px;
  color: #1b2a4a;
}

.stat-card :deep(.el-card__body) > small {
  font-size: 12px;
  color: #5a6788;
  line-height: 1.4;
}

.stat-card.tone-blue { background: #f4f8ff; border-color: #cddcf8; }
.stat-card.tone-orange { background: #fff8ef; border-color: #f3d7b4; }
.stat-card.tone-cyan { background: #f1f9ff; border-color: #b8dcf5; }
.stat-card.tone-green { background: #f1fdf6; border-color: #bde9ce; }

.stat-card.tone-orange :deep(.el-card__body) > strong { color: #b85f00; }
.stat-card.tone-cyan :deep(.el-card__body) > strong { color: #2b6fb6; }
.stat-card.tone-green :deep(.el-card__body) > strong { color: #1f8a5f; }
.stat-card.tone-blue :deep(.el-card__body) > strong { color: #2c52cc; }
</style>
