import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import CartView from '@/views/Cart.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: {
    getCarts: vi.fn(),
    getSellingCarts: vi.fn(),
    checkout: vi.fn(),
    removeFromCart: vi.fn(),
  },
}));

const makeCart = (overrides = {}) => ({
  id: 1,
  seller: 'seller1',
  buyer: 'buyer1',
  item_count: 1,
  total_usd: 25,
  order: null,
  items: [
    { id: 1, quantity: 1, card: { id: 'c1', name: 'Card One', set_name: 'Set', image_uri: '', price_usd: '25.00' } },
  ],
  ...overrides,
});

function mountCart() {
  return mount(CartView, {
    global: {
      stubs: { 'router-link': true },
      mocks: { $router: { push: vi.fn() } },
    },
  });
}

describe('Cart.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    BinderService.getCarts.mockResolvedValue({ data: [makeCart()] });
    BinderService.getSellingCarts.mockResolvedValue({ data: [] });
  });

  it('loads buying and selling carts on mount', async () => {
    const wrapper = mountCart();
    await flushPromises();

    expect(BinderService.getCarts).toHaveBeenCalled();
    expect(BinderService.getSellingCarts).toHaveBeenCalled();
    expect(wrapper.vm.carts).toHaveLength(1);
    expect(wrapper.vm.loading).toBe(false);
  });

  it('opens the checkout modal with a clean form for the selected cart', async () => {
    const wrapper = mountCart();
    await flushPromises();

    wrapper.vm.openCheckout(wrapper.vm.carts[0]);

    expect(wrapper.vm.checkoutCart).toEqual(wrapper.vm.carts[0]);
    expect(wrapper.vm.checkoutForm).toEqual({ shipping_method: '', notes: '' });
    expect(wrapper.vm.unavailableCards).toEqual([]);
  });

  it('confirms checkout and redirects to the order chat on success', async () => {
    const wrapper = mountCart();
    await flushPromises();
    wrapper.vm.openCheckout(wrapper.vm.carts[0]);
    wrapper.vm.checkoutForm.shipping_method = 'door_to_door';

    const updatedCart = makeCart({ id: 5, order: { id: 99, status: 'pending' } });
    BinderService.checkout.mockResolvedValue({ data: updatedCart });

    await wrapper.vm.confirmCheckout();

    expect(BinderService.checkout).toHaveBeenCalledWith(1, { shipping_method: 'door_to_door', notes: '' });
    expect(wrapper.vm.checkoutCart).toBeNull();
    expect(wrapper.vm.$router.push).toHaveBeenCalledWith({ name: 'OrderChat', params: { cartId: 5 } });
  });

  it('surfaces unavailable cards on a 409 checkout conflict and refetches carts', async () => {
    const wrapper = mountCart();
    await flushPromises();
    wrapper.vm.openCheckout(wrapper.vm.carts[0]);
    wrapper.vm.checkoutForm.shipping_method = 'door_to_door';

    BinderService.checkout.mockRejectedValue({
      response: {
        data: {
          error: 'Algunas cartas ya no están disponibles.',
          unavailable_cards: [{ id: 'c1', name: 'Card One' }],
        },
      },
    });
    BinderService.getCarts.mockClear();

    await wrapper.vm.confirmCheckout();

    expect(wrapper.vm.checkoutError).toBe('Algunas cartas ya no están disponibles.');
    expect(wrapper.vm.unavailableCards).toEqual([{ id: 'c1', name: 'Card One' }]);
    expect(wrapper.vm.checkoutCart).not.toBeNull();
    expect(BinderService.getCarts).toHaveBeenCalled();
    expect(wrapper.vm.$router.push).not.toHaveBeenCalled();
  });

  it('removes an item and drops the whole cart when it becomes empty', async () => {
    const wrapper = mountCart();
    await flushPromises();
    const cart = wrapper.vm.carts[0];

    BinderService.removeFromCart.mockResolvedValue({ data: { deleted: true } });

    await wrapper.vm.removeItem(cart, cart.items[0]);

    expect(BinderService.removeFromCart).toHaveBeenCalledWith(cart.id, cart.items[0].card.id);
    expect(wrapper.vm.carts).toHaveLength(0);
  });
});
