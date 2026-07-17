<template>
  <div class="order-chat container">

    <div v-if="loading" class="state-msg">Cargando...</div>

    <template v-else-if="cart">
      <!-- Header -->
      <div class="chat-header">
        <router-link to="/cart" class="back-link">← Mis carritos</router-link>
        <div class="order-info">
          <div class="order-title">
            Pedido con
            <router-link :to="`/user/${isBuyer ? cart.seller : cart.buyer}`" class="highlight">
              {{ isBuyer ? cart.seller : cart.buyer }}
            </router-link>
          </div>
          <div class="order-meta">
            <span :class="['status-badge', cart.order.status]">{{ cart.order.status_display }}</span>
            <span class="shipping-badge">{{ cart.order.shipping_method_display }}</span>
            <span class="order-total">${{ cart.total_usd.toFixed(2) }}</span>
          </div>
        </div>

        <!-- Status actions -->
        <div class="order-actions">
          <button
            v-if="isSeller && cart.order.status === 'pending'"
            class="btn-primary btn-sm"
            @click="updateStatus('shipped')"
          >Marcar como enviado</button>
          <button
            v-if="isBuyer && cart.order.status === 'shipped'"
            class="btn-primary btn-sm"
            @click="updateStatus('completed')"
          >Confirmar recepción</button>
          <!-- Upload payment proof -->
          <label
            v-if="isBuyer && ['pending','shipped'].includes(cart.order.status)"
            class="btn-ghost btn-sm upload-label"
            :class="{ uploading }"
          >
            {{ uploading ? 'Subiendo...' : cart.order.payment_proof_url ? '✓ Comprobante enviado' : '📎 Subir comprobante' }}
            <input type="file" accept="image/*,application/pdf" @change="uploadProof" style="display:none" :disabled="uploading" />
          </label>
          <button
            v-if="isBuyer && cart.order.status === 'pending'"
            class="btn-ghost btn-sm danger"
            @click="updateStatus('cancelled')"
          >Cancelar pedido</button>
        </div>
      </div>

      <!-- Rating form: buyer rates the seller once the order is completed -->
      <div v-if="isBuyer && cart.order.status === 'completed' && !cart.order.rating" class="rating-panel">
        <div class="rating-title">
          ¿Cómo fue tu experiencia con <span class="highlight">{{ cart.seller }}</span>?
        </div>
        <p class="rating-sub">Puntuá su confiabilidad de 0 a 10. La puntuación se muestra en su perfil público.</p>
        <div class="score-row">
          <button
            v-for="n in 11"
            :key="n - 1"
            :class="['score-btn', { selected: ratingScore === n - 1 }]"
            @click="ratingScore = n - 1"
          >{{ n - 1 }}</button>
        </div>
        <textarea
          v-model="ratingComment"
          class="rating-comment-input"
          placeholder="Comentario (opcional)"
          rows="2"
        ></textarea>
        <div class="rating-actions">
          <span v-if="ratingError" class="rating-error">{{ ratingError }}</span>
          <button
            class="btn-primary btn-sm"
            :disabled="ratingScore === null || submittingRating"
            @click="submitRating"
          >{{ submittingRating ? 'Enviando...' : 'Enviar puntuación' }}</button>
        </div>
      </div>

      <!-- Existing rating -->
      <div v-else-if="cart.order.rating" class="rating-panel rated">
        <div class="rating-title">
          {{ isBuyer ? 'Tu puntuación para' : 'Puntuación de este pedido para' }}
          <span class="highlight">{{ cart.seller }}</span>
          <span class="rating-score-badge">{{ cart.order.rating.score }}/10</span>
        </div>
        <p v-if="cart.order.rating.comment" class="rating-comment-display">“{{ cart.order.rating.comment }}”</p>
      </div>

      <div class="chat-layout">
        <!-- Sidebar: order items -->
        <div class="order-sidebar">

          <!-- Status timeline -->
          <div class="status-timeline">
            <h4>Estado del pedido</h4>
            <div class="timeline">
              <div :class="['timeline-step', { done: true }]">
                <div class="timeline-dot"></div>
                <div class="timeline-body">
                  <div class="timeline-label">Pedido confirmado</div>
                  <div class="timeline-sub">{{ formatDate(cart.order.created_at) }}</div>
                </div>
              </div>
              <div :class="['timeline-step', { done: !!cart.order.payment_proof_url }]">
                <div class="timeline-dot"></div>
                <div class="timeline-body">
                  <div class="timeline-label">Comprobante de pago</div>
                  <div class="timeline-sub" v-if="cart.order.payment_proof_url">
                    <a :href="cart.order.payment_proof_url" target="_blank" class="proof-link-inline">
                      <span v-if="isImage(cart.order.payment_proof_url)">
                        <img :src="cart.order.payment_proof_url" alt="Comprobante" class="proof-img-sm" />
                      </span>
                      <span v-else>📄 Ver comprobante</span>
                    </a>
                  </div>
                  <div class="timeline-sub muted" v-else>Pendiente de envío</div>
                </div>
              </div>
              <div :class="['timeline-step', { done: ['shipped','completed'].includes(cart.order.status) }]">
                <div class="timeline-dot"></div>
                <div class="timeline-body">
                  <div class="timeline-label">Enviado</div>
                  <div class="timeline-sub muted" v-if="!['shipped','completed'].includes(cart.order.status)">Pendiente</div>
                  <div class="timeline-sub" v-else>{{ cart.order.shipping_method_display }}</div>
                </div>
              </div>
              <div :class="['timeline-step', { done: cart.order.status === 'completed', cancelled: cart.order.status === 'cancelled' }]">
                <div class="timeline-dot"></div>
                <div class="timeline-body">
                  <div class="timeline-label" v-if="cart.order.status === 'cancelled'">Cancelado</div>
                  <div class="timeline-label" v-else>Recibido</div>
                  <div class="timeline-sub muted" v-if="!['completed','cancelled'].includes(cart.order.status)">Pendiente</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Cards -->
          <div class="sidebar-section">
            <h4>Cartas del pedido</h4>
            <div class="order-items">
              <div v-for="item in cart.items" :key="item.id" class="order-item">
                <img v-if="item.card.image_uri" :src="item.card.image_uri" :alt="item.card.name" class="order-item-img" />
                <div class="order-item-info">
                  <div class="order-item-name">{{ item.card.name }}</div>
                  <div class="order-item-set">{{ item.card.set_name }}</div>
                  <div class="order-item-price" v-if="item.card.price_usd">
                    ${{ item.card.price_usd }} × {{ item.quantity }}
                    <span class="order-item-subtotal"> = ${{ ((item.card.price_usd || 0) * item.quantity).toFixed(2) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="order-sidebar-total">
              <span>Total cartas</span>
              <strong>${{ cart.total_usd.toFixed(2) }}</strong>
            </div>
          </div>

          <div class="order-notes" v-if="cart.order.notes">
            <h5>Notas</h5>
            <p>{{ cart.order.notes }}</p>
          </div>
        </div>

        <!-- Chat -->
        <div class="chat-panel">
          <div class="messages-container" ref="messagesContainer">
            <div v-if="messages.length === 0" class="no-messages">
              Iniciá la conversación para coordinar el envío y pago.
            </div>
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['message', { mine: msg.sender === currentUsername }]"
            >
              <div class="message-bubble">
                <span class="message-content">{{ msg.content }}</span>
                <span class="message-time">{{ formatTime(msg.created_at) }}</span>
              </div>
              <div class="message-sender" v-if="msg.sender !== currentUsername">{{ msg.sender }}</div>
            </div>
          </div>

          <div class="message-input-bar">
            <input
              v-model="newMessage"
              @keyup.enter="sendMessage"
              placeholder="Escribí un mensaje..."
              :disabled="sending"
              class="message-input"
            />
            <button class="btn-primary send-btn" @click="sendMessage" :disabled="sending || !newMessage.trim()">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="state-msg">Carrito no encontrado.</div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import BinderService from '@/services/BinderService';

export default {
  name: 'OrderChat',
  computed: {
    ...mapGetters(['currentUser']),
    currentUsername() { return this.currentUser?.username; },
    isBuyer() { return this.cart?.buyer === this.currentUsername; },
    isSeller() { return this.cart?.seller === this.currentUsername; },
  },
  data() {
    return {
      cart: null,
      messages: [],
      loading: true,
      newMessage: '',
      sending: false,
      uploading: false,
      pollInterval: null,
      ratingScore: null,
      ratingComment: '',
      submittingRating: false,
      ratingError: null,
    };
  },
  created() {
    this.loadCart();
  },
  beforeUnmount() {
    clearInterval(this.pollInterval);
  },
  methods: {
    async loadCart() {
      this.loading = true;
      try {
        const cartId = this.$route.params.cartId;
        const [cartRes, msgRes] = await Promise.all([
          BinderService.getCart(cartId),
          BinderService.getMessages(cartId),
        ]);
        this.cart = cartRes.data;
        this.messages = msgRes.data;
        this.$nextTick(() => this.scrollToBottom());
        this.startPolling();
      } catch (e) {
        console.error(e);
      } finally {
        this.loading = false;
      }
    },
    startPolling() {
      this.pollInterval = setInterval(async () => {
        try {
          const res = await BinderService.getMessages(this.$route.params.cartId);
          if (res.data.length !== this.messages.length) {
            this.messages = res.data;
            this.$nextTick(() => this.scrollToBottom());
          }
        } catch (e) { /* silent */ }
      }, 4000);
    },
    async sendMessage() {
      const content = this.newMessage.trim();
      if (!content || this.sending) return;
      this.sending = true;
      try {
        const res = await BinderService.sendMessage(this.$route.params.cartId, content);
        this.messages.push(res.data);
        this.newMessage = '';
        this.$nextTick(() => this.scrollToBottom());
      } catch (e) { console.error(e); }
      finally { this.sending = false; }
    },
    async updateStatus(status) {
      try {
        const res = await BinderService.updateOrderStatus(this.$route.params.cartId, status);
        this.cart = res.data;
      } catch (e) { console.error(e); }
    },
    async submitRating() {
      if (this.ratingScore === null || this.submittingRating) return;
      this.submittingRating = true;
      this.ratingError = null;
      try {
        const res = await BinderService.rateOrder(
          this.$route.params.cartId,
          this.ratingScore,
          this.ratingComment.trim()
        );
        this.cart = res.data;
      } catch (e) {
        this.ratingError = e.response?.data?.error || 'Error al enviar la puntuación.';
      } finally {
        this.submittingRating = false;
      }
    },
    async uploadProof(e) {
      const file = e.target.files?.[0];
      if (!file) return;
      this.uploading = true;
      try {
        const res = await BinderService.uploadPaymentProof(this.$route.params.cartId, file);
        this.cart = res.data;
      } catch (e) { console.error(e); }
      finally { this.uploading = false; }
    },
    isImage(url) {
      return /\.(jpg|jpeg|png|gif|webp)$/i.test(url);
    },
    scrollToBottom() {
      const el = this.$refs.messagesContainer;
      if (el) el.scrollTop = el.scrollHeight;
    },
    formatTime(iso) {
      const d = new Date(iso);
      return d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
    },
    formatDate(iso) {
      const d = new Date(iso);
      return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    },
  }
};
</script>

<style scoped>
.order-chat { padding-top: 24px; padding-bottom: 32px; }

.state-msg { color: var(--text-secondary); text-align: center; padding: 48px 0; }

.back-link { color: var(--text-secondary); font-size: 13px; display: inline-block; margin-bottom: 12px; }
.back-link:hover { color: var(--text-primary); }

.chat-header {
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  padding-bottom: 16px; border-bottom: 1px solid var(--border-color); margin-bottom: 20px;
}

.order-info { flex: 1; }
.order-title { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
.highlight { color: var(--accent); }

.order-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.status-badge {
  font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 500;
}
.status-badge.pending { background: rgba(232,160,32,0.15); color: var(--accent); }
.status-badge.shipped { background: rgba(37,99,235,0.15); color: #60a5fa; }
.status-badge.completed { background: rgba(76,175,125,0.15); color: var(--success); }
.status-badge.cancelled { background: rgba(224,85,85,0.15); color: var(--danger); }

.shipping-badge { font-size: 12px; color: var(--text-secondary); }
.order-total { font-size: 14px; color: var(--accent); font-weight: 600; }

.order-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-sm { padding: 6px 14px; font-size: 12px; }
.btn-sm.danger { color: var(--danger); border-color: var(--danger); }
.btn-sm.danger:hover { background: rgba(224,85,85,0.1); }

/* Rating */
.rating-panel {
  background: var(--bg-surface); border: 1px solid var(--accent);
  border-radius: var(--radius); padding: 18px 20px; margin-bottom: 20px;
}
.rating-panel.rated { border-color: var(--border-color); }

.rating-title { font-size: 15px; font-weight: 600; }
.rating-sub { font-size: 12px; color: var(--text-secondary); margin-top: 4px; margin-bottom: 14px; }

.score-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.score-btn {
  width: 36px; height: 36px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-color); background: var(--bg-elevated);
  color: var(--text-primary); font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.15s;
}
.score-btn:hover { border-color: var(--accent); }
.score-btn.selected { background: var(--accent); border-color: var(--accent); color: #12131a; }

.rating-comment-input { width: 100%; resize: vertical; margin-bottom: 12px; }

.rating-actions { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.rating-error { color: var(--danger); font-size: 12px; }

.rating-score-badge {
  display: inline-block; margin-left: 8px; padding: 2px 10px; border-radius: 999px;
  background: rgba(232,160,32,0.15); color: var(--accent); font-size: 13px; font-weight: 700;
}
.rating-comment-display { font-size: 13px; color: var(--text-secondary); margin-top: 8px; font-style: italic; }

/* Layout */
.chat-layout { display: grid; grid-template-columns: 280px 1fr; gap: 20px; height: calc(100vh - 240px); min-height: 500px; }

/* Sidebar */
.order-sidebar {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); padding: 16px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 16px;
}

.order-sidebar h4 { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }

.sidebar-section { display: flex; flex-direction: column; }

/* Status timeline */
.status-timeline { border-bottom: 1px solid var(--border-color); padding-bottom: 14px; }

.timeline { display: flex; flex-direction: column; gap: 0; }

.timeline-step {
  display: flex; gap: 10px; position: relative;
  padding-bottom: 14px;
}
.timeline-step:last-child { padding-bottom: 0; }

.timeline-step::before {
  content: ''; position: absolute; left: 6px; top: 14px;
  width: 2px; height: calc(100% - 6px);
  background: var(--border-color);
}
.timeline-step:last-child::before { display: none; }

.timeline-dot {
  width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; margin-top: 1px;
  border: 2px solid var(--border-color); background: var(--bg-elevated);
  transition: all 0.2s;
}
.timeline-step.done .timeline-dot {
  background: var(--accent); border-color: var(--accent);
}
.timeline-step.done::before { background: var(--accent); opacity: 0.4; }
.timeline-step.cancelled .timeline-dot { background: var(--danger); border-color: var(--danger); }

.timeline-body { flex: 1; min-width: 0; }
.timeline-label { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.timeline-step:not(.done):not(.cancelled) .timeline-label { color: var(--text-secondary); }
.timeline-sub { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.timeline-sub.muted { color: var(--text-muted); }

.proof-link-inline { display: inline-block; }
.proof-img-sm { max-width: 100%; border-radius: 4px; border: 1px solid var(--border-color); margin-top: 4px; }

/* Cards list */
.order-items { display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px; }

.order-item { display: flex; gap: 10px; align-items: flex-start; }
.order-item-img { width: 46px; height: 64px; object-fit: cover; border-radius: 4px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(0,0,0,0.3); }
.order-item-info { min-width: 0; flex: 1; }
.order-item-name { font-size: 13px; font-weight: 500; line-height: 1.3; }
.order-item-set { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.order-item-price { font-size: 12px; color: var(--text-secondary); margin-top: 3px; }
.order-item-subtotal { color: var(--accent); }

.order-sidebar-total {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 10px; border-top: 1px solid var(--border-color);
  font-size: 13px; color: var(--text-secondary);
}
.order-sidebar-total strong { color: var(--accent); font-size: 15px; }

.order-notes h5 { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.order-notes p { font-size: 12px; color: var(--text-muted); line-height: 1.5; }

.upload-label {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.upload-label.uploading { opacity: 0.6; cursor: not-allowed; }

/* Chat panel */
.chat-panel {
  background: var(--bg-surface); border: 1px solid var(--border-color);
  border-radius: var(--radius); display: flex; flex-direction: column; overflow: hidden;
}

.messages-container { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; }

.no-messages { color: var(--text-muted); font-size: 13px; text-align: center; margin: auto; }

.message { display: flex; flex-direction: column; align-items: flex-start; }
.message.mine { align-items: flex-end; }

.message-bubble {
  max-width: 70%; background: var(--bg-elevated); border-radius: 12px 12px 12px 2px;
  padding: 8px 12px; display: flex; flex-direction: column; gap: 3px;
}
.message.mine .message-bubble { background: var(--accent); border-radius: 12px 12px 2px 12px; }

.message-content { font-size: 14px; color: var(--text-primary); line-height: 1.4; word-break: break-word; }
.message.mine .message-content { color: #12131a; }

.message-time { font-size: 10px; color: var(--text-muted); align-self: flex-end; }
.message.mine .message-time { color: rgba(18,19,26,0.6); }

.message-sender { font-size: 11px; color: var(--text-muted); margin-top: 3px; margin-left: 4px; }

.message-input-bar {
  display: flex; gap: 8px; padding: 12px 16px;
  border-top: 1px solid var(--border-color); background: var(--bg-elevated);
}

.message-input { flex: 1; height: 38px; }

.send-btn { width: 38px; height: 38px; padding: 0; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.send-btn svg { width: 16px; height: 16px; }
</style>
