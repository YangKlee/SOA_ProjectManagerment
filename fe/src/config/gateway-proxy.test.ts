// @vitest-environment node
import { createServer as createHttpServer } from 'node:http'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { fileURLToPath } from 'node:url'
import { createServer as createViteServer } from 'vite'
import type { ViteDevServer } from 'vite'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { createGatewayProxy, DEFAULT_GATEWAY_TARGET, GATEWAY_PREFIXES } from './gateway-proxy'

describe('Gateway proxy configuration', () => {
  it('uses only Gateway prefixes and the default port 8000 target', () => {
    const proxy = createGatewayProxy()
    expect(Object.keys(proxy)).toHaveLength(4)
    for (const options of Object.values(proxy)) {
      expect(options.target).toBe(DEFAULT_GATEWAY_TARGET)
      expect(options.changeOrigin).toBe(true)
      expect(options.rewrite).toBeUndefined()
    }
    const matches = (path: string) => Object.keys(proxy).some((key) => new RegExp(key).test(path))
    for (const prefix of GATEWAY_PREFIXES) {
      expect(matches(`${prefix}/api/items/?page=2`)).toBe(true)
      expect(matches(prefix)).toBe(true)
    }
    for (const path of ['/login', '/admin', '/lecture', '/student', '/authentication/login/', '/topics-extra/']) {
      expect(matches(path)).toBe(false)
    }
  })

  it('supports a configured Gateway origin and defaults when empty', () => {
    expect(Object.values(createGatewayProxy(' https://gateway.example.com '))[0].target).toBe('https://gateway.example.com')
    expect(Object.values(createGatewayProxy(' '))[0].target).toBe(DEFAULT_GATEWAY_TARGET)
  })

  it.each(['ftp://gateway.example.com', 'http://user:password@gateway.example.com', 'http://gateway.example.com/path', 'http://gateway.example.com?token=test'])('rejects invalid proxy targets: %s', (target) => {
    expect(() => createGatewayProxy(target)).toThrow()
  })
})

describe('Vite proxy HTTP integration', () => {
  let gateway: Server
  let vite: ViteDevServer | undefined
  let frontendOrigin: string
  let gatewayOrigin: string
  const received: { path: string; method: string | undefined }[] = []

  beforeAll(async () => {
    gateway = createHttpServer(async (request, response) => {
      const chunks: Buffer[] = []
      for await (const chunk of request) chunks.push(Buffer.from(chunk))
      received.push({ path: request.url ?? '', method: request.method })
      response.writeHead(request.url === '/auth/status/401/' ? 401 : 200, { 'Content-Type': 'application/json' })
      response.end(JSON.stringify({
        path: request.url,
        method: request.method,
        body: Buffer.concat(chunks).toString(),
        authorization: request.headers.authorization,
        host: request.headers.host,
      }))
    })
    await new Promise<void>((resolve) => gateway.listen(0, '127.0.0.1', resolve))
    gatewayOrigin = `http://127.0.0.1:${(gateway.address() as AddressInfo).port}`
    vi.stubEnv('VITE_API_PROXY_TARGET', gatewayOrigin)
    // Load the actual project config, including loadEnv and its proxy wiring.
    vite = await createViteServer({
      configFile: fileURLToPath(new URL('../../vite.config.ts', import.meta.url)),
      mode: 'test',
      logLevel: 'silent',
      server: { host: '127.0.0.1', port: 0, strictPort: false, hmr: false, watch: null },
      optimizeDeps: { noDiscovery: true, include: [] },
    })
    await vite.listen()
    frontendOrigin = `http://127.0.0.1:${(vite.httpServer!.address() as AddressInfo).port}`
  }, 20_000)

  afterAll(async () => {
    try {
      await vite?.close()
    } finally {
      if (gateway?.listening) {
        gateway.closeAllConnections()
        await new Promise<void>((resolve, reject) => gateway.close((error) => error ? reject(error) : resolve()))
      }
      vi.unstubAllEnvs()
    }
  })

  it('forwards login method, query, body and Bearer through the same frontend origin', async () => {
    const body = JSON.stringify({ identifier: 'test-user', password: ' test-only-password ' })
    const response = await fetch(`${frontendOrigin}/auth/login/?source=test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer test-only-token', Origin: frontendOrigin },
      body,
    })
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({
      path: '/auth/login/?source=test', method: 'POST', body,
      authorization: 'Bearer test-only-token', host: new URL(gatewayOrigin).host,
    })
    expect(received.filter((entry) => entry.path === '/auth/login/?source=test')).toHaveLength(1)
    expect(received.some((entry) => entry.method === 'OPTIONS')).toBe(false)
  })

  it.each(GATEWAY_PREFIXES)('preserves the %s prefix and query for Gateway routing', async (prefix) => {
    const response = await fetch(`${frontendOrigin}${prefix}/api/items/?page=2`)
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({ path: `${prefix}/api/items/?page=2`, method: 'GET' })
  })

  it('preserves backend authorization error status and body', async () => {
    const response = await fetch(`${frontendOrigin}/auth/status/401/`)
    expect(response.status).toBe(401)
    expect(await response.json()).toMatchObject({ path: '/auth/status/401/' })
  })

  it('serves frontend routes as SPA HTML without sending them to the Gateway', async () => {
    const before = received.length
    for (const path of ['/login', '/admin', '/lecture', '/student', '/admin/departments', '/admin/majors', '/admin/students', '/admin/lecturers', '/lecture/topics', '/student/registrations', '/admin/profile', '/missing', '/authentication/login/']) {
      const response = await fetch(`${frontendOrigin}${path}`, { headers: { Accept: 'text/html' } })
      expect(response.status).toBe(200)
      expect(response.headers.get('content-type')).toContain('text/html')
      expect(await response.text()).toContain('/src/main.tsx')
    }
    expect(received).toHaveLength(before)
  })
})
