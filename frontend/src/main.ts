import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'

import App from './App.vue'
import { setupAuth } from './features/auth'
import router from './router'
import { i18n } from './i18n'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)

// Wire shared/http ↔ features/auth and restore session from storage.
setupAuth()

app.mount('#app')
