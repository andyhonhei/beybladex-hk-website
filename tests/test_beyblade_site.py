import json
import os
import re
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from site_data import (
    DISCORD_INVITE_URL,
    GO_CACHE_CONTROL,
    HTML_CACHE_CONTROL,
    HTML_CACHE_TAG,
    IMAGE_CACHE_CONTROL,
    TELEGRAM_INVITE_URL,
    THREADS_SUBSCRIBE_ASK,
    admin_credentials_ok,
    admin_host_request,
    admin_session_ok,
    admin_session_token,
    apply_config,
    cached_bytes,
    display_status_shops,
    filter_index_notifies,
    filter_notify_history,
    explore_href,
    explore_http_result,
    go_href,
    go_http_result,
    go_page_target,
    go_target_from_item,
    group_listings_by_model,
    is_admin_host,
    is_preview_crawler,
    listing_model_code,
    listing_state_fingerprint,
    load_config,
    load_notify_history,
    load_shop_products_for_shop_id,
    mysql_ok_cached,
    parse_go_path,
    product_path_redirect,
    shop_list_redirect,
    prune_edge_purge_log,
    purge_edge_cache,
    request_edge_purge,
    reset_edge_purge_state,
    probe_go_url,
    product_image_path,
    refresh_status_pages_if_listings_changed,
    reset_status_caches,
    run_web_notify_test,
    shop_chip_shops,
    shop_page_meta,
    shop_products_from_state,
    sources_for_shop_page,
    status_request_redirect,
    wrap_notify_item_links,
)
from site_pages import (
    notify_rows_html,
    privacy_page_url,
    product_card_html,
    product_thumb_html,
    render_admin_login_html,
    render_coffee_html,
    render_go_bounce_html,
    render_go_html,
    render_history_html,
    render_models_html,
    render_not_found_html,
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
    shop_chips_html,
    site_footer_html,
    site_nav_html,
    sitemap_xml,
    subscribe_page_url,
    subscribe_widget_html,
    terms_page_url,
    web_manifest,
)


class SiteCliTests(unittest.TestCase):
    def test_module_imports_serve_forever(self):
        import beyblade_site

        self.assertTrue(callable(beyblade_site.serve_forever))

    def test_serve_forever_status_overlay_keeps_shop_sources(self):
        import beyblade_site
        import site_data
        from site_data import CONFIG as imported_config

        apply_config(
            {
                "sources": [{"id": "hobbyland", "label": "Hobbyland"}],
                "storage": {"mysql": {"enabled": True, "database": "hobbyland_watch"}},
                "status": {"host": "127.0.0.1", "port": 8080},
            }
        )
        self.assertIs(imported_config, site_data.CONFIG)
        st = dict((site_data.CONFIG or {}).get("status") or {})
        st["enabled"] = True
        if st.get("host") in ("0.0.0.0", "::"):
            st["host"] = "127.0.0.1"
        cfg = dict(site_data.CONFIG or {})
        cfg["status"] = st
        apply_config(cfg)
        self.assertEqual(
            [s.get("id") for s in (imported_config.get("sources") or [])],
            ["hobbyland"],
        )
        self.assertTrue(site_data.mysql_settings().get("enabled"))
        self.assertTrue(callable(beyblade_site.serve_forever))

    def test_site_pages_has_home_html(self):
        from site_pages import render_status_html
        html = render_status_html({"shops": [], "updated_at": ""})
        self.assertIn("<", html)

    def test_home_does_not_show_scanning_rules_panel(self):
        from site_pages import render_status_html

        apply_config(
            {
                "filter": {
                    "phrases": ["beyblade", "陀螺"],
                    "line_codes": ["UX", "CX", "BX"],
                    "skip_phrases": ["無限邂逅", "MegaloMaria", "Tomica"],
                },
                "sources": [],
            }
        )
        html = render_status_html({"shops": [], "checked_at": "2026-09-08 03:00:00"})
        self.assertNotIn("掃描規則", html)
        self.assertNotIn("只跟進標題含", html)

    def test_site_data_mysql_settings_keys(self):
        import site_data
        site_data.apply_config({"storage": {"mysql": {"enabled": True, "database": "beyblade_watch"}}})
        s = site_data.mysql_settings()
        self.assertEqual(s["database"], "beyblade_watch")
        self.assertTrue(s["enabled"])



class StatusPageTests(unittest.TestCase):
    def test_subscribe_dropdown_lists_telegram_discord_threads(self):
        markup = subscribe_widget_html("訂閱")
        names = re.findall(r'class="subscribe-name">([^<]+)', markup)
        self.assertEqual(names, ["Telegram", "Discord", "Threads"])
        self.assertIn(explore_href("https://t.me/+mbTPVeGFBalhMjQ9"), markup)
        self.assertIn(explore_href("https://discord.gg/C8Q5gZf3y5"), markup)
        self.assertIn(explore_href("https://www.threads.com/@hkbeybladex_com"), markup)
        self.assertIn("香港爆旋陀螺到貨通知", markup)
        self.assertIn('<a href="/shops">Online舖頭</a>', markup)
        self.assertNotIn("本地舖頭", markup)
        self.assertIn("訂閱／鐘仔", markup)

    def test_shops_page_uses_index_status_table(self):
        page = render_shops_html(
            {
                "sources": [
                    {
                        "id": "cuapp",
                        "label": "CU APP",
                        "origin": "https://eshop.cuapp.com",
                        "enabled": True,
                    }
                ]
            },
            payload={
                "checked_at": "2026-08-30 14:00:00",
                "ok": True,
                "shops": [
                    {
                        "id": "cuapp",
                        "label": "CU APP",
                        "sku_count": 10,
                        "in_stock": 3,
                        "out_of_stock": 7,
                        "updated_at": "2026-08-30 13:00:00",
                        "error": None,
                    }
                ],
            },
        )
        self.assertIn('<h1 class="page-title">店舖現況</h1>', page)
        self.assertIn('<a href="/shops">店舖現況</a>', page)
        self.assertNotIn("<th>網站</th>", page)
        self.assertNotIn("https://eshop.cuapp.com", page)
        self.assertIn("href='/product?shop=cuapp'", page)
        self.assertNotIn("/shop/cuapp", page)
        self.assertIn("index, follow", page)
        self.assertIn(
            'name="keywords" content="店舖現況, HobbyDigi, BuyMarketToy, MoonroadHK, Takara Tomy Mall, 爆旋陀螺現貨, 爆旋陀螺開訂, beyblade x, 陀螺, 戰鬥陀螺, hkbeybladex"',
            page,
        )
        self.assertNotIn("Beyblade X restock HK", page)
        self.assertIn("<th>商店</th>", page)
        self.assertIn("<th>狀態</th>", page)
        self.assertIn("<th>SKU</th>", page)
        self.assertIn("<th>有貨</th>", page)
        self.assertIn("<th>缺貨</th>", page)
        self.assertNotIn("<th>最後更新時間</th>", page)
        self.assertNotIn("2026-08-30 13:00:00", page)
        self.assertNotIn("2026-08-30 14:00:00", page)
        self.assertNotIn("HKT", page)
        self.assertNotIn("<th>錯誤</th>", page)
        self.assertIn(">10</td>", page)
        self.assertIn("整體", page)
        admin = render_shops_html(
            {
                "sources": [
                    {
                        "id": "cuapp",
                        "label": "CU APP",
                        "origin": "https://eshop.cuapp.com",
                        "enabled": True,
                    }
                ]
            },
            payload={
                "checked_at": "2026-08-30 14:00:00",
                "ok": True,
                "shops": [
                    {
                        "id": "cuapp",
                        "label": "CU APP",
                        "sku_count": 10,
                        "in_stock": 3,
                        "out_of_stock": 7,
                        "updated_at": "2026-08-30 13:00:00",
                        "error": None,
                    }
                ],
            },
            show_updated=True,
        )
        self.assertIn("<th>最後更新時間</th>", admin)
        self.assertIn("2026-08-30 13:00:00", admin)
        self.assertIn("更新 2026-08-30 14:00:00 HKT", admin)
        self.assertIn('content="noindex, nofollow"', admin)
        self.assertIn("/shopslist", admin)
        self.assertNotIn("cms107", admin)
        self.assertNotIn("Website list", page)
        self.assertNotIn("Status live", page)
        self.assertIn("<h2>香港店舖</h2>", page)
        self.assertNotIn("<h2>海外店舖</h2>", page)

    def test_shopslist_marks_overseas_stores_in_chinese(self):
        page = render_shops_html(
            {
                "sources": [
                    {"id": "cuapp", "label": "CU APP", "enabled": True},
                    {"id": "takaratomymall", "label": "Takara Tomy Mall", "enabled": True},
                ]
            },
            payload={
                "checked_at": "2026-11-13 21:00:00",
                "ok": True,
                "shops": [
                    {"id": "cuapp", "label": "CU APP", "sku_count": 2, "in_stock": 1, "out_of_stock": 1},
                    {
                        "id": "takaratomymall",
                        "label": "Takara Tomy Mall",
                        "sku_count": 24,
                        "in_stock": 16,
                        "out_of_stock": 8,
                    },
                ],
            },
            show_updated=True,
        )
        self.assertLess(page.find("<h2>香港店舖</h2>"), page.find("CU APP"))
        self.assertLess(page.find("CU APP"), page.find("<h2>海外店舖</h2>"))
        self.assertLess(page.find("<h2>海外店舖</h2>"), page.find("Takara Tomy Mall"))
        self.assertIn("/shopslist", page)
        chips = shop_chips_html(
            [
                {"id": "cuapp", "label": "CU APP"},
                {"id": "takaratomymall", "label": "Takara Tomy Mall"},
            ]
        )
        self.assertLess(chips.find("CU APP"), chips.find("海外店舖"))
        self.assertLess(chips.find("海外店舖"), chips.find("Takara Tomy Mall"))

    def test_hidden_japan_shops_stay_off_the_public_shop_list(self):
        cfg = {
            "sources": [
                {"id": "takaratomymall", "label": "Takara Tomy Mall", "enabled": True},
                {
                    "id": "biccamera",
                    "label": "Bic Camera",
                    "enabled": False,
                    "hidden": True,
                },
                {
                    "id": "yodobashi",
                    "label": "Yodobashi",
                    "enabled": False,
                    "hidden": True,
                },
            ]
        }
        payload = {
            "checked_at": "2026-11-15 03:00:00",
            "ok": True,
            "shops": [
                {"id": "takaratomymall", "label": "Takara Tomy Mall", "sku_count": 2},
                {"id": "biccamera", "label": "Bic Camera", "sku_count": 3},
                {"id": "yodobashi", "label": "Yodobashi", "sku_count": 4},
            ],
        }
        rows = display_status_shops(payload["shops"], cfg)
        self.assertEqual([row["id"] for row in rows], ["all", "takaratomymall"])
        self.assertIsNone(shop_page_meta("biccamera", cfg))
        self.assertIsNone(shop_page_meta("yodobashi", cfg))
        page = render_shops_html(cfg, payload, show_updated=True)
        self.assertIn("Takara Tomy Mall", page)
        self.assertNotIn("Bic Camera", page)
        self.assertNotIn("Yodobashi", page)

    def test_test_shop_shows_only_on_shopslist(self):
        cfg = {
            "sources": [
                {"id": "cuapp", "label": "CU APP", "enabled": True},
                {
                    "id": "1999jp",
                    "label": "1999.jp",
                    "origin": "https://www.1999.co.jp",
                    "region": "jp",
                    "enabled": True,
                    "test": True,
                },
            ]
        }
        payload = {
            "checked_at": "2026-11-15 03:00:00",
            "ok": True,
            "shops": [
                {"id": "cuapp", "label": "CU APP", "sku_count": 2, "in_stock": 1, "out_of_stock": 1},
                {"id": "1999jp", "label": "1999.jp", "sku_count": 4, "in_stock": 1, "out_of_stock": 3},
            ],
        }
        public = render_shops_html(cfg, payload, show_updated=False)
        admin = render_shops_html(cfg, payload, show_updated=True)
        self.assertIn("CU APP", public)
        self.assertNotIn("1999.jp", public)
        self.assertIn("/shops", public)
        self.assertIn("1999.jp", admin)
        self.assertIn("/shopslist", admin)
        self.assertIn("/product?shop=1999jp", admin)
        self.assertEqual(shop_page_meta("1999jp", cfg)["label"], "1999.jp")
        chips = shop_chip_shops(cfg)
        self.assertIn("1999jp", [row["id"] for row in chips])
        product = render_models_html(
            [
                {
                    "sku": "11335022",
                    "shop_id": "1999jp",
                    "shop_label": "1999.jp",
                    "title": "BX-01 Dran Sword",
                    "model": "BX-01",
                    "tag": "BX",
                    "price": "1980",
                    "status": "in_stock",
                    "url": "https://www.1999.co.jp/11335022",
                }
            ],
            shops=chips,
        )
        self.assertIn("1999.jp", product)
        self.assertIn('href="/product?shop=1999jp"', product)
        self.assertIn("BX-01 Dran Sword", product)

    def test_nav_includes_history_button(self):
        nav = site_nav_html()
        self.assertIn('id="site-nav-drawer"', nav)
        self.assertIn('<a href="/history">最新通知</a>', nav)
        self.assertNotIn(">通知歷史</a>", nav)
        self.assertNotIn('href="/catalog"', nav)
        self.assertNotIn('href="/collection"', nav)

    def test_coffee_page_is_hidden_from_nav_and_footer(self):
        apply_config({"status": {"coffee": True}})
        self.assertNotIn("/coffee", site_nav_html())
        self.assertNotIn("/coffee", site_footer_html())
        self.assertNotIn("Allow: /coffee", robots_txt())
        self.assertNotIn("/coffee", sitemap_xml({"sources": []}))
        page = render_status_html(
            {"checked_at": "2026-08-26 19:00:00", "ok": True, "shops": []},
            notifies=[],
        )
        self.assertNotIn('href="/coffee"', page)

    def test_unknown_url_is_a_branded_404_page(self):
        page = render_not_found_html()
        self.assertIn("找不到頁面", page)
        self.assertIn("HK BEYBLADEX.COM", page)
        self.assertIn("呢個網址冇對應頁面", page)
        self.assertIn('href="/"', page)
        self.assertIn("noindex, nofollow", page)
        self.assertNotIn("倉庫", page)

        import beyblade_site

        apply_config(
            {"status": {"enabled": True, "host": "127.0.0.1", "port": 18764}}
        )
        server = beyblade_site.start_status_server()
        try:
            class _Keep(urllib.request.HTTPErrorProcessor):
                def http_response(self, request, response):
                    return response

                https_response = http_response

            opener = urllib.request.build_opener(_Keep)
            response = opener.open("http://127.0.0.1:18764/this-page-does-not-exist")
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 404)
            self.assertIn("找不到頁面", body)
            self.assertIn("noindex", response.headers.get("X-Robots-Tag", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_coffee_page_explains_free_project_and_costs(self):
        page = render_coffee_html()
        self.assertIn("請我飲杯咖啡", page)
        self.assertIn("完全免費", page)
        self.assertIn("伺服器", page)
        self.assertIn("開發", page)
        self.assertIn("心機", page)
        self.assertIn("<details", page)
        self.assertIn("PayMe", page)
        self.assertIn(explore_href("https://payme.hsbc/andyhuihh"), page)
        self.assertIn("AlipayHK", page)
        self.assertIn("/alipayhk.jpg", page)
        self.assertNotIn("buymeacoffee", page)
        self.assertIn("noindex, nofollow", page)
        self.assertNotIn('href="/coffee"', site_nav_html())

    def test_subscribe_page_lists_channels_and_is_hidden_from_nav(self):
        page = render_subscribe_html()
        self.assertIn("訂閱通知", page)
        self.assertIn(explore_href("https://t.me/+mbTPVeGFBalhMjQ9"), page)
        self.assertIn(explore_href("https://discord.gg/C8Q5gZf3y5"), page)
        self.assertIn(explore_href("https://www.threads.com/@hkbeybladex_com"), page)
        self.assertIn("加入群組", page)
        self.assertIn("加入頻道", page)
        self.assertIn("鐘仔", page)
        self.assertNotIn("/subscribe", site_nav_html())
        self.assertNotIn("/subscribe", site_footer_html())
        self.assertEqual(subscribe_page_url(), "https://hkbeybladex.com/subscribe")

    def test_privacy_page_explains_data_use_for_meta(self):
        page = render_privacy_html()
        self.assertIn("Privacy Policy", page)
        self.assertIn("Google Analytics", page)
        self.assertIn("Threads", page)
        self.assertIn("Telegram", page)
        self.assertIn("Discord", page)
        self.assertIn("We do not sell personal data", page)
        self.assertNotIn("bxw_go_skip", page)
        self.assertNotIn("Hop-page preference", page)
        self.assertIn("私隱政策", page)
        self.assertEqual(
            privacy_page_url(),
            "https://hkbeybladex.com/privacy",
        )
        self.assertIn('href="/privacy"', site_footer_html())
        self.assertNotIn("/privacy", site_nav_html())

    def test_terms_page_explains_use_for_meta(self):
        page = render_terms_html()
        self.assertIn("Terms of Service", page)
        self.assertIn("not affiliated", page)
        self.assertIn("Threads", page)
        self.assertIn("Telegram", page)
        self.assertIn("Discord", page)
        self.assertIn("No warranty", page)
        self.assertIn("/privacy", page)
        self.assertIn("服務條款", page)
        self.assertEqual(
            terms_page_url(),
            "https://hkbeybladex.com/terms",
        )
        self.assertIn('href="/terms"', site_footer_html())
        self.assertNotIn("/terms", site_nav_html())

    def test_pages_include_google_analytics_gtag(self):
        page = render_status_html(
            {"checked_at": "2026-08-26 19:00:00", "ok": True, "shops": []},
            notifies=[],
        )
        self.assertIn(
            "https://www.googletagmanager.com/gtag/js?id=G-19VVZP9R25",
            page,
        )
        self.assertIn("gtag('config', 'G-19VVZP9R25');", page)

    def test_pages_include_ga_standard_event_script(self):
        page = render_status_html(
            {"checked_at": "2026-08-26 19:00:00", "ok": True, "shops": []},
            notifies=[],
        )
        self.assertIn('gtag("event","select_item"', page)
        self.assertIn('gtag("event","generate_lead"', page)
        self.assertIn(".subscribe-method,.coffee-cta", page)
        self.assertIn('gtag("event","view_item_list"', page)
        self.assertIn('data-method="Telegram"', page)
        self.assertIn('data-method="Discord"', page)
        self.assertIn('data-method="Threads"', page)

    def test_html_shows_shop_counts_and_health(self):
        page = render_status_html(
            {
                "checked_at": "2026-08-26 19:00:00",
                "ok": True,
                "mysql": True,
                "shops": [
                    {
                        "id": "animepro",
                        "label": "AnimesPro",
                        "sku_count": 32,
                        "in_stock": 0,
                        "out_of_stock": 32,
                        "updated_at": "2026-08-26 19:00:00",
                        "error": None,
                    }
                ],
            }
        )
        self.assertIn("AnimesPro", page)
        self.assertIn("全部", page)
        self.assertIn("/shop/all", page)
        self.assertIn("32", page)
        self.assertIn("正常", page)
        self.assertNotIn("MySQL", page)
        self.assertNotIn("EC2", page)
        self.assertNotIn("#128a3e", page)
        self.assertIn("href='/product?shop=animepro'", page)
        self.assertNotIn("/shop/animepro", page)
        self.assertIn('id="site-nav-menu-btn"', page)
        self.assertIn('href="/shop/all?stock=in"', page)
        self.assertIn("全部現貨", page)
        self.assertIn('class="site-nav"', page)
        self.assertEqual(page.count(">訂閱通知</button>"), 3)
        self.assertIn('id="subscribe-btn"', page)
        self.assertIn('id="subscribe-hero-btn"', page)
        self.assertNotIn(">/\\\\-_ =+|  beybladex  |+= _-/\\\\</button>", page)
        self.assertIn('class="ascii"', page)
        self.assertIn(explore_href("https://discord.gg/C8Q5gZf3y5"), page)
        self.assertIn(explore_href("https://www.threads.com/@hkbeybladex_com"), page)
        self.assertIn(explore_href("https://t.me/+mbTPVeGFBalhMjQ9"), page)
        self.assertIn("subscribe-method", page)
        self.assertIn("Threads", page)
        self.assertIn("Discord", page)
        self.assertIn("Telegram", page)
        self.assertIn("香港爆旋陀螺到貨通知", page)
        self.assertIn("Online舖頭", page)
        self.assertNotIn("本地舖頭", page)
        self.assertIn('<a href="/shops">Online舖頭</a>', page)
        self.assertIn('<a href="/shops">店舖現況</a>', page)
        self.assertIn('<h2><a href="/shops">店舖現況</a></h2>', page)
        self.assertNotIn("Status live", page)
        self.assertIn("Hong Kong · Threads / Discord / Telegram alerts", page)
        self.assertIn(".subscribe > button{background:#fff;color:var(--blue)", page)
        self.assertIn(".subscribe-list{display:none;position:absolute;right:0;top:calc(100% + 8px);min-width:280px;\nbackground:#fff;color:var(--blue)", page)
        self.assertIn('name="robots"', page)
        self.assertIn("index, follow", page)
        self.assertNotIn("noindex, nofollow", page)
        self.assertNotIn('http-equiv="refresh"', page)
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/share"',
            page,
        )
        self.assertIn(
            'rel="canonical" href="https://hkbeybladex.com/share"',
            page,
        )
        self.assertIn("/og-card.jpg", page)
        self.assertNotIn('id="menu-btn"', page)
        self.assertNotIn('id="discord-test-btn"', page)
        self.assertNotIn('id="telegram-test-btn"', page)
        self.assertNotIn("/notify-test", page)
        self.assertNotIn("notify-btn", page)
        self.assertNotIn("Chrome alerts", page)
        self.assertIn("install-hint", page)
        self.assertIn("加入主畫面", page)
        self.assertIn("開首頁", page)
        self.assertIn("bxw-install-visits", page)
        self.assertIn("id=\"install-dismiss\"", page)
        self.assertIn("/logo.png", page)
        self.assertNotIn("/seo-image.png", page)
        self.assertIn('rel="icon"', page)
        self.assertIn("/favicon.ico", page)
        self.assertNotIn("hero-blade", page)
        self.assertIn("--blue:#1a1aff", page)
        self.assertIn('class="brand-mark"', page)
        self.assertIn('class="brand-name"', page)
        self.assertIn(">HK BeybladeX Watch</span>", page)
        self.assertIn('letter-spacing:.04em;text-transform:uppercase;color:#fff!important}', page)
        self.assertIn("<title>HK BeybladeX Watch</title>", page)
        self.assertNotIn("最後更新時間", page)
        self.assertNotIn("2026-08-26 19:00:00", page)
        self.assertNotIn("最後寫入", page)
        self.assertNotIn("nav.site-nav{flex-wrap:wrap", page)
        self.assertNotIn(".nav-end{width:100%", page)
        self.assertIn(".brand-name{display:none}", page)
        self.assertIn("position:fixed", page)

    def test_preview_crawler_gets_share_card_without_product_thumbs(self):
        self.assertTrue(is_preview_crawler("facebookexternalhit/1.1"))
        self.assertTrue(is_preview_crawler("TelegramBot (like TwitterBot)"))
        self.assertFalse(is_preview_crawler("Mozilla/5.0"))
        page = render_share_card_html()
        self.assertIn(
            'rel="canonical" href="https://hkbeybladex.com/share"',
            page,
        )
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/share"',
            page,
        )
        self.assertIn("/og-card.jpg", page)
        self.assertIn('property="og:image:type" content="image/jpeg"', page)
        self.assertNotIn("/images/", page)
        self.assertNotIn("最新通知", page)

    def test_og_test_page_is_self_canonical_with_unique_title(self):
        page = render_og_test_html()
        self.assertIn(
            'rel="canonical" href="https://hkbeybladex.com/og-test-20260830"',
            page,
        )
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/og-test-20260830"',
            page,
        )
        self.assertIn("OG probe 20260830", page)
        self.assertIn("/og-card.jpg?v=og-test-20260830", page)
        self.assertNotIn("最新通知", page)
        goal = render_og_test_html("/goal")
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/goal"',
            goal,
        )
        self.assertIn("BeybladeX Watch goal card", goal)

    def test_status_stock_counts_link_when_positive(self):
        page = render_status_html(
            {
                "checked_at": "2026-08-27 16:00:00",
                "ok": True,
                "shops": [
                    {
                        "id": "lastchance",
                        "label": "LastChanceToy",
                        "sku_count": 5,
                        "in_stock": 3,
                        "out_of_stock": 2,
                        "updated_at": "2026-08-27 16:00:00",
                        "error": None,
                    },
                    {
                        "id": "animepro",
                        "label": "AnimesPro",
                        "sku_count": 10,
                        "in_stock": 0,
                        "out_of_stock": 10,
                        "updated_at": "2026-08-27 16:00:00",
                        "error": None,
                    },
                ],
            }
        )
        self.assertIn("href='/product'", page)
        self.assertIn("href='/product?stock=in'", page)
        self.assertIn("href='/product?stock=out'", page)
        self.assertIn("href='/product?shop=lastchance'", page)
        self.assertIn("href='/product?stock=in&amp;shop=lastchance'", page)
        self.assertIn("href='/product?stock=out&amp;shop=lastchance'", page)
        self.assertIn("href='/product?shop=animepro'", page)
        self.assertIn("href='/product?stock=out&amp;shop=animepro'", page)
        self.assertNotIn("href='/product?stock=in&amp;shop=animepro'", page)
        self.assertNotIn("/shop/lastchance", page)
        self.assertNotIn("/shop/animepro", page)

    def test_hobbyland_sources_share_one_website_and_all_row(self):
        cfg = {
            "sources": [
                {
                    "id": "hobbyland",
                    "label": "Hobbyland",
                    "origin": "https://www.hobbylandeshop.com",
                    "enabled": True,
                },
                {
                    "id": "hobbyland-beyblade",
                    "label": "HobbylandBeyblade",
                    "origin": "https://www.hobbylandeshop.com",
                    "enabled": True,
                },
                {
                    "id": "toysrus",
                    "label": "ToysRUs",
                    "origin": "https://www.toysrus.com.hk",
                    "enabled": True,
                },
            ]
        }
        ids = [source.get("id") for source in sources_for_shop_page("hobbyland", cfg)]
        self.assertEqual(ids, ["hobbyland", "hobbyland-beyblade"])
        self.assertEqual(
            [source.get("id") for source in sources_for_shop_page("hobbyland-beyblade", cfg)],
            ["hobbyland", "hobbyland-beyblade"],
        )
        self.assertEqual(shop_page_meta("hobbyland-beyblade", cfg)["id"], "hobbyland")
        self.assertEqual(shop_page_meta("hobbyland-beyblade", cfg)["label"], "Hobbyland")
        self.assertEqual(shop_page_meta("all", cfg)["id"], "all")
        self.assertEqual(shop_page_meta("all", cfg)["label"], "全部")
        all_ids = [source.get("id") for source in sources_for_shop_page("all", cfg)]
        self.assertEqual(all_ids, ["hobbyland", "hobbyland-beyblade", "toysrus"])
        rows = display_status_shops(
            [
                {
                    "id": "hobbyland",
                    "label": "Hobbyland",
                    "sku_count": 2,
                    "in_stock": 1,
                    "out_of_stock": 1,
                    "updated_at": "2026-08-27 10:00:00",
                    "error": None,
                    "enabled": True,
                },
                {
                    "id": "hobbyland-beyblade",
                    "label": "HobbylandBeyblade",
                    "sku_count": 3,
                    "in_stock": 2,
                    "out_of_stock": 1,
                    "updated_at": "2026-08-28 00:00:00",
                    "error": None,
                    "enabled": True,
                },
                {
                    "id": "toysrus",
                    "label": "ToysRUs",
                    "sku_count": 4,
                    "in_stock": 0,
                    "out_of_stock": 4,
                    "updated_at": "2026-08-27 12:00:00",
                    "error": None,
                    "enabled": True,
                },
            ],
            cfg,
        )
        self.assertEqual([row["id"] for row in rows], ["all", "hobbyland", "toysrus"])
        self.assertEqual(rows[0]["label"], "全部")
        self.assertEqual(rows[0]["sku_count"], 9)
        self.assertEqual(rows[0]["in_stock"], 3)
        self.assertEqual(rows[1]["label"], "Hobbyland")
        self.assertEqual(rows[1]["sku_count"], 5)
        self.assertEqual(rows[1]["in_stock"], 3)
        self.assertNotIn("HobbylandBeyblade", [row["label"] for row in rows])
        apply_config(cfg)
        try:
            page = render_status_html(
                {
                    "checked_at": "2026-08-28 00:00:00",
                    "ok": True,
                    "shops": [
                        {
                            "id": "hobbyland",
                            "label": "Hobbyland",
                            "sku_count": 2,
                            "in_stock": 1,
                            "out_of_stock": 1,
                            "updated_at": "2026-08-27 10:00:00",
                            "error": None,
                            "enabled": True,
                        },
                        {
                            "id": "hobbyland-beyblade",
                            "label": "HobbylandBeyblade",
                            "sku_count": 3,
                            "in_stock": 2,
                            "out_of_stock": 1,
                            "updated_at": "2026-08-28 00:00:00",
                            "error": None,
                            "enabled": True,
                        },
                        {
                            "id": "toysrus",
                            "label": "ToysRUs",
                            "sku_count": 4,
                            "in_stock": 0,
                            "out_of_stock": 4,
                            "updated_at": "2026-08-27 12:00:00",
                            "error": None,
                            "enabled": True,
                        },
                    ],
                }
            )
        finally:
            apply_config(load_config())
        self.assertIn("Hobbyland", page)
        self.assertNotIn(">HobbylandBeyblade<", page)
        self.assertIn("/shop/all", page)
        self.assertIn("href='/product?shop=hobbyland'", page)
        self.assertNotIn("/shop/hobbyland", page)

    def test_hobbyland_products_use_website_name(self):
        cfg = {
            "sources": [
                {
                    "id": "hobbyland",
                    "label": "Hobbyland",
                    "origin": "https://www.hobbylandeshop.com",
                    "enabled": True,
                },
                {
                    "id": "hobbyland-beyblade",
                    "label": "HobbylandBeyblade",
                    "origin": "https://www.hobbylandeshop.com",
                    "enabled": True,
                },
                {
                    "id": "toysrus",
                    "label": "ToysRUs",
                    "origin": "https://www.toysrus.com.hk",
                    "enabled": True,
                },
            ]
        }
        import site_data as mod

        original = mod.load_shop_products_for_source

        def fake_load(source):
            return [
                {
                    "sku": source.get("id"),
                    "title": source.get("id"),
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                }
            ]

        mod.load_shop_products_for_source = fake_load
        try:
            items = load_shop_products_for_shop_id("all", cfg)
        finally:
            mod.load_shop_products_for_source = original
        labels = {item["sku"]: item.get("shop_label") for item in items}
        self.assertEqual(labels["hobbyland"], "Hobbyland")
        self.assertEqual(labels["hobbyland-beyblade"], "Hobbyland")
        self.assertEqual(labels["toysrus"], "ToysRUs")
        page = render_products_html(shop_page_meta("all", cfg), items)
        self.assertIn("Hobbyland", page)
        self.assertNotIn(">HobbylandBeyblade<", page)

    def test_all_product_cards_include_shop_name(self):
        card = product_card_html(
            {
                "sku": "1",
                "title": "CX-19",
                "shop_label": "ToysRUs",
                "status_label": "有貨",
            },
            "toysrus",
        )
        self.assertIn("ToysRUs", card)

    def test_product_card_has_ga_item_fields(self):
        card = product_card_html(
            {
                "sku": "1",
                "title": "CX-19",
                "price": "99.00",
                "url": "https://example.com/p",
                "shop_label": "ToysRUs",
            },
            "toysrus",
        )
        self.assertIn("data-name='CX-19'", card)
        self.assertIn("data-price='99.00'", card)
        self.assertIn("data-brand='ToysRUs'", card)

    def test_admin_credentials_are_checked_server_side(self):
        self.assertTrue(admin_credentials_ok("andyhhh", "Demo1234!"))
        self.assertFalse(admin_credentials_ok("andyhhh", "wrong"))
        self.assertFalse(admin_credentials_ok("other", "Demo1234!"))
        self.assertFalse(admin_credentials_ok("", "Demo1234!"))
        self.assertFalse(admin_credentials_ok("andyhhh", ""))

    def test_admin_session_token_is_not_the_password(self):
        token = admin_session_token()
        self.assertTrue(admin_session_ok(token))
        self.assertFalse(admin_session_ok("Demo1234!"))
        self.assertFalse(admin_session_ok(""))
        self.assertNotIn("Demo1234!", token)

    def test_admin_host_only_serves_admin_paths(self):
        self.assertTrue(is_admin_host("beybladex-admin.andyhhh.com"))
        self.assertTrue(is_admin_host("beybladex-admin.andyhhh.com:8080"))
        self.assertFalse(is_admin_host("hkbeybladex.com"))
        self.assertEqual(
            admin_host_request("hkbeybladex.com", "/notify-test"),
            "not_found",
        )
        self.assertEqual(
            admin_host_request("hkbeybladex.com", "/login"),
            "not_found",
        )
        self.assertEqual(
            admin_host_request("beybladex-admin.andyhhh.com", "/notify-test"),
            "login_required",
        )
        self.assertEqual(
            admin_host_request(
                "beybladex-admin.andyhhh.com",
                "/notify-test",
                cookie=admin_session_token(),
            ),
            "ok",
        )
        self.assertEqual(
            admin_host_request("beybladex-admin.andyhhh.com", "/login"),
            "ok",
        )
        self.assertEqual(
            admin_host_request("beybladex-admin.andyhhh.com", "/"),
            "login_required",
        )

    def test_login_and_notify_pages_do_not_contain_credentials(self):
        login = render_admin_login_html()
        notify = render_notify_test_html()
        self.assertIn("noindex, nofollow", login)
        self.assertIn("noindex, nofollow", notify)
        for page in (login, notify):
            self.assertNotIn("Demo1234!", page)
            self.assertNotIn("88888888", page)
            self.assertNotIn("unlock", page)
            self.assertNotIn("password:", page.lower().replace("type=\"password\"", ""))
        self.assertIn('name="username"', login)
        self.assertIn('name="password"', login)
        self.assertIn('method="post"', login)
        self.assertIn('action="/login"', login)
        self.assertNotIn("fetch(", login)
        self.assertIn('id="notify-message"', notify)
        self.assertIn('id="notify-send-all"', notify)
        self.assertIn('id="discord-test-btn"', notify)
        self.assertIn('id="telegram-test-btn"', notify)
        self.assertIn('id="threads-test-btn"', notify)
        self.assertNotIn("password", notify.lower())

    def test_notify_page_puts_send_actions_in_dropdown(self):
        notify = render_notify_test_html()
        self.assertIn('id="notify-actions-btn"', notify)
        self.assertIn(">Actions</button>", notify)
        self.assertIn('id="notify-actions-list"', notify)
        list_at = notify.find('id="notify-actions-list"')
        self.assertGreater(list_at, 0)
        self.assertGreater(notify.find('id="notify-send-all"', list_at), list_at)
        self.assertGreater(notify.find('id="discord-test-btn"', list_at), list_at)
        self.assertGreater(notify.find('id="telegram-test-btn"', list_at), list_at)
        self.assertGreater(notify.find('id="threads-test-btn"', list_at), list_at)
        self.assertIn('querySelectorAll(".subscribe")', notify)

    def test_web_notify_test_requires_session_and_message(self):
        code, body = run_web_notify_test({"channel": "all", "message": "hello"})
        self.assertEqual(code, 401)
        self.assertFalse(body.get("ok"))
        code, body = run_web_notify_test(
            {"channel": "all", "message": "  "}, authenticated=True
        )
        self.assertEqual(code, 400)
        self.assertFalse(body.get("ok"))

    def test_web_notify_test_sends_message_to_all_channels(self):
        discord = []
        telegram = []
        threads = []
        import site_data as mod

        apply_config(
            {
                "notify": {
                    "discord": {
                        "enabled": True,
                        "webhook_url": "https://discord.com/api/webhooks/live/xyz",
                    },
                    "telegram": {"enabled": True, "bot_token": "t", "chat_id": "1"},
                    "threads": {
                        "enabled": True,
                        "user_id": "123",
                        "access_token": "th",
                    },
                },
                "sources": [],
                "filter": {},
            }
        )
        original_dc = mod.post_discord
        original_tg = mod.post_telegram
        original_th = mod.post_threads
        mod.post_discord = lambda payload, webhook_url=None: discord.append(
            (payload, webhook_url)
        ) or True
        mod.post_telegram = lambda text: telegram.append(text) or True
        mod.post_threads = lambda text: threads.append(text) or True
        try:
            code, body = run_web_notify_test(
                {"channel": "all", "message": "Restock tonight"},
                authenticated=True,
            )
        finally:
            mod.post_discord = original_dc
            mod.post_telegram = original_tg
            mod.post_threads = original_th
            apply_config(load_config())
        self.assertEqual(code, 200)
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("sent"))
        self.assertEqual(discord[0][0].get("content"), "Restock tonight")
        self.assertIn("Restock tonight", telegram[0])
        self.assertEqual(threads[0], "Restock tonight")
        self.assertIn("Discord", body.get("message"))
        self.assertIn("Telegram", body.get("message"))
        self.assertIn("Threads", body.get("message"))

    def test_product_list_page_shows_title_and_link(self):
        page = render_products_html(
            {"id": "fooklemodel", "label": "FookLeModel"},
            [
                {
                    "sku": "115537",
                    "title": "Beyblade X BXG-47",
                    "price": "150",
                    "url": "https://fooklemodel.com/product/bxg-47/",
                    "status_label": "有貨",
                    "image_path": "images/fooklemodel/115537.jpg",
                }
            ],
            key_query="?key=abc",
        )
        self.assertIn("Beyblade X BXG-47", page)
        self.assertIn(explore_href("https://fooklemodel.com/product/bxg-47/"), page)
        self.assertIn("HK$150", page)
        self.assertIn("/images/fooklemodel/115537.jpg", page)
        self.assertIn("product-card", page)
        self.assertIn("data-item-list-id=\"fooklemodel\"", page)
        self.assertIn("data-item-list-name=\"FookLeModel\"", page)
        self.assertIn('gtag("event","view_item_list"', page)
        self.assertIn("class='stock-in'", page)
        self.assertIn(".stock-in{color:var(--blue)}", page)
        self.assertIn("max-width:700px", page)
        self.assertIn('href="/"', page)
        self.assertIn('id="site-nav-drawer"', page)
        self.assertIn('href="/shop/all?stock=in"', page)
        self.assertIn("全部現貨", page)
        self.assertIn('id="subscribe-btn"', page)
        self.assertIn("subscribe-method", page)
        self.assertNotIn("key=abc", page)
        self.assertIn("FookLeModel 爆旋陀螺", page)
        self.assertIn("index, follow", page)
        self.assertIn('name="twitter:card" content="summary_large_image"', page)
        self.assertIn("og:image", page)
        self.assertIn("/og-card.jpg", page)
        self.assertIn('property="og:image:width" content="1200"', page)
        self.assertIn("/logo.png", page)
        self.assertNotIn("/seo-image.png", page)
        self.assertIn("加入主畫面", page)
        self.assertIn("alt='Beyblade X BXG-47'", page)

    def test_product_list_puts_in_stock_first_and_has_filters(self):
        page = render_products_html(
            {"id": "fooklemodel", "label": "FookLeModel"},
            [
                {
                    "sku": "out-1",
                    "title": "Out of stock top",
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                },
                {
                    "sku": "in-1",
                    "title": "In stock later",
                    "status": "in_stock",
                    "status_label": "有貨",
                },
            ],
        )
        self.assertLess(page.find("In stock later"), page.find("Out of stock top"))
        self.assertIn('href="/product?shop=fooklemodel"', page)
        self.assertIn('href="/product?stock=in&amp;shop=fooklemodel"', page)
        self.assertIn('href="/product?stock=out&amp;shop=fooklemodel"', page)
        self.assertNotIn("/shop/fooklemodel", page)
        self.assertIn("全部 2", page)
        self.assertIn("有貨 1", page)
        self.assertIn("缺貨 1", page)
        self.assertIn(">All</a>", page)
        self.assertNotIn("全部線", page)

    def test_product_list_has_shop_chips_for_all_and_other_stores(self):
        cfg = {
            "sources": [
                {
                    "id": "hobbyland",
                    "label": "Hobbyland",
                    "origin": "https://www.hobbylandeshop.com",
                    "enabled": True,
                },
                {
                    "id": "hobbyland-beyblade",
                    "label": "HobbylandBeyblade",
                    "origin": "https://www.hobbylandeshop.com",
                    "enabled": True,
                },
                {
                    "id": "animepro",
                    "label": "AnimesPro",
                    "origin": "https://animes-pro.com",
                    "enabled": True,
                },
            ]
        }
        page = render_products_html(
            shop_page_meta("hobbyland-beyblade", cfg),
            [
                {
                    "sku": "PRE-059905",
                    "title": "BX-57",
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                }
            ],
            shops=shop_chip_shops(cfg),
        )
        self.assertIn('href="/product">All</a>', page)
        self.assertIn('href="/product?shop=hobbyland"', page)
        self.assertIn('href="/product?shop=animepro"', page)
        self.assertNotIn("/shop/hobbyland", page)
        self.assertIn("AnimesPro", page)
        self.assertIn("Hobbyland", page)
        self.assertNotIn(">HobbylandBeyblade<", page)
        self.assertIn("shop-chips", page)

    def test_shop_filter_uses_search_select_when_more_than_seven_options(self):
        shops = [{"id": "s%d" % i, "label": "Shop%d" % i} for i in range(7)]
        markup = shop_chips_html(shops, current_id="all")
        self.assertIn("filter-combo", markup)
        self.assertIn("filter-store", markup)
        self.assertIn("Store", markup)
        self.assertIn("filter-combo-arrow", markup)
        self.assertIn('type="search"', markup)
        self.assertIn("Shop0", markup)
        self.assertIn("Shop6", markup)
        self.assertIn(">All</a>", markup)
        chips = shop_chips_html(
            [{"id": "s%d" % i, "label": "Shop%d" % i} for i in range(6)],
            current_id="all",
        )
        self.assertNotIn("filter-combo", chips)
        self.assertIn('href="/product">All</a>', chips)
        page = render_products_html(
            {"id": "all", "label": "全部"},
            [],
            stock_filter="in_stock",
            shops=shops,
        )
        self.assertIn("filter-combo", page)
        home = render_status_html(
            {"checked_at": "2026-08-30 12:00:00", "ok": True, "shops": []},
            notifies=[],
            shops=shops,
        )
        self.assertNotIn('class="filter-store"', home)
        self.assertNotIn('class="filter-combo', home)
        self.assertIn(".filter-store{background:#fff;color:var(--ink);padding:12px;margin:0;max-width:360px}", home)
        self.assertIn(".filter-combo-arrow{color:var(--ink)", home)

    def test_history_model_filter_uses_search_select_when_more_than_seven(self):
        rows = [
            {
                "at": "2026-08-30 04:00:00",
                "shop_id": "hobbyland",
                "shop": "Hobbyland",
                "event": "new",
                "title": "M-%s" % i,
                "model": "CX-%02d" % i,
                "change": "無 → 有貨",
            }
            for i in range(8)
        ]
        page = render_history_html(
            rows,
            shops=[{"id": "hobbyland", "label": "Hobbyland"}],
        )
        self.assertIn("filter-combo", page)
        self.assertIn('type="search"', page)
        self.assertIn("CX-00", page)
        self.assertNotIn("全部型號", page)
        self.assertIn(">All</a>", page)

    def test_product_list_stock_filter_keeps_only_matching_items(self):
        page = render_products_html(
            {"id": "fooklemodel", "label": "FookLeModel"},
            [
                {
                    "sku": "out-1",
                    "title": "Out of stock top",
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                },
                {
                    "sku": "in-1",
                    "title": "In stock later",
                    "status": "in_stock",
                    "status_label": "有貨",
                },
            ],
            stock_filter="in_stock",
        )
        self.assertIn("In stock later", page)
        self.assertNotIn("Out of stock top", page)
        self.assertIn('class="filter on"', page)
        self.assertIn("noindex, nofollow", page)

    def test_product_list_tag_filters(self):
        items = [
            {
                "sku": "cx-1",
                "title": "Beyblade X CX-19",
                "status": "in_stock",
                "status_label": "有貨",
                "tag": "CX",
                "model": "CX-19",
            },
            {
                "sku": "bx-1",
                "title": "Beyblade X BX-50",
                "status": "out_of_stock",
                "status_label": "缺貨",
                "tag": "BX",
                "model": "BX-50",
            },
            {
                "sku": "ot-1",
                "title": "Beyblade stadium",
                "status": "in_stock",
                "status_label": "有貨",
                "tag": "other",
            },
        ]
        page = render_products_html({"id": "fooklemodel", "label": "FookLeModel"}, items)
        self.assertIn('href="/product?tag=CX&amp;shop=fooklemodel"', page)
        self.assertIn('href="/product?tag=BX&amp;shop=fooklemodel"', page)
        self.assertIn('href="/product?tag=UX&amp;shop=fooklemodel"', page)
        self.assertIn('href="/product?tag=other&amp;shop=fooklemodel"', page)
        self.assertIn("CX [1]", page)
        self.assertIn("BX [1]", page)
        self.assertIn("UX [0]", page)
        self.assertIn("other [1]", page)
        cx_page = render_products_html(
            {"id": "fooklemodel", "label": "FookLeModel"},
            items,
            tag_filter="CX",
        )
        self.assertIn("Beyblade X CX-19", cx_page)
        self.assertNotIn("Beyblade X BX-50", cx_page)
        self.assertNotIn("Beyblade stadium", cx_page)
        self.assertIn('href="/product?stock=in&amp;tag=CX&amp;shop=fooklemodel"', cx_page)

    def test_shop_products_fall_back_to_skus(self):
        items = shop_products_from_state(
            {
                "skus": ["PRE-1"],
                "stock": {"PRE-1": "out_of_stock"},
            }
        )
        self.assertEqual(items[0]["sku"], "PRE-1")
        self.assertEqual(items[0]["status_label"], "缺貨")

    def test_html_uses_red_only_for_errors(self):
        page = render_status_html(
            {
                "checked_at": "2026-08-26 19:00:00",
                "ok": False,
                "mysql": False,
                "shops": [
                    {
                        "label": "ToysRUs",
                        "sku_count": 0,
                        "in_stock": 0,
                        "out_of_stock": 0,
                        "updated_at": "",
                        "error": "timeout",
                    }
                ],
            }
        )
        self.assertNotIn("class='bad'", page)
        self.assertNotIn("timeout", page)
        self.assertNotIn("<th>錯誤</th>", page)
        self.assertNotIn("<details class='status-pop'>", page)
        self.assertNotIn(">錯誤<", page)
        self.assertIn(">正常<", page)
        self.assertIn("#e10600", page)
        self.assertNotIn("#128a3e", page)
        hidden = render_shops_html(
            payload={
                "checked_at": "2026-08-26 19:00:00",
                "ok": False,
                "shops": [
                    {
                        "id": "toysrus",
                        "label": "ToysRUs",
                        "enabled": True,
                        "sku_count": 0,
                        "in_stock": 0,
                        "out_of_stock": 0,
                        "updated_at": "",
                        "error": "timeout",
                    }
                ],
            },
            show_updated=True,
        )
        self.assertIn("<details class='status-pop'>", hidden)
        self.assertIn("<span class='bad'>錯誤</span>", hidden)
        self.assertIn("<span class='bad'>異常</span>", hidden)
        self.assertIn("timeout", hidden)
        self.assertIn("status-pop:hover .status-tip", hidden)
        self.assertIn("status-pop[open] .status-tip", hidden)
        self.assertNotIn("<th>錯誤</th>", hidden)

    def test_shopslist_keeps_amazon_jp_retail_separate(self):
        cfg = {
            "sources": [
                {
                    "id": "amazon-jp",
                    "label": "Amazon (JP)",
                    "origin": "https://www.amazon.co.jp",
                    "enabled": True,
                },
                {
                    "id": "amazon-jp-retail",
                    "label": "Amazon.co.jp 直販",
                    "origin": "https://www.amazon.co.jp",
                    "enabled": True,
                },
            ]
        }
        page = render_shops_html(
            cfg,
            payload={
                "checked_at": "2026-11-13 16:00:00",
                "ok": True,
                "shops": [
                    {
                        "id": "amazon-jp",
                        "label": "Amazon (JP)",
                        "enabled": True,
                        "sku_count": 77,
                        "in_stock": 14,
                        "out_of_stock": 63,
                    },
                    {
                        "id": "amazon-jp-retail",
                        "label": "Amazon.co.jp 直販",
                        "enabled": True,
                        "sku_count": 6,
                        "in_stock": 0,
                        "out_of_stock": 6,
                    },
                ],
            },
            show_updated=True,
        )
        self.assertIn("Amazon.co.jp 直販", page)
        self.assertIn("href='/product?shop=amazon-jp-retail'", page)
        self.assertNotIn("/shop/amazon-jp-retail", page)
        self.assertIn("/shopslist", page)
        self.assertEqual(
            [row["id"] for row in display_status_shops(cfg["sources"], cfg)],
            ["all", "amazon-jp", "amazon-jp-retail"],
        )


class StatusAuthTests(unittest.TestCase):
    def test_old_key_urls_redirect_to_clean_paths(self):
        self.assertEqual(status_request_redirect("/?key=abc"), "/")
        self.assertEqual(
            status_request_redirect("/in-stock?key=abc"),
            "/shop/all?stock=in",
        )
        self.assertEqual(status_request_redirect("/in-stock"), "/shop/all?stock=in")
        self.assertEqual(status_request_redirect("/instock"), "/shop/all?stock=in")
        self.assertEqual(status_request_redirect("/shop/cuapp?key=abc"), "/shop/cuapp")
        self.assertIsNone(status_request_redirect("/"))
        self.assertIsNone(status_request_redirect("/shop/cuapp?stock=in"))
        self.assertEqual(
            status_request_redirect("/shop/cuapp?key=abc&stock=in"),
            "/shop/cuapp?stock=in",
        )

    def test_old_model_paths_redirect_to_product(self):
        self.assertEqual(product_path_redirect("/models"), "/product")
        self.assertEqual(product_path_redirect("/models/"), "/product")
        self.assertEqual(product_path_redirect("/model"), "/product")
        self.assertEqual(
            product_path_redirect("/models/BX-01?stock=in"),
            "/product/BX-01?stock=in",
        )
        self.assertEqual(product_path_redirect("/model/CX-18"), "/product/CX-18")
        self.assertIsNone(product_path_redirect("/product"))
        self.assertIsNone(product_path_redirect("/product/BX-01"))
        self.assertIsNone(product_path_redirect("/shops"))

    def test_shop_list_pages_redirect_to_product_filter(self):
        apply_config(
            {
                "sources": [
                    {
                        "id": "hobbyland",
                        "label": "Hobbyland",
                        "origin": "https://www.hobbylandeshop.com",
                        "enabled": True,
                    },
                    {
                        "id": "hobbyland-beyblade",
                        "label": "HobbylandBeyblade",
                        "origin": "https://www.hobbylandeshop.com",
                        "enabled": True,
                    },
                    {
                        "id": "animepro",
                        "label": "AnimesPro",
                        "origin": "https://animes-pro.com",
                        "enabled": True,
                    },
                ]
            }
        )
        try:
            self.assertEqual(
                shop_list_redirect("/shop/hobbyland"),
                "/product?shop=hobbyland",
            )
            self.assertEqual(
                shop_list_redirect("/shop/hobbyland-beyblade"),
                "/product?shop=hobbyland",
            )
            self.assertEqual(
                shop_list_redirect("/shop/hobbyland?stock=in&tag=CX"),
                "/product?stock=in&tag=CX&shop=hobbyland",
            )
            self.assertEqual(
                shop_list_redirect("/shop/animepro?stock=out"),
                "/product?stock=out&shop=animepro",
            )
            self.assertEqual(shop_list_redirect("/shop/all"), "/product")
            self.assertEqual(shop_list_redirect("/shop/all?tag=BX"), "/product?tag=BX")
            self.assertIsNone(shop_list_redirect("/shop/all?stock=in"))
            self.assertIsNone(shop_list_redirect("/shop/all?stock=in&shop=amazon"))
            self.assertIsNone(shop_list_redirect("/shop/missing"))
            self.assertIsNone(shop_list_redirect("/shops"))
            self.assertIsNone(shop_list_redirect("/product?shop=hobbyland"))
        finally:
            apply_config(load_config())

    def test_robots_txt_allows_catalog_and_blocks_home(self):
        apply_config({})
        body = robots_txt()
        self.assertIn("User-agent: *", body)
        self.assertIn("Allow: /", body)
        self.assertNotIn("\nDisallow: /\n", body)
        self.assertNotIn("Allow: /in-stock", body)
        self.assertIn("Sitemap: https://hkbeybladex.com/sitemap.xml", body)
        self.assertIn("Disallow: /shopslist", body)
        self.assertIn("Disallow: /login", body)
        self.assertIn("Disallow: /notify-test", body)
        self.assertNotIn("Disallow: /product", body)
        self.assertNotIn("\nDisallow: /\n", body)
        admin_robots = robots_txt("beybladex-admin.andyhhh.com")
        self.assertIn("Disallow: /", admin_robots)
        self.assertNotIn("Sitemap:", admin_robots)
        self.assertNotIn("Allow: /", admin_robots)

    def test_sitemap_lists_in_stock_and_shops(self):
        apply_config({})
        xml = sitemap_xml(
            {
                "sources": [
                    {
                        "id": "cuapp",
                        "label": "CU APP",
                        "origin": "https://eshop.cuapp.com",
                        "enabled": True,
                    }
                ]
            }
        )
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn('xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', xml)
        self.assertIn("<lastmod>", xml)
        self.assertIn("https://hkbeybladex.com/", xml)
        self.assertIn("https://hkbeybladex.com/watch", xml)
        self.assertIn("https://hkbeybladex.com/share", xml)
        self.assertNotIn("https://hkbeybladex.com/shop/all", xml)
        self.assertIn("https://hkbeybladex.com/shops", xml)
        self.assertIn("https://hkbeybladex.com/catalog", xml)
        self.assertIn("https://hkbeybladex.com/parts", xml)
        self.assertIn("https://hkbeybladex.com/collection", xml)
        self.assertIn("https://hkbeybladex.com/subscribe", xml)
        self.assertIn("https://hkbeybladex.com/privacy", xml)
        self.assertIn("https://hkbeybladex.com/terms", xml)
        self.assertNotIn("/coffee", xml)
        self.assertNotIn("https://hkbeybladex.com/shop/cuapp", xml)
        self.assertNotIn("/product?shop=", xml)
        self.assertNotIn("/in-stock", xml)
        self.assertNotIn("/notify-test", xml)
        self.assertNotIn("/shopslist", xml)
        self.assertNotIn("/login", xml)
        self.assertNotIn("/models", xml)
        self.assertIn("https://hkbeybladex.com/product", xml)
        self.assertIn("https://hkbeybladex.com/history", xml)
        self.assertNotIn("/go/", xml)
        self.assertNotIn("/explore", xml)
        import xml.etree.ElementTree as ET

        root = ET.fromstring(xml)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [node.text for node in root.findall("sm:url/sm:loc", ns)]
        self.assertEqual(locs[0], "https://hkbeybladex.com/")
        self.assertEqual(len(locs), len(set(locs)))
        self.assertTrue(all(loc.startswith("https://hkbeybladex.com/") for loc in locs))
        for lastmod in root.findall("sm:url/sm:lastmod", ns):
            self.assertRegex(lastmod.text, r"^\d{4}-\d{2}-\d{2}$")

    def test_web_manifest_points_at_logo(self):
        data = json.loads(web_manifest())
        self.assertEqual(data["start_url"], "/")
        self.assertEqual(data["name"], "HK BeybladeX Watch")
        self.assertEqual(data["short_name"], "HK BeybladeX")
        self.assertEqual(data["theme_color"], "#1a1aff")
        self.assertEqual(
            data["icons"][0]["src"],
            "https://beybladex-cdn.andyhhh.com/logo.png",
        )




class GoTrackTests(unittest.TestCase):
    def test_parse_and_build_go_path(self):
        self.assertEqual(parse_go_path("/go/uat/test"), ("uat", "test"))
        self.assertEqual(
            parse_go_path("/go/hobbyland-beyblade/UX-08"),
            ("hobbyland-beyblade", "UX-08"),
        )
        self.assertEqual(
            go_href("uat", "test"),
            "https://hkbeybladex.com/go/uat/test",
        )
        self.assertEqual(
            go_href("uat", "test", source="discord"),
            "https://hkbeybladex.com/go/uat/test?from=discord&utm_source=discord&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test&pv=3",
        )
        self.assertEqual(
            go_href("uat", "test", source="threads"),
            "https://hkbeybladex.com/go/uat/test?from=threads&utm_source=threads&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test&pv=3",
        )
        self.assertIsNone(parse_go_path("/shop/uat"))
        self.assertIsNone(parse_go_path("/go/uat"))
        self.assertIsNone(parse_go_path("/go/all/x"))
        self.assertIsNone(parse_go_path("/go/buymarkettoy"))
        self.assertIsNone(parse_go_path("/go/buymarkettoy/"))

    def test_go_buymarkettoy_landing_uses_homepage_seo(self):
        result = go_http_result("/go/buymarkettoy/")
        self.assertEqual(result["status"], 200)
        page = result["html"]
        self.assertIn("<title>HK BeybladeX Watch</title>", page)
        self.assertIn(
            'property="og:title" content="HK BeybladeX Watch"',
            page,
        )
        self.assertIn(
            'property="og:description" content="24小時自動監控香港各大網店及官方渠道（HobbyDigi、BuyMarketToy、MoonroadHK、Takara Tomy Mall等）爆旋陀螺 X 現貨與開訂狀態。即時接收 Telegram、Discord 及 Threads 補貨通知，與香港陀螺手交流情報！"',
            page,
        )
        self.assertIn(
            'name="keywords" content="beybladex, 爆旋陀螺, 爆旋陀螺 X, Beyblade X 香港, 爆旋陀螺補貨, 爆旋陀螺現貨, 爆旋陀螺開訂, HK BeybladeX Watch, Takara Tomy 香港, 陀螺社群, Beyblade X restock HK, beyblade x, 陀螺, 戰鬥陀螺, hkbeybladex"',
            page,
        )
        self.assertIn("/og-card.jpg", page)
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/go/buymarkettoy/"',
            page,
        )
        self.assertIn(
            'rel="canonical" href="https://hkbeybladex.com/go/buymarkettoy/"',
            page,
        )
        slashless = go_http_result("/go/buymarkettoy")
        self.assertEqual(slashless["status"], 200)
        self.assertIn("<title>HK BeybladeX Watch</title>", slashless["html"])
        self.assertEqual(go_http_result("/go/hobbyland/")["status"], 404)
        self.assertEqual(go_http_result("/go/marktoys/")["status"], 404)

    def test_uat_target_points_at_original_store(self):
        target = go_page_target("uat", "test")
        self.assertEqual(
            target["dest"],
            "https://www.hobbylandeshop.com/product-category/nproduct_booking",
        )
        self.assertTrue(target.get("title"))
        self.assertEqual(target.get("price"), "199.00")
        self.assertEqual(target.get("status"), "有貨")

    def test_unknown_go_target_is_missing(self):
        self.assertIsNone(go_page_target("no-such-shop", "no-sku", items=[]))

    def test_known_sku_uses_store_url(self):
        target = go_page_target(
            "fooklemodel",
            "115537",
            items=[
                {
                    "sku": "115537",
                    "title": "BXG-47",
                    "url": "https://fooklemodel.com/product/bxg-47/",
                    "price": "150",
                    "status": "in_stock",
                    "image": "https://fooklemodel.com/img.jpg",
                }
            ],
        )
        self.assertEqual(target["dest"], "https://fooklemodel.com/product/bxg-47/")
        self.assertEqual(target["title"], "BXG-47")
        self.assertEqual(target["price"], "150")
        self.assertEqual(target["status"], "有貨")
        self.assertIn("fooklemodel.com/img.jpg", target["image"])

    def test_wrap_notify_links_only_rewrites_to_go(self):
        wrapped = wrap_notify_item_links(
            [{"title": "X", "sku": "test", "link": "https://shop.example/p"}],
            shop_id="uat",
            source="telegram",
        )
        self.assertEqual(
            wrapped[0]["link"],
            "https://hkbeybladex.com/go/uat/test?from=telegram&utm_source=telegram&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test&pv=3",
        )

    def test_wrap_warm_uses_go_when_cloudflare_ready(self):
        wrapped = wrap_notify_item_links(
            [{"title": "X", "sku": "test", "link": "https://shop.example/p"}],
            shop_id="uat",
            source="discord",
            warm=True,
            probe=lambda url: True,
        )
        self.assertEqual(
            wrapped[0]["link"],
            "https://hkbeybladex.com/go/uat/test?from=discord&utm_source=discord&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test&pv=3",
        )

    def test_wrap_warm_falls_back_to_store_when_probe_fails(self):
        wrapped = wrap_notify_item_links(
            [{"title": "X", "sku": "test", "link": "https://shop.example/p"}],
            shop_id="uat",
            source="discord",
            warm=True,
            probe=lambda url: False,
        )
        self.assertEqual(wrapped[0]["link"], "https://shop.example/p")

    def test_probe_go_url_accepts_302(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://example/go", 302, "Found", {}, None
        )
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            self.assertTrue(probe_go_url("https://hkbeybladex.com/go/uat/test"))

    def test_probe_go_url_rejects_404_and_errors(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://example/go", 404, "Not Found", {}, None
        )
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            with mock.patch(
                "site_data.subprocess.run", side_effect=TimeoutError()
            ):
                self.assertFalse(probe_go_url("https://hkbeybladex.com/go/uat/test"))
        opener.open.side_effect = TimeoutError()
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            with mock.patch(
                "site_data.subprocess.run", side_effect=TimeoutError()
            ):
                self.assertFalse(
                    probe_go_url("https://hkbeybladex.com/go/uat/test")
                )

    def test_probe_go_url_uses_curl_without_following_redirects(self):
        opener = mock.Mock()
        opener.open.side_effect = OSError("ssl")
        proc = mock.Mock(returncode=0, stdout="302")
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            with mock.patch("site_data.subprocess.run", return_value=proc) as run:
                self.assertTrue(
                    probe_go_url("https://hkbeybladex.com/go/uat/test")
                )
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "curl")
        self.assertNotIn("-L", argv)

    def test_go_http_discord_loads_bounce_page(self):
        result = go_http_result("/go/uat/test", query="from=discord")
        self.assertEqual(result["status"], 200)
        self.assertEqual(
            result["location"],
            "https://www.hobbylandeshop.com/product-category/nproduct_booking",
        )
        self.assertIn("location.replace(dest)", result["html"])
        self.assertIn("setTimeout(go, 500)", result["html"])
        self.assertIn("go-loading", result["html"])
        self.assertNotIn("go-card", result["html"])
        self.assertNotIn('http-equiv="refresh"', result["html"])
        self.assertIn("gtag('config', 'G-19VVZP9R25')", result["html"])
        self.assertIn("transport_type:'beacon'", result["html"])
        self.assertIn("前往商店", result["html"])
        self.assertNotIn("以後唔好再顯示", result["html"])
        self.assertEqual(result.get("cache"), "private, no-store")

    def test_go_http_threads_shows_loading_for_browsers(self):
        result = go_http_result("/go/uat/test", query="from=threads")
        self.assertEqual(result["status"], 200)
        self.assertEqual(result.get("cache"), "private, no-store")
        self.assertIn("go-loading", result["html"])
        self.assertNotIn("go-card", result["html"])
        self.assertIn("setTimeout(go, 500)", result["html"])

    def test_go_http_preview_crawler_keeps_go_og_tags(self):
        result = go_http_result(
            "/go/uat/test",
            query="from=threads",
            user_agent="facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        )
        self.assertEqual(result["status"], 200)
        self.assertEqual(result.get("cache"), "private, no-store")
        self.assertIn('property="og:title"', result["html"])
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/go/uat/test?from=threads"',
            result["html"],
        )
        self.assertIn("og-card.jpg", result["html"])
        self.assertIn('name="twitter:card" content="summary"', result["html"])
        self.assertNotIn('http-equiv="refresh"', result["html"])
        self.assertNotIn("location.replace(dest)", result["html"])
        self.assertNotIn("go-loading", result["html"])
        self.assertNotIn(
            'property="og:url" content="https://www.hobbylandeshop.com/',
            result["html"],
        )
        telegram = go_http_result(
            "/go/uat/test",
            query="from=telegram",
            user_agent="TelegramBot (like TwitterBot)",
        )
        self.assertNotIn('http-equiv="refresh"', telegram["html"])
        self.assertNotIn("location.replace(dest)", telegram["html"])
        self.assertNotIn("go-loading", telegram["html"])
        self.assertIn('property="og:title"', telegram["html"])
        human = go_http_result("/go/uat/test", query="from=telegram")
        self.assertIn("go-loading", human["html"])
        self.assertNotIn("go-card", human["html"])
        self.assertIn("setTimeout(go, 500)", human["html"])
        preview = go_http_result("/go/uat/preview", query="from=threads")
        self.assertEqual(preview["status"], 200)
        self.assertIn('property="og:title" content="HK BeybladeX Watch"', preview["html"])
        self.assertIn("/go/uat/preview?from=threads", preview["html"])

    def test_wrap_threads_uses_go_hop(self):
        wrapped = wrap_notify_item_links(
            [{"title": "X", "sku": "test", "link": "https://shop.example/p"}],
            shop_id="uat",
            source="threads",
            warm=True,
            probe=lambda url: True,
        )
        self.assertIn("/go/uat/test", wrapped[0]["link"])
        self.assertIn("from=threads", wrapped[0]["link"])
        self.assertNotIn("skip=1", wrapped[0]["link"])
        seen = []
        wrap_notify_item_links(
            [{"title": "X", "sku": "test", "link": "https://shop.example/p"}],
            shop_id="uat",
            source="threads",
            warm=True,
            probe=lambda url: seen.append(url) or True,
        )
        self.assertEqual(len(seen), 1)
        self.assertNotIn("skip=1", seen[0])

    def test_go_http_threads_has_no_hide_forever(self):
        invite = go_http_result("/go/uat/test", query="from=threads")
        self.assertNotIn("?skip=1", invite["html"])
        self.assertNotIn("以後唔好再顯示", invite["html"])
        self.assertNotIn("以後不顯示", invite["html"])
        self.assertNotIn("bxw_go_skip", invite["html"])
        self.assertIn("location.replace(dest)", invite["html"])
        self.assertIn("setTimeout(go, 500)", invite["html"])
        with_cookie = go_http_result(
            "/go/uat/test",
            query="from=threads",
            cookie="bxw_go_skip=1",
        )
        self.assertNotIn("以後唔好再顯示", with_cookie["html"])
        self.assertIn("location.replace(dest)", with_cookie["html"])
        leftover = go_http_result("/go/uat/test", query="from=threads&skip=1")
        self.assertEqual(leftover["status"], 200)
        self.assertEqual(leftover.get("cache"), "private, no-store")
        self.assertIn("location.replace(dest)", leftover["html"])
        self.assertIn("setTimeout(go, 500)", leftover["html"])

    def test_go_page_invites_and_keeps_store_seo(self):
        page = render_go_html(go_page_target("uat", "test"), "uat", "test")
        self.assertIn("index, follow", page)
        self.assertNotIn("noindex, nofollow", page)
        self.assertIn('name="twitter:card" content="summary"', page)
        self.assertNotIn("summary_large_image", page)
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/go/uat/test"',
            page,
        )
        self.assertIn("og-card.jpg", page)
        self.assertIn('property="og:site_name"', page)
        self.assertIn('property="og:image:width" content="1200"', page)
        self.assertIn(
            'property="og:description" content="Hobbyland 爆旋陀螺新品預訂分類，官方授權香港代理商品。"',
            page,
        )
        bounce = render_go_bounce_html(go_page_target("uat", "test"), "uat", "test")
        self.assertIn('name="twitter:card" content="summary"', bounce)
        self.assertIn(
            'property="og:description" content="Hobbyland 爆旋陀螺新品預訂分類，官方授權香港代理商品。"',
            bounce,
        )
        self.assertIn("location.replace(dest)", bounce)
        self.assertIn("setTimeout(go, 500)", bounce)
        self.assertIn("x-safari-", bounce)
        self.assertIn("intent://", bounce)
        self.assertIn("go-loading", bounce)
        self.assertNotIn('http-equiv="refresh"', bounce)
        self.assertIn(explore_href("https://discord.gg/C8Q5gZf3y5"), page)
        self.assertIn(explore_href("https://t.me/+mbTPVeGFBalhMjQ9"), page)
        self.assertIn(explore_href("https://www.threads.com/@hkbeybladex_com"), page)
        self.assertIn(
            "Follow 我哋 Threads 之後記得撳右上角訂閱／鐘仔掣，訂閱帖文通知",
            page,
        )
        self.assertIn('<a href="/shops">Online舖頭</a>', page)
        self.assertNotIn("本地舖頭", page)
        self.assertNotIn("隔離訂閱", page)
        self.assertNotIn("打開帖文通知", page)
        self.assertNotIn("以後唔好再顯示", page)
        self.assertNotIn("以後不顯示", page)
        self.assertNotIn("bxw_go_skip", page)
        self.assertIn("前往商店", page)
        self.assertNotIn("前往商店 (5)", page)
        self.assertNotIn("?skip=1", page)
        self.assertNotIn("n=5", page)
        self.assertNotIn("location.href=dest", page)
        self.assertNotIn("location.replace(skip)", page)
        self.assertNotIn("form.submit()", page)
        self.assertIn("HK$199.00", page)
        self.assertIn("有貨", page)
        self.assertIn("class='thumb'", page)

    def test_go_og_image_uses_site_card_not_shopline(self):
        target = go_target_from_item(
            {
                "title": "BX-34",
                "sku": "NOCACHE-OG-TEST",
                "url": "https://www.buymarkettoy.com/products/x",
                "image": "https://cdn.example/x/165x165f.webp",
                "price": "159.00",
                "status_label": "缺貨",
            },
            "buymarkettoy",
        )
        page = render_go_html(target, "buymarkettoy", "NOCACHE-OG-TEST")
        self.assertIn(
            'property="og:image" content="https://beybladex-cdn.andyhhh.com/og-card.jpg"',
            page,
        )
        bounce = render_go_bounce_html(target, "buymarkettoy", "NOCACHE-OG-TEST")
        self.assertIn(
            'property="og:image" content="https://beybladex-cdn.andyhhh.com/og-card.jpg"',
            bounce,
        )
        self.assertNotIn("shoplineimg.com", bounce)

    def test_go_og_image_skips_shopline_hotlink(self):
        target = go_target_from_item(
            {
                "title": "CX-00",
                "sku": "4904810085683",
                "url": "https://www.dreamtoys.com.hk/products/x",
                "image": "https://shoplineimg.com/5c299830975186000156cc24/6a952150749860663294a20d/165x165f.webp?source_format=jpeg",
                "price": "349.00",
                "status_label": "缺貨",
            },
            "dreamtoys",
        )
        page = render_go_html(target, "dreamtoys", "4904810085683")
        self.assertIn(
            'property="og:image" content="https://beybladex-cdn.andyhhh.com/og-card.jpg"',
            page,
        )
        self.assertNotIn(
            'property="og:image" content="https://shoplineimg.com/',
            page,
        )
        self.assertIn("165x165f.webp", page)

    def test_go_og_image_uses_cdn_when_file_is_not_on_this_machine(self):
        target = go_target_from_item(
            {
                "title": "Set of 6",
                "sku": "129635",
                "url": "https://fooklemodel.com/product/set-of-6/",
                "image_path": "images/fooklemodel/129635.jpg",
                "price": "99",
                "status_label": "有貨",
            },
            "fooklemodel",
        )
        page = render_go_html(target, "fooklemodel", "129635")
        self.assertIn(
            'property="og:image" content="https://beybladex-cdn.andyhhh.com/images/fooklemodel/129635.jpg"',
            page,
        )
        self.assertNotIn(
            'property="og:image" content="https://beybladex-cdn.andyhhh.com/og-card.jpg"',
            page,
        )

    def test_go_og_image_uses_cached_jpeg(self):
        import site_data as mod

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old = mod.DATA_DIR
        mod.DATA_DIR = tmp.name
        try:
            rel = product_image_path("buymarkettoy", "BY914563")
            dest = os.path.join(tmp.name, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(b"jpeg" * 600)
            target = go_target_from_item(
                {
                    "title": "BX-34",
                    "sku": "BY914563",
                    "url": "https://www.buymarkettoy.com/products/x",
                    "image": "https://shoplineimg.com/5f8928fdb9748d005312ca75/69c1f1cc33220234975d0bf3/375x.webp?source_format=png",
                    "image_path": rel,
                    "price": "159.00",
                    "status_label": "缺貨",
                },
                "buymarkettoy",
            )
            page = render_go_html(target, "buymarkettoy", "BY914563")
            self.assertIn(
                'property="og:image" content="https://beybladex-cdn.andyhhh.com/images/buymarkettoy/BY914563.jpg?v=',
                page,
            )
            self.assertIn('property="og:image:type" content="image/jpeg"', page)
            self.assertIn('name="twitter:card" content="summary"', page)
            self.assertNotIn('property="og:image:width"', page)
            self.assertNotIn("shoplineimg.com/5f8928fdb9748d005312ca75", page.split('property="og:image"')[1][:300])
        finally:
            mod.DATA_DIR = old

    def test_go_og_image_stays_absolute_when_cdn_origin_is_local(self):
        import site_data as mod

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old_data = mod.DATA_DIR
        old_cdn = os.environ.get("BEYBLADE_CDN_ORIGIN")
        os.environ["BEYBLADE_CDN_ORIGIN"] = "local"
        mod.DATA_DIR = tmp.name
        try:
            rel = product_image_path("houseparaland", "5451")
            dest = os.path.join(tmp.name, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(b"jpeg" * 600)
            target = go_target_from_item(
                {
                    "title": "UX-15",
                    "sku": "5451",
                    "url": "https://housenookparaland.com/product/5451/x",
                    "image": "https://images.storeberry.chat/shops/v185/products/M/x.jpg",
                    "image_path": rel,
                    "price": "219.00",
                    "status_label": "缺貨",
                },
                "houseparaland",
            )
            page = render_go_html(target, "houseparaland", "5451")
            self.assertIn(
                'property="og:image" content="https://hkbeybladex.com/images/houseparaland/5451.jpg?v=',
                page,
            )
            self.assertNotIn(
                'property="og:image" content="/images/houseparaland/5451.jpg',
                page,
            )
        finally:
            mod.DATA_DIR = old_data
            if old_cdn is None:
                os.environ.pop("BEYBLADE_CDN_ORIGIN", None)
            else:
                os.environ["BEYBLADE_CDN_ORIGIN"] = old_cdn




class StatusPageCacheTests(unittest.TestCase):
    def setUp(self):
        reset_status_caches()
        reset_edge_purge_state()

    def tearDown(self):
        reset_status_caches()
        reset_edge_purge_state()

    def test_html_and_images_use_public_cache_headers(self):
        self.assertIn("public", HTML_CACHE_CONTROL)
        self.assertIn("max-age=60", HTML_CACHE_CONTROL)
        self.assertIn("s-maxage=31536000", HTML_CACHE_CONTROL)
        self.assertNotIn("s-maxage=30", HTML_CACHE_CONTROL)
        self.assertIn("s-maxage=86400", GO_CACHE_CONTROL)
        self.assertIn("max-age=300", GO_CACHE_CONTROL)
        self.assertIn("stale-if-error=604800", GO_CACHE_CONTROL)
        self.assertEqual(
            IMAGE_CACHE_CONTROL,
            "public, max-age=31536000, s-maxage=31536000, immutable",
        )

    def test_load_config_merges_local_cloudflare_token(self):
        folder = tempfile.mkdtemp()
        base = os.path.join(folder, "watch_config.json")
        local = os.path.join(folder, "watch_config.local.json")
        with open(base, "w", encoding="utf-8") as fh:
            json.dump({"status": {"enabled": True}}, fh)
        with open(local, "w", encoding="utf-8") as fh:
            json.dump({"cloudflare": {"api_token": "secret-token", "zone_id": "zone"}}, fh)
        cfg = load_config(base)
        self.assertEqual(cfg["cloudflare"]["api_token"], "secret-token")
        self.assertEqual(cfg["cloudflare"]["zone_id"], "zone")
        self.assertTrue(cfg["status"]["enabled"])

    def test_purge_log_keeps_api_response_for_3_days(self):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "edge_purge.jsonl")
        old = os.environ.get("BEYBLADE_CF_API_TOKEN")
        os.environ["BEYBLADE_CF_API_TOKEN"] = "test-token"
        captured = {}

        class Resp(object):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"success": true, "errors": [], "result": {"id": "zone"}}'

        def fake_urlopen(request, timeout=20):
            captured["auth"] = request.get_header("Authorization")
            return Resp()

        try:
            result = purge_edge_cache(urlopen=fake_urlopen, log_path=path, now=lambda: 1_700_000_000)
        finally:
            if old is None:
                os.environ.pop("BEYBLADE_CF_API_TOKEN", None)
            else:
                os.environ["BEYBLADE_CF_API_TOKEN"] = old
        self.assertTrue(result["cloudflare"])
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["http"], 200)
        self.assertTrue(rows[0]["response"]["success"])
        self.assertEqual(rows[0]["at"], "2023-11-15T06:13:20")
        self.assertNotIn("test-token", json.dumps(rows[0]))
        stale_at = "2023-11-11T06:13:20"
        fresh_at = "2023-11-13T06:13:20"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": stale_at, "ok": True}) + "\n")
            fh.write(json.dumps({"at": fresh_at, "ok": True}) + "\n")
        kept = prune_edge_purge_log(path=path, now=lambda: 1_700_000_000)
        self.assertEqual(kept, 1)
        with open(path, encoding="utf-8") as fh:
            left = [json.loads(line) for line in fh if line.strip()]
        self.assertEqual(left[0]["at"], fresh_at)

    def test_purge_edge_cache_posts_html_tag_and_drops_origin_cache(self):
        cached_bytes("home", lambda: b"stale", ttl=30, now=lambda: 0)
        captured = {}

        class Resp(object):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"success": true, "errors": []}'

        def fake_urlopen(request, timeout=20):
            captured["url"] = request.full_url
            captured["body"] = request.data.decode("utf-8")
            captured["auth"] = request.get_header("Authorization")
            return Resp()

        old = os.environ.get("BEYBLADE_CF_API_TOKEN")
        os.environ["BEYBLADE_CF_API_TOKEN"] = "test-token"
        try:
            result = purge_edge_cache(urlopen=fake_urlopen)
        finally:
            if old is None:
                os.environ.pop("BEYBLADE_CF_API_TOKEN", None)
            else:
                os.environ["BEYBLADE_CF_API_TOKEN"] = old
        self.assertTrue(result["ok"])
        self.assertTrue(result["cloudflare"])
        self.assertIn("/purge_cache", captured["url"])
        self.assertIn(HTML_CACHE_TAG, captured["body"])
        self.assertEqual(captured["auth"], "Bearer test-token")
        built = {"n": 0}

        def build():
            built["n"] += 1
            return b"fresh"

        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 1), b"fresh")
        self.assertEqual(built["n"], 1)

    def test_purge_edge_cache_without_token_still_clears_origin(self):
        cached_bytes("home", lambda: b"stale", ttl=30, now=lambda: 0)
        old = os.environ.get("BEYBLADE_CF_API_TOKEN")
        os.environ.pop("BEYBLADE_CF_API_TOKEN", None)
        try:
            result = purge_edge_cache(urlopen=lambda *args, **kwargs: None)
        finally:
            if old is not None:
                os.environ["BEYBLADE_CF_API_TOKEN"] = old
        self.assertFalse(result["ok"])
        self.assertTrue(result["origin"])
        self.assertFalse(result["cloudflare"])
        self.assertEqual(result["error"], "missing_token")
        built = {"n": 0}

        def build():
            built["n"] += 1
            return b"fresh"

        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 1), b"fresh")
        self.assertEqual(built["n"], 1)

    def test_stock_change_purges_cloudflare_within_rate_limit(self):
        calls = []

        class Resp(object):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"success": true}'

        def fake_urlopen(request, timeout=20):
            calls.append(request.full_url)
            return Resp()

        old = os.environ.get("BEYBLADE_CF_API_TOKEN")
        os.environ["BEYBLADE_CF_API_TOKEN"] = "test-token"
        try:
            self.assertTrue(request_edge_purge(now=0, urlopen=fake_urlopen)["cloudflare"])
            limited = request_edge_purge(now=30, urlopen=fake_urlopen)
            self.assertEqual(limited.get("reason"), "rate_limit")
            self.assertEqual(len(calls), 1)
            self.assertTrue(request_edge_purge(now=60, urlopen=fake_urlopen)["cloudflare"])
            self.assertEqual(len(calls), 2)
            for index in range(2, 10):
                self.assertTrue(
                    request_edge_purge(now=index * 60, urlopen=fake_urlopen)["cloudflare"]
                )
            blocked = request_edge_purge(now=10 * 60, urlopen=fake_urlopen)
            self.assertEqual(blocked.get("reason"), "rate_limit")
            self.assertEqual(len(calls), 10)
            self.assertTrue(request_edge_purge(now=20 * 60, urlopen=fake_urlopen)["cloudflare"])
            for index in range(11, 20):
                when = (20 * 60) + (index - 10) * 60
                self.assertTrue(request_edge_purge(now=when, urlopen=fake_urlopen)["cloudflare"])
            self.assertEqual(len(calls), 20)
            capped = request_edge_purge(now=(20 * 60) + (10 * 60), urlopen=fake_urlopen)
            self.assertEqual(capped.get("reason"), "rate_limit")
            self.assertEqual(len(calls), 20)
            aged = request_edge_purge(now=1740 + (20 * 60), urlopen=fake_urlopen)
            self.assertEqual(aged.get("reason"), "rate_limit")
            self.assertEqual(len(calls), 20)
        finally:
            if old is None:
                os.environ.pop("BEYBLADE_CF_API_TOKEN", None)
            else:
                os.environ["BEYBLADE_CF_API_TOKEN"] = old

    def test_cached_bytes_reuses_builder_within_ttl(self):
        n = {"c": 0}

        def build():
            n["c"] += 1
            return b"body"

        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 100), b"body")
        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 129), b"body")
        self.assertEqual(n["c"], 1)

    def test_listing_watch_keeps_page_cache_when_file_touched_without_stock_change(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "shop_seen_skus.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "skus": ["keep"],
                    "stock": {"keep": "in_stock"},
                    "stock_changed_at": {"keep": "2026-11-08 02:00:00"},
                    "updated_at": "2026-11-08 02:00:00",
                },
                fh,
            )
        prev = listing_state_fingerprint(tmp.name)
        cached_bytes("home", lambda: b"stale", ttl=30, now=lambda: 0)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "skus": ["keep"],
                    "stock": {"keep": "in_stock"},
                    "stock_changed_at": {"keep": "2026-11-08 02:00:00"},
                    "updated_at": "2026-11-08T02:30:00.123456",
                },
                fh,
            )
        current = refresh_status_pages_if_listings_changed(prev, data_dir=tmp.name)
        self.assertEqual(current, prev)
        n = {"c": 0}

        def build():
            n["c"] += 1
            return b"fresh"

        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 1), b"stale")
        self.assertEqual(n["c"], 0)

    def test_listing_watch_clears_page_cache_when_stock_changes(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "shop_seen_skus.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "skus": ["keep"],
                    "stock": {"keep": "out_of_stock"},
                    "stock_changed_at": {"keep": "2026-11-08 02:00:00"},
                },
                fh,
            )
        prev = listing_state_fingerprint(tmp.name)
        cached_bytes("home", lambda: b"stale", ttl=30, now=lambda: 0)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "skus": ["keep"],
                    "stock": {"keep": "in_stock"},
                    "stock_changed_at": {"keep": "2026-11-08 02:00:20"},
                },
                fh,
            )
        current = refresh_status_pages_if_listings_changed(prev, data_dir=tmp.name)
        self.assertNotEqual(current, prev)
        n = {"c": 0}

        def build():
            n["c"] += 1
            return b"fresh"

        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 1), b"fresh")
        self.assertEqual(n["c"], 1)

    def test_listing_watch_keeps_page_cache_when_files_unchanged(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "shop_seen_skus.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"skus": ["keep"], "stock": {"keep": "in_stock"}}, fh)
        prev = listing_state_fingerprint(tmp.name)
        cached_bytes("home", lambda: b"stale", ttl=30, now=lambda: 0)
        current = refresh_status_pages_if_listings_changed(prev, data_dir=tmp.name)
        self.assertEqual(current, prev)
        n = {"c": 0}

        def build():
            n["c"] += 1
            return b"fresh"

        self.assertEqual(cached_bytes("home", build, ttl=30, now=lambda: 1), b"stale")
        self.assertEqual(n["c"], 0)

    def test_cached_bytes_keeps_body_after_ttl_when_stock_unchanged(self):
        n = {"c": 0}

        def build():
            n["c"] += 1
            return ("v%d" % n["c"]).encode("utf-8")

        self.assertEqual(
            cached_bytes("home", build, ttl=30, now=lambda: 0, revision=lambda: "stock-a"),
            b"v1",
        )
        self.assertEqual(
            cached_bytes("home", build, ttl=30, now=lambda: 31, revision=lambda: "stock-a"),
            b"v1",
        )
        self.assertEqual(n["c"], 1)
        self.assertEqual(
            cached_bytes("home", build, ttl=30, now=lambda: 62, revision=lambda: "stock-a"),
            b"v1",
        )

    def test_cached_bytes_rebuilds_after_ttl_when_stock_changed(self):
        n = {"c": 0}
        marks = {"value": "stock-a"}

        def build():
            n["c"] += 1
            return ("v%d" % n["c"]).encode("utf-8")

        self.assertEqual(
            cached_bytes("home", build, ttl=30, now=lambda: 0, revision=lambda: marks["value"]),
            b"v1",
        )
        self.assertEqual(
            cached_bytes("home", build, ttl=30, now=lambda: 20, revision=lambda: marks["value"]),
            b"v1",
        )
        marks["value"] = "stock-b"
        self.assertEqual(
            cached_bytes("home", build, ttl=30, now=lambda: 31, revision=lambda: marks["value"]),
            b"v2",
        )
        self.assertEqual(n["c"], 2)

    def test_mysql_ok_cached_does_not_reconnect_within_ttl(self):
        import site_data as mod

        calls = {"n": 0}

        class FakeConn(object):
            def close(self):
                return None

        def fake_connect():
            calls["n"] += 1
            return FakeConn()

        old_settings = mod.mysql_settings
        old_connect = mod.mysql_connect
        mod.mysql_settings = lambda: {"enabled": True}
        mod.mysql_connect = fake_connect
        try:
            self.assertTrue(mysql_ok_cached(now=lambda: 10))
            self.assertTrue(mysql_ok_cached(now=lambda: 39))
            self.assertEqual(calls["n"], 1)
            self.assertTrue(mysql_ok_cached(now=lambda: 41))
            self.assertEqual(calls["n"], 2)
        finally:
            mod.mysql_settings = old_settings
            mod.mysql_connect = old_connect


class ProductLineHtmlTests(unittest.TestCase):
    def test_out_of_stock_label_is_not_blue(self):
        card = product_card_html(
            {"sku": "2", "title": "CX-19", "status": "out_of_stock", "status_label": "缺貨"},
            "toysrus",
        )
        self.assertIn("缺貨", card)
        self.assertNotIn("class='stock-in'", card)

    def test_mall_sale_notes_render_as_tags(self):
        card = product_card_html(
            {
                "sku": "4904810077398",
                "title": "【現貨】【アプリ・イベント限定】BEYBLADE X【レアベイ購入チケット対象】",
                "status": "in_stock",
                "status_label": "有貨（現貨・稀有陀螺購買券・應用活動限定）",
            },
            "takaratomymall",
        )
        self.assertIn("sale-tag--event", card)
        self.assertIn("App/活動限定", card)
        self.assertIn("sale-tag--ticket", card)
        self.assertIn("稀有陀螺購買券", card)
        self.assertIn("sale-tag--spot", card)
        self.assertIn(">現貨<", card)
        self.assertIn("有貨", card)
        self.assertNotIn("有貨（現貨）", card)
        self.assertNotIn("有貨（現貨・稀有陀螺購買券・應用活動限定）", card)

    def test_stock_kinds_render_as_tags(self):
        card = product_card_html(
            {
                "sku": "2",
                "title": "【抽選已完】BEYBLADE X",
                "status": "out_of_stock",
                "status_label": "缺貨（抽選已完）",
            },
            "takaratomymall",
        )
        self.assertIn("sale-tag--ended", card)
        self.assertIn(">抽選已完<", card)
        self.assertNotIn("sale-tag--raffle", card)
        self.assertIn("缺貨", card)
        self.assertNotIn("缺貨（抽選已完）", card)

    def test_yen_shop_price_converts_to_hkd(self):
        from site_data import _FX_HKD_CACHE

        _FX_HKD_CACHE["JPY"] = {"rate": 0.05, "at": time.time()}
        card = product_card_html(
            {
                "sku": "3",
                "title": "【預約】BX-55",
                "price": "1600",
                "status": "in_stock",
                "status_label": "有貨（預約）",
            },
            "yodobashi",
        )
        self.assertIn("¥1,600", card)
        self.assertIn("約 HK$80", card)
        self.assertNotIn("HK$1600", card)
        self.assertIn("sale-tag--preorder", card)
        self.assertIn(">預約<", card)
        self.assertIn("data-price='80'", card)

    def test_usd_grid_price_keeps_dollars_and_hkd_estimate(self):
        from site_data import _FX_HKD_CACHE
        from site_pages import model_grid_card_html

        _FX_HKD_CACHE["USD"] = {"rate": 7.8, "at": time.time()}
        card = model_grid_card_html(
            {
                "model": "",
                "items": [
                    {
                        "sku": "B0TEST",
                        "shop_id": "amazon-us-retail",
                        "title": "Cobalt Drake",
                        "price": "22.67",
                        "currency": "USD",
                        "status": "in_stock",
                        "status_label": "有貨",
                    }
                ],
            }
        )
        self.assertIn("US$22.67（約 HK$177）", card)
        self.assertNotIn("USD・美元", card)
        self.assertNotIn("HK$22.67", card)

    def test_amazon_jp_retail_price_uses_jpy_prefix(self):
        from site_data import _FX_HKD_CACHE
        from site_pages import model_grid_card_html, notify_rows_html

        _FX_HKD_CACHE["JPY"] = {"rate": 0.05, "at": time.time()}
        card = model_grid_card_html(
            {
                "model": "BX-01",
                "items": [
                    {
                        "sku": "B0JP",
                        "shop_id": "amazon-jp-retail",
                        "title": "BX-01",
                        "price": "1580",
                        "currency": "JPY",
                        "status": "in_stock",
                        "status_label": "有貨",
                    }
                ],
            }
        )
        self.assertIn("JPY¥1580（約 HK$79）", card)
        self.assertNotIn("¥1,580", card)
        row = notify_rows_html(
            [
                {
                    "at": "2026-08-30 09:00:00",
                    "shop": "Amazon.co.jp 直販",
                    "shop_id": "amazon-jp-retail",
                    "event": "restock",
                    "title": "BX-01",
                    "price": "1580",
                    "currency": "JPY",
                }
            ]
        )
        self.assertIn("JPY¥1580（約 HK$79）", row)

    def test_in_stock_card_includes_tag_and_model(self):
        card = product_card_html(
            {
                "sku": "1",
                "title": "CX-19",
                "status": "in_stock",
                "status_label": "有貨",
                "model": "CX-19",
                "tag": "CX",
            },
            "toysrus",
        )
        self.assertIn("data-tag='CX'", card)
        self.assertIn("data-model='CX-19'", card)
        self.assertIn("class='stock-in'", card)
        self.assertIn("有貨", card)


class NotifyHistoryHtmlTests(unittest.TestCase):
    def test_filter_notify_history_drops_skipped_products(self):
        apply_config(
            {
                "filter": {
                    "skip_phrases": ["Tomica", "SANRIO CHARACTERS", "Hiace"],
                }
            }
        )
        rows = [
            {"title": "Tomica Premium Hiace", "sku": "1", "shop_id": "hobbyland"},
            {"title": "Beyblade X CX-03", "sku": "2", "shop_id": "hobbyland"},
            {"title": "SANRIO CHARACTERS sticker", "sku": "3", "shop_id": "hobbyland"},
        ]
        kept = filter_notify_history(rows)
        self.assertEqual([r["title"] for r in kept], ["Beyblade X CX-03"])

    def test_load_notify_history_mysql_drops_skipped_products(self):
        import site_data as m

        apply_config({"filter": {"skip_phrases": ["Tomica", "變形金剛"]}})
        rows = [
            {"title": "Tomica car", "sku": "t1", "event": "new"},
            {"title": "Beyblade X UX-08", "sku": "b1", "event": "restock"},
            {"title": "變形金剛 陀螺", "sku": "x1", "event": "new"},
        ]
        orig_mysql = m.mysql_settings
        orig_load = m.load_notify_history_mysql
        m.mysql_settings = lambda: {"enabled": True}
        m.load_notify_history_mysql = lambda *a, **k: list(rows)
        try:
            got = load_notify_history(limit=10)
            self.assertEqual([r["title"] for r in got], ["Beyblade X UX-08"])
        finally:
            m.mysql_settings = orig_mysql
            m.load_notify_history_mysql = orig_load

    def test_notify_rows_html_shows_product_thumb(self):
        html = notify_rows_html(
            [
                {
                    "at": "2026-09-08 04:00:00",
                    "shop_id": "hobbyland",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "CX-03",
                    "sku": "933",
                    "url": "https://example.com/p",
                    "change": "無 → 有貨",
                    "image": "https://cdn.example/cx03.jpg",
                    "image_path": "images/hobbyland/933.jpg",
                }
            ]
        )
        self.assertIn("class='thumb'", html)
        self.assertIn("https://cdn.example/cx03.jpg", html)
        self.assertIn("/images/hobbyland/933.jpg", html)

    def test_notify_rows_html_shows_price(self):
        from datetime import date

        html = notify_rows_html(
            [
                {
                    "at": "2026-08-30 09:00:00",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "CX-03",
                    "price": "199",
                    "change": "無 → 有貨",
                }
            ],
            today=date(2026, 8, 30),
        )
        self.assertIn("HK$199", html)

    def test_notify_rows_html_marks_last_days(self):
        from datetime import date

        html = notify_rows_html(
            [
                {
                    "at": "2026-08-30 09:00:00",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "TodayTop",
                    "change": "無 → 有貨",
                },
                {
                    "at": "2026-08-29 04:00:00",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "YdayTop",
                    "change": "無 → 有貨",
                },
                {
                    "at": "2026-08-28 04:00:00",
                    "shop": "ToysRUs",
                    "event": "new",
                    "title": "OlderTop",
                    "change": "無 → 有貨",
                },
            ],
            today=date(2026, 8, 30),
        )
        self.assertIn('class="notify-day"', html)
        self.assertIn("今天", html)
        self.assertIn("昨天", html)
        self.assertIn("2026-08-28", html)
        self.assertLess(html.find("今天"), html.find("TodayTop"))
        self.assertLess(html.find("昨天"), html.find("YdayTop"))

    def test_filter_index_notifies_keeps_latest_five_within_seven_days(self):
        from datetime import datetime

        import site_data as mod

        rows = [
            {
                "at": "2026-08-30 %02d:00:00" % hour,
                "title": "n%s" % hour,
                "change": "無 → 有貨",
            }
            for hour in range(12, 6, -1)
        ]
        rows.append(
            {"at": "2026-08-24 10:00:00", "title": "week", "change": "無 → 有貨"}
        )
        rows.append(
            {"at": "2026-08-23 10:00:00", "title": "old", "change": "無 → 有貨"}
        )
        rows.append(
            {"at": "2026-08-30 11:00:00", "title": "oos", "change": "缺貨 → 缺貨"}
        )
        now = datetime(2026, 8, 30, 12, 0, 0, tzinfo=mod.HKT_TZ)
        kept = filter_index_notifies(rows, now=now, limit=5)
        self.assertEqual([row["title"] for row in kept], ["n12", "n11", "n10", "n9", "n8"])
        week = filter_index_notifies(rows, now=now)
        self.assertEqual(
            [row["title"] for row in week],
            ["n12", "n11", "n10", "n9", "n8", "n7", "week"],
        )

    def test_notify_rows_html_uses_cached_path_when_file_exists(self):
        import site_data as mod

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old_data = mod.DATA_DIR
        old_mysql = mod.mysql_settings
        self.addCleanup(lambda: setattr(mod, "DATA_DIR", old_data))
        self.addCleanup(lambda: setattr(mod, "mysql_settings", old_mysql))
        mod.DATA_DIR = tmp.name
        mod.mysql_settings = lambda: {"enabled": False}
        rel = product_image_path("hobbyland", "PRE-059905")
        dest = os.path.join(tmp.name, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(b"jpeg")
        html = notify_rows_html(
            [
                {
                    "shop_id": "hobbyland",
                    "sku": "PRE-059905",
                    "title": "UX-08",
                    "event": "restock",
                    "change": "缺貨 → 有貨",
                }
            ]
        )
        self.assertIn("class='thumb'", html)
        self.assertIn("/images/hobbyland/PRE-059905.jpg", html)

    def test_notify_rows_html_uses_seen_skus_image_when_history_blank(self):
        import site_data as mod

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old_data = mod.DATA_DIR
        old_mysql = mod.mysql_settings
        self.addCleanup(lambda: setattr(mod, "DATA_DIR", old_data))
        self.addCleanup(lambda: setattr(mod, "mysql_settings", old_mysql))
        self.addCleanup(lambda: apply_config({}))
        mod.DATA_DIR = tmp.name
        mod.mysql_settings = lambda: {"enabled": False}
        apply_config(
            {
                "sources": [
                    {"id": "toytoy", "enabled": True, "state": "toytoy_seen_skus.json"}
                ]
            }
        )
        with open(os.path.join(tmp.name, "toytoy_seen_skus.json"), "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "skus": ["4904810098775"],
                    "products": [
                        {
                            "sku": "4904810098775",
                            "title": "CX-11",
                            "image": "https://shoplineimg.com/shop/cx11.jpg",
                        }
                    ],
                },
                fh,
            )
        html = notify_rows_html(
            [
                {
                    "shop_id": "toytoy",
                    "sku": "4904810098775",
                    "title": "CX-11",
                    "event": "new",
                    "change": "無 → 有貨",
                    "image": None,
                    "image_path": None,
                }
            ]
        )
        self.assertIn("https://shoplineimg.com/shop/cx11.jpg", html)
        self.assertNotIn("src='/images/toytoy/4904810098775.jpg'", html)

    def test_status_page_shows_latest_notifies_and_history_link(self):
        page = render_status_html(
            {"checked_at": "2026-11-08 04:00:00", "ok": True, "shops": []},
            notifies=[
                {
                    "at": "2026-11-08 04:00:00",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "UX-08",
                    "url": "https://example.com/p",
                    "change": "無 → 有貨",
                }
            ],
        )
        self.assertIn("最新通知", page)
        self.assertIn("UX-08", page)
        self.assertIn('href="/history"', page)
        self.assertIn("查看更多", page)
        self.assertLess(page.find("最新通知"), page.find('<h2><a href="/shops">店舖現況</a></h2>'))
        self.assertIn("香港店舖", page)
        self.assertIn(">Amazon<", page)
        self.assertIn('href="/?src=amazon"', page)

    def test_status_page_amazon_tab_hides_hk_rows(self):
        page = render_status_html(
            {"checked_at": "2026-11-08 04:00:00", "ok": True, "shops": []},
            notifies=[
                {
                    "at": "2026-11-08 04:00:00",
                    "shop_id": "hobbyland",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "HK-Blade",
                    "url": "https://example.com/hk",
                    "change": "無 → 有貨",
                },
                {
                    "at": "2026-11-08 04:01:00",
                    "shop_id": "amazon-jp",
                    "shop": "Amazon JP",
                    "event": "restock",
                    "title": "JP-Blade",
                    "url": "https://example.com/jp",
                    "change": "缺貨 → 有貨",
                },
            ],
            src="amazon",
        )
        self.assertIn("JP-Blade", page)
        self.assertNotIn("HK-Blade", page)
        self.assertIn('href="/history?src=amazon"', page)

    def test_status_page_hides_latest_notifies_when_empty(self):
        page = render_status_html(
            {"checked_at": "2026-08-29 04:00:00", "ok": True, "shops": []},
            notifies=[],
        )
        self.assertIn('<a href="/history">最新通知</a>', page)
        self.assertNotIn("<h2>最新通知</h2>", page)
        self.assertNotIn("尚未有通知", page)
        self.assertNotIn("查看更多", page)
        self.assertIn('<h2><a href="/shops">店舖現況</a></h2>', page)
        self.assertNotIn("Status live", page)

    def test_status_page_hides_non_boundary_notifies(self):
        page = render_status_html(
            {"checked_at": "2026-08-29 04:00:00", "ok": True, "shops": []},
            notifies=[
                {
                    "title": "NewOOS",
                    "change": "無 → 缺貨",
                    "event": "new",
                    "url": "https://example.com/o",
                },
                {
                    "title": "BackIn",
                    "change": "缺貨 → 有貨",
                    "event": "restock",
                    "url": "https://example.com/i",
                },
            ],
        )
        self.assertIn("BackIn", page)
        self.assertNotIn("NewOOS", page)

    def test_history_page_shows_non_boundary_notifies(self):
        page = render_history_html(
            [
                {
                    "at": "2026-09-08 04:00:00",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "NewOOS",
                    "url": "https://example.com/o",
                    "change": "無 → 缺貨",
                }
            ]
        )
        self.assertIn("NewOOS", page)
        self.assertIn("無 → 缺貨", page)

    def test_history_page_has_shop_and_model_filters(self):
        page = render_history_html(
            [
                {
                    "at": "2026-09-08 04:00:00",
                    "shop_id": "hobbyland",
                    "shop": "Hobbyland",
                    "event": "new",
                    "title": "UX-08",
                    "model": "UX-08",
                    "url": "https://example.com/p",
                    "change": "無 → 有貨",
                }
            ],
            shops=[{"id": "hobbyland", "label": "Hobbyland"}],
            shop_id="hobbyland",
            model="UX-08",
        )
        self.assertIn("最新通知", page)
        self.assertIn('rel="canonical" href="https://hkbeybladex.com/history"', page)
        self.assertIn("/history?shop=hobbyland", page)
        self.assertIn("model=UX-08", page)
        self.assertIn("Hobbyland", page)
        self.assertIn("UX-08", page)
        self.assertIn("noindex, nofollow", page)
        self.assertIn("filter-store-label", page)
        self.assertIn(">Store</p>", page)
        self.assertIn(">Model</p>", page)
        self.assertNotIn("history-dates", page)
        self.assertNotIn(">Date</p>", page)

    def test_history_page_is_indexable_without_filters(self):
        page = render_history_html([])
        self.assertIn('content="index, follow"', page)
        self.assertNotIn("noindex", page)
        self.assertIn('rel="canonical" href="https://hkbeybladex.com/history"', page)


class ListingDataDirTests(unittest.TestCase):
    def test_status_reads_listings_from_beyblade_data_dir(self):
        import site_data as mod

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old_env = os.environ.get("BEYBLADE_DATA_DIR")

        def restore_env():
            if old_env is None:
                os.environ.pop("BEYBLADE_DATA_DIR", None)
            else:
                os.environ["BEYBLADE_DATA_DIR"] = old_env

        self.addCleanup(restore_env)
        os.environ["BEYBLADE_DATA_DIR"] = tmp.name
        with open(os.path.join(tmp.name, "hobbyland_seen_skus.json"), "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "skus": ["A", "B"],
                    "stock": {"A": "in_stock", "B": "out_of_stock"},
                    "updated_at": "2026-11-08 03:19:03",
                    "products": [
                        {"sku": "A", "title": "UX-01", "status": "in_stock"},
                        {"sku": "B", "title": "BX-02", "status": "out_of_stock"},
                    ],
                },
                fh,
            )
        cfg = {
            "storage": {"mysql": {"enabled": False}},
            "sources": [
                {
                    "id": "hobbyland",
                    "label": "Hobbyland",
                    "state": "hobbyland_seen_skus.json",
                    "enabled": True,
                }
            ],
        }
        status = mod.build_watcher_status(cfg)
        self.assertEqual(status["shops"][0]["sku_count"], 2)
        self.assertEqual(status["shops"][0]["in_stock"], 1)
        self.assertEqual(status["shops"][0]["out_of_stock"], 1)
        products = mod.load_shop_products_for_shop_id("hobbyland", cfg)
        self.assertEqual([item["sku"] for item in products], ["A", "B"])


class ProductImageHtmlTests(unittest.TestCase):
    def test_thumb_prefers_shop_image_and_falls_back_to_ours(self):
        html = product_thumb_html(
            {
                "image": "https://cdn.example/a.jpg",
                "image_path": "images/lastchance/1.jpg",
            }
        )
        self.assertIn("src='https://cdn.example/a.jpg'", html)
        self.assertIn(
            "this.src='https://beybladex-cdn.andyhhh.com/images/lastchance/1.jpg'",
            html,
        )

    def test_thumb_uses_cached_image_when_shop_url_missing(self):
        html = product_thumb_html({"image_path": "images/lastchance/1.jpg"})
        self.assertIn(
            "src='https://beybladex-cdn.andyhhh.com/images/lastchance/1.jpg'",
            html,
        )
        self.assertNotIn("onerror", html)



class ModelGridTests(unittest.TestCase):
    def test_listing_model_code_normalizes_and_parses(self):
        self.assertEqual(listing_model_code({"model": "bx01"}), "BX-01")
        self.assertEqual(listing_model_code({"title": "Wizard CX-04"}), "CX-04")
        self.assertEqual(listing_model_code({"title": "no code here"}), "")
        self.assertEqual(
            listing_model_code(
                {"model": "BX-00", "title": "BX-00 BXG-47 烈風天馬3-70A"}
            ),
            "BXG-47",
        )
        self.assertEqual(
            listing_model_code(
                {"model": "", "title": "DMM 一番賞 Vol.2 G賞"}
            ),
            "KUJI-DMM-V2-G",
        )
        self.assertEqual(
            listing_model_code({"model": "BXA01", "title": "壽司郎"}),
            "BXA-01",
        )
        self.assertEqual(
            listing_model_code(
                {"model": "BX-00", "title": "BX-00 美國隊長 4-70GB & 紅浩克 1-80R"}
            ),
            "BXA-03",
        )
        self.assertEqual(listing_model_code({"title": "BXA-02"}), "BXG-25")
        self.assertEqual(
            listing_model_code({"model": "BX-00", "title": "BX-00 Marvel"}),
            "BXA-04",
        )
        self.assertEqual(
            listing_model_code({"title": "UX-00 翔空天馬 3-70A"}),
            "BXH-10",
        )
        self.assertEqual(
            listing_model_code({"model": "UX-00:AERO:3-70A", "title": "UX-00:AERO:3-70A"}),
            "BXH-10",
        )
        self.assertEqual(
            listing_model_code({"title": "UX-00 翔空天馬 3-70A 紅色"}),
            "BXG-24",
        )

    def test_multi_model_name_is_other_and_marks_every_model(self):
        from site_data import group_tag_key, product_tag_key

        bundle = {
            "sku": "set",
            "shop_id": "h1",
            "title": "CX-16 啟動衝刺套裝 + CX-20 自訂改裝套組",
            "model": "CX-16",
            "tag": "CX",
            "price": "500",
            "status": "in_stock",
        }
        same_set = {
            "sku": "set-b",
            "shop_id": "h2",
            "title": "CX20 自訂改裝套組C + CX16 啟動套裝",
            "model": "CX-20",
            "tag": "CX",
            "price": "480",
            "status": "in_stock",
        }
        single = {
            "sku": "cx16",
            "shop_id": "h1",
            "title": "CX-16 龍王閃擊",
            "model": "CX-16",
            "tag": "CX",
            "price": "100",
            "status": "in_stock",
        }
        packed = {
            "sku": "pack",
            "shop_id": "h3",
            "title": "優惠 Bundle（CX16 + UX03 + 自選 BX25 / BX43）",
            "model": "CX-16",
            "tag": "CX",
            "price": "900",
            "status": "in_stock",
        }
        self.assertEqual(listing_model_code(bundle), "CX-16+CX-20")
        self.assertEqual(listing_model_code(same_set), "CX-16+CX-20")
        self.assertEqual(listing_model_code(single), "CX-16")
        self.assertEqual(listing_model_code(packed), "BX-25+BX-43+CX-16+UX-03")
        self.assertEqual(product_tag_key(bundle), "other")
        groups = group_listings_by_model([single, bundle, same_set, packed])
        by_model = {group["model"]: group for group in groups}
        self.assertEqual(len(by_model["CX-16"]["items"]), 1)
        self.assertEqual(len(by_model["CX-16+CX-20"]["items"]), 2)
        self.assertEqual(group_tag_key(by_model["CX-16+CX-20"]), "other")
        page = render_models_html([single, bundle, same_set, packed])
        other_at = page.index("id='models-other'")
        self.assertLess(page.index("data-model='CX-16'"), other_at)
        self.assertLess(other_at, page.index("catalog-card__id'>CX-16 · CX-20"))
        self.assertLess(other_at, page.index("catalog-card__id'>BX-25 · BX-43 · CX-16 · UX-03"))
        cx = render_models_html([single, bundle], tag_filter="CX")
        self.assertIn("data-model='CX-16'", cx)
        self.assertNotIn("CX-16 · CX-20", cx)
        other = render_models_html([single, bundle, packed], tag_filter="other")
        self.assertIn("CX-16 · CX-20", other)
        self.assertIn("BX-25 · BX-43 · CX-16 · UX-03", other)
        self.assertNotIn("龍王閃擊", other)

    def test_group_merges_same_model_in_alpha_order(self):
        groups = group_listings_by_model(
            [
                {"model": "UX-01", "sku": "a", "shop_id": "s1", "title": "Later"},
                {"model": "BX-02", "sku": "b", "shop_id": "s1", "title": "First"},
                {"model": "BX-02", "sku": "c", "shop_id": "s2", "title": "First again"},
            ]
        )
        self.assertEqual([group["model"] for group in groups], ["BX-02", "UX-01"])
        self.assertEqual(len(groups[0]["items"]), 2)

    def test_group_keeps_skus_without_a_model(self):
        groups = group_listings_by_model(
            [
                {"sku": "1", "shop_id": "a", "title": "Zebra part"},
                {"sku": "2", "shop_id": "a", "title": "Apple part"},
            ]
        )
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["model"], "")
        self.assertEqual(groups[0]["items"][0]["title"], "Apple part")
        self.assertEqual(groups[1]["items"][0]["title"], "Zebra part")

    def test_models_page_merges_stock_and_uses_cheapest_notify_image(self):
        import parts_catalog
        import site_pages

        with tempfile.TemporaryDirectory() as dest:
            with open(os.path.join(dest, "products.json"), "w", encoding="utf-8") as fh:
                fh.write("{}")
            site_pages._CATALOG_PRODUCT_CACHE["stamp"] = None
            with mock.patch.object(parts_catalog, "PARTS_DIR", dest):
                page = self._render_merged_models_page()
        button = page.split("class='catalog-card__hit'", 1)[1].split("</a>", 1)[0]
        self.assertIn("src='https://cdn.example/cheap.jpg'", button)
        self.assertNotIn("expensive.jpg", button)
        self.assertNotIn("old.jpg", button)
        self.assertEqual(page.count("<article class='catalog-card product-card'"), 4)
        self.assertIn("out.jpg", page)
        self.assertIn(explore_href("https://b.example/2"), page)
        self.assertIn(explore_href("https://c.example/6"), page)
        self.assertNotIn("2 間店", page)
        self.assertNotIn("最低 HK$", page)
        self.assertIn("HK$120 – HK$200", button)
        self.assertIn(">有貨<", button)
        self.assertNotIn("缺貨", button)
        marker = "<h2 class='catalog-card__name'>UX-10 sold out</h2>"
        start = page.rfind("<article class='catalog-card product-card'", 0, page.index(marker))
        sold = page[start:page.find("</article>", start)]
        self.assertIn("缺貨", sold)
        self.assertIn("HK$90", sold)
        self.assertIn('href="/product?stock=in"', page)
        self.assertIn('href="/product?stock=out"', page)
        self.assertIn("有貨 3", page)
        self.assertIn("缺貨 2", page)
        self.assertIn("class='stock-out'", page)
        self.assertIn("class='stock-in'", page)
        self.assertNotIn("catalog-card__shops", page)
        self.assertNotIn("ShopA", button)
        self.assertNotIn("ShopB", button)
        self.assertIn("ShopA", page)
        self.assertIn("ShopB", page)
        self.assertIn('id="model-modal"', page)
        self.assertIn("repeat(3,minmax(0,1fr))", page)
        self.assertIn("repeat(6,minmax(0,1fr))", page)
        self.assertIn("repeat(8,minmax(0,1fr))", page)
        self.assertIn("object-fit:contain", page)
        self.assertIn("letter-spacing:0", page)
        self.assertIn("text-transform:none", page)
        self.assertIn("BX-01", page)
        self.assertIn("Mystery blade", page)
        self.assertIn("Another mystery", page)
        self.assertIn("<h1 class=\"page-title\">全部現貨</h1>", page)
        self.assertIn("全部現貨 · ", page)
        self.assertIn('href="/shop/all?stock=in">列表</a>', page)
        self.assertIn('href="/product?tag=BX"', page)

    def _render_merged_models_page(self):
        return render_models_html(
            [
                {
                    "sku": "1",
                    "shop_id": "h1",
                    "shop_label": "ShopA",
                    "title": "BX-01 Dran Sword",
                    "model": "BX-01",
                    "tag": "BX",
                    "price": "200",
                    "url": "https://a.example/1",
                    "status": "in_stock",
                    "image": "https://cdn.example/expensive.jpg",
                    "image_path": "images/h1/1.jpg",
                },
                {
                    "sku": "2",
                    "shop_id": "h2",
                    "shop_label": "ShopB",
                    "title": "BX-01 Dran Sword",
                    "model": "BX-01",
                    "tag": "BX",
                    "price": "120",
                    "url": "https://b.example/2",
                    "status": "in_stock",
                    "image": "https://cdn.example/cheap.jpg",
                },
                {
                    "sku": "3",
                    "shop_id": "h1",
                    "shop_label": "ShopA",
                    "title": "UX-10 sold out",
                    "model": "UX-10",
                    "tag": "UX",
                    "price": "90",
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                    "image": "https://cdn.example/out.jpg",
                },
                {
                    "sku": "6",
                    "shop_id": "h3",
                    "shop_label": "ShopC",
                    "title": "BX-01 Dran Sword old",
                    "model": "BX-01",
                    "tag": "BX",
                    "price": "50",
                    "url": "https://c.example/6",
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                    "image": "https://cdn.example/old.jpg",
                },
                {
                    "sku": "4",
                    "shop_id": "h1",
                    "shop_label": "ShopA",
                    "title": "Mystery blade",
                    "price": "50",
                    "url": "https://a.example/4",
                    "status": "in_stock",
                    "image": "https://cdn.example/mystery.jpg",
                },
                {
                    "sku": "5",
                    "shop_id": "h1",
                    "shop_label": "ShopA",
                    "title": "Another mystery",
                    "price": "40",
                    "url": "https://a.example/5",
                    "status": "in_stock",
                },
            ]
        )

    def test_model_card_prefers_synced_browser_image_over_shop_cache(self):
        import site_pages

        with tempfile.TemporaryDirectory() as dest:
            with open(os.path.join(dest, "catalog.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "products": [
                            {
                                "id": "BX-01",
                                "kind": "set",
                                "image": "/browser/assets/site__Blade__BX-01.png",
                            }
                        ]
                    },
                    fh,
                )
            with open(os.path.join(dest, "i18n.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {"BX-01": {"zh-HK": "BX-01 翔龍神劍 3-60F", "en": "BX-01 DRANSWORD"}},
                    fh,
                )
            site_pages._BROWSER_CATALOG_CACHE["stamp"] = None
            with mock.patch.object(site_pages, "browser_catalog_dir", return_value=dest):
                page = render_models_html(
                    [
                        {
                            "sku": "1",
                            "shop_id": "moonroadhk",
                            "title": "BX-01 店名標題",
                            "model": "BX-01",
                            "tag": "BX",
                            "price": "120",
                            "status": "in_stock",
                            "image": "https://cdn.example/shop.jpg",
                            "image_path": "images/moonroadhk/1.jpg",
                        }
                    ]
                )
        button = page.split("class='catalog-card__hit'", 1)[1].split("</a>", 1)[0]
        self.assertIn("src='/browser/assets/site__Blade__BX-01.png'", button)
        self.assertIn("<h2 class='catalog-card__name'>翔龍神劍 3-60F</h2>", button)
        self.assertNotIn("shop.jpg", button.split("onerror", 1)[0])
        self.assertNotIn("店名標題", button)

    def test_model_card_uses_official_catalog_name_and_image(self):
        import parts_catalog
        import site_pages

        with tempfile.TemporaryDirectory() as dest:
            with open(os.path.join(dest, "products.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "BXG-47": {
                            "id": "BXG-47",
                            "name_zh": "BXG-47 暴風天馬 3-70RA",
                            "image_path": "images/products/BXG-47.jpg",
                        }
                    },
                    fh,
                )
            site_pages._CATALOG_PRODUCT_CACHE["stamp"] = None
            with mock.patch.object(parts_catalog, "PARTS_DIR", dest):
                page = render_models_html(
                    [
                        {
                            "sku": "1",
                            "shop_id": "h1",
                            "title": "BX-00 烈風天馬3-70RA",
                            "model": "BXG-47",
                            "tag": "BX",
                            "price": "100",
                            "status": "in_stock",
                            "image": "https://shop.example/listing.jpg",
                        }
                    ]
                )
        button = page.split("class='catalog-card__hit'", 1)[1].split("</a>", 1)[0]
        self.assertIn("<h2 class='catalog-card__name'>暴風天馬 3-70RA</h2>", button)
        self.assertIn("/parts-images/products/BXG-47.jpg", button)
        self.assertNotIn("烈風天馬", button)
        self.assertNotIn("listing.jpg", button)
        self.assertIn("letter-spacing:0;text-transform:none", page)

    def test_accessory_model_card_uses_official_tool_name_and_image(self):
        page = render_models_html(
            [
                {
                    "sku": "1",
                    "shop_id": "h1",
                    "title": "BX-18 某店旋風發射器",
                    "model": "BX-18",
                    "tag": "BX",
                    "price": "80",
                    "status": "in_stock",
                    "image": "https://shop.example/launcher.jpg",
                }
            ]
        )
        button = page.split("class='catalog-card__hit'", 1)[1].split("</a>", 1)[0]
        self.assertIn("<h2 class='catalog-card__name'>旋風發射器</h2>", button)
        self.assertIn("https://beybladehub.app/accessories/raw/BX-18.webp", button)
        self.assertNotIn("某店旋風發射器", button)
        self.assertNotIn("launcher.jpg", button)

    def test_models_tag_filter_keeps_matching_groups(self):
        items = [
            {
                "sku": "cx",
                "shop_id": "h1",
                "shop_label": "ShopA",
                "title": "CX-04 Wizard",
                "model": "CX-04",
                "price": "80",
                "url": "https://a.example/cx",
                "status": "in_stock",
                "image": "https://cdn.example/cx.jpg",
            },
            {
                "sku": "bx",
                "shop_id": "h1",
                "shop_label": "ShopA",
                "title": "BX-01 Dran",
                "model": "BX-01",
                "price": "90",
                "url": "https://a.example/bx",
                "status": "in_stock",
                "image": "https://cdn.example/bx.jpg",
            },
        ]
        page = render_models_html(items, tag_filter="CX")
        self.assertIn("CX-04", page)
        self.assertIn("https://cdn.example/cx.jpg", page)
        self.assertNotIn("BX-01", page)
        self.assertNotIn("bx.jpg", page)
        self.assertIn('class="filter on" href="/product?tag=CX"', page)
        self.assertIn("CX [1]", page)
        self.assertIn("BX [1]", page)
        self.assertIn('href="/product?stock=in&amp;tag=CX"', page)

    def test_models_kuji_filter_is_separate_from_other(self):
        items = [
            {
                "sku": "kuji",
                "shop_id": "h1",
                "title": "BeybladeX 陀螺 x DMM 一番賞 Vol.2 G賞",
                "tag": "other",
                "price": "80",
                "status": "in_stock",
                "image": "https://cdn.example/kuji.jpg",
            },
            {
                "sku": "misc",
                "shop_id": "h1",
                "title": "Mystery blade",
                "tag": "other",
                "price": "40",
                "status": "in_stock",
            },
        ]
        page = render_models_html(items)
        self.assertIn("一番賞 [1]", page)
        self.assertIn("other [1]", page)
        self.assertIn('href="/product?tag=kuji"', page)
        kuji = render_models_html(items, tag_filter="kuji")
        self.assertIn("KUJI-DMM-V2-G", kuji)
        self.assertIn("https://cdn.example/kuji.jpg", kuji)
        self.assertNotIn("Mystery blade", kuji)
        other = render_models_html(items, tag_filter="other")
        self.assertIn("Mystery blade", other)
        self.assertNotIn("KUJI-DMM-V2-G", other)

    def test_models_all_page_puts_kuji_and_other_last(self):
        page = render_models_html(
            [
                {
                    "sku": "bx",
                    "shop_id": "h1",
                    "title": "BX-01 Dran",
                    "model": "BX-01",
                    "price": "90",
                    "status": "in_stock",
                },
                {
                    "sku": "kuji",
                    "shop_id": "h1",
                    "title": "DMM 一番賞 Vol.2 G賞",
                    "price": "80",
                    "status": "in_stock",
                },
                {
                    "sku": "misc",
                    "shop_id": "h1",
                    "title": "Mystery blade",
                    "price": "40",
                    "status": "in_stock",
                },
            ]
        )
        bx = page.index("data-model='BX-01'")
        kuji = page.index("id='models-kuji'")
        other = page.index("id='models-other'")
        self.assertLess(bx, kuji)
        self.assertLess(kuji, other)
        self.assertIn("<h2>一番賞</h2>", page)
        self.assertIn("<h2>other</h2>", page)
        self.assertLess(page.index("KUJI-DMM-V2-G"), page.index("Mystery blade"))

    def test_models_all_page_puts_bxg_after_main_lines(self):
        page = render_models_html(
            [
                {
                    "sku": "cx",
                    "shop_id": "h1",
                    "title": "CX-01",
                    "model": "CX-01",
                    "tag": "CX",
                    "price": "90",
                    "status": "in_stock",
                },
                {
                    "sku": "wizard",
                    "shop_id": "h1",
                    "title": "BXG-43 Wizard",
                    "model": "BXG-43",
                    "tag": "CX",
                    "price": "120",
                    "status": "in_stock",
                    "stock_changed_at": "2026-08-01 12:00:00",
                },
                {
                    "sku": "eva",
                    "shop_id": "h1",
                    "title": "BXG-57 Evangelion",
                    "model": "BXG-57",
                    "tag": "CX",
                    "price": "130",
                    "status": "in_stock",
                },
                {
                    "sku": "sushiro",
                    "shop_id": "h1",
                    "title": "BXA-01",
                    "model": "BXA-01",
                    "tag": "BX",
                    "price": "80",
                    "status": "in_stock",
                },
                {
                    "sku": "aero",
                    "shop_id": "h1",
                    "title": "UX-00 翔空天馬 3-70A",
                    "model": "UX-00:AERO:3-70A",
                    "tag": "UX",
                    "price": "140",
                    "status": "in_stock",
                },
            ]
        )
        self.assertLess(page.index("data-model='CX-01'"), page.index("id='models-bxg'"))
        self.assertLess(page.index("id='models-bxg'"), page.index("data-model='BXG-43'"))
        self.assertLess(page.index("id='models-bxg'"), page.index("data-model='BXA-01'"))
        self.assertLess(page.index("id='models-bxg'"), page.index("data-model='BXH-10'"))
        self.assertIn("<h2>BX+</h2>", page)
        self.assertIn("BX+ [4]", page)
        self.assertIn('href="/product?tag=BXG"', page)
        self.assertNotIn("更新 ", page)
        filtered = render_models_html(
            [
                {
                    "sku": "wizard",
                    "shop_id": "h1",
                    "title": "BXG-43 Wizard",
                    "model": "BXG-43",
                    "tag": "CX",
                    "price": "120",
                    "status": "in_stock",
                },
                {
                    "sku": "cx",
                    "shop_id": "h1",
                    "title": "CX-01",
                    "model": "CX-01",
                    "tag": "CX",
                    "price": "90",
                    "status": "in_stock",
                },
            ],
            tag_filter="BXG",
        )
        self.assertIn("data-model='BXG-43'", filtered)
        self.assertNotIn("data-model='CX-01'", filtered)

    def test_models_sort_by_publish_time_and_modal_lists_name(self):
        import site_pages

        with tempfile.TemporaryDirectory() as dest:
            with open(os.path.join(dest, "catalog.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "products": [
                            {
                                "id": "BX-01",
                                "kind": "set",
                                "image": "/browser/assets/bx-01.png",
                                "releaseDate": "2023-07-15",
                            },
                            {
                                "id": "UX-10",
                                "kind": "set",
                                "image": "/browser/assets/ux-10.png",
                                "releaseDate": "2025-01-02",
                            },
                        ]
                    },
                    fh,
                )
            with open(os.path.join(dest, "i18n.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "BX-01": {"zh-HK": "BX-01 翔龍神劍 3-60F"},
                        "UX-10": {"zh-HK": "UX-10 客製化套裝"},
                    },
                    fh,
                )
            site_pages._BROWSER_CATALOG_CACHE["stamp"] = None
            with mock.patch.object(site_pages, "browser_catalog_dir", return_value=dest):
                page = render_models_html(
                    [
                        {
                            "sku": "1",
                            "shop_id": "h1",
                            "shop_label": "ShopA",
                            "title": "BX-01 old",
                            "model": "BX-01",
                            "price": "100",
                            "status": "in_stock",
                            "stock_changed_at": "2026-01-01 10:00:00",
                        },
                        {
                            "sku": "2",
                            "shop_id": "h2",
                            "shop_label": "ShopB",
                            "title": "UX-10 new",
                            "model": "UX-10",
                            "price": "200",
                            "status": "in_stock",
                        },
                    ],
                    sort_filter="new",
                )
        self.assertLess(page.index("data-model='UX-10'"), page.index("data-model='BX-01'"))
        self.assertIn('class="filter on" href="/product?sort=new"', page)
        self.assertIn("data-detail='HK$200 · 1 間店 · 發售日 2025-01-02'", page)
        self.assertNotIn("更新 ", page)
        self.assertIn('title.textContent=code?code+" · "+name:name', page)
        self.assertIn("font-size:10px;letter-spacing:.04em;padding:2px 6px", page)
        self.assertIn("width:72px;height:72px", page)
        head_at = page.index('<div class="model-modal__head">')
        close_at = page.index('<button type="button" class="model-modal__close"')
        scroll_at = page.index('<div class="model-modal__scroll">')
        self.assertLess(head_at, close_at)
        self.assertLess(close_at, scroll_at)

    def test_models_stock_filter_keeps_matching_offers(self):
        items = [
            {
                "sku": "1",
                "shop_id": "h1",
                "shop_label": "ShopA",
                "title": "BX-01 Dran Sword",
                "model": "BX-01",
                "price": "200",
                "url": "https://a.example/1",
                "status": "in_stock",
                "image": "https://cdn.example/in.jpg",
            },
            {
                "sku": "2",
                "shop_id": "h2",
                "shop_label": "ShopB",
                "title": "BX-01 Dran Sword",
                "model": "BX-01",
                "price": "50",
                "url": "https://b.example/2",
                "status": "out_of_stock",
                "status_label": "缺貨",
                "image": "https://cdn.example/out.jpg",
            },
            {
                "sku": "3",
                "shop_id": "h1",
                "shop_label": "ShopA",
                "title": "UX-10 sold out",
                "model": "UX-10",
                "price": "90",
                "status": "out_of_stock",
                "image": "https://cdn.example/ux.jpg",
            },
        ]
        instock = render_models_html(items, stock_filter="in_stock")
        self.assertEqual(instock.count("<article class='catalog-card product-card'"), 1)
        self.assertIn(explore_href("https://a.example/1"), instock)
        self.assertIn(explore_href("https://b.example/2"), instock)
        self.assertNotIn("UX-10", instock)
        self.assertIn('class="filter on" href="/product?stock=in"', instock)
        self.assertIn('href="/product?stock=in&amp;tag=BX"', instock)
        self.assertIn("catalog-card__subtitle price-in", instock)
        self.assertIn("<span class='price-in'>HK$200</span>", instock)
        self.assertIn("<span class='price-out'>HK$50</span>", instock)
        soldout = render_models_html(items, stock_filter="out_of_stock")
        self.assertEqual(soldout.count("<article class='catalog-card product-card'"), 2)
        self.assertIn("UX-10", soldout)
        self.assertIn(explore_href("https://b.example/2"), soldout)
        self.assertIn(explore_href("https://a.example/1"), soldout)
        self.assertIn("catalog-card__subtitle price-out", soldout)
        self.assertIn('class="filter on" href="/product?stock=out"', soldout)
        both = render_models_html(items, tag_filter="UX", stock_filter="out_of_stock")
        self.assertIn("UX-10", both)
        self.assertNotIn("BX-01", both)
        self.assertIn('class="filter on" href="/product?stock=out&amp;tag=UX"', both)

    def test_product_page_splits_tclub_and_takara_tomy_mall(self):
        items = [
            {
                "sku": "hk",
                "shop_id": "hobby",
                "shop_label": "HobbyLand",
                "title": "BX-01 Dran",
                "model": "BX-01",
                "tag": "BX",
                "price": "100",
                "status": "in_stock",
            },
            {
                "sku": "tc",
                "shop_id": "tclub",
                "shop_label": "TClub",
                "title": "CX-09 TClub",
                "model": "CX-09",
                "tag": "CX",
                "price": "88",
                "status": "in_stock",
            },
            {
                "sku": "tc-only",
                "shop_id": "tclub",
                "shop_label": "TClub",
                "title": "CX-00:S4-70V",
                "model": "CX-00:S4-70V",
                "tag": "CX",
                "price": "99",
                "status": "in_stock",
            },
            {
                "sku": "tc-shared",
                "shop_id": "tclub",
                "shop_label": "TClub",
                "title": "BX-00:4-60F",
                "model": "BX-00:4-60F",
                "tag": "BX",
                "price": "120",
                "status": "in_stock",
            },
            {
                "sku": "hk-shared",
                "shop_id": "hobby",
                "shop_label": "HobbyLand",
                "title": "BX-00:4-60F",
                "model": "BX-00:4-60F",
                "tag": "BX",
                "price": "130",
                "status": "in_stock",
            },
            {
                "sku": "tc-plus",
                "shop_id": "tclub",
                "shop_label": "TClub",
                "title": "BXG-47 only here",
                "model": "BXG-47",
                "tag": "BXG",
                "price": "150",
                "status": "in_stock",
            },
            {
                "sku": "mall",
                "shop_id": "takaratomymall",
                "shop_label": "Takara Tomy Mall",
                "title": "【抽選】【アプリ・イベント限定】UX-04 Mall",
                "model": "UX-04",
                "tag": "UX",
                "price": "1980",
                "status": "in_stock",
                "status_label": "有貨（抽選）",
                "remark": "抽選",
            },
        ]
        page = render_models_html(items, shops=[])
        self.assertIn("id='models-tclub'", page)
        tclub = page.split("id='models-tclub'", 1)[1].split("</section>", 1)[0]
        mall = page.split("id='models-takaratomymall'", 1)[1].split("</section>", 1)[0]
        main = page.split("id='models-tclub'", 1)[0]
        self.assertIn("<h2>TClub</h2>", tclub)
        self.assertIn("data-model='CX-00:S4-70V'", tclub)
        self.assertIn("data-model='BXG-47'", tclub)
        self.assertNotIn("data-model='CX-09'", tclub)
        self.assertNotIn("data-model='BX-00:4-60F'", tclub)
        self.assertNotIn("data-model='BX-01'", tclub)
        self.assertIn("data-model='CX-09'", main)
        self.assertIn("data-model='BX-00:4-60F'", main)
        self.assertIn("<h2>Takara Tomy Mall</h2>", mall)
        self.assertIn("data-model='UX-04'", mall)
        visible = mall.split("model-offer-list", 1)[0]
        self.assertIn("sale-tag--raffle", visible)
        self.assertIn(">抽選<", visible)
        self.assertIn("sale-tag--event", visible)
        self.assertIn("App/活動限定", visible)
        self.assertNotIn("data-model='UX-04'", main)
        self.assertLess(page.index("id='models-tclub'"), page.index("id='models-takaratomymall'"))
        from site_pages import render_model_detail_html

        detail = render_model_detail_html("UX-04", items)
        self.assertIn("sale-tag--raffle", detail)
        self.assertIn(">抽選<", detail)
        self.assertIn("App/活動限定", detail)
        focused = render_models_html(items, shop_filter="tclub", shops=[])
        self.assertNotIn("id='models-tclub'", focused)
        self.assertIn("data-model='CX-09'", focused)
        self.assertNotIn("data-model='UX-04'", focused)

    def test_amazon_us_retail_is_a_us_edition_section(self):
        items = [
            {
                "sku": "hk",
                "shop_id": "hobby",
                "title": "BX-01 Dran",
                "model": "BX-01",
                "tag": "BX",
                "price": "100",
                "status": "in_stock",
            },
            {
                "sku": "us-bx",
                "shop_id": "amazon-us-retail",
                "title": "Beyblade X BX-01 Dran Sword",
                "model": "BX-01",
                "tag": "BX",
                "price": "14.99",
                "status": "in_stock",
            },
            {
                "sku": "us-other",
                "shop_id": "amazon-us-retail",
                "title": "Beyblade X Clash & Carry Beystadium",
                "model": "",
                "tag": "other",
                "price": "49.99",
                "status": "in_stock",
            },
        ]
        page = render_models_html(items, shops=[])
        us = page.split("id='models-amazon-us-retail'", 1)[1].split("</section>", 1)[0]
        main = page.split("id='models-amazon-us-retail'", 1)[0]
        self.assertIn("<h2>美版</h2>", us)
        self.assertIn("data-sku='us-bx'", us)
        self.assertIn("data-sku='us-other'", us)
        self.assertIn("data-model=''", us)
        self.assertNotIn(">/product/BX-01<", us)
        self.assertNotIn("href='/product/BX-01'", us)
        self.assertIn("Beyblade X BX-01 Dran Sword", us)
        self.assertIn("data-model='BX-01'", main)
        self.assertNotIn("data-sku='us-bx'", main)
        self.assertNotIn("data-sku='us-other'", main)
        bx = render_models_html(items, tag_filter="BX", shops=[])
        self.assertIn("data-sku='hk'", bx)
        self.assertNotIn("id='models-amazon-us-retail'", bx)
        self.assertNotIn("data-sku='us-bx'", bx)
        focused = render_models_html(items, shop_filter="amazon-us-retail", shops=[])
        self.assertEqual(focused.count("id='models-amazon-us-retail'"), 1)
        self.assertIn("<h2>美版</h2>", focused)
        self.assertNotIn("id='models-bxg'", focused)
        self.assertNotIn("id='models-other'", focused)
        self.assertNotIn(">CX [", focused)
        self.assertNotIn(">BX [", focused)
        self.assertNotIn(">UX [", focused)
        self.assertIn("data-sku='us-bx'", focused)
        self.assertIn("data-sku='us-other'", focused)
        self.assertIn("data-model=''", focused)
        self.assertNotIn("data-sku='hk'", focused)
        from site_data import group_tag_key, product_line_fields, product_tag_key
        from site_pages import render_model_detail_html

        us_item = items[1]
        self.assertEqual(listing_model_code(us_item), "")
        self.assertEqual(product_tag_key(us_item), "")
        self.assertEqual(product_line_fields(us_item), {"model": "", "tag": "other"})
        self.assertEqual(group_tag_key({"model": "BX-01", "items": [us_item]}), "")
        detail = render_model_detail_html("BX-01", items)
        self.assertNotIn("Beyblade X BX-01 Dran Sword", detail or "")
        self.assertIn("BX-01 Dran", detail or "")

    def test_product_page_shop_grid_filters_models(self):
        shops = [
            {"id": "hobby", "label": "HobbyLand"},
            {"id": "amazon", "label": "Amazon.co.jp 直販"},
        ]
        items = [
            {
                "sku": "1",
                "shop_id": "hobby",
                "title": "BX-01 Dran",
                "model": "BX-01",
                "tag": "BX",
                "price": "100",
                "status": "in_stock",
            },
            {
                "sku": "2",
                "shop_id": "amazon",
                "title": "CX-02 Wizard",
                "model": "CX-02",
                "tag": "CX",
                "price": "200",
                "status": "in_stock",
            },
        ]
        page = render_models_html(items, shops=shops)
        self.assertIn('id="all-stock"', page)
        self.assertIn('class="model-filters"', page)
        self.assertNotIn(">全部現貨</p>", page)
        self.assertEqual(page.count('class="filter-combo shop-chips"'), 1)
        self.assertNotIn(">海外店舖</p>", page)
        self.assertIn('value="全部現貨"', page)
        self.assertIn('href="/product" data-label="全部現貨"', page)
        self.assertIn('href="/product?shop=hobby" data-label="HobbyLand"', page)
        self.assertIn('href="/product?shop=amazon"', page)
        self.assertIn('<h1 class="page-title">全部現貨</h1>', page)
        self.assertIn('class="filter on" href="/product">圖庫</a>', page)
        self.assertIn('href="/shop/all?stock=in">列表</a>', page)
        listed = render_models_html(items, stock_filter="in_stock", shops=shops, layout="list")
        self.assertIn("class='sku-row product-card'", listed)
        self.assertNotIn("<div class='model-grid'", listed)
        self.assertIn('href="/shop/all?stock=in" data-label="全部現貨"', listed)
        self.assertIn('href="/shop/all?stock=in&amp;shop=amazon"', listed)
        self.assertIn('class="filter on" href="/shop/all?stock=in">列表</a>', listed)
        self.assertIn('href="/product">圖庫</a>', listed)
        self.assertIn("noindex, nofollow", listed)
        filtered = render_models_html(items, shop_filter="hobby", shops=shops)
        self.assertIn("BX-01", filtered)
        self.assertNotIn("CX-02", filtered)
        self.assertIn('value="HobbyLand"', filtered)
        self.assertIn('class="filter on" href="/product?shop=hobby"', filtered)
        self.assertIn('href="/product?stock=in&amp;shop=hobby"', filtered)
        self.assertIn("noindex, nofollow", filtered)

    def test_nav_links_model_grid_and_stock_list_stays_rows(self):
        nav = site_nav_html()
        self.assertIn('href="/product">全部現貨</a>', nav)
        self.assertIn('href="/shop/all?stock=in">列表</a>', nav)
        page = render_products_html(
            {"id": "all", "label": "全部"},
            [
                {
                    "sku": "1",
                    "title": "BX-01 Dran",
                    "model": "BX-01",
                    "price": "100",
                    "url": "https://a.example/1",
                    "status": "in_stock",
                    "status_label": "有貨",
                    "image": "https://cdn.example/a.jpg",
                }
            ],
            stock_filter="in_stock",
        )
        self.assertIn("class='sku-row product-card'", page)
        self.assertNotIn("<div class='model-grid'", page)
        self.assertNotIn("class='catalog-card product-card'", page)

    def test_sitemap_includes_models_page(self):
        xml = sitemap_xml({"sources": []})
        self.assertIn("https://hkbeybladex.com/product", xml)

    def test_sitemap_lists_browser_items_from_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "catalog.json"), "w", encoding="utf-8") as fh:
                json.dump({"products": [{"id": "BX-01"}], "parts": []}, fh)
            xml = sitemap_xml({"sources": []}, browser_catalog_dir_override=td)
        self.assertIn("https://hkbeybladex.com/browser/item/BX-01", xml)
        self.assertIn("https://hkbeybladex.com/browser<", xml)

    def test_model_detail_page_is_indexable_product(self):
        import parts_catalog
        import site_pages
        from site_pages import render_model_detail_html

        with tempfile.TemporaryDirectory() as dest:
            with open(os.path.join(dest, "products.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "BX-52": {
                            "id": "BX-52",
                            "name_zh": "輝耀龍騎士（BX-52）",
                            "name_en": "Wizard Arrow",
                            "jan": "4904810085553",
                            "description": "左迴旋攻擊型入門組。",
                            "released_on": "2026-10-10",
                            "bey_type": "攻擊型",
                            "stock_combo": "6-60LC",
                        }
                    },
                    fh,
                )
            site_pages._CATALOG_PRODUCT_CACHE["stamp"] = None
            with mock.patch.object(parts_catalog, "PARTS_DIR", dest):
                page = render_model_detail_html(
                    "BX-52",
                    [
                        {
                            "sku": "1",
                            "shop_id": "h1",
                            "shop_label": "ShopA",
                            "title": "BX-52",
                            "model": "BX-52",
                            "price": "188",
                            "url": "https://a.example/1",
                            "status": "in_stock",
                        }
                    ],
                )
                missing = render_model_detail_html("NOPE", [])
                xml = sitemap_xml({"sources": []})
        self.assertIsNone(missing)
        self.assertIn(
            "<title>BX-52 輝耀龍騎士 Wizard Arrow 香港現貨 · HK BeybladeX Watch</title>",
            page,
        )
        self.assertIn('content="index, follow"', page)
        self.assertNotIn("noindex", page)
        self.assertIn('href="https://hkbeybladex.com/product/BX-52"', page)
        self.assertIn('"@type": "Product"', page)
        self.assertIn("AggregateOffer", page)
        self.assertIn("HKD", page)
        self.assertIn("4904810085553", page)
        self.assertIn("ShopA", page)
        self.assertIn("左迴旋攻擊型入門組", page)
        self.assertIn("https://hkbeybladex.com/product/BX-52", xml)

    def test_model_detail_uses_browser_item_layout(self):
        import parts_catalog
        import site_pages
        from site_pages import render_model_detail_html

        with tempfile.TemporaryDirectory() as dest, tempfile.TemporaryDirectory() as parts:
            with open(os.path.join(dest, "catalog.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "products": [
                            {
                                "id": "BX-44",
                                "kind": "set",
                                "line": "BX",
                                "manufacturer": "tt",
                                "description": {"zh-HK": "高穩定性的刃擊環。"},
                                "price": "¥1,500",
                                "releaseDate": "2025-06-27",
                                "partIds": ["BL-1"],
                                "image": "/browser/assets/set.png",
                                "shops": [
                                    {
                                        "label": "Takara Tomy",
                                        "url": "https://beyblade.takaratomy.co.jp/beyblade-x/lineup/bx44.html",
                                    }
                                ],
                            },
                            {
                                "id": "BX44",
                                "kind": "package",
                                "image": "/browser/assets/pack-0.jpg",
                                "images": [
                                    "/browser/assets/pack-0.jpg",
                                    "/browser/assets/pack-1.png",
                                ],
                                "partIds": ["BX-44"],
                            },
                        ],
                        "parts": [
                            {
                                "id": "BL-1",
                                "kind": "blade",
                                "image": "/browser/assets/blade.png",
                            }
                        ],
                    },
                    fh,
                )
            with open(os.path.join(dest, "i18n.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "BX-44": {"zh-HK": "BX-44 三角龍壓M-85BS", "en": "BX-44 TRICERAPRESS"},
                        "BL-1": {"zh-HK": "三角龍壓刃", "en": "Tricerapress blade"},
                    },
                    fh,
                )
            with open(os.path.join(dest, "stock-history.json"), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "byCode": {
                            "BX44": [
                                {
                                    "shop": "ShopA",
                                    "at": "2026-06-01T10:00:00Z",
                                    "title": "三角龍壓到貨",
                                    "price": "188",
                                    "url": "https://shop.example/bx44",
                                }
                            ]
                        }
                    },
                    fh,
                )
            with open(os.path.join(parts, "products.json"), "w", encoding="utf-8") as fh:
                json.dump({}, fh)
            site_pages._CATALOG_PRODUCT_CACHE["stamp"] = None
            site_pages._BROWSER_DETAIL_CACHE["records"] = None
            site_pages._STOCK_HISTORY_CACHE["by_code"] = None
            with mock.patch.object(parts_catalog, "PARTS_DIR", parts), mock.patch.object(
                site_pages, "browser_catalog_dir", return_value=dest
            ):
                page = render_model_detail_html(
                    "BX-44",
                    [
                        {
                            "sku": "939528",
                            "shop_id": "h1",
                            "shop_label": "ShopA",
                            "title": "BX-44 三角龍壓",
                            "model": "BX-44",
                            "price": "188",
                            "url": "https://shop.example/bx44",
                            "image": "https://shop.example/bx44.jpg",
                            "status": "in_stock",
                        }
                    ],
                )
        self.assertIn("<h1>BX-44 三角龍壓M-85BS</h1>", page)
        self.assertEqual(page.count("<h1>"), 1)
        self.assertIn(
            "<title>BX-44 三角龍壓M-85BS 香港現貨 · HK BeybladeX Watch</title>",
            page,
        )
        self.assertIn('content="index, follow"', page)
        self.assertIn('href="https://hkbeybladex.com/product/BX-44"', page)
        self.assertIn("高穩定性的刃擊環", page)
        self.assertIn("套組", page)
        self.assertIn("亞版", page)
        self.assertIn("香港現價", page)
        self.assertIn("1 間有貨", page)
        self.assertIn("src='/browser/assets/pack-0.jpg'", page)
        self.assertIn("src='/browser/assets/pack-1.png'", page)
        self.assertIn("href='/browser/item/BL-1'", page)
        self.assertIn("三角龍壓刃", page)
        self.assertIn("Takara Tomy", page)
        self.assertIn(explore_href("https://beyblade.takaratomy.co.jp/beyblade-x/lineup/bx44.html"), page)
        self.assertIn(explore_href("https://shop.example/bx44"), page)
        self.assertIn("香港店舖庫存", page)
        self.assertIn("model-stock--photo", page)
        self.assertIn("src='https://shop.example/bx44.jpg'", page)
        self.assertIn("入貨紀錄", page)
        self.assertIn("三角龍壓到貨", page)
        self.assertIn("HK$188", page)
        self.assertIn("2026-06-01T10:00", page)
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page)
        product = next(
            node
            for node in json.loads(match.group(1))["@graph"]
            if node.get("@type") == "Product"
        )
        self.assertIsInstance(product["image"], list)
        self.assertGreaterEqual(len(product["image"]), 2)
        self.assertTrue(any(url.endswith("pack-0.jpg") for url in product["image"]))
        self.assertTrue(any(url.endswith("pack-1.png") for url in product["image"]))
        self.assertIn("AggregateOffer", page)
        self.assertIn("BreadcrumbList", page)

    def test_umbrella_variant_detail_accepts_colon_code(self):
        from site_pages import public_model_code, render_model_detail_html

        page = render_model_detail_html(
            "CX-00%3AS4-70V",
            [
                {
                    "sku": "4904810954316",
                    "shop_id": "takaratomymall",
                    "shop_label": "Takara Tomy Mall",
                    "title": "BEYBLADE X CX-00 S4-70V",
                    "model": "CX-00:S4-70V",
                    "price": "1800",
                    "url": "https://takaratomymall.jp/shop/g/g4904810954316/",
                    "status": "in_stock",
                }
            ],
        )
        self.assertIsNotNone(page)
        self.assertIn("/product/CX-00%3AS4-70V", page)
        self.assertIn("Takara Tomy Mall", page)
        self.assertIn("4904810954316", page)
        self.assertEqual(public_model_code("CX-00:限定S6-60V"), "CX-00:限定S6-60V")
        self.assertEqual(public_model_code("CX-00/S4-70V"), "")
        self.assertEqual(public_model_code("CX-00:../S4"), "")

    def test_models_grid_links_detail_and_keeps_mobile_modal(self):
        page = render_models_html(
            [
                {
                    "sku": "1",
                    "shop_id": "h1",
                    "title": "BX-01 Dran Sword",
                    "model": "BX-01",
                    "price": "100",
                    "status": "in_stock",
                }
            ]
        )
        self.assertIn("href='/product/BX-01'", page)
        self.assertIn("(min-width:960px)", page)
        self.assertIn('id="model-modal-page"', page)
        self.assertIn("查看詳情", page)
        self.assertIn("preventDefault", page)
        self.assertIn("ItemList", page)


class ExploreRedirectTests(unittest.TestCase):
    def test_explore_href_wraps_external_and_keeps_our_pages(self):
        shop = "https://shop.example/bx44"
        wrapped = explore_href(shop)
        self.assertTrue(wrapped.startswith("/explore/?url="))
        self.assertIn("shop.example", wrapped)
        self.assertEqual(explore_href("/product/BX-01"), "/product/BX-01")
        self.assertEqual(
            explore_href("https://hkbeybladex.com/go/uat/test"),
            "https://hkbeybladex.com/go/uat/test",
        )
        self.assertEqual(explore_href("https://cdn.hkbeybladex.com/images/a.jpg"), "https://cdn.hkbeybladex.com/images/a.jpg")
        self.assertEqual(explore_href("javascript:alert(1)"), "javascript:alert(1)")

    def test_explore_rejects_bad_targets(self):
        self.assertEqual(explore_http_result("")["status"], 404)
        self.assertEqual(explore_http_result("url=javascript:alert(1)")["status"], 404)
        self.assertEqual(
            explore_http_result("url=https://user:pass@shop.example/x")["status"],
            404,
        )
        self.assertEqual(
            explore_http_result("url=https://hkbeybladex.com/product/BX-01")["status"],
            404,
        )
        self.assertEqual(
            explore_http_result("url=https://www.hkbeybladex.com/explore/?url=1")["status"],
            404,
        )

    def test_visitor_redirects_after_half_second_and_bot_keeps_product_data(self):
        import urllib.parse

        dest = "https://www.buymarkettoy.com/products/x"
        query = "url=" + urllib.parse.quote(dest, safe="")
        items = [
            {
                "title": "BX-34",
                "sku": "BY914563",
                "shop_id": "buymarkettoy",
                "url": dest,
                "image": "https://cdn.example/x.jpg",
                "price": "159.00",
                "status_label": "有貨",
            }
        ]
        human = explore_http_result(query, user_agent="Mozilla/5.0", items=items)
        self.assertEqual(human["status"], 200)
        self.assertEqual(human["cache"], "private, no-store")
        self.assertEqual(human["location"], dest)
        self.assertIn("setTimeout(go, 500)", human["html"])
        self.assertIn("location.replace(dest)", human["html"])
        self.assertIn(dest, human["html"])
        self.assertIn("go-loading", human["html"])
        self.assertNotIn("go-card", human["html"])
        self.assertNotIn("class='thumb'", human["html"])

        bot = explore_http_result(query, user_agent="TelegramBot (like TwitterBot)", items=items)
        self.assertEqual(bot["status"], 200)
        self.assertIn("BX-34", bot["html"])
        self.assertIn("HK$159.00", bot["html"])
        self.assertIn("有貨", bot["html"])
        self.assertIn("https://cdn.example/x.jpg", bot["html"])
        self.assertIn("class='thumb'", bot["html"])
        cached = explore_http_result(
            query,
            user_agent="TelegramBot (like TwitterBot)",
            items=[
                dict(
                    items[0],
                    image_path="images/buymarkettoy/BY914563.jpg",
                )
            ],
        )
        self.assertIn("class='thumb'", cached["html"])
        self.assertIn("/images/buymarkettoy/BY914563.jpg", cached["html"])
        self.assertNotIn("location.replace(dest)", bot["html"])
        self.assertNotIn("setTimeout(go, 500)", bot["html"])
        self.assertIn(
            'property="og:url" content="https://hkbeybladex.com/explore/?url=',
            bot["html"],
        )
        self.assertIn(urllib.parse.quote(dest, safe=""), bot["html"])

    def test_unknown_destination_still_shows_host_to_bots(self):
        import urllib.parse

        dest = "https://beyblade.takaratomy.co.jp/beyblade-x/lineup/bx44.html"
        result = explore_http_result(
            "url=" + urllib.parse.quote(dest, safe=""),
            user_agent="facebookexternalhit/1.1",
            items=[],
        )
        self.assertEqual(result["status"], 200)
        self.assertIn("beyblade.takaratomy.co.jp", result["html"])
        self.assertNotIn("location.replace(dest)", result["html"])


if __name__ == "__main__":
    unittest.main()
