export type Mode = 'sync' | 'page' | 'workspace'
export type Profile = {
  name: string; headline: string; email: string; location: string; about: string
  skills: string[]; experience: { company: string; role: string; period: string }[]
  projects: { name: string; description: string; stack: string[] }[]
}
export type Version = { id: string; label: string; mode: Mode; createdAt: string; status: 'pending' | 'active' | 'archived'; changes: string[]; previewUrl?: string; versionNumber?: number }
export type Job = { id: string; status: string; message: string; version?: Version }
export type VersionDiff = { version: Version; previousVersion: Version | null; changes: string[]; profileChanges: string[] }
export type VariableDefinition = { key: string; description: string; sample_json?: unknown }
export type PortfolioVariable = VariableDefinition & { value: unknown; version?: string }
export type ExternalDatabaseConfig = {
  engine: 'postgresql' | 'mysql'; host: string; port: number; database: string; username: string
  password: string; schema?: string; table: string; key_column: string; response_column: string
  description_column: string; version_column: string; ssl: boolean
}
export type ExternalRecord = { key: string; description: string; response: unknown; previous_response?: unknown; version?: string | number | null; selected?: boolean }
