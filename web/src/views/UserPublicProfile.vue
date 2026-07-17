<template>
  <div class="public-profile container">
    <div v-if="loading" class="state-msg">Cargando...</div>
    <div v-else-if="notFound" class="state-msg">Usuario no encontrado.</div>

    <div v-else class="profile-layout">
      <!-- Identity + trust score -->
      <div class="profile-sidebar">
        <div class="avatar-card">
          <div class="big-avatar">{{ profile.username[0].toUpperCase() }}</div>
          <div class="avatar-name">{{ profile.username }}</div>
          <div class="avatar-since">Miembro desde {{ formatDate(profile.date_joined) }}</div>

          <div class="trust-score" :class="scoreClass">
            <template v-if="profile.rating_avg !== null">
              <span class="trust-n">{{ profile.rating_avg }}</span>
              <span class="trust-max">/10</span>
              <div class="trust-label">
                Confiabilidad · {{ profile.rating_count }}
                {{ profile.rating_count === 1 ? 'puntuación' : 'puntuaciones' }}
              </div>
            </template>
            <template v-else>
              <span class="trust-none">Sin puntuaciones aún</span>
            </template>
          </div>
        </div>

        <div class="profile-stats">
          <div class="profile-stat">
            <span class="stat-n">{{ profile.successful_trades }}</span>
            <span class="stat-l">Trades exitosos</span>
          </div>
          <div class="profile-stat">
            <span class="stat-n">{{ profile.cards_sold }}</span>
            <span class="stat-l">Cartas vendidas</span>
          </div>
        </div>
      </div>

      <div class="profile-main">
        <!-- Public binders -->
        <div class="panel">
          <h3 class="panel-title">Carpetas públicas</h3>
          <div v-if="profile.binders.length === 0" class="empty-msg">No tiene carpetas públicas.</div>
          <div v-else class="binder-list">
            <router-link
              v-for="binder in profile.binders"
              :key="binder.id"
              :to="`/binder/${binder.id}`"
              class="binder-row"
            >
              <span class="binder-name">{{ binder.name }}</span>
              <span class="binder-count">{{ binder.card_count }} cartas</span>
            </router-link>
          </div>
        </div>

        <!-- Recent ratings -->
        <div class="panel">
          <h3 class="panel-title">Últimas puntuaciones</h3>
          <div v-if="profile.recent_ratings.length === 0" class="empty-msg">
            Todavía no recibió puntuaciones.
          </div>
          <div v-else class="rating-list">
            <div v-for="rating in profile.recent_ratings" :key="rating.id" class="rating-row">
              <div class="rating-row-header">
                <span class="rating-score" :class="scoreColorClass(rating.score)">{{ rating.score }}/10</span>
                <span class="rating-rater">por {{ rating.rater }}</span>
                <span class="rating-date">{{ formatDate(rating.created_at) }}</span>
              </div>
              <p v-if="rating.comment" class="rating-text">“{{ rating.comment }}”</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'UserPublicProfile',
  props: { username: { type: String, required: true } },
  data() {
    return {
      loading: true,
      notFound: false,
      profile: null,
    };
  },
  computed: {
    scoreClass() {
      if (this.profile?.rating_avg === null) return '';
      return this.scoreColorClass(this.profile.rating_avg);
    },
  },
  watch: {
    username() { this.load(); },
  },
  created() {
    this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      this.notFound = false;
      try {
        const res = await BinderService.getPublicProfile(this.username);
        this.profile = res.data;
      } catch (e) {
        this.notFound = true;
      } finally {
        this.loading = false;
      }
    },
    scoreColorClass(score) {
      if (score >= 7) return 'score-good';
      if (score >= 4) return 'score-mid';
      return 'score-bad';
    },
    formatDate(iso) {
      const d = new Date(iso);
      return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    },
  },
};
</script>

<style scoped>
.public-profile { padding-top: 40px; padding-bottom: 64px; }

.state-msg { color: var(--text-secondary); text-align: center; padding: 48px 0; }

.profile-layout { display: grid; grid-template-columns: 260px 1fr; gap: 24px; align-items: start; }

/* Sidebar */
.profile-sidebar { display: flex; flex-direction: column; gap: 16px; }

.avatar-card {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 28px 20px; text-align: center;
}

.big-avatar {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #f0b840);
  color: #0d0e17; font-size: 28px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 12px;
}

.avatar-name { font-size: 16px; font-weight: 700; margin-bottom: 4px; }
.avatar-since { font-size: 12px; color: var(--text-secondary); }

.trust-score {
  margin-top: 16px; padding-top: 16px;
  border-top: 1px solid var(--border-color);
}
.trust-n { font-size: 36px; font-weight: 800; }
.trust-max { font-size: 16px; color: var(--text-secondary); font-weight: 600; }
.trust-score.score-good .trust-n { color: var(--success); }
.trust-score.score-mid .trust-n { color: var(--accent); }
.trust-score.score-bad .trust-n { color: var(--danger); }
.trust-label { font-size: 11px; color: var(--text-secondary); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.trust-none { font-size: 13px; color: var(--text-muted); }

.profile-stats {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 16px 12px;
  display: flex;
}
.profile-stat { flex: 1; text-align: center; }
.stat-n { display: block; font-size: 22px; font-weight: 800; color: var(--accent); }
.stat-l { display: block; font-size: 11px; color: var(--text-secondary); margin-top: 2px; }

/* Main panels */
.profile-main { display: flex; flex-direction: column; gap: 20px; }

.panel {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 20px 24px;
}

.panel-title {
  font-size: 12px; font-weight: 700; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.05em;
  padding-bottom: 12px; margin-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
}

.empty-msg { font-size: 13px; color: var(--text-muted); }

.binder-list { display: flex; flex-direction: column; gap: 8px; }
.binder-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; border-radius: var(--radius-sm);
  background: var(--bg-elevated); border: 1px solid var(--border-color);
  transition: border-color 0.15s;
}
.binder-row:hover { border-color: var(--accent); }
.binder-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.binder-count { font-size: 12px; color: var(--text-secondary); }

.rating-list { display: flex; flex-direction: column; gap: 14px; }
.rating-row { border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }
.rating-row:last-child { border-bottom: none; padding-bottom: 0; }

.rating-row-header { display: flex; align-items: center; gap: 10px; }
.rating-score {
  font-size: 13px; font-weight: 700; padding: 2px 10px; border-radius: 999px;
}
.rating-score.score-good { background: rgba(76,175,125,0.15); color: var(--success); }
.rating-score.score-mid { background: rgba(232,160,32,0.15); color: var(--accent); }
.rating-score.score-bad { background: rgba(224,85,85,0.15); color: var(--danger); }
.rating-rater { font-size: 13px; color: var(--text-secondary); }
.rating-date { font-size: 12px; color: var(--text-muted); margin-left: auto; }
.rating-text { font-size: 13px; color: var(--text-secondary); margin-top: 6px; font-style: italic; }

@media (max-width: 768px) {
  .profile-layout { grid-template-columns: 1fr; }
}
</style>
