import { createApp } from 'vue'

import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'

import App from './App.vue'
import { useAuth } from './composables/useAuth'
import { i18n } from './i18n'
import './style.css'

const app = createApp(App)

app.use(PrimeVue, {
  theme: {
    preset: Aura,
  },
})

app.use(i18n)

const { refreshAuth } = useAuth()
void refreshAuth()

app.mount('#app')
