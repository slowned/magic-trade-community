import { createStore } from "vuex";
import apiClient from '@/services/BinderService.js';

const store = createStore ({
  state: {
    token: localStorage.getItem('token') || '',
    user: null,
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem('token', token)
    },
    SET_USER(state, user) {
      state.user = user;
      localStorage.setItem('user', user)
    },
    CLEAR_AUTH(state) {
      state.token = '';
      state.user = null;
      localStorage.removeItem('user')
      localStorage.removeItem('token')
    },
  },
  actions: {
    async register({ commit }, data) {
      try {
        const response = await apiClient.createUser(data);
        // tiene q retornar el token para la session
        commit('SET_TOKEN', response.data.access);
      } catch (error) {
        console.error("Register failed:", error);
      }
    },
    async login({ commit }, credentials) {
      try {
        const response = await apiClient.generateToken(credentials);
        const token = response.data.access;
        commit('SET_TOKEN', token);
        await this.dispatch('fetchUser'); // Obtener datos del usuario
      } catch (error) {
        console.error("Login failed:", error);
      }
    },
    async fetchUser({ commit, state }) {
      if (state.token) {
        console.log("ELTOKEN:", state.token);

        try {
          const response = await apiClient.get('/users/users/', {
            headers: { Authorization: `Bearer ${state.token}` }
          });
          commit('SET_USER', response.data);
        } catch (error) {
          console.error("Failed to fetch user:", error);
          commit('CLEAR_AUTH');
        }
      }
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
