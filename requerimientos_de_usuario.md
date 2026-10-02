# Requerimientos de usuario

Relevamiento de **todo lo que puede hacer cada tipo de usuario** en MTG Trade
Community, derivado del código (no de la documentación). Refleja el estado del
repo al 2026-09-22, incluyendo el trabajo de subastas todavía sin commitear.

## Tipos de usuario

El sistema no tiene un modelo de roles propio. Los "tipos" salen de tres cosas:

| Tipo | Cómo se determina | Dónde |
|---|---|---|
| **Anónimo** | Sin JWT válido en el header | `OptionalJWTAuthentication` |
| **Registrado** | JWT válido (`request.user.is_authenticated`) | `api/token/` |
| **Staff** | `User.is_staff = True` | `IsAdminUser`, `meta.requiresStaff` |
| **Superusuario** | `User.is_superuser = True` | `/admin/` de Django |

Dentro de "Registrado" hay dos papeles situacionales que cambian lo que se puede
hacer sobre un objeto concreto:

- **Dueño** de un binder / wishlist / perfil.
- **Comprador** o **vendedor** de un carrito (`Cart.buyer` / `Cart.seller`).

No son roles: el mismo usuario es vendedor en un carrito y comprador en otro.

---

## 1. Usuario anónimo

### Puede

| Acción | Endpoint / ruta |
|---|---|
| Registrarse | `POST users/users/` |
| Iniciar sesión (obtener JWT) | `POST api/token/` |
| Renovar el token | `POST api/token/refresh/` |
| Ver la landing | `/` (Home) |
| Listar binders públicos | `GET binders/binders/` |
| Buscar binders por carta | `GET binders/binders/?card_name=` → `/search`, `/carpetas` |
| Ver el detalle de un binder y sus cartas | `GET binders/binders/{id}/` → `/binder/:id` |
| Ver el perfil público de un usuario (reputación, trades, cartas vendidas, binders públicos, últimas reseñas) | `GET users/users/public-profile/{username}/` → `/user/:username` |
| Listar subastas (abiertas, en curso, próximas, cerradas) y buscarlas | `GET auctions/auctions/?status=&q=` → `/subastas` |
| Ver el detalle de una subasta | `GET auctions/auctions/{id}/` → `/subasta/:id` |
| Ver el historial público de pujas | `GET auctions/auctions/{id}/bids/` |
| Ver la documentación de la API | `/swagger/`, `/redoc/` |

### No puede

- Crear binders, agregar o quitar cartas.
- Usar el autocompletado de cartas (`cards/autocomplete/` exige login).
- Usar el chequeo masivo de cartas (`cards/check-cards/` exige login).
- Usar el escáner de cartas (`scanner/identify/` exige login).
- Wishlist, carrito, checkout, chat, puntuaciones.
- Pujar en subastas.

> El front redirige a `/login` cualquier ruta con `meta.requiresAuth`
> (`web/src/router/index.js:128`).

---

## 2. Usuario registrado

Hereda todo lo del anónimo, más lo siguiente.

### 2.1 Cuenta y perfil

- Ver sus propios datos: `GET users/users/me/`.
- Ver su perfil completo: `GET users/users/profile/`.
- Editar su perfil: `PATCH users/users/profile/` → `first_name`, `last_name`,
  `email`, `phone`, `address`, `city`, `province` (`/profile`).
- Cerrar sesión (limpia `localStorage`, es solo del cliente).

El `UserProfile` se crea solo al registrarse, vía signal `post_save`
(`backend/users/models.py:18`).

### 2.2 Binders (colección propia)

- Listar sus binders, públicos y privados: `GET binders/binders/my-binders/` → `/my-binders`.
- Crear un binder: `POST binders/binders/` (queda a su nombre automáticamente).
- Editar un binder (nombre, `is_public`): `PUT`/`PATCH binders/binders/{id}/`.
- Borrar un binder: `DELETE binders/binders/{id}/`.
- Agregar cartas por nombre (batch, resuelve contra Scryfall): `POST .../add-cards/`.
- Agregar una impresión concreta por UUID de Scryfall: `POST .../add-card-by-id/`.
- Importar un CSV exportado de Moxfield: `POST .../import-moxfield/`
  (respeta `Count` y `Foil`).
- Quitar cartas por nombre (baja de a una unidad): `POST .../remove-cards/`.
- Marcar un binder como público (lo pone a la venta) o privado (lo saca).

Todas estas acciones validan propiedad con `_assert_owner`
(`backend/binders/views.py:115`): sobre un binder ajeno devuelven 403.

**Solo los binders públicos están a la venta** — el descuento de stock filtra por
`binder__is_public=True` (`backend/carts/stock.py:30`).

### 2.3 Wishlist

- Ver su wishlist: `GET binders/wishlist/` → `/wishlist`.
- Agregar cartas por nombre: `POST binders/wishlist/`.
- Quitar una carta: `DELETE binders/wishlist/{card_id}/`.
- Ver coincidencias: qué usuarios tienen en binders públicos las cartas que
  busca, agrupado por usuario y ordenado por cantidad de matches:
  `GET binders/wishlist/matches/`. Excluye sus propios binders.

### 2.4 Escáner y búsqueda de cartas

- Identificar una carta desde la cámara: `POST scanner/identify/` → `/scanner`.
  Manda un JPEG en base64, recibe la mejor coincidencia más 3 candidatos con
  `distance` y `confidence` (dhash, `backend/scanner/views.py`).
- Autocompletar nombres de cartas contra Scryfall: `GET cards/autocomplete/?q=`.
- Chequear en lote qué nombres existen en la base: `POST cards/check-cards/`.

### 2.5 Comprar (papel de comprador)

- Agregar al carrito una carta de un binder público ajeno:
  `POST carts/carts/add-card/`. Reglas:
  - No puede comprarse a sí mismo (400).
  - No puede pedir más copias de las que el vendedor tiene publicadas (409).
  - Se agrupa un carrito abierto por vendedor: un carrito = un vendedor.
- Ver sus carritos como comprador: `GET carts/carts/` → `/cart`.
- Ver un carrito: `GET carts/carts/{id}/`.
- Quitar una carta del carrito: `POST carts/carts/{id}/remove-card/`
  (si queda vacío, el carrito se borra). **No permitido en carritos de subasta.**
- Hacer checkout: `POST carts/carts/{id}/checkout/` con `shipping_method`
  (`door_to_door` | `branch_pickup`), `shipping_cost` y `notes` opcionales.
  - Nada se reserva antes: gana el primero que hace checkout; el resto recibe
    409 con `unavailable_cards`.
  - Descuenta el stock de los binders del vendedor y registra de qué binder
    salió cada copia (`CartItemAllocation`).
- Subir el comprobante de pago: `POST carts/carts/{id}/upload-payment/`.
- Marcar la orden como **completada** o **cancelada**:
  `POST carts/carts/{id}/update-status/`. Cancelar devuelve las cartas a los
  binders exactos de donde salieron.
- Puntuar al vendedor (0 a 10 + comentario) una sola vez, y solo con la orden en
  `completed`: `POST carts/carts/{id}/rate/`.
- Chatear con el vendedor: `GET`/`POST carts/carts/{id}/messages/` → `/cart/:cartId`.

### 2.6 Vender (papel de vendedor)

- Ver los carritos donde es vendedor: `GET carts/carts/selling/`.
- Ver el detalle de esos carritos (`_participant_cart` acepta comprador o vendedor).
- Marcar la orden como **enviada**: `POST .../update-status/` con `shipped`.
  Es el único estado que puede setear el vendedor.
- Chatear con el comprador.
- Recibir puntuaciones (no puede responderlas ni puntuar al comprador).

El vendedor **no** puede cancelar ni completar una orden: eso es exclusivo del
comprador (`backend/carts/views.py:224`).

### 2.7 Subastas (papel de postor)

- Pujar: `POST auctions/auctions/{id}/bid/` con `max_amount`. Proxy bidding
  estilo eBay: se declara el máximo que se está dispuesto a pagar y el sistema
  solo cobra `current_price`, un incremento por encima del segundo.
  - Solo con la subasta en `live` (400 si está `scheduled`, `closed` o `cancelled`).
  - No se puede pujar en la propia subasta.
  - Primera puja ≥ `starting_price`; el resto ≥ `current_price + min_increment`.
  - Si ya es líder, solo puede subir su propio techo.
  - Una puja en los últimos 3 minutos (`ANTI_SNIPE_WINDOW`) corre el cierre.
- Ver su propio máximo (`my_max_bid`) y si va ganando (`is_leading`) — campos que
  el serializer calcula por usuario.
- Filtrar las subastas en las que participó: `GET auctions/auctions/?mine=1`.
- Al ganar: se le crea automáticamente un `Cart` con `source='auction'`, un
  `CartItem` con `price_ars` = puja ganadora, y un mensaje inicial del vendedor.
  Desde ahí sigue el flujo normal de orden (checkout, comprobante, chat, rating),
  salteando las validaciones de stock de binder.

Nadie —ni staff— ve el techo oculto del líder (`leader_max_amount`) ni el
`max_amount` ajeno en el historial: `BidSerializer` los omite a propósito.

---

## 3. Staff (`is_staff`)

Hereda todo lo del usuario registrado. Es, hoy, el **único que corre subastas**:
la plataforma es la vendedora.

| Acción | Endpoint |
|---|---|
| Crear una subasta (por `card_id` o `card_name`; si la carta no está, la trae de Scryfall) | `POST auctions/auctions/` |
| Editar una subasta — **solo si no tiene pujas** (409 si las tiene) | `PATCH auctions/auctions/{id}/` |
| Borrar una subasta — **solo si no tiene pujas** | `DELETE auctions/auctions/{id}/` |
| Cerrar anticipadamente (liquida al precio actual y abre el carrito del ganador) | `POST auctions/auctions/{id}/close/` |
| Cancelar una subasta (sin ganador ni carrito) | `POST auctions/auctions/{id}/cancel/` |
| Obtener la ventana viernes-a-viernes sugerida para prellenar el formulario | `GET auctions/auctions/default-window/` |
| Ver el `reserve_price` (el resto solo ve si se alcanzó o no) | campo de `AuctionSerializer` |

En el front: `/subastas/admin` (`AuctionAdmin.vue`), protegida por
`meta.requiresStaff` y el link del navbar solo visible con `isStaff`.

Campos configurables al crear: carta, título, descripción, condición
(NM/SP/MP/HP/DMG), foil, etched, imagen, precio inicial, incremento mínimo,
precio de reserva, inicio y cierre.

---

## 4. Superusuario (Django admin)

- Acceso a `/admin/`.
- Gestión completa de usuarios, grupos y permisos de Django.
- ABM de subastas y pujas con inline de pujas, filtros por estado/condición/foil
  y búsqueda por título o nombre de carta (`backend/auctions/admin.py`).
  Los campos derivados (precio actual, líder, techo del líder, ganador, carrito)
  son de solo lectura.
- **El resto de los modelos no está registrado en el admin**: `Binder`,
  `BinderCard`, `Card`, `Cart`, `Order`, `Rating`, `Message`, `WishlistCard` y
  `UserProfile` no se pueden ver ni editar desde `/admin/`.

### Comandos de gestión (requieren acceso al contenedor, no a la web)

| Comando | Qué hace |
|---|---|
| `close_auctions` | Cierra las subastas vencidas (redundante: cada lectura de la API ya llama a `settle_due_auctions()`) |
| `seed_community` | Carga datos de comunidad de prueba |
| `seed_data`, `create_binders`, `load_cards` | Semillas de cartas y binders |
| `compute_card_hashes` | Calcula los dhash que usa el escáner |

---

## 5. Matriz resumen

| Capacidad | Anónimo | Registrado | Staff | Superuser |
|---|:---:|:---:|:---:|:---:|
| Ver binders públicos y buscar cartas | ✅ | ✅ | ✅ | ✅ |
| Ver perfiles públicos y reputación | ✅ | ✅ | ✅ | ✅ |
| Ver subastas e historial de pujas | ✅ | ✅ | ✅ | ✅ |
| Registrarse / iniciar sesión | ✅ | — | — | — |
| Crear y administrar binders propios | ❌ | ✅ | ✅ | ✅ |
| Importar CSV de Moxfield | ❌ | ✅ | ✅ | ✅ |
| Wishlist y matches | ❌ | ✅ | ✅ | ✅ |
| Escáner de cartas / autocompletado | ❌ | ✅ | ✅ | ✅ |
| Carrito y checkout | ❌ | ✅ | ✅ | ✅ |
| Subir comprobante, marcar completado/cancelado | ❌ | ✅ (comprador) | ✅ | ✅ |
| Marcar enviado | ❌ | ✅ (vendedor) | ✅ | ✅ |
| Chat de la orden | ❌ | ✅ (participante) | ✅ | ✅ |
| Puntuar (0-10) | ❌ | ✅ (comprador) | ✅ | ✅ |
| Pujar en subastas | ❌ | ✅ | ✅ | ✅ |
| Crear / editar / cerrar / cancelar subastas | ❌ | ❌ | ✅ | ✅ |
| Ver el precio de reserva | ❌ | ❌ | ✅ | ✅ |
| Django admin | ❌ | ❌ | ⚠️ ver abajo | ✅ |

⚠️ `is_staff` habilita el ingreso a `/admin/`, pero sin permisos de modelo
asignados el usuario staff solo ve un admin vacío.

---

## 6. Huecos detectados durante el relevamiento

Cosas que el código permite o impide y que probablemente no sean intencionales.
No las toqué; quedan acá para decidir.

1. **Cualquier usuario autenticado puede editar o borrar a cualquier otro
   usuario.** `UserViewSet` aplica `IsAuthenticated` a `update`, `partial_update`
   y `destroy` sin chequear que el objeto sea uno mismo
   (`backend/users/views.py:22`). También permite listar todos los usuarios con
   su email.
2. **Los binders privados se pueden leer por ID.** El filtro `is_public=True`
   solo aplica a `list`; `retrieve` es `AllowAny` y no filtra
   (`backend/binders/views.py:103`). Un `GET binders/binders/{id}/` devuelve
   cualquier binder, privado incluido.
3. **El autocompletado y `check-cards` exigen login** aunque la búsqueda pública
   de binders no. Un visitante puede buscar pero sin ayuda de autocompletado.
4. **El vendedor no puede cancelar una orden.** Si no tiene la carta o el
   comprador desaparece, solo el comprador puede cerrarla.
5. **No hay puntuación del vendedor al comprador.** `Rating` es unidireccional.
6. **Los usuarios no pueden crear subastas propias.** Está previsto —el FK
   `Auction.seller` existe— pero hoy `create` es `IsAdminUser`.
7. **La mayoría de los modelos no está en el Django admin**, así que no hay
   forma de moderar binders, órdenes, mensajes ni ratings desde la web.
8. **No hay borrado de cuenta propio ni cambio de contraseña** por API.
9. **El chat no tiene estado de leído ni notificaciones**: hay que entrar al
   carrito para ver si llegó un mensaje.
