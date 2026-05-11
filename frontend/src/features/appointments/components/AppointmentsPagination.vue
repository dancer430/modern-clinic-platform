<script setup lang="ts">
defineProps<{
  page: number
  pageSize: 10 | 20 | 50
  totalCount: number
}>()

const emit = defineEmits<{
  pageChange: [page: number]
  sizeChange: [size: number]
}>()
</script>

<template>
  <section class="table-card pagination-bar">
    <ElPagination
      :current-page="page"
      :page-size="pageSize"
      :total="totalCount"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      @current-change="(value) => emit('pageChange', value)"
      @size-change="(value) => emit('sizeChange', value)"
    />
  </section>
</template>
