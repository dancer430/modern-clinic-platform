import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

const postMock = vi.fn()

vi.mock('axios', () => ({
  default: {
    post: (...args: unknown[]) => postMock(...args),
  },
}))

let originalLocation: Location | undefined

const setLocation = () => {
  originalLocation = window.location
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { origin: 'http://localhost', href: '' },
  })
}

const restoreLocation = () => {
  if (originalLocation !== undefined) {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    })
  }
}

const storage = window.localStorage

describe('refreshAccessToken', () => {
  beforeEach(async () => {
    vi.resetModules()
    postMock.mockReset()
    storage.clear()
    setLocation()
  })

  afterEach(() => {
    restoreLocation()
  })

  it('rejects when no refresh token is in storage', async () => {
    const { refreshAccessToken } = await import('../tokenRefresh')
    await expect(refreshAccessToken()).rejects.toThrow('No refresh token')
    expect(postMock).not.toHaveBeenCalled()
  })

  it('deduplicates two concurrent calls into one network request', async () => {
    storage.setItem('refreshToken', 'r-1')
    let resolveResponse: (value: { data: { access: string; refresh: string } }) => void = () => {}
    postMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveResponse = resolve
        }),
    )

    const { refreshAccessToken } = await import('../tokenRefresh')
    const first = refreshAccessToken()
    const second = refreshAccessToken()

    expect(postMock).toHaveBeenCalledTimes(1)

    resolveResponse({ data: { access: 'a-1', refresh: 'r-2' } })
    await expect(first).resolves.toBe('a-1')
    await expect(second).resolves.toBe('a-1')

    expect(storage.getItem('accessToken')).toBe('a-1')
    expect(storage.getItem('refreshToken')).toBe('r-2')
  })

  it('clears the pending promise after success so a later call hits the network again', async () => {
    storage.setItem('refreshToken', 'r-1')
    postMock
      .mockResolvedValueOnce({ data: { access: 'a-1', refresh: 'r-2' } })
      .mockResolvedValueOnce({ data: { access: 'a-2', refresh: 'r-3' } })

    const { refreshAccessToken } = await import('../tokenRefresh')
    await refreshAccessToken()
    await refreshAccessToken()

    expect(postMock).toHaveBeenCalledTimes(2)
    expect(storage.getItem('accessToken')).toBe('a-2')
  })

  it('rejects all concurrent callers when the network request fails', async () => {
    storage.setItem('refreshToken', 'r-1')
    const error = new Error('boom')
    postMock.mockRejectedValueOnce(error)

    const { refreshAccessToken } = await import('../tokenRefresh')
    const first = refreshAccessToken()
    const second = refreshAccessToken()

    await expect(first).rejects.toBe(error)
    await expect(second).rejects.toBe(error)
    expect(postMock).toHaveBeenCalledTimes(1)
  })
})

describe('clearTokens', () => {
  beforeEach(() => {
    vi.resetModules()
    storage.clear()
    setLocation()
  })

  afterEach(() => {
    restoreLocation()
  })

  it('removes tokens from storage and navigates to /login', async () => {
    storage.setItem('accessToken', 'a-1')
    storage.setItem('refreshToken', 'r-1')
    const { clearTokens } = await import('../tokenRefresh')
    clearTokens()
    expect(storage.getItem('accessToken')).toBeNull()
    expect(storage.getItem('refreshToken')).toBeNull()
    expect(window.location.href).toBe('/login')
  })
})
