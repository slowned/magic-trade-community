<template>
  <div class="my-binders container">
    <div class="page-header">
      <div>
        <h1>Mis carpetas</h1>
        <p class="subtitle">Administrá tus colecciones de cartas</p>
      </div>
      <button class="btn-primary" @click="showCreateModal = true">+ Nueva carpeta</button>
    </div>

    <div v-if="loading" class="state-msg">Cargando...</div>

    <div v-else-if="binders.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <p>No tenés carpetas todavía.</p>
      <button class="btn-primary" @click="showCreateModal = true">Crear primera carpeta</button>
    </div>

    <div v-else class="binder-grid">
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
        <div class="binder-count">{{ binder.card_count != null ? binder.card_count + ' cartas' : '—' }}</div>
      </router-link>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h3>Nueva carpeta</h3>
        <div class="form-group">
          <label>Nombre</label>
          <input v-model="newBinder.name" placeholder="Mi colección" @keyup.enter="handleCreate" />
        </div>
        <div class="form-row">
          <label class="toggle-label">
            <input type="checkbox" v-model="newBinder.is_public" style="width:auto" />
            <span>Pública (visible para todos)</span>
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showCreateModal = false">Cancelar</button>
          <button class="btn-primary" @click="handleCreate" :disabled="!newBinder.name.trim()">
            Crear
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'MyBinders',
  data() {
    return {
      binders: [],
      loading: true,
      showCreateModal: false,
      newBinder: { name: '', is_public: true },
    };
  },
  created() {
    this.fetchBinders();
  },
  methods: {
    fetchBinders() {
      this.loading = true;
      BinderService.getMyBinders()
        .then(r => { this.binders = r.data; })
        .catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    },
    async handleCreate() {
      if (!this.newBinder.name.trim()) return;
      try {
        const res = await BinderService.createBinder(this.newBinder);
        this.showCreateModal = false;
        this.newBinder = { name: '', is_public: true };
        this.$router.push({ name: 'BinderDetail', params: { id: res.data.id } });
      } catch (e) {
        console.error(e);
      }
    }
  }
};
</script>

<style scoped>
.my-binders {
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

.page-header h1 {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 4px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

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
  margin-bottom: 10px;
}

.binder-name { font-weight: 600; font-size: 15px; }

.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge.public { background: rgba(76,175,125,0.15); color: var(--success); }
.badge.private { background: rgba(232,160,32,0.15); color: var(--accent); }

.binder-count { color: var(--text-muted); font-size: 12px; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
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
  width: 360px;
}

.modal h3 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }

.form-group { margin-bottom: 16px; }

.form-group label {
  display: block;
  color: var(--text-secondary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
}

.form-row { margin-bottom: 16px; }

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 13px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
}
</style>
