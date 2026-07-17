import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import OrderChat from '@/views/OrderChat.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: {
    getCart: vi.fn(),
    getMessages: vi.fn(),
    rateOrder: vi.fn(),
    updateOrderStatus: vi.fn(),
    uploadPaymentProof: vi.fn(),
    sendMessage: vi.fn(),
  },
}));

const makeCart = (overrides = {}) => ({
  id: 1,
  seller: 'seller1',
  buyer: 'buyer1',
  total_usd: 25,
  items: [],
  order: {
    id: 9,
    status: 'completed',
    status_display: 'Completado',
    shipping_method_display: 'Puerta a puerta',
    payment_proof_url: null,
    notes: '',
    rating: null,
    created_at: '2026-07-16T12:00:00Z',
    ...overrides.order,
  },
  ...overrides,
});

function mountOrderChat(username = 'buyer1') {
  return mount(OrderChat, {
    global: {
      stubs: { 'router-link': true },
      mocks: {
        $route: { params: { cartId: '1' } },
        $store: { getters: { currentUser: { username } } },
      },
    },
  });
}

describe('OrderChat.vue — rating', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    BinderService.getMessages.mockResolvedValue({ data: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('shows the rating form to the buyer on a completed unrated order', async () => {
    BinderService.getCart.mockResolvedValue({ data: makeCart() });
    const wrapper = mountOrderChat('buyer1');
    await flushPromises();

    expect(wrapper.find('.rating-panel').exists()).toBe(true);
    expect(wrapper.findAll('.score-btn')).toHaveLength(11);
  });

  it('does not show the rating form to the seller', async () => {
    BinderService.getCart.mockResolvedValue({ data: makeCart() });
    const wrapper = mountOrderChat('seller1');
    await flushPromises();

    expect(wrapper.find('.score-btn').exists()).toBe(false);
  });

  it('does not show the rating form while the order is not completed', async () => {
    BinderService.getCart.mockResolvedValue({ data: makeCart({ order: { status: 'shipped' } }) });
    const wrapper = mountOrderChat('buyer1');
    await flushPromises();

    expect(wrapper.find('.rating-panel').exists()).toBe(false);
  });

  it('submits the selected score and swaps the form for the rating badge', async () => {
    BinderService.getCart.mockResolvedValue({ data: makeCart() });
    const rated = makeCart({
      order: { rating: { id: 1, score: 8, comment: 'Muy bueno', rater: 'buyer1', ratee: 'seller1' } },
    });
    BinderService.rateOrder.mockResolvedValue({ data: rated });

    const wrapper = mountOrderChat('buyer1');
    await flushPromises();

    wrapper.vm.ratingScore = 8;
    wrapper.vm.ratingComment = 'Muy bueno';
    await wrapper.vm.submitRating();
    await flushPromises();

    expect(BinderService.rateOrder).toHaveBeenCalledWith('1', 8, 'Muy bueno');
    expect(wrapper.find('.score-btn').exists()).toBe(false);
    expect(wrapper.find('.rating-score-badge').text()).toBe('8/10');
  });

  it('surfaces the backend error when rating fails', async () => {
    BinderService.getCart.mockResolvedValue({ data: makeCart() });
    BinderService.rateOrder.mockRejectedValue({
      response: { data: { error: 'Este pedido ya fue puntuado.' } },
    });

    const wrapper = mountOrderChat('buyer1');
    await flushPromises();

    wrapper.vm.ratingScore = 0;
    await wrapper.vm.submitRating();
    await flushPromises();

    expect(wrapper.vm.ratingError).toBe('Este pedido ya fue puntuado.');
    expect(wrapper.find('.rating-error').text()).toBe('Este pedido ya fue puntuado.');
  });
});
