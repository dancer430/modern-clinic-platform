// Node 25 ships an experimental built-in `localStorage` global that lacks a
// full Web Storage API (no `clear()` / `key()` / `length`). Vitest's happy-dom
// environment also struggles to provide a complete Storage in this Node
// version. Install a minimal in-memory Storage shim so tests get a stable,
// real Web Storage on both `window.localStorage` and `globalThis.localStorage`.

class MemoryStorage implements Storage {
  private map = new Map<string, string>()

  get length(): number {
    return this.map.size
  }

  clear(): void {
    this.map.clear()
  }

  getItem(key: string): string | null {
    return this.map.has(key) ? (this.map.get(key) as string) : null
  }

  key(index: number): string | null {
    return Array.from(this.map.keys())[index] ?? null
  }

  removeItem(key: string): void {
    this.map.delete(key)
  }

  setItem(key: string, value: string): void {
    this.map.set(key, String(value))
  }
}

const installStorage = (key: 'localStorage' | 'sessionStorage') => {
  const store = new MemoryStorage()
  Object.defineProperty(globalThis, key, {
    configurable: true,
    writable: true,
    value: store,
  })
  if (typeof window !== 'undefined') {
    Object.defineProperty(window, key, {
      configurable: true,
      writable: true,
      value: store,
    })
  }
}

installStorage('localStorage')
installStorage('sessionStorage')

beforeEach(() => {
  window.localStorage.clear()
  window.sessionStorage.clear()
})
