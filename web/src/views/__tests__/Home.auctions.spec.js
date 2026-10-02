import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import Home from '@/views/Home.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: { getAuctions: vi.fn() },
}));

function makeStore(authenticated = false) {
  return createStore({
    state: { token: authenticated ? 'fake-token' : '' },
    getters: { isAuthenticated: (state) => !!state.token },
  });
}

function auction(id, overrides = {}) {
  return {
    id,
    card: { name: `Card ${id}`, set_name: 'Alpha' },
    display_title: `Card ${id}`,
    display_image: 'http://img',
    condition_display: 'Near Mint',
    foil: false,
    status: 'live',
    status_display: 'En curso',
    current_price: '10000.00',
    bid_count: 2,
    seconds_left: 86400,
    has_reserve: false,
    reserve_met: true,
    winner: null,
    my_max_bid: null,
    is_leading: false,
    ...overrides,
  };
}

function mountHome() {
  return mount(Home, {
    global: {
      plugins: [makeStore()],
      stubs: { 'router-link': true },
    },
  });
}

describe('Home.vue — auctions on the landing', () => {
  beforeEach(() => vi.clearAllMocks());

  it('asks the API only for auctions that are still open', async () => {
    BinderService.getAuctions.mockResolvedValue({ data: [] });
    mountHome();
    await flushPromises();

    expect(BinderService.getAuctions).toHaveBeenCalledWith({ status: 'open' });
  });

  it('spotlights the live auction closing soonest and lists the rest', async () => {
    BinderService.getAuctions.mockResolvedValue({
      data: [auction(1), auction(2), auction(3)],
    });
    const wrapper = mountHome();
    await flushPromises();

    expect(wrapper.vm.featured.id).toBe(1);
    expect(wrapper.vm.restAuctions.map(a => a.id)).toEqual([2, 3]);
    expect(wrapper.find('.hero-feature').exists()).toBe(true);
    expect(wrapper.find('.auctions-strip').exists()).toBe(true);
  });

  it('prefers a live auction over one that has not opened yet', async () => {
    BinderService.getAuctions.mockResolvedValue({
      data: [auction(1, { status: 'scheduled' }), auction(2, { status: 'live' })],
    });
    const wrapper = mountHome();
    await flushPromises();

    expect(wrapper.vm.featured.id).toBe(2);
  });

  it('hides both auction blocks when there is nothing running', async () => {
    BinderService.getAuctions.mockResolvedValue({ data: [] });
    const wrapper = mountHome();
    await flushPromises();

    expect(wrapper.vm.featured).toBeNull();
    expect(wrapper.find('.hero-feature').exists()).toBe(false);
    expect(wrapper.find('.auctions-strip').exists()).toBe(false);
  });

  it('still renders the landing when the auctions request fails', async () => {
    BinderService.getAuctions.mockRejectedValue(new Error('network'));
    const wrapper = mountHome();
    await flushPromises();

    expect(wrapper.vm.auctions).toEqual([]);
    expect(wrapper.find('.hero').exists()).toBe(true);
  });

  it('drops the strip when a single auction leaves nothing after the spotlight', async () => {
    BinderService.getAuctions.mockResolvedValue({ data: [auction(1)] });
    const wrapper = mountHome();
    await flushPromises();

    expect(wrapper.vm.restAuctions).toEqual([]);
    expect(wrapper.find('.auctions-strip').exists()).toBe(false);
  });

  it('ticks the countdown down without refetching', async () => {
    BinderService.getAuctions.mockResolvedValue({ data: [auction(1, { seconds_left: 10 })] });
    const wrapper = mountHome();
    await flushPromises();

    wrapper.vm.decrementCountdowns();

    expect(wrapper.vm.featured.seconds_left).toBe(9);
    expect(BinderService.getAuctions).toHaveBeenCalledTimes(1);
  });
});
