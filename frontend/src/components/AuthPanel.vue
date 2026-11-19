<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'

import { useAuth } from '../composables/useAuth'

const { t } = useI18n({ useScope: 'global' })

const {
  authState,
  currentUser,
  refreshAuth,
  loginWithDiscord,
  logout,
} = useAuth()

</script>


<template>
  <div class="rounded-lg border p-4 space-y-2">
    <h2 class="font-bold">{{ t('auth.title') }}</h2>

    <p v-if="authState === 'loading'">
      {{ t('auth.loading') }}
    </p>

    <div
      v-else-if="authState === 'connected' && currentUser"
      class="flex items-center gap-3"
    >
      <img
        v-if="currentUser.avatar_url"
        :src="currentUser.avatar_url"
        alt=""
        class="h-12 w-12 rounded-full object-cover"
        referrerpolicy="no-referrer"
      />

      <div
        v-else
        class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-200 text-gray-700"
        aria-hidden="true"
      >
        ?
      </div>

      <div>
        <p class="font-semibold">
          {{ currentUser.display_name }}
        </p>
        <p class="text-sm opacity-70">
          {{ t('auth.connected', { id: currentUser.user_id }) }}
        </p>
      </div>
    </div>

    <p v-else-if="authState === 'disconnected'">
      {{ t('auth.disconnected') }}
    </p>

    <p v-else-if="authState === 'error'">
      {{ t('auth.error') }}
    </p>

    <div class="flex flex-wrap gap-2">
      <Button
        v-if="authState === 'disconnected'"
        :label="t('auth.login')"
        @click="loginWithDiscord"
      />

      <Button
        v-else-if="authState === 'connected'"
        :label="t('auth.logout')"
        severity="secondary"
        @click="logout"
      />

      <Button
        :label="t('app.refresh')"
        severity="secondary"
        outlined
        @click="refreshAuth"
      />
    </div>
  </div>
</template>
