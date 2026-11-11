<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import DatePicker from 'primevue/datepicker'
import { useLanguage } from './i18n/useLanguage'

const testDate = ref<Date | null>(new Date())

const compteur = ref(0)
const apiStatus = ref<'loading' | 'ok' | 'error'>('loading')

const { t, locale, changeLanguage } = useLanguage()


async function checkAPI() {
  try {
    const response = await fetch('/api/health')

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error('Unexpected API status')
    }

    apiStatus.value = 'ok'

  } catch (error) {
    console.error('Erreur API :', error)
    apiStatus.value = 'error'
  }
}

onMounted(checkAPI)
</script>

<template>
  <main class="mx-auto max-w-2xl p-8 space-y-6">

    <h1 class="text-3xl font-bold text-blue-600">
      Team Baguette V2 🥖
    </h1>

    <div class="flex gap-2">
      <Button
        label="Français"
        :outlined="locale !== 'fr'"
        @click="changeLanguage('fr')"
      />

      <Button
       label="English"
       :outlined="locale !== 'en'"
       @click="changeLanguage('en')"
      />
    </div>

    <div class="space-y-2">
      <DatePicker v-model="testDate" inline />
    </div>

    <p>{{ t('app.welcome') }}</p>

    <div class="flex items-center gap-4">
      <Button
         :label="t('app.testPrimeVue')"
         @click="compteur++"
      />

      <span>{{ t('app.clicks', { count: compteur }) }}</span>
    </div>

    <div class="rounded-lg border p-4 space-y-2">
      <h2 class="font-bold">{{ t('app.apiConnection') }}</h2>
      <p>
       {{ t('app.apiStatus') }} :
       {{ t(`app.statuses.${apiStatus}`) }}
      </p>

      <Button
       :label="t('app.refresh')"
       severity="secondary"
       @click="checkAPI"
      />
    </div>

  </main>
</template>
