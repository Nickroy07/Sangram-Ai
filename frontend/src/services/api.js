import { apiBaseUrl, apiRequest } from './apiClient'

const json = (method, body) => ({ method, body: JSON.stringify(body) })

export const authApi = {
  login: (data) => apiRequest('/api/auth/login', json('POST', data)),
  googleLogin: (credential) => apiRequest('/api/auth/google', json('POST', { credential })),
  register: (data) => apiRequest('/api/auth/register', json('POST', data)),
  me: () => apiRequest('/api/users/me/profile'),
  logout: () => apiRequest('/api/auth/logout', json('POST', {})),
  verifyEmail: (code) => apiRequest('/api/auth/verify-email', json('POST', { code })),
  resendVerification: () => apiRequest('/api/auth/resend-verification', json('POST', {})),
  forgotPassword: (email) => apiRequest('/api/auth/forgot-password', json('POST', { email })),
  resetPassword: (token, newPassword) => apiRequest('/api/auth/reset-password', json('POST', { token, newPassword }))
}

export const supportApi = {
  contact: (data) => apiRequest('/api/support/contact', json('POST', data))
}

export const userApi = {
  updateProfile: (data) => apiRequest('/api/users/me/profile', json('PUT', data)),
  preferences: () => apiRequest('/api/users/me/preferences'),
  updatePreferences: (data) => apiRequest('/api/users/me/preferences', json('PUT', data)),
  completeOnboarding: (data) => apiRequest('/api/users/me/onboarding', json('PUT', data)),
  changePassword: (currentPassword, newPassword) => apiRequest('/api/auth/change-password', json('POST', { currentPassword, newPassword })),
  sessions: () => apiRequest('/api/auth/sessions')
}

export const catalogApi = {
  models: () => apiRequest('/api/models'),
  archetypes: () => apiRequest('/api/archetypes')
}

export const battlesApi = {
  create: (payload) => apiRequest('/api/battles', json('POST', payload)),
  get: (id) => apiRequest(`/api/battles/${encodeURIComponent(id)}`),
  history: (page = 1, pageSize = 50) => apiRequest(`/api/battles?page=${page}&page_size=${pageSize}`),
  remove: (id) => apiRequest(`/api/battles/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export const savedApi = {
  list: async () => (await apiRequest('/api/saved')).items || [],
  save: (data) => apiRequest('/api/saved', json('POST', data)),
  remove: (id) => apiRequest(`/api/saved/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export const billingApi = {
  plans: () => apiRequest('/api/billing/plans'),
  subscription: () => apiRequest('/api/billing/subscription'),
  checkout: (payload) => apiRequest('/api/billing/checkout', json('POST', payload)),
  invoices: () => apiRequest('/api/billing/invoices'),
  usage: () => apiRequest('/api/usage')
}

export function subscribeBattle(battleId, onEvent, onError) {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('sangram_token') : null
  const query = token ? `?token=${encodeURIComponent(token)}` : ''
  const source = new EventSource(`${apiBaseUrl}/api/battles/${encodeURIComponent(battleId)}/events${query}`, { withCredentials: true })
  const eventTypes = ['battle.stage', 'battle.message.start', 'battle.message.chunk', 'battle.message.done', 'battle.round.summary', 'battle.synthesis.start', 'battle.final', 'battle.error', 'battle.done']
  eventTypes.forEach((type) => source.addEventListener(type, (event) => {
    try { onEvent(type, JSON.parse(event.data)) } catch { onError(new Error('The battle stream returned an invalid event.')); source.close() }
  }))
  source.onerror = () => { source.close(); onError(new Error('The battle stream disconnected. Reload the battle to reconnect.')) }
  return () => source.close()
}
