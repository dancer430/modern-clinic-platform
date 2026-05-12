<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { DepartmentCard } from '../types'
import { portalDepartmentsApi } from '../api/departments'

const props = withDefaults(defineProps<{ intervalMs?: number; limit?: number }>(), {
  intervalMs: 4000,
  limit: 5,
})

const router = useRouter()
const items = ref<DepartmentCard[]>([])
const current = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const visible = computed(() => items.value[current.value])

const advance = () => {
  if (items.value.length === 0) return
  current.value = (current.value + 1) % items.value.length
}

const start = () => {
  if (timer) return
  timer = setInterval(advance, props.intervalMs)
}

const stop = () => {
  if (timer) clearInterval(timer)
  timer = null
}

const go = (idx: number) => {
  current.value = idx
}

const goTo = (slug: string) => {
  router.push(`/portal/departments/${slug}`)
}

onMounted(async () => {
  try {
    items.value = await portalDepartmentsApi.list(props.limit)
    start()
  } catch {
    // swallow — login page should still render without portal data
  }
})

onBeforeUnmount(stop)
</script>

<template>
  <div v-if="items.length" class="dept-carousel" @mouseenter="stop" @mouseleave="start">
    <div class="dept-carousel__card" @click="visible && goTo(visible.slug)">
      <h4>{{ visible?.name }}</h4>
      <p>{{ visible?.summary }}</p>
    </div>
    <div class="dept-carousel__dots">
      <button
        v-for="(item, idx) in items"
        :key="item.id"
        :class="{ active: idx === current }"
        :aria-label="`Show ${item.name}`"
        @click="go(idx)"
      />
    </div>
  </div>
</template>

<style scoped>
.dept-carousel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dept-carousel__card {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 14px;
  padding: 18px 22px;
  color: #fff;
  cursor: pointer;
  transition: background 0.18s ease;
}
.dept-carousel__card:hover {
  background: rgba(255, 255, 255, 0.2);
}
.dept-carousel__card h4 {
  margin: 0 0 6px;
  font-size: 16px;
}
.dept-carousel__card p {
  margin: 0;
  font-size: 13px;
  opacity: 0.85;
}
.dept-carousel__dots {
  display: flex;
  gap: 6px;
}
.dept-carousel__dots button {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 0;
  padding: 0;
  background: rgba(255, 255, 255, 0.4);
  cursor: pointer;
}
.dept-carousel__dots button.active {
  background: #fff;
}
</style>
