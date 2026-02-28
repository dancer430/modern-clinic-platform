<script setup lang="ts">
import { onMounted } from 'vue'
import { usePlatformBrand } from '@/composables/usePlatformBrand'

withDefaults(
  defineProps<{
    size?: 'sm' | 'md' | 'lg'
    monochrome?: boolean
  }>(),
  {
    size: 'md',
    monochrome: false,
  }
)

const { platformName, logoData, hasCustomLogo, loadPlatformBrand } = usePlatformBrand()

onMounted(async () => {
  await loadPlatformBrand()
})
</script>

<template>
  <div class="brand-logo" :class="[`size-${size}`, { monochrome }]" :aria-label="`${platformName} logo`">
    <img v-if="hasCustomLogo" :src="logoData" alt="platform logo" class="brand-logo-image" />
    <svg v-else viewBox="0 0 96 96" role="img" aria-hidden="true">
      <defs>
        <linearGradient id="brandGradient" x1="10%" y1="12%" x2="88%" y2="92%">
          <stop offset="0%" stop-color="#5f86ff" />
          <stop offset="100%" stop-color="#2e57db" />
        </linearGradient>
      </defs>
      <rect x="8" y="8" width="80" height="80" rx="22" fill="url(#brandGradient)" />
      <circle cx="48" cy="48" r="21" fill="rgba(255,255,255,0.14)" />
      <path
        d="M48 27.5c4.2 0 7.8 2.7 9 6.6h7.4v8.4H57v7.5h-8.3v-7.5h-7.5v-8.4h7.5v-6.6z"
        fill="#ffffff"
      />
      <circle cx="68" cy="66" r="7.5" fill="#f8fbff" />
      <path d="M64.8 66h6.4" stroke="#2e57db" stroke-width="2.2" stroke-linecap="round" />
      <path d="M68 62.8v6.4" stroke="#2e57db" stroke-width="2.2" stroke-linecap="round" />
    </svg>
    <span class="wordmark">
      <strong>{{ platformName }}</strong>
      <small>Smart Clinical Booking</small>
    </span>
  </div>
</template>
