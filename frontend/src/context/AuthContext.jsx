import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../services/api'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    authApi.me().then((profile) => { if (active) setUser(profile) })
      .catch(() => { if (active) setUser(null) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const login = async (credentials) => {
    setLoading(true)
    try {
      await authApi.login(credentials)
      const profile = await authApi.me()
      setUser(profile)
      return profile
    } finally { setLoading(false) }
  }

  const loginWithGoogle = async (credential) => {
    setLoading(true)
    try {
      await authApi.googleLogin(credential)
      const profile = await authApi.me()
      setUser(profile)
      return profile
    } finally { setLoading(false) }
  }

  const signup = async (data) => {
    setLoading(true)
    try {
      const profile = await authApi.register(data)
      setUser(profile)
      return profile
    } finally { setLoading(false) }
  }

  const logout = async () => {
    try { await authApi.logout() } finally { setUser(null) }
  }

  return <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, loginWithGoogle, signup, logout, loading, setUser }}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
