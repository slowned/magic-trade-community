import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import BinderDetail from '@/views/BinderDetail.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: {
    getBinder: vi.fn(),
    addToCart: vi.fn(),
  },
}));

function makeStore(isAuthenticated) {
  return createStore({
    state: { token: isAuthenticated ? 'fake-token' : '', user: isAuthenticated ? { username: 'buyer1' } : null },
    getters: {
      isAuthenticated: (state) => !!state.token,
      currentUser: (state) => state.user,
    },
  });
}

function mountBinderDetail(isAuthenticated) {
  return mount(BinderDetail, {
    global: {
      plugins: [makeStore(isAuthenticated)],
      mocks: { $route: { params: { id: '42' } } },
      stubs: { 'router-link': true },
    },
  });
}

const card = { id: 'c1', name: 'Card One', image_uri: '', price_usd: '10.00', color_identity: '', set_code: '' };

describe('BinderDetail.vue — handleAddToCart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    BinderService.getBinder.mockResolvedValue({
      data: { name: 'Binder', user: 'seller1', card_set: [card] },
    });
  });

  it('prompts login instead of calling the API when not authenticated', async () => {
    const wrapper = mountBinderDetail(false);
    await flushPromises();

    wrapper.vm.handleAddToCart(card);

    expect(wrapper.vm.showLoginPrompt).toBe(true);
    expect(BinderService.addToCart).not.toHaveBeenCalled();
  });

  it('adds the card to the cart and shows a toast when authenticated', async () => {
    const wrapper = mountBinderDetail(true);
    await flushPromises();
    BinderService.addToCart.mockResolvedValue({ data: {} });

    wrapper.vm.handleAddToCart(card);
    await flushPromises();

    expect(BinderService.addToCart).toHaveBeenCalledWith('seller1', 'c1');
    expect(wrapper.vm.cartToast).toBe('Card One');
  });
});
