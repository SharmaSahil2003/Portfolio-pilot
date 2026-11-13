import type { ExternalDatabaseConfig, ExternalRecord, Job, Mode, PortfolioVariable, Profile, VariableDefinition, Version, VersionDiff } from './types'

const API = import.meta.env.VITE_API_URL ?? '/api'
const tokenKey = 'portfolio-pilot-token'
const token = () => localStorage.getItem(tokenKey)
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (token()) headers.set('Authorization', `Bearer ${token()}`)
  const response = await fetch(`${API}${path}`, { ...init, headers })
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail ?? `Request failed (${response.status})`)
  return response.json() as Promise<T>
}
export const api = {
  async login(email: string, password: string, register = false) {
    const data = await request<{ access_token: string }>(register ? '/auth/register' : '/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
    localStorage.setItem(tokenKey, data.access_token)
  },
  logout() { localStorage.removeItem(tokenKey) },
  profile: () => request<Profile>('/profile'),
  updateProfile: (profile: Profile) => request<Profile>('/profile', { method: 'PUT', body: JSON.stringify(profile) }),
  resumeInfo: () => request<{ filename: string | null; uploadedAt: string | null }>('/resume'),
  uploadResume(file: File) { const data = new FormData(); data.append('file', file); return request<{ filename: string; uploadedAt: string }>('/resume', { method: 'POST', body: data }) },
  uploadWorkspace(file: File) { const data = new FormData(); data.append('file', file); return request<{ filename: string }>('/workspace', { method: 'POST', body: data }) },
  definitions: () => request<{ definitions: VariableDefinition[] }>('/variables/definitions'),
  generateVariables: (definitions: VariableDefinition[]) => request<{ id: string; status: string; message: string; version: Version; variables: PortfolioVariable[]; aiEnabled: boolean }>('/variables/generate', { method: 'POST', body: JSON.stringify({ definitions }) }),
  databaseConfig: () => request<Partial<ExternalDatabaseConfig> & { connected: boolean }>('/database/config'),
  connectDatabase: (config: ExternalDatabaseConfig) => request<{ connected: boolean; message: string }>('/database/connect', { method: 'POST', body: JSON.stringify(config) }),
  databaseRecords: () => request<{ records: ExternalRecord[]; version: string | number | null }>('/database/records', { method: 'POST' }),
  databasePropose: (mode: 'sync' | 'page', expectedVersion: string | number | null, records: ExternalRecord[]) => request<{ records: ExternalRecord[]; version: string | number | null; changes: string[] }>('/database/propose', { method: 'POST', body: JSON.stringify({ mode, expected_version: expectedVersion, records }) }),
  databasePublish: (mode: 'sync' | 'page', expectedVersion: string | number | null, records: ExternalRecord[]) => request<{ published: boolean; version: string | number; message: string }>('/database/publish', { method: 'POST', body: JSON.stringify({ mode, expected_version: expectedVersion, records }) }),
  updateVersionVariables: (id: string, variables: PortfolioVariable[]) => request<{ variables: PortfolioVariable[] }>(`/versions/${id}/variables`, { method: 'PUT', body: JSON.stringify({ variables }) }),
  versionVariables: (id: string) => request<{ variables: PortfolioVariable[] }>(`/versions/${id}/variables`),
  activeVariables: () => request<{ version: Version | null; variables: PortfolioVariable[] }>('/variables/active'),
  integration: () => request<{ public_id: string; endpoint: string }>('/portfolio/integration'),
  generate: (mode: Mode, page?: string) => request<Job>('/generations', { method: 'POST', body: JSON.stringify({ mode, page }) }),
  versions: () => request<Version[]>('/versions'),
  versionDiff: (id: string) => request<VersionDiff>(`/versions/${id}/diff`),
  approve: (id: string) => request<Version>(`/versions/${id}/approve`, { method: 'POST' }),
  rollback: (id: string) => request<Version>(`/versions/${id}/rollback`, { method: 'POST' }),
}
