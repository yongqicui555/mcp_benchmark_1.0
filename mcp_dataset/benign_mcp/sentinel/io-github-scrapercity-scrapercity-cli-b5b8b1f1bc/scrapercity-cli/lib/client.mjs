// lib/client.mjs — Shared ScraperCity API client
import fs from 'fs'
import path from 'path'
import os from 'os'

const BASE = 'https://app.scrapercity.com'
const RC_PATH = path.join(os.homedir(), '.scrapercityrc')

// ── Auth ──────────────────────────────────────────────────────
export function getApiKey() {
  // 1) env var
  if (process.env.SCRAPERCITY_API_KEY) return process.env.SCRAPERCITY_API_KEY
  // 2) rc file
  if (fs.existsSync(RC_PATH)) {
    const rc = JSON.parse(fs.readFileSync(RC_PATH, 'utf-8'))
    if (rc.apiKey) return rc.apiKey
  }
  return null
}

export function saveApiKey(key) {
  fs.writeFileSync(RC_PATH, JSON.stringify({ apiKey: key }), { mode: 0o600 })
}

// ── HTTP helpers ──────────────────────────────────────────────
async function req(method, urlPath, body) {
  const key = getApiKey()
  if (!key) throw new Error('No API key. Run: scrapercity login  OR  export SCRAPERCITY_API_KEY=...')

  const opts = {
    method,
    headers: {
      'Authorization': `Bearer ${key}`,
      'Content-Type': 'application/json',
      'User-Agent': 'scrapercity-cli/1.0'
    }
  }
  if (body && method !== 'GET') opts.body = JSON.stringify(body)

  const url = urlPath.startsWith('http') ? urlPath : `${BASE}${urlPath}`
  const res = await fetch(url, opts)
  const text = await res.text()

  let data
  try { data = JSON.parse(text) } catch { data = { raw: text } }

  if (!res.ok) {
    const msg = data.error || data.message || `HTTP ${res.status}`
    const err = new Error(msg)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

const get  = (p)    => req('GET', p)
const post = (p, b) => req('POST', p, b)

// ── Wallet & Runs ─────────────────────────────────────────────
export const wallet = ()                      => get('/api/v1/wallet')
export const runs   = (hours = 24, limit = 50) => get(`/api/v1/runs?hours=${hours}&limit=${limit}`)

// ── Status / Download / Cancel / Logs ─────────────────────────
export const status   = (runId) => get(`/api/v1/scrape/status/${runId}`)
export const cancel   = (runId) => post(`/api/v1/scrape/cancel/${runId}`)
export const logs     = (runId) => get(`/api/v1/scrape/logs/${runId}`)

export async function download(runId, outputPath) {
  const key = getApiKey()
  if (!key) throw new Error('No API key')
  const res = await fetch(`${BASE}/api/downloads/${runId}`, {
    headers: { 'Authorization': `Bearer ${key}` }
  })
  if (!res.ok) throw new Error(`Download failed: HTTP ${res.status}`)
  const buf = Buffer.from(await res.arrayBuffer())
  const out = outputPath || `${runId}.csv`
  fs.writeFileSync(out, buf)
  return { path: out, bytes: buf.length }
}

// ── Apollo ────────────────────────────────────────────────────
export const apollo = (url, count = 1000, fileName = '') =>
  post('/api/v1/scrape/apollo', { url, count, fileName })

export const apolloFilters = (filters) =>
  post('/api/v1/scrape/apollo-filters', filters)

export const apolloStatus = () => get('/api/v1/apollo-status')

// ── Maps ──────────────────────────────────────────────────────
export const maps = (query, location, limit = 500) =>
  post('/api/v1/scrape/maps', {
    searchStringsArray: Array.isArray(query) ? query : [query],
    locationQuery: location,
    maxCrawledPlacesPerSearch: limit
  })

// ── Email Validator ───────────────────────────────────────────
export const emailValidate = (emails) =>
  post('/api/v1/scrape/email-validator', { emails })

// ── Email Finder ──────────────────────────────────────────────
export const emailFind = (contacts, opts = {}) =>
  post('/api/v1/scrape/email-finder', {
    contacts,
    autoValidateEmails: opts.validate || false,
    autoFindMobiles: opts.mobiles || false
  })

// ── Mobile Finder ─────────────────────────────────────────────
export const mobileFinder = (inputs) =>
  post('/api/v1/scrape/mobile-finder', { inputs })

// ── People Finder / Skip Trace ────────────────────────────────
export const peopleFinder = (params) =>
  post('/api/v1/scrape/people-finder', params)

// ── Store Leads (Ecommerce) ───────────────────────────────────
export const storeLeads = (params) =>
  post('/api/v1/scrape/store-leads', params)

// ── BuiltWith ─────────────────────────────────────────────────
export const builtwith = (technology, fileName) =>
  post('/api/v1/scrape/builtwith', { technology, fileName })

// ── Criminal Records ──────────────────────────────────────────
export const criminal = (name, state, dob) =>
  post('/api/v1/scrape/criminal-records', { name, state, dob })

// ── Airbnb Email ──────────────────────────────────────────────
export const airbnb = (params) =>
  post('/api/v1/scrape/airbnb-email', params)

// ── YouTube Email ─────────────────────────────────────────────
export const youtubeEmail = (channels) =>
  post('/api/v1/scrape/youtube-email', { channels })

// ── Website Finder ────────────────────────────────────────────
export const websiteFinder = (domains, jobTitle) =>
  post('/api/v1/scrape/website-finder', { domains, jobTitle })

// ── Yelp ──────────────────────────────────────────────────────
export const yelp = (params) =>
  post('/api/v1/scrape/yelp-scraper', params)

// ── Angi (Angie's List) ──────────────────────────────────────
export const angi = (keyword, zipCodes, maxItems = 100) =>
  post('/api/v1/scrape/angi-angies-list-scraper', { keyword, zipCodes, maxItems })

// ── Zillow Agents ─────────────────────────────────────────────
export const zillowAgents = (location, opts = {}) =>
  post('/api/v1/scrape/zillow-agents', { location, ...opts })

// ── BizBuySell ────────────────────────────────────────────────
export const bizbuysell = (startUrls, maxItems = 100) =>
  post('/api/v1/scrape/bizbuysell-scraper', { startUrls, maxItems })

// ── Crexi ─────────────────────────────────────────────────────
export const crexi = (startUrls) =>
  post('/api/v1/scrape/crexi-scraper', { startUrls })

// ── Property Lookup ───────────────────────────────────────────
export const propertyLookup = (addresses, includeOwnerContact = false) =>
  post('/api/v1/scrape/property-lookup', { addresses, includeOwnerContact })

// ── Generic Scraper (fallback for any slug) ───────────────────
export const scrape = (slug, body) =>
  post(`/api/v1/scrape/${slug}`, body)

// ── Databases ($649 plan) ─────────────────────────────────────
export const dbLeads = (params) => {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) v.forEach(x => qs.append(k, x))
    else qs.append(k, String(v))
  }
  return get(`/api/v1/database/leads?${qs}`)
}

export const dbLocalBusinesses = (params) => {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) v.forEach(x => qs.append(k, x))
    else qs.append(k, String(v))
  }
  return get(`/api/v1/database/local-businesses?${qs}`)
}

export const dbEcommerce = (params) => {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) v.forEach(x => qs.append(k, x))
    else qs.append(k, String(v))
  }
  return get(`/api/v1/database/ecommerce?${qs}`)
}

// ── Poll until done ───────────────────────────────────────────
export async function pollUntilDone(runId, { interval = 15000, timeout = 3600000, onStatus } = {}) {
  const start = Date.now()
  while (Date.now() - start < timeout) {
    const s = await status(runId)
    if (onStatus) onStatus(s)
    if (s.status === 'SUCCEEDED') return s
    if (s.status === 'FAILED' || s.status === 'CANCELLED') {
      throw new Error(`Run ${runId} ended with status: ${s.status} — ${s.statusMessage || ''}`)
    }
    await new Promise(r => setTimeout(r, interval))
  }
  throw new Error(`Timed out after ${timeout / 1000}s waiting for run ${runId}`)
}
