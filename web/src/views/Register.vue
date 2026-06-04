<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h2>Crear cuenta</h2>
        <p>¿Ya tenés cuenta? <router-link to="/login">Iniciá sesión</router-link></p>
      </div>

      <form @submit.prevent="handleRegister">
        <div class="form-row">
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
          <label>Usuario *</label>
          <input
            v-model="form.username"
            placeholder="tu_usuario"
            autocomplete="username"
            required
          />
        </div>

        <div class="form-group">
          <label>Email *</label>
          <input
            v-model="form.email"
            type="email"
            placeholder="vos@mail.com"
            autocomplete="email"
            required
          />
        </div>

        <div class="form-group">
          <label>Contraseña *</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />
        </div>

        <div v-if="errors.error" class="error-msg">{{ errors.error }}</div>

        <button type="submit" class="btn-primary submit-btn">Crear cuenta</button>
      </form>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'RegisterView',
  data() {
    return {
      form: { username: '', password: '', first_name: '', last_name: '', email: '' },
      errors: { error: null }
    };
  },
  methods: {
    ...mapActions(['register']),
    async handleRegister() {
      this.errors.error = null;
      try {
        await this.register(this.form);
        this.$router.push('/');
      } catch (error) {
        this.errors.error = 'Error al crear la cuenta. Verificá los datos.';
      }
    }
  }
};
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.auth-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 36px;
  width: 100%;
  max-width: 420px;
}

.auth-header {
  margin-bottom: 28px;
}

.auth-header h2 {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 6px;
}

.auth-header p {
  color: var(--text-secondary);
  font-size: 13px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  color: var(--text-secondary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
}

.error-msg {
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 12px;
  padding: 10px 12px;
  background: rgba(224, 85, 85, 0.1);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(224, 85, 85, 0.2);
}

.submit-btn {
  width: 100%;
  height: 42px;
  font-size: 15px;
  margin-top: 8px;
}
</style>
