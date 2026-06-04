<template>
  <div>
    <div v-if="loading" class="state-msg">Cargando binders...</div>
    <div v-else-if="filtered.length === 0" class="state-msg">
      {{ searchQuery ? 'Ningún usuario tiene "' + searchQuery + '" en su binder.' : 'No hay binders públicos todavía.' }}
    </div>
    <div v-else class="binder-grid">
      <router-link
        v-for="binder in filtered"
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
        <div class="binder-owner">por {{ binder.user }}</div>
        <div class="binder-meta">
          <span class="binder-count">{{ binder.card_count != null ? binder.card_count + ' cartas' : '—' }}</span>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import BinderService from "@/services/BinderService";

export default {
  name: 'BindersList',
  props: {
    searchQuery: { type: String, default: '' }
  },
  data() {
    return { binders: [], loading: true };
  },
  computed: {
    ...mapGetters(['currentUser']),
    filtered() {
      const list = this.binders || [];
      if (this.currentUser?.username) {
        return list.filter(b => b.user !== this.currentUser.username);
      }
      return list;
    }
  },
  watch: {
    searchQuery(val) {
      this.fetchBinders(val);
    }
  },
  created() {
    this.fetchBinders(this.searchQuery);
  },
  methods: {
    fetchBinders(cardName = '') {
      this.loading = true;
      const params = cardName ? { card_name: cardName } : {};
      BinderService.getBinders(params)
        .then(r => { this.binders = r.data; })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    }
  }
}
</script>

<style scoped>
.state-msg {
  color: var(--text-secondary);
  text-align: center;
  padding: 48px 0;
}

.binder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.binder-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 20px;
  color: var(--text-primary);
  display: block;
  transition: border-color 0.15s, background-color 0.15s;
}

.binder-card:hover {
  border-color: var(--accent);
  background-color: var(--bg-elevated);
  color: var(--text-primary);
}

.binder-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.binder-name {
  font-weight: 600;
  font-size: 15px;
  line-height: 1.3;
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge.public {
  background: rgba(76, 175, 125, 0.15);
  color: var(--success);
}

.badge.private {
  background: rgba(232, 160, 32, 0.15);
  color: var(--accent);
}

.binder-owner {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 12px;
}

.binder-count {
  color: var(--text-muted);
  font-size: 12px;
}
</style>
