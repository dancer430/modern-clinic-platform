<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { DraftStatus } from '../types'

const props = defineProps<{ status: DraftStatus; published?: boolean }>()

const { t } = useI18n()

const label = computed(() => {
  switch (props.status) {
    case 'pending': return t('publishStatus.pendingReview')
    case 'approved': return props.published ? t('publishStatus.published') : t('publishStatus.approved')
    case 'rejected': return t('publishStatus.rejected')
    default: return props.published ? t('publishStatus.published') : t('publishStatus.draft')
  }
})

const variant = computed(() => {
  if (props.status === 'pending') return 'pending'
  if (props.status === 'rejected') return 'rejected'
  if (props.status === 'approved' || props.published) return 'published'
  return 'draft'
})
</script>

<template>
  <span class="status-pill" :data-variant="variant">{{ label }}</span>
</template>
