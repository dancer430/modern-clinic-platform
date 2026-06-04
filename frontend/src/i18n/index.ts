import { computed, ref } from 'vue'
import { createI18n } from 'vue-i18n'
import elEn from 'element-plus/es/locale/lang/en'
import elZhCn from 'element-plus/es/locale/lang/zh-cn'

import en from './locales/en'
import zh from './locales/zh'

export type AppLocale = 'en' | 'zh'

const STORAGE_KEY = 'locale'

function detectLocale(): AppLocale {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'en' || saved === 'zh') return saved
  } catch {
    /* storage may be unavailable */
  }
  const nav = typeof navigator !== 'undefined' ? navigator.language : 'en'
  return nav && nav.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: detectLocale(),
  fallbackLocale: 'en',
  messages: { en, zh },
})

/** Reactive current locale, kept in sync with the i18n instance. */
export const currentLocale = ref<AppLocale>(i18n.global.locale.value as AppLocale)

/** Element Plus locale bundle that follows the app locale. */
export const elementLocale = computed(() => (currentLocale.value === 'zh' ? elZhCn : elEn))

export function setLocale(locale: AppLocale): void {
  i18n.global.locale.value = locale
  currentLocale.value = locale
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    /* ignore */
  }
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('lang', locale === 'zh' ? 'zh-CN' : 'en')
  }
}

// Apply the detected locale's <html lang> on load.
setLocale(currentLocale.value)
