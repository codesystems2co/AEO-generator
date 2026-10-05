"""Shop page for the paid catalog pack. Same business flow, different service."""
from __future__ import annotations

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


def catalog_product_url(owned: bool = False) -> str:
    """Catalog product page — always available so users can buy more fichas."""
    del owned  # ownership no longer hides the acquire URL
    return PRODUCT_URL
