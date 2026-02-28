<script setup lang="ts">
import { computed, ref } from 'vue'

interface UploadItem {
  id: number
  name: string
  size: string
  uploadedAt: string
}

const selectedFile = ref<File | null>(null)
const note = ref('')
const uploads = ref<UploadItem[]>([])

const previewUrl = computed(() => {
  if (!selectedFile.value) return ''
  return URL.createObjectURL(selectedFile.value)
})

const chooseFile = (event: Event) => {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null
}

const upload = () => {
  if (!selectedFile.value) return
  uploads.value.unshift({
    id: Date.now(),
    name: selectedFile.value.name,
    size: `${Math.max(1, Math.round(selectedFile.value.size / 1024))} KB`,
    uploadedAt: new Date().toLocaleString(),
  })
  selectedFile.value = null
  note.value = ''
}
</script>

<template>
  <div class="page upload-page">
    <section class="toolbar">
      <div>
        <h2>Image Library</h2>
        <p>Upload and manage imaging files for consultations.</p>
      </div>
    </section>

    <section class="upload-grid">
      <article class="upload-card">
        <h3>Upload</h3>
        <input type="file" accept="image/*" @change="chooseFile" />
        <textarea v-model="note" placeholder="Add clinical note (optional)"></textarea>
        <div v-if="previewUrl" class="preview-wrap">
          <img :src="previewUrl" alt="preview" />
        </div>
        <button class="primary" @click="upload">Upload</button>
      </article>

      <article class="upload-card">
        <h3>Recent Uploads</h3>
        <ul class="upload-list">
          <li v-for="item in uploads" :key="item.id">
            <strong>{{ item.name }}</strong>
            <span>{{ item.size }} · {{ item.uploadedAt }}</span>
          </li>
          <li v-if="uploads.length === 0" class="empty">No uploaded images yet.</li>
        </ul>
      </article>
    </section>
  </div>
</template>
