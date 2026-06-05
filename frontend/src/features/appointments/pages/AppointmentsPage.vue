<script setup lang="ts">
import { computed, ref } from 'vue'
import AppointmentDetailDrawer from '../components/AppointmentDetailDrawer.vue'
import AppointmentsFilters from '../components/AppointmentsFilters.vue'
import AppointmentsPagination from '../components/AppointmentsPagination.vue'
import AppointmentsTableCard from '../components/AppointmentsTableCard.vue'
import CancelAppointmentDialog from '../components/CancelAppointmentDialog.vue'
import CompleteAppointmentDialog from '../components/CompleteAppointmentDialog.vue'
import ConfirmAppointmentDialog from '../components/ConfirmAppointmentDialog.vue'
import CreateAppointmentDialog from '../components/CreateAppointmentDialog.vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/features/auth/store'

import { useAppointmentsPage } from '../composables/useAppointmentsPage'
import type { AppointmentItem } from '../types'

const { t } = useI18n()
const authStore = useAuthStore()

const detailVisible = ref(false)
const selectedAppointment = ref<AppointmentItem | null>(null)

const openDetail = (row: AppointmentItem) => {
  selectedAppointment.value = row
  detailVisible.value = true
}

const isOperator = computed(() => authStore.user?.user_type === 'operator')

const pageTitle = computed(() =>
  authStore.user?.user_type === 'admin' || isOperator.value
    ? t('appointments.titleManage')
    : t('appointments.titleMine')
)

const canManage = computed(() => authStore.isAdmin || authStore.isDoctor)

const {
  applyListFilters,
  dateFilter,
  cancelAppointment,
  cancelDialogMessage,
  canComplete,
  canConfirm,
  closeCancelDialog,
  completeForm,
  completeFormInvalid,
  completeSubmitAttempted,
  completeUploaderDragging,
  confirmInfoForm,
  confirmInfoTooLong,
  createAppointment,
  createSubmitAttempted,
  displayName,
  doctorFilter,
  doctors,
  filtered,
  form,
  handlePageChange,
  handleSizeChange,
  loading,
  onCompleteAttachmentChange,
  onCompleteUploaderDrop,
  openCancelDialog,
  openCompleteDialog,
  openConfirmDialog,
  openCreate,
  page,
  pageSize,
  patientFilter,
  patients,
  removeCompleteAttachment,
  resetListFilters,
  setToday,
  showCancelDialog,
  showCompleteDialog,
  showConfirmDialog,
  showDialog,
  showSqliteAttachmentHint,
  slotOptions,
  status,
  submitComplete,
  submitConfirm,
  totalCount,
} = useAppointmentsPage()
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div class="page-header">
        <h2>{{ pageTitle }}</h2>
        <p v-if="!isOperator">{{ t('appointments.slotsHint') }}</p>
      </div>
      <ElButton v-if="canManage" type="primary" @click="openCreate">{{ t('appointments.newAppointment') }}</ElButton>
    </section>

    <AppointmentsFilters
      :doctor-id="doctorFilter"
      :patient-id="patientFilter"
      :doctors="doctors"
      :patients="patients"
      :status="status"
      :date="dateFilter"
      @update:doctor-id="doctorFilter = $event"
      @update:patient-id="patientFilter = $event"
      @update:status="status = $event"
      @update:date="dateFilter = $event"
      @search="applyListFilters"
      @reset="resetListFilters"
      @today="setToday"
    />

    <AppointmentsTableCard
      :loading="loading"
      :appointments="filtered"
      :can-confirm="canConfirm"
      :can-complete="canComplete"
      :can-manage="canManage"
      :can-cancel="!isOperator"
      @confirm="openConfirmDialog"
      @cancel="openCancelDialog"
      @complete="openCompleteDialog"
      @view="openDetail"
    />

    <AppointmentDetailDrawer v-model="detailVisible" :appointment="selectedAppointment" />

    <AppointmentsPagination
      :page="page"
      :page-size="pageSize"
      :total-count="totalCount"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <CreateAppointmentDialog
      v-model="showDialog"
      :create-submit-attempted="createSubmitAttempted"
      :form="form"
      :patients="patients"
      :doctors="doctors"
      :slot-options="slotOptions"
      :display-name="displayName"
      @update:create-submit-attempted="createSubmitAttempted = $event"
      @submit="createAppointment"
    />

    <ConfirmAppointmentDialog
      v-model="showConfirmDialog"
      :confirm-info="confirmInfoForm"
      :confirm-info-too-long="confirmInfoTooLong"
      @update:confirm-info="confirmInfoForm = $event"
      @submit="submitConfirm"
    />

    <CompleteAppointmentDialog
      v-model="showCompleteDialog"
      :complete-form="completeForm"
      :complete-submit-attempted="completeSubmitAttempted"
      :complete-form-invalid="completeFormInvalid"
      :complete-uploader-dragging="completeUploaderDragging"
      :show-sqlite-attachment-hint="showSqliteAttachmentHint"
      @update:complete-submit-attempted="completeSubmitAttempted = $event"
      @update:complete-uploader-dragging="completeUploaderDragging = $event"
      @attachment-change="onCompleteAttachmentChange"
      @attachment-drop="onCompleteUploaderDrop"
      @remove-attachment="removeCompleteAttachment"
      @submit="submitComplete"
    />

    <CancelAppointmentDialog
      v-model="showCancelDialog"
      :message="cancelDialogMessage"
      @close="closeCancelDialog"
      @confirm="cancelAppointment"
    />
  </div>
</template>
