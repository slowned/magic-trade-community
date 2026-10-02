import axios from "axios";
import store from "@/store";
import router from "@/router";

const API_URL = process.env.VUE_APP_API_URL || "http://localhost:8000/";

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: false,
  headers: { Accept: "application/json" },
});

// Attach JWT token from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Single in-flight refresh shared by concurrent 401s
let refreshPromise = null;

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = apiClient
      .post('api/token/refresh/', { refresh: localStorage.getItem('refresh') })
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

// On 401, try to silently renew the access token with the stored refresh
// token and retry the request. Only if that fails, log out and redirect.
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config;
    const isAuthEndpoint = original?.url?.includes('api/token');

    if (error.response?.status !== 401 || isAuthEndpoint) {
      return Promise.reject(error);
    }

    if (!original._retry && localStorage.getItem('refresh')) {
      original._retry = true;
      try {
        const res = await refreshAccessToken();
        store.commit('SET_TOKEN', res.data.access);
        if (res.data.refresh) store.commit('SET_REFRESH', res.data.refresh);
        original.headers.Authorization = `Bearer ${res.data.access}`;
        return apiClient(original);
      } catch (e) { /* refresh expired/invalid — fall through to logout */ }
    }

    store.dispatch('logout');
    if (router.currentRoute.value.meta.requiresAuth) {
      router.push({ name: 'Login' });
    }
    return Promise.reject(error);
  }
);

export default {
  // Binders
  getBinders(params = {}) {
    return apiClient.get("binders/binders/", { params });
  },
  getMyBinders() {
    return apiClient.get("binders/binders/my-binders/");
  },
  getBinder(id) {
    return apiClient.get(`binders/binders/${id}/`);
  },
  createBinder(params) {
    return apiClient.post("binders/binders/", params);
  },
  deleteBinder(id) {
    return apiClient.delete(`binders/binders/${id}/`);
  },

  // Cards in binder
  addCardById(binderId, cardId, { quantity = 1, condition = 'NM', language = 'EN' } = {}) {
    return apiClient.post(`binders/binders/${binderId}/add-card-by-id/`, {
      card_id: cardId, quantity, condition, language,
    });
  },
  addCardsToBinder(binderId, cardNames) {
    return apiClient.post(`binders/binders/${binderId}/add-cards/`, { card_names: cardNames });
  },
  removeCardsFromBinder(binderId, cardNames) {
    return apiClient.post(`binders/binders/${binderId}/remove-cards/`, { card_names: cardNames });
  },
  importMoxfield(binderId, csvData) {
    return apiClient.post(`binders/binders/${binderId}/import-moxfield/`, { csv_data: csvData });
  },

  // Cart (P2P)
  getCarts() {
    return apiClient.get("carts/carts/");
  },
  getSellingCarts() {
    return apiClient.get("carts/carts/selling/");
  },
  getCart(cartId) {
    return apiClient.get(`carts/carts/${cartId}/`);
  },
  addToCart(sellerUsername, cardId, quantity = 1) {
    return apiClient.post("carts/carts/add-card/", {
      seller_username: sellerUsername,
      card_id: cardId,
      quantity,
    });
  },
  removeFromCart(cartId, cardId) {
    return apiClient.post(`carts/carts/${cartId}/remove-card/`, { card_id: cardId });
  },
  checkout(cartId, form) {
    return apiClient.post(`carts/carts/${cartId}/checkout/`, form);
  },
  getMessages(cartId) {
    return apiClient.get(`carts/carts/${cartId}/messages/`);
  },
  sendMessage(cartId, content) {
    return apiClient.post(`carts/carts/${cartId}/messages/`, { content });
  },
  updateOrderStatus(cartId, status) {
    return apiClient.post(`carts/carts/${cartId}/update-status/`, { status });
  },
  rateOrder(cartId, score, comment = '') {
    return apiClient.post(`carts/carts/${cartId}/rate/`, { score, comment });
  },

  // Auctions
  getAuctions(params = {}) {
    return apiClient.get("auctions/auctions/", { params });
  },
  getAuction(id) {
    return apiClient.get(`auctions/auctions/${id}/`);
  },
  getAuctionBids(id) {
    return apiClient.get(`auctions/auctions/${id}/bids/`);
  },
  placeBid(id, maxAmount) {
    return apiClient.post(`auctions/auctions/${id}/bid/`, { max_amount: maxAmount });
  },
  // Staff only
  createAuction(data) {
    return apiClient.post("auctions/auctions/", data);
  },
  updateAuction(id, data) {
    return apiClient.patch(`auctions/auctions/${id}/`, data);
  },
  deleteAuction(id) {
    return apiClient.delete(`auctions/auctions/${id}/`);
  },
  closeAuction(id) {
    return apiClient.post(`auctions/auctions/${id}/close/`);
  },
  cancelAuction(id) {
    return apiClient.post(`auctions/auctions/${id}/cancel/`);
  },
  getAuctionDefaultWindow() {
    return apiClient.get("auctions/auctions/default-window/");
  },

  // Wishlist
  getWishlist() {
    return apiClient.get("binders/wishlist/");
  },
  addToWishlist(cardNames) {
    return apiClient.post("binders/wishlist/", { card_names: cardNames });
  },
  removeFromWishlist(cardId) {
    return apiClient.delete(`binders/wishlist/${cardId}/`);
  },
  getWishlistMatches() {
    return apiClient.get('binders/wishlist/matches/');
  },

  // Profile
  getProfile() {
    return apiClient.get("users/users/profile/");
  },
  updateProfile(data) {
    return apiClient.patch("users/users/profile/", data);
  },
  getPublicProfile(username) {
    return apiClient.get(`users/users/public-profile/${encodeURIComponent(username)}/`);
  },

  // Payment proof
  uploadPaymentProof(cartId, file) {
    const form = new FormData();
    form.append('payment_proof', file);
    return apiClient.post(`carts/carts/${cartId}/upload-payment/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Auth
  createUser(data) {
    return apiClient.post("users/users/", data);
  },
  generateToken(credentials) {
    return apiClient.post("api/token/", credentials);
  },
  getMe() {
    return apiClient.get("users/users/me/");
  },

  cardExists(names) {
    return apiClient.post("cards/check-cards/", names);
  },
  autocompleteCards(q) {
    return apiClient.get("cards/autocomplete/", { params: { q } });
  },

  /**
   * Send a base64-encoded JPEG frame to the scanner endpoint.
   * Returns { card, distance, confidence } or { card: null, message }.
   *
   * @param {string} base64 - Raw base64 string (without the data:image/... prefix)
   */
  identifyCard(base64) {
    return apiClient.post("scanner/identify/", { image: base64 });
  },
};

export { apiClient };
