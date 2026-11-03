<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'

const compteur = ref(0)
const apiStatus = ref('Chargement...')

async function checkAPI() {
  try {
    const response = await fetch('/api/health')

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()
    apiStatus.value = data.status

  } catch (error) {
    console.error('Erreur API :', error)
    apiStatus.value = 'Erreur de connexion'
  }
}

onMounted(checkAPI)
</script>

<template>
  <main class="mx-auto max-w-2xl p-8 space-y-6">

    <h1 class="text-3xl font-bold text-blue-600">
      Team Baguette V2 🥖
    </h1>

    <p>Notre environnement frontend fonctionne !</p>

    <div class="flex items-center gap-4">
      <Button
        label="Tester PrimeVue"
        @click="compteur++"
      />
      <span>Clics : {{ compteur }}</span>
    </div>

    <div class="rounded-lg border p-4 space-y-2">
      <h2 class="font-bold">Connexion à FastAPI</h2>
      <p>État de l'API : {{ apiStatus }}</p>

      <Button
        label="Actualiser"
        severity="secondary"
        @click="checkAPI"
      />
    </div>

  </main>
</template>
