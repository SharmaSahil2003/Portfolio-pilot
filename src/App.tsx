import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, ArrowRight, Check, Database, MoreHorizontal, Paintbrush2, Plus, RefreshCw, Sparkles, Trash2, Upload, X } from 'lucide-react'
import { api } from './api'
import type { ExternalDatabaseConfig, ExternalRecord, Mode } from './types'
import { Actions, AsideBlock, Badge, Breadcrumb, Card, CardBody, CardHead, CardTitle, Column, DefinitionArea, DefinitionInput, Divider, DropCopy, Dropzone, Eyebrow, Field, Grid, H1, IconButton, Main, Modal, ModalShade, ModeCard, ModeGrid, Muted, PageHeader, PrimaryButton, Row, SecondaryButton, SectionNote, SectionTitle, Shell, StepButton, StepContent, StepFooter, Steps, Toast, Topbar, UploadIcon } from './styles'

type DraftRecord = ExternalRecord & { responseText: string }
const modes: { key: Mode; title: string; description: string; icon: typeof Database }[] = [
  { key: 'sync', title: 'Data sync', description: 'Refresh the key/value records your portfolio reads from your database.', icon: Database },
  { key: 'page', title: 'Page update', description: 'Redesign and update the selected portfolio page source stored in your database.', icon: Paintbrush2 },
]
const stepNames = [{ title: 'Resume', note: 'Latest source' }, { title: 'Mode', note: 'Choose updates' }, { title: 'Database', note: 'Connect a table' }, { title: 'Select', note: 'Keys or pages' }, { title: 'Review', note: 'Publish a version' }]
const emptyConfig: ExternalDatabaseConfig = { engine: 'postgresql', host: '', port: 5432, database: '', username: '', password: '', schema: '', table: '', key_column: 'key', response_column: 'response', description_column: 'description', version_column: 'version', ssl: false }

function draftRecord(row: ExternalRecord): DraftRecord {
  const responseText = typeof row.response === 'string' ? row.response : JSON.stringify(row.response ?? null, null, 2) ?? 'null'
  return { ...row, responseText }
}

function currentResponse(row: DraftRecord, mode: Mode): unknown {
  if (mode === 'page') return row.responseText
  try { return JSON.parse(row.responseText) } catch { return row.responseText }
}

function displayResponse(value: unknown): string {
  if (value == null) return '(empty)'
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2) ?? String(value)
}

function responsePayload(rows: DraftRecord[], mode: Mode): ExternalRecord[] {
  return rows.map(row => ({ key: row.key, description: row.description, version: row.version, selected: row.selected, response: currentResponse(row, mode) }))
}

export default function App() {
  const [demo, setDemo] = useState(!localStorage.getItem('portfolio-pilot-token'))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [register, setRegister] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState<{ text: string; error?: boolean } | null>(null)
  const [section, setSection] = useState('Update flow')
  const [step, setStep] = useState(0)
  const [mode, setMode] = useState<Mode>('sync')
  const [resumeName, setResumeName] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [config, setConfig] = useState<ExternalDatabaseConfig>(emptyConfig)
  const [connected, setConnected] = useState(false)
  const [records, setRecords] = useState<DraftRecord[]>([])
  const [proposal, setProposal] = useState<DraftRecord[]>([])
  const [expectedVersion, setExpectedVersion] = useState<string | number | null>(null)
  const [generatedChanges, setGeneratedChanges] = useState<string[]>([])
  const [publishedVersion, setPublishedVersion] = useState<string | number | null>(null)

  function notify(text: string, error = false) { setToast({ text, error }); window.setTimeout(() => setToast(null), 5000) }

  async function loadAccount() {
    const [resume, database] = await Promise.all([api.resumeInfo(), api.databaseConfig()])
    setResumeName(resume.filename ?? '')
    if (database.connected) {
      setConnected(true)
      setConfig(current => ({ ...current, ...database, password: '' }))
      try {
        const latest = await api.databaseRecords()
        setRecords(latest.records.map(draftRecord))
        setExpectedVersion(latest.version)
      } catch (error) { notify((error as Error).message, true) }
    }
  }

  useEffect(() => {
    if (!localStorage.getItem('portfolio-pilot-token')) return
    setDemo(false)
    loadAccount().catch((error: Error) => notify(error.message, true))
  }, [])

  async function onResume(file?: File) {
    if (!file) return
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) { notify('Choose a PDF resume.', true); return }
    setBusy(true)
    try {
      setResumeFile(file)
      if (!demo) await api.uploadResume(file)
      setResumeName(file.name)
      setStep(1)
      notify(demo ? 'Resume selected. Sign in to connect your database and run the update.' : 'Resume uploaded. Choose a mode to continue.')
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }

  async function connectDatabase() {
    if (demo) { setAuthOpen(true); notify('Sign in before connecting a database.', true); return }
    setBusy(true)
    try {
      await api.connectDatabase(config)
      setConnected(true)
      const loaded = await api.databaseRecords()
      setRecords(loaded.records.map(draftRecord))
      setExpectedVersion(loaded.version)
      setProposal([])
      setPublishedVersion(null)
      notify(`Connected. Loaded ${loaded.records.length} rows from version ${loaded.version ?? 'empty'}.`)
    } catch (error) { setConnected(false); notify((error as Error).message, true) } finally { setBusy(false) }
  }

  async function reloadRecords() {
    setBusy(true)
    try {
      const loaded = await api.databaseRecords()
      setRecords(loaded.records.map(draftRecord))
      setExpectedVersion(loaded.version)
      notify(`Loaded ${loaded.records.length} rows from version ${loaded.version ?? 'empty'}.`)
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }

  function updateRecord(index: number, field: 'key' | 'description' | 'responseText' | 'selected', value: string | boolean) {
    setRecords(current => current.map((row, rowIndex) => {
      if (rowIndex !== index) return row
      if (field === 'selected') return { ...row, selected: Boolean(value) }
      if (field === 'key') return { ...row, key: String(value) }
      if (field === 'description') return { ...row, description: String(value) }
      return { ...row, responseText: String(value) }
    }))
  }

  function addRecord() {
    setRecords(current => [...current, { key: '', description: '', response: null, responseText: '', version: expectedVersion, selected: true }])
  }

  async function generateProposal() {
    if (demo) { setAuthOpen(true); notify('Sign in to generate a proposal from your database.', true); return }
    const keys = records.map(row => row.key.trim())
    if (keys.some(key => !key) || new Set(keys).size !== keys.length) { notify('Every row needs a unique, non-empty key or page name.', true); return }
    if (records.some(row => !row.description.trim())) { notify('Add a description for every key or page before generating.', true); return }
    setBusy(true)
    try {
      const result = await api.databasePropose(mode as 'sync' | 'page', expectedVersion, records.map(row => ({ key: row.key, description: row.description, response: row.response, version: row.version, selected: row.selected })))
      setProposal(result.records.map(draftRecord))
      setGeneratedChanges(result.changes)
      setStep(4)
      setSection('Review proposal')
      notify('Proposal ready. Review every row, then publish it to your database.')
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }

  async function publishProposal() {
    if (!proposal.length || publishedVersion !== null) return
    setBusy(true)
    try {
      const result = await api.databasePublish(mode as 'sync' | 'page', expectedVersion, responsePayload(proposal, mode))
      setExpectedVersion(result.version)
      setRecords(proposal.map(row => ({ ...row, version: result.version })))
      setPublishedVersion(result.version)
      notify(`Published version ${result.version} to your database.`)
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }

  async function login(event: FormEvent) {
    event.preventDefault(); setBusy(true)
    try {
      await api.login(email, password, register)
      if (resumeFile) await api.uploadResume(resumeFile)
      setDemo(false); setAuthOpen(false); await loadAccount()
      notify(register ? 'Account created.' : 'Welcome back.')
    } catch (error) { notify((error as Error).message, true) } finally { setBusy(false) }
  }

  function logout() {
    api.logout(); setDemo(true); setConnected(false); setResumeName(''); setResumeFile(null); setRecords([]); setProposal([]); setExpectedVersion(null); setPublishedVersion(null); setAuthOpen(false); setStep(0); notify('Signed out.')
  }

  const canContinue = step === 0 ? !!resumeName : step === 1 ? !!mode : step === 2 ? connected : false
  const sectionTitle = step === 0 ? 'Upload your resume' : step === 1 ? 'Choose an update mode' : step === 2 ? 'Connect your database' : step === 3 ? 'Choose keys or pages' : publishedVersion !== null ? `Version ${publishedVersion} published` : 'Review generated updates'

  return <Shell><Main>
    <Topbar><Breadcrumb>Workspace <span> / {section}</span></Breadcrumb><Actions><Badge $tone={demo ? 'amber' : 'green'}>{demo ? 'SIGN IN TO CONNECT DATABASE' : 'PRIVATE WORKSPACE'}</Badge><IconButton aria-label="Account" onClick={() => demo ? setAuthOpen(true) : logout()}>{demo ? <MoreHorizontal/> : <X/>}</IconButton></Actions></Topbar>
    <PageHeader><div><Eyebrow>RESUME → YOUR DATABASE <span style={{ color:'#737b7d' }}>· PUBLISH REVIEWED VERSIONS</span></Eyebrow><H1>Keep your portfolio current.</H1><Muted>Connect the key/response table your site reads. PortfolioPilot uses its current version and your latest resume to prepare updates.</Muted></div><PrimaryButton onClick={() => { setStep(0); setProposal([]); setPublishedVersion(null); setSection('Update flow') }}><RefreshCw/> New update</PrimaryButton></PageHeader>

    <Steps>{stepNames.map((item, index) => <StepButton key={item.title} $active={step === index} $done={step > index} disabled={index > step || busy} onClick={() => { if (index <= step) setStep(index) }}><span className="number">{step > index ? <Check size={12}/> : index + 1}</span><span><strong>{item.title}</strong><small>{item.note}</small></span></StepButton>)}</Steps>
    <Grid><Column><Card id={`step-${step}`}><CardHead><CardTitle>{sectionTitle}</CardTitle><Badge $tone={step === 4 ? 'green' : 'muted'}>STEP {step + 1} OF 5</Badge></CardHead><CardBody><StepContent>
      {step === 0 && <><SectionTitle>Start with your latest resume</SectionTitle><SectionNote>Upload a selectable-text PDF. Its facts are used only to prepare the database changes you review.</SectionNote><Dropzone><UploadIcon><Upload/></UploadIcon><DropCopy><strong>{resumeName || 'Drop your resume here, or browse'}</strong><small>PDF only · up to 25 MB</small></DropCopy><input type="file" accept="application/pdf,.pdf" onChange={event => void onResume(event.target.files?.[0])}/></Dropzone>{resumeName && <Muted>Resume ready: {resumeName}</Muted>}</>}

      {step === 1 && <><SectionTitle>Choose what to update</SectionTitle><SectionNote>Data sync updates your existing key/value records. Page update redesigns selected page source code stored in response values.</SectionNote><ModeGrid style={{ gridTemplateColumns: 'repeat(2, minmax(0,1fr))' }}>{modes.map(item => { const Icon = item.icon; return <ModeCard key={item.key} $selected={mode === item.key} onClick={() => setMode(item.key)}><strong><Icon/>{item.title}</strong><small>{item.description}</small></ModeCard> })}</ModeGrid></>}

      {step === 2 && <><SectionTitle>Connect the table your site reads</SectionTitle><SectionNote>Use PostgreSQL or MySQL and a least-privilege database user with SELECT and INSERT access to one key/response/version table. Credentials are encrypted at rest and never returned to the browser. The table must allow the same key in multiple versions (use a composite key/version uniqueness rule). Your portfolio should read rows from the latest version.</SectionNote>{demo && <Muted style={{ color:'#e6bd69' }}>Sign in or create an account before connecting your database.</Muted>}<div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))', gap:12 }}>
        <Field>DATABASE ENGINE<select value={config.engine} onChange={event => setConfig(current => ({ ...current, engine: event.target.value as ExternalDatabaseConfig['engine'], port: event.target.value === 'mysql' ? 3306 : 5432 }))} style={selectStyle}><option value="postgresql">PostgreSQL</option><option value="mysql">MySQL</option></select></Field>
        <ConfigField label="HOST" value={config.host} onChange={value => setConfig(current => ({ ...current, host: value }))} placeholder="db.example.com"/>
        <ConfigField label="PORT" value={String(config.port)} onChange={value => setConfig(current => ({ ...current, port: Number(value) || 0 }))} placeholder="5432"/>
        <ConfigField label="DATABASE" value={config.database} onChange={value => setConfig(current => ({ ...current, database: value }))} placeholder="portfolio"/>
        <ConfigField label="USERNAME" value={config.username} onChange={value => setConfig(current => ({ ...current, username: value }))} placeholder="portfolio_app"/>
        <ConfigField label="PASSWORD" value={config.password} onChange={value => setConfig(current => ({ ...current, password: value }))} placeholder={connected ? 'Saved securely · leave blank to keep' : 'Database password'} type="password"/>
        <ConfigField label="SCHEMA · OPTIONAL" value={config.schema || ''} onChange={value => setConfig(current => ({ ...current, schema: value }))} placeholder="public"/>
        <ConfigField label="TABLE" value={config.table} onChange={value => setConfig(current => ({ ...current, table: value }))} placeholder="portfolio_content"/>
        <ConfigField label="KEY COLUMN" value={config.key_column} onChange={value => setConfig(current => ({ ...current, key_column: value }))} placeholder="key"/>
        <ConfigField label="RESPONSE / PAGE CODE COLUMN" value={config.response_column} onChange={value => setConfig(current => ({ ...current, response_column: value }))} placeholder="response"/>
        <ConfigField label="DESCRIPTION COLUMN" value={config.description_column} onChange={value => setConfig(current => ({ ...current, description_column: value }))} placeholder="description"/>
        <ConfigField label="VERSION COLUMN" value={config.version_column} onChange={value => setConfig(current => ({ ...current, version_column: value }))} placeholder="version"/>
        <label style={{ display:'flex', alignItems:'center', gap:9, color:'#aab2ad', fontSize:12 }}><input type="checkbox" checked={config.ssl} onChange={event => setConfig(current => ({ ...current, ssl: event.target.checked }))}/> Require SSL</label>
      </div><Row style={{ marginTop:18, justifyContent:'flex-start' }}><PrimaryButton disabled={busy || demo} onClick={() => void connectDatabase()}>{busy ? 'Connecting…' : connected ? 'Verify and reload table' : 'Verify and save connection'}</PrimaryButton>{connected && <Badge $tone="green"><Check size={12}/> CONNECTED · VERSION {expectedVersion ?? 'EMPTY'}</Badge>}</Row></>}

      {step === 3 && <><SectionTitle>{mode === 'sync' ? 'Review and choose database keys' : 'Select portfolio pages to redesign'}</SectionTitle><SectionNote>{mode === 'sync' ? 'These descriptions and previous responses came from your latest database version. Edit descriptions, add keys, or remove rows before generation.' : 'Each key names a page (for example home, about, skills, projects); its response should contain that page’s full source code. Select one, several, or all pages.'}</SectionNote>{records.length === 0 && <Muted>No rows were found in the connected table. Add the first {mode === 'page' ? 'page and its source code' : 'key'} below.</Muted>}
        {records.map((row, index) => <div key={index} style={recordCardStyle}><div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:10 }}><input aria-label={`Select ${row.key || 'row'}`} type="checkbox" checked={row.selected !== false} onChange={event => updateRecord(index, 'selected', event.target.checked)}/><DefinitionInput aria-label={mode === 'page' ? 'Page key' : 'Database key'} placeholder={mode === 'page' ? 'about' : 'skills'} value={row.key} onChange={event => updateRecord(index, 'key', event.target.value)}/><IconButton aria-label={`Remove ${row.key || 'row'}`} onClick={() => setRecords(current => current.filter((_, i) => i !== index))}><Trash2/></IconButton></div><DefinitionArea aria-label="Description" placeholder="Describe what this key or page contains" value={row.description} onChange={event => updateRecord(index, 'description', event.target.value)}/><details style={{ marginTop:9, color:'#8f9993', fontSize:11 }}><summary>Previous response · version {row.version ?? 'empty'}</summary><pre style={sourcePreviewStyle}>{row.responseText || '(empty)'}</pre></details></div>)}
        <Row style={{ marginTop:14, justifyContent:'flex-start' }}><SecondaryButton onClick={addRecord}><Plus/> Add {mode === 'page' ? 'page' : 'key'}</SecondaryButton><SecondaryButton disabled={busy} onClick={() => void reloadRecords()}><RefreshCw/> Reload latest rows</SecondaryButton></Row>
      </>}

      {step === 4 && <><SectionTitle>{publishedVersion !== null ? `Version ${publishedVersion} is now in your database` : 'Review before publishing'}</SectionTitle><SectionNote>{mode === 'page' ? 'Compare the stored page source with the redesigned source. Review every selected page before publishing this complete version.' : 'The latest resume facts were merged with the existing key responses. Review the generated values and publish the complete version.'}</SectionNote>{generatedChanges.length > 0 && <ul style={{ color:'#b5c0b6', fontSize:12, lineHeight:1.7 }}>{generatedChanges.map((change, index) => <li key={index}>{change}</li>)}</ul>}
        {proposal.map((row, index) => <div key={index} style={recordCardStyle}><Row><strong style={{ color:'#eff2e9', fontSize:13 }}>{row.key}</strong><Badge $tone={row.selected ? 'green' : 'muted'}>{row.selected ? 'UPDATED' : 'UNCHANGED'}</Badge></Row><Field style={{ marginTop:12 }}>DESCRIPTION<DefinitionArea value={row.description} disabled={publishedVersion !== null} onChange={event => setProposal(current => current.map((item, i) => i === index ? { ...item, description: event.target.value } : item))}/></Field><Field style={{ marginTop:12 }}>{mode === 'page' ? 'PROPOSED PAGE SOURCE' : 'PROPOSED RESPONSE'}<DefinitionArea style={{ minHeight: mode === 'page' ? 300 : 130, fontFamily: mode === 'page' ? 'DM Mono, monospace' : undefined }} value={row.responseText} disabled={publishedVersion !== null} onChange={event => setProposal(current => current.map((item, i) => i === index ? { ...item, responseText: event.target.value } : item))}/></Field>{row.selected && <details open={mode === 'page'} style={{ marginTop:8, color:'#8f9993', fontSize:11 }}><summary>Previous response / page source · version {row.version ?? 'empty'}</summary><pre style={sourcePreviewStyle}>{displayResponse(row.previous_response)}</pre></details>}</div>)}
      </>}
    </StepContent>

    <StepFooter><SecondaryButton disabled={step === 0 || busy} onClick={() => setStep(current => Math.max(0, current - 1))}><ArrowLeft/> Back</SecondaryButton>
      {step < 3 && <PrimaryButton disabled={!canContinue || busy} onClick={() => { setStep(current => current + 1); setSection(stepNames[step + 1].title) }}>Continue <ArrowRight/></PrimaryButton>}
      {step === 3 && <PrimaryButton disabled={busy || demo || records.length === 0} onClick={() => void generateProposal()}>{busy ? 'Generating…' : <><Sparkles/> Generate proposal</>}</PrimaryButton>}
      {step === 4 && publishedVersion === null && <PrimaryButton disabled={busy || proposal.length === 0} onClick={() => void publishProposal()}>{busy ? 'Publishing…' : <><Check/> Publish new version</>}</PrimaryButton>}
      {step === 4 && publishedVersion !== null && <Badge $tone="green"><Check size={12}/> PUBLISHED · {publishedVersion}</Badge>}
    </StepFooter>
    </CardBody></Card></Column></Grid>

    {toast && <Toast $error={toast.error}>{toast.text}</Toast>}
    {authOpen && <ModalShade onClick={() => setAuthOpen(false)}><Modal onClick={event => event.stopPropagation()}><Row><div><Eyebrow>{register ? 'GET STARTED' : 'WELCOME BACK'}</Eyebrow><H1 style={{ fontSize:23 }}>{register ? 'Create your account.' : 'Sign in to PortfolioPilot.'}</H1></div><IconButton aria-label="Close" onClick={() => setAuthOpen(false)}><X/></IconButton></Row><Muted style={{ marginBottom:19 }}>Your resume metadata and encrypted database connection are scoped to your account.</Muted><form onSubmit={event => void login(event)}><AsideBlock><Field>EMAIL<input required type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)}/></Field><Field>PASSWORD<input required minLength={8} type="password" autoComplete={register ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)}/></Field><PrimaryButton disabled={busy}>{busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}<ArrowRight/></PrimaryButton></AsideBlock></form><Divider/><Row><small style={{ color:'#8b9494',fontSize:10 }}>{register ? 'Already have an account?' : 'New to PortfolioPilot?'}</small><SecondaryButton onClick={() => setRegister(!register)}>{register ? 'Sign in' : 'Create account'}</SecondaryButton></Row></Modal></ModalShade>}
  </Main></Shell>
}

function ConfigField({ label, value, onChange, placeholder, type = 'text' }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string }) {
  return <Field>{label}<input type={type} value={value} placeholder={placeholder} onChange={event => onChange(event.target.value)}/></Field>
}

const selectStyle = { background:'#0f1417', border:'1px solid #30373b', borderRadius:7, padding:10, color:'#e7ebe5', fontSize:12 }
const recordCardStyle = { border:'1px solid #2b3335', borderRadius:9, background:'#101518', padding:14, marginTop:12 }
const sourcePreviewStyle = { maxHeight:300, overflow:'auto' as const, whiteSpace:'pre-wrap' as const, overflowWrap:'anywhere' as const, background:'#0b1012', border:'1px solid #293033', borderRadius:7, padding:12, color:'#b8c7b8', font:'10px/1.55 DM Mono, monospace' }
