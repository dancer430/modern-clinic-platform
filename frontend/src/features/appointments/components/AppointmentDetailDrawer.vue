<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusBadge from '@/shared/components/StatusBadge.vue'
import type { AppointmentItem } from '../types'

const { t } = useI18n()

const props = defineProps<{
  modelValue: boolean
  appointment: AppointmentItem | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const dateTime = computed(() => {
  if (!props.appointment) return ''
  return `${props.appointment.appointment_date} · ${props.appointment.appointment_time.slice(0, 5)}`
})
</script>

<template>
  <ElDrawer
    :model-value="modelValue"
    :title="t('appointments.detailTitle')"
    size="420px"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <div v-if="appointment" class="detail-body">
      <div class="detail-header">
        <StatusBadge :status="appointment.status" />
      </div>

      <section class="detail-section">
        <h3 class="detail-section-title">{{ t('appointments.sectionPatient') }}</h3>
        <dl class="detail-rows">
          <div class="detail-row">
            <dt>{{ t('appointments.colPatient') }}</dt>
            <dd>{{ appointment.patient_name }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.contactPhone') }}</dt>
            <dd>{{ appointment.patient_phone || t('appointments.notProvided') }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.contactEmail') }}</dt>
            <dd>{{ appointment.patient_email || t('appointments.notProvided') }}</dd>
          </div>
        </dl>
      </section>

      <section class="detail-section">
        <h3 class="detail-section-title">{{ t('appointments.sectionDoctor') }}</h3>
        <dl class="detail-rows">
          <div class="detail-row">
            <dt>{{ t('appointments.colDoctor') }}</dt>
            <dd>{{ appointment.doctor_name }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.contactPhone') }}</dt>
            <dd>{{ appointment.doctor_phone || t('appointments.notProvided') }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.contactEmail') }}</dt>
            <dd>{{ appointment.doctor_email || t('appointments.notProvided') }}</dd>
          </div>
        </dl>
      </section>

      <section class="detail-section">
        <h3 class="detail-section-title">{{ t('appointments.fieldDateTime') }}</h3>
        <dl class="detail-rows">
          <div class="detail-row">
            <dt>{{ t('appointments.fieldDateTime') }}</dt>
            <dd>{{ dateTime }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.reason') }}</dt>
            <dd>{{ appointment.reason || t('appointments.notProvided') }}</dd>
          </div>
        </dl>
      </section>

      <section v-if="appointment.status === 'completed'" class="detail-section">
        <dl class="detail-rows">
          <div class="detail-row">
            <dt>{{ t('appointments.diagnosisResult') }}</dt>
            <dd>{{ appointment.diagnosis_result || t('appointments.notProvided') }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.treatmentPlan') }}</dt>
            <dd>{{ appointment.treatment_plan || t('appointments.notProvided') }}</dd>
          </div>
          <div class="detail-row">
            <dt>{{ t('appointments.medicalAdvice') }}</dt>
            <dd>{{ appointment.medical_advice || t('appointments.notProvided') }}</dd>
          </div>
        </dl>
      </section>
    </div>
  </ElDrawer>
</template>

<style scoped>
.detail-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.detail-header {
  display: flex;
  align-items: center;
}
.detail-section-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.detail-rows {
  margin: 0;
}
.detail-row {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--el-border-color-lighter, #ebeef5);
}
.detail-row:last-child {
  border-bottom: none;
}
.detail-row dt {
  flex: 0 0 96px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.detail-row dd {
  margin: 0;
  flex: 1;
  color: var(--el-text-color-primary);
  font-size: 13px;
  word-break: break-word;
  white-space: pre-wrap;
}
</style>
