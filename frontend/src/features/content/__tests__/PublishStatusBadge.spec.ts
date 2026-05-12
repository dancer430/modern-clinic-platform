import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PublishStatusBadge from '../components/PublishStatusBadge.vue'

describe('PublishStatusBadge', () => {
  it('renders pending', () => {
    const w = mount(PublishStatusBadge, { props: { status: 'pending' } })
    expect(w.text()).toContain('Pending review')
    expect(w.attributes('data-variant')).toBe('pending')
  })
  it('shows published when approved + published', () => {
    const w = mount(PublishStatusBadge, { props: { status: 'approved', published: true } })
    expect(w.text()).toContain('Published')
  })
  it('shows rejected', () => {
    const w = mount(PublishStatusBadge, { props: { status: 'rejected' } })
    expect(w.attributes('data-variant')).toBe('rejected')
  })
})
