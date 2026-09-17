# Addendum — gate UX (same aeo_generator thread, no second stack)

Fold into CURSOR_PROMPT_PHASE5_HOSTNAME_LOCK_01.md §2. Do not open a new Composer thread.

## Sin pedido (screenshot from Alex)

Today: key + site inputs + four buttons (Comprobar clave, Comenzar asistente, Crear o confirmar pedido, Entrar en Arkiphere). Too much.

### Keep
- **Clave de activación** as a real input. Pack will also be sold outside Arkiphere (other marketplaces). User pastes `AEO-…` then checks.
- **Comprobar clave** as the redeem action for a pasted key.

### Remove from the empty/blocked state
- **Sitio (HTTPS) as an input** — never. Not a field. If consume `allowed: true`, show the commerce hostname as **read-only text/value** (label + value, not `<input>`). Hide the site row entirely when there is no confirmed order.
- **Comenzar asistente** until allowed.
- **Crear o confirmar pedido en Arkiphere** and **Entrar en Arkiphere**.

### One designed CTA when blocked
Single button inviting purchase on the **product page** (not shop home, not login):

https://arkiphere.cloud/shop/aeo-optimizator-ia-search-optimizator-pack-aeo-seo-and-google-search-109

Copy e.g. **Adquirir el pack** / **Comprar en Arkiphere**. Open AEO from a confirmed Arkiphere order still lands with `?license=&site=` and unlocks naturally.

### After allowed
Show pedido badge + site **value** (locked, from consume SoT) + **Comenzar asistente**. Server still rejects tampered site (hostname lock).

Rebuild live :9012. Evidence in same `_bmad-output/2026-09-16_hostname_lock/` folder.
