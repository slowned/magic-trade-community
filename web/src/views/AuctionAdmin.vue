<template>
  <div class="auction-admin container">
    <div class="page-header">
      <h1>Administrar subastas</h1>
      <p class="subtitle">Subí cartas a subasta como plataforma. Por defecto abren el próximo viernes y cierran el viernes siguiente.</p>
    </div>

    <!-- ── Create form ── -->
    <form class="create-card" @submit.prevent="createAuction">
      <h2>Nueva subasta</h2>

      <div class="field span-2">
        <label for="card-name">Carta</label>
        <div class="search-wrapper">
          <input
            id="card-name"
            v-model="form.card_name"
            @input="onCardInput"
            @blur="hideSuggestionsDelayed"
            placeholder="Buscá por nombre… Black Lotus"
            autocomplete="off"
            required
          />
          <ul v-if="showSuggestions && suggestions.length" class="suggestions-list">
            <li
              v-for="name in suggestions"
              :key="name"
              @mousedown.prevent="selectSuggestion(name)"
              class="suggestion-item"
            >{{ name }}</li>
          </ul>
        </div>
        <span class="hint">Se resuelve contra Scryfall al crear la subasta.</span>
      </div>

      <div class="field span-2">
        <label for="title">Título (opcional)</label>
        <input id="title" v-model="form.title" placeholder="Vacío usa el nombre de la carta" />
      </div>

      <div class="field span-2">
        <label for="description">Descripción (opcional)</label>
        <textarea id="description" v-model="form.description" rows="3" placeholder="Detalles del estado, fotos reales, etc."></textarea>
      </div>

      <div class="field">
        <label for="condition">Condición</label>
        <select id="condition" v-model="form.condition">
          <option v-for="c in conditions" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>

      <div class="field checkboxes">
        <label><input type="checkbox" v-model="form.foil" /> Foil</label>
        <label><input type="checkbox" v-model="form.etched" /> Etched</label>
      </div>

      <div class="field">
        <label for="starting-price">Precio inicial (ARS)</label>
        <input id="starting-price" v-model="form.starting_price" type="number" min="1" step="1" required />
      </div>

      <div class="field">
        <label for="min-increment">Incremento mínimo (ARS)</label>
        <input id="min-increment" v-model="form.min_increment" type="number" min="1" step="1" required />
      </div>

      <div class="field span-2">
        <label for="reserve">Precio de reserva (opcional)</label>
        <input id="reserve" v-model="form.reserve_price" type="number" min="0" step="1" placeholder="Sin reserva" />
        <span class="hint">Si no se alcanza, la subasta cierra sin ganador. Los postores solo ven si se alcanzó, nunca el monto.</span>
      </div>

      <div class="field">
        <label for="starts-at">Apertura</label>
        <input id="starts-at" v-model="form.starts_at" type="datetime-local" required />
      </div>

      <div class="field">
        <label for="ends-at">Cierre</label>
        <input id="ends-at" v-model="form.ends_at" type="datetime-local" required />
      </div>

      <div class="field span-2">
        <label for="image">Imagen propia (opcional)</label>
        <input id="image" v-model="form.image_url" type="url" placeholder="Vacío usa la imagen de Scryfall" />
      </div>

      <div class="form-footer span-2">
        <button class="btn-ghost" type="button" @click="resetWindow">Restaurar viernes a viernes</button>
        <button class="btn-primary" type="submit" :disabled="creating">
          {{ creating ? 'Creando...' : 'Crear subasta' }}
        </button>
      </div>

      <p v-if="createError" class="form-error span-2">{{ createError }}</p>
      <p v-if="createSuccess" class="form-success span-2">{{ createSuccess }}</p>
    </form>

    <!-- ── Manage existing ── -->
    <section class="manage">
      <h2>Subastas cargadas</h2>

      <div v-if="loading" class="state-msg">Cargando...</div>
      <div v-else-if="auctions.length === 0" class="state-msg">Todavía no hay subastas.</div>

      <table v-else class="admin-table">
        <thead>
          <tr>
            <th>Carta</th><th>Estado</th><th>Precio</th><th>Pujas</th><th>Cierre</th><th>Ganador</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="auction in auctions" :key="auction.id">
            <td>
              <router-link :to="`/subasta/${auction.id}`">{{ auction.display_title }}</router-link>
            </td>
            <td><span class="status" :class="auction.status">{{ auction.status_display }}</span></td>
            <td class="amount-cell">{{ formatArs(auction.current_price) }}</td>
            <td>{{ auction.bid_count }}</td>
            <td class="when-cell">{{ formatDateTime(auction.ends_at) }}</td>
            <td>{{ auction.winner || '—' }}</td>
            <td class="actions-cell">
              <template v-if="['scheduled', 'live'].includes(auction.status)">
                <button class="link-btn" @click="close(auction)" :disabled="acting">Cerrar</button>
                <button class="link-btn danger" @click="cancel(auction)" :disabled="acting">Cancelar</button>
              </template>
              <button
                v-if="auction.bid_count === 0"
                class="link-btn danger"
                @click="remove(auction)"
                :disabled="acting"
              >Borrar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';
import { formatArs, formatDateTime, toLocalInputValue } from '@/utils/auction';

const CONDITIONS = [
  { value: 'NM', label: 'Near Mint' },
  { value: 'SP', label: 'Slightly Played' },
  { value: 'MP', label: 'Moderately Played' },
  { value: 'HP', label: 'Heavily Played' },
  { value: 'DMG', label: 'Damaged' },
];

function emptyForm() {
  return {
    card_name: '',
    title: '',
    description: '',
    condition: 'NM',
    foil: false,
    etched: false,
    starting_price: '',
    min_increment: '500',
    reserve_price: '',
    starts_at: '',
    ends_at: '',
    image_url: '',
  };
}

export default {
  name: 'AuctionAdminView',
  data() {
    return {
      form: emptyForm(),
      conditions: CONDITIONS,
      auctions: [],
      loading: true,
      creating: false,
      acting: false,
      createError: null,
      createSuccess: null,
      suggestions: [],
      showSuggestions: false,
      searchTimer: null,
    };
  },
  created() {
    this.resetWindow();
    this.fetchAuctions();
  },
  methods: {
    formatArs,
    formatDateTime,
    fetchAuctions() {
      this.loading = true;
      BinderService.getAuctions({ status: 'all' })
        .then(r => { this.auctions = r.data; })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    },
    resetWindow() {
      BinderService.getAuctionDefaultWindow()
        .then(r => {
          this.form.starts_at = toLocalInputValue(r.data.starts_at);
          this.form.ends_at = toLocalInputValue(r.data.ends_at);
        })
        .catch(e => console.error(e));
    },
    onCardInput() {
      clearTimeout(this.searchTimer);
      const query = this.form.card_name.trim();
      if (query.length < 3) {
        this.suggestions = [];
        return;
      }
      this.searchTimer = setTimeout(() => {
        BinderService.autocompleteCards(query)
          .then(r => {
            this.suggestions = r.data;
            this.showSuggestions = true;
          })
          .catch(() => { this.suggestions = []; });
      }, 250);
    },
    selectSuggestion(name) {
      this.form.card_name = name;
      this.suggestions = [];
      this.showSuggestions = false;
    },
    hideSuggestionsDelayed() {
      setTimeout(() => { this.showSuggestions = false; }, 150);
    },
    async createAuction() {
      this.createError = null;
      this.createSuccess = null;
      this.creating = true;

      const payload = {
        ...this.form,
        starts_at: new Date(this.form.starts_at).toISOString(),
        ends_at: new Date(this.form.ends_at).toISOString(),
        reserve_price: this.form.reserve_price === '' ? null : this.form.reserve_price,
      };

      try {
        const response = await BinderService.createAuction(payload);
        this.createSuccess = `Subasta creada: ${response.data.display_title}`;
        // Keep the window so loading a batch of cards stays quick.
        const { starts_at: startsAt, ends_at: endsAt } = this.form;
        this.form = { ...emptyForm(), starts_at: startsAt, ends_at: endsAt };
        this.fetchAuctions();
      } catch (e) {
        this.createError = this.readError(e);
      } finally {
        this.creating = false;
      }
    },
    readError(e) {
      const data = e.response?.data;
      if (!data) return 'No pudimos crear la subasta.';
      if (data.error) return data.error;
      const [first] = Object.entries(data);
      if (!first) return 'No pudimos crear la subasta.';
      const [field, messages] = first;
      return `${field}: ${Array.isArray(messages) ? messages[0] : messages}`;
    },
    async close(auction) {
      if (!confirm(`¿Cerrar "${auction.display_title}" ahora?`)) return;
      this.acting = true;
      try {
        await BinderService.closeAuction(auction.id);
        this.fetchAuctions();
      } finally {
        this.acting = false;
      }
    },
    async cancel(auction) {
      if (!confirm(`¿Cancelar "${auction.display_title}"? No se le adjudica a nadie.`)) return;
      this.acting = true;
      try {
        await BinderService.cancelAuction(auction.id);
        this.fetchAuctions();
      } finally {
        this.acting = false;
      }
    },
    async remove(auction) {
      if (!confirm(`¿Borrar "${auction.display_title}"?`)) return;
      this.acting = true;
      try {
        await BinderService.deleteAuction(auction.id);
        this.fetchAuctions();
      } finally {
        this.acting = false;
      }
    },
  },
};
</script>

<style scoped>
.auction-admin { padding: 32px 24px 64px; }

.page-header { margin-bottom: 24px; }
h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }
.subtitle { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }

.create-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.create-card h2 { grid-column: 1 / -1; font-size: 17px; font-weight: 700; }
.span-2 { grid-column: 1 / -1; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 600; }
.field input, .field select, .field textarea {
  padding: 9px 12px; font-size: 14px; font-family: inherit;
  border: 1px solid var(--border-color); border-radius: var(--radius);
  background: var(--bg-primary); color: var(--text-primary);
}
.field input:focus, .field select:focus, .field textarea:focus { outline: none; border-color: var(--accent); }
.field textarea { resize: vertical; }
.hint { font-size: 11px; color: var(--text-muted); }

.checkboxes { flex-direction: row; align-items: center; gap: 18px; padding-top: 22px; }
.checkboxes label { display: flex; align-items: center; gap: 6px; font-weight: 400; font-size: 13px; }
.checkboxes input { width: auto; }

.search-wrapper { position: relative; }
.search-wrapper input { width: 100%; }
.suggestions-list {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 20;
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); margin-top: 4px; max-height: 240px; overflow-y: auto;
  list-style: none; box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.suggestion-item { padding: 8px 12px; font-size: 13px; cursor: pointer; }
.suggestion-item:hover { background: var(--bg-elevated); }

.form-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 4px; }
.form-error { color: var(--danger); font-size: 13px; }
.form-success { color: var(--success); font-size: 13px; }

.manage { margin-top: 44px; }
.manage h2 { font-size: 18px; font-weight: 700; margin-bottom: 14px; }
.state-msg { padding: 32px 0; text-align: center; color: var(--text-secondary); }

.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th {
  text-align: left; padding: 8px 10px; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--text-muted); border-bottom: 1px solid var(--border-color);
}
.admin-table td { padding: 10px; border-bottom: 1px solid var(--border-color); }
.amount-cell { color: var(--accent); font-weight: 700; }
.when-cell { color: var(--text-secondary); }

.status { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; background: var(--bg-elevated); color: var(--text-secondary); }
.status.live { background: rgba(46,143,94,0.15); color: var(--success); }
.status.cancelled { background: rgba(201,64,64,0.12); color: var(--danger); }

.actions-cell { display: flex; gap: 10px; flex-wrap: wrap; }
.link-btn { background: none; padding: 0; font-size: 12px; color: var(--accent); }
.link-btn.danger { color: var(--danger); }
.link-btn:disabled { opacity: 0.5; }

@media (max-width: 700px) {
  .create-card { grid-template-columns: 1fr; }
  .span-2 { grid-column: 1; }
  .checkboxes { padding-top: 0; }
}
</style>
