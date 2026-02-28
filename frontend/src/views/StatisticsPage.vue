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
      <select v-model="selectedRange" class="range-select">
        <option v-for="item in ranges" :key="item" :value="item">{{ item }}</option>
      </select>
    </section>

    <section class="stats-grid">
      <article class="stat-card" v-for="item in kpis" :key="item.label">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="table-card">
      <h3>Department Performance</h3>
      <table>
        <thead>
          <tr>
            <th>Department</th>
            <th>Visits</th>
            <th>Activity</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in departments" :key="item.name">
            <td>{{ item.name }}</td>
            <td>{{ item.visits }}</td>
            <td>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: `${Math.min(item.visits / 1.5, 100)}%` }"></div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
