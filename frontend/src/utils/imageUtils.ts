import imageConversion from 'image-conversion'

export interface CompressionResult {
  base64: string
  originalSize: number
  compressedSize: number
  ratio: number
}

export const compressImage = async (
  file: File,
  maxSizeKB: number = 300,
  quality: number = 0.8,
  maxWidth: number = 1920,
  maxHeight: number = 1080
): Promise<CompressionResult> => {
  const compressedBlob = await imageConversion.compress(file, {
    quality,
    outputType: 'image/jpeg',
    maxWidth,
    maxHeight,
    maxSizeKB,
  })

  const base64String = await previewImage(compressedBlob)
  const originalSize = Math.round(file.size / 1024)
  const compressedSize = Math.round((base64String.length * 0.75) / 1024)
  const ratio = originalSize > 0 ? ((1 - compressedSize / originalSize) * 100).toFixed(1) : '0'

  return {
    base64: base64String,
    originalSize,
    compressedSize,
    ratio: parseFloat(ratio),
  }
}

export const previewImage = (file: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to preview image'))

    reader.readAsDataURL(file)
  })
}

export const getImageDimensions = (file: File): Promise<{ width: number; height: number }> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve({ width: img.width, height: img.height })
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to load image'))
    }

    img.src = url
  })
}

export const validateImageFile = (file: File): { valid: boolean; error?: string } => {
  const maxSize = 10 * 1024 * 1024
  const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']
  const validType = allowedTypes.includes(file.type)

  if (!validType) {
    return { valid: false, error: 'Only JPG, PNG, GIF formats are supported' }
  }

  if (file.size > maxSize) {
    return { valid: false, error: 'Image size cannot exceed 10MB' }
  }

  return { valid: true }
}
