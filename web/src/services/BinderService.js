import axios from "axios";
import store from "@/store";

const API_URL = "http://192.168.1.114:8000/";
// const API_URL = "http://localhost:8000/";

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

// On 401, clear auth from store and localStorage so the router redirects to login
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      store.dispatch('logout');
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
  addCardById(binderId, cardId) {
    return apiClient.post(`binders/binders/${binderId}/add-card-by-id/`, { card_id: cardId });
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

  // Profile
  getProfile() {
    return apiClient.get("users/users/profile/");
  },
  updateProfile(data) {
    return apiClient.patch("users/users/profile/", data);
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
