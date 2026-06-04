<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { CreateAppointmentForm, UserOption } from '../types'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
  createSubmitAttempted: boolean
  form: CreateAppointmentForm
  patients: UserOption[]
  doctors: UserOption[]
  slotOptions: Array<{ time: string; blocked: boolean; booked: number; label: string }>
  displayName: (user: UserOption) => string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:createSubmitAttempted': [value: boolean]
  submit: []
}>()

const closeDialog = () => {
  emit('update:modelValue', false)
  emit('update:createSubmitAttempted', false)
}
</script>

<template>
  <ElDialog
    :model-value="modelValue"
    :title="t('appointments.newAppointmentTitle')"
    width="600px"
    :before-close="closeDialog"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <ElForm label-position="top">
      <ElFormItem :label="t('appointments.colPatient')" required>
        <ElSelect
          v-model="form.patient"
          :placeholder="t('appointments.selectPatient')"
          style="width: 100%;"
          :class="{ 'is-error': createSubmitAttempted && !form.patient }"
        >
          <ElOption
            v-for="patient in patients"
            :key="patient.id"
            :label="displayName(patient)"
            :value="patient.id"
          />
        </ElSelect>
      </ElFormItem>
      <ElFormItem :label="t('appointments.colDoctor')" required>
        <ElSelect
          v-model="form.doctor"
          :placeholder="t('appointments.selectDoctor')"
          style="width: 100%;"
          :class="{ 'is-error': createSubmitAttempted && !form.doctor }"
        >
          <ElOption
            v-for="doctor in doctors"
            :key="doctor.id"
            :label="displayName(doctor)"
            :value="doctor.id"
          />
        </ElSelect>
      </ElFormItem>
      <ElFormItem :label="t('appointments.colDate')" required>
        <ElDatePicker
          v-model="form.date"
          type="date"
          :placeholder="t('appointments.pickDate')"
          value-format="YYYY-MM-DD"
          style="width: 100%;"
          :class="{ 'is-error': createSubmitAttempted && !form.date }"
        />
      </ElFormItem>
      <ElFormItem :label="t('appointments.timeSlot')" required>
        <ElSelect
          v-model="form.time"
          :placeholder="t('appointments.selectTimeSlot')"
          style="width: 100%;"
          :class="{ 'is-error': createSubmitAttempted && !form.time }"
        >
          <ElOption
            v-for="slot in slotOptions"
            :key="slot.time"
            :label="slot.label"
            :value="slot.time"
            :disabled="slot.blocked"
          />
        </ElSelect>
      </ElFormItem>
      <ElFormItem :label="t('appointments.reason')">
        <ElInput v-model="form.reason" type="textarea" :rows="3" :placeholder="t('appointments.reason')" />
      </ElFormItem>
    </ElForm>

    <div class="slot-hint-card">
      <p>{{ t('appointments.bookedCountHint') }}</p>
      <ul>
        <li v-for="slot in slotOptions" :key="slot.time">
          <span>{{ slot.time }}</span>
          <span>{{ slot.blocked ? t('appointments.unavailableBySchedule') : t('appointments.bookedCount', { count: slot.booked }) }}</span>
        </li>
      </ul>
    </div>

    <template #footer>
      <ElButton @click="closeDialog">{{ t('common.cancel') }}</ElButton>
      <ElButton type="primary" @click="emit('submit')">{{ t('appointments.create') }}</ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
.slot-hint-card {
  margin-top: 8px;
  padding: 12px;
  background: var(--el-fill-color-light, #f5f7fa);
  border-radius: 4px;
  font-size: 13px;
}
.slot-hint-card ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 4px;
}
.slot-hint-card li {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
}
</style>
