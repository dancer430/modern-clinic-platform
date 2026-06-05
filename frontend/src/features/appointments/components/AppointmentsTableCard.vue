<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/shared/components/StatusBadge.vue'
import type { AppointmentItem } from '../types'

const { t } = useI18n()

defineProps<{
  loading: boolean
  appointments: AppointmentItem[]
  canConfirm: (item: AppointmentItem) => boolean
  canComplete: (item: AppointmentItem) => boolean
  canManage: boolean
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
      stripe
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
          <StatusBadge :status="row.status" />
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('common.actions')" width="220">
        <template #default="{ row }">
          <div class="row-actions">
            <template v-if="row.status === 'pending'">
              <ElButton
                type="primary"
                plain
                round
                size="small"
                :disabled="!canConfirm(row)"
                :title="canConfirm(row) ? '' : t('appointments.onlyResponsibleConfirm')"
                @click="emit('confirm', row.id)"
              >
                {{ t('appointments.confirm') }}
              </ElButton>
              <ElButton v-if="canManage" type="danger" plain round size="small" @click="emit('cancel', row.id)">
                {{ t('common.cancel') }}
              </ElButton>
            </template>
            <template v-else-if="row.status === 'confirmed'">
              <ElButton
                type="success"
                plain
                round
                size="small"
                :disabled="!canComplete(row)"
                :title="canComplete(row) ? '' : t('appointments.onlyResponsibleComplete')"
                @click="emit('complete', row.id)"
              >
                {{ t('appointments.complete') }}
              </ElButton>
            </template>
            <span v-else class="row-actions-empty">—</span>
          </div>
        </template>
      </ElTableColumn>
      <template #empty>
        <ElEmpty :description="t('appointments.noAppointments')" />
      </template>
    </ElTable>
  </section>
</template>

<style scoped>
.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}
.row-actions-empty {
  color: var(--el-text-color-placeholder);
}
</style>
