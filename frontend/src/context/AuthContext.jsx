import { createContext, useContext, useState } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('fs_user')
    return raw ? JSON.parse(raw) : null
  })

  async function login(email, password) {
    const res = await api.post('/auth/login', { email, password })
    api.setToken(res.access_token)
    const u = { role: res.role, companyId: res.company_id, fullName: res.full_name, email }
    localStorage.setItem('fs_user', JSON.stringify(u))
    setUser(u)
    return u
  }

  async function signup(companyName, fullName, email, password) {
    const res = await api.post('/auth/signup', { company_name: companyName, full_name: fullName, email, password })
    api.setToken(res.access_token)
    const u = { role: res.role, companyId: res.company_id, fullName: res.full_name, email }
    localStorage.setItem('fs_user', JSON.stringify(u))
    setUser(u)
    return u
  }

  function logout() {
    api.clearToken()
    localStorage.removeItem('fs_user')
    setUser(null)
  }

  // Central permission matrix mirrored from the backend for UI gating
  // (the backend is always the source of truth / real enforcement).
  const ROLE_PERMISSIONS = {
    admin: ['*'],
    finance_manager: ['view_all_financials', 'approve_expense', 'approve_invoice', 'generate_report', 'view_forecast', 'view_ai_insights', 'manage_budget', 'view_audit_log'],
    accountant: ['manage_transaction', 'manage_invoice', 'manage_expense', 'reconcile', 'generate_report'],
    viewer: ['view_permitted'],
  }

  function can(permission) {
    if (!user) return false
    const perms = ROLE_PERMISSIONS[user.role] || []
    return perms.includes('*') || perms.includes(permission)
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, can }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
