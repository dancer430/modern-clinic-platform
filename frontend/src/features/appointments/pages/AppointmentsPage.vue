<script setup lang="ts">
import AppointmentsFilters from '../components/AppointmentsFilters.vue'
import AppointmentsPagination from '../components/AppointmentsPagination.vue'
import AppointmentsTableCard from '../components/AppointmentsTableCard.vue'
import CancelAppointmentDialog from '../components/CancelAppointmentDialog.vue'
import CompleteAppointmentDialog from '../components/CompleteAppointmentDialog.vue'
import ConfirmAppointmentDialog from '../components/ConfirmAppointmentDialog.vue'
import CreateAppointmentDialog from '../components/CreateAppointmentDialog.vue'
import { useAppointmentsPage } from '../composables/useAppointmentsPage'

const {
  applyListFilters,
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
  patients,
  removeCompleteAttachment,
  resetListFilters,
  search,
  showCancelDialog,
  showCompleteDialog,
  showConfirmDialog,
  showDialog,
  showSqliteAttachmentHint,
  slotOptions,
  status,
  statusTagType,
  submitComplete,
  submitConfirm,
  totalCount,
} = useAppointmentsPage()
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div>
        <h2>Appointments</h2>
        <p>Limited slots: 08:00-11:30 and 14:00-17:00 (every 30 minutes).</p>
      </div>
      <ElButton type="primary" @click="openCreate">+ New Appointment</ElButton>
    </section>

    <AppointmentsFilters
      :search="search"
      :status="status"
      @update:search="search = $event"
      @update:status="status = $event"
      @search="applyListFilters"
      @reset="resetListFilters"
    />

    <AppointmentsTableCard
      :loading="loading"
      :appointments="filtered"
      :status-tag-type="statusTagType"
      :can-confirm="canConfirm"
      :can-complete="canComplete"
      @confirm="openConfirmDialog"
      @cancel="openCancelDialog"
      @complete="openCompleteDialog"
    />

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
