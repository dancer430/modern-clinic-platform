<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
  <div class="page">
    <h2>{{ t('patientHome.title') }}</h2>
    <p>{{ t('patientHome.subtitle') }}</p>
  </div>
</template>
