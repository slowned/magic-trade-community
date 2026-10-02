import { describe, it, expect, beforeEach } from 'vitest';
import { apiClient } from '@/services/BinderService';
import store from '@/store';

// Fake axios adapter so the interceptors run against controlled responses
function jsonResponse(config, status, data) {
  if (status >= 400) {
    const error = new Error(`Request failed with status code ${status}`);
    error.config = config;
    error.response = { status, data, config };
    error.isAxiosError = true;
    return Promise.reject(error);
  }
  return Promise.resolve({ status, data, config, headers: {}, statusText: 'OK' });
}

describe('session interceptor — silent token refresh', () => {
  beforeEach(() => {
    localStorage.clear();
    store.commit('CLEAR_AUTH');
  });

  it('renews the access token on 401 and retries the original request', async () => {
    localStorage.setItem('token', 'expired-access');
    localStorage.setItem('refresh', 'valid-refresh');

    const calls = [];
    apiClient.defaults.adapter = (config) => {
      calls.push(config.url);
      if (config.url === 'api/token/refresh/') {
        expect(JSON.parse(config.data)).toEqual({ refresh: 'valid-refresh' });
        return jsonResponse(config, 200, { access: 'new-access' });
      }
      return config.headers.Authorization === 'Bearer new-access'
        ? jsonResponse(config, 200, { ok: true })
        : jsonResponse(config, 401, { detail: 'token expired' });
    };

    const res = await apiClient.get('binders/binders/my-binders/');

    expect(res.data).toEqual({ ok: true });
    expect(localStorage.getItem('token')).toBe('new-access');
    expect(calls).toEqual([
      'binders/binders/my-binders/',
      'api/token/refresh/',
      'binders/binders/my-binders/',
    ]);
  });

  it('logs out when the refresh token is also rejected', async () => {
    store.commit('SET_TOKEN', 'expired-access');
    store.commit('SET_REFRESH', 'dead-refresh');

    apiClient.defaults.adapter = (config) => jsonResponse(config, 401, { detail: 'expired' });

    await expect(apiClient.get('binders/binders/my-binders/')).rejects.toMatchObject({
      response: { status: 401 },
    });
    expect(store.getters.isAuthenticated).toBe(false);
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('refresh')).toBeNull();
  });

  it('does not try to refresh on a failed login (401 from api/token/)', async () => {
    const calls = [];
    apiClient.defaults.adapter = (config) => {
      calls.push(config.url);
      return jsonResponse(config, 401, { detail: 'bad credentials' });
    };

    await expect(
      apiClient.post('api/token/', { username: 'u', password: 'mala' })
    ).rejects.toMatchObject({ response: { status: 401 } });
    expect(calls).toEqual(['api/token/']);
  });
});
