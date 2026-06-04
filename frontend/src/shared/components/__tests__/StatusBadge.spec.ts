import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../StatusBadge.vue'

describe('StatusBadge', () => {
  it('renders translated appointment status + maps variant', () => {
    const w = mount(StatusBadge, { props: { kind: 'appointment', status: 'pending' } })
    expect(w.attributes('data-variant')).toBe('pending')
    expect(w.text()).toContain('Pending')
  })
  it('maps cancelled appointment to cancelled variant', () => {
    expect(mount(StatusBadge, { props: { kind: 'appointment', status: 'cancelled' } }).attributes('data-variant')).toBe('cancelled')
  })
  it('maps publish statuses', () => {
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'published' } }).attributes('data-variant')).toBe('completed')
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'pending' } }).attributes('data-variant')).toBe('pending')
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'rejected' } }).attributes('data-variant')).toBe('cancelled')
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'draft' } }).attributes('data-variant')).toBe('neutral')
  })
})
