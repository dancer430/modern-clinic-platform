<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <div class="page">
    <h2>Doctor #{{ route.params.id }}</h2>
  </div>
</template>
