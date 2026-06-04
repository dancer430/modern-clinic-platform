<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import httpClient from '@/shared/http'
import StatusBadge from '@/shared/components/StatusBadge.vue'

const { t } = useI18n()
const router = useRouter()

type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled'

interface PatientAppointment {
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

const loading = ref(false)
const appointments = ref<PatientAppointment[]>([])

const today = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
})

const upcomingAppointments = computed(() =>
  appointments.value
    .filter((item) => item.appointment_date >= today.value && item.status !== 'cancelled')
    .sort((a, b) => {
      const aKey = `${a.appointment_date} ${a.appointment_time}`
      const bKey = `${b.appointment_date} ${b.appointment_time}`
      return aKey.localeCompare(bKey)
    })
)

const fetchAppointments = async () => {
  loading.value = true
  try {
    const resp = await httpClient.get('/api/appointments/', { params: { page_size: 50 } })
    const data = resp.data as PaginatedResponse<PatientAppointment> | PatientAppointment[]
    appointments.value = Array.isArray(data) ? data : data.results
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('dashboard.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchAppointments()
})
</script>

<template>
  <div class="page patient-home-page">
    <section class="hero-row">
      <div>
        <h2>{{ t('patientHome.title') }}</h2>
        <p>{{ t('patientHome.subtitle') }}</p>
      </div>
      <el-button type="primary" @click="router.push('/portal/doctors')">
        {{ t('patientHome.book') }}
      </el-button>
    </section>

    <el-card class="panel upcoming-panel" shadow="never">
      <template #header>
        <h3>{{ t('patientHome.upcoming') }}</h3>
      </template>

      <template v-if="loading">
        <el-skeleton animated :rows="4" />
      </template>

      <template v-else-if="upcomingAppointments.length > 0">
        <ul class="appointment-list">
          <li
            v-for="item in upcomingAppointments"
            :key="item.id"
            class="appointment-row"
            :class="`row-${item.status}`"
          >
            <div class="appointment-info">
              <strong>{{ item.doctor_name }}</strong>
              <span>{{ item.appointment_date }} · {{ item.appointment_time.slice(0, 5) }}</span>
            </div>
            <StatusBadge kind="appointment" :status="item.status" />
          </li>
        </ul>
      </template>

      <el-empty v-else :description="t('patientHome.noUpcoming')" :image-size="80" />
    </el-card>
  </div>
</template>

<style scoped>
.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.hero-row h2 {
  margin: 0 0 4px;
}

.hero-row p {
  margin: 0;
  color: var(--muted, #5a6788);
  font-size: 14px;
}

.upcoming-panel {
  border-radius: 14px;
  border: 1px solid var(--line, #e2e8f0);
}

.appointment-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.appointment-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  background: #f8faff;
  border: 1px solid #e8edf8;
}

.appointment-row.row-confirmed {
  background: #f1f9ff;
  border-color: #b8dcf5;
}

.appointment-row.row-completed {
  background: #f1fdf6;
  border-color: #bde9ce;
}

.appointment-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.appointment-info strong {
  font-size: 14px;
  color: #1b2a4a;
}

.appointment-info span {
  font-size: 12px;
  color: #5a6788;
}
</style>
