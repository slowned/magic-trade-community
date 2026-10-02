import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createStore } from 'vuex';
import BinderDetail from '@/views/BinderDetail.vue';
import BinderService from '@/services/BinderService';

vi.mock('@/services/BinderService', () => ({
  default: {
    getBinder: vi.fn(),
    importMoxfield: vi.fn(),
    addCardsToBinder: vi.fn(),
  },
}));

function mountAsOwner() {
  const store = createStore({
    state: { token: 'fake-token', user: { username: 'owner1' } },
    getters: {
      isAuthenticated: (state) => !!state.token,
      currentUser: (state) => state.user,
    },
  });
  return mount(BinderDetail, {
    global: {
      plugins: [store],
      mocks: { $route: { params: { id: '42' } } },
      stubs: { 'router-link': true },
    },
  });
}

const CSV = 'Count,Name,Edition,Condition,Language,Foil\n4,Lightning Bolt,M10,Near Mint,English,';

// jsdom's FileReader needs a real Blob-backed File to read from.
const csvFile = (text, name = 'moxfield.csv') =>
  new File([text], name, { type: 'text/csv' });

describe('BinderDetail.vue — importar CSV desde archivo', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    BinderService.getBinder.mockResolvedValue({
      data: { name: 'Binder', user: 'owner1', card_set: [] },
    });
  });

  it('shows the file picker on the CSV tab', async () => {
    const wrapper = mountAsOwner();
    await flushPromises();

    wrapper.vm.openAddModal('csv');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.csv-dropzone input[type="file"]').exists()).toBe(true);
  });

  it('reads the chosen file into csvData and remembers its name', async () => {
    const wrapper = mountAsOwner();
    await flushPromises();
    wrapper.vm.openAddModal('csv');

    await wrapper.vm.onCsvFile({ target: { files: [csvFile(CSV)], value: '' } });
    // FileReader resolves on a later tick.
    await vi.waitFor(() => expect(wrapper.vm.csvData).toBe(CSV));

    expect(wrapper.vm.csvFileName).toBe('moxfield.csv');
    expect(wrapper.vm.csvFileError).toBeNull();
  });

  it('sends the uploaded contents through import-moxfield', async () => {
    const wrapper = mountAsOwner();
    await flushPromises();
    wrapper.vm.openAddModal('csv');
    BinderService.importMoxfield.mockResolvedValue({ data: { added: ['Lightning Bolt'], not_found: [] } });

    await wrapper.vm.onCsvFile({ target: { files: [csvFile(CSV)], value: '' } });
    await vi.waitFor(() => expect(wrapper.vm.csvData).toBe(CSV));
    await wrapper.vm.handleAdd();

    expect(BinderService.importMoxfield).toHaveBeenCalledWith('42', CSV);
  });

  it('rejects a file over 2 MB without touching csvData', async () => {
    const wrapper = mountAsOwner();
    await flushPromises();
    wrapper.vm.openAddModal('csv');

    const huge = csvFile('x'.repeat(2 * 1024 * 1024 + 1), 'huge.csv');
    await wrapper.vm.onCsvFile({ target: { files: [huge], value: '' } });

    expect(wrapper.vm.csvFileError).toBe('El archivo supera los 2 MB.');
    expect(wrapper.vm.csvData).toBe('');
    expect(wrapper.vm.csvFileName).toBe('');
  });

  it('clears the picked file when the modal closes', async () => {
    const wrapper = mountAsOwner();
    await flushPromises();
    wrapper.vm.openAddModal('csv');

    await wrapper.vm.onCsvFile({ target: { files: [csvFile(CSV)], value: '' } });
    await vi.waitFor(() => expect(wrapper.vm.csvFileName).toBe('moxfield.csv'));

    wrapper.vm.closeAddModal();

    expect(wrapper.vm.csvData).toBe('');
    expect(wrapper.vm.csvFileName).toBe('');
  });
});
