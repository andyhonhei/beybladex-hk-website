# Beyblade X HK website

Public HTTP dashboard for Beyblade X Hong Kong stock status, `/go` hop links, catalog pages, and admin notify test UI. Reads shop SKU state from shared MySQL (written by the sibling [**beybladex-hk-watch**](https://github.com/andyhonhei/beybladex-hk-watch) watcher).

This repo does **not** scrape shops or send alerts. It only serves pages and SELECTs from MySQL.

## Layout

| Path | Purpose |
| --- | --- |
| `src/beyblade_site.py` | CLI + `ThreadingHTTPServer` on `status.host`/`status.port` |
| `src/site_pages.py` | HTML renderers |
| `src/site_data.py` | MySQL reads, `/go` builders, admin session |
| `src/catalog_pages.py` | Catalog HTML routes |
| `src/parts_catalog.py` | Catalog data for display (no shop scrape parsers) |
| `static/` | Logos, OG images |
| `deploy/nginx-beyblade-status.conf` | nginx vhost (hkbeybladex.com, older names, admin) |
| `deploy/DNS.md` | Cloudflare hostname inventory |
| `config/site_config.example.json` | Keys the site reads (`status`, `storage.mysql`, `admin`) |

## Requirements

- Python 3 (stdlib only; no pip deps)
- MySQL with `beyblade_watch` schema populated by the watcher

## Config

Copy the example and fill secrets locally (do not commit):

```bash
cp config/site_config.example.json config/watch_config.json
```

On EC2 you may keep using the **existing** watcher config so MySQL credentials are not duplicated:

```bash
python3 src/beyblade_site.py --config /home/ubuntu/hobbyland_checknew_product/config/watch_config.json
```

The site loads config through `site_data.apply_config` (not the watcher's `apply_config`). Both processes share the same MySQL DSN.

## Run locally

```bash
python3 src/beyblade_site.py --config config/watch_config.json
# default bind: 127.0.0.1:8080
```

## Tests

```bash
python3 -m unittest tests.test_beyblade_site tests.test_catalog_pages
```

## Deploy

- `deploy/beybladex-site.service` — systemd unit (see `WorkingDirectory` / `ExecStart`)
- `deploy/nginx-beyblade-status.conf` — copy to `/etc/nginx/sites-available/` on EC2
- Cloudflare Workers: `deploy/beybladex-cdn.js`, `deploy/beybladex-privacy.js` (+ `.wrangler.jsonc`)
- Hostname / proxy rules: `deploy/DNS.md`
