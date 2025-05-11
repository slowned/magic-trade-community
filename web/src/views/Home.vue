<template>
  <div>
    <h1>Home</h1>
    <p>Bienvenidos a la página principal.</p>
    <BinderList msg="Listado de Carpetas"/>
  </div>
</template>

<script>
import BinderList from '@/components/BinderList.vue'
export default {
  name: 'HomeView',
  components: {
    BinderList
  }
}
</script>
