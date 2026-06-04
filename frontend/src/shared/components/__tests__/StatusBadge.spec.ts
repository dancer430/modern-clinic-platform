import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../StatusBadge.vue'

describe('StatusBadge', () => {
  it('renders translated appointment status + maps variant', () => {
    const w = mount(StatusBadge, { props: { status: 'pending' } })
    expect(w.attributes('data-variant')).toBe('pending')
    expect(w.text()).toContain('Pending')
  })
  it('maps cancelled to cancelled variant', () => {
    expect(mount(StatusBadge, { props: { status: 'cancelled' } }).attributes('data-variant')).toBe('cancelled')
  })
  it('falls back to neutral for unknown status', () => {
    expect(mount(StatusBadge, { props: { status: 'whatever' } }).attributes('data-variant')).toBe('neutral')
  })
})
