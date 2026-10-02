<template>
  <div class="wishlist container">
    <div class="page-header">
      <div class="header-top">
        <div>
          <h1>Wishlist</h1>
          <p class="subtitle">Cartas que querés conseguir</p>
        </div>
        <div class="header-actions">
          <button class="btn-ghost" @click="fetchMatches" :disabled="matchesLoading">
            {{ matchesLoading ? 'Buscando...' : '🔍 Ver quién tiene tus cartas' }}
          </button>
          <button class="btn-primary" @click="showAddModal = true">+ Agregar por lista</button>
        </div>
      </div>
      <div class="search-wrapper">
        <input
          v-model="searchQuery"
          @input="onSearchInput"
          @focus="showSuggestions = suggestions.length > 0"
          @blur="hideSuggestionsDelayed"
          @keydown.esc="clearSearch"
          placeholder="Buscar carta para agregar..."
          class="search-input"
          autocomplete="off"
        />
        <div v-if="searchLoading" class="search-spinner"></div>
        <ul v-if="showSuggestions && suggestions.length" class="suggestions-list">
          <li
            v-for="name in suggestions"
            :key="name"
            @mousedown.prevent="selectSuggestion(name)"
            class="suggestion-item"
          >
            {{ name }}
          </li>
        </ul>
      </div>
      <div v-if="searchError" class="search-error">{{ searchError }}</div>
      <div v-if="addSuccess" class="search-success">{{ addSuccess }}</div>
    </div>

    <div v-if="loading" class="state-msg">Cargando wishlist...</div>

    <div v-else-if="cards.length === 0" class="empty-state">
      <div class="empty-icon">🎯</div>
      <p>Tu wishlist está vacía.</p>
      <button class="btn-primary" @click="showAddModal = true">Agregar cartas</button>
    </div>

    <div v-else class="cards-grid">
      <div v-for="entry in cards" :key="entry.id" class="card-item">
        <div class="card-img-wrapper">
          <img
            v-if="entry.card.image_uri"
            :src="entry.card.image_uri"
            :alt="entry.card.name"
            class="card-img"
            loading="lazy"
          />
          <div v-else class="card-img-placeholder">{{ entry.card.name }}</div>
        </div>
        <div class="card-info">
          <span class="card-name" :title="entry.card.name">{{ entry.card.name }}</span>
          <span class="card-price" v-if="entry.card.price_usd">${{ entry.card.price_usd }}</span>
        </div>
        <button class="remove-btn" @click="removeCard(entry)" title="Quitar de wishlist">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Matches section -->
    <div v-if="matches !== null" class="matches-section">
      <div class="matches-header">
        <h2>Usuarios que tienen tus cartas</h2>
        <button class="close-matches" @click="matches = null" title="Cerrar">✕</button>
      </div>

      <div v-if="matchesError" class="state-msg">{{ matchesError }}</div>

      <div v-else-if="matches.length === 0" class="state-msg">
        Ningún usuario tiene cartas de tu wishlist en sus binders públicos.
      </div>

      <div v-else class="matches-list">
        <div v-for="match in matches" :key="match.username" class="match-card">
          <div class="match-user">
            <div class="match-avatar">{{ match.username[0].toUpperCase() }}</div>
            <div>
              <span class="match-username">{{ match.username }}</span>
              <span class="match-count">{{ match.match_count }} carta{{ match.match_count !== 1 ? 's' : '' }}</span>
            </div>
          </div>
          <div class="match-cards">
            <div
              v-for="card in match.cards"
              :key="card.id + '_' + card.binder_id"
              class="match-card-item"
              :title="card.name + (card.price_usd ? ' — $' + card.price_usd : '')"
            >
              <div class="match-card-img-wrapper">
                <img v-if="card.image_uri" :src="card.image_uri" :alt="card.name" class="match-card-img" loading="lazy" />
                <div v-else class="match-card-placeholder">{{ card.name }}</div>
                <span v-if="card.quantity > 1" class="match-card-qty-badge">x{{ card.quantity }}</span>
              </div>
              <span class="match-card-name">{{ card.name }}</span>
              <span v-if="card.price_usd" class="match-card-price">${{ card.price_usd }}</span>
              <button
                class="match-add-cart-btn"
                :class="{ success: cartFeedback[match.username + '_' + card.id] === 'ok', error: cartFeedback[match.username + '_' + card.id] === 'err' }"
                :disabled="!!addingToCart[match.username + '_' + card.id]"
                @click="addToCart(match.username, card)"
              >
                <template v-if="cartFeedback[match.username + '_' + card.id] === 'ok'">✓ Agregado</template>
                <template v-else-if="cartFeedback[match.username + '_' + card.id] === 'err'">Error</template>
                <template v-else-if="addingToCart[match.username + '_' + card.id]">...</template>
                <template v-else>+ Carrito</template>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Card Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal">
        <h3>Agregar a wishlist</h3>
        <p class="modal-hint">Una carta por línea</p>
        <textarea
          v-model="newCardNames"
          placeholder="Lightning Bolt&#10;Force of Will&#10;Black Lotus"
          rows="8"
        />
        <div v-if="addError" class="error-msg">{{ addError }}</div>
        <div class="modal-actions">
          <button class="btn-ghost" @click="closeAddModal">Cancelar</button>
          <button class="btn-primary" @click="addCards" :disabled="adding || !newCardNames.trim()">
            {{ adding ? 'Agregando...' : 'Agregar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'WishlistView',
  data() {
    return {
      cards: [],
      loading: true,
      showAddModal: false,
      newCardNames: '',
      adding: false,
      addError: null,
      // Matches
      matches: null,
      matchesLoading: false,
      matchesError: null,
      // Inline search
      searchQuery: '',
      suggestions: [],
      searchLoading: false,
      showSuggestions: false,
      searchError: null,
      addSuccess: null,
      searchTimer: null,
      // Cart actions from matches
      addingToCart: {},
      cartFeedback: {},
    };
  },
  created() {
    this.fetchWishlist();
  },
  methods: {
    fetchWishlist() {
      this.loading = true;
      BinderService.getWishlist()
        .then(r => { this.cards = r.data; })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    },
    closeAddModal() {
      this.showAddModal = false;
      this.newCardNames = '';
      this.addError = null;
    },
    async addCards() {
      this.addError = null;
      this.adding = true;
      const cardNames = this.newCardNames
        .split('\n')
        .map(l => l.trim())
        .filter(l => l.length > 0);

      try {
        const res = await BinderService.addToWishlist(cardNames);
        if (res.data.not_found?.length) {
          this.addError = `No encontradas: ${res.data.not_found.join(', ')}`;
        }
        if (res.data.added?.length) {
          this.closeAddModal();
          this.fetchWishlist();
        }
      } catch (e) {
        this.addError = 'Error al agregar las cartas.';
        console.error(e);
      } finally {
        this.adding = false;
      }
    },
    async fetchMatches() {
      this.matchesLoading = true;
      this.matchesError = null;
      this.matches = null;
      try {
        const res = await BinderService.getWishlistMatches();
        this.matches = res.data;
      } catch {
        this.matchesError = 'Error al buscar matches.';
        this.matches = [];
      } finally {
        this.matchesLoading = false;
      }
    },
    onSearchInput() {
      this.searchError = null;
      this.addSuccess = null;
      clearTimeout(this.searchTimer);
      if (this.searchQuery.trim().length < 2) {
        this.suggestions = [];
        this.showSuggestions = false;
        return;
      }
      this.searchLoading = true;
      this.searchTimer = setTimeout(async () => {
        try {
          const res = await BinderService.autocompleteCards(this.searchQuery.trim());
          this.suggestions = res.data;
          this.showSuggestions = this.suggestions.length > 0;
        } catch {
          this.suggestions = [];
        } finally {
          this.searchLoading = false;
        }
      }, 300);
    },
    hideSuggestionsDelayed() {
      setTimeout(() => { this.showSuggestions = false; }, 150);
    },
    async selectSuggestion(name) {
      this.showSuggestions = false;
      this.suggestions = [];
      this.searchQuery = name;
      this.searchError = null;
      this.addSuccess = null;
      try {
        const res = await BinderService.addToWishlist([name]);
        if (res.data.not_found?.length) {
          this.searchError = `"${name}" no es una carta válida.`;
        } else if (res.data.added?.length) {
          this.addSuccess = `"${name}" agregada a tu wishlist.`;
          this.searchQuery = '';
          this.fetchWishlist();
        }
      } catch {
        this.searchError = 'Error al agregar la carta.';
      }
    },
    clearSearch() {
      this.searchQuery = '';
      this.suggestions = [];
      this.showSuggestions = false;
      this.searchError = null;
      this.addSuccess = null;
    },
    async removeCard(entry) {
      try {
        await BinderService.removeFromWishlist(entry.card.id);
        this.cards = this.cards.filter(c => c.id !== entry.id);
      } catch (e) {
        console.error(e);
      }
    },
    async addToCart(username, card) {
      const key = `${username}_${card.id}`;
      this.addingToCart[key] = true;
      this.cartFeedback[key] = null;
      try {
        await BinderService.addToCart(username, card.id);
        this.cartFeedback[key] = 'ok';
        setTimeout(() => { this.cartFeedback[key] = null; }, 2500);
      } catch {
        this.cartFeedback[key] = 'err';
        setTimeout(() => { this.cartFeedback[key] = null; }, 3000);
      } finally {
        this.addingToCart[key] = false;
      }
    }
  }
};
</script>

<style scoped>
.wishlist {
  padding-top: 40px;
  padding-bottom: 64px;
}

.page-header {
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h1 { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
.subtitle { color: var(--text-secondary); font-size: 14px; }

.state-msg {
  color: var(--text-secondary);
  text-align: center;
  padding: 48px 0;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
}

.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { margin-bottom: 20px; font-size: 16px; }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(235px, 1fr));
  gap: 12px;
}

.card-item {
  background: var(--bg-surface);
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border-color);
  position: relative;
  transition: border-color 0.15s, transform 0.15s;
}

.card-item:hover { border-color: var(--accent); transform: translateY(-2px); }

.card-img-wrapper {
  width: 100%;
  aspect-ratio: 235 / 327;
  overflow: hidden;
  background: var(--bg-elevated);
}

.card-img { width: 100%; height: 100%; object-fit: cover; display: block; }

.card-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}

.card-info {
  padding: 8px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 4px;
}

.card-name {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-price { font-size: 12px; color: var(--accent); white-space: nowrap; flex-shrink: 0; }

.remove-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
}

.card-item:hover .remove-btn { opacity: 1; }
.remove-btn:hover { color: var(--danger); border-color: var(--danger); }
.remove-btn svg { width: 12px; height: 12px; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 28px;
  width: 400px;
  max-width: 95vw;
}

.modal h3 { font-size: 18px; font-weight: 600; margin-bottom: 6px; }

.modal-hint {
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: 14px;
}

textarea {
  resize: vertical;
  min-height: 160px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.error-msg {
  color: var(--danger);
  font-size: 13px;
  margin-top: 8px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

/* Inline search */
.search-wrapper {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 10px 36px 10px 14px;
  font-size: 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
}

.search-spinner {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: translateY(-50%) rotate(360deg); } }

.suggestions-list {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  list-style: none;
  margin: 0;
  padding: 4px 0;
  max-height: 260px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}

.suggestion-item {
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: background 0.1s, color 0.1s;
}

.suggestion-item:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.search-error {
  margin-top: 8px;
  font-size: 13px;
  color: var(--danger);
}

.search-success {
  margin-top: 8px;
  font-size: 13px;
  color: var(--accent);
}

/* Header actions */
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

/* Matches */
.matches-section {
  margin-top: 48px;
  border-top: 1px solid var(--border-color);
  padding-top: 28px;
}

.matches-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.matches-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.close-matches {
  background: transparent;
  border: none;
  padding: 4px 8px;
  font-size: 16px;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
}
.close-matches:hover { color: var(--text-primary); background: var(--bg-elevated); }

.matches-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.match-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 16px;
}

.match-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.match-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.match-username {
  font-weight: 600;
  font-size: 14px;
  display: block;
}

.match-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.match-cards {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.match-card-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 118px;
}

.match-card-img-wrapper {
  position: relative;
  width: 118px;
  flex-shrink: 0;
}

.match-card-img {
  width: 118px;
  height: 164px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  display: block;
}

.match-card-qty-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 999px;
  line-height: 1.4;
}

.match-card-placeholder {
  width: 80px;
  height: 112px;
  background: var(--bg-elevated);
  border-radius: 4px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: var(--text-muted);
  text-align: center;
  padding: 4px;
}

.match-card-name {
  font-size: 10px;
  color: var(--text-secondary);
  text-align: center;
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-card-price {
  font-size: 10px;
  color: var(--accent);
  font-weight: 600;
}

.match-add-cart-btn {
  margin-top: 4px;
  width: 100%;
  padding: 3px 0;
  font-size: 10px;
  font-weight: 600;
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.match-add-cart-btn:hover:not(:disabled) {
  background: var(--accent);
  color: #12131a;
}

.match-add-cart-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.match-add-cart-btn.success {
  border-color: var(--success, #4caf7d);
  color: var(--success, #4caf7d);
}

.match-add-cart-btn.error {
  border-color: var(--danger);
  color: var(--danger);
}
</style>
