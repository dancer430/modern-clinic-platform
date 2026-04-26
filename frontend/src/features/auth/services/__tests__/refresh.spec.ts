import { describe, it, expect, beforeEach, vi } from 'vitest'

const refreshRequestMock = vi.fn()

vi.mock('../../api', () => ({
  refreshRequest: (token: string) => refreshRequestMock(token),
  loginRequest: vi.fn(),
  logoutRequest: vi.fn(),
}))

import { __resetPendingForTests, refreshAccessToken } from '../refresh'

describe('refreshAccessToken (auth service)', () => {
  beforeEach(() => {
    refreshRequestMock.mockReset()
    __resetPendingForTests()
    window.localStorage.clear()
  })

  it('rejects when no refresh token is in storage', async () => {
    await expect(refreshAccessToken()).rejects.toThrow('No refresh token')
    expect(refreshRequestMock).not.toHaveBeenCalled()
  })

  it('deduplicates two concurrent calls into one network request', async () => {
    window.localStorage.setItem('refreshToken', 'r-1')
    let resolveResponse: (value: { access: string; refresh: string }) => void = () => {}
    refreshRequestMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveResponse = resolve
        }),
    )

    const first = refreshAccessToken()
    const second = refreshAccessToken()

    expect(refreshRequestMock).toHaveBeenCalledTimes(1)
    expect(refreshRequestMock).toHaveBeenCalledWith('r-1')

    resolveResponse({ access: 'a-1', refresh: 'r-2' })
    await expect(first).resolves.toBe('a-1')
    await expect(second).resolves.toBe('a-1')

    expect(window.localStorage.getItem('accessToken')).toBe('a-1')
    expect(window.localStorage.getItem('refreshToken')).toBe('r-2')
  })

  it('clears the pending promise after success so a later call hits the network again', async () => {
    window.localStorage.setItem('refreshToken', 'r-1')
    refreshRequestMock
      .mockResolvedValueOnce({ access: 'a-1', refresh: 'r-2' })
      .mockResolvedValueOnce({ access: 'a-2', refresh: 'r-3' })

    await refreshAccessToken()
    await refreshAccessToken()

    expect(refreshRequestMock).toHaveBeenCalledTimes(2)
    expect(window.localStorage.getItem('accessToken')).toBe('a-2')
    expect(window.localStorage.getItem('refreshToken')).toBe('r-3')
  })

  it('rejects all concurrent callers when the network request fails', async () => {
    window.localStorage.setItem('refreshToken', 'r-1')
    const error = new Error('boom')
    refreshRequestMock.mockRejectedValueOnce(error)

    const first = refreshAccessToken()
    const second = refreshAccessToken()

    await expect(first).rejects.toBe(error)
    await expect(second).rejects.toBe(error)
    expect(refreshRequestMock).toHaveBeenCalledTimes(1)
  })

  it('still keeps the existing refresh token when the response omits a new one', async () => {
    window.localStorage.setItem('refreshToken', 'r-keep')
    refreshRequestMock.mockResolvedValueOnce({ access: 'a-only' })

    await refreshAccessToken()

    expect(window.localStorage.getItem('refreshToken')).toBe('r-keep')
    expect(window.localStorage.getItem('accessToken')).toBe('a-only')
  })
})
