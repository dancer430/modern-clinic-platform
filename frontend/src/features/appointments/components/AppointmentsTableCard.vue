<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { AppointmentItem } from '../types'

const { t } = useI18n()

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
      <ElTableColumn prop="patient_name" :label="t('appointments.colPatient')" />
      <ElTableColumn prop="doctor_name" :label="t('appointments.colDoctor')" />
      <ElTableColumn :label="t('appointments.colDate')">
        <template #default="{ row }">
          {{ row.appointment_date }} &middot; {{ row.appointment_time.slice(0, 5) }}
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('appointments.colStatus')" width="130">
        <template #default="{ row }">
          <ElTag :type="statusTagType(row.status)" size="small">{{ t('status.' + row.status) }}</ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('common.actions')" width="200">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <ElButton
              text
              :disabled="!canConfirm(row)"
              :title="canConfirm(row) ? '' : t('appointments.onlyResponsibleConfirm')"
              @click="emit('confirm', row.id)"
            >
              {{ t('appointments.confirm') }}
            </ElButton>
            <ElButton text type="danger" @click="emit('cancel', row.id)">{{ t('common.cancel') }}</ElButton>
          </template>
          <template v-else-if="row.status === 'confirmed'">
            <ElButton
              text
              :disabled="!canComplete(row)"
              :title="canComplete(row) ? '' : t('appointments.onlyResponsibleComplete')"
              @click="emit('complete', row.id)"
            >
              {{ t('appointments.complete') }}
            </ElButton>
          </template>
        </template>
      </ElTableColumn>
      <template #empty>
        <ElEmpty :description="t('appointments.noAppointments')" />
      </template>
    </ElTable>
  </section>
</template>
