<template>
  <div class="cart-page container">
    <div class="page-header">
      <div class="tabs">
        <button :class="['tab', { active: view === 'buying' }]" @click="view = 'buying'">
          Comprando ({{ carts.length }})
        </button>
        <button :class="['tab', { active: view === 'selling' }]" @click="switchToSelling">
          Ventas ({{ sellingCarts.length }})
        </button>
      </div>
    </div>

    <div v-if="loading" class="state-msg">Cargando...</div>

    <!-- Buying view -->
    <template v-else-if="view === 'buying'">
      <div v-if="carts.length === 0" class="empty-state">
        <div class="empty-icon">🛒</div>
        <p>No tenés carritos activos.</p>
        <router-link to="/"><button class="btn-primary">Explorar binders</button></router-link>
      </div>

      <div v-else class="carts-list">
        <div v-for="cart in carts" :key="cart.id" class="cart-card">
          <div class="cart-header">
            <div class="cart-seller-info">
              <div class="seller-avatar">{{ cart.seller[0].toUpperCase() }}</div>
              <div>
                <div class="seller-name">{{ cart.seller }}</div>
                <div class="item-count">{{ cart.item_count }} {{ cart.item_count === 1 ? 'carta' : 'cartas' }}</div>
              </div>
            </div>
            <div class="cart-header-right">
              <div class="cart-total">${{ cart.total_usd.toFixed(2) }}</div>
              <template v-if="cart.order">
                <span :class="['status-badge', cart.order.status]">{{ cart.order.status_display }}</span>
                <router-link :to="{ name: 'OrderChat', params: { cartId: cart.id } }">
                  <button class="btn-primary btn-sm">💬 Chat</button>
                </router-link>
              </template>
              <button v-else class="btn-primary btn-sm" @click="openCheckout(cart)">
                Checkout →
              </button>
            </div>
          </div>

          <div class="cart-items">
            <div v-for="item in cart.items" :key="item.id" class="cart-item">
              <img v-if="item.card.image_uri" :src="item.card.image_uri" :alt="item.card.name" class="item-img" />
              <div class="item-info">
                <div class="item-name">{{ item.card.name }}</div>
                <div class="item-set">{{ item.card.set_name }}</div>
                <div class="item-price" v-if="item.card.price_usd">${{ item.card.price_usd }}</div>
              </div>
              <div class="item-qty">x{{ item.quantity }}</div>
              <button v-if="!cart.order" class="remove-item-btn" @click="removeItem(cart, item)">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Selling view -->
    <template v-else>
      <div v-if="sellingCarts.length === 0" class="empty-state">
        <div class="empty-icon">📦</div>
        <p>Nadie te hizo pedidos todavía.</p>
      </div>

      <div v-else class="carts-list">
        <div v-for="cart in sellingCarts" :key="cart.id" class="cart-card">
          <div class="cart-header">
            <div class="cart-seller-info">
              <div class="seller-avatar buyer">{{ cart.buyer[0].toUpperCase() }}</div>
              <div>
                <div class="seller-name">{{ cart.buyer }}</div>
                <div class="item-count">quiere {{ cart.item_count }} {{ cart.item_count === 1 ? 'carta' : 'cartas' }}</div>
              </div>
            </div>
            <div class="cart-header-right">
              <div class="cart-total">${{ cart.total_usd.toFixed(2) }}</div>
              <template v-if="cart.order">
                <span :class="['status-badge', cart.order.status]">{{ cart.order.status_display }}</span>
                <router-link :to="{ name: 'OrderChat', params: { cartId: cart.id } }">
                  <button class="btn-primary btn-sm">💬 Chat</button>
                </router-link>
              </template>
              <span v-else class="status-badge pending">Esperando checkout</span>
            </div>
          </div>

          <div class="cart-items">
            <div v-for="item in cart.items" :key="item.id" class="cart-item">
              <img v-if="item.card.image_uri" :src="item.card.image_uri" :alt="item.card.name" class="item-img" />
              <div class="item-info">
                <div class="item-name">{{ item.card.name }}</div>
                <div class="item-price" v-if="item.card.price_usd">${{ item.card.price_usd }}</div>
              </div>
              <div class="item-qty">x{{ item.quantity }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Checkout modal -->
    <div v-if="checkoutCart" class="modal-overlay" @click.self="checkoutCart = null">
      <div class="modal">
        <h3>Confirmar pedido</h3>

        <div class="checkout-summary">
          <div class="checkout-items">
            <div class="checkout-item" v-for="item in checkoutCart.items" :key="item.id">
              <img v-if="item.card.image_uri" :src="item.card.image_uri" :alt="item.card.name" class="checkout-item-img" />
              <div class="checkout-item-info">
                <div class="checkout-item-name">{{ item.card.name }}</div>
                <div class="checkout-item-set">{{ item.card.set_name }}</div>
                <div class="checkout-item-price" v-if="item.card.price_usd">
                  ${{ item.card.price_usd }} × {{ item.quantity }}
                  <span class="checkout-item-sub"> = ${{ ((item.card.price_usd || 0) * item.quantity).toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-row total">
            <span>Subtotal cartas</span>
            <strong>${{ checkoutCart.total_usd.toFixed(2) }}</strong>
          </div>
        </div>

        <div class="form-group">
          <label>Método de envío</label>
          <div class="shipping-options">
            <label class="shipping-option" :class="{ active: checkoutForm.shipping_method === 'door_to_door' }">
              <input type="radio" v-model="checkoutForm.shipping_method" value="door_to_door" />
              <div class="shipping-info">
                <span class="shipping-name">🚚 Puerta a puerta</span>
                <span class="shipping-desc">El vendedor envía a tu domicilio</span>
              </div>
            </label>
            <label class="shipping-option" :class="{ active: checkoutForm.shipping_method === 'branch_pickup' }">
              <input type="radio" v-model="checkoutForm.shipping_method" value="branch_pickup" />
              <div class="shipping-info">
                <span class="shipping-name">🏪 Retiro en sucursal</span>
                <span class="shipping-desc">Coordinan punto de retiro o correo</span>
              </div>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>Notas al vendedor (opcional)</label>
          <textarea v-model="checkoutForm.notes" placeholder="Dirección, horarios, consultas..." rows="3" />
        </div>

        <div class="trust-notice">
          ⚠️ Esta plataforma es de confianza mutua. Al confirmar acordás pagar las cartas más el envío al vendedor según lo coordinado en el chat.
        </div>

        <div v-if="checkoutError" class="error-msg">{{ checkoutError }}</div>
        <div v-if="unavailableCards.length" class="unavailable-cards">
          <div class="unavailable-title">Cartas que ya no están disponibles:</div>
          <ul>
            <li v-for="card in unavailableCards" :key="card.id">{{ card.name }}</li>
          </ul>
          <div class="unavailable-hint">Removelas del carrito para continuar.</div>
        </div>

        <div class="modal-actions">
          <button class="btn-ghost" @click="checkoutCart = null">Cancelar</button>
          <button class="btn-primary" @click="confirmCheckout" :disabled="!checkoutForm.shipping_method || checkingOut">
            {{ checkingOut ? 'Procesando...' : 'Confirmar y abrir chat' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'CartView',
  data() {
    return {
      view: 'buying',
      carts: [],
      sellingCarts: [],
      loading: true,
      checkoutCart: null,
      checkoutForm: { shipping_method: '', notes: '' },
      checkoutError: null,
      unavailableCards: [],
      checkingOut: false,
    };
  },
  created() {
    this.fetchCarts();
  },
  methods: {
    fetchCarts() {
      this.loading = true;
      Promise.all([
        BinderService.getCarts(),
        BinderService.getSellingCarts(),
      ]).then(([buying, selling]) => {
        this.carts = buying.data;
        this.sellingCarts = selling.data;
      }).catch(e => console.error(e))
        .finally(() => { this.loading = false; });
    },
    switchToSelling() {
      this.view = 'selling';
    },
    openCheckout(cart) {
      this.checkoutCart = cart;
      this.checkoutForm = { shipping_method: '', notes: '' };
      this.checkoutError = null;
      this.unavailableCards = [];
    },
    async confirmCheckout() {
      this.checkoutError = null;
      this.checkingOut = true;
      try {
        const res = await BinderService.checkout(this.checkoutCart.id, this.checkoutForm);
        const updated = res.data;
        const idx = this.carts.findIndex(c => c.id === updated.id);
        if (idx >= 0) this.carts[idx] = updated;
        this.checkoutCart = null;
        this.$router.push({ name: 'OrderChat', params: { cartId: updated.id } });
      } catch (e) {
        this.checkoutError = e.response?.data?.error || 'Error al procesar el checkout.';
        this.unavailableCards = e.response?.data?.unavailable_cards || [];
        if (this.unavailableCards.length) {
          await this.fetchCarts();
        }
      } finally {
        this.checkingOut = false;
      }
    },
    async removeItem(cart, item) {
      try {
        const res = await BinderService.removeFromCart(cart.id, item.card.id);
        if (res.data.deleted) {
          this.carts = this.carts.filter(c => c.id !== cart.id);
        } else {
          const idx = this.carts.findIndex(c => c.id === cart.id);
          if (idx >= 0) this.carts[idx] = res.data;
        }
      } catch (e) { console.error(e); }
    }
  }
};
</script>

<style scoped>
.cart-page { padding-top: 40px; padding-bottom: 64px; }

.page-header { margin-bottom: 28px; }

.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border-color); padding-bottom: 0; }
.tab {
  background: none; border: none; padding: 10px 18px;
  font-size: 14px; color: var(--text-secondary); cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.tab:hover { color: var(--text-primary); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

.state-msg { color: var(--text-secondary); text-align: center; padding: 48px 0; }
.empty-state { text-align: center; padding: 80px 0; color: var(--text-secondary); }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-state p { margin-bottom: 20px; font-size: 16px; }

.carts-list { display: flex; flex-direction: column; gap: 20px; }

.cart-card { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius); overflow: hidden; }

.cart-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid var(--border-color);
  background: var(--bg-elevated);
}

.cart-seller-info { display: flex; align-items: center; gap: 10px; }
.seller-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: var(--accent); color: #12131a;
  font-weight: 700; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
}
.seller-avatar.buyer { background: #2563eb; color: white; }
.seller-name { font-weight: 600; font-size: 14px; }
.item-count { color: var(--text-secondary); font-size: 12px; margin-top: 2px; }

.cart-header-right { display: flex; align-items: center; gap: 10px; }
.cart-total { color: var(--accent); font-weight: 600; font-size: 15px; }

.btn-sm { padding: 5px 12px; font-size: 12px; }

.status-badge {
  font-size: 11px; padding: 3px 10px; border-radius: 999px; font-weight: 500;
}
.status-badge.pending { background: rgba(232,160,32,0.15); color: var(--accent); }
.status-badge.shipped { background: rgba(37,99,235,0.15); color: #60a5fa; }
.status-badge.completed { background: rgba(76,175,125,0.15); color: var(--success); }
.status-badge.cancelled { background: rgba(224,85,85,0.15); color: var(--danger); }

.cart-items { padding: 12px 20px; display: flex; flex-direction: column; gap: 6px; }

.cart-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border-color); }
.cart-item:last-child { border-bottom: none; }

.item-img { width: 36px; height: 50px; object-fit: cover; border-radius: 3px; flex-shrink: 0; }
.item-info { flex: 1; min-width: 0; }
.item-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-set { font-size: 11px; color: var(--text-muted); }
.item-price { font-size: 12px; color: var(--accent); }
.item-qty { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }

.remove-item-btn {
  width: 26px; height: 26px; padding: 0; border: none; background: transparent;
  color: var(--text-muted); border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.remove-item-btn:hover { color: var(--danger); background: rgba(224,85,85,0.1); }
.remove-item-btn svg { width: 13px; height: 13px; }

/* Checkout modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.65); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 28px; width: 480px; max-width: 95vw; max-height: 90vh; overflow-y: auto; }
.modal h3 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }

.checkout-summary { background: var(--bg-elevated); border-radius: var(--radius-sm); padding: 14px 16px; margin-bottom: 20px; }

.checkout-items { display: flex; flex-direction: column; gap: 10px; margin-bottom: 4px; }
.checkout-item { display: flex; gap: 12px; align-items: flex-start; }
.checkout-item-img { width: 52px; height: 72px; object-fit: cover; border-radius: 4px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(0,0,0,0.35); }
.checkout-item-info { flex: 1; min-width: 0; padding-top: 2px; }
.checkout-item-name { font-size: 14px; font-weight: 500; line-height: 1.3; }
.checkout-item-set { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.checkout-item-price { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.checkout-item-sub { color: var(--accent); }

.summary-row { display: flex; justify-content: space-between; font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
.summary-row.total { color: var(--text-primary); margin-top: 4px; }
.summary-divider { height: 1px; background: var(--border-color); margin: 10px 0; }

.form-group { margin-bottom: 18px; }
.form-group label { display: block; color: var(--text-secondary); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }

.shipping-options { display: flex; flex-direction: column; gap: 8px; }
.shipping-option {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  background: var(--bg-elevated); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); cursor: pointer; transition: border-color 0.15s;
}
.shipping-option input { display: none; }
.shipping-option.active { border-color: var(--accent); }
.shipping-info { display: flex; flex-direction: column; gap: 2px; }
.shipping-name { font-size: 14px; font-weight: 500; }
.shipping-desc { font-size: 12px; color: var(--text-secondary); }

.trust-notice {
  background: rgba(232,160,32,0.08); border: 1px solid rgba(232,160,32,0.2);
  border-radius: var(--radius-sm); padding: 10px 14px;
  font-size: 12px; color: var(--text-secondary); margin-bottom: 16px; line-height: 1.5;
}

.error-msg { color: var(--danger); font-size: 13px; margin-bottom: 10px; }

.unavailable-cards {
  background: rgba(224,85,85,0.08); border: 1px solid rgba(224,85,85,0.25);
  border-radius: var(--radius-sm); padding: 12px 14px; margin-bottom: 12px;
}
.unavailable-title { font-size: 13px; font-weight: 600; color: var(--danger); margin-bottom: 6px; }
.unavailable-cards ul { margin: 0 0 6px 16px; padding: 0; }
.unavailable-cards li { font-size: 13px; color: var(--text-primary); margin-bottom: 2px; }
.unavailable-hint { font-size: 11px; color: var(--text-secondary); }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
