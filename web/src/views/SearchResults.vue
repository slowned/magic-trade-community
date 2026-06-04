<template>
  <div class="search-page">
    <!-- Card spotlight -->
    <div class="spotlight">
      <div class="container spotlight-inner">
        <div class="card-preview">
          <div class="card-preview-frame">
            <img
              v-if="cardImageLoaded"
              :src="cardImageUrl"
              :alt="query"
              class="card-preview-img"
              @error="cardImageLoaded = false"
            />
            <div v-else class="card-preview-placeholder">
              <span>🃏</span>
              <span>{{ query }}</span>
            </div>
          </div>
        </div>

        <div class="spotlight-info">
          <p class="eyebrow">Buscando carta</p>
          <h1 class="card-title">{{ query }}</h1>
          <div v-if="binders.length > 0" class="found-in">
            <span class="found-count">{{ binders.length }}</span>
            usuario{{ binders.length !== 1 ? 's tienen' : ' tiene' }} esta carta disponible
          </div>
          <div v-else-if="!loading" class="not-found">
            Ningún usuario tiene esta carta en su binder.
          </div>
          <router-link to="/carpetas">
            <button class="btn-ghost back-btn">← Ver todas las carpetas</button>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Binder results -->
    <div class="container results-section">
      <div v-if="loading" class="state-msg">Buscando...</div>

      <template v-else-if="binders.length > 0">
        <h2 class="results-title">Carpetas con esta carta</h2>
        <div class="binder-grid">
          <router-link
            v-for="binder in binders"
            :key="binder.id"
            :to="{ name: 'BinderDetail', params: { id: binder.id } }"
            class="binder-card"
          >
            <div class="binder-top">
              <span class="binder-name">{{ binder.name }}</span>
              <svg class="arrow" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div class="binder-owner">por <span>{{ binder.user }}</span></div>
            <div class="binder-meta">
              <span class="binder-count">{{ binder.card_count != null ? binder.card_count + ' cartas' : '—' }}</span>
              <span class="tip">Ver más cartas →</span>
            </div>
          </router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'SearchResults',
  data() {
    return {
      query: '',
      binders: [],
      loading: true,
      cardImageLoaded: false,
      cardImageUrl: '',
    };
  },
  created() {
    this.query = this.$route.query.card || '';
    if (this.query) {
      this.cardImageUrl = `https://api.scryfall.com/cards/named?fuzzy=${encodeURIComponent(this.query)}&format=image&version=normal`;
      this.cardImageLoaded = true;
      this.fetchBinders();
    } else {
      this.$router.replace('/carpetas');
    }
  },
  watch: {
    '$route.query.card'(val) {
      this.query = val || '';
      this.cardImageUrl = `https://api.scryfall.com/cards/named?fuzzy=${encodeURIComponent(this.query)}&format=image&version=normal`;
      this.cardImageLoaded = true;
      this.fetchBinders();
    }
  },
  methods: {
    fetchBinders() {
      this.loading = true;
      BinderService.getBinders({ card_name: this.query })
        .then(r => { this.binders = r.data; })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    }
  }
};
</script>

<style scoped>
.search-page { min-height: calc(100vh - 64px); }

/* Spotlight */
.spotlight {
  background: linear-gradient(135deg, #0d0e17 0%, #151627 50%, #0d0e17 100%);
  border-bottom: 1px solid var(--border-color);
  padding: 48px 0;
}

.spotlight-inner {
  display: flex; align-items: center; gap: 48px; flex-wrap: wrap;
}

.card-preview { flex-shrink: 0; }

.card-preview-frame {
  width: 160px; height: 224px; border-radius: 10px;
  overflow: hidden; box-shadow: 0 24px 64px rgba(0,0,0,0.8);
  border: 1px solid rgba(255,255,255,0.1);
  filter: drop-shadow(0 0 30px rgba(232,160,32,0.3));
  animation: cardGlow 3s ease-in-out infinite;
}

@keyframes cardGlow {
  0%, 100% { filter: drop-shadow(0 0 20px rgba(232,160,32,0.2)); }
  50%       { filter: drop-shadow(0 0 40px rgba(232,160,32,0.5)); }
}

.card-preview-img { width: 100%; height: 100%; object-fit: cover; display: block; }

.card-preview-placeholder {
  width: 100%; height: 100%;
  background: var(--bg-elevated);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 8px; font-size: 13px; color: var(--text-muted);
}
.card-preview-placeholder span:first-child { font-size: 36px; }

.spotlight-info { flex: 1; }

.eyebrow {
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--accent); margin-bottom: 8px;
}

.card-title {
  font-size: clamp(28px, 5vw, 48px); font-weight: 800;
  color: var(--text-primary); margin-bottom: 16px;
  letter-spacing: -0.02em; line-height: 1.1;
}

.found-in {
  font-size: 18px; color: var(--text-secondary); margin-bottom: 24px;
}
.found-count {
  font-size: 32px; font-weight: 800; color: var(--accent);
  display: block; line-height: 1;
}

.not-found { font-size: 15px; color: var(--text-secondary); margin-bottom: 24px; }

.back-btn { font-size: 13px; }

/* Results */
.results-section { padding: 40px 0 80px; }

.state-msg { color: var(--text-secondary); text-align: center; padding: 48px 0; }

.results-title { font-size: 20px; font-weight: 700; margin-bottom: 24px; }

.binder-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }

.binder-card {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 20px;
  color: var(--text-primary); display: block;
  transition: border-color 0.15s, transform 0.15s;
}
.binder-card:hover { border-color: var(--accent); transform: translateY(-2px); color: var(--text-primary); }

.binder-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.binder-name { font-weight: 600; font-size: 15px; }
.arrow { width: 16px; height: 16px; color: var(--text-muted); flex-shrink: 0; }
.binder-card:hover .arrow { color: var(--accent); }

.binder-owner { color: var(--text-secondary); font-size: 13px; margin-bottom: 12px; }
.binder-owner span { color: var(--accent); }

.binder-meta { display: flex; justify-content: space-between; align-items: center; }
.binder-count { color: var(--text-muted); font-size: 12px; }
.tip { font-size: 11px; color: var(--text-muted); opacity: 0; transition: opacity 0.15s; }
.binder-card:hover .tip { opacity: 1; color: var(--accent); }
</style>
