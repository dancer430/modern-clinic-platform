<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ kind: 'appointment' | 'publish'; status: string }>()
const { t } = useI18n()

const APPT_VARIANT: Record<string, string> = {
  pending: 'pending', confirmed: 'confirmed', completed: 'completed', cancelled: 'cancelled',
}
const PUBLISH_VARIANT: Record<string, string> = {
  published: 'completed', approved: 'completed', pending: 'pending',
  pendingReview: 'pending', rejected: 'cancelled', draft: 'neutral', none: 'neutral',
}
const PUBLISH_LABEL_KEY: Record<string, string> = {
  published: 'publishStatus.published', approved: 'publishStatus.approved',
  pending: 'publishStatus.pendingReview', pendingReview: 'publishStatus.pendingReview',
  rejected: 'publishStatus.rejected', draft: 'publishStatus.draft', none: 'publishStatus.draft',
}

const variant = computed(() =>
  props.kind === 'appointment' ? (APPT_VARIANT[props.status] ?? 'neutral') : (PUBLISH_VARIANT[props.status] ?? 'neutral'))
const label = computed(() =>
  props.kind === 'appointment' ? t(`status.${props.status}`) : t(PUBLISH_LABEL_KEY[props.status] ?? 'publishStatus.draft'))
</script>

<template>
  <span class="status-pill" :data-variant="variant">{{ label }}</span>
</template>
