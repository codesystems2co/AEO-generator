"""Shop page for the paid catalog pack. Same business flow, different service."""
from __future__ import annotations

from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

PRODUCT_NAME = "Product Catalog AEO and SEO pack With IA"
PRODUCT_PATH = "/shop/product-catalog-aeo-and-seo-pack-with-ia-110"
PRODUCT_URL = "https://arkiphere.cloud/shop/product-catalog-aeo-and-seo-pack-with-ia-110"

PRODUCT_DESCRIPTION = (
    "Mismo asistente, otro servicio: recorre las fichas del catálogo de un hostname, "
    "escribe AEO y SEO en cada producto y entrega un informe cuando ese trabajo termina. "
    "No inventa precio ni SKU. Las preguntas viven en la ficha, no en una URL nueva."
)

PRODUCT_WEBSITE_HTML = """
<h2>Optimización AEO y SEO para cada ficha del catálogo</h2>
<p>Un hostname. Lectura por bloques. Informe de catálogo.</p>
<ul>
<li>Pack SEO: título, metadatos y canónica de cada producto.</li>
<li>Odoo, PrestaShop y WooCommerce.</li>
<li>Compra por hostname. Resultados medibles.</li>
</ul>
<h3>Qué incluye</h3>
<ol>
<li>Lectura del catálogo por bloques de 20, con cola visible de seis productos.</li>
<li>Pack AEO por ficha: resumen que responde primero y preguntas cotidianas en la descripción.</li>
<li>Pack SEO por ficha: título 30–60, meta 120–160, palabras clave y canónica igual a la URL del producto.</li>
<li>Esquema Product con el precio ya guardado. No se inventa otro precio.</li>
<li>Escritura solo en campos nativos. En Odoo: website_meta_title, website_meta_description, website_meta_keywords y website_description.</li>
<li>Informe de catálogo cuando el trabajo de las fichas termina.</li>
</ol>
<h3>Plataformas compatibles</h3>
<ul>
<li>Odoo Website / eCommerce: product.template</li>
<li>PrestaShop: producto del webservice</li>
<li>WooCommerce: producto REST, Yoast o Rank Math solo si ya existen</li>
</ul>
<h3>Protección de datos</h3>
<ul>
<li>Reutiliza la conexión ya guardada del pack general.</li>
<li>No crea campos nuevos ni instala módulos.</li>
<li>La primera publicación de prueba escribe solo la ficha AEO data.</li>
</ul>
"""


def _normalize_host_for_query(value: Optional[str]) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if "://" not in text:
        text = "https://" + text
    try:
        host = urlparse(text).hostname or ""
    except Exception:
        host = ""
    host = host.lower().removeprefix("www.")
    return host


def catalog_product_url(
    owned: bool = False,
    *,
    host: Optional[str] = None,
    quantity: Optional[int] = None,
) -> str:
    """Catalog product page with optional session hostname + needed qty query.

    Always available so users can buy more fichas. Shop aeo_base autofills
    hostname from ``aeo_site_url`` / ``hostname`` and writes it on cart lines.
    """
    del owned  # ownership no longer hides the acquire URL
    params = []
    bare = _normalize_host_for_query(host)
    if bare:
        site = f"https://{bare}"
        params.append(("aeo_site_url", site))
        params.append(("hostname", bare))
    try:
        qty = int(quantity) if quantity is not None else 0
    except (TypeError, ValueError):
        qty = 0
    if qty > 0:
        params.append(("qty", str(qty)))
    if not params:
        return PRODUCT_URL
    parsed = urlparse(PRODUCT_URL)
    existing = parse_qsl(parsed.query, keep_blank_values=True)
    # Prefer our session params over any stale query on the base URL.
    keys = {k for k, _ in params}
    merged = [(k, v) for k, v in existing if k not in keys] + params
    return urlunparse(parsed._replace(query=urlencode(merged)))
