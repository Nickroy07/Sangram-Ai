const DEFAULT_API_BASE_URL = 'http://localhost:8000'
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '')
const REQUEST_TIMEOUT_MS = 30000
let refreshInFlight = null

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'API_FAILURE', retryable = false, details = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.retryable = retryable
    this.details = details
  }
}

export async function apiRequest(path, options = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs || REQUEST_TIMEOUT_MS)
  try {
    const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
    const storedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('sangram_token') : null
    const authHeaders = storedToken ? { Authorization: `Bearer ${storedToken}` } : {}
    const requestOptions = {
      ...options,
      credentials: 'include',
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...authHeaders,
        ...options.headers
      }
    }
    let response = await fetch(url, requestOptions)
    const isSessionEndpoint = /^\/api\/auth\/(?:login|register|logout|refresh)(?:\?|$)/.test(path)
    if (response.status === 401 && !isSessionEndpoint) {
      refreshInFlight ||= fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST', credentials: 'include', signal: controller.signal,
        headers: { Accept: 'application/json', ...authHeaders }
      }).then(async (refreshResponse) => {
        if (!refreshResponse.ok) return false
        const refreshedPayload = await refreshResponse.json().catch(() => null)
        if (refreshedPayload?.access_token && typeof localStorage !== 'undefined') {
          localStorage.setItem('sangram_token', refreshedPayload.access_token)
        }
        return true
      }).catch(() => false).finally(() => { refreshInFlight = null })
      if (await refreshInFlight) {
        const updatedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('sangram_token') : null
        if (updatedToken) {
          requestOptions.headers['Authorization'] = `Bearer ${updatedToken}`
        }
        response = await fetch(url, requestOptions)
      }
    }
    const payload = response.status === 204 ? null : await response.json().catch(() => null)
    if (!response.ok) {
      throw new ApiError(payload?.message || payload?.detail || `Request failed (${response.status}).`, {
        status: response.status,
        code: payload?.code || 'API_FAILURE',
        retryable: Boolean(payload?.retryable),
        details: payload?.details || null
      })
    }
    if (payload?.access_token && typeof localStorage !== 'undefined') {
      localStorage.setItem('sangram_token', payload.access_token)
    }
    if (path.includes('/api/auth/logout') && typeof localStorage !== 'undefined') {
      localStorage.removeItem('sangram_token')
    }
    return payload
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error.name === 'AbortError') throw new ApiError('The server took too long to respond. Please try again.', { code: 'TIMEOUT', retryable: true })
    throw new ApiError('Could not reach Sangram AI. Check that the backend is running and try again.', { code: 'NETWORK_OFFLINE', retryable: true })
  } finally {
    clearTimeout(timeout)
  }
}

export const apiBaseUrl = API_BASE_URL
