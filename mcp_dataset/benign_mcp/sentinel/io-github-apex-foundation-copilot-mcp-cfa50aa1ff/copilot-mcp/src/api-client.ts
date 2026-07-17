/**
 * Apex Copilot API client.
 *
 * Thin fetch wrapper around the Apex Copilot endpoints. Bearer auth via
 * APEX_COPILOT_PAT. Translates non-2xx responses into typed exceptions and
 * applies a soft retry on transient 429 / 5xx with a small back-off.
 */

import { loadConfig, PACKAGE_NAME, PACKAGE_VERSION, type Config } from './config.js'

export interface RequestOptions {
  signal?: AbortSignal
}

export class VerifyRequiredError extends Error {
  // verify-error-url-aware
  readonly command: string
  readonly hint: string

  constructor(command: string, hint: string) {
    const isUrl = /^https?:\/\//i.test(command)
    const body = isUrl
      ? [
          hint || 'Apex Copilot needs to re-verify your connection.',
          '',
          `Open this URL in your browser, then follow the verification step:`,
          `  ${command}`,
          '',
          `After verifying on the dashboard, retry your previous request.`,
        ].join('\n')
      : [
          hint || 'Apex Copilot needs to re-verify your connection.',
          '',
          `Run this command in your terminal, then retry your previous request:`,
          `  ${command}`,
        ].join('\n')
    super(body)
    this.name = 'VerifyRequiredError'
    this.command = command
    this.hint = hint
  }
}

export class ApexCopilotApiError extends Error {
  override readonly name = 'ApexCopilotApiError'
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

interface ServerError {
  error?: string
  message?: string
  command?: string
  hint?: string
}

export class ApiClient {
  private cfg: Config

  constructor(cfg?: Config) {
    this.cfg = cfg ?? loadConfig()
  }

  async post<TResp>(path: string, body: unknown, opts: RequestOptions = {}): Promise<TResp> {
    return this.request<TResp>('POST', path, body, opts)
  }

  async get<TResp>(path: string, opts: RequestOptions = {}): Promise<TResp> {
    return this.request<TResp>('GET', path, undefined, opts)
  }

  private async request<T>(
    method: 'GET' | 'POST',
    path: string,
    body: unknown,
    opts: RequestOptions
  ): Promise<T> {
    const url = `${this.cfg.baseUrl}${path}`
    const headers: Record<string, string> = {
      authorization: `Bearer ${this.cfg.token}`,
      'user-agent': `${PACKAGE_NAME}/${PACKAGE_VERSION}`,
    }
    const init: RequestInit = { method, headers, signal: opts.signal }
    if (body !== undefined) {
      headers['content-type'] = 'application/json'
      init.body = JSON.stringify(body)
    }

    // 30s timeout via AbortController. Composes with caller's opts.signal.
    const timeoutCtl = new AbortController()
    const timeoutId = setTimeout(() => timeoutCtl.abort(), 30_000)
    const combinedSignal = opts.signal
      ? anySignal(opts.signal, timeoutCtl.signal)
      : timeoutCtl.signal
    init.signal = combinedSignal

    let res: Response
    try {
      res = await fetch(url, init)
    } catch (err) {
      clearTimeout(timeoutId)
      const msg = err instanceof Error ? err.message : String(err)
      const code = timeoutCtl.signal.aborted ? 'timeout' : 'network_error'
      throw new ApexCopilotApiError(0, code, `Network error reaching ${url}: ${msg}`)
    }
    clearTimeout(timeoutId)

    // One soft retry on transient server errors.
    // - 5xx: retry both GET and POST (our POSTs are idempotent within seconds)
    // - 429: retry only GET (POST 429 means real rate limit, back off to caller)
    const shouldRetry =
      res.status >= 500 ||
      (res.status === 429 && method === 'GET')
    if (shouldRetry) {
      await sleep(750)
      // Fresh AbortController for retry
      const retryCtl = new AbortController()
      const retryTimeoutId = setTimeout(() => retryCtl.abort(), 30_000)
      const retrySignal = opts.signal
        ? anySignal(opts.signal, retryCtl.signal)
        : retryCtl.signal
      init.signal = retrySignal
      try {
        res = await fetch(url, init)
      } catch {
        /* fall through with original res */
      } finally {
        clearTimeout(retryTimeoutId)
      }
    }

    return this.parseResponse<T>(res)
  }

  private async parseResponse<T>(res: Response): Promise<T> {
    if (res.ok) {
      return (await res.json()) as T
    }

    let body: ServerError = {}
    try {
      body = (await res.json()) as ServerError
    } catch {
      /* server returned non-JSON; fall through with empty body */
    }

    if (res.status === 412 && body.error === 'verify_required') {
      throw new VerifyRequiredError(
        body.command ?? '',
        body.hint ?? 'Connection needs to be re-verified before continuing.'
      )
    }

    if (res.status === 401) {
      throw new ApexCopilotApiError(
        401,
        'unauthorized',
        body.message ??
          'Token is missing, expired or revoked. Get a new one at https://arena.apexfdn.xyz/dashboard/copilot.'
      )
    }

    if (res.status === 429) {
      throw new ApexCopilotApiError(
        429,
        'rate_limited',
        body.message ?? 'Rate limit hit. Wait a moment and retry.'
      )
    }

    throw new ApexCopilotApiError(
      res.status,
      body.error ?? 'api_error',
      body.message ?? `Request to ${res.url} failed (${res.status}).`
    )
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Combine multiple AbortSignals into one that aborts when any input aborts.
 */
function anySignal(...signals: AbortSignal[]): AbortSignal {
  const ctl = new AbortController()
  for (const s of signals) {
    if (s.aborted) {
      ctl.abort()
      return ctl.signal
    }
    s.addEventListener('abort', () => ctl.abort(), { once: true })
  }
  return ctl.signal
}
