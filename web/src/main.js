import { createApp } from 'vue'
import App from './App.vue'
import router from '@/router/index.js'
import store from "@/store";

const app = createApp(App)

app.use(router)
app.use(store)
app.mount('#app')

// Revalidate the persisted session against the backend; a dead token
// gets cleaned up by the 401 interceptor (refresh attempt → logout).
if (store.getters.isAuthenticated) {
  store.dispatch('fetchUser').catch(() => {});
}
