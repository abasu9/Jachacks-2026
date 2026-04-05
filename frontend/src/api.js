// In dev, Vite proxy handles /api → localhost:8000
// In prod, VITE_API_URL points to the Render backend
const BASE = import.meta.env.VITE_API_URL || '/api'

export function api(path, options) {
  return fetch(`${BASE}${path}`, options)
}
