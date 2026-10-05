"""Live catalog shops. Writes stay on native product fields."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from xmlrpc import client as xmlrpc_client

from app.services.catalog_apply import _TARGETS
from app.services.catalog_reader import (
    BLOCK_SIZE,
    odoo_count_call,
    odoo_fetch_call,
    normalize_odoo,
    normalize_prestashop,
    normalize_woocommerce,
    prestashop_fetch_params,
    woocommerce_fetch_params,
)

FIXTURE_NAME = "AEO data"
SAMPLE_PRODUCTS = (
    ("Cuaderno de campo", "Cuaderno de tapa dura para notas de trabajo, con papel ahuesado y una cinta para marcar la última página escrita.", 12.0),
    ("Lámpara de escritorio", "Lámpara de escritorio con brazo flexible y luz cálida para leer o dibujar sin reflejo en la mesa.", 28.0),
    ("Taza de cerámica", "Taza de cerámica esmaltada, apta para bebidas calientes, con asa ancha y base estable.", 14.0),
    ("Mochila de viaje", "Mochila de viaje con compartimento para un portátil y bolsillo delantero de acceso rápido.", 46.0),
    ("Botella térmica", "Botella térmica de acero que mantiene la bebida caliente o fría durante la jornada de trabajo.", 19.0),
    ("Agenda semanal", "Agenda semanal de un año, con espacio diario para tareas y una cinta de cierre.", 11.0),
    ("Auriculares de estudio", "Auriculares de estudio cerrados, para escuchar una mezcla sin ruido de la sala.", 54.0),
    ("Estuche de lápices", "Estuche rígido para lápices, gomas y un sacapuntas, con cierre de cremallera.", 9.0),
)
FIXTURE_DESCRIPTION = (
    "AEO acerca la ficha del comercio a los buscadores: el nombre y la descripción "
    "de esta oferta quedan listos para el rastreo y para los motores de respuesta."
)


class OdooCatalogShop:
    platform = "odoo"

    def __init__(self, execute: Callable[..., Any], origin: str = ""):
        self.execute = execute
        self.origin = (origin or "").rstrip("/")
        self.fields = set(_TARGETS["odoo"].values())

    def count(self) -> int:
        call = odoo_count_call()
        return int(self.execute(call["model"], call["method"], call["domain"]) or 0)

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        call = odoo_fetch_call(offset, limit)
        rows = self.execute(
            call["model"],
            call["method"],
            call["domain"],
            fields=call["fields"],
            offset=call["offset"],
            limit=call["limit"],
        ) or []
        return [normalize_odoo(row, self.origin) for row in rows]

    def read_block(self, offset: int, limit: int = BLOCK_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        return self.fetch(offset, limit), self.count()

    def read_product(self, product_id: Any) -> Dict[str, Any]:
        call = odoo_fetch_call(0, 1)
        rows = self.execute(
            "product.template",
            "search_read",
            [("id", "=", product_id)],
            fields=call["fields"],
            limit=1,
        ) or []
        if not rows:
            raise KeyError(product_id)
        return normalize_odoo(rows[0], self.origin)

    def write_product(self, product_id: Any, values: Dict[str, Any]) -> None:
        self.execute("product.template", "write", [product_id], values)

    def ensure_samples(self) -> List[int]:
        """Eight new sheets with a name and description, and no search metadata yet."""
        ids: List[int] = []
        for name, description, price in SAMPLE_PRODUCTS:
            found = self.execute(
                "product.template",
                "search_read",
                [("name", "=", name)],
                fields=["id"],
                limit=1,
            ) or []
            if found:
                ids.append(int(found[0]["id"]))
                continue
            product_id = self.execute(
                "product.template",
                "create",
                {
                    "name": name,
                    "description_sale": description,
                    "website_description": f"<p>{description}</p>",
                    "list_price": price,
                    "is_published": True,
                    "website_published": True,
                    "website_meta_title": False,
                    "website_meta_description": False,
                    "website_meta_keywords": False,
                },
            )
            ids.append(int(product_id))
        return ids

    def create_fixture(self) -> Dict[str, Any]:
        found = self._find_fixture()
        if found:
            return found
        product_id = self.execute(
            "product.template",
            "create",
            {
                "name": FIXTURE_NAME,
                "description_sale": FIXTURE_DESCRIPTION,
                "website_description": f"<p>{FIXTURE_DESCRIPTION}</p>",
                "is_published": True,
                "website_published": True,
                "list_price": 0.0,
            },
        )
        return self.read_product(product_id)

    def _find_fixture(self) -> Optional[Dict[str, Any]]:
        call = odoo_fetch_call(0, 1)
        rows = self.execute(
            "product.template",
            "search_read",
            [("name", "=", FIXTURE_NAME)],
            fields=call["fields"],
            limit=1,
        ) or []
        return normalize_odoo(rows[0], self.origin) if rows else None


class HttpCatalogShop:
    def __init__(self, http: Callable[..., Any], origin: str, platform: str, fields: Optional[set] = None):
        self.http = http
        self.origin = (origin or "").rstrip("/")
        self.platform = platform
        self.fields = set(fields or _TARGETS.get(platform, {}).values())

    def count(self) -> int:
        raise NotImplementedError

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def read_block(self, offset: int, limit: int = BLOCK_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        return self.fetch(offset, limit), self.count()

    def read_product(self, product_id: Any) -> Dict[str, Any]:
        for row in self.fetch(0, BLOCK_SIZE):
            if row.get("id") == product_id:
                return row
        raise KeyError(product_id)

    def write_product(self, product_id: Any, values: Dict[str, Any]) -> None:
        self.http("write", product_id, values)


class PrestashopCatalogShop(HttpCatalogShop):
    def __init__(self, http: Callable[..., Any], origin: str = ""):
        super().__init__(http, origin, "prestashop", set(_TARGETS["prestashop"].values()) | {"link_rewrite"})

    def count(self) -> int:
        """Full product count — page id listing when PrestaShop omits total."""
        payload = self.http("GET", "/api/products", {"limit": "0,1", "display": "[id]"})
        if isinstance(payload, dict) and payload.get("total") is not None:
            return int(payload["total"])
        if isinstance(payload, dict) and payload.get("count") is not None:
            return int(payload["count"])
        # Fall back: walk id pages until a short page (no artificial max).
        total = 0
        page_size = 100
        offset = 0
        while True:
            chunk = self.http(
                "GET",
                "/api/products",
                {"limit": f"{offset},{page_size}", "display": "[id]"},
            )
            rows = _as_list((chunk or {}).get("products") if isinstance(chunk, dict) else chunk)
            total += len(rows)
            if len(rows) < page_size:
                break
            offset += page_size
        return total

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        params = prestashop_fetch_params(offset, limit)
        payload = self.http("GET", "/api/products", params)
        rows = _as_list((payload or {}).get("products") if isinstance(payload, dict) else payload)
        return [normalize_prestashop(row, self.origin) for row in rows]


class WooCatalogShop(HttpCatalogShop):
    def __init__(self, http: Callable[..., Any], origin: str = ""):
        super().__init__(http, origin, "woocommerce", set(_TARGETS["woocommerce"].values()))
        self.total = 0

    def count(self) -> int:
        if self.total:
            return self.total
        _rows, total = self._page(1, 1)
        if total and total >= 1:
            self.total = total
            return total
        # No X-WP-Total: page until a short page so every product is counted.
        total = 0
        page = 1
        per_page = 100
        while True:
            rows, _hint = self._page(page, per_page)
            total += len(rows)
            if len(rows) < per_page:
                break
            page += 1
        self.total = total
        return total

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        params = woocommerce_fetch_params(offset, limit)
        rows, total = self._page(params["page"], params["per_page"])
        if total:
            self.total = total
        return [normalize_woocommerce(row) for row in rows]

    def _page(self, page: int, per_page: int) -> Tuple[List[Dict[str, Any]], int]:
        payload = self.http("GET", "/wp-json/wc/v3/products", {"page": page, "per_page": per_page})
        if isinstance(payload, dict):
            rows = list(payload.get("products") or payload.get("items") or [])
            total = int(payload.get("total") or payload.get("x-wp-total") or 0)
            return rows, total
        rows = list(payload or [])
        return rows, 0


def _as_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        if "product" in value and isinstance(value["product"], list):
            return [item for item in value["product"] if isinstance(item, dict)]
        if value.get("id") is not None:
            return [value]
    return []


def odoo_execute_from_secrets(secrets: Dict[str, Any]) -> Callable[..., Any]:
    url = (secrets.get("url") or "").rstrip("/")
    database = secrets.get("database") or ""
    username = secrets.get("username") or ""
    api_key = secrets.get("api_key") or ""
    common = xmlrpc_client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(database, username, api_key, {})
    if not uid:
        raise RuntimeError("Odoo authentication failed")
    models = xmlrpc_client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    def execute(model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        return models.execute_kw(database, uid, api_key, model, method, list(args), kwargs or {})

    return execute


class SelectedCatalogShop:
    """A catalog pass limited to the sheets created for this interaction."""

    def __init__(self, inner: Any, product_ids: List[int]):
        self.inner = inner
        self.ids = [int(item) for item in product_ids]
        self.platform = getattr(inner, "platform", None)
        self.fields = getattr(inner, "fields", set())
        self.origin = getattr(inner, "origin", "")

    def count(self) -> int:
        return len(self.ids)

    def fetch(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        chosen = self.ids[max(0, int(offset)) : max(0, int(offset)) + max(0, int(limit))]
        return [self.inner.read_product(product_id) for product_id in chosen]

    def read_block(self, offset: int, limit: int = BLOCK_SIZE) -> Tuple[List[Dict[str, Any]], int]:
        return self.fetch(offset, limit), self.count()

    def read_product(self, product_id: Any) -> Dict[str, Any]:
        if int(product_id) not in self.ids:
            raise KeyError(product_id)
        return self.inner.read_product(product_id)

    def write_product(self, product_id: Any, values: Dict[str, Any]) -> None:
        if int(product_id) not in self.ids:
            raise KeyError(product_id)
        self.inner.write_product(product_id, values)


def shop_from_secrets(secrets: Dict[str, Any]) -> Any:
    platform = str(secrets.get("platform") or "").strip().lower()
    origin = (secrets.get("url") or "").rstrip("/")
    if platform == "odoo":
        return OdooCatalogShop(odoo_execute_from_secrets(secrets), origin)
    if platform == "prestashop":
        return PrestashopCatalogShop(_http_json(origin, secrets.get("ws_key"), None), origin)
    if platform == "woocommerce":
        return WooCatalogShop(_http_json(origin, secrets.get("consumer_key"), secrets.get("consumer_secret")), origin)
    raise ValueError(f"unsupported platform: {platform}")


def _http_json(origin: str, user: Optional[str], password: Optional[str]) -> Callable[..., Any]:
    import urllib.request

    def http(method: str, path: str, params: Any = None) -> Any:
        if method == "write":
            product_id, values = path, params
            req = urllib.request.Request(
                urljoin(origin + "/", f"wp-json/wc/v3/products/{product_id}"),
                data=json.dumps(values).encode("utf-8"),
                method="PUT",
                headers={"Content-Type": "application/json"},
            )
        else:
            from urllib.parse import urlencode

            query = urlencode(params or {})
            url = f"{origin}{path}" + (f"?{query}" if query else "")
            req = urllib.request.Request(url, method=method)
        if user:
            import base64

            token = base64.b64encode(f"{user}:{password or ''}".encode("utf-8")).decode("ascii")
            req.add_header("Authorization", f"Basic {token}")
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read()
            total = response.headers.get("X-WP-Total")
            payload = json.loads(raw.decode("utf-8") or "null")
            if total is not None and isinstance(payload, list):
                return {"products": payload, "total": int(total)}
            return payload

    return http
