<template>
  <div class="explore-page">
    <div class="explore-header">
      <div class="container">
        <h1>Explorar carpetas</h1>
        <p class="subtitle">Colecciones públicas de la comunidad</p>
        <div class="search-bar">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input v-model="search" placeholder="Buscá por nombre de carta..." @keyup.enter="applySearch" />
          <button class="btn-primary" @click="applySearch">Buscar</button>
        </div>
        <div v-if="activeSearch" class="active-search-pill">
          Mostrando binders con: <strong>{{ activeSearch }}</strong>
          <button @click="clearSearch">✕</button>
        </div>
      </div>
    </div>

    <div class="container explore-body">
      <div v-if="loading" class="state-msg">Cargando...</div>

      <div v-else-if="binders.length === 0" class="empty-state">
        <p>{{ activeSearch ? `Ningún usuario tiene "${activeSearch}" disponible.` : 'No hay binders públicos todavía.' }}</p>
      </div>

      <div v-else>
        <p class="result-count">{{ binders.length }} carpeta{{ binders.length !== 1 ? 's' : '' }}</p>
        <div class="binder-grid">
          <router-link
            v-for="binder in binders"
            :key="binder.id"
            :to="{ name: 'BinderDetail', params: { id: binder.id } }"
            class="binder-card"
          >
            <div class="binder-card-top">
              <span class="binder-name">{{ binder.name }}</span>
              <span class="badge" :class="binder.is_public ? 'public' : 'private'">
                {{ binder.is_public ? 'Público' : 'Privado' }}
              </span>
            </div>
            <div class="binder-owner">
              por
              <span
                class="owner-link"
                @click.stop.prevent="$router.push(`/user/${binder.user}`)"
              >{{ binder.user }}</span>
            </div>
            <div class="binder-count">{{ binder.card_count != null ? binder.card_count + ' cartas' : '—' }}</div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'ExploreView',
  data() {
    return { binders: [], loading: true, search: '', activeSearch: '' };
  },
  created() {
    if (this.$route.query.card) {
      this.search = this.$route.query.card;
      this.activeSearch = this.$route.query.card;
    }
    this.fetchBinders();
  },
  watch: {
    '$route.query.card'(val) {
      this.search = val || '';
      this.activeSearch = val || '';
      this.fetchBinders();
    }
  },
  methods: {
    fetchBinders() {
      this.loading = true;
      const params = this.activeSearch ? { card_name: this.activeSearch } : {};
      BinderService.getBinders(params)
        .then(r => { this.binders = r.data; })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    },
    applySearch() {
      this.activeSearch = this.search.trim();
      this.$router.replace({ path: '/carpetas', query: this.activeSearch ? { card: this.activeSearch } : {} });
      this.fetchBinders();
    },
    clearSearch() {
      this.search = '';
      this.activeSearch = '';
      this.$router.replace({ path: '/carpetas' });
      this.fetchBinders();
    }
  }
};
</script>

<style scoped>
.explore-header {
  background: linear-gradient(180deg, #111220 0%, #0d0e17 100%);
  border-bottom: 1px solid var(--border-color);
  padding: 48px 0 32px;
}

.explore-header h1 { font-size: 32px; font-weight: 800; margin-bottom: 6px; }
.subtitle { color: var(--text-secondary); font-size: 15px; margin-bottom: 24px; }

.search-bar {
  display: flex; align-items: center; gap: 8px; max-width: 560px;
  background: rgba(255,255,255,0.05); border: 1px solid var(--border-color);
  border-radius: 10px; padding: 6px 6px 6px 14px;
}
.search-bar svg { width: 16px; height: 16px; color: var(--text-muted); flex-shrink: 0; }
.search-bar input { flex: 1; background: transparent; border: none; color: var(--text-primary); font-size: 14px; outline: none; }
.search-bar input::placeholder { color: var(--text-muted); }
.search-bar .btn-primary { padding: 8px 18px; font-size: 13px; border-radius: 7px; flex-shrink: 0; }

.active-search-pill {
  display: inline-flex; align-items: center; gap: 8px;
  margin-top: 12px; font-size: 13px; color: var(--text-secondary);
  background: rgba(232,160,32,0.1); border: 1px solid rgba(232,160,32,0.25);
  border-radius: 999px; padding: 4px 12px;
}
.active-search-pill strong { color: var(--accent); }
.active-search-pill button { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 0; font-size: 12px; }

.explore-body { padding: 32px 0 80px; }

.result-count { color: var(--text-muted); font-size: 13px; margin-bottom: 20px; }

.state-msg { color: var(--text-secondary); text-align: center; padding: 64px 0; }
.empty-state { text-align: center; padding: 80px 0; color: var(--text-secondary); font-size: 15px; }

.binder-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }

.binder-card {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 20px; color: var(--text-primary);
  display: block; transition: border-color 0.15s, transform 0.15s;
}
.binder-card:hover { border-color: var(--accent); transform: translateY(-2px); color: var(--text-primary); }

.binder-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.binder-name { font-weight: 600; font-size: 15px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 999px; white-space: nowrap; flex-shrink: 0; }
.badge.public { background: rgba(76,175,125,0.15); color: var(--success); }
.badge.private { background: rgba(232,160,32,0.15); color: var(--accent); }
.binder-owner { color: var(--text-secondary); font-size: 13px; margin-bottom: 10px; }
.binder-owner span { color: var(--accent); }
.owner-link:hover { text-decoration: underline; }
.binder-count { color: var(--text-muted); font-size: 12px; }
</style>
