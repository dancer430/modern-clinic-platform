import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import { useAuthStore } from './stores/auth'
import './style.css'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// 从 localStorage 恢复认证状态
const authStore = useAuthStore()
authStore.loadFromStorage()

app.mount('#app')
