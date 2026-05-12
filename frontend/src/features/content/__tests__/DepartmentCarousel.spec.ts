import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import DepartmentCarousel from '../components/DepartmentCarousel.vue'

vi.mock('../api/departments', () => ({
  portalDepartmentsApi: {
    list: vi.fn(async () => [
      { id: 1, slug: 'a', name: 'A', summary: 'sa', cover_image_url: null, display_order: 0 },
      { id: 2, slug: 'b', name: 'B', summary: 'sb', cover_image_url: null, display_order: 1 },
    ]),
  },
}))

const router = {
  push: vi.fn(),
}
vi.mock('vue-router', () => ({
  useRouter: () => router,
}))

afterEach(() => vi.clearAllMocks())

describe('DepartmentCarousel', () => {
  it('renders fetched items and routes on click', async () => {
    vi.useFakeTimers()
    const w = mount(DepartmentCarousel, { props: { intervalMs: 1000 } })
    await flushPromises()
    expect(w.text()).toContain('A')

    vi.advanceTimersByTime(1000)
    await flushPromises()
    expect(w.text()).toContain('B')

    await w.find('.dept-carousel__card').trigger('click')
    expect(router.push).toHaveBeenCalledWith('/portal/departments/b')
    vi.useRealTimers()
  })
})
