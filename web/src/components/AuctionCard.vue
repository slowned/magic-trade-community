<template>
  <router-link :to="`/subasta/${auction.id}`" class="auction-card" :class="{ dark }">
    <div class="card-img-wrapper">
      <img v-if="auction.display_image" :src="auction.display_image" :alt="auction.display_title" loading="lazy" />
      <div v-else class="img-placeholder">🃏</div>

      <span class="status-chip" :class="urgency">{{ chipLabel }}</span>
      <span v-if="auction.foil" class="foil-chip">Foil</span>
    </div>

    <div class="card-body">
      <h3 class="card-title">{{ auction.display_title }}</h3>
      <p class="card-meta">{{ auction.card.set_name }} · {{ auction.condition_display }}</p>

      <div class="price-row">
        <div>
          <span class="price-label">{{ auction.bid_count ? 'Oferta actual' : 'Precio inicial' }}</span>
          <span class="price">{{ formatArs(auction.current_price) }}</span>
        </div>
        <span class="bid-count">{{ auction.bid_count }} {{ auction.bid_count === 1 ? 'puja' : 'pujas' }}</span>
      </div>

      <div class="card-footer">
        <span v-if="auction.is_leading" class="badge leading">Vas ganando</span>
        <span v-else-if="auction.my_max_bid" class="badge outbid">Te superaron</span>
        <span v-else-if="auction.has_reserve && !auction.reserve_met" class="badge reserve">Sin alcanzar la reserva</span>
        <span v-else-if="auction.winner" class="badge won">Ganó {{ auction.winner }}</span>
        <span v-else class="badge muted">{{ auction.status_display }}</span>
      </div>
    </div>
  </router-link>
</template>

<script>
import { formatArs, formatCountdown, urgencyClass } from '@/utils/auction';

export default {
  name: 'AuctionCard',
  props: {
    auction: { type: Object, required: true },
    // The landing sits on a dark background; the auctions grid on the app's light one.
    dark: { type: Boolean, default: false },
  },
  computed: {
    isActive() {
      return ['scheduled', 'live'].includes(this.auction.status);
    },
    urgency() {
      return this.isActive ? urgencyClass(this.auction.seconds_left) : 'ended';
    },
    chipLabel() {
      const { status, seconds_left: secondsLeft } = this.auction;
      if (status === 'cancelled') return 'Cancelada';
      if (status === 'closed') return 'Cerrada';
      if (status === 'scheduled') return 'Próximamente';
      return formatCountdown(secondsLeft);
    },
  },
  methods: { formatArs },
};
</script>

<style scoped>
.auction-card {
  /* Themed through local custom properties so the same card works on the
     light app shell and on the landing's dark sections. */
  --card-bg: var(--bg-surface);
  --card-border: var(--border-color);
  --card-title: var(--text-primary);
  --card-meta: var(--text-muted);
  --card-secondary: var(--text-secondary);
  --card-elevated: var(--bg-elevated);

  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  overflow: hidden;
  color: inherit;
  display: flex;
  flex-direction: column;
  transition: border-color 0.15s, transform 0.15s;
}

.auction-card.dark {
  --card-bg: rgba(255, 255, 255, 0.03);
  --card-border: rgba(255, 255, 255, 0.10);
  --card-title: #fff;
  --card-meta: rgba(255, 255, 255, 0.42);
  --card-secondary: rgba(255, 255, 255, 0.6);
  --card-elevated: rgba(255, 255, 255, 0.06);
}

.auction-card:hover { border-color: var(--accent); transform: translateY(-3px); color: inherit; }

.card-img-wrapper {
  position: relative;
  aspect-ratio: 235 / 327;
  background: var(--card-elevated);
  display: flex; align-items: center; justify-content: center;
}
.card-img-wrapper img { width: 100%; height: 100%; object-fit: cover; display: block; }
.img-placeholder { font-size: 34px; opacity: 0.4; }

.status-chip {
  position: absolute; top: 8px; left: 8px;
  padding: 3px 9px; border-radius: 999px;
  font-size: 11px; font-weight: 700;
  background: rgba(0,0,0,0.72); color: #fff;
  backdrop-filter: blur(4px);
}
.status-chip.urgent { background: rgba(201,64,64,0.85); }
.status-chip.critical { background: #c94040; animation: pulse 1.2s ease-in-out infinite; }
.status-chip.ended { background: rgba(0,0,0,0.55); }
@keyframes pulse { 50% { opacity: 0.6; } }

.foil-chip {
  position: absolute; top: 8px; right: 8px;
  padding: 3px 9px; border-radius: 999px;
  font-size: 10px; font-weight: 700; color: #12131a;
  background: linear-gradient(120deg, #ffd700, #7ce7ff, #ff8ad4);
}

.card-body { padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.card-title {
  font-size: 14px; font-weight: 700; color: var(--card-title);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.card-meta { font-size: 11px; color: var(--card-meta); }

.price-row { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 4px; }
.price-label { display: block; font-size: 10px; color: var(--card-meta); text-transform: uppercase; letter-spacing: 0.06em; }
.price { font-size: 17px; font-weight: 800; color: var(--accent); }
.bid-count { font-size: 11px; color: var(--card-secondary); }

.card-footer { margin-top: auto; padding-top: 8px; }
.badge { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.badge.leading { background: rgba(46,143,94,0.15); color: var(--success); }
.badge.outbid { background: rgba(201,64,64,0.13); color: var(--danger); }
.badge.reserve { background: rgba(184,110,16,0.13); color: var(--accent); }
.badge.won { background: rgba(46,143,94,0.15); color: var(--success); }
.badge.muted { background: var(--card-elevated); color: var(--card-secondary); }
</style>
