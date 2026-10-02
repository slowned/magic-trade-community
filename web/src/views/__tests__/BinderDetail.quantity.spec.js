import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import BinderDetail from '@/views/BinderDetail.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: { getBinder: vi.fn(), addToCart: vi.fn() },
}));

const card = (id, name, quantity) => ({
  id, name, quantity,
  image_uri: `http://img/${id}.jpg`,
  price_usd: '10.00',
  color_identity: '',
  set_code: '',
  set_name: 'Set',
});

function mountBinder(cards) {
  BinderService.getBinder.mockResolvedValue({
    data: { name: 'B', user: 'seller1', card_set: cards },
  });
  const store = createStore({
    state: { token: 'tok', user: { username: 'buyer1' } },
    getters: {
      isAuthenticated: (s) => !!s.token,
      currentUser: (s) => s.user,
    },
  });
  return mount(BinderDetail, {
    global: {
      plugins: [store],
      mocks: { $route: { params: { id: '7' } } },
      stubs: { 'router-link': true },
    },
  });
}

const stockOf = (wrapper) =>
  wrapper.findAll('.spec-row')
    .filter(r => r.find('dt').text() === 'Stock')
    .map(r => r.find('dd').text());

describe('BinderDetail.vue — cantidad de copias', () => {
  beforeEach(() => vi.clearAllMocks());

  it('reports copies only through the Stock row, with no badge over the art', async () => {
    const wrapper = mountBinder([card('c1', 'Sol Ring', 3)]);
    await flushPromises();

    expect(stockOf(wrapper)).toEqual(['3']);
    expect(wrapper.find('.qty-badge').exists()).toBe(false);
  });

  it('gives every card its own stock figure', async () => {
    const wrapper = mountBinder([
      card('c1', 'Sol Ring', 2), card('c2', 'Bolt', 1), card('c3', 'Signet', 4),
    ]);
    await flushPromises();

    expect(stockOf(wrapper)).toEqual(['2', '1', '4']);
  });

  it('totals the copies next to the card count', async () => {
    const wrapper = mountBinder([
      card('c1', 'Sol Ring', 2), card('c2', 'Bolt', 1), card('c3', 'Signet', 4),
    ]);
    await flushPromises();

    expect(wrapper.vm.copyCount).toBe(7);
    expect(wrapper.find('.copies-meta').text()).toBe('(7 copias)');
  });

  it('hides the copies total when every card is a single', async () => {
    const wrapper = mountBinder([card('c1', 'Sol Ring', 1)]);
    await flushPromises();

    expect(wrapper.find('.copies-meta').exists()).toBe(false);
  });

  it('counts a card with no quantity field as one copy', async () => {
    const wrapper = mountBinder([card('c1', 'Sol Ring', undefined)]);
    await flushPromises();

    expect(wrapper.vm.copyCount).toBe(1);
    expect(stockOf(wrapper)).toEqual(['1']);
  });
});
