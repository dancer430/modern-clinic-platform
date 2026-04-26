<script setup lang="ts">
import type { CreateAppointmentForm, UserOption } from '../types'

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
    title="New Appointment"
    width="600px"
    :before-close="closeDialog"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <ElForm label-position="top">
      <ElFormItem label="Patient" required>
        <ElSelect
          v-model="form.patient"
          placeholder="Select patient"
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
      <ElFormItem label="Doctor" required>
        <ElSelect
          v-model="form.doctor"
          placeholder="Select doctor"
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
      <ElFormItem label="Date" required>
        <ElDatePicker
          v-model="form.date"
          type="date"
          placeholder="Pick a date"
          value-format="YYYY-MM-DD"
          style="width: 100%;"
          :class="{ 'is-error': createSubmitAttempted && !form.date }"
        />
      </ElFormItem>
      <ElFormItem label="Time Slot" required>
        <ElSelect
          v-model="form.time"
          placeholder="Select time slot"
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
      <ElFormItem label="Reason">
        <ElInput v-model="form.reason" type="textarea" :rows="3" placeholder="Reason" />
      </ElFormItem>
    </ElForm>

    <div class="slot-hint-card">
      <p>Booked count by time for selected doctor/date</p>
      <ul>
        <li v-for="slot in slotOptions" :key="slot.time">
          <span>{{ slot.time }}</span>
          <span>{{ slot.blocked ? 'Unavailable by schedule' : `${slot.booked} booked` }}</span>
        </li>
      </ul>
    </div>

    <template #footer>
      <ElButton @click="closeDialog">Cancel</ElButton>
      <ElButton type="primary" @click="emit('submit')">Create</ElButton>
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
