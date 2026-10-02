import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import BinderDetail from '@/views/BinderDetail.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: { getBinder: vi.fn(), addCardById: vi.fn(), addToCart: vi.fn() },
}));

const edition = { id: 'p1', name: 'Sol Ring', set_name: 'Set', set_code: 'set', image_uri: '', price_usd: null };

function mountOwnBinder(cards = []) {
  BinderService.getBinder.mockResolvedValue({
    data: { name: 'B', user: 'owner1', card_set: cards },
  });
  const store = createStore({
    state: { token: 'tok', user: { username: 'owner1' } },
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

async function openSearchWithEdition(wrapper) {
  wrapper.vm.openAddModal('search');
  wrapper.vm.cardEditions = [edition];
  wrapper.vm.selectedEdition = edition;
  await wrapper.vm.$nextTick();
}

describe('BinderDetail.vue — agregar una carta buscada', () => {
  beforeEach(() => vi.clearAllMocks());

  it('sends quantity, language and condition picked in the modal', async () => {
    BinderService.addCardById.mockResolvedValue({
      data: { added: 'Sol Ring', quantity: 3, condition: 'SP', language: 'JA' },
    });
    const wrapper = mountOwnBinder();
    await flushPromises();
    await openSearchWithEdition(wrapper);

    await wrapper.find('.qty-input').setValue(3);
    const [language, condition] = wrapper.findAll('.copy-fields select');
    await language.setValue('JA');
    await condition.setValue('SP');
    await wrapper.find('.modal-actions .btn-primary').trigger('click');
    await flushPromises();

    expect(BinderService.addCardById).toHaveBeenCalledWith('7', 'p1', {
      quantity: 3, condition: 'SP', language: 'JA',
    });
    expect(wrapper.find('.result-msg').text()).toContain('3× Sol Ring');
  });

  it('defaults to one Near Mint English copy', async () => {
    BinderService.addCardById.mockResolvedValue({
      data: { added: 'Sol Ring', quantity: 1, condition: 'NM', language: 'EN' },
    });
    const wrapper = mountOwnBinder();
    await flushPromises();
    await openSearchWithEdition(wrapper);

    await wrapper.find('.modal-actions .btn-primary').trigger('click');
    await flushPromises();

    expect(BinderService.addCardById).toHaveBeenCalledWith('7', 'p1', {
      quantity: 1, condition: 'NM', language: 'EN',
    });
  });

  it('shows the same printing twice when held in two conditions', async () => {
    const row = (pk, condition) => ({
      id: 'p1', binder_card_id: pk, name: 'Sol Ring', quantity: 1, condition,
      set_name: 'Set', set_code: 'set', color_identity: '', image_uri: '',
    });
    const wrapper = mountOwnBinder([row(1, 'NM'), row(2, 'SP')]);
    await flushPromises();

    expect(wrapper.findAll('.card-item')).toHaveLength(2);
  });
});
