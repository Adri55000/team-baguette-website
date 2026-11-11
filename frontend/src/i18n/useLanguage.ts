import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePrimeVue } from 'primevue/config'

import { en as primeEn } from 'primelocale/js/en.js'
import { fr as primeFr } from 'primelocale/js/fr.js'

import { saveLanguage, type SupportedLanguage } from './language'

export function useLanguage() {
  const { t, locale } = useI18n({ useScope: 'global' })
  const primevue = usePrimeVue()

  // Synchroniser PrimeVue et la langue du document
    watch(
      locale,
     (language) => {
        if (primevue.config.locale) {
         Object.assign(
           primevue.config.locale,
           language === 'fr' ? primeFr : primeEn
          )
        }

       document.documentElement.lang = language
      },
      { immediate: true }
    )

  // Changement explicite de langue
  function changeLanguage(language: SupportedLanguage) {
    locale.value = language
    saveLanguage(language)
  }

  return {
    t,
    locale,
    changeLanguage,
  }
}