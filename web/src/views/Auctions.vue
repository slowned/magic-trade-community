<template>
  <div class="auctions container">
    <div class="page-header">
      <div class="header-top">
        <div>
          <h1>Subastas</h1>
          <p class="subtitle">Cartas subastadas por la plataforma. Abren los viernes y cierran el viernes siguiente.</p>
        </div>
        <router-link v-if="isStaff" to="/subastas/admin">
          <button class="btn-primary">+ Nueva subasta</button>
        </router-link>
      </div>

      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="tab"
          :class="{ active: activeTab === tab.value }"
          @click="selectTab(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="state-msg">Cargando subastas...</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <div v-else-if="auctions.length === 0" class="empty-state">
      <div class="empty-icon">🔨</div>
      <p>{{ emptyMessage }}</p>
    </div>

    <div v-else class="auction-grid">
      <AuctionCard v-for="auction in auctions" :key="auction.id" :auction="auction" />
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import AuctionCard from '@/components/AuctionCard.vue';
import BinderService from '@/services/BinderService';

export default {
  name: 'AuctionsView',
  components: { AuctionCard },
  data() {
    return {
      auctions: [],
      loading: true,
      error: null,
      activeTab: 'open',
      // Local clock so the countdown ticks without hammering the API.
      tick: null,
      refresh: null,
    };
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser']),
    isStaff() {
      return !!this.currentUser?.is_staff;
    },
    tabs() {
      const tabs = [
        { value: 'open', label: 'Activas' },
        { value: 'closed', label: 'Cerradas' },
      ];
      if (this.isAuthenticated) tabs.splice(1, 0, { value: 'mine', label: 'Mis pujas' });
      return tabs;
    },
    emptyMessage() {
      if (this.activeTab === 'mine') return 'Todavía no pujaste en ninguna subasta.';
      if (this.activeTab === 'closed') return 'No hay subastas cerradas.';
      return 'No hay subastas activas por ahora. Volvé el viernes.';
    },
  },
  created() {
    this.fetchAuctions();
    // Countdowns are derived client-side; a slower poll keeps prices honest.
    this.tick = setInterval(this.decrementCountdowns, 1000);
    this.refresh = setInterval(this.fetchAuctions, 30000);
  },
  beforeUnmount() {
    clearInterval(this.tick);
    clearInterval(this.refresh);
  },
  methods: {
    selectTab(value) {
      this.activeTab = value;
      this.fetchAuctions();
    },
    fetchAuctions() {
      const params = this.activeTab === 'mine'
        ? { status: 'all', mine: 1 }
        : { status: this.activeTab };

      BinderService.getAuctions(params)
        .then(r => { this.auctions = r.data; this.error = null; })
        .catch(() => { this.error = 'No pudimos cargar las subastas.'; })
        .finally(() => { this.loading = false; });
    },
    decrementCountdowns() {
      this.auctions.forEach(a => {
        if (a.seconds_left > 0) a.seconds_left -= 1;
      });
    },
  },
};
</script>

<style scoped>
.auctions { padding: 32px 24px 64px; }

.page-header { margin-bottom: 28px; }
.header-top {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 16px; flex-wrap: wrap; margin-bottom: 20px;
}
h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }
.subtitle { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }

.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border-color); }
.tab {
  background: none; border: none; border-bottom: 2px solid transparent;
  padding: 10px 16px; font-size: 14px; color: var(--text-secondary);
  border-radius: 0; margin-bottom: -1px;
}
.tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }

.state-msg { padding: 48px 0; text-align: center; color: var(--text-secondary); }
.state-msg.error { color: var(--danger); }

.empty-state { padding: 64px 0; text-align: center; color: var(--text-secondary); }
.empty-icon { font-size: 40px; margin-bottom: 12px; }

.auction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(235px, 1fr));
  gap: 18px;
}

@media (max-width: 600px) {
  .auction-grid { grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)); gap: 12px; }
}
</style>
