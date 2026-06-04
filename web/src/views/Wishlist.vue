<template>
  <div class="wishlist container">
    <div class="page-header">
      <div>
        <h1>Wishlist</h1>
        <p class="subtitle">Cartas que querés conseguir</p>
      </div>
      <button class="btn-primary" @click="showAddModal = true">+ Agregar carta</button>
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
    async removeCard(entry) {
      try {
        await BinderService.removeFromWishlist(entry.card.id);
        this.cards = this.cards.filter(c => c.id !== entry.id);
      } catch (e) {
        console.error(e);
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
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
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
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
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
  aspect-ratio: 5 / 7;
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
  background: rgba(18, 19, 26, 0.85);
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
  background: rgba(0,0,0,0.65);
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
</style>
