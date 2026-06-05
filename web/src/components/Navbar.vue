<template>
  <nav class="navbar">
    <div class="navbar-inner container">
      <div class="navbar-left">
        <router-link to="/" class="navbar-logo">
          <img src="@/assets/magic-the-gathering.png" alt="MTG Trade" class="logo-img" />
          <span class="logo-text">MTG Trade</span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/carpetas" class="nav-link">Carpetas</router-link>
          <router-link v-if="isAuthenticated" to="/scanner" class="nav-link scanner-link" title="Escanear carta">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
            <span class="scanner-label">Escanear</span>
          </router-link>
        </nav>
      </div>

      <div class="navbar-search">
        <div class="search-wrapper">
          <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
          <input
            v-model="searchQuery"
            @keyup.enter="handleSearch"
            placeholder="Buscar carta en la comunidad..."
            class="search-input"
          />
        </div>
      </div>

      <div class="navbar-right">
        <template v-if="isAuthenticated">
          <div class="user-menu" ref="userMenu">
            <button class="user-btn" @click="toggleMenu">
              <span class="user-avatar">{{ userInitial }}</span>
              <span class="username">{{ currentUser?.username }}</span>
              <svg class="chevron" :class="{ open: menuOpen }" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>

            <div v-if="menuOpen" class="dropdown">
              <router-link to="/my-binders" class="dropdown-item" @click="menuOpen = false">
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" /></svg>
                Mis carpetas
              </router-link>
              <router-link to="/wishlist" class="dropdown-item" @click="menuOpen = false">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd" /></svg>
                Wishlist
              </router-link>
              <router-link to="/cart" class="dropdown-item" @click="menuOpen = false">
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3z"/><path d="M16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/></svg>
                Carritos y ventas
              </router-link>
              <router-link to="/profile" class="dropdown-item" @click="menuOpen = false">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>
                Mi perfil
              </router-link>
              <div class="dropdown-divider" />
              <button class="dropdown-item danger" @click="handleLogout">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd" /></svg>
                Cerrar sesión
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <router-link to="/login">
            <button class="btn-ghost">Iniciar sesión</button>
          </router-link>
          <router-link to="/register">
            <button class="btn-primary">Registrarse</button>
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'NavbarComponent',
  data() {
    return { searchQuery: '', menuOpen: false };
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser']),
    userInitial() {
      return (this.currentUser?.username || '?')[0].toUpperCase();
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    ...mapActions(['logout']),
    toggleMenu() {
      this.menuOpen = !this.menuOpen;
    },
    handleClickOutside(e) {
      if (this.$refs.userMenu && !this.$refs.userMenu.contains(e.target)) {
        this.menuOpen = false;
      }
    },
    async handleLogout() {
      this.menuOpen = false;
      this.logout();
      this.$router.push('/login');
    },
    handleSearch() {
      const q = this.searchQuery.trim();
      if (!q) return;
      this.$router.push({ path: '/search', query: { card: q } });
      this.searchQuery = '';
    }
  },
};
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 64px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
}

.navbar-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 100%;
}

.navbar-left { flex-shrink: 0; display: flex; align-items: center; gap: 20px; }

.nav-links { display: flex; gap: 4px; }

.nav-link {
  color: var(--text-secondary);
  font-size: 14px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background-color 0.15s;
  text-decoration: none;
}
.nav-link:hover { color: var(--text-primary); background: var(--bg-elevated); }

.scanner-link { display: flex; align-items: center; gap: 5px; }
.scanner-link svg { width: 15px; height: 15px; }
.scanner-label { font-size: 14px; }

.navbar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font-weight: 700;
  font-size: 16px;
}

.logo-img { height: 28px; width: 28px; object-fit: contain; }

.navbar-search {
  flex: 1;
  max-width: 420px;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  padding-left: 34px;
  height: 36px;
  background-color: var(--bg-primary);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
}

/* User menu */
.user-menu { position: relative; }

.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 5px 12px 5px 6px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background-color 0.15s;
}

.user-btn:hover { background-color: var(--bg-elevated); }

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--accent);
  color: #12131a;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.username { font-size: 13px; }

.chevron {
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  transition: transform 0.2s;
}
.chevron.open { transform: rotate(180deg); }

.dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 192px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  padding: 4px;
  z-index: 200;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  font-family: inherit;
  transition: background-color 0.1s;
  text-decoration: none;
}

.dropdown-item:hover {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
}

.dropdown-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--text-muted);
}

.dropdown-item.danger { color: var(--danger); }
.dropdown-item.danger svg { color: var(--danger); }
.dropdown-item.danger:hover { background-color: rgba(224, 85, 85, 0.1); }

.dropdown-divider {
  height: 1px;
  background: var(--border-color);
  margin: 4px 0;
}

button { padding: 7px 14px; }
</style>
