import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import BinderDetail from '@/views/BinderDetail.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: { getBinder: vi.fn(), addToCart: vi.fn() },
}));

const fullCard = (overrides = {}) => ({
  id: 'c1',
  name: 'Sol Ring',
  set_name: 'Commander 2021',
  set_code: 'c21',
  collector_number: '264',
  image_uri: 'http://img/c1.jpg',
  price_usd: '3.50',
  color_identity: '',
  quantity: 2,
  condition: 'SP',
  condition_display: 'Slightly Played',
  language: 'ES',
  language_display: 'Español',
  ...overrides,
});

function mountBinder({ owner = 'seller1', me = 'buyer1', authed = true, cards = [fullCard()] } = {}) {
  BinderService.getBinder.mockResolvedValue({
    data: { name: 'B', user: owner, card_set: cards },
  });
  const store = createStore({
    state: { token: authed ? 'tok' : '', user: authed ? { username: me } : null },
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

const specs = (wrapper) =>
  Object.fromEntries(
    wrapper.findAll('.spec-row').map(r => [
      r.find('dt').text(),
      r.find('dd').text(),
    ])
  );

describe('BinderDetail.vue — card-item', () => {
  beforeEach(() => vi.clearAllMocks());

  it('identifies the card by name, edition and collector number', async () => {
    const wrapper = mountBinder();
    await flushPromises();

    expect(wrapper.find('.card-name').text()).toBe('Sol Ring');
    expect(wrapper.find('.card-set').text()).toBe('Commander 2021');
    expect(wrapper.find('.card-collector').text()).toBe('#264');
  });

  it('lists price, language, condition and stock below the rule', async () => {
    const wrapper = mountBinder();
    await flushPromises();

    expect(specs(wrapper)).toEqual({
      Precio: '$3.50',
      Idioma: 'Español',
      Condición: 'Slightly Played',
      Stock: '2',
    });
  });

  it('falls back to a dash for details the card does not carry', async () => {
    const wrapper = mountBinder({
      cards: [fullCard({
        price_usd: null, condition_display: '', language_display: '', quantity: undefined,
      })],
    });
    await flushPromises();

    expect(specs(wrapper)).toEqual({
      Precio: '—', Idioma: '—', Condición: '—', Stock: '1',
    });
  });

  it('omits the collector number when the printing has none', async () => {
    const wrapper = mountBinder({ cards: [fullCard({ collector_number: '' })] });
    await flushPromises();

    expect(wrapper.find('.card-collector').exists()).toBe(false);
  });

  it('shows an add-to-cart button with a cart icon to buyers', async () => {
    const wrapper = mountBinder();
    await flushPromises();

    const btn = wrapper.find('.add-cart-btn');
    expect(btn.exists()).toBe(true);
    expect(btn.text()).toContain('Agregar');
    expect(btn.find('svg').exists()).toBe(true);
  });

  it('adds the card to the cart when the button is clicked', async () => {
    BinderService.addToCart.mockResolvedValue({ data: {} });
    const wrapper = mountBinder();
    await flushPromises();

    await wrapper.find('.add-cart-btn').trigger('click');

    expect(BinderService.addToCart).toHaveBeenCalledWith('seller1', 'c1');
  });

  it('hides the button from the binder owner', async () => {
    const wrapper = mountBinder({ owner: 'me', me: 'me' });
    await flushPromises();

    expect(wrapper.find('.add-cart-btn').exists()).toBe(false);
  });

  it('marks the button disabled for a visitor and prompts login instead', async () => {
    const wrapper = mountBinder({ authed: false });
    await flushPromises();

    const btn = wrapper.find('.add-cart-btn');
    expect(btn.classes()).toContain('disabled');

    await btn.trigger('click');

    expect(BinderService.addToCart).not.toHaveBeenCalled();
    expect(wrapper.vm.showLoginPrompt).toBe(true);
  });
});
