<script setup lang="ts">
import { ref } from 'vue'

const ranges = ['Last 7 days', 'Last 30 days', 'Quarter']
const selectedRange = ref(ranges[1])

const kpis = ref([
  { label: 'Patients Growth', value: '+14%', hint: 'vs previous period' },
  { label: 'Doctor Utilization', value: '78%', hint: 'average per doctor' },
  { label: 'Appointment Completion', value: '91%', hint: 'successful check-ins' },
  { label: 'No-show Rate', value: '6.2%', hint: 'needs follow-up' },
])

const departments = ref([
  { name: 'Cardiology', visits: 136 },
  { name: 'Neurology', visits: 94 },
  { name: 'Pediatrics', visits: 82 },
  { name: 'Dermatology', visits: 67 },
])
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div>
        <h2>Analytics</h2>
        <p>Operational insights for your healthcare team.</p>
      </div>
      <el-select v-model="selectedRange" style="width: 180px">
        <el-option v-for="item in ranges" :key="item" :label="item" :value="item" />
      </el-select>
    </section>

    <section class="stats-grid">
      <el-card v-for="item in kpis" :key="item.label" class="stat-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </el-card>
    </section>

    <el-card class="table-card">
      <template #header>
        <h3>Department Performance</h3>
      </template>
      <el-table :data="departments" style="width: 100%">
        <el-table-column prop="name" label="Department" />
        <el-table-column prop="visits" label="Visits" width="100" />
        <el-table-column label="Activity">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.min(Math.round(row.visits / 1.5), 100)"
              :show-text="false"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
}

.stat-card strong {
  font-size: 1.8em;
  margin: 8px 0 4px;
}

.stat-card small {
  color: var(--el-text-color-secondary);
}

.table-card {
  margin-top: 0;
}
</style>
