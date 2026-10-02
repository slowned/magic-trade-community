<template>
  <div class="auction-detail container">
    <div v-if="loading" class="state-msg">Cargando subasta...</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <template v-else-if="auction">
      <router-link to="/subastas" class="back-link">← Volver a subastas</router-link>

      <div class="detail-grid">
        <!-- ── Card art ── -->
        <div class="art-col">
          <img
            v-if="auction.display_image"
            :src="auction.display_image"
            :alt="auction.display_title"
            class="card-art"
          />
          <div v-else class="art-placeholder">🃏</div>

          <a
            v-if="auction.card.scryfall_uri"
            :href="auction.card.scryfall_uri"
            target="_blank"
            rel="noopener"
            class="scryfall-link"
          >Ver en Scryfall ↗</a>
        </div>

        <!-- ── Bidding panel ── -->
        <div class="info-col">
          <div class="title-row">
            <h1>{{ auction.display_title }}</h1>
            <span class="status-chip" :class="urgency">{{ chipLabel }}</span>
          </div>

          <p class="meta-line">
            {{ auction.card.set_name }}
            <span v-if="auction.card.set_code">({{ auction.card.set_code.toUpperCase() }})</span>
            · {{ auction.condition_display }}
            <span v-if="auction.foil"> · Foil</span>
            <span v-if="auction.etched"> · Etched</span>
          </p>

          <p v-if="auction.description" class="description">{{ auction.description }}</p>

          <div class="price-box">
            <div class="price-main">
              <span class="label">{{ auction.bid_count ? 'Oferta actual' : 'Precio inicial' }}</span>
              <span class="amount">{{ formatArs(auction.current_price) }}</span>
              <span class="bid-count">
                {{ auction.bid_count }} {{ auction.bid_count === 1 ? 'puja' : 'pujas' }}
                <template v-if="auction.current_leader"> · va ganando {{ auction.current_leader }}</template>
              </span>
            </div>

            <div v-if="auction.card.price_usd" class="price-ref">
              Referencia Scryfall: USD {{ auction.card.price_usd }}
            </div>

            <div v-if="auction.has_reserve" class="reserve-note" :class="{ met: auction.reserve_met }">
              {{ auction.reserve_met ? '✓ Reserva alcanzada' : 'Reserva no alcanzada' }}
              <span v-if="auction.reserve_price"> ({{ formatArs(auction.reserve_price) }})</span>
            </div>
          </div>

          <div class="timing">
            <div><span class="label">Abre</span> {{ formatDateTime(auction.starts_at) }}</div>
            <div><span class="label">Cierra</span> {{ formatDateTime(auction.ends_at) }}</div>
          </div>

          <!-- Your status -->
          <div v-if="auction.is_leading" class="banner success">
            Sos el mejor postor. Tu máximo es {{ formatArs(auction.my_max_bid) }}.
          </div>
          <div v-else-if="auction.my_max_bid" class="banner danger">
            Te superaron. Tu máximo era {{ formatArs(auction.my_max_bid) }}.
          </div>

          <!-- ── Bid form ── -->
          <form v-if="canBid" class="bid-form" @submit.prevent="submitBid">
            <label for="max-amount">
              Tu oferta máxima
              <span class="hint">Pujamos por vos solo lo necesario para ir ganando.</span>
            </label>
            <div class="bid-row">
              <input
                id="max-amount"
                v-model="bidAmount"
                type="number"
                :min="auction.min_next_bid"
                step="1"
                :placeholder="`Mínimo ${auction.min_next_bid}`"
                required
              />
              <button class="btn-primary" type="submit" :disabled="bidding">
                {{ bidding ? 'Ofertando...' : 'Ofertar' }}
              </button>
            </div>
            <p class="increment-note">
              Puja mínima {{ formatArs(auction.min_next_bid) }} · incremento {{ formatArs(auction.min_increment) }}
            </p>
            <p v-if="bidError" class="form-error">{{ bidError }}</p>
          </form>

          <div v-else-if="!isAuthenticated" class="banner muted">
            <router-link to="/login">Iniciá sesión</router-link> para participar.
          </div>
          <div v-else-if="isOwnAuction" class="banner muted">Es tu subasta, no podés pujar.</div>
          <div v-else-if="auction.status === 'scheduled'" class="banner muted">
            Todavía no arrancó. Abre el {{ formatDateTime(auction.starts_at) }}.
          </div>

          <!-- ── Closed outcome ── -->
          <div v-if="auction.status === 'closed'" class="outcome">
            <template v-if="auction.winner">
              <p class="outcome-title">
                Ganó <strong>{{ auction.winner }}</strong> por {{ formatArs(auction.winning_amount) }}
              </p>
              <router-link v-if="isWinner && auction.cart_id" :to="`/cart/${auction.cart_id}`">
                <button class="btn-primary">Ir a coordinar pago y envío →</button>
              </router-link>
            </template>
            <p v-else class="outcome-title muted">Cerró sin ganador.</p>
          </div>

          <!-- ── Staff controls ── -->
          <div v-if="isStaff && isActive" class="staff-box">
            <span class="staff-label">Panel de plataforma</span>
            <div class="staff-actions">
              <button class="btn-ghost" @click="doClose" :disabled="acting">Cerrar ya</button>
              <button class="btn-ghost danger" @click="doCancel" :disabled="acting">Cancelar subasta</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Bid history ── -->
      <section class="history">
        <h2>Historial de pujas</h2>
        <p v-if="bids.length === 0" class="state-msg">Todavía no hay pujas. Estrenala vos.</p>
        <table v-else class="bid-table">
          <thead>
            <tr><th>Postor</th><th>Precio</th><th>Cuándo</th></tr>
          </thead>
          <tbody>
            <tr v-for="bid in bids" :key="bid.id" :class="{ leader: bid.became_leader }">
              <td>{{ bid.bidder }}</td>
              <td class="amount-cell">{{ formatArs(bid.price_after) }}</td>
              <td class="when-cell">{{ formatDateTime(bid.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import BinderService from '@/services/BinderService';
import { formatArs, formatCountdown, formatDateTime, urgencyClass } from '@/utils/auction';

export default {
  name: 'AuctionDetailView',
  props: { id: { type: String, required: true } },
  data() {
    return {
      auction: null,
      bids: [],
      loading: true,
      error: null,
      bidAmount: '',
      bidding: false,
      bidError: null,
      acting: false,
      tick: null,
      refresh: null,
    };
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser']),
    isStaff() {
      return !!this.currentUser?.is_staff;
    },
    isOwnAuction() {
      return this.auction?.seller === this.currentUser?.username;
    },
    isWinner() {
      return this.auction?.winner === this.currentUser?.username;
    },
    isActive() {
      return ['scheduled', 'live'].includes(this.auction?.status);
    },
    canBid() {
      return this.isAuthenticated && this.auction?.is_open && !this.isOwnAuction;
    },
    urgency() {
      if (!this.isActive) return 'ended';
      return urgencyClass(this.auction.seconds_left);
    },
    chipLabel() {
      const { status, seconds_left: secondsLeft } = this.auction;
      if (status === 'cancelled') return 'Cancelada';
      if (status === 'closed') return 'Cerrada';
      if (status === 'scheduled') return 'Próximamente';
      return `Cierra en ${formatCountdown(secondsLeft)}`;
    },
  },
  created() {
    this.fetchAll();
    this.tick = setInterval(() => {
      if (this.auction?.seconds_left > 0) this.auction.seconds_left -= 1;
    }, 1000);
    // Someone else's bid should show up without a manual reload.
    this.refresh = setInterval(this.fetchAll, 15000);
  },
  beforeUnmount() {
    clearInterval(this.tick);
    clearInterval(this.refresh);
  },
  methods: {
    formatArs,
    formatDateTime,
    fetchAll() {
      return Promise.all([
        BinderService.getAuction(this.id),
        BinderService.getAuctionBids(this.id),
      ])
        .then(([auctionRes, bidsRes]) => {
          this.auction = auctionRes.data;
          this.bids = bidsRes.data;
          this.error = null;
        })
        .catch(() => { this.error = 'No pudimos cargar esta subasta.'; })
        .finally(() => { this.loading = false; });
    },
    async submitBid() {
      this.bidError = null;
      this.bidding = true;
      try {
        const response = await BinderService.placeBid(this.id, this.bidAmount);
        this.auction = response.data;
        this.bidAmount = '';
        const bids = await BinderService.getAuctionBids(this.id);
        this.bids = bids.data;
      } catch (e) {
        this.bidError = e.response?.data?.error || 'No pudimos registrar tu puja.';
      } finally {
        this.bidding = false;
      }
    },
    async doClose() {
      if (!confirm('¿Cerrar la subasta ahora, con el precio actual?')) return;
      this.acting = true;
      try {
        const response = await BinderService.closeAuction(this.id);
        this.auction = response.data;
      } finally {
        this.acting = false;
      }
    },
    async doCancel() {
      if (!confirm('¿Cancelar la subasta? No se le adjudica a nadie.')) return;
      this.acting = true;
      try {
        const response = await BinderService.cancelAuction(this.id);
        this.auction = response.data;
      } finally {
        this.acting = false;
      }
    },
  },
};
</script>

<style scoped>
.auction-detail { padding: 24px 24px 64px; }

.back-link { display: inline-block; font-size: 13px; margin-bottom: 18px; }

.state-msg { padding: 48px 0; text-align: center; color: var(--text-secondary); }
.state-msg.error { color: var(--danger); }

.detail-grid { display: grid; grid-template-columns: 320px 1fr; gap: 36px; align-items: start; }

.art-col { position: sticky; top: 24px; }
.card-art { width: 100%; border-radius: 14px; display: block; box-shadow: 0 10px 30px rgba(0,0,0,0.14); }
.art-placeholder {
  aspect-ratio: 488 / 680; display: flex; align-items: center; justify-content: center;
  background: var(--bg-elevated); border-radius: 14px; font-size: 44px; opacity: 0.4;
}
.scryfall-link { display: block; margin-top: 10px; font-size: 12px; text-align: center; }

.title-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }

.status-chip { padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 700; background: var(--bg-elevated); color: var(--text-secondary); }
.status-chip.urgent { background: rgba(201,64,64,0.14); color: var(--danger); }
.status-chip.critical { background: var(--danger); color: #fff; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: 0.6; } }

.meta-line { font-size: 13px; color: var(--text-secondary); margin-top: 6px; }
.description { font-size: 14px; color: var(--text-secondary); margin-top: 14px; line-height: 1.6; white-space: pre-line; }

.price-box {
  margin-top: 20px; padding: 18px 20px;
  background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 12px;
}
.price-main .label { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-muted); }
.price-main .amount { display: block; font-size: 32px; font-weight: 800; color: var(--accent); letter-spacing: -0.02em; }
.price-main .bid-count { font-size: 12px; color: var(--text-secondary); }
.price-ref { margin-top: 8px; font-size: 12px; color: var(--text-muted); }
.reserve-note { margin-top: 8px; font-size: 12px; font-weight: 600; color: var(--danger); }
.reserve-note.met { color: var(--success); }

.timing { display: flex; gap: 24px; margin-top: 14px; font-size: 13px; flex-wrap: wrap; }
.timing .label { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-muted); }

.banner { margin-top: 16px; padding: 11px 14px; border-radius: 8px; font-size: 13px; }
.banner.success { background: rgba(46,143,94,0.12); color: var(--success); }
.banner.danger { background: rgba(201,64,64,0.12); color: var(--danger); }
.banner.muted { background: var(--bg-elevated); color: var(--text-secondary); }

.bid-form { margin-top: 20px; }
.bid-form label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.hint { display: block; font-weight: 400; font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.bid-row { display: flex; gap: 10px; }
.bid-row input {
  flex: 1; padding: 11px 14px; font-size: 15px; font-family: inherit;
  border: 1px solid var(--border-color); border-radius: var(--radius);
  background: var(--bg-surface); color: var(--text-primary);
}
.bid-row input:focus { outline: none; border-color: var(--accent); }
.bid-row button { padding: 11px 26px; font-weight: 700; }
.increment-note { margin-top: 8px; font-size: 12px; color: var(--text-muted); }
.form-error { margin-top: 8px; font-size: 13px; color: var(--danger); }

.outcome { margin-top: 20px; padding: 18px 20px; background: var(--bg-elevated); border-radius: 12px; }
.outcome-title { font-size: 15px; margin-bottom: 12px; }
.outcome-title.muted { color: var(--text-secondary); margin-bottom: 0; }

.staff-box { margin-top: 24px; padding: 14px 16px; border: 1px dashed var(--border-color); border-radius: 10px; }
.staff-label { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: 10px; }
.staff-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-ghost.danger { color: var(--danger); border-color: rgba(201,64,64,0.4); }

.history { margin-top: 48px; }
.history h2 { font-size: 18px; font-weight: 700; margin-bottom: 14px; }
.bid-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.bid-table th {
  text-align: left; padding: 8px 12px; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--text-muted); border-bottom: 1px solid var(--border-color);
}
.bid-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-color); }
.bid-table tr.leader td { font-weight: 600; }
.amount-cell { color: var(--accent); font-weight: 700; }
.when-cell { color: var(--text-secondary); }

@media (max-width: 820px) {
  .detail-grid { grid-template-columns: 1fr; gap: 24px; }
  .art-col { position: static; max-width: 260px; margin: 0 auto; }
}
</style>
