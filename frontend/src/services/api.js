// In local dev, Vite proxies "/api" to the backend on :8000 (see vite.config.js).
// In production (Vercel), frontend and backend are on different domains, so
// VITE_API_BASE_URL must be set to the deployed backend's full URL, e.g.
// https://your-backend.onrender.com/api — set this in Vercel's project
// environment variables before building.
const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

function getToken() {
  return localStorage.getItem('fs_token')
}

async function request(path, { method = 'GET', body, params, isForm = false } = {}) {
  let url = `${BASE}${path}`
  if (params) {
    const qs = new URLSearchParams(params).toString()
    url += `?${qs}`
  }
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!isForm && body !== undefined) headers['Content-Type'] = 'application/json'

  const res = await fetch(url, {
    method,
    headers,
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    localStorage.removeItem('fs_token')
    window.location.href = '/login'
    throw new Error('Session expired')
  }

  const contentType = res.headers.get('content-type') || ''
  if (!res.ok) {
    const errBody = contentType.includes('application/json') ? await res.json() : await res.text()
    const message = typeof errBody === 'object' ? (errBody.detail || JSON.stringify(errBody)) : errBody
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }

  if (contentType.includes('application/json')) return res.json()
  return res
}

export const API_BASE = BASE

export const api = {
  get: (path, params) => request(path, { method: 'GET', params }),
  post: (path, body, opts = {}) => request(path, { method: 'POST', body, ...opts }),
  upload: (path, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(path, { method: 'POST', body: form, isForm: true })
  },
  setToken: (t) => localStorage.setItem('fs_token', t),
  clearToken: () => localStorage.removeItem('fs_token'),
  getToken,
}
