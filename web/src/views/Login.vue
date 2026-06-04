<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h2>Iniciar sesión</h2>
        <p>¿No tenés cuenta? <router-link to="/register">Registrate</router-link></p>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Usuario</label>
          <input
            v-model="username"
            placeholder="tu_usuario"
            autocomplete="username"
            required
          />
        </div>
        <div class="form-group">
          <label>Contraseña</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="btn-primary submit-btn" :disabled="loading">
          {{ loading ? 'Entrando...' : 'Iniciar sesión' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'LoginView',
  data() {
    return { username: '', password: '', error: null, loading: false };
  },
  methods: {
    ...mapActions(['login']),
    async handleLogin() {
      this.error = null;
      this.loading = true;
      try {
        await this.login({ username: this.username, password: this.password });
        this.$router.push('/');
      } catch (e) {
        this.error = 'Usuario o contraseña incorrectos.';
      } finally {
        this.loading = false;
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
  max-width: 380px;
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

.form-group {
  margin-bottom: 16px;
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
  margin-top: 4px;
}
</style>
