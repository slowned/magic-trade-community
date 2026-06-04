import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import BinderDetail from '@/views/BinderDetail.vue'
import MyBinders from '@/views/MyBinders.vue'
import Wishlist from '@/views/Wishlist.vue'
import Cart from '@/views/Cart.vue'
import OrderChat from '@/views/OrderChat.vue'
import Profile from '@/views/Profile.vue'
import Explore from '@/views/Explore.vue'
import SearchResults from '@/views/SearchResults.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: false },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false },
  },
  {
    path: '/binder/:id',
    name: 'BinderDetail',
    component: BinderDetail,
    props: true,
    meta: { requiresAuth: false },
  },
  {
    path: '/my-binders',
    name: 'MyBinders',
    component: MyBinders,
    meta: { requiresAuth: true },
  },
  {
    path: '/wishlist',
    name: 'Wishlist',
    component: Wishlist,
    meta: { requiresAuth: true },
  },
  {
    path: '/cart',
    name: 'Cart',
    component: Cart,
    meta: { requiresAuth: true },
  },
  {
    path: '/cart/:cartId',
    name: 'OrderChat',
    component: OrderChat,
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true },
  },
  {
    path: '/carpetas',
    name: 'Explore',
    component: Explore,
    meta: { requiresAuth: false },
  },
  {
    path: '/search',
    name: 'SearchResults',
    component: SearchResults,
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'Login' });
  } else if (to.name === 'Login' && isAuthenticated) {
    next({ name: 'Home' });
  } else {
    next();
  }
})

export default router
