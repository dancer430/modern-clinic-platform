<script setup lang="ts">
import type { AppointmentItem } from '../types'

defineProps<{
  loading: boolean
  appointments: AppointmentItem[]
  statusTagType: (status: AppointmentItem['status']) => string
  canConfirm: (item: AppointmentItem) => boolean
  canComplete: (item: AppointmentItem) => boolean
}>()

const emit = defineEmits<{
  confirm: [id: number]
  cancel: [id: number]
  complete: [id: number]
}>()
</script>

<template>
  <section class="table-card">
    <ElTable
      v-loading="loading"
      :data="appointments"
      style="width: 100%;"
    >
      <ElTableColumn prop="patient_name" label="Patient" />
      <ElTableColumn prop="doctor_name" label="Doctor" />
      <ElTableColumn label="Date">
        <template #default="{ row }">
          {{ row.appointment_date }} &middot; {{ row.appointment_time.slice(0, 5) }}
        </template>
      </ElTableColumn>
      <ElTableColumn label="Status" width="130">
        <template #default="{ row }">
          <ElTag :type="statusTagType(row.status)" size="small">{{ row.status }}</ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="Actions" width="200">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <ElButton
              text
              :disabled="!canConfirm(row)"
              :title="canConfirm(row) ? '' : 'Only responsible doctor can confirm'"
              @click="emit('confirm', row.id)"
            >
              Confirm
            </ElButton>
            <ElButton text type="danger" @click="emit('cancel', row.id)">Cancel</ElButton>
          </template>
          <template v-else-if="row.status === 'confirmed'">
            <ElButton
              text
              :disabled="!canComplete(row)"
              :title="canComplete(row) ? '' : 'Only responsible doctor can complete'"
              @click="emit('complete', row.id)"
            >
              Complete
            </ElButton>
          </template>
        </template>
      </ElTableColumn>
      <template #empty>
        <ElEmpty description="No appointments found" />
      </template>
    </ElTable>
  </section>
</template>
