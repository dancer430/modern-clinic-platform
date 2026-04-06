<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'

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

// Fix memory leak: revoke previous object URL when it changes
let previousUrl = ''
watch(previewUrl, (newUrl) => {
  if (previousUrl) URL.revokeObjectURL(previousUrl)
  previousUrl = newUrl
})
onUnmounted(() => {
  if (previousUrl) URL.revokeObjectURL(previousUrl)
})

const handleChange = (uploadFile: UploadFile) => {
  selectedFile.value = uploadFile.raw || null
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
  ElMessage.success('Image uploaded successfully')
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
      <el-card>
        <template #header>
          <h3>Upload</h3>
        </template>
        <el-upload
          drag
          :auto-upload="false"
          accept="image/*"
          :show-file-list="false"
          :on-change="handleChange"
        >
          <el-icon style="font-size: 40px; color: var(--el-text-color-placeholder)">
            <i class="el-icon-upload" />
          </el-icon>
          <div>Drop image here or <em>click to browse</em></div>
        </el-upload>

        <el-input
          v-model="note"
          type="textarea"
          placeholder="Add clinical note (optional)"
          :rows="3"
          style="margin-top: 16px"
        />

        <div v-if="previewUrl" class="preview-wrap">
          <el-image :src="previewUrl" alt="preview" fit="cover" style="max-height: 200px; width: 100%" />
        </div>

        <el-button type="primary" style="margin-top: 16px" @click="upload">Upload</el-button>
      </el-card>

      <el-card>
        <template #header>
          <h3>Recent Uploads</h3>
        </template>
        <ul v-if="uploads.length" class="upload-list">
          <li v-for="item in uploads" :key="item.id">
            <strong>{{ item.name }}</strong>
            <span>{{ item.size }} &middot; {{ item.uploadedAt }}</span>
          </li>
        </ul>
        <el-empty v-else description="No uploaded images yet." />
      </el-card>
    </section>
  </div>
</template>

<style scoped>
.upload-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.preview-wrap {
  margin-top: 16px;
}

.upload-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.upload-list li {
  display: flex;
  flex-direction: column;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.upload-list li:last-child {
  border-bottom: none;
}
</style>
