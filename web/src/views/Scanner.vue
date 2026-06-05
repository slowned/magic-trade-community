<template>
  <div class="scanner-page">
    <div class="scanner-header">
      <h1 class="scanner-title">Escanear carta</h1>
      <p class="scanner-subtitle">Apuntá la cámara al nombre de la carta y tocá Escanear</p>
    </div>

    <!-- Camera -->
    <div class="camera-wrapper">
      <video ref="video" class="camera-feed" autoplay playsinline muted />
      <canvas ref="canvas" class="hidden-canvas" />

      <div class="scan-overlay">
        <div class="scan-corner tl" /><div class="scan-corner tr" />
        <div class="scan-corner bl" /><div class="scan-corner br" />
        <!-- Name zone indicator -->
        <div class="name-zone" />
      </div>

      <div v-if="!cameraActive && !cameraError" class="camera-placeholder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M12 18.75H4.5a2.25 2.25 0 01-2.25-2.25V9m12.841 9.091L16.5 19.5m-1.409-1.409c.407-.507.67-1.143.67-1.841V8.25a2.25 2.25 0 00-2.25-2.25h-5.25" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <button class="btn-primary" @click="startCamera">Activar cámara</button>
      </div>
      <div v-if="cameraError" class="camera-error">
        <p>{{ cameraError }}</p>
        <button class="btn-ghost" @click="startCamera">Reintentar</button>
      </div>
    </div>

    <!-- Scan button -->
    <button
      v-if="cameraActive && !result"
      class="btn-scan"
      :disabled="scanning"
      @click="scan"
    >
      <span v-if="scanning">{{ scanStatus }}</span>
      <span v-else>📷 Escanear</span>
    </button>

    <!-- Manual search fallback -->
    <div v-if="!result" class="manual-search">
      <p class="manual-label">O escribí el nombre directamente:</p>
      <div class="manual-row">
        <input
          v-model="manualQuery"
          @keyup.enter="searchByName(manualQuery)"
          placeholder="Ej: Lightning Bolt"
          class="manual-input"
        />
        <button class="btn-primary" :disabled="!manualQuery || searching" @click="searchByName(manualQuery)">
          {{ searching ? '...' : 'Buscar' }}
        </button>
      </div>
    </div>

    <!-- Error + "did you mean" suggestions -->
    <div v-if="searchError && !result" class="search-error-block">
      <p class="search-error-msg">{{ searchError }}</p>
      <div v-if="nameSuggestions.length">
        <p class="search-suggest-label">¿Quisiste decir?</p>
        <div class="search-suggestions">
          <button
            v-for="s in nameSuggestions"
            :key="s"
            class="suggestion-chip"
            @click="manualQuery = s; searchByName(s)"
          >{{ s }}</button>
        </div>
      </div>
    </div>

    <!-- Search results (multiple editions) -->
    <div v-if="editions.length && !result" class="editions">
      <p class="editions-label">Seleccioná la edición correcta:</p>
      <div
        v-for="card in editions"
        :key="card.id"
        class="edition-item"
        @click="selectEdition(card)"
      >
        <img v-if="card.image_uri" :src="card.image_uri" class="edition-img" />
        <div>
          <p class="edition-name">{{ card.name }}</p>
          <p class="edition-set">{{ card.set_name }} ({{ card.set_code?.toUpperCase() }})</p>
          <p v-if="card.price_usd" class="edition-price">USD {{ card.price_usd }}</p>
        </div>
      </div>
    </div>

    <!-- Selected card result -->
    <transition name="slide-up">
      <div v-if="result" class="result-card">
        <div class="result-inner">
          <img v-if="result.image_uri" :src="result.image_uri" :alt="result.name" class="result-img" />
          <div class="result-info">
            <p class="result-set">{{ result.set_name }} · {{ result.set_code?.toUpperCase() }}</p>
            <h2 class="result-name">{{ result.name }}</h2>
            <p class="result-type">{{ result.type_line }}</p>
            <div class="result-prices">
              <span v-if="result.price_usd" class="price">USD {{ result.price_usd }}</span>
              <span v-if="result.price_usd_foil" class="price foil">Foil USD {{ result.price_usd_foil }}</span>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <select v-model="selectedBinder" class="binder-select">
            <option value="" disabled>Seleccioná un binder</option>
            <option v-for="b in myBinders" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
          <button class="btn-primary" :disabled="!selectedBinder || adding" @click="addToBinder">
            {{ adding ? 'Agregando...' : 'Agregar al binder' }}
          </button>
          <button class="btn-ghost" @click="clearResult">Escanear otra</button>
        </div>

        <p v-if="addMessage" class="add-message" :class="{ error: addError }">{{ addMessage }}</p>
      </div>
    </transition>
  </div>
</template>

<script>
import BinderService from '@/services/BinderService';

export default {
  name: 'ScannerView',

  data() {
    return {
      cameraActive: false,
      cameraError: null,
      scanning: false,
      scanStatus: '',
      result: null,
      editions: [],
      myBinders: [],
      selectedBinder: '',
      adding: false,
      addMessage: '',
      addError: false,
      stream: null,
      manualQuery: '',
      searching: false,
      searchError: '',
      nameSuggestions: [],
      tesseractWorker: null,
    };
  },

  mounted() {
    this.loadMyBinders();
    this.startCamera();
  },

  beforeUnmount() {
    this.stopCamera();
    if (this.tesseractWorker) this.tesseractWorker.terminate();
  },

  methods: {
    async startCamera() {
      this.cameraError = null;
      if (!navigator.mediaDevices?.getUserMedia) {
        this.cameraError = 'La cámara requiere HTTPS. En Chrome mobile habilitá http://192.168.1.114:3000 en chrome://flags/#unsafely-treat-insecure-origin-as-secure';
        return;
      }
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 } },
        });
        this.$refs.video.srcObject = this.stream;
        this.cameraActive = true;
      } catch (err) {
        this.cameraError = err.name === 'NotAllowedError'
          ? 'Permiso de cámara denegado.'
          : `No se pudo acceder a la cámara: ${err.message}`;
      }
    },

    stopCamera() {
      if (this.stream) this.stream.getTracks().forEach(t => t.stop());
    },

    /** Load Tesseract.js from CDN on demand. */
    async loadTesseract() {
      if (window.Tesseract) return;
      return new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
      });
    },

    /**
     * Capture a frame, crop + preprocess the name area, run OCR, search Scryfall.
     *
     * Preprocessing steps applied before Tesseract:
     *  1. Crop top 20% of frame (card name area)
     *  2. Scale 3× (Tesseract reads larger text better)
     *  3. Convert to grayscale + boost contrast (makes text pop on any background)
     */
    async scan() {
      this.scanning = true;
      this.scanStatus = 'Capturando...';
      this.editions = [];
      this.cameraError = null;

      const video = this.$refs.video;
      const canvas = this.$refs.canvas;
      const w = video.videoWidth;
      const h = video.videoHeight;

      canvas.width = w;
      canvas.height = h;
      canvas.getContext('2d').drawImage(video, 0, 0);

      // Step 1: crop top 20% (card name region)
      const cropH = Math.floor(h * 0.20);
      const scale = 3;

      const procCanvas = document.createElement('canvas');
      procCanvas.width = w * scale;
      procCanvas.height = cropH * scale;
      const ctx = procCanvas.getContext('2d');

      // Step 2: draw scaled
      ctx.drawImage(canvas, 0, 0, w, cropH, 0, 0, w * scale, cropH * scale);

      // Step 3: grayscale + contrast boost
      const img = ctx.getImageData(0, 0, procCanvas.width, procCanvas.height);
      const d = img.data;
      for (let i = 0; i < d.length; i += 4) {
        const gray = 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
        const boosted = Math.min(255, Math.max(0, (gray - 128) * 2.5 + 128));
        d[i] = d[i + 1] = d[i + 2] = boosted;
      }
      ctx.putImageData(img, 0, 0);

      try {
        this.scanStatus = 'Cargando OCR...';
        await this.loadTesseract();

        this.scanStatus = 'Leyendo nombre...';
        const { data: { text } } = await window.Tesseract.recognize(procCanvas, 'eng', {
          logger: () => {},
          tessedit_pageseg_mode: '7',       // single text line mode
          tessedit_char_whitelist: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',-.!",
        });

        // Clean up OCR result: take longest line (card names can have spaces)
        const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 1);
        const name = lines.sort((a, b) => b.length - a.length)[0] || '';

        if (!name) {
          this.cameraError = 'No se pudo leer el nombre. Escribilo manualmente.';
          return;
        }

        this.scanStatus = `Buscando "${name}"...`;
        await this.searchByName(name);
      } catch {
        this.cameraError = 'Error al procesar. Escribí el nombre manualmente.';
      } finally {
        this.scanning = false;
        this.scanStatus = '';
      }
    },

    /** Search Scryfall for all printings of a card name. */
    async searchByName(name) {
      if (!name?.trim()) return;
      this.searching = true;
      this.editions = [];
      this.searchError = '';
      this.nameSuggestions = [];
      const q = name.trim();
      try {
        const resp = await fetch(
          `https://api.scryfall.com/cards/search?q=!"${encodeURIComponent(q)}"&unique=prints&order=released`,
          { headers: { Accept: 'application/json' } }
        );

        if (!resp.ok) {
          // No results — fetch autocomplete suggestions as "did you mean"
          this.searchError = `No existe ninguna carta llamada "${q}".`;
          const sugResp = await fetch(
            `https://api.scryfall.com/cards/autocomplete?q=${encodeURIComponent(q)}`,
            { headers: { Accept: 'application/json' } }
          );
          if (sugResp.ok) {
            const sugData = await sugResp.json();
            this.nameSuggestions = sugData.data?.slice(0, 5) || [];
          }
          return;
        }

        const data = await resp.json();
        this.editions = (data.data || []).map(c => ({
          id: c.id,
          name: c.name,
          set_name: c.set_name,
          set_code: c.set,
          type_line: c.type_line || '',
          image_uri: c.image_uris?.normal || c.card_faces?.[0]?.image_uris?.normal || '',
          price_usd: c.prices?.usd || null,
          price_usd_foil: c.prices?.usd_foil || null,
          color_identity: (c.color_identity || []).join(','),
          uri: c.uri || '',
          scryfall_uri: c.scryfall_uri || '',
        }));
      } catch {
        this.searchError = 'Error al conectar con Scryfall.';
      } finally {
        this.searching = false;
      }
    },

    /** User picks a specific edition from the list. */
    selectEdition(card) {
      this.result = card;
      this.editions = [];
      this.manualQuery = '';
    },

    async loadMyBinders() {
      try {
        const { data } = await BinderService.getMyBinders();
        this.myBinders = data;
      } catch {
        this.myBinders = [];
      }
    },

    /** Add the selected card to the chosen binder. */
    async addToBinder() {
      if (!this.selectedBinder || !this.result) return;
      this.adding = true;
      this.addMessage = '';
      this.addError = false;
      try {
        await BinderService.addCardsToBinder(this.selectedBinder, [this.result.name]);
        this.addMessage = `"${this.result.name}" agregada correctamente.`;
      } catch {
        this.addMessage = 'Error al agregar la carta.';
        this.addError = true;
      } finally {
        this.adding = false;
      }
    },

    clearResult() {
      this.result = null;
      this.editions = [];
      this.manualQuery = '';
      this.addMessage = '';
      this.addError = false;
    },
  },
};
</script>

<style scoped>
.scanner-page {
  max-width: 480px;
  margin: 0 auto;
  padding: 80px 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scanner-header { text-align: center; }
.scanner-title { font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.scanner-subtitle { font-size: 13px; color: var(--text-secondary); margin: 0; }

/* Camera */
.camera-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;
  background: #000;
  border-radius: var(--radius);
  overflow: hidden;
}
.camera-feed { width: 100%; height: 100%; object-fit: cover; display: block; }
.hidden-canvas { display: none; }

.scan-overlay { position: absolute; inset: 0; pointer-events: none; }
.scan-corner { position: absolute; width: 28px; height: 28px; border-color: var(--accent); border-style: solid; }
.tl { top: 16px; left: 16px; border-width: 3px 0 0 3px; }
.tr { top: 16px; right: 16px; border-width: 3px 3px 0 0; }
.bl { bottom: 16px; left: 16px; border-width: 0 0 3px 3px; }
.br { bottom: 16px; right: 16px; border-width: 0 3px 3px 0; }

/* Name zone guide: top ~18% of camera */
.name-zone {
  position: absolute;
  top: 5%;
  left: 5%;
  right: 5%;
  height: 13%;
  border: 2px dashed rgba(232, 197, 71, 0.6);
  border-radius: 4px;
}

.camera-placeholder, .camera-error {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px;
  background: var(--bg-elevated); color: var(--text-secondary);
}
.camera-placeholder svg { width: 56px; height: 56px; opacity: 0.4; }
.camera-error p { color: var(--danger); font-size: 14px; text-align: center; padding: 0 24px; }

/* Scan button */
.btn-scan {
  width: 100%;
  padding: 14px;
  background: var(--accent);
  color: #12131a;
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 0.15s;
}
.btn-scan:disabled { opacity: 0.6; cursor: not-allowed; }

/* Manual search */
.manual-search { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 14px; }
.manual-label { font-size: 12px; color: var(--text-muted); margin: 0 0 8px; }
.manual-row { display: flex; gap: 8px; }
.manual-input {
  flex: 1; padding: 9px 12px;
  background: var(--bg-primary); border: 1px solid var(--border-color);
  border-radius: var(--radius-sm); color: var(--text-primary);
  font-size: 14px; font-family: inherit;
}

/* Search error + suggestions */
.search-error-block { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 14px; }
.search-error-msg { color: var(--danger); font-size: 13px; margin: 0 0 10px; }
.search-suggest-label { font-size: 12px; color: var(--text-muted); margin: 0 0 8px; }
.search-suggestions { display: flex; flex-wrap: wrap; gap: 8px; }
.suggestion-chip {
  padding: 5px 12px; border: 1px solid var(--border-color);
  border-radius: 999px; background: var(--bg-elevated);
  color: var(--text-primary); font-size: 13px; cursor: pointer;
  font-family: inherit; transition: border-color 0.15s;
}
.suggestion-chip:hover { border-color: var(--accent); color: var(--accent); }

/* Editions list */
.editions { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 14px; }
.editions-label { font-size: 12px; color: var(--text-muted); margin: 0 0 10px; font-weight: 600; }
.edition-item {
  display: flex; align-items: center; gap: 12px;
  padding: 8px; border-radius: var(--radius-sm); cursor: pointer; transition: background 0.1s;
}
.edition-item:hover { background: var(--bg-elevated); }
.edition-img { width: 48px; border-radius: 4px; flex-shrink: 0; }
.edition-name { font-size: 13px; font-weight: 600; margin: 0 0 2px; }
.edition-set { font-size: 11px; color: var(--text-muted); margin: 0; }
.edition-price { font-size: 12px; color: var(--accent); font-weight: 600; margin: 2px 0 0; }

/* Result */
.result-card { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 16px; display: flex; flex-direction: column; gap: 14px; }
.result-inner { display: flex; gap: 14px; }
.result-img { width: 96px; border-radius: 6px; flex-shrink: 0; object-fit: cover; }
.result-info { flex: 1; }
.result-set { font-size: 11px; color: var(--text-muted); margin: 0 0 4px; text-transform: uppercase; }
.result-name { font-size: 16px; font-weight: 700; margin: 0 0 4px; }
.result-type { font-size: 12px; color: var(--text-secondary); margin: 0 0 8px; }
.result-prices { display: flex; flex-wrap: wrap; gap: 8px; }
.price { font-size: 13px; font-weight: 600; color: var(--accent); background: rgba(232,197,71,0.12); padding: 2px 8px; border-radius: 4px; }
.price.foil { color: #a78bfa; background: rgba(167,139,250,0.12); }

.result-actions { display: flex; flex-direction: column; gap: 8px; }
.binder-select { width: 100%; padding: 9px 12px; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 14px; font-family: inherit; }

.add-message { font-size: 13px; color: #4caf50; margin: 0; text-align: center; }
.add-message.error { color: var(--danger); }

.slide-up-enter-active { transition: all 0.3s ease; }
.slide-up-enter-from { opacity: 0; transform: translateY(20px); }
</style>
