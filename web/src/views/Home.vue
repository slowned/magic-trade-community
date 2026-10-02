<template>
  <div class="landing">

    <!-- ══════════════════ HERO ══════════════════ -->
    <section class="hero" :class="{ 'has-feature': !!featured }">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="hero-grid-lines" aria-hidden="true"></div>

      <div class="hero-content container">
        <!-- LEFT: copy + search -->
        <div class="hero-left">
          <div class="hero-badge">🃏 Magic: The Gathering</div>
          <h1 class="hero-title">
            El marketplace<br>
            <span class="gradient-text">TCG Argentina</span>
          </h1>
          <p class="hero-subtitle">
            Comprá y vendé cartas P2P, o pujá en las subastas semanales.
            Trato directo entre coleccionistas.
          </p>

          <div class="hero-search-wrap">
            <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
            </svg>
            <input
              v-model="searchQuery"
              @keyup.enter="handleSearch"
              placeholder="Buscá una carta… Black Lotus, Lightning Bolt…"
              aria-label="Buscar carta"
            />
            <button @click="handleSearch">Buscar</button>
          </div>

          <div class="hero-ctas">
            <router-link v-if="!isAuthenticated" to="/register">
              <button class="btn-cta-gold">Crear cuenta gratis</button>
            </router-link>
            <router-link to="/subastas">
              <button class="btn-cta-ghost">Ver subastas →</button>
            </router-link>
            <router-link to="/carpetas">
              <button class="btn-cta-plain">Explorar carpetas</button>
            </router-link>
          </div>
        </div>

        <!-- RIGHT: the auction closing soonest, so it lands above the fold -->
        <aside v-if="featured" class="hero-feature">
          <router-link :to="`/subasta/${featured.id}`" class="feature-card">
            <div class="feature-head">
              <span class="feature-eyebrow">
                <span class="live-dot" :class="{ scheduled: featured.status === 'scheduled' }"></span>
                {{ featured.status === 'scheduled' ? 'Próxima subasta' : 'Subasta en curso' }}
              </span>
              <span class="feature-timer" :class="featuredUrgency">{{ featuredTimer }}</span>
            </div>

            <div class="feature-body">
              <img
                v-if="featured.display_image"
                :src="featured.display_image"
                :alt="featured.display_title"
                class="feature-img"
              />
              <div class="feature-info">
                <h2 class="feature-title">{{ featured.display_title }}</h2>
                <p class="feature-meta">{{ featured.card.set_name }} · {{ featured.condition_display }}</p>

                <span class="feature-price-label">
                  {{ featured.bid_count ? 'Oferta actual' : 'Precio inicial' }}
                </span>
                <span class="feature-price">{{ formatArs(featured.current_price) }}</span>
                <span class="feature-bids">
                  {{ featured.bid_count }} {{ featured.bid_count === 1 ? 'puja' : 'pujas' }}
                </span>

                <span class="feature-cta">Ofertar →</span>
              </div>
            </div>
          </router-link>
        </aside>
      </div>
    </section>

    <!-- ══════════════════ SUBASTAS ACTIVAS ══════════════════ -->
    <section v-if="restAuctions.length" class="auctions-strip">
      <div class="container">
        <div class="strip-head">
          <div>
            <p class="eyebrow">Cerrando pronto</p>
            <h2 class="section-h tight">Subastas activas</h2>
          </div>
          <router-link to="/subastas" class="see-all">Ver todas →</router-link>
        </div>

        <div class="strip-grid">
          <AuctionCard
            v-for="auction in restAuctions"
            :key="auction.id"
            :auction="auction"
            dark
          />
        </div>
      </div>
    </section>

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
            <div class="feat-icon purple">🔨</div>
            <h3>Subastas</h3>
            <p>Cargás tu oferta máxima y pujamos por vos. Abren los viernes y cierran el viernes siguiente.</p>
          </div>
          <div class="feat-card">
            <div class="feat-icon green">💬</div>
            <h3>Chat integrado</h3>
            <p>Coordiná envío y pago por chat. Puerta a puerta o retiro en sucursal.</p>
          </div>
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
import AuctionCard from '@/components/AuctionCard.vue';
import BinderService from '@/services/BinderService';
import { formatArs, formatCountdown, urgencyClass } from '@/utils/auction';

export default {
  name: 'HomeView',
  components: { AuctionCard },
  computed: {
    ...mapGetters(['isAuthenticated']),
    /** Spotlight the one closing soonest — a live auction beats a scheduled one. */
    featured() {
      return this.auctions.find(a => a.status === 'live') || this.auctions[0] || null;
    },
    restAuctions() {
      return this.auctions.filter(a => a.id !== this.featured?.id).slice(0, 4);
    },
    featuredTimer() {
      if (!this.featured) return '';
      if (this.featured.status === 'scheduled') return 'Pronto';
      return `Cierra en ${formatCountdown(this.featured.seconds_left)}`;
    },
    featuredUrgency() {
      return this.featured ? urgencyClass(this.featured.seconds_left) : 'normal';
    },
  },
  data() {
    return { searchQuery: '', auctions: [], tick: null };
  },
  created() {
    this.fetchAuctions();
    this.tick = setInterval(this.decrementCountdowns, 1000);
  },
  beforeUnmount() {
    clearInterval(this.tick);
  },
  methods: {
    formatArs,
    fetchAuctions() {
      // The API orders by ends_at, so the first ones are the ones closing next.
      // A failure here just means the landing renders without the auction blocks.
      BinderService.getAuctions({ status: 'open' })
        .then(r => { this.auctions = r.data.slice(0, 5); })
        .catch(() => { this.auctions = []; });
    },
    decrementCountdowns() {
      this.auctions.forEach(a => {
        if (a.seconds_left > 0) a.seconds_left -= 1;
      });
    },
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
.landing { overflow-x: hidden; background: #0d0e17; }

/* ══ HERO ══
   Deliberately not 100vh: the fold has to reach the auctions below. */
.hero {
  position: relative;
  padding: 72px 0 80px;
  overflow: hidden;
  background:
    radial-gradient(ellipse 80% 60% at 15% 0%, rgba(232,160,32,0.13), transparent 60%),
    radial-gradient(ellipse 70% 60% at 90% 20%, rgba(76,29,149,0.30), transparent 65%),
    linear-gradient(180deg, #12132033 0%, #0d0e17 100%),
    #0d0e17;
}

.hero-glow {
  position: absolute;
  top: -180px; left: 50%;
  width: 900px; height: 460px;
  transform: translateX(-50%);
  background: radial-gradient(circle, rgba(232,160,32,0.16), transparent 70%);
  filter: blur(50px);
  pointer-events: none;
}

/* Faint grid — gives the flat background some texture without a hosted image. */
.hero-grid-lines {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 70% 70% at 50% 30%, #000 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse 70% 70% at 50% 30%, #000 30%, transparent 75%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr;
  gap: 44px;
  align-items: center;
}
.hero.has-feature .hero-content { grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr); }

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
  margin-bottom: 18px;
}

.hero-title {
  font-size: clamp(38px, 5vw, 60px);
  font-weight: 900;
  line-height: 1.05;
  color: #fff;
  margin-bottom: 16px;
  letter-spacing: -0.03em;
}

.gradient-text {
  background: linear-gradient(90deg, #ffd700 0%, #e8a020 40%, #ff6b35 80%, #e8a020 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shine 5s linear infinite;
}
@keyframes shine { to { background-position: 200% center; } }

.hero-subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.62);
  line-height: 1.65;
  margin-bottom: 26px;
  max-width: 480px;
}

.hero-search-wrap {
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 12px;
  padding: 5px 5px 5px 14px;
  max-width: 520px;
  margin-bottom: 20px;
  backdrop-filter: blur(12px);
  transition: border-color 0.2s;
}
.hero-search-wrap:focus-within { border-color: var(--accent); }

.search-icon { width: 16px; height: 16px; color: rgba(255,255,255,0.35); flex-shrink: 0; }

.hero-search-wrap input {
  flex: 1; min-width: 0;
  background: transparent; border: none;
  color: #fff; font-size: 14px; font-family: inherit;
  outline: none; padding: 11px 10px;
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

.hero-ctas { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.btn-cta-gold {
  background: linear-gradient(135deg, #e8a020, #f0b840);
  color: #0d0e17; border: none; border-radius: 10px;
  padding: 12px 26px; font-size: 15px; font-weight: 700;
  cursor: pointer; font-family: inherit;
  box-shadow: 0 6px 24px rgba(232,160,32,0.28);
  transition: transform 0.15s, box-shadow 0.15s;
}
.btn-cta-gold:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(232,160,32,0.44); }

.btn-cta-ghost {
  background: transparent;
  color: rgba(255,255,255,0.78);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px; padding: 12px 22px;
  font-size: 15px; cursor: pointer; font-family: inherit;
  transition: background-color 0.15s, color 0.15s, border-color 0.15s;
}
.btn-cta-ghost:hover { background: rgba(255,255,255,0.07); color: #fff; border-color: rgba(255,255,255,0.4); }

.btn-cta-plain {
  background: none; border: none;
  color: rgba(255,255,255,0.5);
  font-size: 14px; font-family: inherit; cursor: pointer;
  padding: 12px 8px;
  transition: color 0.15s;
}
.btn-cta-plain:hover { color: #fff; }

/* ── Featured auction ── */
.hero-feature { min-width: 0; }

.feature-card {
  display: block;
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(232,160,32,0.24);
  border-radius: 18px;
  padding: 16px;
  color: inherit;
  backdrop-filter: blur(10px);
  box-shadow: 0 18px 48px rgba(0,0,0,0.34);
  transition: border-color 0.18s, transform 0.18s;
}
.feature-card:hover { border-color: rgba(232,160,32,0.55); transform: translateY(-3px); color: inherit; }

.feature-head {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; margin-bottom: 14px;
}

.feature-eyebrow {
  display: inline-flex; align-items: center; gap: 7px;
  font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: rgba(255,255,255,0.62);
}

.live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 0 0 rgba(74,222,128,0.6);
  animation: livePulse 2s ease-out infinite;
}
.live-dot.scheduled { background: var(--accent); animation: none; }
@keyframes livePulse {
  70%  { box-shadow: 0 0 0 7px rgba(74,222,128,0); }
  100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); }
}

.feature-timer {
  font-size: 12px; font-weight: 700;
  padding: 4px 10px; border-radius: 999px;
  background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.8);
  white-space: nowrap;
}
.feature-timer.urgent { background: rgba(201,64,64,0.22); color: #ff9c9c; }
.feature-timer.critical { background: #c94040; color: #fff; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: 0.62; } }

.feature-body { display: flex; gap: 16px; align-items: stretch; }

.feature-img {
  width: 132px; flex-shrink: 0;
  border-radius: 10px; display: block;
  box-shadow: 0 8px 22px rgba(0,0,0,0.4);
}

.feature-info { display: flex; flex-direction: column; min-width: 0; }

.feature-title {
  font-size: 18px; font-weight: 800; color: #fff;
  line-height: 1.2; letter-spacing: -0.01em;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.feature-meta { font-size: 11px; color: rgba(255,255,255,0.42); margin: 4px 0 14px; }

.feature-price-label {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em;
  color: rgba(255,255,255,0.42);
}
.feature-price {
  font-size: 28px; font-weight: 900; color: var(--accent);
  letter-spacing: -0.02em; line-height: 1.1;
}
.feature-bids { font-size: 11px; color: rgba(255,255,255,0.5); }

.feature-cta {
  margin-top: auto; padding-top: 14px;
  font-size: 13px; font-weight: 700; color: var(--accent);
}

/* ══ SUBASTAS ACTIVAS ══ */
.auctions-strip {
  padding: 56px 0 64px;
  border-top: 1px solid rgba(255,255,255,0.07);
  background: linear-gradient(180deg, #0f101c, #0d0e17);
}

.strip-head {
  display: flex; justify-content: space-between; align-items: flex-end;
  gap: 16px; flex-wrap: wrap; margin-bottom: 24px;
}
.see-all { font-size: 14px; font-weight: 600; color: var(--accent); white-space: nowrap; }

.strip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(235px, 1fr));
  gap: 16px;
}

/* ══ SHARED SECTION HEADINGS ══ */
.eyebrow {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.14em; color: var(--accent); margin-bottom: 10px;
}

.section-h {
  font-size: clamp(26px, 4vw, 40px); font-weight: 800;
  color: #fff; line-height: 1.15;
  margin-bottom: 48px; letter-spacing: -0.02em;
}
.section-h.tight { margin-bottom: 0; }

/* ══ FEATURES ══ */
.features { padding: 88px 0; background: #0d0e17; }

.feat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 18px;
}

.feat-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 26px; position: relative;
  transition: border-color 0.2s, transform 0.2s;
}
.feat-card:hover { border-color: rgba(232,160,32,0.35); transform: translateY(-4px); }
.feat-card.gold { border-color: rgba(232,160,32,0.25); background: linear-gradient(135deg, rgba(232,160,32,0.07), rgba(255,255,255,0.03)); }

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
.feat-icon.purple { background: rgba(124,58,237,0.18); }

.feat-card h3 { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 8px; }
.feat-card p  { font-size: 13px; color: rgba(255,255,255,0.55); line-height: 1.6; }

/* ══ STEPS ══ */
.steps-section { padding: 88px 0; background: linear-gradient(180deg, #0d0e17, #111220); }

.steps-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: start;
}

.step-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
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
.step-card h3 { font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 8px; }
.step-card p  { font-size: 13px; color: rgba(255,255,255,0.55); line-height: 1.6; }

.step-arrow {
  display: flex; align-items: center; justify-content: center;
  padding: 0 12px; margin-top: 58px;
  font-size: 22px; color: rgba(232,160,32,0.3);
}

/* ══ CTA ══ */
.cta-section { padding: 72px 0 88px; background: #0d0e17; }

.cta-box {
  position: relative;
  background: linear-gradient(135deg, rgba(232,160,32,0.08) 0%, rgba(76,29,149,0.12) 100%);
  border: 1px solid rgba(232,160,32,0.2);
  border-radius: 24px; padding: 56px;
  overflow: hidden;
}

.cta-body { position: relative; z-index: 2; max-width: 540px; }
.cta-body h2 { font-size: clamp(24px,4vw,36px); font-weight: 800; color: #fff; margin-bottom: 12px; letter-spacing: -0.02em; }
.cta-body p  { font-size: 15px; color: rgba(255,255,255,0.6); line-height: 1.7; margin-bottom: 26px; }

.cta-btns { display: flex; gap: 12px; flex-wrap: wrap; }

/* ══ RESPONSIVE ══ */
@media (max-width: 940px) {
  .hero { padding: 52px 0 60px; }
  .hero.has-feature .hero-content { grid-template-columns: 1fr; }
  .hero-subtitle { max-width: none; }
  .feature-card { max-width: 460px; }
  .steps-grid { grid-template-columns: 1fr; gap: 14px; }
  .step-arrow { display: none; }
  .cta-box { padding: 36px 24px; }
}

@media (max-width: 560px) {
  .hero-ctas { gap: 8px; }
  .hero-ctas > * { flex: 1 1 auto; }
  .hero-ctas button { width: 100%; }
  .feature-body { gap: 12px; }
  .feature-img { width: 104px; }
  .feature-price { font-size: 24px; }
  .strip-grid { grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)); gap: 12px; }
}

/* Perpetual motion is decorative here — respect the OS preference. */
@media (prefers-reduced-motion: reduce) {
  .gradient-text, .live-dot, .feature-timer.critical { animation: none; }
  .feat-card:hover, .feature-card:hover, .btn-cta-gold:hover { transform: none; }
}
</style>
