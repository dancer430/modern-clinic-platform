import { describe, it, expect } from 'vitest'

import { SLOT_TIMES, toApiTime, toLocalDateString } from '../types'

describe('appointments/types helpers', () => {
  it('SLOT_TIMES exposes the 15 allowed clinic slots in order', () => {
    expect(SLOT_TIMES.length).toBe(15)
    expect(SLOT_TIMES[0]).toBe('08:00')
    expect(SLOT_TIMES[SLOT_TIMES.length - 1]).toBe('17:00')
    expect(SLOT_TIMES.includes('12:00' as never)).toBe(false)
  })

  it('toLocalDateString formats local-zone date as YYYY-MM-DD with zero padding', () => {
    expect(toLocalDateString(new Date(2026, 0, 5))).toBe('2026-01-05')
    expect(toLocalDateString(new Date(2026, 11, 31))).toBe('2026-12-31')
  })

  it('toApiTime appends seconds for backend slot_time field', () => {
    expect(toApiTime('09:00')).toBe('09:00:00')
    expect(toApiTime('17:30')).toBe('17:30:00')
  })
})
