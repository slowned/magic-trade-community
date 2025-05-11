<template>
  <div class="binders">
    <h1>{{ msg }}</h1>

    <ul>
      <li v-for="binder in binders" :key="binder.id">
        <router-link :to="{ name: 'BinderDetail', params: { id: binder.id } }">
          {{ binder.name }} ** {{ binder.id }} **- Created by: {{ binder.user }}
        </router-link>
      </li>
    </ul>

  </div>
</template>

<script>
import BinderService from "@/services/BinderService";

export default {
  name: 'BindersList',
  props: {
    msg: String
  },
  data() {
    return {
      binders: []
    };
  },
  created() {
    BinderService.getBinders()
      .then(response => {
      this.binders = response.data;
      })
      .catch(error => {
      console.error('Error fetching binders:', error);
      });
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.binders {
  border: 1px solid black;
}
</style>
