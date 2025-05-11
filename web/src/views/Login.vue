<template>
  <div>
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <input v-model="username" placeholder="username" required />
      <input v-model="password" type="password" placeholder="Password" required />
      <button type="submit">Login</button>
    </form>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'LoginView',
  data() {
    return {
      password: '',
      username: ''
    };
  },
  methods: {
    ...mapActions(['login']),
    async handleLogin() {
      const credentials = {
        username: this.username,
        password: this.password
      };

      try {
        await this.login(credentials); // Llama a la acción `login` del store
        this.$router.push('/'); // Redirigir al usuario después del login exitoso
      } catch (error) {
        console.error("Error during login:", error);
        alert("Login failed. Please check your credentials.");
      }
    }
  }
};
</script>
