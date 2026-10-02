import { describe, it, expect, vi, beforeEach } from 'vitest';
import store from '@/store';
import BinderService from '@/services/BinderService.js';

vi.mock('@/services/BinderService.js', () => ({
  default: {
    generateToken: vi.fn(),
    createUser: vi.fn(),
    getMe: vi.fn(),
  },
}));

describe('store — sesión', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    store.commit('CLEAR_AUTH');
  });

  it('login stores token, refresh and user in state and localStorage', async () => {
    BinderService.generateToken.mockResolvedValue({
      data: { access: 'acc', refresh: 'ref', user: { id: 1, username: 'u1' } },
    });

    await store.dispatch('login', { username: 'u1', password: 'p' });

    expect(store.getters.isAuthenticated).toBe(true);
    expect(store.getters.currentUser.username).toBe('u1');
    expect(localStorage.getItem('token')).toBe('acc');
    expect(localStorage.getItem('refresh')).toBe('ref');
    expect(JSON.parse(localStorage.getItem('user')).username).toBe('u1');
  });

  it('register creates the user and logs in with the same credentials', async () => {
    BinderService.createUser.mockResolvedValue({ data: { id: 2, username: 'nuevo' } });
    BinderService.generateToken.mockResolvedValue({
      data: { access: 'acc2', refresh: 'ref2', user: { id: 2, username: 'nuevo' } },
    });

    await store.dispatch('register', { username: 'nuevo', password: 'p', email: 'a@b.c' });

    expect(BinderService.createUser).toHaveBeenCalled();
    expect(BinderService.generateToken).toHaveBeenCalledWith({ username: 'nuevo', password: 'p' });
    expect(store.getters.isAuthenticated).toBe(true);
    expect(store.getters.currentUser.username).toBe('nuevo');
  });

  it('logout clears state and localStorage', async () => {
    store.commit('SET_TOKEN', 'acc');
    store.commit('SET_REFRESH', 'ref');
    store.commit('SET_USER', { id: 1, username: 'u1' });

    await store.dispatch('logout');

    expect(store.getters.isAuthenticated).toBe(false);
    expect(store.getters.currentUser).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('refresh')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('rehydrates token and user from localStorage on store creation', async () => {
    localStorage.setItem('token', 'persisted');
    localStorage.setItem('user', JSON.stringify({ id: 3, username: 'persistido' }));

    vi.resetModules();
    const fresh = (await import('@/store')).default;

    expect(fresh.getters.isAuthenticated).toBe(true);
    expect(fresh.getters.currentUser.username).toBe('persistido');
  });

  it('ignores a corrupt persisted user', async () => {
    localStorage.setItem('user', '{not json');

    vi.resetModules();
    const fresh = (await import('@/store')).default;

    expect(fresh.getters.currentUser).toBeNull();
  });
});
