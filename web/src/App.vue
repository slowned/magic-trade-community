<template>
  <div id="app">
    <Navbar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar.vue";

export default {
  name: 'App',
  components: { Navbar }
}
</script>

<style>
:root {
  color-scheme: dark;

  /* Same ink as the landing, so the app and the marketing page are one surface. */
  --bg-primary: #0d0e17;
  --bg-surface: #14161f;
  --bg-elevated: #1c1f2b;
  --border-color: #272b3a;
  --border-strong: #363b4e;

  /* Gold pulled from the Bazaar of Baghdad art the navbar is built on. */
  --accent: #e8a020;
  --accent-hover: #f0b840;
  --accent-soft: rgba(232, 160, 32, 0.13);

  --text-primary: #e9ebf3;
  --text-secondary: #9ba1b9;
  --text-muted: #6c7289;

  --success: #4caf7d;
  --danger: #e35d5d;

  --radius: 8px;
  --radius-sm: 4px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

button {
  cursor: pointer;
  border: none;
  font-family: inherit;
  font-size: 14px;
  border-radius: var(--radius-sm);
  padding: 8px 16px;
  transition: background-color 0.15s, color 0.15s;
}

.btn-primary {
  background-color: var(--accent);
  color: #12131a;
  font-weight: 600;
}
.btn-primary:hover:not(:disabled) { background-color: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  background-color: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.btn-ghost:hover { background-color: var(--bg-elevated); border-color: var(--border-strong); }

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

input, textarea, select {
  background-color: #10121a;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 14px;
  padding: 8px 12px;
  width: 100%;
  outline: none;
  transition: border-color 0.15s;
}
input:focus, textarea:focus, select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
input::placeholder, textarea::placeholder { color: var(--text-muted); }

.main-content {
  padding-top: 64px;
  min-height: 100vh;
}

::-webkit-scrollbar { width: 11px; height: 11px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: #2b3040; border-radius: 6px; border: 2px solid var(--bg-primary); }
::-webkit-scrollbar-thumb:hover { background: #3a4054; }
</style>
