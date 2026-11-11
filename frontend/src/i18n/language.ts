export type SupportedLanguage = 'en' | 'fr'

const STORAGE_KEY = 'tb_language'

function normalizeLanguage(language: string): SupportedLanguage | null {
  const code = language.toLowerCase().split('-')[0]

  if (code === 'fr' || code === 'en') {
    return code
  }

  return null
}

export function getInitialLanguage(): SupportedLanguage {
  // 1. Choix enregistré dans le navigateur
  const saved = localStorage.getItem(STORAGE_KEY)

  if (saved === 'fr' || saved === 'en') {
    return saved
  }

  // 2. Langues préférées du navigateur
  for (const language of navigator.languages) {
    const normalized = normalizeLanguage(language)

    if (normalized) {
      return normalized
    }
  }

  // 3. Anglais par défaut
  return 'en'
}

export function saveLanguage(language: SupportedLanguage): void {
  localStorage.setItem(STORAGE_KEY, language)
}