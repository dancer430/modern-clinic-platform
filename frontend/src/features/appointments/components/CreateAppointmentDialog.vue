<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/features/auth'

import type { CreateAppointmentForm, UserOption } from '../types'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
  createSubmitAttempted: boolean
  form: CreateAppointmentForm
  patients: UserOption[]
  doctors: UserOption[]
  slotOptions: Array<{ time: string; blocked: boolean; booked: number; state: 'available' | 'booked' | 'unavailable'; label: string }>
  displayName: (user: UserOption) => string
}>()

const authStore = useAuthStore()
const isDoctorSelf = computed(() => authStore.user?.user_type === 'doctor')
const selfName = computed(() => authStore.user?.name || authStore.user?.username || '')

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
        <div v-if="isDoctorSelf" class="locked-field">{{ selfName }}</div>
        <ElSelect
          v-else
          v-model="form.doctor"
          :placeholder="t('appointments.selectDoctor')"
          style="width: 100%;"
          :class="{ 'is-error': createSubmitAttempted && !form.doctor }"
        >
          <ElOption v-for="doctor in doctors" :key="doctor.id" :label="displayName(doctor)" :value="doctor.id" />
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
      <ElFormItem :label="t('appointments.pickSlot')" required>
        <div class="slot-grid" :class="{ 'is-error': createSubmitAttempted && !form.time }">
          <template v-if="slotOptions.length">
            <button
              v-for="slot in slotOptions"
              :key="slot.time"
              type="button"
              class="slot-chip"
              :class="[`slot-chip--${slot.state}`, { 'slot-chip--selected': form.time === slot.time }]"
              :disabled="slot.state !== 'available'"
              @click="form.time = slot.time"
            >
              <span class="slot-chip__time">{{ slot.time }}</span>
              <span v-if="slot.state === 'booked'" class="slot-chip__tag">{{ t('appointments.slotBooked') }}</span>
              <span v-else-if="slot.state === 'unavailable'" class="slot-chip__tag">{{ t('appointments.slotOff') }}</span>
            </button>
          </template>
          <p v-else class="slot-empty">{{ form.doctor && form.date ? t('appointments.noSlotsForDay') : t('appointments.selectDoctorFirst') }}</p>
        </div>
      </ElFormItem>
      <ElFormItem :label="t('appointments.reason')">
        <ElInput v-model="form.reason" type="textarea" :rows="3" :placeholder="t('appointments.reason')" />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <ElButton @click="closeDialog">{{ t('common.cancel') }}</ElButton>
      <ElButton type="primary" @click="emit('submit')">{{ t('appointments.create') }}</ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
.slot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; width: 100%; }
.slot-grid.is-error { outline: 1px solid var(--danger-text); outline-offset: 4px; border-radius: 8px; }
.slot-chip {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 8px 6px; border-radius: var(--radius-control, 10px);
  border: 1px solid var(--line); background: #fff; cursor: pointer;
  font-size: 13px; color: var(--primary); transition: all .15s ease;
}
.slot-chip--available:hover { border-color: var(--primary); background: var(--primary-soft); }
.slot-chip--selected { background: var(--primary); border-color: var(--primary); color: #fff; }
.slot-chip--booked { background: var(--status-pending-bg); border-color: transparent; color: var(--status-pending-text); cursor: not-allowed; }
.slot-chip--unavailable { background: var(--status-neutral-bg); border-color: transparent; color: var(--muted); cursor: not-allowed; }
.slot-chip__tag { font-size: 10px; }
.slot-empty { color: var(--muted); font-size: 13px; margin: 4px 0; }
.locked-field { height: 32px; display: flex; align-items: center; padding: 0 10px; border-radius: var(--radius-control, 10px); background: var(--primary-soft); color: var(--primary); font-size: 13px; }
</style>
