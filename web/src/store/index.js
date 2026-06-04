import { createStore } from "vuex";
import BinderService from '@/services/BinderService.js';

const store = createStore ({
  state: {
    token: localStorage.getItem('token') || '',
    user: null,
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token);
    },
    SET_USER(state, user) {
      state.user = user;
      localStorage.setItem('user', JSON.stringify(user));
    },
    CLEAR_AUTH(state) {
      state.token = '';
      state.user = null;
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    },
  },
  actions: {
    async register({ commit }, data) {
      const response = await BinderService.createUser(data);
      if (response.data.access) {
        commit('SET_TOKEN', response.data.access);
      }
    },
    async login({ commit }, credentials) {
      const response = await BinderService.generateToken(credentials);
      const token = response.data.access;
      const user = response.data.user || null;
      commit('SET_TOKEN', token);
      if (user) commit('SET_USER', user);
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
  }
});

export default store;
