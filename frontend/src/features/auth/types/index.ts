export type Role = 'admin' | 'doctor' | 'patient' | 'operator'

export interface User {
  id: number
  username: string
  email: string
  name: string
  user_type: Role
  db_vendor?: 'sqlite' | 'postgresql' | string
  phone: string
  avatar_data?: string
  avatar_type?: string
  avatar_size?: number | null
}

export interface LoginCredentials {
  account: string
  password: string
}

export interface AuthSession {
  access: string
  refresh: string
  user: User
}

export interface RefreshResponse {
  access: string
  refresh?: string
}
