#!/usr/bin/env python3
from __future__ import print_function

import argparse
import json
import os
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from site_data import (
    DATA_DIR,
    DEFAULT_CONFIG_PATH,
    HTML_CACHE_CONTROL,
    IMAGE_CACHE_CONTROL,
    INDEX_NOTIFY_SCAN,
    OG_GOAL_PATH,
    OG_HOME_PATH,
    OG_TEST_PATH,
    PRIVACY_ALIAS_PATH,
    PRIVACY_PATH,
    STATIC_PNGS,
    SUBSCRIBE_PATH,
    TERMS_ALIAS_PATH,
    TERMS_PATH,
    admin_credentials_ok,
    admin_host_request,
    admin_session_ok,
    admin_set_cookie,
    apply_config,
    build_watcher_status,
    cached_bytes,
    filter_index_notifies,
    go_http_result,
    go_shop_landing_id,
    is_admin_host,
    is_preview_crawler,
    load_config,
    load_notify_history,
    load_shop_products_for_shop_id,
    parse_go_path,
    run_web_notify_test,
    shop_chip_shops,
    shop_page_meta,
    start_listing_watch_loop,
    status_request_redirect,
    status_settings,
    stock_filter_from_query,
    tag_filter_from_query,
)
from site_pages import (
    render_admin_login_html,
    render_coffee_html,
    render_history_html,
    render_notify_test_html,
    render_og_test_html,
    render_privacy_html,
    render_products_html,
    render_share_card_html,
    render_shops_html,
    render_status_html,
    render_subscribe_html,
    render_terms_html,
    robots_txt,
    sitemap_xml,
    web_manifest,
)


def start_status_server():
    cfg = status_settings()
    if not cfg["enabled"]:
        return None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def _bytes(self, code, content_type, body, cache="no-store", robots=None, cookie=None):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            if self.command == "OPTIONS":
                self.send_header("Allow", "GET, HEAD, OPTIONS, POST")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS, POST")
                self.send_header("Access-Control-Allow-Headers", "*")
            if cookie:
                self.send_header("Set-Cookie", cookie)
            if robots:
                self.send_header("X-Robots-Tag", robots)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _host(self):
            return self.headers.get("Host") or ""

        def _cookie(self):
            return self.headers.get("Cookie") or ""

        def _serve_go(self, parsed, remember=False, force_store=False):
            result = go_http_result(
                parsed.path,
                query=parsed.query,
                cookie=self._cookie(),
                remember=remember,
                force_store=force_store,
                user_agent=self.headers.get("User-Agent") or "",
            )
            if result.get("status") == 404:
                self.send_error(404)
                return
            if result.get("status") == 302:
                self.send_response(302)
                self.send_header("Location", result["location"])
                self.send_header("Cache-Control", "private, no-store")
                self.send_header("X-Robots-Tag", "noindex, nofollow")
                self.end_headers()
                return
            self._bytes(
                200,
                "text/html; charset=utf-8",
                result["html"].encode("utf-8"),
                cache=result.get("cache") or "private, no-store",
            )

        def _secure(self):
            proto = (self.headers.get("X-Forwarded-Proto") or "").lower()
            return proto == "https"

        def _read_body(self):
            length = int(self.headers.get("Content-Length") or 0)
            return self.rfile.read(length) if length else b""

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            host = self._host()
            if parse_go_path(parsed.path) or go_shop_landing_id(parsed.path):
                if is_admin_host(host):
                    self.send_error(404)
                    return
                raw = self._read_body()
                data = dict(urllib.parse.parse_qsl(raw.decode("utf-8"), keep_blank_values=True))
                remember = str(data.get("remember") or "").lower() in ("1", "on", "true")
                self._serve_go(parsed, remember=remember, force_store=True)
                return
            if parsed.path == "/login":
                if not is_admin_host(host):
                    self.send_error(404)
                    return
                raw = self._read_body()
                ctype = (self.headers.get("Content-Type") or "").lower()
                data = {}
                if "json" in ctype:
                    try:
                        parsed_json = json.loads(raw.decode("utf-8") or "{}")
                    except Exception:
                        parsed_json = {}
                    if isinstance(parsed_json, dict):
                        data = parsed_json
                else:
                    data = dict(urllib.parse.parse_qsl(raw.decode("utf-8"), keep_blank_values=True))
                if admin_credentials_ok(data.get("username"), data.get("password")):
                    self.send_response(302)
                    self.send_header("Location", "/notify-test")
                    self.send_header("Set-Cookie", admin_set_cookie(secure=self._secure()))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    return
                self._bytes(
                    401,
                    "text/html; charset=utf-8",
                    render_admin_login_html(error=True).encode("utf-8"),
                    cache="no-store",
                    robots="noindex, nofollow",
                )
                return
            if parsed.path != "/notify-test":
                self.send_error(404)
                return
            if not is_admin_host(host):
                self.send_error(404)
                return
            raw = self._read_body()
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                data = {}
            if not isinstance(data, dict):
                data = {}
            authed = admin_session_ok(self._cookie())
            code, payload = run_web_notify_test(data, authenticated=authed)
            self._json(code, payload)

        def do_OPTIONS(self):
            # Meta Sharing Debugger sends OPTIONS first; an empty 200 is
            # treated as a failed scrape (shown as 403 / robots).
            self.do_GET()

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            redirect = status_request_redirect(self.path)
            if redirect is not None:
                self.send_response(302)
                self.send_header("Location", redirect)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            parsed = urllib.parse.urlparse(self.path)
            host = self._host()
            decision = admin_host_request(host, parsed.path, cookie=self._cookie())
            if decision == "not_found":
                self.send_error(404)
                return
            if decision == "login_required":
                self.send_response(302)
                self.send_header("Location", "/login")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            if parsed.path == "/robots.txt":
                self._bytes(
                    200,
                    "text/plain; charset=utf-8",
                    robots_txt().encode("utf-8"),
                )
                return
            if parsed.path == "/sitemap.xml":
                self._bytes(
                    200,
                    "application/xml; charset=utf-8",
                    sitemap_xml().encode("utf-8"),
                    cache="public, max-age=300",
                )
                return
            if parsed.path == "/manifest.webmanifest":
                self._bytes(
                    200,
                    "application/manifest+json; charset=utf-8",
                    web_manifest().encode("utf-8"),
                    cache="public, max-age=3600",
                )
                return
            if parsed.path in STATIC_PNGS:
                full = STATIC_PNGS[parsed.path]
                if not os.path.isfile(full):
                    self.send_error(404)
                    return
                with open(full, "rb") as fh:
                    body = fh.read()
                ctype = "image/jpeg" if full.endswith(".jpg") else "image/png"
                self._bytes(200, ctype, body, cache=IMAGE_CACHE_CONTROL)
                return
            go = parse_go_path(parsed.path) or go_shop_landing_id(parsed.path)
            if go:
                self._serve_go(parsed)
                return
            if parsed.path.startswith("/images/"):
                rel = urllib.parse.unquote(parsed.path.lstrip("/"))
                full = os.path.realpath(os.path.join(DATA_DIR, rel))
                root = os.path.realpath(os.path.join(DATA_DIR, "images"))
                if not (full == root or full.startswith(root + os.sep)) or not os.path.isfile(full):
                    self.send_error(404)
                    return
                with open(full, "rb") as fh:
                    body = fh.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("X-Robots-Tag", "noindex, nofollow")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", IMAGE_CACHE_CONTROL)
                self.end_headers()
                self.wfile.write(body)
                return
            from catalog_pages import handle_catalog_http

            catalog_hit = (
                parsed.path in ("/catalog", "/parts", "/collection", "/browser", "/browser/")
                or parsed.path.startswith("/catalog/")
                or parsed.path.startswith("/parts/")
                or parsed.path.startswith("/parts-images/")
            )
            if catalog_hit:
                result = handle_catalog_http(parsed.path, parsed.query)
                if not result or result.get("status") == 404:
                    self.send_error(404)
                    return
                if result.get("file"):
                    with open(result["file"], "rb") as fh:
                        body = fh.read()
                    ctype = result.get("content_type") or "image/jpeg"
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("X-Robots-Tag", "noindex, nofollow")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", IMAGE_CACHE_CONTROL)
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(body)
                    return
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    (result.get("html") or "").encode("utf-8"),
                    cache=result.get("cache") or HTML_CACHE_CONTROL,
                )
                return
            if parsed.path == "/history":
                qs = urllib.parse.parse_qs(parsed.query)
                shop_id = (qs.get("shop") or [""])[0]
                model = (qs.get("model") or [""])[0]
                cache_key = parsed.path + "?" + parsed.query

                def _history_page():
                    shops = shop_chip_shops()
                    rows = filter_index_notifies(
                        load_notify_history(
                            limit=INDEX_NOTIFY_SCAN, shop_id=shop_id, model=model, shops=shops
                        ),
                        in_stock_only=False,
                    )
                    return render_history_html(
                        rows, shops=shops, shop_id=shop_id, model=model
                    ).encode("utf-8")

                body = cached_bytes(cache_key, _history_page)
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                    robots="noindex, nofollow",
                )
                return
            if parsed.path == "/login":
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    render_admin_login_html().encode("utf-8"),
                    cache="no-store",
                    robots="noindex, nofollow",
                )
                return
            if parsed.path == "/notify-test":
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    render_notify_test_html().encode("utf-8"),
                    cache="no-store",
                )
                return
            if parsed.path in ("/status.json", "/json"):
                payload = build_watcher_status()
                body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/shop/"):
                shop_id = urllib.parse.unquote(parsed.path[len("/shop/"):].strip("/"))
                meta = shop_page_meta(shop_id)
                if not meta:
                    self.send_error(404)
                    return
                stock_filter = stock_filter_from_query(parsed.query)
                tag_filter = tag_filter_from_query(parsed.query)
                cache_key = parsed.path + "?" + parsed.query

                def _shop_page():
                    return render_products_html(
                        meta,
                        load_shop_products_for_shop_id(shop_id),
                        stock_filter=stock_filter,
                        tag_filter=tag_filter,
                        shops=shop_chip_shops(),
                    ).encode("utf-8")

                body = cached_bytes(cache_key, _shop_page)
                robots = None if not stock_filter and not tag_filter else "noindex, nofollow"
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                    robots=robots,
                )
                return
            if parsed.path == "/history":
                qs = urllib.parse.parse_qs(parsed.query)
                shop_id = (qs.get("shop") or [""])[0]
                model = (qs.get("model") or [""])[0]
                shops = shop_chip_shops()
                cache_key = parsed.path + "?" + parsed.query

                def _history_page():
                    return render_history_html(
                        filter_index_notifies(
                            load_notify_history(
                                limit=INDEX_NOTIFY_SCAN,
                                shop_id=shop_id,
                                model=model,
                                shops=shops,
                            ),
                            in_stock_only=False,
                        ),
                        shops=shops,
                        shop_id=shop_id,
                        model=model,
                    ).encode("utf-8")

                body = cached_bytes(cache_key, _history_page)
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                    robots="noindex, nofollow",
                )
                return
            if parsed.path == "/shops":
                body = cached_bytes(
                    parsed.path,
                    lambda: render_shops_html(payload=build_watcher_status()).encode("utf-8"),
                )
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                )
                return
            if parsed.path == "/coffee":
                body = cached_bytes(
                    parsed.path,
                    lambda: render_coffee_html().encode("utf-8"),
                )
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                    robots="noindex, nofollow",
                )
                return
            if parsed.path == SUBSCRIBE_PATH:
                body = cached_bytes(
                    parsed.path,
                    lambda: render_subscribe_html().encode("utf-8"),
                )
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                )
                return
            if parsed.path in (PRIVACY_PATH, PRIVACY_ALIAS_PATH):
                body = cached_bytes(
                    PRIVACY_PATH,
                    lambda: render_privacy_html().encode("utf-8"),
                )
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                )
                return
            if parsed.path in (TERMS_PATH, TERMS_ALIAS_PATH):
                body = cached_bytes(
                    TERMS_PATH,
                    lambda: render_terms_html().encode("utf-8"),
                )
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    body,
                    cache=HTML_CACHE_CONTROL,
                )
                return
            if parsed.path in (OG_TEST_PATH, OG_GOAL_PATH):
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    render_og_test_html(parsed.path).encode("utf-8"),
                    cache="private, no-store",
                )
                return
            if parsed.path not in ("/", "/status", "/index.html", "/watch", OG_HOME_PATH):
                self.send_error(404)
                return
            ua = self.headers.get("User-Agent") or ""
            if is_preview_crawler(ua):
                self._bytes(
                    200,
                    "text/html; charset=utf-8",
                    render_share_card_html().encode("utf-8"),
                    cache="private, no-store",
                )
                return
            body = cached_bytes(
                parsed.path,
                lambda: render_status_html(build_watcher_status()).encode("utf-8"),
            )
            self._bytes(
                200,
                "text/html; charset=utf-8",
                body,
                cache=HTML_CACHE_CONTROL,
            )

    server = ThreadingHTTPServer((cfg["host"], cfg["port"]), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    start_listing_watch_loop()
    print("Status page on port %s" % cfg["port"], flush=True)
    return server


def serve_forever(config_path=None):
    os.environ.setdefault("BEYBLADE_CDN_ORIGIN", "local")
    if config_path:
        if os.path.isfile(config_path):
            apply_config(load_config(config_path))
        else:
            apply_config({})
    import site_data

    st = dict((site_data.CONFIG or {}).get("status") or {})
    st["enabled"] = True
    host = str(st.get("host") or "127.0.0.1")
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    st["host"] = host
    st["port"] = int(st.get("port") or 8080)
    cfg = dict(site_data.CONFIG or {})
    cfg["status"] = st
    apply_config(cfg)
    try:
        server = start_status_server()
    except OSError:
        st["port"] = 8765
        cfg["status"] = st
        apply_config(cfg)
        server = start_status_server()
    if server is None:
        print("status server did not start", file=sys.stderr)
        return 1
    print("Catalog: http://%s:%s/catalog" % (st["host"], st["port"]), flush=True)
    print("Browser: http://%s:%s/browser" % (st["host"], st["port"]), flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.shutdown()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the Beyblade status/catalog site locally"
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="JSON watch config")
    args = parser.parse_args(argv)
    return serve_forever(args.config)


if __name__ == "__main__":
    sys.exit(main() or 0)
