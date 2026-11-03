<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'

const compteur = ref(0)
</script>

<template>
  <main class="mx-auto max-w-2xl p-8 space-y-6">

    <h1 class="text-3xl font-bold text-blue-600">
      Team Baguette V2 🥖
    </h1>

    <p class="text-lg">
      Notre environnement frontend fonctionne !
    </p>

    <div class="flex items-center gap-4">
      <Button
        label="Tester PrimeVue"
        @click="compteur++"
      />

      <span>
        Clics : {{ compteur }}
      </span>
    </div>

    <p class="text-sm text-gray-500">
      Vue 3 + TypeScript + Vite + PrimeVue + Tailwind
    </p>

  </main>
</template>
