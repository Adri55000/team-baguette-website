import { ref } from 'vue'
import { getAuthStatus, logoutRequest, type AuthStatus } from '../services/auth'

type AuthState = 'loading' | 'connected' | 'disconnected' | 'error'

// Ces variables sont partagées entre les composants.
const authState = ref<AuthState>('loading')
const currentUser = ref<Extract<AuthStatus, { authenticated: true }> | null>(null)

async function refreshAuth() {
  authState.value = 'loading'

  try {
    const result = await getAuthStatus()

    if (result.authenticated) {
      currentUser.value = result
      authState.value = 'connected'
    } else {
      currentUser.value = null
      authState.value = 'disconnected'
    }
  } catch (error) {
    console.error('Erreur authentification :', error)
    currentUser.value = null
    authState.value = 'error'
  }
}

function loginWithDiscord() {
  window.location.assign('/api/auth/discord/login')
}

async function logout() {
  try {
    await logoutRequest()
  } catch (error) {
    console.error('Erreur de déconnexion :', error)
  } finally {
    await refreshAuth()
  }
}

export function useAuth() {
  return {
    authState,
    currentUser,
    refreshAuth,
    loginWithDiscord,
    logout,
  }
}
