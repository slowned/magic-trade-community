<template>
  <div class="landing">

    <!-- ══════════════════ HERO ══════════════════ -->
    <section class="hero">
      <!-- Background art: Etali -->
      <div class="hero-art-bg"></div>
      <div class="hero-overlay"></div>

      <div class="hero-content container">
        <!-- LEFT: copy + search -->
        <div class="hero-left">
          <div class="hero-badge">🃏 Magic · Pokémon · Yu-Gi-Oh!</div>
          <h1 class="hero-title">
            El marketplace<br>
            <span class="gradient-text">TCG Argentina</span>
          </h1>
          <p class="hero-subtitle">
            Comprá y vendé cartas P2P. Sin comisiones, sin intermediarios.<br>
            Trato directo entre coleccionistas.
          </p>

          <div class="hero-search-wrap">
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              placeholder="Buscá una carta… Black Lotus, Charizard, Dark Magician…"
            />
            <button @click="handleSearch">Buscar</button>
          </div>

          <div class="hero-ctas">
            <router-link v-if="!isAuthenticated" to="/register">
              <button class="btn-cta-gold">Crear cuenta gratis</button>
            </router-link>
            <router-link to="/carpetas">
              <button class="btn-cta-ghost">Explorar carpetas →</button>
            </router-link>
          </div>
        </div>

        <!-- RIGHT: floating cards -->
        <div class="hero-right" aria-hidden="true">
          <div class="cards-stage">
            <!-- Card 3 — back left -->
            <div class="card-wrap card-wrap-3">
              <div class="card-tilt c3">
                <img
                  src="https://api.scryfall.com/cards/named?exact=Black+Lotus&format=image&version=normal"
                  alt="Black Lotus"
                  class="card-img"
                  loading="lazy"
                />
              </div>
            </div>
            <!-- Card 2 — center -->
            <div class="card-wrap card-wrap-2">
              <div class="card-tilt c2">
                <img
                  src="https://api.scryfall.com/cards/named?exact=Urza%2C+Lord+High+Artificer&format=image&version=normal"
                  alt="Urza"
                  class="card-img"
                  loading="lazy"
                />
              </div>
            </div>
            <!-- Card 1 — front right -->
            <div class="card-wrap card-wrap-1">
              <div class="card-tilt c1">
                <img
                  src="https://api.scryfall.com/cards/named?exact=Etali%2C+Primal+Storm&format=image&version=normal"
                  alt="Etali"
                  class="card-img"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scroll hint -->
      <div class="scroll-hint">
        <div class="scroll-dot"></div>
      </div>
    </section>

    <!-- ══════════════════ STATS ══════════════════ -->
    <div class="stats-strip">
      <div class="container stats-inner">
        <div class="stat-item">
          <span class="stat-v">10,000+</span>
          <span class="stat-l">Cartas en la plataforma</span>
        </div>
        <span class="stat-sep">·</span>
        <div class="stat-item">
          <span class="stat-v">P2P</span>
          <span class="stat-l">Sin intermediarios</span>
        </div>
        <span class="stat-sep">·</span>
        <div class="stat-item">
          <span class="stat-v">Gratis</span>
          <span class="stat-l">Sin comisiones</span>
        </div>
        <span class="stat-sep">·</span>
        <div class="stat-item">
          <span class="stat-v">Argentina</span>
          <span class="stat-l">Comunidad local</span>
        </div>
      </div>
    </div>

    <!-- ══════════════════ FEATURES ══════════════════ -->
    <section class="features">
      <div class="container">
        <p class="eyebrow">¿Cómo funciona?</p>
        <h2 class="section-h">Todo lo que necesitás<br>para coleccionar</h2>

        <div class="feat-grid">
          <div class="feat-card">
            <div class="feat-icon blue">🔍</div>
            <h3>Buscá por carta</h3>
            <p>Encontrá qué usuarios tienen la carta que necesitás con precios en tiempo real desde Scryfall.</p>
          </div>
          <div class="feat-card gold">
            <div class="feat-badge">Popular</div>
            <div class="feat-icon amber">🛒</div>
            <h3>Carritos P2P</h3>
            <p>Armá pedidos directo con el vendedor. Sin fees. Trato 100% entre coleccionistas.</p>
          </div>
          <div class="feat-card">
            <div class="feat-icon green">💬</div>
            <h3>Chat integrado</h3>
            <p>Coordiná envío y pago por chat. Puerta a puerta o retiro en sucursal.</p>
          </div>
          <div class="feat-card">
            <div class="feat-icon red">❤️</div>
            <h3>Wishlist</h3>
            <p>Guardá las cartas que querés conseguir y organizá tu colección objetivo.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════════════ URZA BANNER ══════════════════ -->
    <section class="character-banner">
      <div class="banner-art-bg"></div>
      <div class="banner-overlay"></div>
      <div class="container banner-content">
        <div class="banner-text">
          <p class="eyebrow-light">Comunidad de coleccionistas</p>
          <h2>Encontrá lo que<br>necesitás hoy</h2>
          <p class="banner-sub">Miles de cartas disponibles en binders públicos. Buscá, comprá, coordiná el envío.</p>
          <router-link to="/carpetas">
            <button class="btn-cta-gold">Explorar carpetas</button>
          </router-link>
        </div>
      </div>
    </section>

    <!-- ══════════════════ STEPS ══════════════════ -->
    <section class="steps-section">
      <div class="container">
        <p class="eyebrow">Simple y rápido</p>
        <h2 class="section-h">Tres pasos para conseguir tu carta</h2>
        <div class="steps-grid">
          <div class="step-card">
            <div class="step-num">01</div>
            <h3>Buscá</h3>
            <p>Ingresá el nombre de la carta y encontrá todos los usuarios que la tienen disponible.</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step-card">
            <div class="step-num">02</div>
            <h3>Agregá al carrito</h3>
            <p>Seleccioná cartas del binder del vendedor. Un carrito por vendedor, sin límites.</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step-card">
            <div class="step-num">03</div>
            <h3>Coordiná</h3>
            <p>Confirmá el pedido y coordiná pago y envío por el chat integrado.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ══════════════════ CTA ══════════════════ -->
    <section class="cta-section" v-if="!isAuthenticated">
      <div class="container">
        <div class="cta-box">
          <div class="cta-deco" aria-hidden="true">
            <div class="d-card d1"></div>
            <div class="d-card d2"></div>
            <div class="d-card d3"></div>
          </div>
          <div class="cta-body">
            <h2>¿Tenés cartas para vender?</h2>
            <p>Creá tu binder gratis y empezá a vender a otros coleccionistas hoy mismo.</p>
            <div class="cta-btns">
              <router-link to="/register">
                <button class="btn-cta-gold">Crear cuenta gratis</button>
              </router-link>
              <router-link to="/login">
                <button class="btn-cta-ghost">Iniciar sesión</button>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  name: 'HomeView',
  computed: {
    ...mapGetters(['isAuthenticated']),
  },
  data() {
    return { searchQuery: '' };
  },
  methods: {
    handleSearch() {
      const q = this.searchQuery.trim();
      if (!q) return;
      this.$router.push({ path: '/search', query: { card: q } });
      this.searchQuery = '';
    }
  }
};
</script>

<style scoped>
.landing { overflow-x: hidden; }

/* ── HERO ── */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-art-bg {
  position: absolute;
  inset: 0;
  background-image: url('https://api.scryfall.com/cards/named?exact=Etali%2C+Primal+Storm&format=image&version=art_crop');
  background-size: cover;
  background-position: center 30%;
  transform: scale(1.05);
  animation: heroZoom 20s ease-in-out infinite alternate;
}

@keyframes heroZoom {
  from { transform: scale(1.05); }
  to   { transform: scale(1.12); }
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    105deg,
    rgba(10,10,20,0.97) 0%,
    rgba(10,10,20,0.85) 45%,
    rgba(10,10,20,0.3) 75%,
    rgba(10,10,20,0.7) 100%
  );
}

.hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: center;
  padding-top: 80px;
  padding-bottom: 80px;
}

/* Hero left */
.hero-badge {
  display: inline-block;
  background: rgba(232,160,32,0.12);
  border: 1px solid rgba(232,160,32,0.3);
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.05em;
  margin-bottom: 20px;
}

.hero-title {
  font-size: clamp(42px, 6vw, 72px);
  font-weight: 900;
  line-height: 1.05;
  color: #fff;
  margin-bottom: 20px;
  letter-spacing: -0.03em;
}

.gradient-text {
  background: linear-gradient(90deg, #ffd700 0%, #e8a020 40%, #ff6b35 80%, #e8a020 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shine 4s linear infinite;
}
@keyframes shine { to { background-position: 200% center; } }

.hero-subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.65);
  line-height: 1.7;
  margin-bottom: 32px;
}

.hero-search-wrap {
  display: flex;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 12px;
  padding: 5px 5px 5px 16px;
  max-width: 520px;
  margin-bottom: 24px;
  backdrop-filter: blur(12px);
  transition: border-color 0.2s;
}
.hero-search-wrap:focus-within { border-color: var(--accent); }

.hero-search-wrap input {
  flex: 1; background: transparent; border: none;
  color: #fff; font-size: 14px; outline: none; padding: 10px 0;
}
.hero-search-wrap input::placeholder { color: rgba(255,255,255,0.35); }

.hero-search-wrap button {
  background: var(--accent); color: #0d0e17;
  border: none; border-radius: 8px;
  padding: 10px 22px; font-size: 14px; font-weight: 700;
  cursor: pointer; white-space: nowrap;
  transition: background-color 0.15s;
}
.hero-search-wrap button:hover { background: #f0b840; }

.hero-ctas { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

.btn-cta-gold {
  background: linear-gradient(135deg, #e8a020, #f0b840);
  color: #0d0e17; border: none; border-radius: 10px;
  padding: 13px 28px; font-size: 15px; font-weight: 700;
  cursor: pointer; font-family: inherit;
  box-shadow: 0 0 28px rgba(232,160,32,0.4);
  transition: transform 0.15s, box-shadow 0.15s;
}
.btn-cta-gold:hover { transform: translateY(-2px); box-shadow: 0 0 44px rgba(232,160,32,0.6); }

.btn-cta-ghost {
  background: transparent;
  color: rgba(255,255,255,0.75);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px; padding: 13px 24px;
  font-size: 15px; cursor: pointer; font-family: inherit;
  transition: background-color 0.15s, color 0.15s, border-color 0.15s;
}
.btn-cta-ghost:hover { background: rgba(255,255,255,0.07); color: #fff; border-color: rgba(255,255,255,0.4); }

/* Hero right — card showcase */
.hero-right {
  display: flex;
  align-items: center;
  justify-content: center;
}

.cards-stage {
  position: relative;
  width: 360px;
  height: 480px;
}

.card-wrap {
  position: absolute;
  animation: floatCard 5s ease-in-out infinite;
}

/* Each card positioned in a fan */
.card-wrap-1 { top: 20px;  left: 160px; z-index: 3; animation-delay: 0s; }
.card-wrap-2 { top: 40px;  left: 80px;  z-index: 2; animation-delay: 1.2s; }
.card-wrap-3 { top: 60px;  left: 0px;   z-index: 1; animation-delay: 2.4s; }

@keyframes floatCard {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-18px); }
}

.card-tilt { transition: transform 0.4s ease; }

.c1 { transform: rotate(8deg); }
.c2 { transform: rotate(-3deg); }
.c3 { transform: rotate(-16deg); }

.card-wrap:hover .card-tilt { transform: rotate(0deg) scale(1.05) translateY(-8px) !important; z-index: 10; }

.card-img {
  width: 155px;
  border-radius: 10px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,255,255,0.08);
  display: block;
}

/* Scroll hint */
.scroll-hint {
  position: absolute;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
}
.scroll-dot {
  width: 6px;
  height: 6px;
  background: rgba(255,255,255,0.4);
  border-radius: 50%;
  animation: scrollBounce 2s ease-in-out infinite;
}
@keyframes scrollBounce {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50%       { transform: translateY(8px); opacity: 1; }
}

/* ── STATS ── */
.stats-strip {
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid var(--border-color);
  padding: 18px 0;
}
.stats-inner {
  display: flex; align-items: center; justify-content: center;
  gap: 24px; flex-wrap: wrap;
}
.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-v { font-size: 20px; font-weight: 800; color: var(--accent); letter-spacing: -0.02em; }
.stat-l { font-size: 11px; color: var(--text-secondary); white-space: nowrap; }
.stat-sep { color: var(--border-color); font-size: 20px; }

/* ── FEATURES ── */
.features { padding: 96px 0; background: #0d0e17; }

.eyebrow {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.14em; color: var(--accent); margin-bottom: 10px;
}

.section-h {
  font-size: clamp(26px, 4vw, 42px); font-weight: 800;
  color: var(--text-primary); line-height: 1.15;
  margin-bottom: 52px; letter-spacing: -0.02em;
}

.feat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 18px;
}

.feat-card {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: 16px; padding: 26px; position: relative;
  transition: border-color 0.2s, transform 0.2s;
}
.feat-card:hover { border-color: rgba(232,160,32,0.35); transform: translateY(-4px); }
.feat-card.gold { border-color: rgba(232,160,32,0.25); background: linear-gradient(135deg, rgba(232,160,32,0.04), var(--bg-surface)); }

.feat-badge {
  position: absolute; top: -11px; left: 18px;
  background: var(--accent); color: #0d0e17;
  font-size: 10px; font-weight: 800; padding: 2px 10px; border-radius: 999px;
  text-transform: uppercase; letter-spacing: 0.05em;
}

.feat-icon {
  width: 46px; height: 46px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; margin-bottom: 14px;
}
.feat-icon.blue   { background: rgba(37,99,235,0.15); }
.feat-icon.amber  { background: rgba(232,160,32,0.15); }
.feat-icon.green  { background: rgba(76,175,125,0.15); }
.feat-icon.red    { background: rgba(239,68,68,0.15); }

.feat-card h3 { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.feat-card p  { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

/* ── CHARACTER BANNER ── */
.character-banner {
  position: relative;
  padding: 100px 0;
  overflow: hidden;
}

.banner-art-bg {
  position: absolute;
  inset: 0;
  background-image: url('https://api.scryfall.com/cards/named?exact=Urza%2C+Lord+High+Artificer&format=image&version=art_crop');
  background-size: cover;
  background-position: center;
}

.banner-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(10,10,20,0.95) 0%,
    rgba(10,10,20,0.7) 50%,
    rgba(10,10,20,0.5) 100%
  );
}

.banner-content { position: relative; z-index: 2; }

.banner-text { max-width: 520px; }

.eyebrow-light {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.14em; color: rgba(232,160,32,0.8); margin-bottom: 10px;
}

.banner-text h2 {
  font-size: clamp(32px, 5vw, 52px); font-weight: 900;
  color: #fff; line-height: 1.1; margin-bottom: 16px;
  letter-spacing: -0.02em;
}

.banner-sub { font-size: 15px; color: rgba(255,255,255,0.6); line-height: 1.7; margin-bottom: 28px; }

/* ── STEPS ── */
.steps-section { padding: 96px 0; background: linear-gradient(180deg, #0d0e17, #111220); }

.steps-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  gap: 0;
  align-items: start;
  margin-top: 16px;
}

.step-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 16px; padding: 28px;
  transition: border-color 0.2s;
}
.step-card:hover { border-color: rgba(232,160,32,0.35); }

.step-num {
  font-size: 44px; font-weight: 900;
  color: transparent;
  -webkit-text-stroke: 2px rgba(232,160,32,0.4);
  margin-bottom: 14px; line-height: 1;
}
.step-card h3 { font-size: 17px; font-weight: 700; margin-bottom: 8px; }
.step-card p  { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

.step-arrow {
  display: flex; align-items: center; justify-content: center;
  padding: 0 12px; margin-top: 58px;
  font-size: 22px; color: rgba(232,160,32,0.3);
}

/* ── CTA ── */
.cta-section { padding: 80px 0; background: #0d0e17; }

.cta-box {
  position: relative;
  background: linear-gradient(135deg, rgba(232,160,32,0.07) 0%, rgba(37,99,235,0.05) 100%);
  border: 1px solid rgba(232,160,32,0.2);
  border-radius: 24px; padding: 64px;
  overflow: hidden;
}

.cta-deco { position: absolute; inset: 0; pointer-events: none; }

.d-card {
  position: absolute;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.06);
  background-size: 400% 400%;
  animation: holoShift 12s ease infinite, floatCard 8s ease-in-out infinite;
}
.d1 { width: 100px; height: 140px; right: 8%;  top: -20px;  background: linear-gradient(135deg,#e8a020,#2563eb,#16a34a); opacity:0.25; transform:rotate(15deg); }
.d2 { width: 75px;  height: 105px; right: 20%; bottom:-15px; background: linear-gradient(135deg,#2563eb,#7c3aed,#e8a020); opacity:0.18; transform:rotate(-10deg); animation-delay:3s; }
.d3 { width: 60px;  height: 84px;  right: 13%; top:35%;     background: linear-gradient(135deg,#16a34a,#e8a020,#2563eb); opacity:0.12; transform:rotate(5deg); animation-delay:6s; }

@keyframes holoShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.cta-body { position: relative; z-index: 2; max-width: 540px; }
.cta-body h2 { font-size: clamp(24px,4vw,38px); font-weight: 800; margin-bottom: 12px; letter-spacing: -0.02em; }
.cta-body p  { font-size: 15px; color: var(--text-secondary); line-height: 1.7; margin-bottom: 28px; }

.cta-btns { display: flex; gap: 12px; flex-wrap: wrap; }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .hero-content { grid-template-columns: 1fr; }
  .hero-right { display: none; }
  .steps-grid { grid-template-columns: 1fr; }
  .step-arrow { display: none; }
  .cta-box { padding: 40px 24px; }
  .cta-deco { display: none; }
}
</style>
