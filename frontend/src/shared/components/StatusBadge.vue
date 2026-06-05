<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ status: string }>()
const { t } = useI18n()

const VARIANT: Record<string, string> = {
  pending: 'pending', confirmed: 'confirmed', completed: 'completed', cancelled: 'cancelled',
}
const variant = computed(() => VARIANT[props.status] ?? 'neutral')
const label = computed(() => t(`status.${props.status}`))
</script>

<template>
  <span class="status-pill" :data-variant="variant">{{ label }}</span>
</template>
