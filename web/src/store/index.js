import { createStore } from "vuex";
import BinderService from '@/services/BinderService.js';

function storedUser() {
  try {
    return JSON.parse(localStorage.getItem('user')) || null;
  } catch (e) {
    return null;
  }
}

const store = createStore ({
  state: {
    token: localStorage.getItem('token') || '',
    refresh: localStorage.getItem('refresh') || '',
    user: storedUser(),
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token);
    },
    SET_REFRESH(state, refresh) {
      state.refresh = refresh;
      localStorage.setItem('refresh', refresh);
    },
    SET_USER(state, user) {
      state.user = user;
      localStorage.setItem('user', JSON.stringify(user));
    },
    CLEAR_AUTH(state) {
      state.token = '';
      state.refresh = '';
      state.user = null;
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('refresh');
    },
  },
  actions: {
    async register({ dispatch }, data) {
      await BinderService.createUser(data);
      await dispatch('login', { username: data.username, password: data.password });
    },
    async login({ commit }, credentials) {
      const response = await BinderService.generateToken(credentials);
      commit('SET_TOKEN', response.data.access);
      if (response.data.refresh) commit('SET_REFRESH', response.data.refresh);
      if (response.data.user) commit('SET_USER', response.data.user);
    },
    async fetchUser({ commit, state }) {
      if (!state.token) return;
      const response = await BinderService.getMe();
      commit('SET_USER', response.data);
    },
    logout({ commit }) {
      commit('CLEAR_AUTH');
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    isStaff: (state) => !!state.user?.is_staff,
  }
});

export default store;
