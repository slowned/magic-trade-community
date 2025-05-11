<template>
  <nav class="navbar">
    <router-link to="/">Home</router-link>

    {{ isAuthenticated }}
    <div v-if="isAuthenticated">
      <p>Bienvenido, {{ currentUser?.username }}</p>
      <button @click="logout">Cerrar sesión</button>
    </div>
    <div v-else>
      <router-link to="/login">Iniciar sesión</router-link>
      <router-link to="/">Registrarse</router-link>
    </div>

</nav>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'NavbarComponent',
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser']),
  },
  methods: {
    ...mapActions(['logout']),
  },
};
</script>

<style scoped>
.navbar {
  border: 1px solid black;
  padding: 10px;
}
</style>

