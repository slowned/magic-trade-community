<template>
  <div class="binder-detail container">

    <!-- Header -->
    <div class="binder-header">
      <div>
        <router-link to="/" class="back-link">← Binders</router-link>
        <h1 class="binder-title">{{ binderName || 'Binder' }}</h1>
        <span class="card-meta">
          {{ filteredCards.length }} / {{ cards.length }} cartas
          <span v-if="copyCount > cards.length" class="copies-meta">({{ copyCount }} copias)</span> ·
          <router-link v-if="binderOwner" :to="`/user/${binderOwner}`" class="owner-name">{{ binderOwner }}</router-link>
          <span v-else class="owner-name">{{ binderOwner }}</span>
        </span>
      </div>
      <div class="header-actions">
        <button v-if="cards.length && isOwner" class="btn-ghost" @click="exportCSV">↓ Exportar CSV</button>
        <button v-if="isOwner" class="btn-primary" @click="openAddModal('names')">+ Agregar cartas</button>
      </div>
    </div>

    <!-- Filters bar -->
    <div v-if="cards.length" class="filters-bar">
      <div class="search-wrapper">
        <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
        </svg>
        <input v-model="searchQuery" placeholder="Buscar en esta carpeta..." class="search-input" />
        <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">✕</button>
      </div>

      <div class="color-filters">
        <button
          v-for="c in COLOR_OPTIONS"
          :key="c.code"
          :class="['color-btn', c.code, { active: activeColors.includes(c.code) }]"
          :title="c.label"
          @click="toggleColor(c.code)"
        >{{ c.symbol }}</button>
      </div>

      <select v-model="filterSet" class="set-select">
        <option value="">Todos los sets</option>
        <option v-for="s in availableSets" :key="s.code" :value="s.code">
          {{ s.name }} ({{ s.code.toUpperCase() }})
        </option>
      </select>

      <button v-if="hasFilters" class="btn-ghost clear-filters" @click="clearFilters">
        Limpiar filtros
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-msg">Cargando cartas...</div>

    <!-- Empty binder -->
    <div v-else-if="cards.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <p>Este binder no tiene cartas todavía.</p>
      <button v-if="isOwner" class="btn-primary" @click="openAddModal('names')">Agregar cartas</button>
    </div>

    <!-- No results after filter -->
    <div v-else-if="filteredCards.length === 0" class="state-msg">
      Sin resultados para los filtros actuales.
    </div>

    <!-- Cards grid -->
    <div v-else class="cards-grid">
      <div v-for="card in filteredCards" :key="card.binder_card_id ?? card.id" class="card-item">
        <div class="card-img-wrapper">
          <img v-if="card.image_uri" :src="card.image_uri" :alt="card.name" class="card-img" loading="lazy" />
          <div v-else class="card-img-placeholder">{{ card.name }}</div>
        </div>
        <div class="card-info">
          <!-- What the card is -->
          <div class="card-id">
            <span class="card-name" :title="card.name">{{ card.name }}</span>
            <span class="card-set" :title="card.set_name">{{ card.set_name }}</span>
            <span class="card-collector" v-if="card.collector_number">#{{ card.collector_number }}</span>
          </div>

          <!-- What this particular copy is like -->
          <dl class="card-specs">
            <div class="spec-row">
              <dt>Precio</dt>
              <dd class="spec-price">{{ card.price_usd ? `$${card.price_usd}` : '—' }}</dd>
            </div>
            <div class="spec-row">
              <dt>Idioma</dt>
              <dd>{{ card.language_display || '—' }}</dd>
            </div>
            <div class="spec-row">
              <dt>Condición</dt>
              <dd>{{ card.condition_display || '—' }}</dd>
            </div>
            <div class="spec-row">
              <dt>Stock</dt>
              <dd>{{ card.quantity ?? 1 }}</dd>
            </div>
          </dl>

          <!-- Cart button (only visible to non-owners) -->
          <button
            v-if="!isOwner"
            class="add-cart-btn"
            :class="{ disabled: !isAuthenticated }"
            :title="isAuthenticated ? 'Agregar al carrito' : 'Registrate para comprar'"
            @click="handleAddToCart(card)"
          >
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3z"/>
              <path d="M16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/>
            </svg>
            Agregar
          </button>
        </div>
      </div>
    </div>

    <!-- Add cards modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal">
        <div class="modal-tabs">
          <button :class="['tab', { active: addTab === 'search' }]" @click="addTab = 'search'">Buscar</button>
          <button :class="['tab', { active: addTab === 'names' }]" @click="addTab = 'names'">Por nombre</button>
          <button :class="['tab', { active: addTab === 'csv' }]" @click="addTab = 'csv'">Importar CSV</button>
        </div>

        <!-- Tab: buscar con autocomplete -->
        <template v-if="addTab === 'search'">
          <div class="autocomplete-wrapper">
            <input
              v-model="cardSearchQuery"
              @input="onSearchInput"
              @keydown.esc="suggestions = []"
              placeholder="Escribí el nombre de la carta..."
              class="autocomplete-input"
              autocomplete="off"
            />
            <ul v-if="suggestions.length" class="suggestions-list">
              <li
                v-for="name in suggestions"
                :key="name"
                class="suggestion-item"
                @mousedown.prevent="selectSuggestion(name)"
              >{{ name }}</li>
            </ul>
          </div>

          <!-- Editions picker -->
          <div v-if="cardEditions.length" class="editions-list">
            <p class="modal-hint">Seleccioná la edición:</p>
            <div
              v-for="card in cardEditions"
              :key="card.id"
              class="edition-row"
              :class="{ selected: selectedEdition?.id === card.id }"
              @click="selectedEdition = card"
            >
              <img v-if="card.image_uri" :src="card.image_uri" class="edition-thumb" />
              <div class="edition-info">
                <span class="edition-name">{{ card.name }}</span>
                <span class="edition-set">{{ card.set_name }} ({{ card.set_code?.toUpperCase() }})</span>
                <span v-if="card.price_usd" class="edition-price">USD {{ card.price_usd }}</span>
              </div>
            </div>
          </div>

          <div class="copy-fields">
            <label class="copy-field">
              Cantidad
              <input
                v-model.number="addQuantity"
                type="number"
                min="1"
                max="999"
                class="qty-input"
                @keydown.enter="handleAddById"
              />
            </label>
            <label class="copy-field">
              Idioma
              <select v-model="addLanguage">
                <option v-for="l in LANGUAGE_OPTIONS" :key="l.code" :value="l.code">{{ l.label }}</option>
              </select>
            </label>
            <label class="copy-field">
              Condición
              <select v-model="addCondition">
                <option v-for="c in CONDITION_OPTIONS" :key="c.code" :value="c.code">{{ c.label }}</option>
              </select>
            </label>
          </div>

          <div v-if="addError" class="error-msg">{{ addError }}</div>
          <div v-if="addResult" class="result-msg">
            ✓ {{ addResult.quantity > 1 ? `${addResult.quantity}× ` : '' }}{{ addResult.added }}
            ({{ addResult.condition }}, {{ addResult.language }}) agregada
          </div>

          <div class="modal-actions">
            <button class="btn-ghost" @click="closeAddModal">Cerrar</button>
            <button class="btn-primary" :disabled="!selectedEdition || adding || !validQuantity" @click="handleAddById">
              {{ adding ? 'Agregando...' : 'Agregar' }}
            </button>
          </div>
        </template>

        <!-- Tab: por nombre -->
        <template v-else-if="addTab === 'names'">
          <p class="modal-hint">Una carta por línea. Podés incluir cantidad: <code>4 Lightning Bolt</code></p>
          <textarea v-model="newCards" placeholder="Lightning Bolt&#10;4 Counterspell&#10;Sol Ring" rows="10" />

          <div v-if="addError" class="error-msg">{{ addError }}</div>
          <div v-if="addResult" class="result-msg">
            ✓ {{ addResult.added.length }} cartas agregadas
            <span v-if="addResult.not_found.length"> · {{ addResult.not_found.length }} no encontradas: {{ addResult.not_found.join(', ') }}</span>
          </div>

          <div v-if="adding" class="spinner-overlay">
            <div class="spinner"></div>
            <span>Buscando cartas en Scryfall...</span>
          </div>

          <div class="modal-actions">
            <button class="btn-ghost" @click="closeAddModal">Cerrar</button>
            <button class="btn-primary" @click="handleAdd" :disabled="adding || !canSubmit">
              {{ adding ? 'Agregando...' : 'Agregar' }}
            </button>
          </div>
        </template>

        <!-- Tab: importar CSV (Moxfield) -->
        <template v-else>
          <p class="modal-hint">
            Subí el CSV exportado desde Moxfield, o pegá su contenido abajo.<br>
            Formato: <code>Count,Name,Edition,Condition,Language,Foil,Collector Number</code>
          </p>

          <pre class="csv-example">Count,Name,Edition,Condition,Language,Foil,Collector Number
4,Lightning Bolt,M10,Near Mint,English,,146
1,Sol Ring,C21,Near Mint,English,foil,264
2,Arcane Signet,ELD,Slightly Played,Spanish,,331</pre>

          <p class="modal-hint">
            <strong>Foil:</strong> vacío es carta normal; <code>foil</code> la marca como foil
            (también valen <code>yes</code>, <code>true</code> y <code>1</code>).
          </p>

          <label class="csv-dropzone" :class="{ 'has-file': csvFileName }">
            <input type="file" accept=".csv,text/csv" @change="onCsvFile" />
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm5 5a1 1 0 112 0v3.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 111.414-1.414L9 11.586V8z" clip-rule="evenodd"/>
            </svg>
            <span v-if="csvFileName" class="csv-file-name">{{ csvFileName }}</span>
            <span v-else>Elegir archivo .csv</span>
          </label>
          <div v-if="csvFileError" class="error-msg">{{ csvFileError }}</div>

          <div class="csv-separator"><span>o pegalo a mano</span></div>

          <textarea v-model="csvData" placeholder="Count,Name,Edition,Condition,Language,Foil,Collector Number&#10;4,Lightning Bolt,M10,Near Mint,English,,146&#10;1,Sol Ring,C21,Near Mint,English,foil,264" rows="8" />

          <div v-if="addError" class="error-msg">{{ addError }}</div>
          <div v-if="addResult" class="result-msg">
            ✓ {{ addResult.added.length }} cartas agregadas
            <span v-if="addResult.not_found.length"> · {{ addResult.not_found.length }} no encontradas: {{ addResult.not_found.join(', ') }}</span>
          </div>

          <div v-if="adding" class="spinner-overlay">
            <div class="spinner"></div>
            <span>Buscando cartas en Scryfall...</span>
          </div>

          <div class="modal-actions">
            <button class="btn-ghost" @click="closeAddModal">Cerrar</button>
            <button class="btn-primary" @click="handleAdd" :disabled="adding || !canSubmit">
              {{ adding ? 'Agregando...' : 'Agregar' }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Login prompt modal -->
    <div v-if="showLoginPrompt" class="modal-overlay" @click.self="showLoginPrompt = false">
      <div class="modal modal-sm">
        <h3>Necesitás una cuenta</h3>
        <p class="modal-hint">Para agregar cartas al carrito necesitás estar registrado.</p>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showLoginPrompt = false">Cancelar</button>
          <router-link to="/register"><button class="btn-primary">Registrarse</button></router-link>
          <router-link to="/login"><button class="btn-ghost">Iniciar sesión</button></router-link>
        </div>
      </div>
    </div>

    <!-- Cart added toast -->
    <div v-if="cartToast" class="toast">
      ✓ {{ cartToast }} agregada al carrito
    </div>

  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import BinderService from "@/services/BinderService";
import { CONDITION_OPTIONS, LANGUAGE_OPTIONS } from "@/utils/cardCopy";

const COLOR_OPTIONS = [
  { code: 'W', symbol: 'W', label: 'Blanco' },
  { code: 'U', symbol: 'U', label: 'Azul' },
  { code: 'B', symbol: 'B', label: 'Negro' },
  { code: 'R', symbol: 'R', label: 'Rojo' },
  { code: 'G', symbol: 'G', label: 'Verde' },
  { code: 'C', symbol: 'C', label: 'Incoloro' },
];

export default {
  name: 'BinderDetail',
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser']),
    isOwner() {
      return this.isAuthenticated && this.currentUser?.username === this.binderOwner;
    },
    availableSets() {
      const seen = new Map();
      this.cards.forEach(c => {
        if (c.set_code && !seen.has(c.set_code)) {
          seen.set(c.set_code, c.set_name || c.set_code);
        }
      });
      return Array.from(seen.entries())
        .map(([code, name]) => ({ code, name }))
        .sort((a, b) => a.name.localeCompare(b.name));
    },
    filteredCards() {
      return this.cards.filter(card => {
        if (this.searchQuery) {
          const q = this.searchQuery.toLowerCase();
          if (!card.name.toLowerCase().includes(q)) return false;
        }
        if (this.activeColors.length) {
          const cardColors = card.color_identity ? card.color_identity.split(',') : [];
          const isColorless = cardColors.length === 0;
          const wantsColorless = this.activeColors.includes('C');
          if (wantsColorless && isColorless) return true;
          if (wantsColorless && !isColorless) {
            if (this.activeColors.filter(c => c !== 'C').length === 0) return false;
          }
          const nonColorless = this.activeColors.filter(c => c !== 'C');
          if (nonColorless.length && !nonColorless.some(c => cardColors.includes(c))) return false;
        }
        if (this.filterSet && card.set_code !== this.filterSet) return false;
        return true;
      });
    },
    copyCount() {
      return this.cards.reduce((total, c) => total + (c.quantity || 1), 0);
    },
    validQuantity() {
      return Number.isInteger(this.addQuantity) && this.addQuantity >= 1 && this.addQuantity <= 999;
    },
    hasFilters() {
      return this.searchQuery || this.activeColors.length || this.filterSet;
    },
    canSubmit() {
      return this.addTab === 'names' ? this.newCards.trim() : this.csvData.trim();
    },
  },
  data() {
    return {
      COLOR_OPTIONS,
      CONDITION_OPTIONS,
      LANGUAGE_OPTIONS,
      binderName: '',
      binderOwner: '',
      cards: [],
      loading: true,
      // Filters
      searchQuery: '',
      activeColors: [],
      filterSet: '',
      // Add modal
      showAddModal: false,
      addTab: 'search',
      newCards: '',
      cardSearchQuery: '',
      suggestions: [],
      cardEditions: [],
      selectedEdition: null,
      addQuantity: 1,
      addCondition: 'NM',
      addLanguage: 'EN',
      searchDebounce: null,
      csvData: '',
      csvFileName: '',
      csvFileError: null,
      adding: false,
      addError: null,
      addResult: null,
      // Cart
      showLoginPrompt: false,
      cartToast: null,
      cartToastTimer: null,
    };
  },
  created() {
    this.fetchBinder();
  },
  methods: {
    fetchBinder() {
      this.loading = true;
      BinderService.getBinder(this.$route.params.id)
        .then(r => {
          this.binderName = r.data.name;
          this.binderOwner = r.data.user;
          this.cards = r.data.card_set || [];
        })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    },

    // --- Filters ---
    toggleColor(code) {
      const idx = this.activeColors.indexOf(code);
      if (idx >= 0) this.activeColors.splice(idx, 1);
      else this.activeColors.push(code);
    },
    clearFilters() {
      this.searchQuery = '';
      this.activeColors = [];
      this.filterSet = '';
    },

    // --- Export CSV ---
    exportCSV() {
      const header = 'Count,Name,Set,Set Code,Price USD';
      const rows = this.cards.map(c =>
        `1,"${c.name}","${c.set_name || ''}","${c.set_code || ''}","${c.price_usd || ''}"`
      );
      const csv = [header, ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${this.binderName || 'binder'}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    },

    // --- Add modal ---
    openAddModal(tab = 'names') {
      this.addTab = tab;
      this.addError = null;
      this.addResult = null;
      this.showAddModal = true;
    },
    closeAddModal() {
      this.showAddModal = false;
      this.newCards = '';
      this.csvData = '';
      this.csvFileName = '';
      this.csvFileError = null;
      this.cardSearchQuery = '';
      this.suggestions = [];
      this.cardEditions = [];
      this.selectedEdition = null;
      this.addQuantity = 1;
      this.addCondition = 'NM';
      this.addLanguage = 'EN';
      this.addError = null;
      this.addResult = null;
    },

    // Reading the file here keeps the upload path identical to the paste path:
    // the backend still receives plain CSV text via import-moxfield.
    onCsvFile(event) {
      const file = event.target.files?.[0];
      this.csvFileError = null;
      if (!file) return;

      if (file.size > 2 * 1024 * 1024) {
        this.csvFileError = 'El archivo supera los 2 MB.';
        event.target.value = '';
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        this.csvData = String(reader.result || '').trim();
        this.csvFileName = file.name;
        this.addError = null;
        this.addResult = null;
      };
      reader.onerror = () => {
        this.csvFileError = 'No se pudo leer el archivo.';
        this.csvFileName = '';
      };
      reader.readAsText(file);
      event.target.value = '';
    },

    onSearchInput() {
      clearTimeout(this.searchDebounce);
      this.suggestions = [];
      this.cardEditions = [];
      this.selectedEdition = null;
      if (this.cardSearchQuery.length < 2) return;
      this.searchDebounce = setTimeout(() => this.fetchSuggestions(), 300);
    },

    async fetchSuggestions() {
      try {
        const resp = await fetch(
          `https://api.scryfall.com/cards/autocomplete?q=${encodeURIComponent(this.cardSearchQuery)}`,
          { headers: { Accept: 'application/json' } }
        );
        const data = await resp.json();
        this.suggestions = data.data?.slice(0, 8) || [];
      } catch { this.suggestions = []; }
    },

    async selectSuggestion(name) {
      this.cardSearchQuery = name;
      this.suggestions = [];
      this.cardEditions = [];
      this.selectedEdition = null;
      try {
        const resp = await fetch(
          `https://api.scryfall.com/cards/search?q=!"${encodeURIComponent(name)}"&unique=prints&order=released`,
          { headers: { Accept: 'application/json' } }
        );
        const data = await resp.json();
        this.cardEditions = (data.data || []).map(c => ({
          id: c.id,
          name: c.name,
          set_name: c.set_name,
          set_code: c.set,
          image_uri: c.image_uris?.normal || c.card_faces?.[0]?.image_uris?.normal || '',
          price_usd: c.prices?.usd || null,
        }));
      } catch { this.cardEditions = []; }
    },

    async handleAddById() {
      if (!this.selectedEdition || this.adding || !this.validQuantity) return;
      this.adding = true;
      this.addError = null;
      this.addResult = null;
      try {
        const res = await BinderService.addCardById(this.$route.params.id, this.selectedEdition.id, {
          quantity: this.addQuantity,
          condition: this.addCondition,
          language: this.addLanguage,
        });
        this.addResult = res.data;
        this.selectedEdition = null;
        this.addQuantity = 1;
        this.cardEditions = [];
        this.cardSearchQuery = '';
        this.fetchBinder();
      } catch (err) {
        this.addError = err.response?.data?.error || 'Error al agregar la carta.';
      } finally {
        this.adding = false;
      }
    },
    async handleAdd() {
      this.addError = null;
      this.addResult = null;
      this.adding = true;
      try {
        let res;
        if (this.addTab === 'names') {
          const cardNames = this.newCards
            .split('\n')
            .map(line => {
              const parts = line.trim().split(' ');
              if (parts.length > 1 && !isNaN(parts[0])) parts.shift();
              return parts.join(' ').trim();
            })
            .filter(n => n.length > 0);
          res = await BinderService.addCardsToBinder(this.$route.params.id, cardNames);
        } else {
          res = await BinderService.importMoxfield(this.$route.params.id, this.csvData);
        }
        this.addResult = res.data;
        this.newCards = '';
        this.csvData = '';
        this.csvFileName = '';
        this.csvFileError = null;
        this.fetchBinder();
      } catch (e) {
        this.addError = 'Error al agregar las cartas.';
        console.error(e);
      } finally {
        this.adding = false;
      }
    },

    // --- Cart ---
    handleAddToCart(card) {
      if (!this.isAuthenticated) {
        this.showLoginPrompt = true;
        return;
      }
      BinderService.addToCart(this.binderOwner, card.id)
        .then(() => {
          this.showCartToast(card.name);
        })
        .catch(e => console.error(e));
    },
    showCartToast(cardName) {
      this.cartToast = cardName;
      clearTimeout(this.cartToastTimer);
      this.cartToastTimer = setTimeout(() => { this.cartToast = null; }, 3000);
    },
  }
}
</script>

<style scoped>
.binder-detail {
  padding-top: 32px;
  padding-bottom: 64px;
}

.back-link {
  color: var(--text-secondary);
  font-size: 13px;
  display: inline-block;
  margin-bottom: 8px;
}
.back-link:hover { color: var(--text-primary); }

.binder-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.binder-title { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
.copies-meta { color: var(--accent); }

.card-meta { color: var(--text-secondary); font-size: 14px; }
.owner-name { color: var(--accent); }

.header-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }

/* Filters */
.filters-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  flex: 1;
  min-width: 160px;
  max-width: 280px;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input { padding-left: 30px; height: 34px; font-size: 13px; }

.clear-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  padding: 0;
  font-size: 12px;
  cursor: pointer;
}

.color-filters { display: flex; gap: 4px; }

.color-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.15s, border-color 0.15s;
}
.color-btn:hover, .color-btn.active { opacity: 1; border-color: white; }
.color-btn.W { background: #f9fafb; color: #374151; }
.color-btn.U { background: #2563eb; color: white; }
.color-btn.B { background: #1f2937; color: #d1d5db; }
.color-btn.R { background: #dc2626; color: white; }
.color-btn.G { background: #16a34a; color: white; }
.color-btn.C { background: #6b7280; color: white; }

.set-select {
  height: 34px;
  width: auto;
  min-width: 140px;
  font-size: 13px;
  padding: 0 28px 0 10px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%238890b0'%3E%3Cpath fill-rule='evenodd' d='M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 14px;
  -webkit-appearance: none;
  appearance: none;
}

.clear-filters { height: 34px; font-size: 12px; padding: 0 12px; }

/* State messages */
.state-msg { color: var(--text-secondary); text-align: center; padding: 48px 0; }

.empty-state { text-align: center; padding: 80px 0; color: var(--text-secondary); }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { margin-bottom: 20px; font-size: 16px; }

/* Cards grid */
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
.card-item:hover { border-color: var(--accent); transform: translateY(-3px); }

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
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Identity block: what card this is */
.card-id { display: flex; flex-direction: column; gap: 2px; min-width: 0; }

.card-set {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-collector {
  font-size: 11px;
  color: var(--text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

/* Per-copy details, split off by a rule as requested */
.card-specs {
  margin: 0;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.spec-row { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.spec-row dt { font-size: 11px; color: var(--text-muted); }
.spec-row dd {
  margin: 0;
  font-size: 12px;
  color: var(--text-primary);
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.spec-row dd.spec-price { color: var(--accent); font-weight: 600; font-size: 14px; }

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}



/* Cart button */
.add-cart-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 10px;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  color: #12131a;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s;
}
.add-cart-btn:hover { filter: brightness(1.08); }
.add-cart-btn svg { width: 15px; height: 15px; flex-shrink: 0; }
.add-cart-btn.disabled {
  background: transparent;
  border-color: var(--border-color);
  color: var(--text-muted);
}

/* CSV upload */
.csv-example {
  background: var(--bg-elevated); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px; line-height: 1.6; color: var(--text-primary);
  overflow-x: auto; white-space: pre;
}

.csv-dropzone {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 16px; margin-bottom: 12px; cursor: pointer;
  background: var(--bg-elevated); border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm); color: var(--text-secondary); font-size: 13px;
  transition: border-color 0.15s, color 0.15s;
}
.csv-dropzone:hover { border-color: var(--accent); color: var(--text-primary); }
.csv-dropzone.has-file { border-style: solid; border-color: var(--accent); color: var(--text-primary); }
.csv-dropzone input { display: none; }
.csv-dropzone svg { width: 18px; height: 18px; flex-shrink: 0; }
.csv-file-name { font-weight: 500; word-break: break-all; }

.csv-separator {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 12px; color: var(--text-muted); font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.06em;
}
.csv-separator::before, .csv-separator::after {
  content: ''; flex: 1; height: 1px; background: var(--border-color);
}

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
  padding: 24px 28px 28px;
  width: 460px;
  max-width: 95vw;
  position: relative;
  overflow: hidden;
}

.modal-sm { width: 340px; }
.modal-sm h3 { font-size: 17px; font-weight: 600; margin-bottom: 8px; }

/* Autocomplete search */
.autocomplete-wrapper { position: relative; }
.autocomplete-input {
  width: 100%; padding: 10px 12px;
  background: var(--bg-primary); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); color: var(--text-primary);
  font-size: 14px; font-family: inherit; box-sizing: border-box;
}
.suggestions-list {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 50;
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); margin: 2px 0 0; padding: 4px 0;
  max-height: 220px; overflow-y: auto; list-style: none;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.suggestion-item {
  padding: 8px 14px; font-size: 13px; cursor: pointer; color: var(--text-primary);
}
.suggestion-item:hover { background: var(--bg-elevated); }

/* Editions list */
.editions-list { display: flex; flex-direction: column; gap: 6px; max-height: 300px; overflow-y: auto; margin-top: 8px; }
.edition-row {
  display: flex; align-items: center; gap: 10px; padding: 8px;
  border: 1px solid var(--border-color); border-radius: var(--radius-sm);
  cursor: pointer; transition: background 0.1s;
}
.edition-row:hover { background: var(--bg-elevated); }
.edition-row.selected { border-color: var(--accent); background: rgba(232,197,71,0.08); }
.edition-thumb { width: 44px; border-radius: 4px; flex-shrink: 0; }
.edition-info { display: flex; flex-direction: column; gap: 2px; }
.edition-name { font-size: 13px; font-weight: 600; }
.edition-set { font-size: 11px; color: var(--text-muted); }
.edition-price { font-size: 12px; color: var(--accent); font-weight: 600; }

.modal-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0;
}

.tab {
  background: none;
  border: none;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s;
}
.tab:hover { color: var(--text-primary); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

.modal-hint {
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: 12px;
  line-height: 1.6;
}
.modal-hint code {
  background: var(--bg-elevated);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--accent);
  font-size: 11px;
}

textarea {
  resize: vertical;
  min-height: 180px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.error-msg { color: var(--danger); font-size: 13px; margin-top: 8px; }
.result-msg { color: var(--success); font-size: 13px; margin-top: 8px; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.copy-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}
.copy-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}
.copy-field select { height: 34px; font-size: 13px; }
.qty-input { width: 72px; height: 34px; }

/* Spinner overlay */
.spinner-overlay {
  position: absolute;
  inset: 0;
  background: rgba(18,19,26,0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 13px;
  z-index: 10;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: var(--bg-elevated);
  border: 1px solid var(--success);
  color: var(--success);
  padding: 10px 18px;
  border-radius: var(--radius);
  font-size: 13px;
  z-index: 300;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from { transform: translateY(8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
