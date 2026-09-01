# Beyblade X HK Website

Website-only runtime for HK BeybladeX Watch. This repository serves the public
HTTP pages, catalog pages, static assets, CDN Worker, and privacy/terms Worker.

The stock watcher and shop parsers live in the separate watch repository. This
repo reads existing status, history, product, image, and catalog data from the
configured data directory or MySQL database.

## Layout

- `src/beyblade_site.py` - HTTP server entry point.
- `src/site_data.py` - data/config helpers used by the website.
- `src/site_pages.py` - public page rendering.
- `src/catalog_pages.py` - catalog and collection page rendering.
- `src/parts_catalog.py` - catalog load/write/display helpers.
- `static/` - public images and icons.
- `deploy/` - nginx, systemd, and Cloudflare Worker deployment files.

## Configuration

Copy `config/site_config.example.json` if you want a website-specific config.
On EC2, the website may keep using the existing watch config at
`/home/ubuntu/hobbyland_checknew_product/config/watch_config.json` so MySQL and
admin credentials are not duplicated.

Run locally with:

```bash
python3 src/beyblade_site.py --config config/site_config.example.json
```

## Tests

```bash
python3 -m unittest tests.test_beyblade_site tests.test_catalog_pages
```

## Deploy

The example systemd unit in `deploy/beybladex-site.service` runs the site from
`/home/ubuntu/beybladex-hk-website` and reads the existing EC2 watch config.
