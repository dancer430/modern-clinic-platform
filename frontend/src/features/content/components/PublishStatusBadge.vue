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
  <span class="status-badge" :data-variant="variant">{{ label }}</span>
</template>

<style scoped>
.status-badge { display: inline-flex; align-items: center; font-size: 12px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.status-badge[data-variant='published'] { background: #e6f4ea; color: #1e7a36; }
.status-badge[data-variant='pending'] { background: #fff6e2; color: #b27800; }
.status-badge[data-variant='rejected'] { background: #fdecee; color: #b1273a; }
.status-badge[data-variant='draft'] { background: #eef0f6; color: #5b6478; }
</style>
