<template>
  <div class="profile-page container">
    <div class="page-header">
      <div>
        <h1>Mi perfil</h1>
        <p class="subtitle">Datos personales y dirección de envío</p>
      </div>
    </div>

    <div v-if="loading" class="state-msg">Cargando...</div>

    <div v-else class="profile-layout">
      <!-- Avatar section -->
      <div class="profile-sidebar">
        <div class="avatar-card">
          <div class="big-avatar">{{ (form.username || '?')[0].toUpperCase() }}</div>
          <div class="avatar-name">{{ form.username }}</div>
          <div class="avatar-email">{{ form.email }}</div>
        </div>
        <div class="profile-stats">
          <div class="profile-stat">
            <span class="stat-n">{{ binders.length }}</span>
            <span class="stat-l">Carpetas</span>
          </div>
        </div>
      </div>

      <!-- Form -->
      <form class="profile-form" @submit.prevent="save">
        <div class="form-section">
          <h3 class="form-section-title">Datos personales</h3>
          <div class="form-row-2">
            <div class="form-group">
              <label>Nombre</label>
              <input v-model="form.first_name" placeholder="Mariano" />
            </div>
            <div class="form-group">
              <label>Apellido</label>
              <input v-model="form.last_name" placeholder="García" />
            </div>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="form.email" type="email" placeholder="vos@mail.com" />
          </div>
        </div>

        <div class="form-section">
          <h3 class="form-section-title">Datos de envío</h3>
          <p class="form-section-hint">Esta información se muestra al vendedor cuando confirmás un pedido.</p>
          <div class="form-group">
            <label>Teléfono / WhatsApp</label>
            <input v-model="form.phone" placeholder="+54 11 1234-5678" />
          </div>
          <div class="form-group">
            <label>Dirección</label>
            <input v-model="form.address" placeholder="Av. Corrientes 1234, Piso 3" />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Ciudad</label>
              <input v-model="form.city" placeholder="Buenos Aires" />
            </div>
            <div class="form-group">
              <label>Provincia</label>
              <input v-model="form.province" placeholder="CABA" />
            </div>
          </div>
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>
        <div v-if="saved" class="success-msg">✓ Perfil actualizado correctamente</div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'ProfileView',
  data() {
    return {
      loading: true,
      saving: false,
      saved: false,
      error: null,
      binders: [],
      form: {
        username: '', email: '', first_name: '', last_name: '',
        phone: '', address: '', city: '', province: '',
      },
    };
  },
  created() {
    Promise.all([
      BinderService.getProfile(),
      BinderService.getMyBinders(),
    ]).then(([profileRes, bindersRes]) => {
      Object.assign(this.form, profileRes.data);
      this.binders = bindersRes.data;
    }).catch(e => console.error(e))
      .finally(() => { this.loading = false; });
  },
  methods: {
    async save() {
      this.saving = true;
      this.error = null;
      this.saved = false;
      try {
        await BinderService.updateProfile(this.form);
        this.saved = true;
        setTimeout(() => { this.saved = false; }, 3000);
      } catch (e) {
        this.error = 'Error al guardar. Verificá los datos.';
      } finally {
        this.saving = false;
      }
    }
  }
};
</script>

<style scoped>
.profile-page { padding-top: 40px; padding-bottom: 64px; }

.page-header { margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color); }
.page-header h1 { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
.subtitle { color: var(--text-secondary); font-size: 14px; }

.state-msg { color: var(--text-secondary); text-align: center; padding: 48px 0; }

.profile-layout { display: grid; grid-template-columns: 240px 1fr; gap: 24px; align-items: start; }

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
.avatar-email { font-size: 12px; color: var(--text-secondary); word-break: break-all; }

.profile-stats {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 16px 20px;
  display: flex; gap: 0;
}
.profile-stat { flex: 1; text-align: center; }
.stat-n { display: block; font-size: 22px; font-weight: 800; color: var(--accent); }
.stat-l { display: block; font-size: 12px; color: var(--text-secondary); }

/* Form */
.profile-form {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 28px;
}

.form-section { margin-bottom: 32px; }
.form-section:last-of-type { margin-bottom: 0; }

.form-section-title {
  font-size: 14px; font-weight: 700; color: var(--text-primary);
  margin-bottom: 6px; padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  text-transform: uppercase; letter-spacing: 0.05em; font-size: 12px;
}

.form-section-hint { font-size: 12px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.5; }

.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.form-group { margin-bottom: 14px; }
.form-group label {
  display: block; color: var(--text-secondary);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px;
}

.error-msg {
  color: var(--danger); font-size: 13px; margin-bottom: 12px;
  padding: 10px 12px; background: rgba(224,85,85,0.1);
  border-radius: var(--radius-sm); border: 1px solid rgba(224,85,85,0.2);
}

.success-msg {
  color: var(--success); font-size: 13px; margin-bottom: 12px;
  padding: 10px 12px; background: rgba(76,175,125,0.1);
  border-radius: var(--radius-sm); border: 1px solid rgba(76,175,125,0.2);
}

.form-actions { margin-top: 24px; display: flex; justify-content: flex-end; }

@media (max-width: 768px) {
  .profile-layout { grid-template-columns: 1fr; }
}
</style>
