import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import AuctionDetail from '@/views/AuctionDetail.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: {
    getAuction: vi.fn(),
    getAuctionBids: vi.fn(),
    placeBid: vi.fn(),
    closeAuction: vi.fn(),
    cancelAuction: vi.fn(),
  },
}));

function makeStore({ authenticated = true, username = 'juan', isStaff = false } = {}) {
  return createStore({
    state: {
      token: authenticated ? 'fake-token' : '',
      user: authenticated ? { username, is_staff: isStaff } : null,
    },
    getters: {
      isAuthenticated: (state) => !!state.token,
      currentUser: (state) => state.user,
      isStaff: (state) => !!state.user?.is_staff,
    },
  });
}

function auctionFixture(overrides = {}) {
  return {
    id: 7,
    card: { name: 'Black Lotus', set_name: 'Alpha', set_code: 'lea', scryfall_uri: '', price_usd: '10000.00' },
    seller: 'platform',
    display_title: 'Black Lotus',
    display_image: 'http://img',
    description: '',
    condition_display: 'Near Mint',
    foil: false,
    etched: false,
    starting_price: '10000.00',
    min_increment: '500.00',
    min_next_bid: '10500.00',
    has_reserve: false,
    reserve_price: null,
    reserve_met: true,
    starts_at: '2026-08-21T21:00:00Z',
    ends_at: '2026-08-28T21:00:00Z',
    status: 'live',
    status_display: 'En curso',
    current_price: '10000.00',
    current_leader: 'maria',
    bid_count: 1,
    seconds_left: 86400,
    is_open: true,
    winner: null,
    winning_amount: null,
    cart_id: null,
    my_max_bid: null,
    is_leading: false,
    ...overrides,
  };
}

function mountDetail(storeOptions, auctionOverrides = {}) {
  BinderService.getAuction.mockResolvedValue({ data: auctionFixture(auctionOverrides) });
  BinderService.getAuctionBids.mockResolvedValue({ data: [] });
  return mount(AuctionDetail, {
    props: { id: '7' },
    global: {
      plugins: [makeStore(storeOptions)],
      stubs: { 'router-link': true },
    },
  });
}

describe('AuctionDetail.vue', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows the bid form to a logged-in user on a live auction', async () => {
    const wrapper = mountDetail();
    await flushPromises();

    expect(wrapper.vm.canBid).toBe(true);
    expect(wrapper.find('.bid-form').exists()).toBe(true);
  });

  it('hides the bid form from anonymous visitors', async () => {
    const wrapper = mountDetail({ authenticated: false });
    await flushPromises();

    expect(wrapper.vm.canBid).toBe(false);
    expect(wrapper.find('.bid-form').exists()).toBe(false);
  });

  it('will not let the seller bid on their own auction', async () => {
    const wrapper = mountDetail({ username: 'platform', isStaff: true });
    await flushPromises();

    expect(wrapper.vm.canBid).toBe(false);
  });

  it('submits the max amount and takes the updated auction from the response', async () => {
    const wrapper = mountDetail();
    await flushPromises();
    BinderService.placeBid.mockResolvedValue({
      data: auctionFixture({ current_price: '10500.00', current_leader: 'juan', is_leading: true, my_max_bid: '20000.00' }),
    });
    BinderService.getAuctionBids.mockResolvedValue({ data: [] });

    wrapper.vm.bidAmount = '20000';
    await wrapper.vm.submitBid();

    expect(BinderService.placeBid).toHaveBeenCalledWith('7', '20000');
    expect(wrapper.vm.auction.is_leading).toBe(true);
    expect(wrapper.vm.bidAmount).toBe('');
  });

  it("surfaces the backend's rejection message", async () => {
    const wrapper = mountDetail();
    await flushPromises();
    BinderService.placeBid.mockRejectedValue({ response: { data: { error: 'La puja mínima es $10500.' } } });

    wrapper.vm.bidAmount = '1';
    await wrapper.vm.submitBid();

    expect(wrapper.vm.bidError).toBe('La puja mínima es $10500.');
  });

  it('offers staff controls only to staff on an active auction', async () => {
    const asBidder = mountDetail();
    await flushPromises();
    const asStaff = mountDetail({ username: 'admin', isStaff: true });
    await flushPromises();

    expect(asBidder.find('.staff-box').exists()).toBe(false);
    expect(asStaff.find('.staff-box').exists()).toBe(true);
  });

  it('points the winner at their cart once the auction closes', async () => {
    const wrapper = mountDetail({}, {
      status: 'closed', is_open: false, winner: 'juan',
      winning_amount: '12500.00', cart_id: 42, seconds_left: 0,
    });
    await flushPromises();

    expect(wrapper.vm.isWinner).toBe(true);
    expect(wrapper.find('.outcome').text()).toContain('juan');
  });
});
