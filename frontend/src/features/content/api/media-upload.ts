import api from '@/shared/http/client'

export async function uploadMedia(file: File): Promise<string> {
  const data = new FormData()
  data.append('file', file)
  const res = await api.post<{ url: string }>('/api/media/upload/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data.url
}
