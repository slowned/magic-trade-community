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
  --bg-primary: #f4f5f9;
  --bg-surface: #ffffff;
  --bg-elevated: #eaebf2;
  --border-color: #d4d6e8;
  --accent: #b86e10;
  --accent-hover: #d4820f;
  --text-primary: #1a1b2e;
  --text-secondary: #555878;
  --text-muted: #9096b8;
  --success: #2e8f5e;
  --danger: #c94040;
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
.btn-ghost:hover { background-color: var(--bg-elevated); }

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

input, textarea, select {
  background-color: var(--bg-elevated);
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
input:focus, textarea:focus { border-color: var(--accent); }
input::placeholder, textarea::placeholder { color: var(--text-muted); }

.main-content {
  padding-top: 64px;
  min-height: 100vh;
}
</style>
