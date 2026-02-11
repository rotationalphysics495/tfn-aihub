import '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import Module from 'node:module'

// Patch Node's require resolution to find .ts/.tsx files when extension is omitted.
// Vitest handles ESM imports via Vite transform, but CJS require() in tests
// (e.g., const { fn } = require('../Module')) uses Node's native resolver
// which only checks .js/.json/.node extensions by default.
const origResolveFilename = (Module as any)._resolveFilename
;(Module as any)._resolveFilename = function (
  request: string,
  parent: any,
  isMain: boolean,
  options: any,
) {
  try {
    return origResolveFilename.call(this, request, parent, isMain, options)
  } catch (err: any) {
    if (err?.code === 'MODULE_NOT_FOUND' && !request.startsWith('node:')) {
      for (const ext of ['.ts', '.tsx']) {
        try {
          return origResolveFilename.call(
            this,
            request + ext,
            parent,
            isMain,
            options,
          )
        } catch {
          continue
        }
      }
    }
    throw err
  }
}

// Provide jest global shim so @testing-library/react detects vitest fake timers.
// Without this, waitFor() hangs when vi.useFakeTimers() is active because
// @testing-library checks for `jest` global to detect fake timer mode.
globalThis.jest = {
  ...globalThis.jest,
  advanceTimersByTime: vi.advanceTimersByTime.bind(vi),
} as any

// Mock scrollIntoView since jsdom doesn't support it
window.HTMLElement.prototype.scrollIntoView = vi.fn()

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
  useSearchParams: () => ({
    get: vi.fn().mockReturnValue(null),
  }),
  usePathname: () => '/',
  useParams: () => ({}),
}))

// Mock environment variables
process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test-project.supabase.co'
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'test-anon-key'
