# Scanner feature — feedback y guía de testing

## Qué se implementó

- **Backend**: app `scanner` con endpoint `POST /scanner/identify/`
  - OpenCV detecta el rectángulo de la carta y corrige perspectiva
  - `imagehash.phash` compara contra todas las cartas de la DB
  - Devuelve carta + distancia Hamming + score de confianza 0–1
- **Management command**: `compute_card_hashes` descarga imágenes de Scryfall y calcula phash para cada carta
- **Management command**: `seed_data` expandido a 5 usuarios con 2 binders cada uno (temáticos)
- **Frontend**: vista `/scanner` con video en tiempo real, auto-detección cada 900ms, resultado con precio y botón "Agregar al binder"
- **PWA**: `manifest.json` + `sw.js` → instalable desde Chrome mobile; funciona responsive sin instalar
- **Navbar**: ícono de cámara visible para usuarios autenticados

---

## Cosas que mejoraría (backlog técnico)

1. **Caché de hashes en RAM al levantar el servidor**
   Hoy cada request escanea toda la tabla `Card` en Python.
   Con 30k cartas puede tardar 1–2 s.  La mejora es cargar todos los
   `(id, phash)` en un dict en memoria al iniciar Django (usando `AppConfig.ready()`).

2. **Umbral de confianza configurable por settings**
   `MAX_DISTANCE = 15` está hardcodeado en `scanner/views.py`.
   Exponerlo como `SCANNER_MAX_DISTANCE` en `settings.py` permite ajustarlo
   sin tocar código (útil para cartas viejas con arte oscuro que tienen más ruido).

3. **Feedback visual en tiempo real en la cámara**
   Dibujar un rectángulo verde sobre el contorno detectado mientras el backend
   responde.  Requiere comunicar el resultado del `_detect_card` de vuelta al
   frontend (posiblemente como coordenadas en el JSON de respuesta).

4. **Detección multi-carta**
   Detectar varios contornos en un mismo frame y devolver una lista de cartas.
   Útil para escanear una mano de cartas de una vez.

5. **Offline scanner con modelo local (TFLite)**
   Para casos sin conexión: exportar un modelo liviano de clasificación de cartas
   y correrlo directo en el browser con TensorFlow.js.  Requiere dataset etiquetado.

6. **Rate limiting en el endpoint**
   Agregar `throttle_classes` en `CardIdentifyView` para evitar que se abuse del
   endpoint (especialmente porque hace queries sobre toda la tabla).

7. **Campo `condition` en BinderCard**
   Agregar estado físico de la carta (NM, LP, MP, HP, DMG) para que el scanner
   pueda mostrar el precio correcto según condición.

8. **Historial de escaneos**
   Guardar las últimas N cartas escaneadas por usuario en IndexedDB (frontend)
   para poder revisarlas sin repetir el escaneo.

---

## Guía para testear en el celular

### Paso 0 — Levantar el backend y el frontend

```bash
# Terminal 1 — Backend
cd backend && docker-compose up

# Terminal 2 — Frontend (sin Docker, para poder cambiar el host)
cd web && npm install && npm run serve -- --host 0.0.0.0
```

---

### Paso 1 — Cargar las hashes de las cartas (una sola vez)

```bash
# Primero cargá las cartas con el seed
docker-compose exec web python manage.py seed_data

# Después calculá las hashes
docker-compose exec web python manage.py compute_card_hashes
# Opción para probar solo con 20 cartas:
docker-compose exec web python manage.py compute_card_hashes --limit 20
```

---

### Opción A — Red local WiFi (más simple)

1. Conectá la PC y el cel a la misma red WiFi.

2. Encontrá la IP local de tu PC:
   ```bash
   ip addr show | grep 'inet ' | grep -v 127
   # Ejemplo: 192.168.1.42
   ```

3. En `web/src/services/BinderService.js` cambiá la `API_URL`:
   ```js
   const API_URL = "http://192.168.1.42:8000/";
   ```

4. En el cel, abrí Chrome y entrá a `http://192.168.1.42:8080`.

5. **La cámara solo funciona en HTTPS o localhost.**
   Para habilitarla en HTTP local, en Chrome mobile abrí:
   `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
   → escribí `http://192.168.1.42:8080` → Habilitar → Reiniciar Chrome.

---

### Opción B — ngrok (recomendado, HTTPS automático)

```bash
# Instalar ngrok: https://ngrok.com/download
ngrok http 8080
# Te da algo como: https://xxxx.ngrok-free.app
```

- Esa URL ya tiene HTTPS → la cámara del cel funciona sin configuración extra.
- Cambiá también la `API_URL` en BinderService.js para que apunte al backend:
  ```bash
  ngrok http 8000  # en otra terminal
  ```

---

### Checklist de pruebas

- [ ] El scanner abre la cámara trasera del cel automáticamente
- [ ] Al apuntar a una carta, el backend responde en menos de 3 s
- [ ] La carta identificada es correcta para al menos 2 ediciones distintas de "Dark Ritual"
- [ ] El porcentaje de confianza sube cuando la carta está bien encuadrada
- [ ] El botón "Agregar al binder" agrega la carta y muestra confirmación
- [ ] "Seguir escaneando" reactiva la cámara correctamente
- [ ] La PWA se puede instalar desde Chrome mobile (menú → "Agregar a pantalla de inicio")
- [ ] La app se ve bien en pantalla de 375 px de ancho (iPhone SE / Android pequeño)
- [ ] Al entrar sin login, el router redirige a /login antes de abrir el scanner






