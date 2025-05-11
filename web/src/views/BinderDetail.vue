<template>
  <div>
    <h1>Detalle del Binder</h1>
    <p>Información detallada sobre el binder seleccionado.</p>

    <button @click="showModal = true"> BULK UPDATE </button>

    <div v-if="showModal" class="modal-overlay">
      <div class="modal-content">
      <textarea v-model="newCards" placeholder="Escribir los nombre de las cartas"></textarea>
      <button @click="addCardsToBinder">Agregar</button>
      <button @click="showModal = false">Cerrar</button>

      <button @click="check">check</button>
      </div>
    </div>



    <ul>
      <li v-for="card in cards" :key="card.id">
        <p> {{ card.name }} </p>
        <img :src="card.image_uri" :alt="card.name" width="280" height="400" />
      </li>
    </ul>
  </div>
</template>

<script>
import BinderService from "@/services/BinderService";
export default {
  name: 'BinderDetail',
  components: {
  },
  data() {
    return {
      cards: [],
      showModal: false,
      newCards: ""
    }
  },
  created() {
    this.fetchBinderCards();
  },
  methods: {
    exists(cardNames) {
      BinderService.cardExists(cardNames);
    },
    check() {
      console.log("check method");
      console.log("CARDS TO ADD: ", this.newCards);
      const cardNames = this.newCards.split('\n').map(line => {
        const elements = line.trim().split(' ');
        if (!isNaN(elements[0])) {
          elements.shift();
        }
        return elements.join(' ');
      }).filter(name => name.length > 0); 
      self.exists(cardNames);
    },
    addCardsToBinder() {
      console.log("CARDS TO ADD: ", this.newCards);
      const cardNames = this.newCards.split('\n').map(name => name.trim()).filter(name => name);
      const binderId = this.$route.params.id;

      // Verifica que estés usando `then` y `catch` correctamente en esta llamada
      BinderService.addCardsToBinder(binderId, cardNames)
        .then(() => {
          alert("Cartas agregadas correctamente");
          this.showModal = false; // Cerrar el modal
          this.newCards = ""; // Limpiar el campo de entrada
          this.fetchBinderCards(); // Actualizar la lista de cartas en el binder
        })
        .catch(error => {
          console.error("Error adding cards to binder:", error);
          alert("Hubo un problema al agregar las cartas.");
        });
    },
    fetchBinderCards() {
      const id = this.$route.params.id;
      BinderService.getBinder(id)
        .then(response => {
          console.log("BINDER CARD LIST", response.data);
          this.cards = response.data.card_set;
        })
        .catch(error => {
          console.error("Error fetching binder cards:", error);
        });
    }
  },
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  width: 300px;
  text-align: center;
}

textarea {
  width: 100%;
  height: 80px;
  margin-bottom: 10px;
}
</style>
