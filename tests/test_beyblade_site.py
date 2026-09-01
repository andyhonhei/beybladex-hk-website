import json
import os
import re
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from site_data import (
    DISCORD_INVITE_URL,
    GO_CACHE_CONTROL,
    HTML_CACHE_CONTROL,
    IMAGE_CACHE_CONTROL,
    TELEGRAM_INVITE_URL,
    THREADS_SUBSCRIBE_ASK,
    admin_credentials_ok,
    admin_host_request,
    admin_session_ok,
    admin_session_token,
    apply_config,
    display_status_shops,
    go_href,
    go_http_result,
    go_page_target,
    go_target_from_item,
    is_admin_host,
    is_preview_crawler,
    load_config,
    load_shop_products_for_shop_id,
    parse_go_path,
    probe_go_url,
    product_image_path,
    run_web_notify_test,
    shop_chip_shops,
    shop_page_meta,
    shop_products_from_state,
    sources_for_shop_page,
    threads_subscribe_footer,
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
    def test_site_pages_has_home_html(self):
        from site_pages import render_status_html

        html = render_status_html({"shops": [], "updated_at": ""})

        self.assertIn("<", html)

    def test_site_data_mysql_settings_keys(self):
        import site_data

        original_config = dict(site_data.CONFIG or {})
        self.addCleanup(site_data.apply_config, original_config)
        site_data.apply_config(
            {"storage": {"mysql": {"enabled": True, "database": "beyblade_watch"}}}
        )
        s = site_data.mysql_settings()

        self.assertEqual(s["database"], "beyblade_watch")
        self.assertTrue(s["enabled"])

    def test_module_imports_serve_forever(self):
        import beyblade_site

        self.assertTrue(callable(beyblade_site.serve_forever))

    def test_missing_config_path_uses_empty_config(self):
        import beyblade_site
        import site_data

        original_config = dict(site_data.CONFIG or {})
        self.addCleanup(site_data.apply_config, original_config)
        original_cdn_origin = os.environ.get("BEYBLADE_CDN_ORIGIN")

        def restore_cdn_origin():
            if original_cdn_origin is None:
                os.environ.pop("BEYBLADE_CDN_ORIGIN", None)
            else:
                os.environ["BEYBLADE_CDN_ORIGIN"] = original_cdn_origin

        self.addCleanup(restore_cdn_origin)

        class FakeServer:
            def __init__(self):
                self.shutdown_called = False

            def shutdown(self):
                self.shutdown_called = True

        server = FakeServer()
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "missing.json")
            with mock.patch.object(
                beyblade_site,
                "load_config",
                side_effect=AssertionError("missing config should not be loaded"),
            ) as load:
                with mock.patch.object(
                    beyblade_site, "start_status_server", return_value=server
                ):
                    with mock.patch.object(
                        beyblade_site.time, "sleep", side_effect=KeyboardInterrupt()
                    ):
                        self.assertEqual(beyblade_site.serve_forever(missing), 0)

        load.assert_not_called()
        self.assertTrue(server.shutdown_called)
        self.assertEqual(
            site_data.CONFIG.get("status"),
            {"enabled": True, "host": "127.0.0.1", "port": 8080},
        )


class SiteNotifyHistoryTests(unittest.TestCase):
    def test_notify_rows_html_shows_product_thumb(self):
        html = notify_rows_html(
            [
                {
                    "at": "2026-08-29 04:00:00",
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
        self.addCleanup(lambda: mod.apply_config({}))
        mod.DATA_DIR = tmp.name
        mod.mysql_settings = lambda: {"enabled": False}
        mod.apply_config(
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
            {"checked_at": "2026-08-29 04:00:00", "ok": True, "shops": []},
            notifies=[
                {
                    "at": "2026-08-29 04:00:00",
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

    def test_status_page_hides_latest_notifies_when_empty(self):
        page = render_status_html(
            {"checked_at": "2026-08-29 04:00:00", "ok": True, "shops": []},
            notifies=[],
        )
        self.assertIn('<a class="nav-btn" href="/history">最新通知</a>', page)
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
                    "at": "2026-08-29 04:00:00",
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
                    "at": "2026-08-29 04:00:00",
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
        self.assertIn("/history?shop=hobbyland", page)
        self.assertIn("model=UX-08", page)
        self.assertIn("Hobbyland", page)
        self.assertIn("UX-08", page)
        self.assertIn("noindex, nofollow", page)
        self.assertIn("filter-store-label", page)
        self.assertIn(">Store</p>", page)
        self.assertIn(">Model</p>", page)


class StatusPageTests(unittest.TestCase):
    def test_subscribe_dropdown_lists_telegram_discord_threads(self):
        markup = subscribe_widget_html("訂閱")
        names = re.findall(r'class="subscribe-name">([^<]+)', markup)
        self.assertEqual(names, ["Telegram", "Discord", "Threads"])
        self.assertIn("https://t.me/+mbTPVeGFBalhMjQ9", markup)
        self.assertIn("https://discord.gg/qpnuMgBv8", markup)
        self.assertIn("https://www.threads.com/@beybladex_hk_watch", markup)
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
        self.assertIn('<a class="nav-btn" href="/shops">店舖現況</a>', page)
        self.assertNotIn("<th>網站</th>", page)
        self.assertNotIn("https://eshop.cuapp.com", page)
        self.assertIn("/shop/cuapp", page)
        self.assertIn("index, follow", page)
        self.assertIn("<th>商店</th>", page)
        self.assertIn("<th>狀態</th>", page)
        self.assertIn("<th>SKU</th>", page)
        self.assertIn("<th>有貨</th>", page)
        self.assertIn("<th>缺貨</th>", page)
        self.assertIn("<th>最後更新時間</th>", page)
        self.assertIn("<th>錯誤</th>", page)
        self.assertIn(">10</td>", page)
        self.assertIn("2026-08-30 13:00:00", page)
        self.assertIn("整體", page)
        self.assertIn("2026-08-30 14:00:00", page)
        self.assertNotIn("Website list", page)
        self.assertNotIn("Status live", page)

    def test_nav_includes_history_button(self):
        nav = site_nav_html()
        self.assertIn('<a class="nav-btn" href="/history">最新通知</a>', nav)
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

    def test_coffee_page_explains_free_project_and_costs(self):
        page = render_coffee_html()
        self.assertIn("請我飲杯咖啡", page)
        self.assertIn("完全免費", page)
        self.assertIn("伺服器", page)
        self.assertIn("開發", page)
        self.assertIn("心機", page)
        self.assertIn("<details", page)
        self.assertIn("PayMe", page)
        self.assertIn("https://payme.hsbc/andyhuihh", page)
        self.assertIn("AlipayHK", page)
        self.assertIn("/alipayhk.jpg", page)
        self.assertNotIn("buymeacoffee", page)
        self.assertIn("noindex, nofollow", page)
        self.assertNotIn('href="/coffee"', site_nav_html())

    def test_subscribe_page_lists_channels_and_is_hidden_from_nav(self):
        page = render_subscribe_html()
        self.assertIn("訂閱通知", page)
        self.assertIn("https://t.me/+mbTPVeGFBalhMjQ9", page)
        self.assertIn("https://discord.gg/qpnuMgBv8", page)
        self.assertIn("https://www.threads.com/@beybladex_hk_watch", page)
        self.assertIn("加入群組", page)
        self.assertIn("加入頻道", page)
        self.assertIn("鐘仔", page)
        self.assertNotIn("/subscribe", site_nav_html())
        self.assertNotIn("/subscribe", site_footer_html())
        self.assertEqual(subscribe_page_url(), "https://beybladex-watch.andyhhh.com/subscribe")

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
            "https://beybladex-watch.andyhhh.com/privacy",
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
            "https://beybladex-watch.andyhhh.com/terms",
        )
        self.assertIn('href="/terms"', site_footer_html())
        self.assertNotIn("/terms", site_nav_html())

    def test_threads_subscribe_comment_links_subscribe_page(self):
        footer = threads_subscribe_footer()
        self.assertIn(THREADS_SUBSCRIBE_ASK, footer)
        self.assertIn(subscribe_page_url(), footer)
        self.assertNotIn(TELEGRAM_INVITE_URL, footer)
        self.assertNotIn(DISCORD_INVITE_URL, footer)

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
        self.assertIn("/shop/animepro", page)
        self.assertIn('class="nav-btn"', page)
        self.assertIn('href="/shop/all?stock=in"', page)
        self.assertIn("全部現貨", page)
        self.assertIn('class="site-nav"', page)
        self.assertEqual(page.count(">訂閱通知</button>"), 2)
        self.assertIn('id="subscribe-btn"', page)
        self.assertIn('id="subscribe-hero-btn"', page)
        self.assertNotIn(">/\\\\-_ =+|  beybladex  |+= _-/\\\\</button>", page)
        self.assertIn('class="ascii"', page)
        self.assertIn("https://www.threads.com/@beybladex_hk_watch", page)
        self.assertIn("https://discord.gg/qpnuMgBv8", page)
        self.assertIn("https://t.me/+mbTPVeGFBalhMjQ9", page)
        self.assertIn("subscribe-method", page)
        self.assertIn("Threads", page)
        self.assertIn("Discord", page)
        self.assertIn("Telegram", page)
        self.assertIn("香港爆旋陀螺到貨通知", page)
        self.assertIn("Online舖頭", page)
        self.assertNotIn("本地舖頭", page)
        self.assertIn('<a href="/shops">Online舖頭</a>', page)
        self.assertIn('<a class="nav-btn" href="/shops">店舖現況</a>', page)
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
            'property="og:url" content="https://beybladex-watch.andyhhh.com/share"',
            page,
        )
        self.assertIn(
            'rel="canonical" href="https://beybladex-watch.andyhhh.com/share"',
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
        self.assertIn("最後更新時間", page)
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
            'rel="canonical" href="https://beybladex-watch.andyhhh.com/share"',
            page,
        )
        self.assertIn(
            'property="og:url" content="https://beybladex-watch.andyhhh.com/share"',
            page,
        )
        self.assertIn("/og-card.jpg", page)
        self.assertIn('property="og:image:type" content="image/jpeg"', page)
        self.assertNotIn("/images/", page)
        self.assertNotIn("最新通知", page)

    def test_og_test_page_is_self_canonical_with_unique_title(self):
        page = render_og_test_html()
        self.assertIn(
            'rel="canonical" href="https://beybladex-watch.andyhhh.com/og-test-20260830"',
            page,
        )
        self.assertIn(
            'property="og:url" content="https://beybladex-watch.andyhhh.com/og-test-20260830"',
            page,
        )
        self.assertIn("OG probe 20260830", page)
        self.assertIn("/og-card.jpg?v=og-test-20260830", page)
        self.assertNotIn("最新通知", page)
        goal = render_og_test_html("/goal")
        self.assertIn(
            'property="og:url" content="https://beybladex-watch.andyhhh.com/goal"',
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
        self.assertIn("href='/shop/all'", page)
        self.assertIn("href='/shop/all?stock=in'", page)
        self.assertIn("href='/shop/all?stock=out'", page)
        self.assertIn("href='/shop/lastchance'", page)
        self.assertIn("href='/shop/lastchance?stock=in'", page)
        self.assertIn("href='/shop/lastchance?stock=out'", page)
        self.assertIn("href='/shop/animepro'", page)
        self.assertIn("href='/shop/animepro?stock=out'", page)
        self.assertNotIn("href='/shop/animepro?stock=in'", page)

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
        import site_data

        site_data.apply_config(cfg)
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
            site_data.apply_config(load_config(os.path.join(ROOT, "config/site_config.example.json")))
        self.assertIn("Hobbyland", page)
        self.assertNotIn(">HobbylandBeyblade<", page)
        self.assertIn("/shop/all", page)
        self.assertIn("/shop/hobbyland", page)
        self.assertNotIn("/shop/hobbyland-beyblade", page)

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
        apply_config({"admin": {"username": "admin-user", "password": "config-password"}})
        self.addCleanup(apply_config, {})
        self.assertTrue(admin_credentials_ok("admin-user", "config-password"))
        self.assertFalse(admin_credentials_ok("admin-user", "wrong"))
        self.assertFalse(admin_credentials_ok("other", "config-password"))
        self.assertFalse(admin_credentials_ok("", "config-password"))
        self.assertFalse(admin_credentials_ok("admin-user", ""))

    def test_admin_credentials_default_empty_rejects_login(self):
        apply_config({})
        self.assertFalse(admin_credentials_ok("admin-user", "config-password"))
        self.assertEqual(admin_session_token(), "")

    def test_admin_session_token_is_not_the_password(self):
        apply_config({"admin": {"username": "admin-user", "password": "config-password"}})
        self.addCleanup(apply_config, {})
        token = admin_session_token()
        self.assertTrue(admin_session_ok(token))
        self.assertFalse(admin_session_ok("config-password"))
        self.assertFalse(admin_session_ok(""))
        self.assertNotIn("config-password", token)

    def test_admin_host_only_serves_admin_paths(self):
        apply_config({"admin": {"username": "admin-user", "password": "config-password"}})
        self.addCleanup(apply_config, {})
        self.assertTrue(is_admin_host("beybladex-admin.andyhhh.com"))
        self.assertTrue(is_admin_host("beybladex-admin.andyhhh.com:8080"))
        self.assertFalse(is_admin_host("beybladex-watch.andyhhh.com"))
        self.assertEqual(
            admin_host_request("beybladex-watch.andyhhh.com", "/notify-test"),
            "not_found",
        )
        self.assertEqual(
            admin_host_request("beybladex-watch.andyhhh.com", "/login"),
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
        self.assertNotIn("noindex, nofollow", notify)
        for page in (login, notify):
            self.assertNotIn("config-password", page)
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
            apply_config(load_config(os.path.join(ROOT, "config/site_config.example.json")))
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
        self.assertIn("https://fooklemodel.com/product/bxg-47/", page)
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
        self.assertIn('class="nav-btn"', page)
        self.assertIn('href="/shop/all?stock=in"', page)
        self.assertIn("全部現貨", page)
        self.assertIn('id="subscribe-btn"', page)
        self.assertIn("subscribe-method", page)
        self.assertNotIn("key=abc", page)
        self.assertIn("FookLeModel 爆旋陀螺", page)
        self.assertIn("index, follow", page)
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
        self.assertIn('href="/shop/fooklemodel"', page)
        self.assertIn('href="/shop/fooklemodel?stock=in"', page)
        self.assertIn('href="/shop/fooklemodel?stock=out"', page)
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
        self.assertIn('href="/shop/all">All</a>', page)
        self.assertIn('href="/shop/hobbyland"', page)
        self.assertIn('href="/shop/animepro"', page)
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
        self.assertIn('href="/shop/all">All</a>', chips)
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
        self.assertIn('href="/shop/fooklemodel?tag=CX"', page)
        self.assertIn('href="/shop/fooklemodel?tag=BX"', page)
        self.assertIn('href="/shop/fooklemodel?tag=UX"', page)
        self.assertIn('href="/shop/fooklemodel?tag=other"', page)
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
        self.assertIn('href="/shop/fooklemodel?stock=in&amp;tag=CX"', cx_page)

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
        self.assertIn("class='bad'", page)
        self.assertIn("timeout", page)
        self.assertIn("#e10600", page)
        self.assertNotIn("#128a3e", page)


class GoTrackTests(unittest.TestCase):
    def test_parse_and_build_go_path(self):
        self.assertEqual(parse_go_path("/go/uat/test"), ("uat", "test"))
        self.assertEqual(
            parse_go_path("/go/hobbyland-beyblade/UX-08"),
            ("hobbyland-beyblade", "UX-08"),
        )
        self.assertEqual(
            go_href("uat", "test"),
            "https://beybladex-watch.andyhhh.com/go/uat/test",
        )
        self.assertEqual(
            go_href("uat", "test", source="discord"),
            "https://beybladex-watch.andyhhh.com/go/uat/test?from=discord&utm_source=discord&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test",
        )
        self.assertEqual(
            go_href("uat", "test", source="threads"),
            "https://beybladex-watch.andyhhh.com/go/uat/test?from=threads&utm_source=threads&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test",
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
            'property="og:description" content="香港爆旋陀螺到貨通知。Online舖頭 有新品、補貨、缺貨就出帖。非官方。 可經 Threads、Discord、Telegram 收通知。"',
            page,
        )
        self.assertIn("/og-card.jpg", page)
        self.assertIn(
            'property="og:url" content="https://beybladex-watch.andyhhh.com/go/buymarkettoy/"',
            page,
        )
        self.assertIn(
            'rel="canonical" href="https://beybladex-watch.andyhhh.com/go/buymarkettoy/"',
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
            "https://beybladex-watch.andyhhh.com/go/uat/test?from=telegram&utm_source=telegram&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test",
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
            "https://beybladex-watch.andyhhh.com/go/uat/test?from=discord&utm_source=discord&utm_medium=notify&utm_campaign=stock_alert&utm_content=uat-test",
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
            self.assertTrue(probe_go_url("https://beybladex-watch.andyhhh.com/go/uat/test"))

    def test_probe_go_url_rejects_404_and_errors(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://example/go", 404, "Not Found", {}, None
        )
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            with mock.patch(
                "site_data.subprocess.run",
                return_value=mock.Mock(returncode=0, stdout="404"),
            ):
                self.assertFalse(
                    probe_go_url("https://beybladex-watch.andyhhh.com/go/uat/test")
                )
        opener.open.side_effect = TimeoutError()
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            with mock.patch(
                "site_data.subprocess.run", side_effect=TimeoutError()
            ):
                self.assertFalse(
                    probe_go_url("https://beybladex-watch.andyhhh.com/go/uat/test")
                )

    def test_probe_go_url_uses_curl_without_following_redirects(self):
        opener = mock.Mock()
        opener.open.side_effect = OSError("ssl")
        proc = mock.Mock(returncode=0, stdout="302")
        with mock.patch("site_data.urllib.request.build_opener", return_value=opener):
            with mock.patch("site_data.subprocess.run", return_value=proc) as run:
                self.assertTrue(
                    probe_go_url("https://beybladex-watch.andyhhh.com/go/uat/test")
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
        self.assertIn("gtag('config', 'G-19VVZP9R25')", result["html"])
        self.assertIn("前往商店", result["html"])
        self.assertNotIn("以後唔好再顯示", result["html"])
        self.assertEqual(result.get("cache"), GO_CACHE_CONTROL)

    def test_go_http_threads_shows_interstitial(self):
        result = go_http_result("/go/uat/test", query="from=threads")
        self.assertEqual(result["status"], 200)
        self.assertEqual(result.get("cache"), GO_CACHE_CONTROL)
        self.assertIn(
            "Follow 我哋 Threads 之後記得撳右上角訂閱／鐘仔掣，訂閱帖文通知",
            result["html"],
        )

    def test_go_http_preview_crawler_keeps_go_og_tags(self):
        result = go_http_result(
            "/go/uat/test",
            query="from=threads",
            user_agent="facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        )
        self.assertEqual(result["status"], 200)
        self.assertEqual(result.get("cache"), GO_CACHE_CONTROL)
        self.assertIn('property="og:title"', result["html"])
        self.assertIn(
            'property="og:url" content="https://beybladex-watch.andyhhh.com/go/uat/test?from=threads"',
            result["html"],
        )
        self.assertIn("og-card.jpg", result["html"])
        self.assertNotIn(
            'property="og:url" content="https://www.hobbylandeshop.com/',
            result["html"],
        )
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
        self.assertNotIn("location.replace(dest)", invite["html"])
        with_cookie = go_http_result(
            "/go/uat/test",
            query="from=threads",
            cookie="bxw_go_skip=1",
        )
        self.assertNotIn("以後唔好再顯示", with_cookie["html"])
        self.assertNotIn("location.replace(dest)", with_cookie["html"])
        leftover = go_http_result("/go/uat/test", query="from=threads&skip=1")
        self.assertEqual(leftover["status"], 200)
        self.assertEqual(leftover.get("cache"), GO_CACHE_CONTROL)
        self.assertNotIn("location.replace(dest)", leftover["html"])
        self.assertIn(
            "Follow 我哋 Threads 之後記得撳右上角訂閱／鐘仔掣，訂閱帖文通知",
            leftover["html"],
        )

    def test_go_page_invites_and_keeps_store_seo(self):
        page = render_go_html(go_page_target("uat", "test"), "uat", "test")
        self.assertIn("index, follow", page)
        self.assertNotIn("noindex, nofollow", page)
        self.assertIn(
            'property="og:url" content="https://beybladex-watch.andyhhh.com/go/uat/test"',
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
        self.assertIn(
            'property="og:description" content="Hobbyland 爆旋陀螺新品預訂分類，官方授權香港代理商品。"',
            bounce,
        )
        self.assertIn("discord.gg/qpnuMgBv8", page)
        self.assertIn("t.me/+mbTPVeGFBalhMjQ9", page)
        self.assertIn("threads.com/@beybladex_hk_watch", page)
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
            self.assertNotIn("shoplineimg.com/5f8928fdb9748d005312ca75", page.split('property="og:image"')[1][:300])
            self.assertIn("375x.webp", page)
        finally:
            mod.DATA_DIR = old


class SiteStatusPageCacheTests(unittest.TestCase):
    def test_html_and_images_use_public_cache_headers(self):
        self.assertIn("public", HTML_CACHE_CONTROL)
        self.assertIn("max-age=30", HTML_CACHE_CONTROL)
        self.assertIn("s-maxage=30", HTML_CACHE_CONTROL)
        self.assertIn("s-maxage=86400", GO_CACHE_CONTROL)
        self.assertIn("max-age=300", GO_CACHE_CONTROL)
        self.assertIn("stale-if-error=604800", GO_CACHE_CONTROL)
        self.assertEqual(
            IMAGE_CACHE_CONTROL,
            "public, max-age=31536000, s-maxage=31536000, immutable",
        )



class SiteProductLineTests(unittest.TestCase):
    def test_product_card_keeps_model_and_tag_data_attributes(self):
        card = product_card_html(
            {
                "sku": "1",
                "title": "CX-19",
                "price": "99.00",
                "link": "/zh-hk/cx-19.html",
                "origin": "https://www.toysrus.com.hk",
                "status": "in_stock",
                "status_label": "有貨",
                "in_stock": True,
                "model": "CX-19",
                "tag": "CX",
            },
            "toysrus",
        )
        self.assertIn("data-tag='CX'", card)
        self.assertIn("data-model='CX-19'", card)
        self.assertIn("class='stock-in'", card)
        self.assertIn("有貨", card)

    def test_out_of_stock_label_is_not_blue(self):
        card = product_card_html(
            {"sku": "2", "title": "CX-19", "status": "out_of_stock", "status_label": "缺貨"},
            "toysrus",
        )
        self.assertIn("缺貨", card)
        self.assertNotIn("class='stock-in'", card)


class SiteStatusAuthTests(unittest.TestCase):
    def test_robots_txt_allows_catalog_and_blocks_home(self):
        apply_config({})
        body = robots_txt()
        self.assertIn("User-agent: *", body)
        self.assertIn("Allow: /", body)
        self.assertNotIn("\nDisallow: /\n", body)
        self.assertNotIn("Allow: /in-stock", body)
        self.assertIn("Sitemap: https://beybladex-watch.andyhhh.com/sitemap.xml", body)
        self.assertNotIn("Disallow:", body)

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
        self.assertIn("https://beybladex-watch.andyhhh.com/", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/watch", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/share", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/shop/all", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/shops", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/catalog", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/parts", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/collection", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/subscribe", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/privacy", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/terms", xml)
        self.assertNotIn("/coffee", xml)
        self.assertIn("https://beybladex-watch.andyhhh.com/shop/cuapp", xml)
        self.assertNotIn("/in-stock", xml)
        self.assertNotIn("/notify-test", xml)
        self.assertNotIn("/go/", xml)
        import xml.etree.ElementTree as ET

        root = ET.fromstring(xml)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [node.text for node in root.findall("sm:url/sm:loc", ns)]
        self.assertEqual(locs[0], "https://beybladex-watch.andyhhh.com/")
        self.assertEqual(len(locs), len(set(locs)))
        self.assertTrue(all(loc.startswith("https://beybladex-watch.andyhhh.com/") for loc in locs))
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


class SiteProductImageTests(unittest.TestCase):
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

