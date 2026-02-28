import apiClient from '@/utils/apiClient'

export interface MedicalImage {
  id: number
  image_data: string
  image_format: string
  original_size: number
  compressed_size: number
  compression_ratio: number
  image_type: string
  description: string
  uploaded_at: string
}

export interface UploadResponse {
  message: string
  image: MedicalImage
  info: {
    original_size: string
    compressed_size: string
    compression_ratio: string
  }
}

export interface MedicalImageListResponse {
  count: number
  next: string | null
  previous: string | null
  results: MedicalImage[]
}

export const uploadMedicalImage = async (data: {
  image_data: string
  image_format: string
  original_size: number
  compressed_size: number
  compression_ratio: number
  image_type?: string
  description?: string
}): Promise<UploadResponse> => {
  const response = await apiClient.post<UploadResponse>('/api/images/upload/', data)
  return response.data
}

export const getMedicalImages = async (params?: {
  image_type?: string
  search?: string
}): Promise<MedicalImageListResponse> => {
  const response = await apiClient.get<MedicalImageListResponse>('/api/images/', { params })
  return response.data
}

export const deleteMedicalImage = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/images/${id}/`)
}
