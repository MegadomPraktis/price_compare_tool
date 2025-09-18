const BASE =
  (import.meta.env.VITE_API && import.meta.env.VITE_API.trim() !== '')
    ? import.meta.env.VITE_API
    : window.location.origin

export async function api<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: HeadersInit =
    options.method && options.method !== 'GET'
      ? { 'Content-Type': 'application/json', ...(options.headers || {}) }
      : (options.headers || {})
  const res = await fetch(BASE + path, { ...options, headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
