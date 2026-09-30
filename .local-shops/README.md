# Local demo shops

## Odoo (already in repo)

```bash
cd ../.local-odoo && docker compose up -d
```

- URL: http://127.0.0.1:8069
- DB: create `demo` in UI or use existing; master password set on first visit.

## WooCommerce + PrestaShop

```bash
cd .local-shops && docker compose up -d
```

| Platform     | URL                     | Notes                                      |
|-------------|-------------------------|--------------------------------------------|
| WooCommerce | http://127.0.0.1:8080   | Finish WP install; install WooCommerce plugin; create REST keys |
| PrestaShop  | http://127.0.0.1:8081   | Auto-install; admin `demo@prestashop.com` / `prestashop_demo` |

For the Optimizator wizard, use each shop’s public URL (or host IP) when registering connections.
