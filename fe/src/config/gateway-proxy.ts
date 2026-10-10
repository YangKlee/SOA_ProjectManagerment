import type { ProxyOptions } from 'vite'

export const GATEWAY_PREFIXES = ['/auth', '/academic', '/registrations', '/topics'] as const
export const DEFAULT_GATEWAY_TARGET = 'http://localhost:8000'

/** Proxy API prefixes only. Do not rewrite the path: the Gateway owns routing. */
export function createGatewayProxy(configuredTarget?: string): Record<string, ProxyOptions> {
  const target = configuredTarget?.trim() || DEFAULT_GATEWAY_TARGET
  const url = new URL(target)
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password
    || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('VITE_API_PROXY_TARGET must be an HTTP(S) Gateway origin without credentials or a path.')
  }

  return Object.fromEntries(GATEWAY_PREFIXES.map((prefix) => [
    `^${prefix}(?:/|\\?|$)`,
    {
      target: url.origin,
      changeOrigin: true,
      timeout: 10_000,
      proxyTimeout: 10_000,
    },
  ]))
}
