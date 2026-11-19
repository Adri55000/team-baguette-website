export type AuthStatus =
  | {
      authenticated: false
    }
  | {
      authenticated: true
      user_id: number
      display_name: string
      discord_username: string
      avatar_url: string | null
    }


export async function getAuthStatus(): Promise<AuthStatus> {
  const response = await fetch('/api/auth/me', {
    credentials: 'same-origin',
  })

  if (!response.ok) {
    throw new Error('Unable to retrieve authentication status')
  }

  return response.json() as Promise<AuthStatus>
}

export async function logoutRequest(): Promise<void> {
  
    const response = await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
        'X-TB-Request': '1',
    },
    })


    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
    }
}
