<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { currentLocale, setLocale, type AppLocale } from '@/i18n'

const { t } = useI18n()

const current = computed(() => currentLocale.value)

const choose = (locale: AppLocale) => {
  if (locale !== currentLocale.value) setLocale(locale)
}
</script>

<template>
  <el-dropdown trigger="click" @command="choose">
    <button type="button" class="lang-trigger" :title="t('language.label')">
      <span class="lang-globe" aria-hidden="true">🌐</span>
      <span class="lang-current">{{ current === 'zh' ? t('language.zh') : t('language.en') }}</span>
    </button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="en" :class="{ 'is-active': current === 'en' }">
          {{ t('language.en') }}
        </el-dropdown-item>
        <el-dropdown-item command="zh" :class="{ 'is-active': current === 'zh' }">
          {{ t('language.zh') }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style scoped>
.lang-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(120, 140, 190, 0.35);
  background: rgba(255, 255, 255, 0.9);
  color: #2e3a59;
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.lang-trigger:hover {
  background: #fff;
  border-color: #3f67ea;
}
.lang-globe {
  font-size: 14px;
  line-height: 1;
}
:deep(.is-active) {
  color: #3f67ea;
  font-weight: 700;
}
</style>
