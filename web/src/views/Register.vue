<template>
  <div>

    <h2>Registro de Usuario</h2>

    <form @submit.prevent="handleRegister">
      <input v-model="form.username" placeholder="username" required />
      <input v-model="form.password" type="password" placeholder="Password" required />
      <input v-model="form.first_name" placeholder="Stella" required />
      <input v-model="form.last_surname" placeholder="Lee" required />
      <input v-model="form.email" type="password" placeholder="StellaLee@mtg.com" required />
      <!-- opcionales, necesarios despues-->
      <input v-model="direction" placeholder="Direccion" required />
      <button type="submit">Login</button>
    </form>

    <!-- informe de errores -->
    <div v-if="errors.error">
      <p> HAY ERRORES EN LA CREACION </p>
      <p> {{ errors.error }} </p>
    </div>
    <!-- informe de errores -->

  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'RegisterView',
  data() {
    return {
      form: {
        password: '',
        username: '',
        first_name: '',
        last_name: '',
        email: '',
      },
      errors: {
        error: null,
        msg: null,
      }
      
    };
  },
  methods: {
    ...mapActions(['register']),
    async handleRegister() {
      const data = this.form;
      try {
        await this.register(data);
        this.$router.push('/');
      } catch (error) {
        this.errors.error = error
        console.error("Error during login:", error);
        alert("Login failed. Please check your credentials.");
      }
    }
  }
};
</script>
