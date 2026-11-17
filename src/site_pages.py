#!/usr/bin/env python3
"""HTML/CSS/JS page renderers for the Beyblade HK status site."""
from __future__ import print_function

import html
import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

from site_data import (
    ALIPAYHK_PATH,
    CDN_ORIGIN,
    CONFIG,
    DATA_DIR,
    DISCORD_INVITE_URL,
    FILTER_COMBO_THRESHOLD,
    GO_HOME_SEO_SHOP,
    HKT_TZ,
    IMAGE_MIN_CACHE_BYTES,
    INDEX_NOTIFY_LIMIT,
    INDEX_NOTIFY_SCAN,
    NOTIFY_SRC_AMAZON,
    NOTIFY_SRC_HK,
    LOGO_PATH,
    OG_GOAL_PATH,
    OG_HOME_PATH,
    OG_IMAGE_HEIGHT,
    OG_IMAGE_PATH,
    OG_IMAGE_WIDTH,
    OG_TEST_PATH,
    PAYME_URL,
    PRIVACY_PATH,
    SEO_IMAGE_PATH,
    SITE_BRAND,
    SITE_BRAND_SHORT,
    SITE_META_KEYWORDS,
    SITE_ORIGIN,
    image_data_dir,
    SUBSCRIBE_BUTTON_LABEL,
    SUBSCRIBE_PATH,
    TELEGRAM_INVITE_URL,
    TERMS_PATH,
    THREADS_PROFILE_URL,
    THREADS_SUBSCRIBE_ASK,
    THREADS_SUBSCRIBE_DESC,
    THREADS_SUBSCRIBE_HINT,
    UAT_GO_SHOP,
    build_watcher_status,
    cdn_image_url,
    display_status_shops,
    shop_is_overseas,
    filter_index_notifies,
    filter_notifies_by_src,
    filter_notify_history,
    filter_shops_by_notify_src,
    filter_shop_products,
    find_source_by_id,
    _canonical_model_code,
    group_listings_by_model,
    group_tag_key,
    format_yen_with_hkd,
    format_jpy_retail_with_hkd,
    format_usd_with_hkd,
    shown_price_text,
    amazon_jp_retail_price,
    usd_to_hkd,
    item_currency_code,
    item_uses_jpy,
    jpy_to_hkd,
    listing_hkd_value,
    listing_model_code,
    listing_price_value,
    explore_href,
    go_canonical_url,
    go_path,
    home_seo_description,
    history_href,
    history_query_dates,
    history_row_for_display,
    item_bundle_lines,
    home_href,
    load_index_notifies,
    load_notify_history,
    load_shop_products_for_shop_id,
    mysql_ok_cached,
    notify_at_date,
    notify_day_label,
    notify_src_shop_id,
    normalize_notify_src,
    NOTIFY_EVENT_LABELS,
    page_canonical,
    product_image_path,
    product_image_url,
    product_line_fields,
    product_seo_description,
    product_stock_key,
    product_tag_key,
    seo_image_url,
    shop_chip_shops,
    shop_page_meta,
    sources_for_shop_page,
    shop_products_href,
    skips_line_model,
    stock_status,
    status_text,
)

def outbound_href(url):
    return html.escape(explore_href(url), quote=True)


def page_theme_css():
    return """
:root{--blue:#1a1aff;--ink:#0a0a2a}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--blue);color:#fff;
font-family:Inter,system-ui,sans-serif;overflow-x:hidden}
body.hint-open{padding-bottom:88px}
.slash{position:fixed;right:0;top:12%;width:120px;height:70%;pointer-events:none;
background:repeating-linear-gradient(-32deg,transparent,transparent 10px,#fff 10px,#fff 11px);
opacity:.35}
.wrap{max-width:1080px;margin:0 auto;padding:28px 24px 64px;position:relative;z-index:1}
nav.site-nav{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:nowrap;
font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.16em;text-transform:uppercase}
nav a,nav span{color:#fff;text-decoration:none}
.nav-end{display:flex;align-items:center;gap:8px;margin-left:auto;flex-shrink:0}
.nav-start{display:flex;align-items:center;gap:10px;min-width:0;flex:1 1 auto}
.menu-btn{width:42px;height:42px;padding:0;border:1px solid rgba(255,255,255,.85);background:transparent;color:#fff;
display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;cursor:pointer;
transition:background .18s ease,border-color .18s ease,color .18s ease}
.menu-btn:hover,.menu-btn.is-open{background:#fff;color:var(--blue);border-color:#fff}
.menu-icon{position:relative;width:18px;height:14px;display:block}
.menu-icon span{position:absolute;left:0;right:0;height:2px;background:currentColor;border-radius:999px;
transition:transform .2s ease,opacity .2s ease,top .2s ease}
.menu-icon span:nth-child(1){top:0}
.menu-icon span:nth-child(2){top:6px}
.menu-icon span:nth-child(3){top:12px}
.menu-btn.is-open .menu-icon span:nth-child(1){top:6px;transform:rotate(45deg)}
.menu-btn.is-open .menu-icon span:nth-child(2){opacity:0}
.menu-btn.is-open .menu-icon span:nth-child(3){top:6px;transform:rotate(-45deg)}
.nav-backdrop{position:fixed;inset:0;z-index:20;border:0;padding:0;background:rgba(10,10,42,.55);cursor:pointer;
opacity:0;pointer-events:none;transition:opacity .2s ease}
.nav-backdrop.is-open{opacity:1;pointer-events:auto}
.nav-drawer{position:fixed;inset:0 auto 0 0;z-index:30;width:min(19rem,86vw);padding:18px 16px;
background:#fff;color:var(--blue);box-shadow:12px 0 32px rgba(10,10,42,.24);
transform:translateX(-104%);transition:transform .24s cubic-bezier(.2,.7,.2,1)}
.nav-drawer.is-open{transform:translateX(0)}
.nav-drawer-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-bottom:14px;
border-bottom:3px solid var(--blue)}
.nav-drawer-brand{display:inline-flex;align-items:center;gap:10px;min-width:0;text-decoration:none!important;
color:var(--blue)!important}
.nav-drawer-brand-mark{width:28px;height:28px;object-fit:cover;border:1px solid var(--blue);flex-shrink:0}
.nav-drawer-brand-name{font-family:"Instrument Serif",Georgia,serif;font-size:18px;letter-spacing:.04em;
text-transform:uppercase;line-height:1.15;font-weight:400}
.nav-drawer-close{width:36px;height:36px;border:0;background:transparent;color:var(--blue);
font-size:28px;line-height:1;cursor:pointer;border-radius:4px}
.nav-drawer-close:hover{background:rgba(26,26,255,.08)}
.nav-drawer-links{display:flex;flex-direction:column;gap:4px;padding:12px 0}
.nav-drawer-links a{display:block;text-decoration:none;color:var(--blue)!important;font-weight:600;
padding:9px 12px;border-left:3px solid transparent;font-family:Inter,system-ui,sans-serif;
font-size:13px;letter-spacing:0;text-transform:none;border-radius:0 6px 6px 0;
transition:background .15s ease,border-color .15s ease,transform .15s ease}
.nav-drawer-links a:hover{background:rgba(26,26,255,.08);border-left-color:var(--blue);transform:translateX(2px)}
.nav-drawer-links a.is-active{background:var(--blue);color:#fff!important;border-left-color:#fff}
.nav-drawer-subscribe{margin-top:8px;padding-top:12px;border-top:1px solid rgba(26,26,255,.18)}
.nav-drawer-subscribe .subscribe>button{width:100%;background:var(--blue);color:#fff;border:1px solid var(--blue);
padding:12px 14px;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
.nav-drawer-subscribe .subscribe-list{position:static;min-width:0;width:100%;border:1px solid rgba(26,26,255,.18);
box-shadow:none;margin-top:8px}
body.nav-open{overflow:hidden}
nav a.nav-btn,nav button,.toolbar button{background:transparent;color:#fff;border:1px solid #fff;padding:8px 14px;
font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;cursor:pointer}
.brand{display:inline-flex;align-items:center;gap:10px;font-family:"Instrument Serif",Georgia,serif;font-size:22px;letter-spacing:.04em;text-transform:uppercase;color:#fff!important}
.brand-mark{width:36px;height:36px;object-fit:cover;border:1px solid #fff}
.subscribe{position:relative}
.subscribe-list{display:none;position:absolute;right:0;top:calc(100% + 8px);min-width:280px;
background:#fff;color:var(--blue);z-index:8;border:1px solid #fff}
.subscribe.open .subscribe-list{display:block}
.subscribe-kicker{margin:0;padding:12px 16px 4px;font-family:"IBM Plex Mono",monospace;font-size:10px;
letter-spacing:.16em;text-transform:uppercase;color:var(--blue);opacity:.7}
.subscribe-kicker a{color:inherit;text-decoration:underline}
.subscribe-method{display:flex;flex-direction:column;gap:4px;padding:14px 16px;text-decoration:none!important;
color:var(--blue)!important;text-transform:none;letter-spacing:0;border-top:1px solid rgba(26,26,255,.18)}
.subscribe-method:hover{background:rgba(26,26,255,.08)}
.subscribe-name{font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.12em;text-transform:uppercase}
.subscribe-hint{font-family:Inter,system-ui,sans-serif;font-size:13px;color:var(--blue);opacity:.75;letter-spacing:0;text-transform:none}
nav .subscribe-list a,nav .subscribe-list span{color:var(--blue)!important}
.subscribe-hero{display:inline-block}
.subscribe-hero .subscribe-list{left:50%;right:auto;transform:translateX(-50%)}
.subscribe > button{background:#fff;color:var(--blue);border:1px solid #fff}
.gate-form{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 20px}
.gate-form input{flex:1;min-width:160px;padding:10px 12px;border:1px solid var(--ink);font-size:16px}
.gate-form button{background:transparent;color:var(--ink);border:1px solid var(--ink);
padding:10px 14px;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;
text-transform:uppercase}
.notify-send{margin:0 0 16px}
.notify-send .subscribe > button{background:transparent;color:var(--ink);border:1px solid var(--ink);
padding:10px 14px;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;
text-transform:uppercase}
.notify-send .subscribe-list{left:0;right:auto}
.notify-send .subscribe-list button{display:block;width:100%;background:transparent;border:0;border-radius:0;
text-align:left;cursor:pointer;font:inherit}
.notify-message{width:100%;min-height:140px;padding:10px 12px;border:1px solid var(--ink);
font:inherit;margin:0 0 16px;resize:vertical}
.gate-error{color:#e10600;margin:0 0 16px}
.hero{text-align:center;padding:72px 0 40px}
.kicker{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.2em;margin:0 0 18px}
h1{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:clamp(42px,8vw,88px);
line-height:.95;margin:0 auto 28px;max-width:16ch;text-transform:uppercase}
.page-title{font-size:clamp(32px,6vw,56px);margin:40px 0 24px;max-width:none}
.ascii{display:inline-block;border:1px solid #fff;padding:10px 22px;letter-spacing:.28em;
font-family:"IBM Plex Mono",monospace;font-size:13px;background:#fff;color:var(--blue);cursor:pointer}
.panel{background:#fff;color:var(--ink);margin-top:28px;padding:28px 28px 8px}
.hero + .panel{margin-top:48px}
.panel a{color:inherit;text-decoration:underline}
.panel a:hover{opacity:.7}
.panel h2{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.18em;
text-transform:uppercase;margin:0 0 16px;font-weight:500}
.stats{display:flex;flex-wrap:wrap;gap:18px 28px;margin-bottom:8px;
font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.04em}
.bad{color:#e10600}
.status-pop{display:inline-block}
.status-pop summary{cursor:pointer;list-style:none}
.status-pop summary::-webkit-details-marker{display:none}
.status-pop summary::marker{content:""}
.status-tip{display:none;margin-top:6px;max-width:280px;color:#e10600;font-size:12px;line-height:1.4}
.status-pop:hover .status-tip,
.status-pop[open] .status-tip{display:block}
table{border-collapse:collapse;width:100%;margin:12px 0 24px}
th,td{border-bottom:1px solid #d8d8f0;padding:12px 10px;text-align:left;font-size:14px;color:inherit}
th{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#555}
.shop-chips,.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.shop-chips a{display:inline-block;border:1px solid #fff;color:#fff;text-decoration:none;
padding:8px 12px;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.shop-chips a.on{background:#fff;color:var(--ink)}
.filters a{display:inline-block;border:1px solid var(--ink);color:var(--ink);text-decoration:none;
padding:8px 12px;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.filters a.on{background:var(--ink);color:#fff}
.wrap > .filters a{border:1px solid #fff;color:#fff}
.wrap > .filters a.on{background:#fff;color:var(--ink)}
.filter-store{background:#fff;color:var(--ink);padding:12px;margin:0;max-width:360px}
.filter-store-label{margin:0 0 8px;font-family:"IBM Plex Mono",monospace;font-size:11px;
letter-spacing:.14em;text-transform:uppercase;color:var(--ink)}
.filter-store .shop-chips a{border:1px solid var(--ink);color:var(--ink)}
.filter-store .shop-chips a.on{background:var(--ink);color:#fff}
.history-filters{display:flex;flex-wrap:wrap;align-items:flex-end;gap:8px 12px;margin:0 0 12px}
.history-filters .filter-store{padding:0;margin:0;max-width:none;background:transparent;flex:0 1 auto}
.history-filters .filter-store-label{margin:0 0 4px}
.history-filters .filters,.history-filters .shop-chips{margin:0;gap:6px}
.history-filters .filters a{padding:6px 10px}
.history-filters .filter-combo{margin:0;max-width:200px;min-width:148px}
.filter-combo{position:relative;max-width:320px;margin:0 0 16px;color:var(--ink)}
.filter-combo.shop-chips,.filter-combo.filters{display:block;flex-wrap:unset;gap:0;margin:0}
.filter-combo-field{position:relative}
.filter-combo-input{width:100%;padding:8px 36px 8px 12px;border:1px solid var(--ink);background:#fff;color:var(--ink);
font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.filter-combo-input::-webkit-search-cancel-button,.filter-combo-input::-webkit-search-decoration{-webkit-appearance:none}
.filter-combo-arrow{color:var(--ink);position:absolute;right:0;top:0;bottom:0;width:36px;border:0;background:transparent;
cursor:pointer;font-size:14px;line-height:1;padding:0}
.filter-combo-list{position:absolute;left:0;right:0;top:calc(100% + 4px);z-index:12;max-height:260px;overflow:auto;
background:#fff;color:var(--ink);border:1px solid var(--ink)}
.filter-combo-list a{display:block;padding:8px 12px;text-decoration:none;color:inherit;
font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.filter-combo-list a:hover,.filter-combo-list a.on{background:var(--ink);color:#fff}
.filter-combo-list a[hidden]{display:none}
.model-filters{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 12px}
.model-filters .filters{margin:0;gap:6px}
.model-filters .filters a{padding:6px 9px}
.model-filters #all-stock{flex:1 1 200px;max-width:240px;min-width:0}
.model-filters .filter-combo{margin:0;max-width:none;width:100%}
@media(max-width:640px){.model-filters #all-stock{flex-basis:100%;max-width:none}}
.notify-day{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
margin:16px 0 4px;padding:4px 0;border-bottom:1px solid #d8d8f0}
.product-card{display:flex;gap:14px;align-items:center;padding:14px 0;border-bottom:1px solid #d8d8f0}
.product-card:last-child{border-bottom:0}
.thumb,.thumb-empty{width:96px;height:96px;object-fit:cover;flex:0 0 96px;background:#ececf8}
.meta{flex:1;min-width:0}
.name{font-size:15px;line-height:1.35;margin:0 0 6px}
.sub{font-family:"IBM Plex Mono",monospace;font-size:12px;color:#555;word-break:break-all}
.sale-tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 6px}
.sale-tag{display:inline-block;padding:1px 8px;border-radius:999px;border:1px solid currentColor;
font-size:11px;line-height:1.55;letter-spacing:.02em}
.sale-tag--event{color:#6a4b00;background:#fff4cc}
.sale-tag--ticket{color:#1a3f8a;background:#e7efff}
.sale-tag--member{color:#5a2d82;background:#f3e8ff}
.sale-tag--spot{color:#0d6b3a;background:#e5f8ee}
.sale-tag--preorder{color:#0a4a7a;background:#e5f4ff}
.sale-tag--raffle{color:#8a3b12;background:#ffefe4}
.sale-tag--ended{color:#555;background:#f0f0f0}
.stock-in{color:var(--blue)}
.notify-row{display:flex;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid #d8d8f0}
.notify-row:last-child{border-bottom:0}
.bundle-items{margin:0 0 6px;padding:0;list-style:none;font-size:13px;line-height:1.45}
.bundle-items li{margin:0}
.bundle-price{font-family:"IBM Plex Mono",monospace}
.skip-btn{flex:0 0 auto;min-height:44px;min-width:64px;background:transparent;border:1px solid var(--ink);padding:8px 12px;cursor:pointer;font-size:13px}
.toolbar{margin:0 0 16px}
.install-hint{display:none;position:fixed;left:0;right:0;bottom:0;z-index:30;
background:#fff;color:var(--ink);border-top:1px solid #d8d8f0;padding:12px 18px;
align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.install-hint.show{display:flex}
.install-hint p{margin:0;font-size:14px;flex:1;min-width:200px}
.install-hint .kicker{margin:4px 0 0;letter-spacing:.08em;font-size:11px;color:#555}
.install-hint button{background:transparent;color:var(--ink);border:1px solid var(--ink);padding:8px 12px;cursor:pointer;
font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;flex:0 0 auto}
footer{margin-top:36px;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;
text-transform:uppercase;opacity:.85}
footer a{color:#fff}
.coffee-copy{font-size:15px;line-height:1.65;margin:0 0 14px}
.coffee-method{margin:0 0 16px;border:1px solid var(--ink)}
.coffee-method summary{cursor:pointer;list-style:none;padding:12px 14px;
font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase}
.coffee-method summary::-webkit-details-marker{display:none}
.coffee-method summary:after{content:" +";float:right}
.coffee-method[open] summary:after{content:" –"}
.coffee-method .coffee-body{padding:0 14px 16px}
.coffee-qr{display:block;width:min(280px,100%);height:auto;margin:8px 0;background:#fff}
.coffee-cta{display:inline-block;margin:8px 0 8px;background:var(--ink);color:#fff!important;
text-decoration:none!important;padding:12px 18px;font-family:"IBM Plex Mono",monospace;
font-size:12px;letter-spacing:.12em;text-transform:uppercase}
.subscribe-page{max-width:420px}
.subscribe-page .subscribe-method{border:1px solid var(--ink);margin:0 0 12px;color:var(--ink)!important;
background:#fff}
.subscribe-page .subscribe-name{color:var(--ink)}
.subscribe-page .subscribe-hint{color:var(--ink);opacity:.75}
@media(max-width:700px){
.wrap{padding:16px 12px 40px}
nav.site-nav{flex-wrap:nowrap;gap:8px}
.brand{min-width:0;flex:1 1 auto;gap:8px}
.brand-name{display:none}
.brand-mark{flex-shrink:0}
.nav-end{width:auto;flex-shrink:0;gap:6px}
nav a.nav-btn,nav button{padding:8px 8px;letter-spacing:.06em;white-space:nowrap}
.hero{padding:40px 0 24px}
.ascii{font-size:11px;padding:8px 12px;letter-spacing:.12em}
.panel{padding:16px 10px 4px;overflow-x:auto;margin-top:28px}
.stats{gap:10px 16px}
th:nth-child(3),td:nth-child(3),th:nth-child(6),td:nth-child(6){display:none}
.history-filters{gap:8px}
.history-filters .filter-combo{max-width:100%;min-width:0;flex:1 1 140px}
th,td{font-size:12px;padding:10px 6px}
.slash{opacity:.18;width:64px}
h1.page-title{margin:24px 0 16px}
.product-card,.notify-row{align-items:flex-start;gap:10px;padding:12px 0}
.thumb,.thumb-empty{width:72px;height:72px;flex-basis:72px}
.name{font-size:14px}
.skip-btn{min-height:40px;padding:6px 10px}
}
.model-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:4px 0 20px}
.model-section{margin:8px 0 0}
.model-section h2,.list-section{margin:18px 0 8px;font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.08em;color:var(--ink)}
.model-grid .product-card{display:flex;flex-direction:column;align-items:stretch;gap:0;padding:0;border:0;border-bottom:0;background:transparent}
.model-grid .catalog-card{position:relative;background:#fff;color:var(--ink);border:1px solid #e4e4f4;border-radius:8px;overflow:hidden;min-width:0;
transition:transform .15s ease,border-color .15s ease,box-shadow .15s ease}
.model-grid .catalog-card:hover{transform:translateY(-2px);border-color:var(--blue);box-shadow:0 8px 18px rgba(26,26,255,.12)}
.model-grid .catalog-card__hit{display:flex;flex-direction:column;width:100%;margin:0;padding:0;border:0;background:transparent;
color:inherit;font:inherit;text-align:inherit;cursor:pointer}
.model-grid .catalog-card__image{aspect-ratio:1;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;
background:radial-gradient(circle at 50% 40%,#fff 0%,#f4f6fb 58%,#e7edf6 100%)}
.model-grid .catalog-card__image img{width:100%;height:100%;object-fit:contain;display:block}
.model-grid .catalog-card__placeholder{font-family:"IBM Plex Mono",monospace;font-size:13px;color:#8a8aaa}
.model-grid .catalog-card__badge{position:absolute;top:6px;right:6px;z-index:1;background:var(--blue);color:#fff;
font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.04em;padding:2px 6px;border-radius:999px}
.model-grid .catalog-card__badge--out{background:#6a6a88}
.model-grid .catalog-card__badge .stock-in,.model-grid .catalog-card__badge .stock-out{color:#fff}
.model-grid .catalog-card__body{display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 8px 8px;text-align:center}
.model-grid .catalog-card__id{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.06em;line-height:1.35;color:#6a6a88;max-width:100%;overflow-wrap:anywhere}
.model-grid .catalog-card__name{margin:0;font-family:Inter,system-ui,sans-serif;font-size:11px;font-weight:600;line-height:1.3;letter-spacing:0;text-transform:none;color:#0a0a2a;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}
.model-grid .catalog-card__subtitle{margin:0;font-family:"IBM Plex Mono",monospace;font-size:10px;line-height:1.3;color:#555}
.model-grid .sale-tags{justify-content:center;margin:4px 0 0}
.model-grid .sale-tag{font-size:9px;letter-spacing:0;padding:0 5px}
.model-stock .sale-tags{margin-top:4px}
.model-grid .catalog-card__subtitle.price-in{color:var(--blue)}
.model-grid .catalog-card__subtitle.price-out{color:#888}
.model-offer .stock-in,.model-offer .price-in,.model-modal__detail .price-in{color:var(--blue)}
.model-offer .stock-out,.model-offer .price-out,.model-modal__detail .price-out{color:#888}
.model-offer-list[hidden]{display:none}
.model-offer{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #ececf4}
.model-offer:last-child{border-bottom:0}
.model-offer .thumb,.model-offer .thumb-empty{width:72px;height:72px;flex:0 0 72px;object-fit:contain;background:#f4f6fb}
.model-offer .name{font-size:13px;line-height:1.35;margin:0 0 4px}
.model-offer .name a{color:var(--ink);text-decoration:none}
.model-offer .sub{font-size:11px;color:#555}
body.model-open{overflow:hidden}
.model-modal[hidden]{display:none}
.model-modal{position:fixed;inset:0;z-index:40;display:flex;align-items:flex-end;justify-content:center}
.model-modal__backdrop{position:absolute;inset:0;border:0;padding:0;background:rgba(10,10,42,.55);cursor:pointer}
.model-modal__panel{position:relative;z-index:1;display:flex;flex-direction:column;width:100%;max-height:min(82vh,720px);overflow:hidden;background:#fff;color:var(--ink);
border-radius:12px 12px 0 0;padding:0;box-shadow:0 -12px 32px rgba(10,10,42,.2)}
.model-modal__scroll{overflow:auto;min-height:0;padding:4px 16px 20px}
.model-modal__head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex:0 0 auto;margin:0;padding:14px 8px 10px 16px;background:#fff;border-bottom:1px solid #ececf4}
.model-modal__title{margin:0;font-family:Inter,system-ui,sans-serif;font-size:18px;font-weight:700;line-height:1.35;letter-spacing:0}
.model-modal__detail{margin:6px 0 0;font-size:13px;line-height:1.45;color:#333}
.model-modal__close{flex:0 0 auto;width:36px;height:36px;margin:0;border:0;border-radius:8px;background:#fff;color:var(--ink);font-size:24px;line-height:1;cursor:pointer}
.model-modal__page{flex:0 0 auto;display:block;margin:0 16px 16px;padding:12px 14px;background:var(--blue);color:#fff!important;text-align:center;text-decoration:none;font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.14em}
.model-modal__page[hidden]{display:none}
@media(min-width:700px){
.model-modal{align-items:center;padding:24px}
.model-modal__panel{width:min(680px,100%);border-radius:12px}
}
@media(min-width:640px){.model-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
@media(min-width:960px){.model-grid{grid-template-columns:repeat(6,minmax(0,1fr))}}
@media(min-width:1200px){.model-grid{grid-template-columns:repeat(8,minmax(0,1fr))}}
""".strip()


SEO_KEYWORD_EXTRAS = ("beyblade x", "陀螺", "戰鬥陀螺", "hkbeybladex")


def page_keywords(*parts):
    seen = []
    for part in list(parts) + list(SEO_KEYWORD_EXTRAS):
        text = " ".join(str(part or "").split())
        if text and text not in seen:
            seen.append(text)
    return ", ".join(seen)


def page_seo_head(
    title,
    description,
    path,
    indexable=True,
    canonical_url=None,
    og_url=None,
    image_url=None,
    image_width=None,
    image_height=None,
    og_type="website",
    json_ld=None,
    keywords=None,
):
    robots = "index, follow" if indexable else "noindex, nofollow"
    page_url = canonical_url or page_canonical(path)
    share_url = og_url or page_url
    img_src = image_url or seo_image_url()
    if str(img_src).startswith("//"):
        img_src = "https:" + img_src
    elif str(img_src).startswith("/"):
        origin = (os.environ.get("BEYBLADE_CDN_ORIGIN") or CDN_ORIGIN).rstrip("/")
        if origin in ("", "local", "-"):
            origin = SITE_ORIGIN
        img_src = origin.rstrip("/") + img_src
    if not image_width and not image_height and OG_IMAGE_PATH in str(img_src):
        image_width, image_height = OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT
    elif not image_width and not image_height and "/images/" in str(img_src):
        image_width, image_height = 800, 800
    canon = html.escape(page_url, quote=True)
    share = html.escape(share_url, quote=True)
    img = html.escape(img_src, quote=True)
    t = html.escape(str(title or ""), quote=True)
    d = html.escape(str(description or ""), quote=True)
    kw = html.escape(str(keywords or SITE_META_KEYWORDS), quote=True)
    extra_og = [
        '<meta property="og:site_name" content="%s">'
        % html.escape(SITE_BRAND, quote=True),
        '<meta property="og:locale" content="zh_HK">',
        '<meta property="og:image:secure_url" content="%s">' % img,
    ]
    if image_width and image_height:
        extra_og.append(
            '<meta property="og:image:width" content="%s">' % int(image_width)
        )
        extra_og.append(
            '<meta property="og:image:height" content="%s">' % int(image_height)
        )
    src_l = str(img_src).lower()
    if OG_IMAGE_PATH in str(img_src) or "/images/" in str(img_src) or src_l.endswith(
        (".jpg", ".jpeg")
    ):
        extra_og.append('<meta property="og:image:type" content="image/jpeg">')
    elif src_l.endswith(".png"):
        extra_og.append('<meta property="og:image:type" content="image/png">')
    extra_og = "\n".join(extra_og)
    if json_ld is None:
        json_ld = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": str(title or ""),
            "description": str(description or ""),
            "url": page_url,
            "image": img_src,
        }
    ld = json.dumps(json_ld, ensure_ascii=False)
    return """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<meta name="keywords" content="%s">
<meta name="robots" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%s">
%s
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s">
<meta name="theme-color" content="#1a1aff">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="%s">
<link rel="icon" href="/favicon.ico" type="image/png">
<link rel="apple-touch-icon" href="%s">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script type="application/ld+json">%s</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-19VVZP9R25"></script>
<script async src="https://www.googletagmanager.com/gtm.js?id=GTM-MS2TVW42"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-19VVZP9R25');
</script>
""".strip() % (
        t,
        d,
        kw,
        robots,
        canon,
        html.escape(og_type or "website", quote=True),
        t,
        d,
        share,
        img,
        extra_og,
        t,
        d,
        img,
        html.escape(SITE_BRAND_SHORT, quote=True),
        html.escape(cdn_image_url(LOGO_PATH), quote=True),
        ld.replace("<", "\\u003c"),
    )


def install_hint_html():
    return (
        """
<aside class="install-hint" id="install-hint" hidden>
<div>
<p>把 %s 加入主畫面，之後一點就開首頁睇各店狀態。</p>
<p class="kicker">iPhone：分享 → 加入主畫面 · Android：選單 → 加入主畫面 / 安裝應用程式</p>
</div>
<button type="button" id="install-dismiss">關閉</button>
</aside>
""".strip()
        % html.escape(SITE_BRAND)
    )


def install_hint_script():
    return """
<script>
(function(){
  var CLOSED = "bxw-install-closed";
  var VISITS = "bxw-install-visits";
  var SESSION = "bxw-install-session";
  var box = document.getElementById("install-hint");
  var btn = document.getElementById("install-dismiss");
  if (!box) return;
  function hide(){
    box.classList.remove("show");
    box.setAttribute("hidden", "");
    document.body.classList.remove("hint-open");
  }
  function show(){
    box.removeAttribute("hidden");
    box.classList.add("show");
    document.body.classList.add("hint-open");
  }
  try {
    if (localStorage.getItem(CLOSED) === "1") { hide(); return; }
    if (!sessionStorage.getItem(SESSION)) {
      sessionStorage.setItem(SESSION, "1");
      var n = parseInt(localStorage.getItem(VISITS) || "0", 10);
      if (isNaN(n)) n = 0;
      localStorage.setItem(VISITS, String(n + 1));
    }
    var visits = parseInt(localStorage.getItem(VISITS) || "0", 10);
    if (visits >= 1 && visits <= 3) show();
    else hide();
  } catch (e) { show(); }
  if (btn) btn.onclick = function(){
    try { localStorage.setItem(CLOSED, "1"); } catch (e) {}
    hide();
  };
})();
</script>
""".strip()


def ga_events_script():
    return (
        "<script>(function(){"
        "function itemFrom(card){"
        "var item={"
        'item_id:card.getAttribute("data-sku")||"",'
        'item_name:card.getAttribute("data-name")||"",'
        'item_brand:card.getAttribute("data-brand")||card.getAttribute("data-shop")||"",'
        'item_category:card.getAttribute("data-tag")||""'
        "};"
        'var price=parseFloat(card.getAttribute("data-price")||"");'
        "if(!isNaN(price))item.price=price;"
        "return item;"
        "}"
        "function listMeta(){"
        'var panel=document.querySelector("[data-item-list-id]");'
        "return{"
        'item_list_id:panel?(panel.getAttribute("data-item-list-id")||""):"",'
        'item_list_name:panel?(panel.getAttribute("data-item-list-name")||""):""'
        "};"
        "}"
        'document.addEventListener("click",function(e){'
        'var lead=e.target.closest&&e.target.closest(".subscribe-method,.coffee-cta");'
        "if(lead){"
        'if(typeof gtag==="function")gtag("event","generate_lead",{method:lead.getAttribute("data-method")||""});'
        "return;"
        "}"
        'var link=e.target.closest&&e.target.closest(".product-card a[href]");'
        "if(!link)return;"
        'var card=link.closest(".product-card");'
        "if(!card)return;"
        "var meta=listMeta();"
        'if(typeof gtag==="function")gtag("event","select_item",{'
        'item_list_id:meta.item_list_id||card.getAttribute("data-shop")||"",'
        'item_list_name:meta.item_list_name||"",'
        "items:[itemFrom(card)]"
        "});"
        "});"
        'var cards=document.querySelectorAll(".product-card");'
        "if(!cards.length)return;"
        "var meta=listMeta();"
        "var items=[];"
        "for(var i=0;i<cards.length&&i<200;i++)items.push(itemFrom(cards[i]));"
        'if(typeof gtag==="function")gtag("event","view_item_list",{'
        'item_list_id:meta.item_list_id||"",'
        'item_list_name:meta.item_list_name||"",'
        "items:items"
        "});"
        "})();</script>"
    )


def install_hint_block():
    return (
        install_hint_html()
        + "\n"
        + install_hint_script()
        + "\n"
        + subscribe_script()
        + "\n"
        + nav_drawer_script()
        + "\n"
        + filter_combo_script()
        + "\n"
        + ga_events_script()
    )


def brand_link_html():
    return (
        '<a class="brand" href="/">'
        '<img class="brand-mark" src="%s" alt="%s"><span class="brand-name">%s</span></a>'
        % (
            html.escape(cdn_image_url(LOGO_PATH), quote=True),
            html.escape(SITE_BRAND, quote=True),
            html.escape(SITE_BRAND),
        )
    )


def robots_txt(host=""):
    from site_data import is_admin_host

    if is_admin_host(host):
        return "\n".join(
            [
                "User-agent: *",
                "Disallow: /",
                "",
            ]
        )
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /shopslist",
            "Disallow: /login",
            "Disallow: /notify-test",
            "Sitemap: %s/sitemap.xml" % SITE_ORIGIN,
            "",
        ]
    )


def browser_item_sitemap_paths(catalog_dir=None):
    directory = browser_catalog_dir() if catalog_dir is None else catalog_dir
    if not directory:
        return []
    catalog_path = os.path.join(directory, "catalog.json")
    if not os.path.isfile(catalog_path):
        return []
    try:
        with open(catalog_path, encoding="utf-8") as fh:
            catalog = json.load(fh)
    except (OSError, ValueError):
        return []
    paths = ["/browser"]
    seen = set(paths)
    for collection in ("products", "parts"):
        for entry in catalog.get(collection) or []:
            if not isinstance(entry, dict):
                continue
            item_id = str(entry.get("id") or "").strip()
            if not item_id or "/" in item_id or "\\" in item_id or item_id in (".", ".."):
                continue
            path = "/browser/item/" + urllib.parse.quote(item_id, safe="-._~:")
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def sitemap_xml(cfg=None, browser_catalog_dir_override=None):
    try:
        lastmod = datetime.fromtimestamp(
            os.path.getmtime(os.path.join(image_data_dir(), "watch_status.json")), tz=timezone.utc
        ).date().isoformat()
    except OSError:
        lastmod = datetime.now(timezone.utc).date().isoformat()
    paths = [
        "/",
        "/watch",
        OG_HOME_PATH,
        "/shops",
        "/product",
        "/history",
        "/catalog",
        "/parts",
        "/collection",
        SUBSCRIBE_PATH,
        PRIVACY_PATH,
        TERMS_PATH,
    ]
    urls = []
    seen = set()
    for path in paths:
        url = page_canonical(path)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    for path in browser_item_sitemap_paths(browser_catalog_dir_override):
        url = page_canonical(path)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    for code in model_index_codes(cfg=cfg):
        url = page_canonical(model_public_path(code))
        if url not in seen:
            seen.add(url)
            urls.append(url)
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        body.extend(
            [
                "  <url>",
                "    <loc>%s</loc>" % html.escape(url, quote=True),
                "    <lastmod>%s</lastmod>" % lastmod,
                "  </url>",
            ]
        )
    body.append("</urlset>")
    return "\n".join(body)


def web_manifest():
    return json.dumps(
        {
            "name": SITE_BRAND,
            "short_name": SITE_BRAND_SHORT,
            "start_url": "/",
            "display": "standalone",
            "background_color": "#1a1aff",
            "theme_color": "#1a1aff",
            "icons": [
                {
                    "src": cdn_image_url(LOGO_PATH),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def shop_page_seo(shop, items, indexable=True):
    label = str((shop or {}).get("label") or (shop or {}).get("id") or "Shop")
    in_count = sum(1 for item in (items or []) if product_stock_key(item) == "in_stock")
    out_count = sum(1 for item in (items or []) if product_stock_key(item) == "out_of_stock")
    title = "%s 爆旋陀螺 · %s" % (label, SITE_BRAND)
    desc = "%s 爆旋陀螺庫存：有貨 %s、缺貨 %s。香港店鋪即時監察。可經 Threads、Discord、Telegram 收通知。" % (
        label,
        in_count,
        out_count,
    )
    if not indexable:
        desc = desc + "（篩選結果）"
    return title, desc


def shop_stock_count_cell(shop, kind):
    shop = shop or {}
    count = shop.get(kind)
    if count is None:
        return "—"
    text = html.escape(str(count))
    try:
        n = int(count)
    except (TypeError, ValueError):
        return text
    if n <= 0:
        return text
    href = shop_products_href(shop.get("id"), kind)
    return "<a href='%s'>%s</a>" % (html.escape(href, quote=True), text)


def status_shop_row_html(shop, show_updated=False):
    err = shop.get("error")
    if not shop.get("enabled", True):
        label = "停用"
    elif err and show_updated:
        label = "<span class='bad'>錯誤</span>"
    else:
        label = "正常"
    if show_updated and err:
        state = (
            "<details class='status-pop'><summary>%s</summary>"
            "<span class='status-tip'>%s</span></details>"
            % (label, html.escape(str(err)))
        )
    else:
        state = label
    label = html.escape(str(shop.get("label") or ""))
    href = shop_products_href(shop.get("id"))
    name_cell = "<a href='%s'>%s</a>" % (html.escape(href, quote=True), label)
    cells = [
        name_cell,
        state,
        html.escape(str(shop.get("sku_count") if shop.get("sku_count") is not None else "—")),
        shop_stock_count_cell(shop, "in_stock"),
        shop_stock_count_cell(shop, "out_of_stock"),
    ]
    if show_updated:
        cells.append(html.escape(str(shop.get("updated_at") or "—")))
    return "<tr>%s</tr>" % "".join("<td>%s</td>" % cell for cell in cells)


def status_shop_table_body(payload, cfg=None, show_updated=False, shops=None):
    payload = payload or {}
    if shops is None:
        shops = display_status_shops(payload.get("shops") or [], cfg)
    rows = [
        status_shop_row_html(shop, show_updated=show_updated)
        for shop in shops
    ]
    colspan = "6" if show_updated else "5"
    return "\n".join(rows) or ("<tr><td colspan='%s'>沒有商店資料</td></tr>" % colspan)


def status_shops_section_html(payload, cfg=None, title_html=None, show_updated=False, shops=None, show_stats=True):
    payload = payload or {}
    if shops is None:
        shops = display_status_shops(payload.get("shops") or [], cfg)
    ok = bool(payload.get("ok"))
    if show_updated and not ok:
        health = "<span class='bad'>異常</span>"
    else:
        health = "正常"
    if title_html is None:
        title_html = '<h2><a href="/shops">店舖現況</a></h2>'
    heading = ("%s\n" % title_html) if title_html else ""
    stats = ""
    if show_stats:
        updated_stat = ""
        if show_updated:
            updated_stat = "<span>更新 %s HKT</span>" % html.escape(
                str(payload.get("checked_at") or "—")
            )
        stats = """<div class="stats">
<span>整體 <strong>%s</strong></span>
%s
</div>
""" % (
            health,
            updated_stat,
        )
    updated_head = "<th>最後更新時間</th>" if show_updated else ""
    return """<section class="panel">
%s%s<table>
<thead><tr><th>商店</th><th>狀態</th><th>SKU</th><th>有貨</th><th>缺貨</th>%s</tr></thead>
<tbody>
%s
</tbody>
</table>
</section>
""" % (
        heading,
        stats,
        updated_head,
        status_shop_table_body(payload, cfg, show_updated=show_updated, shops=shops),
    )


def shops_page_sections_html(payload, cfg=None, show_updated=False):
    payload = payload or {}
    rows = display_status_shops(
        payload.get("shops") or [], cfg, include_test=show_updated
    )
    hk = [row for row in rows if row.get("id") == "all" or not shop_is_overseas(row, cfg)]
    overseas = [row for row in rows if row.get("id") != "all" and shop_is_overseas(row, cfg)]
    html_out = status_shops_section_html(
        payload,
        cfg,
        title_html="<h2>香港店舖</h2>",
        show_updated=show_updated,
        shops=hk,
    )
    if overseas:
        html_out += status_shops_section_html(
            payload,
            cfg,
            title_html="<h2>海外店舖</h2>",
            show_updated=show_updated,
            shops=overseas,
            show_stats=False,
        )
    return html_out


def render_status_html(payload, key_query="", notifies=None, shops=None, show_updated=False, src=""):
    payload = payload or {}
    src = normalize_notify_src(src)
    if shops is None:
        shops = shop_chip_shops()
    if notifies is None:
        raw = load_notify_history(limit=INDEX_NOTIFY_SCAN, shops=shops)
    else:
        raw = list(notifies)
    rows = filter_index_notifies(raw, limit=None)
    hk_rows = filter_notifies_by_src(rows, NOTIFY_SRC_HK)[:INDEX_NOTIFY_LIMIT]
    amazon_rows = filter_notifies_by_src(rows, NOTIFY_SRC_AMAZON)[:INDEX_NOTIFY_LIMIT]
    notifies = amazon_rows if src == NOTIFY_SRC_AMAZON else hk_rows
    title = SITE_BRAND
    desc = home_seo_description()
    notify_section = ""
    more_href = history_href(src=src)
    if hk_rows or amazon_rows:
        notify_section = """<section class="panel">
<h2>最新通知</h2>
%s
%s
<p><a href="%s">查看更多</a></p>
</section>
""" % (
            notify_src_chips_html(src=src, home=True),
            notify_rows_html(notifies),
            html.escape(more_href, quote=True),
        )
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<section class="hero">
<p class="kicker">Hong Kong · Threads / Discord / Telegram alerts</p>
<h1>The watch that never sleeps</h1>
%s
</section>
%s
%s
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            OG_HOME_PATH,
            indexable=True,
            keywords=SITE_META_KEYWORDS,
        ),
        page_theme_css(),
        site_nav_html(),
        subscribe_widget_html(
            SUBSCRIBE_BUTTON_LABEL, "ascii", extra_class="subscribe-hero", widget_id="subscribe-hero"
        ),
        notify_section,
        status_shops_section_html(payload, show_updated=show_updated),
        site_footer_html(),
        install_hint_block(),
    )


def render_share_card_html():
    title = SITE_BRAND
    desc = home_seo_description()
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
</head>
<body>
<img src="%s" width="%s" height="%s" alt="%s">
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            OG_HOME_PATH,
            indexable=True,
            keywords=SITE_META_KEYWORDS,
        ),
        html.escape(cdn_image_url(OG_IMAGE_PATH), quote=True),
        OG_IMAGE_WIDTH,
        OG_IMAGE_HEIGHT,
        html.escape(SITE_BRAND, quote=True),
    )


def render_og_test_html(path=None):
    path = path or OG_TEST_PATH
    title = "BeybladeX Watch goal card"
    desc = "Short OG test path for Facebook Sharing Debugger. Not the homepage."
    image = seo_image_url() + "?v=goal"
    if path != OG_GOAL_PATH:
        title = "OG probe 20260830 · HK BeybladeX Watch"
        desc = "Threads preview test page. Not the homepage. Unique title for unfurl."
        image = seo_image_url() + "?v=og-test-20260830"
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
</head>
<body>
<p>%s</p>
<img src="%s" width="%s" height="%s" alt="%s">
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            path,
            indexable=True,
            image_url=image,
            keywords=page_keywords("OG probe", "goal card", "HK BeybladeX Watch"),
        ),
        html.escape(title),
        html.escape(image, quote=True),
        OG_IMAGE_WIDTH,
        OG_IMAGE_HEIGHT,
        html.escape(title, quote=True),
    )


def render_shops_html(cfg=None, payload=None, show_updated=False):
    cfg = cfg if cfg is not None else CONFIG
    payload = payload or {}
    title = "店舖現況 · %s" % SITE_BRAND
    desc = "香港爆旋陀螺店舖現況。一次睇晒 HobbyDigi、BuyMarketToy、MoonroadHK、Takara Tomy Mall 等網店現貨、缺貨同開訂。"
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">店舖現況</h1>
%s
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            "/shopslist" if show_updated else "/shops",
            indexable=not show_updated,
            keywords=page_keywords(
                "店舖現況",
                "HobbyDigi",
                "BuyMarketToy",
                "MoonroadHK",
                "Takara Tomy Mall",
                "爆旋陀螺現貨",
                "爆旋陀螺開訂",
            ),
        ),
        page_theme_css(),
        site_nav_html(),
        shops_page_sections_html(payload, cfg, show_updated=show_updated),
        site_footer_html(),
        install_hint_block(),
    )


def site_footer_html():
    return (
        "<footer>hkbeybladex.com · not affiliated with Takara Tomy"
        ' · <a href="%s">Privacy</a>'
        ' · <a href="%s">Terms</a></footer>'
        % (
            html.escape(PRIVACY_PATH, quote=True),
            html.escape(TERMS_PATH, quote=True),
        )
    )


def render_not_found_html():
    title = "找不到頁面 · HK BEYBLADEX.COM"
    desc = "呢個網址冇對應頁面。"
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
.not-found-kicker{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.2em;
text-transform:uppercase;margin:28px 0 0}
.not-found-en{opacity:.8}
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<p class="not-found-kicker">404</p>
<h1 class="page-title">找不到頁面</h1>
<section class="panel">
<p class="coffee-copy">呢個網址冇對應頁面。</p>
<p class="coffee-copy not-found-en">This address does not match a page.</p>
<a class="coffee-cta" href="/">返回首頁</a>
</section>
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            "/404",
            indexable=False,
            keywords=page_keywords("找不到頁面", "404"),
        ),
        page_theme_css(),
        site_nav_html(),
        site_footer_html(),
        install_hint_block(),
    )


def render_coffee_html():
    title = "請我飲杯咖啡 · %s" % SITE_BRAND
    desc = "呢個係完全免費嘅香港爆旋陀螺到貨通知專案。伺服器同開發都有成本，請我飲杯咖啡可以幫我繼續做落去。"
    payme = outbound_href(PAYME_URL)
    alipay = html.escape(ALIPAYHK_PATH, quote=True)
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">請我飲杯咖啡</h1>
<section class="panel">
<h2>支持呢個免費專案</h2>
<p class="coffee-copy">呢個係一個<strong>完全免費</strong>嘅專案。睇各店貨況、訂閱到貨通知，全部都唔使俾錢。</p>
<p class="coffee-copy">不過網站要行伺服器，有月費；寫碼、對舖、修 bug 同持續開發都要時間同成本。呢啲都係我自己出心機、花時間去捱。</p>
<p class="coffee-copy">如果你覺得有用，請我飲杯咖啡，幫我繼續維持呢個免費服務。</p>
<details class="coffee-method">
<summary>PayMe</summary>
<div class="coffee-body">
<p class="coffee-copy">撳下面開 PayMe 付款。</p>
<a class="coffee-cta" data-method="payme" href="%s" target="_blank" rel="noopener">開啟 PayMe</a>
</div>
</details>
<details class="coffee-method">
<summary>AlipayHK</summary>
<div class="coffee-body">
<p class="coffee-copy">用 AlipayHK 掃下面二維碼。</p>
<img class="coffee-qr" src="%s" alt="AlipayHK 收款二維碼" width="614" height="583">
</div>
</details>
</section>
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            "/coffee",
            indexable=False,
            keywords=page_keywords("請我飲杯咖啡", "PayMe", "AlipayHK", "香港爆旋陀螺"),
        ),
        page_theme_css(),
        site_nav_html(),
        payme,
        alipay,
        site_footer_html(),
        install_hint_block(),
    )


def subscribe_page_url():
    return SITE_ORIGIN.rstrip("/") + SUBSCRIBE_PATH


def privacy_page_url():
    return SITE_ORIGIN.rstrip("/") + PRIVACY_PATH


def terms_page_url():
    return SITE_ORIGIN.rstrip("/") + TERMS_PATH


def render_privacy_html():
    title = "Privacy Policy · %s" % SITE_BRAND
    desc = (
        "Privacy policy for HK BeybladeX Watch: stock alerts, website analytics, "
        "and Threads / Telegram / Discord notifications."
    )
    site = html.escape(SITE_ORIGIN, quote=True)
    return """<!DOCTYPE html>
<html lang="en">
<head>
%s
<style>
%s
.privacy h2{font-size:16px;margin:22px 0 8px}
.privacy ul{margin:0 0 14px;padding-left:1.2em;line-height:1.65;font-size:15px}
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">Privacy Policy</h1>
<section class="panel privacy">
<p class="coffee-copy">Last updated: 1 September 2026</p>
<p class="coffee-copy">This policy applies to <a href="%s">%s</a> and the related Threads, Telegram, and Discord stock-alert channels operated as HK BeybladeX Watch. The project is unofficial and not affiliated with Takara Tomy.</p>
<h2>What this service is</h2>
<p class="coffee-copy">We watch public Hong Kong hobby-shop websites for Beyblade X stock changes and show that information on this site. Optional alerts go to Discord, Telegram, and Threads.</p>
<h2>Information we collect</h2>
<ul>
<li><strong>Website analytics.</strong> Pages load Google Analytics (gtag). Google may receive your IP address, browser type, pages viewed, and similar usage data under Google’s own policy.</li>
<li><strong>Admin login.</strong> The separate admin host uses an HttpOnly session cookie so the operator can send a test notification. Visitors of the public site do not get this cookie.</li>
<li><strong>Shop data.</strong> Product names, prices, stock status, and shop URLs are copied from public shop pages so we can display and alert on them. That is shop catalogue data, not your personal account data.</li>
<li><strong>Messaging platforms.</strong> If you follow or join our Threads, Telegram, or Discord, those platforms process your account under their policies. We do not get your password. We only use our own bot/app tokens to post public stock messages.</li>
</ul>
<h2>How we use it</h2>
<p class="coffee-copy">We use the data above to run the stock dashboard, measure whether the site is useful, and publish stock alerts. We do not sell personal data. We do not use the Threads API to build advertising profiles of followers.</p>
<h2>Sharing</h2>
<p class="coffee-copy">Hosting and CDN providers (including Cloudflare) may process request logs. Google processes Analytics. Meta processes Threads API calls when we post. Telegram and Discord process messages in those channels. We do not sell lists of users.</p>
<h2>Retention</h2>
<p class="coffee-copy">Stock history is kept so the website can show recent in-stock changes. Analytics retention follows Google Analytics settings.</p>
<h2>Your choices</h2>
<p class="coffee-copy">You can block cookies or Analytics in your browser, unfollow or leave the alert channels, or stop using the site. To ask a question about this policy, open <a href="%s">%s</a> or message the HK BeybladeX Watch Threads profile linked from the subscribe page.</p>
<h2>私隱政策（中文摘要）</h2>
<p class="coffee-copy">本網站提供香港爆旋陀螺舖頭貨況同到貨通知。我們會用 Google Analytics 了解瀏覽情況。我們唔會出售你嘅個人資料。Discord、Telegram、Threads 帳戶由該平台處理。查詢請到本網站或 Threads 專頁。</p>
</section>
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            PRIVACY_PATH,
            indexable=True,
            keywords=page_keywords("privacy policy", "私隱政策", "Google Analytics", "HK BeybladeX Watch"),
        ),
        page_theme_css(),
        site_nav_html(),
        site,
        html.escape(SITE_ORIGIN),
        site,
        html.escape(SITE_ORIGIN),
        site_footer_html(),
        install_hint_block(),
    )


def render_terms_html():
    title = "Terms of Service · %s" % SITE_BRAND
    desc = (
        "Terms of service for HK BeybladeX Watch: unofficial Hong Kong Beyblade X "
        "stock dashboard and optional Threads / Telegram / Discord alerts."
    )
    site = html.escape(SITE_ORIGIN, quote=True)
    privacy = html.escape(PRIVACY_PATH, quote=True)
    return """<!DOCTYPE html>
<html lang="en">
<head>
%s
<style>
%s
.privacy h2{font-size:16px;margin:22px 0 8px}
.privacy ul{margin:0 0 14px;padding-left:1.2em;line-height:1.65;font-size:15px}
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">Terms of Service</h1>
<section class="panel privacy">
<p class="coffee-copy">Last updated: 1 September 2026</p>
<p class="coffee-copy">These terms apply to <a href="%s">%s</a> and the related Threads, Telegram, and Discord stock-alert channels operated as HK BeybladeX Watch. The project is unofficial and not affiliated with Takara Tomy, Hasbro, or the shops we watch.</p>
<h2>The service</h2>
<p class="coffee-copy">We show public Hong Kong hobby-shop Beyblade X stock information and may post optional alerts. Stock, prices, and availability can be wrong, delayed, or incomplete. Listings are not an offer to sell. Buy only from the shop’s own website.</p>
<h2>Acceptable use</h2>
<ul>
<li>Use the site and alert channels for personal, non-commercial stock watching.</li>
<li>Do not abuse, overload, or attempt to disrupt the site, alerts, or shop websites through this service.</li>
<li>Do not use the service to impersonate shops, claim official affiliation, or mislead others about stock.</li>
</ul>
<h2>Alerts and third-party platforms</h2>
<p class="coffee-copy">Threads, Telegram, Discord, Google Analytics, Cloudflare, and shop websites are third-party services. Their own terms apply when you use them. We do not control shop checkout, payment, or fulfilment.</p>
<h2>No warranty</h2>
<p class="coffee-copy">The service is provided free, as is, with no guarantee that it will stay online, stay accurate, or continue posting alerts. We may change or stop any part of it at any time.</p>
<h2>Limitation of liability</h2>
<p class="coffee-copy">To the extent allowed by law, we are not liable for missed restocks, incorrect listings, missed alerts, or any purchase you make (or fail to make) because of this site or its channels.</p>
<h2>Privacy</h2>
<p class="coffee-copy">How we handle analytics, cookies, and platform data is described in the <a href="%s">Privacy Policy</a>.</p>
<h2>Contact</h2>
<p class="coffee-copy">Questions about these terms: open <a href="%s">%s</a> or message the HK BeybladeX Watch Threads profile linked from the subscribe page.</p>
<h2>服務條款（中文摘要）</h2>
<p class="coffee-copy">本網站同相關通知頻道係非官方嘅香港爆旋陀螺貨況工具，與 Takara Tomy、Hasbro 及各舖頭無關。貨況可能有錯或延遲，並非售賣要約。請只喺舖頭官方網站購買。服務免費、無保證，我們可以隨時更改或停止。詳情見英文條款同<a href="%s">私隱政策</a>。</p>
</section>
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            TERMS_PATH,
            indexable=True,
            keywords=page_keywords("terms of service", "使用條款", "HK BeybladeX Watch", "非官方"),
        ),
        page_theme_css(),
        site_nav_html(),
        site,
        html.escape(SITE_ORIGIN),
        privacy,
        site,
        html.escape(SITE_ORIGIN),
        privacy,
        site_footer_html(),
        install_hint_block(),
    )


def render_subscribe_html():
    title = "訂閱通知 · %s" % SITE_BRAND
    desc = "香港爆旋陀螺到貨通知。經 Threads、Telegram、Discord 收新品、補貨、缺貨帖。非官方。"
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">訂閱通知</h1>
<section class="panel subscribe-page">
<p class="coffee-copy">%s</p>
<p class="coffee-copy">%s</p>
<a class="subscribe-method" data-method="Telegram" href="%s" target="_blank" rel="noopener">
<span class="subscribe-name">Telegram</span>
<span class="subscribe-hint">加入群組 · 有貨即時通知</span></a>
<a class="subscribe-method" data-method="Discord" href="%s" target="_blank" rel="noopener">
<span class="subscribe-name">Discord</span>
<span class="subscribe-hint">加入頻道 · 有貨即時通知</span></a>
<a class="subscribe-method" data-method="Threads" href="%s" target="_blank" rel="noopener">
<span class="subscribe-name">Threads</span>
<span class="subscribe-hint">%s</span></a>
</section>
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            SUBSCRIBE_PATH,
            indexable=True,
            keywords=page_keywords("訂閱通知", "Telegram", "Discord", "Threads", "爆旋陀螺補貨", "到貨通知"),
        ),
        page_theme_css(),
        site_nav_html(),
        threads_subscribe_desc_html(),
        html.escape(THREADS_SUBSCRIBE_ASK.replace("\n", " ")),
        outbound_href(TELEGRAM_INVITE_URL),
        outbound_href(DISCORD_INVITE_URL),
        outbound_href(THREADS_PROFILE_URL),
        html.escape(THREADS_SUBSCRIBE_HINT),
        site_footer_html(),
        install_hint_block(),
    )


def notify_src_chips_html(src="", home=False, shop_id="", model="", start="", end=""):
    src = normalize_notify_src(src)
    if home:
        items = [
            (home_href(NOTIFY_SRC_HK), "香港店舖", src == NOTIFY_SRC_HK),
            (home_href(NOTIFY_SRC_AMAZON), "Amazon", src == NOTIFY_SRC_AMAZON),
        ]
    else:
        items = [
            (
                history_href(
                    notify_src_shop_id(shop_id, NOTIFY_SRC_HK),
                    model,
                    start,
                    end,
                    src=NOTIFY_SRC_HK,
                ),
                "香港店舖",
                src == NOTIFY_SRC_HK,
            ),
            (
                history_href(
                    notify_src_shop_id(shop_id, NOTIFY_SRC_AMAZON),
                    model,
                    start,
                    end,
                    src=NOTIFY_SRC_AMAZON,
                ),
                "Amazon",
                src == NOTIFY_SRC_AMAZON,
            ),
        ]
    return filter_options_html(items, combo_label="" if home else "來源")


def history_filter_chips_html(shops, models, shop_id="", model="", start="", end="", src=""):
    src = normalize_notify_src(src)
    shop_id = notify_src_shop_id(shop_id, src)
    model = str(model or "")
    start = str(start or "")[:10]
    end = str(end or "")[:10]
    shops = filter_shops_by_notify_src(shops, src)
    shop_items = [(history_href("", model, start, end, src=src), "All", not shop_id)]
    for shop in shops or []:
        sid = str(shop.get("id") or "")
        shop_items.append(
            (
                history_href(sid, model, start, end, src=src),
                str(shop.get("label") or sid),
                sid == shop_id,
            )
        )
    model_items = [(history_href(shop_id, "", start, end, src=src), "All", not model)]
    for item in models or []:
        model_items.append(
            (
                history_href(shop_id, item, start, end, src=src),
                str(item),
                str(item) == model,
            )
        )
    return '<div class="history-filters">%s%s%s</div>' % (
        notify_src_chips_html(src=src, shop_id=shop_id, model=model, start=start, end=end),
        filter_options_html(shop_items, combo_label="Store"),
        filter_options_html(model_items, combo_label="Model", force_combo=True),
    )


def render_history_html(rows, shops=None, shop_id="", model="", start=None, end=None, now=None, src=""):
    src = normalize_notify_src(src)
    shops = shops if shops is not None else shop_chip_shops()
    if start is None or end is None:
        start, end = history_query_dates("", "", now=now)
    shop_id = notify_src_shop_id(shop_id, src)
    rows = filter_notifies_by_src(rows, src)
    models = []
    seen = set()
    for row in rows or []:
        value = str(row.get("model") or "").strip()
        if value and value not in seen:
            seen.add(value)
            models.append(value)
    if model and model not in seen:
        models.append(model)
    title = "最新通知 · %s" % SITE_BRAND
    desc = "香港爆旋陀螺最新到貨通知。可按商店與型號篩選。"
    if shop_id or model:
        picked = "、".join(part for part in (str(shop_id or ""), str(model or "")) if part)
        desc = "香港爆旋陀螺到貨紀錄，篩選 %s。" % picked
    history_keywords = page_keywords("最新通知", shop_id, model, "到貨紀錄", "爆旋陀螺補貨")
    default_start, default_end = history_query_dates("", "", now=now)
    indexable = (
        src == NOTIFY_SRC_HK
        and not shop_id
        and not model
        and start == default_start
        and end == default_end
    )
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">最新通知</h1>
<section class="panel">
%s
%s
</section>
</div>
%s
</body>
</html>
""" % (
        page_seo_head(title, desc, "/history", indexable=indexable, keywords=history_keywords),
        page_theme_css(),
        site_nav_html(),
        history_filter_chips_html(shops, models, shop_id, model, start, end, src=src),
        notify_rows_html(rows),
        install_hint_block(),
    )


def product_thumb_html(item):
    rel = str((item or {}).get("image_path") or "").replace("\\", "/")
    remote = product_image_url(item)
    cached = ""
    if rel.startswith("images/") and ".." not in rel:
        cached = cdn_image_url("/" + rel)
    src = remote or cached
    if not src:
        return "<div class='thumb thumb-empty' aria-hidden='true'></div>"
    extra = ""
    if remote and cached:
        extra = " onerror=\"this.onerror=null;this.src='%s'\"" % html.escape(cached, quote=True)
    return "<img class='thumb' src='%s' alt='%s' loading='lazy'%s>" % (
        html.escape(src, quote=True),
        html.escape(str((item or {}).get("title") or ""), quote=True),
        extra,
    )


_MALL_SALE_TAGS = (
    ("レアベイ購入チケット対象", "稀有陀螺購買券", "ticket"),
    ("プレミアムX会員新規入会特典", "高級X新會員禮", "member"),
    ("アプリ・イベント限定", "App/活動限定", "event"),
)
_STOCK_SALE_TAGS = (
    ("抽選已完", "抽選已完", "ended"),
    ("預約已完", "預約已完", "ended"),
    ("抽選", "抽選", "raffle"),
    ("預約", "預約", "preorder"),
    ("現貨", "現貨", "spot"),
)


def mall_sale_tags(item):
    title = str((item or {}).get("title") or "")
    return [(label, kind) for token, label, kind in _MALL_SALE_TAGS if token in title]


def mall_stock_tags(item):
    item = item or {}
    label = str(item.get("status_label") or "")
    title = str(item.get("title") or "")
    remark = str(item.get("remark") or "")
    found = []
    seen = set()
    for token, text, kind in _STOCK_SALE_TAGS:
        if token in seen:
            continue
        if token in label or token == remark or ("【%s】" % token) in title:
            found.append((text, kind))
            seen.add(token)
            label = label.replace(token, "")
            title = title.replace("【%s】" % token, "")
    return found


def status_without_sale_tags(label):
    text = str(label or "")
    for _token, note, _kind in _MALL_SALE_TAGS:
        text = text.replace(note, "")
    text = text.replace("應用活動限定", "")
    for token, _text, _kind in _STOCK_SALE_TAGS:
        text = text.replace(token, "")
    text = re.sub(r"[・、,，]+", "・", text)
    text = re.sub(r"（\s*・", "（", text)
    text = re.sub(r"・\s*）", "）", text)
    text = text.replace("（）", "").replace("()", "")
    return text.strip(" ・")


def sale_tags_html(item):
    return sale_tags_html_for_items([item])


def sale_tags_html_for_items(items):
    chips = []
    seen = set()
    for item in items or []:
        for label, kind in mall_stock_tags(item) + mall_sale_tags(item):
            if label in seen:
                continue
            seen.add(label)
            chips.append(
                "<span class='sale-tag sale-tag--%s'>%s</span>" % (kind, html.escape(label))
            )
    if not chips:
        return ""
    return "<div class='sale-tags'>%s</div>" % "".join(chips)


def product_card_html(item, shop_id="", extra=""):
    item = item or {}
    sku = str(item.get("sku") or "")
    title = html.escape(str(item.get("title") or sku or ""))
    url = item.get("url") or ""
    if url:
        name = "<a href='%s' target='_blank' rel='noopener'>%s</a>" % (
            outbound_href(url),
            title,
        )
    else:
        name = title
    price = item.get("price") or ""
    price_html = html.escape(shown_price_text(item, shop_id)) if price else ""
    status = html.escape(status_without_sale_tags(item.get("status_label") or ""))
    if product_stock_key(item) == "in_stock" or status == "有貨":
        status = "<span class='stock-in'>%s</span>" % status
    if skips_line_model(item) or skips_line_model({"shop_id": shop_id}):
        tag = ""
        model = ""
    else:
        line = product_line_fields(item)
        tag = str(item.get("tag") or line["tag"] or "other")
        model = str(item.get("model") or line["model"] or "")
    shop_label = str(item.get("shop_label") or "")
    brand = shop_label or str(shop_id or "")
    bits = [
        part
        for part in (
            html.escape(shop_label) if shop_label else "",
            html.escape(tag),
            html.escape(model) if model else "",
            html.escape(sku) if sku else "",
            status,
            price_html,
        )
        if part
    ]
    return (
        "<article class='sku-row product-card' data-shop='%s' data-sku='%s' data-tag='%s' data-model='%s'"
        " data-name='%s' data-price='%s' data-brand='%s'>"
        "%s<div class='meta'><div class='name'>%s</div>%s<div class='sub'>%s</div></div>%s</article>"
        % (
            html.escape(str(shop_id or ""), quote=True),
            html.escape(sku, quote=True),
            html.escape(tag, quote=True),
            html.escape(model, quote=True),
            html.escape(str(item.get("title") or sku or ""), quote=True),
            html.escape(
                ""
                if not price
                else str(
                    listing_hkd_value(item, shop_id)
                    if listing_hkd_value(item, shop_id) is not None
                    else ""
                ),
                quote=True,
            ),
            html.escape(brand, quote=True),
            product_thumb_html(item),
            name,
            sale_tags_html(item),
            " · ".join(bits),
            extra,
        )
    )


def models_href(tag=None, stock=None, sort=None, shop=None, layout="grid"):
    query = []
    if stock == "in_stock":
        query.append(("stock", "in"))
    elif stock == "out_of_stock":
        query.append(("stock", "out"))
    if tag in ("CX", "BX", "UX", "BXG", "kuji", "other"):
        query.append(("tag", tag))
    if sort == "new":
        query.append(("sort", "new"))
    if shop and shop != "all":
        query.append(("shop", shop))
    base = "/shop/all" if layout == "list" else "/product"
    if query:
        return base + "?" + urllib.parse.urlencode(query)
    return base


def _listing_stamp(value):
    text = str(value or "").replace("T", " ")[:19].strip()
    if re.match(r"\d{4}-\d{2}-\d{2}$", text):
        return text + " 00:00:00"
    if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", text):
        return text
    return ""


def group_publish_info(group):
    group = group or {}
    face = catalog_face_for_model(group.get("model")) or {}
    release = _listing_stamp(face.get("release"))
    if release:
        return release, "發售日"
    times = [_listing_stamp(item.get("stock_changed_at")) for item in group.get("items") or []]
    times = [stamp for stamp in times if stamp]
    if times:
        return max(times), ""
    return "", ""


def group_publish_stamp(group):
    return group_publish_info(group)[0]


def _sort_groups_newest(groups):
    dated = []
    undated = []
    for group in groups or []:
        if group_publish_stamp(group):
            dated.append(group)
        else:
            undated.append(group)
    dated.sort(key=group_publish_stamp, reverse=True)
    return dated + undated


_CATALOG_PRODUCT_CACHE = {"stamp": None, "by_id": {}}
_BROWSER_CATALOG_CACHE = {"stamp": None, "dir": None, "by_model": {}}
_BROWSER_CODE_RE = re.compile(r"^(BXG|BXH|BXC|BXA|CX|UX|BX)-?(\d{2})(.*)$", re.I)


def _catalog_products_by_id():
    from parts_catalog import PARTS_DIR

    path = os.path.join(PARTS_DIR, "products.json")
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return {}
    if _CATALOG_PRODUCT_CACHE["stamp"] == stamp:
        return _CATALOG_PRODUCT_CACHE["by_id"]
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        return {}
    by_id = {}
    if isinstance(raw, dict):
        for key, rec in raw.items():
            if not isinstance(rec, dict):
                continue
            product_id = str(rec.get("id") or key).strip().upper()
            if product_id:
                by_id[product_id] = rec
    _CATALOG_PRODUCT_CACHE["stamp"] = stamp
    _CATALOG_PRODUCT_CACHE["by_id"] = by_id
    return by_id


# Takara tool products. These are launchers, grips, stadiums, and cases,
# so the model card uses the official accessory photo instead of a shop listing.
_ACCESSORY_FACES = {
    "BX-09": "對戰通行證",
    "BX-10": "極限對戰盤",
    "BX-11": "發射器握把",
    "BX-12": "3on3 陀螺收納盒",
    "BX-18": "旋風發射器",
    "BX-25": "陀螺收納盒",
    "BX-28": "旋風發射器 白色版",
    "BX-30": "自訂握把 紅色版",
    "BX-32": "寬版極限對戰盤",
    "BX-40": "左迴旋拉條發射器 L",
    "BX-43": "陀螺收納盒 白色版",
    "BX-47": "左迴旋旋風發射器 L 紅色版",
    "BX-57": "3on3 陀螺收納盒 黑色版",
    "BXG-62": "旋風發射器 B4 限定色版",
}
_ACCESSORY_IMAGE = "https://beybladehub.app/accessories/raw/%s.webp"


def browser_catalog_dir():
    override = (os.environ.get("BEYBLADE_BROWSER_DATA") or "").strip()
    if override:
        return override
    prod = "/home/ubuntu/beybladex_hk_notify/browser/dist/data"
    if os.path.isdir(prod):
        return prod
    return ""


def _browser_model_key(raw):
    text = str(raw or "").strip().upper()
    base, sep, rest = text.partition("::")
    match = _BROWSER_CODE_RE.match(base.replace(" ", ""))
    if match:
        base = "%s-%s%s" % (match.group(1).upper(), match.group(2), match.group(3).upper())
    if not sep:
        return base
    return "%s::%s" % (base, rest.lower())


def _browser_face_rank(model, kind):
    if model in _ACCESSORY_FACES and kind in ("stadium", "grip"):
        return 0
    return {"set": 1, "package": 2, "stadium": 3, "grip": 3}.get(kind, 4)


def _browser_face_name(labels, model):
    labels = labels or {}
    text = str(labels.get("zh-HK") or labels.get("en") or "").strip()
    folded = text.upper()
    for prefix in (model, model.replace("-", "")):
        if prefix and folded.startswith(prefix):
            text = text[len(prefix):].strip(" -")
            break
    return text


def _load_browser_faces(directory):
    try:
        with open(os.path.join(directory, "catalog.json"), encoding="utf-8") as fh:
            catalog = json.load(fh)
    except (OSError, ValueError):
        return {}
    try:
        with open(os.path.join(directory, "i18n.json"), encoding="utf-8") as fh:
            i18n = json.load(fh)
    except (OSError, ValueError):
        i18n = {}
    if not isinstance(i18n, dict):
        i18n = {}
    best = {}
    products = catalog.get("products") if isinstance(catalog, dict) else None
    for rec in products or []:
        if not isinstance(rec, dict):
            continue
        image = str(rec.get("image") or "").strip()
        if not image.startswith("/browser/assets/"):
            continue
        key = _browser_model_key(rec.get("id"))
        model = key.split("::", 1)[0]
        if not model:
            continue
        rank = _browser_face_rank(model, str(rec.get("kind") or ""))
        current = best.get(model)
        if current and current[0] <= rank:
            continue
        name = _browser_face_name(i18n.get(rec.get("id")) or i18n.get(key), model)
        release = str(rec.get("releaseDate") or "")[:10]
        best[model] = (rank, {"name": name, "image": image, "release": release})
    return {model: face for model, (_, face) in best.items()}


def _browser_catalog_faces():
    directory = browser_catalog_dir()
    path = os.path.join(directory, "catalog.json") if directory else ""
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        stamp = None
        directory = ""
    cached = _BROWSER_CATALOG_CACHE
    if cached["dir"] == directory and cached["stamp"] == stamp:
        return cached["by_model"]
    faces = _load_browser_faces(directory) if directory else {}
    cached["dir"] = directory
    cached["stamp"] = stamp
    cached["by_model"] = faces
    return faces


def catalog_face_for_model(model):
    model = str(model or "").strip().upper()
    if not model:
        return None
    browser = _browser_catalog_faces().get(model)
    if browser and browser.get("image"):
        return {
            "name": browser.get("name") or model,
            "image": browser["image"],
            "release": browser.get("release") or "",
            "kind": "browser",
        }
    accessory = _ACCESSORY_FACES.get(model)
    if accessory:
        return {
            "name": accessory,
            "image": _ACCESSORY_IMAGE % model,
            "kind": "accessory",
        }
    by_id = _catalog_products_by_id()
    rec = by_id.get(model)
    if rec is None:
        prefix = model + "-"
        for key in sorted(by_id):
            if key.startswith(prefix):
                rec = by_id[key]
                break
    if not rec:
        return None
    name = str(rec.get("name_zh") or rec.get("name_en") or "").strip()
    if name.upper().startswith(model):
        rest = name[len(model):].strip(" -")
        if rest:
            name = rest
    image = ""
    rel = str(rec.get("image_path") or "").strip()
    if rel:
        from catalog_pages import catalog_image_href

        image = catalog_image_href(rel)
    if not name and not image:
        return None
    return {"name": name, "image": image}


def notify_card_image_html(item, alt, placeholder, src=""):
    rel = str((item or {}).get("image_path") or "").replace("\\", "/")
    remote = str(src or "").strip() or product_image_url(item)
    cached = ""
    if rel.startswith("images/") and ".." not in rel:
        cached = cdn_image_url("/" + rel)
    src = remote or cached
    label = html.escape((placeholder or "?")[:2])
    if not src:
        return "<span class='catalog-card__placeholder'>%s</span>" % label
    hide = (
        "this.onerror=null;this.style.display='none';"
        "var ph=this.parentNode.querySelector('.catalog-card__placeholder');"
        "if(ph)ph.hidden=false;"
    )
    if remote and cached:
        extra = " onerror=\"this.onerror=function(){%s};this.src='%s'\"" % (
            hide,
            html.escape(cached, quote=True),
        )
    else:
        extra = ' onerror="%s"' % hide
    return (
        "<img src='%s' alt='%s' loading='lazy' decoding='async'%s>"
        "<span class='catalog-card__placeholder' hidden>%s</span>"
        % (
            html.escape(src, quote=True),
            html.escape(alt, quote=True),
            extra,
            label,
        )
    )


def format_listing_price(value):
    if value is None:
        return ""
    if abs(value - round(value)) < 0.001:
        return "HK$%d" % int(round(value))
    return "HK$%.2f" % value


def listing_price_values(items):
    values = []
    for item in items or []:
        value = listing_hkd_value(item)
        if value is not None:
            values.append(value)
    return values


def _foreign_price_span(priced, formatter):
    values = [listing_price_value(item) for item in priced]
    low, high = min(values), max(values)
    if len(priced) > 1 and high - low >= 0.001:
        return "%s – %s" % (formatter(low), formatter(high))
    return formatter(low)


def listing_price_label(items):
    priced = [item for item in items or [] if listing_price_value(item) is not None]
    if priced and all(item_currency_code(item) == "USD" for item in priced):
        return _foreign_price_span(priced, format_usd_with_hkd)
    if priced and all(
        item_currency_code(item) == "JPY" and amazon_jp_retail_price(item) for item in priced
    ):
        return _foreign_price_span(priced, format_jpy_retail_with_hkd)
    if priced and all(item_currency_code(item) == "JPY" for item in priced):
        return _foreign_price_span(priced, format_yen_with_hkd)
    values = listing_price_values(items)
    if not values:
        return ""
    low, high = min(values), max(values)
    if len(items or []) > 1 and high - low >= 0.001:
        return "%s – %s" % (format_listing_price(low), format_listing_price(high))
    return format_listing_price(values[0] if len(values) == 1 else low)


def current_price_items(items):
    items = list(items or [])
    in_stock = [item for item in items if product_stock_key(item) == "in_stock"]
    return in_stock or items


def group_stock_key(items):
    keys = {product_stock_key(item) for item in items or []}
    if "in_stock" in keys:
        return "in_stock"
    if "out_of_stock" in keys:
        return "out_of_stock"
    return "unknown"


def group_shown_stock_label(items, stock):
    chosen = [item for item in items or [] if product_stock_key(item) == stock]
    labels = [
        status_without_sale_tags((item or {}).get("status_label") or "").strip() for item in chosen
    ]
    plain = status_text(stock)
    if chosen and labels and all(label and label == labels[0] for label in labels) and labels[0] != plain:
        return labels[0]
    return plain


def offer_status_html(item):
    stock = product_stock_key(item)
    label = status_without_sale_tags((item or {}).get("status_label") or status_text(stock) or "")
    if not label:
        return ""
    css = {"in_stock": "stock-in", "out_of_stock": "stock-out"}.get(stock, "")
    if css:
        return "<span class='%s'>%s</span>" % (css, html.escape(label))
    return html.escape(label)


def listing_display_rank(item):
    price = listing_hkd_value(item)
    return (
        0 if product_stock_key(item) == "in_stock" else 1,
        price if price is not None else 10 ** 12,
    )


def _offer_price_html(item):
    price = shown_price_text(item)
    if not price:
        price = format_listing_price(listing_price_value(item))
    if not price:
        return ""
    css = {"in_stock": "price-in", "out_of_stock": "price-out"}.get(product_stock_key(item), "")
    text = html.escape(price)
    if not css:
        return text
    return "<span class='%s'>%s</span>" % (css, text)


# Colon separates umbrella lines (CX-00) from the combo, e.g. CX-00:S4-70V.
# CJK stays so folded shop titles such as CX-00:限定S6-60V stay addressable.
_PUBLIC_MODEL_RE = re.compile(
    r"^[A-Z0-9][A-Z0-9+._:\-\u4e00-\u9fff]{0,80}$"
)


def public_model_code(raw):
    text = urllib.parse.unquote(str(raw or "")).strip()
    if not text or "/" in text or "\\" in text or ".." in text:
        return ""
    code = _canonical_model_code(text)
    if not code or not _PUBLIC_MODEL_RE.match(code):
        return ""
    return code


def model_public_path(code):
    return "/product/" + urllib.parse.quote(str(code or ""), safe="-._")


def model_index_codes(items=None, cfg=None):
    codes = []
    seen = set()

    def add(raw):
        code = public_model_code(raw)
        if not code or code in seen:
            return
        seen.add(code)
        codes.append(code)

    for key in _catalog_products_by_id():
        add(key)
    if items is None:
        items = load_shop_products_for_shop_id("all", cfg)
    for group in group_listings_by_model(items):
        add(group.get("model"))
    codes.sort()
    return codes


def _clean_model_name(code, name):
    name = str(name or "").strip()
    if not name:
        return ""
    name = re.sub(
        r"[（(]\s*%s\s*[）)]" % re.escape(code),
        "",
        name,
        flags=re.I,
    ).strip()
    if name.upper().startswith(code):
        name = name[len(code):].strip(" -·")
    return name.strip()


def _model_english_name(product):
    en = str((product or {}).get("name_en") or "").strip()
    if not en:
        return ""
    if re.search(r"[a-z]", en) or " " in en:
        return en
    return ""


def _schema_price(value):
    if abs(value - round(value)) < 0.001:
        return "%d" % int(round(value))
    return "%.2f" % value


def _schema_availability(stock):
    if stock == "in_stock":
        return "https://schema.org/InStock"
    if stock == "out_of_stock":
        return "https://schema.org/OutOfStock"
    return "https://schema.org/LimitedAvailability"


def _group_for_model(items, code):
    for group in group_listings_by_model(items):
        if str(group.get("model") or "").upper() == code:
            return group
    return None


def model_heading(code, product, face):
    zh = _clean_model_name(
        code,
        (product or {}).get("name_zh") or (face or {}).get("name") or "",
    )
    en = _model_english_name(product)
    bits = [code]
    if zh:
        bits.append(zh)
    if en and en.lower() not in " ".join(bits).lower():
        bits.append(en)
    return " ".join(bits)


_KIND_LABELS = {
    "set": "套組",
    "blade": "鋼鐵戰刃",
    "ratchet": "固鎖輪盤",
    "bit": "軸心",
    "lock_chip": "鎖定紋章",
    "main_blade": "主要戰刃",
    "over_blade": "超越戰刃",
    "metal_blade": "金屬戰刃",
    "assist_blade": "輔助戰刃",
    "package": "彩盒",
    "stadium": "戰鬥盤",
    "grip": "握把",
}
_MAKER_LABELS = {"tt": "亞版", "hasbro": "美版"}
_MODEL_ALIAS_RE = re.compile(r"^(BXG|BXH|BXC|BXA|CX|UX|BX)-?(\d+)(.*)$", re.I)
_BROWSER_DETAIL_CACHE = {"stamp": None, "dir": None, "records": None}
_STOCK_HISTORY_CACHE = {"stamp": None, "path": None, "by_code": None}


def _own_catalog_codes(raw):
    text = str(raw or "").strip().upper().replace(" ", "")
    if not text:
        return set()
    base = text.split("::", 1)[0]
    match = _MODEL_ALIAS_RE.match(base)
    if not match:
        return {text}
    canonical = "%s-%s%s" % (match.group(1).upper(), match.group(2), match.group(3).upper())
    return {canonical, canonical.replace("-", "", 1), text}


def model_code_aliases(value):
    raw = str(value or "").strip().upper()
    if not raw:
        return []
    base = raw.split("::", 1)[0].replace(" ", "")
    match = _MODEL_ALIAS_RE.match(base)
    if match:
        canonical = "%s-%s%s" % (match.group(1).upper(), match.group(2), match.group(3).upper())
    else:
        canonical = base or raw
    aliases = [canonical, canonical.replace("-", "", 1), raw]
    parent = re.match(r"^([A-Z]{2,4})-(\d+)-\d{2}$", canonical)
    if parent:
        aliases = ["%s-%s" % parent.groups(), "%s%s" % parent.groups()] + aliases
    return list(dict.fromkeys(alias for alias in aliases if alias))


def _localized_text(value):
    if isinstance(value, dict):
        return str(value.get("zh-HK") or value.get("zh") or value.get("en") or "").strip()
    return str(value or "").strip()


def _gallery_urls(record):
    raw = record.get("images") if isinstance(record.get("images"), list) else []
    if not raw:
        image = str(record.get("image") or "").strip()
        raw = [image] if image else []
    urls = []
    for url in raw:
        url = str(url or "").strip()
        if url and url not in urls:
            urls.append(url)
    return urls


def _release_parts(value):
    text = str(value or "").strip()
    match = re.match(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)
    if not match:
        return "", text
    iso = "%s-%02d-%02d" % (match.group(1), int(match.group(2)), int(match.group(3)))
    return iso, iso


def _catalog_shops(record):
    shops = []
    for shop in record.get("shops") or []:
        if not isinstance(shop, dict):
            continue
        url = str(shop.get("url") or "").strip()
        label = str(shop.get("label") or "").strip()
        if label and url.startswith("http"):
            shops.append({"label": label, "url": url})
    return shops


def _normalize_browser_record(record, labels):
    item_id = str(record.get("id") or "").strip()
    if not item_id:
        return None
    name = _localized_text(labels.get(item_id) if isinstance(labels, dict) else None)
    kind = str(record.get("kind") or "").strip()
    images = _gallery_urls(record)
    part_ids = []
    for part_id in record.get("partIds") or []:
        part_id = str(part_id or "").strip()
        if part_id and part_id not in part_ids:
            part_ids.append(part_id)
    release_iso, release_label = _release_parts(record.get("releaseDate"))
    return {
        "id": item_id,
        "codes": _own_catalog_codes(item_id),
        "name": name or item_id,
        "description": _localized_text(record.get("description")),
        "kind": kind,
        "kind_label": _KIND_LABELS.get(kind, kind),
        "line": str(record.get("line") or "").strip(),
        "maker_label": _MAKER_LABELS.get(str(record.get("manufacturer") or "").strip(), ""),
        "price": str(record.get("price") or "").strip(),
        "release_iso": release_iso,
        "release_label": release_label,
        "shops": _catalog_shops(record),
        "part_ids": part_ids,
        "images": images,
    }


def _browser_detail_records():
    directory = browser_catalog_dir()
    path = os.path.join(directory, "catalog.json") if directory else ""
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        stamp = None
        directory = ""
    cached = _BROWSER_DETAIL_CACHE
    if cached["dir"] == directory and cached["stamp"] == stamp and cached["records"] is not None:
        return cached["records"]
    records = []
    if directory:
        try:
            with open(path, encoding="utf-8") as fh:
                catalog = json.load(fh)
        except (OSError, ValueError):
            catalog = {}
        try:
            with open(os.path.join(directory, "i18n.json"), encoding="utf-8") as fh:
                labels = json.load(fh)
        except (OSError, ValueError):
            labels = {}
        if not isinstance(labels, dict):
            labels = {}
        if isinstance(catalog, dict):
            for collection in ("products", "parts"):
                for record in catalog.get(collection) or []:
                    if not isinstance(record, dict):
                        continue
                    normalized = _normalize_browser_record(record, labels)
                    if normalized:
                        records.append(normalized)
    cached["dir"] = directory
    cached["stamp"] = stamp
    cached["records"] = records
    return records


def _text_record_rank(code, record):
    exact = 0 if record["id"].upper() == str(code or "").upper() else 1
    kind = {"set": 0, "package": 1, "stadium": 2, "grip": 2}.get(record.get("kind"), 3)
    return (exact, kind, record["id"])


def browser_model_detail(code):
    wanted = _own_catalog_codes(code)
    if not wanted:
        return None
    records = _browser_detail_records()
    matches = [record for record in records if wanted & record["codes"]]
    if not matches:
        return None
    text = sorted(matches, key=lambda record: _text_record_rank(code, record))[0]
    gallery = sorted(
        matches,
        key=lambda record: (-len(record["images"]),) + _text_record_rank(code, record),
    )[0]
    by_id = {record["id"]: record for record in records}
    parts = []
    for part_id in text["part_ids"]:
        if part_id.upper() == str(code or "").upper():
            continue
        part = by_id.get(part_id)
        parts.append(
            {
                "id": part_id,
                "name": part["name"] if part else part_id,
                "kind_label": part["kind_label"] if part else "",
                "image": (part["images"][0] if part and part["images"] else ""),
                "href": "/browser/item/" + urllib.parse.quote(part_id, safe="-._~:"),
            }
        )
    images = gallery["images"] or text["images"]
    return {
        "name": text["name"],
        "description": text["description"] or gallery["description"],
        "kind_label": text["kind_label"],
        "line": text["line"] or gallery["line"],
        "maker_label": text["maker_label"] or gallery["maker_label"],
        "price": text["price"] or gallery["price"],
        "release_iso": text["release_iso"] or gallery["release_iso"],
        "release_label": text["release_label"] or gallery["release_label"],
        "shops": text["shops"] or gallery["shops"],
        "images": images,
        "parts": parts,
    }


def _load_stock_history(path):
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        _STOCK_HISTORY_CACHE["stamp"] = None
        _STOCK_HISTORY_CACHE["path"] = path
        _STOCK_HISTORY_CACHE["by_code"] = {}
        return {}
    cached = _STOCK_HISTORY_CACHE
    if cached["path"] == path and cached["stamp"] == stamp and cached["by_code"] is not None:
        return cached["by_code"]
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        payload = {}
    by_code = payload.get("byCode") if isinstance(payload, dict) else {}
    if not isinstance(by_code, dict):
        by_code = {}
    cached["path"] = path
    cached["stamp"] = stamp
    cached["by_code"] = by_code
    return by_code


def model_stock_history(code, limit=15):
    directory = browser_catalog_dir()
    if not directory:
        return []
    by_code = _load_stock_history(os.path.join(directory, "stock-history.json"))
    if not by_code:
        return []
    keys = []
    for alias in [str(code or "")] + model_code_aliases(code):
        if alias and alias not in keys:
            keys.append(alias)
    seen = set()
    events = []
    for key in keys:
        for row in by_code.get(key) or []:
            if not isinstance(row, dict):
                continue
            ident = (
                str(row.get("at") or ""),
                str(row.get("shop") or ""),
                str(row.get("title") or ""),
            )
            if ident in seen:
                continue
            seen.add(ident)
            events.append(row)
    events.sort(key=lambda row: str(row.get("at") or ""), reverse=True)
    return events[:limit]


def _public_asset_url(url):
    url = str(url or "").strip()
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        origin = (os.environ.get("BEYBLADE_CDN_ORIGIN") or CDN_ORIGIN).rstrip("/")
        if origin in ("", "local", "-"):
            origin = SITE_ORIGIN
        return origin.rstrip("/") + url
    return url


def _schema_images(image):
    if isinstance(image, (list, tuple)):
        values = image
    elif image:
        values = [image]
    else:
        values = []
    urls = []
    for value in values:
        url = _public_asset_url(value)
        if url and url not in urls:
            urls.append(url)
    return urls


def _plain_description(text):
    return " ".join(str(text or "").replace("\\n", " ").split())


def _description_html(text):
    text = str(text or "").replace("\\n", "\n")
    return "<br>".join(html.escape(line) for line in text.split("\n"))


def model_product_json_ld(code, title, description, page_url, image, product, items, name=""):
    items = list(items or [])
    node = {
        "@type": "Product",
        "name": name or model_heading(code, product, {}),
        "sku": code,
        "mpn": code,
        "brand": {"@type": "Brand", "name": "Beyblade X"},
        "description": description,
        "url": page_url,
    }
    images = _schema_images(image)
    if images:
        node["image"] = images
    jan = re.sub(r"\D", "", str((product or {}).get("jan") or ""))
    if len(jan) == 13:
        node["gtin13"] = jan
    offers = []
    for item in items:
        price = listing_hkd_value(item)
        if price is None:
            continue
        shop = str(item.get("shop_label") or item.get("shop_id") or "").strip()
        offer = {
            "@type": "Offer",
            "priceCurrency": "HKD",
            "price": _schema_price(price),
            "availability": _schema_availability(product_stock_key(item)),
            "url": str(item.get("url") or "").strip() or page_url,
        }
        if shop:
            offer["seller"] = {"@type": "Organization", "name": shop}
        offers.append(offer)
    if offers:
        prices = [listing_hkd_value(item) for item in items]
        prices = [price for price in prices if price is not None]
        stock = group_stock_key(items)
        node["offers"] = {
            "@type": "AggregateOffer",
            "priceCurrency": "HKD",
            "lowPrice": _schema_price(min(prices)),
            "highPrice": _schema_price(max(prices)),
            "offerCount": len(offers),
            "availability": _schema_availability(stock),
            "offers": offers,
        }
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "name": title,
                "description": description,
                "url": page_url,
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "首頁",
                        "item": page_canonical("/"),
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "全部現貨",
                        "item": page_canonical("/product"),
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": code,
                        "item": page_url,
                    },
                ],
            },
            node,
        ],
    }


def models_index_json_ld(groups, title, description):
    elements = []
    for group in groups or []:
        code = public_model_code(group.get("model"))
        if not code:
            continue
        elements.append(
            {
                "@type": "ListItem",
                "position": len(elements) + 1,
                "name": code,
                "url": page_canonical(model_public_path(code)),
            }
        )
    if not elements:
        return None
    page_url = page_canonical("/product")
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "name": title,
                "description": description,
                "url": page_url,
            },
            {
                "@type": "ItemList",
                "numberOfItems": len(elements),
                "itemListElement": elements,
            },
        ],
    }


def _model_gallery_html(images, alt):
    images = [str(url or "").strip() for url in images or [] if str(url or "").strip()]
    if not images:
        return ""
    count = ""
    thumbs = ""
    if len(images) > 1:
        buttons = []
        for index, url in enumerate(images):
            buttons.append(
                "<button type='button' class='model-hero__thumb%s' data-model-photo='%s' data-model-index='%d'>"
                "<img src='%s' alt='%s'></button>"
                % (
                    " is-active" if index == 0 else "",
                    html.escape(url, quote=True),
                    index + 1,
                    html.escape(url, quote=True),
                    html.escape("%s 圖 %d" % (alt, index + 1), quote=True),
                )
            )
        thumbs = "<div class='model-hero__thumbs'>%s</div>" % "".join(buttons)
        count = "<span class='model-hero__count' id='model-hero-count'>1 / %d</span>" % len(images)
    main = (
        "<div class='model-hero__stage'><img id='model-hero-photo' src='%s' alt='%s'>%s</div>"
        % (html.escape(images[0], quote=True), html.escape(alt, quote=True), count)
    )
    return "<div class='model-hero__media'>%s%s</div>" % (main, thumbs)


def _model_parts_html(parts):
    cards = []
    for part in parts or []:
        name = str(part.get("name") or part.get("id") or "")
        image = str(part.get("image") or "").strip()
        image_html = (
            "<img src='%s' alt='%s'>"
            % (html.escape(image, quote=True), html.escape(name, quote=True))
            if image
            else ""
        )
        kind = str(part.get("kind_label") or "").strip()
        kind_html = "<span class='model-part__kind'>%s</span>" % html.escape(kind) if kind else ""
        cards.append(
            "<li><a href='%s'>%s%s<code>%s</code><span>%s</span></a></li>"
            % (
                html.escape(str(part.get("href") or ""), quote=True),
                image_html,
                kind_html,
                html.escape(str(part.get("id") or "")),
                html.escape(name),
            )
        )
    if not cards:
        return ""
    return (
        "<section class='model-block'><h2>包含部件</h2><ul class='model-parts'>%s</ul></section>"
        % "".join(cards)
    )


def _model_official_shops_html(shops):
    links = []
    for shop in shops or []:
        url = str(shop.get("url") or "").strip()
        label = str(shop.get("label") or "").strip()
        if not label or not url.startswith("http"):
            continue
        links.append(
            "<li><a href='%s' target='_blank' rel='noopener'>%s</a></li>"
            % (outbound_href(url), html.escape(label))
        )
    if not links:
        return ""
    return (
        "<div class='model-shops'><span class='model-kicker'>官方商店</span><ul>%s</ul></div>"
        % "".join(links)
    )


def _model_offer_card(shop, title, price_html, status_html, when, image_html="", tags_html=""):
    aside = "".join(
        part
        for part in (
            "<span class='model-stock__price'>%s</span>" % price_html if price_html else "",
            status_html,
            "<span class='model-stock__when'>%s</span>" % html.escape(when) if when else "",
        )
    )
    return (
        "%s<span class='model-stock__main'><span class='model-stock__shop'>%s</span>"
        "<span class='model-stock__title'>%s</span>%s</span><span class='model-stock__aside'>%s</span>"
        % (image_html, html.escape(shop), html.escape(title), tags_html, aside)
    )


def _model_stock_row_html(item):
    item = item or {}
    title = str(item.get("title") or item.get("sku") or "")
    shop = str(item.get("shop_label") or item.get("shop_id") or "").strip()
    url = str(item.get("url") or "").strip()
    changed = _listing_stamp(item.get("stock_changed_at"))
    image_html = product_thumb_html(item)
    body = _model_offer_card(
        shop,
        title,
        _offer_price_html(item),
        offer_status_html(item),
        changed[:16] if changed else "",
        image_html,
        sale_tags_html(item),
    )
    css = "model-stock model-stock--photo" if image_html else "model-stock"
    if url:
        return (
            "<li><a class='%s' href='%s' target='_blank' rel='noopener'>%s</a></li>"
            % (css, outbound_href(url), body)
        )
    return "<li><div class='%s'>%s</div></li>" % (css, body)


def _history_price_text(row):
    if isinstance(row, dict):
        text = shown_price_text(row)
        if text:
            return text
        raw = str(row.get("price") or "").strip()
    else:
        raw = str(row or "").strip()
    if raw and raw[0].isdigit():
        return "HK$" + raw
    return raw


def _model_history_html(events):
    rows = []
    for row in events or []:
        shop = str(row.get("shop") or "")
        title = str(row.get("title") or "")
        at = str(row.get("at") or "")[:16]
        price = _history_price_text(row)
        body = _model_offer_card(shop, title, html.escape(price) if price else "", "", at)
        url = str(row.get("url") or "").strip()
        if url.startswith("http"):
            rows.append(
                "<li><a class='model-stock' href='%s' target='_blank' rel='noopener'>%s</a></li>"
                % (outbound_href(url), body)
            )
        else:
            rows.append("<li><div class='model-stock'>%s</div></li>" % body)
    if not rows:
        return ""
    return "<h3>入貨紀錄</h3><ul class='model-stock-list'>%s</ul>" % "".join(rows)


def _model_chips_html(bits):
    chips = []
    for index, bit in enumerate(bits):
        text = str(bit or "").strip()
        if not text:
            continue
        css = " class='is-code'" if index == 0 else ""
        chips.append("<span%s>%s</span>" % (css, html.escape(text)))
    if not chips:
        return ""
    return "<p class='model-chips'>%s</p>" % "".join(chips)


def _model_verdict_html(listed, price_label):
    count = len(listed or [])
    in_count = sum(1 for item in listed or [] if product_stock_key(item) == "in_stock")
    if not count:
        state, css, note = "未有紀錄", "", "香港舖頭"
    elif in_count:
        state, css, note = "%d 間有貨" % in_count, " is-in", "共 %d 間舖" % count
    else:
        state, css, note = "全部缺貨", " is-out", "%d 間舖頭" % count
    price = html.escape(price_label) if price_label else "未標價"
    return (
        "<div class='model-verdict%s'>"
        "<div class='model-verdict__price'><span>香港現價</span><strong>%s</strong></div>"
        "<div class='model-verdict__state'><b>%s</b><span>%s</span></div></div>"
        % (css, price, html.escape(state), html.escape(note))
    )


def _model_gallery_script():
    return """<script>
(function(){
  var photo=document.getElementById("model-hero-photo");
  if(!photo) return;
  var buttons=document.querySelectorAll("[data-model-photo]");
  for(var i=0;i<buttons.length;i++){
    buttons[i].addEventListener("click", function(){
      photo.src=this.getAttribute("data-model-photo");
      for(var j=0;j<buttons.length;j++) buttons[j].classList.remove("is-active");
      this.classList.add("is-active");
      var count=document.getElementById("model-hero-count");
      if(count) count.textContent=this.getAttribute("data-model-index")+" / "+buttons.length;
    });
  }
})();
</script>"""


def render_model_detail_html(code, items=None):
    code = public_model_code(code)
    if not code:
        return None
    if items is None:
        items = load_shop_products_for_shop_id("all")
    group = _group_for_model(items, code)
    listed = list((group or {}).get("items") or [])
    product = _catalog_products_by_id().get(code)
    if not product and not listed:
        return None
    product = product or {}
    face = catalog_face_for_model(code) or {}
    detail = browser_model_detail(code) or {}
    heading = model_heading(code, product, face)
    visible_name = str(detail.get("name") or "").strip()
    if not visible_name or visible_name.upper() == code:
        visible_name = heading
    catalog_name = str(detail.get("name") or "").strip()
    title_heading = catalog_name if catalog_name and catalog_name.upper() != code else heading
    title = "%s 香港現貨 · %s" % (title_heading, SITE_BRAND)
    priced = current_price_items(listed)
    price_label = listing_price_label(priced)
    stock = group_stock_key(listed) if listed else ""
    stock_label = {"in_stock": "有貨", "out_of_stock": "缺貨"}.get(stock, "")
    blurb = _plain_description(detail.get("description") or product.get("description") or "")
    desc = product_seo_description(
        {
            "description": " ".join(
                part
                for part in (blurb, price_label, stock_label, "香港爆旋陀螺現貨")
                if part
            )
        }
    )
    model_keywords = page_keywords(code, visible_name, "香港現貨", "爆旋陀螺價錢", "爆旋陀螺開訂")
    images = list(detail.get("images") or [])
    if not images:
        image = str(face.get("image") or "").strip()
        if not image and listed:
            image = product_image_url(listed[0]) or ""
        if image:
            images = [image]
    page_url = page_canonical(model_public_path(code))
    facts = []
    for label, value in (
        ("JAN", product.get("jan") or ""),
        ("類型", product.get("bey_type") or ""),
        ("原裝配置", product.get("stock_combo") or ""),
    ):
        value = str(value or "").strip()
        if value:
            facts.append(
                "<div class='model-stat'><span>%s</span><b>%s</b></div>"
                % (html.escape(label), html.escape(value))
            )
    release_label = str(detail.get("release_label") or product.get("released_on") or face.get("release") or "").strip()
    release_iso = str(detail.get("release_iso") or "").strip()
    if not release_iso and re.match(r"\d{4}-\d{2}-\d{2}$", release_label):
        release_iso = release_label
    if release_label:
        time_attr = " datetime='%s'" % html.escape(release_iso, quote=True) if release_iso else ""
        facts.insert(
            0,
            "<div class='model-stat'><span>發售</span><b><time%s>%s</time></b></div>"
            % (time_attr, html.escape(release_label)),
        )
    list_price = str(detail.get("price") or "").strip()
    if list_price:
        facts.insert(
            1 if release_label else 0,
            "<div class='model-stat'><span>日版售價</span><b>%s</b></div>" % html.escape(list_price),
        )
    meta_bits = [
        bit
        for bit in (
            detail.get("kind_label"),
            detail.get("line"),
            detail.get("maker_label"),
        )
        if bit
    ]
    chips_html = _model_chips_html([code] + meta_bits)
    verdict_html = _model_verdict_html(listed, price_label)
    body_desc = detail.get("description") or product.get("description") or ""
    desc_html = (
        "<div class='model-copy'><span class='model-kicker'>產品說明</span>"
        "<div class='model-hero__description'>%s</div></div>" % _description_html(body_desc)
        if body_desc
        else ""
    )
    stock_rows = "".join(
        _model_stock_row_html(item) for item in sorted(listed, key=listing_display_rank)
    )
    if not stock_rows:
        stock_rows = "<li class='model-empty'>暫時未有舖頭紀錄</li>"
    history_html = _model_history_html(model_stock_history(code))
    parts_html = _model_parts_html(detail.get("parts"))
    crumbs = (
        "<nav class='crumbs' aria-label='麵包屑'>"
        "<a href='/'>首頁</a> / <a href='/product'>全部現貨</a> / %s</nav>"
        % html.escape(code)
    )
    gallery_script = _model_gallery_script() if len(images) > 1 else ""
    stats_html = "<div class='model-stats'>%s</div>" % "".join(facts) if facts else ""
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
.crumbs{margin:4px 0 0;font-size:12px;line-height:1.3}
.crumbs a{color:#fff}
.wrap:has(.model-page){padding:10px 12px 24px}
.model-page{margin-top:10px;padding:10px 10px 12px;overflow:visible}
.model-hero{display:grid;grid-template-columns:1fr;gap:10px;align-items:start}
.model-hero__media,.model-hero__info,.model-stock__main{min-width:0}
.model-hero__media{display:flex;flex-direction:column;gap:6px}
.model-hero__stage{position:relative;display:flex;align-items:center;justify-content:center;width:fit-content;max-width:100%%;margin-inline:auto;background:#f4f5f8;border:1px solid #e6e6ee;overflow:hidden}
.model-hero__stage img{display:block;width:auto;max-width:100%%;height:auto;max-height:220px;object-fit:contain}
.model-hero__count{position:absolute;right:8px;bottom:8px;padding:2px 6px;background:var(--blue);color:#fff;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.06em}
.model-hero__thumbs{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px}
.model-hero__thumb{flex:0 0 52px;width:52px;height:52px;padding:3px;border:1px solid #e4e4ee;background:#fff;cursor:pointer}
.model-hero__thumb.is-active{border-color:var(--blue);box-shadow:inset 0 0 0 1px var(--blue)}
.model-hero__thumb img{display:block;width:100%%;height:100%%;object-fit:contain}
.model-chips{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 6px}
.model-chips span{border:1px solid #d9d9e4;padding:2px 6px;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.06em;color:#333}
.model-chips .is-code{background:var(--blue);color:#fff;border-color:var(--blue)}
.model-hero h1{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:clamp(22px,5.4vw,26px);line-height:1.15;margin:0 0 8px;max-width:none;text-transform:none;letter-spacing:0}
.model-verdict{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px 12px;padding:8px 10px;margin:0 0 8px;background:var(--blue);color:#fff}
.model-verdict span{display:block;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;opacity:.72}
.model-verdict strong{display:block;margin-top:1px;font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:clamp(22px,5vw,26px);line-height:1}
.model-verdict__state{margin-left:auto;text-align:right;white-space:nowrap}
.model-verdict__state b{display:block;font-size:13px;font-weight:600;letter-spacing:.02em}
.model-verdict.is-in{background:var(--blue)}
.model-verdict.is-out{background:var(--ink)}
.model-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:6px;margin:0 0 8px}
.model-stat{border:1px solid #ececf2;padding:6px 8px;background:#fafafc;min-width:0}
.model-stat span,.model-kicker{display:block;margin-bottom:2px;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#777}
.model-stat b{font-weight:600;font-size:13px;overflow-wrap:anywhere}
.model-shops ul,.model-parts,.model-stock-list{list-style:none;padding:0;margin:0}
.model-shops ul{display:flex;flex-wrap:wrap;gap:6px}
.model-shops a{display:inline-block;border:1px solid var(--ink);padding:5px 8px;color:var(--ink);text-decoration:none;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em}
.model-page a.model-stock,.model-page .model-parts a,.model-page .model-shops a{text-decoration:none}
.model-shops a:hover,.model-parts a:hover,.model-stock:hover{background:rgba(26,26,255,.06)}
.model-copy{margin-top:8px}
.model-hero__description{max-width:68ch;font-size:13px;line-height:1.5;color:#2c2c3a}
.model-page h2{margin:0 0 8px;letter-spacing:.12em}
.model-block{margin-top:12px;padding-top:2px;border-top:1px solid #ececf2}
.model-block h3{margin:12px 0 6px;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#666}
.model-parts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.model-parts a{display:flex;flex-direction:column;gap:4px;min-height:100%%;padding:6px;border:1px solid #ececf2;background:#fff;color:inherit;text-decoration:none}
.model-parts img{width:100%%;aspect-ratio:1;object-fit:contain;background:#f7f7fb}
.model-part__kind,.model-parts code{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.06em;color:#777}
.model-parts a > span:last-child{font-size:12px;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.model-stock-list{display:grid;gap:6px}
.model-stock{display:grid;grid-template-columns:minmax(0,1fr);gap:4px 8px;align-items:center;padding:8px 8px;border:1px solid #ececf2;color:inherit;text-decoration:none;background:#fff}
.model-stock--photo{grid-template-columns:52px minmax(0,1fr)}
.model-stock .thumb,.model-stock .thumb-empty{width:52px;height:52px;flex:none;object-fit:contain;background:#f4f6fb}
.model-stock__shop{display:block;font-weight:700;font-size:14px;line-height:1.25}
.model-stock__title{display:-webkit-box;margin-top:2px;font-size:12px;line-height:1.35;color:#666;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.model-stock__aside{display:flex;flex-direction:row;flex-wrap:wrap;align-items:center;justify-content:flex-start;gap:4px 6px;text-align:left}
.model-stock--photo .thumb,.model-stock--photo .thumb-empty{grid-row:1 / span 2;align-self:center}
.model-stock--photo .model-stock__aside{grid-column:2}
.model-stock__price{font-size:14px;font-weight:700}
.model-stock__when{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.04em;color:#888}
.model-stock .stock-in,.model-stock .stock-out{padding:2px 6px;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.06em}
.model-stock .stock-in{color:#fff;background:var(--blue)}
.model-stock .stock-out{color:var(--ink);background:#ececf8}
.model-stock .price-in,.model-stock .price-out{color:inherit}
.model-empty{padding:10px;border:1px dashed #ddd;color:#666;font-size:13px}
body:has(.install-hint.show) .model-page{padding-bottom:108px}
@media(min-width:700px){
.wrap:has(.model-page){padding:16px 24px 36px}
.model-page{margin-top:14px;padding:14px 16px 16px}
.model-hero{gap:16px}
.model-hero__stage{aspect-ratio:1;width:100%%;max-height:360px;margin:0}
.model-hero__stage img{width:100%%;height:100%%;max-height:none}
.model-hero__thumb{flex-basis:60px;width:60px;height:60px}
.model-hero h1{font-size:clamp(28px,3vw,40px);line-height:1.08;margin:0 0 10px}
.model-verdict{padding:10px 14px}
.model-verdict strong{font-size:clamp(26px,2.6vw,32px)}
.model-verdict__state b{font-size:14px}
.model-stats{gap:8px}
.model-stat{padding:8px 10px}
.model-parts{grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:8px}
.model-stock{grid-template-columns:minmax(0,1fr) auto;gap:10px;padding:8px 12px;align-items:center}
.model-stock--photo{grid-template-columns:56px minmax(0,1fr) auto}
.model-stock .thumb,.model-stock .thumb-empty,.model-stock--photo .thumb,.model-stock--photo .thumb-empty{width:56px;height:56px;grid-column:1;grid-row:1}
.model-stock__main{grid-column:1;grid-row:1;display:flex;align-items:baseline;gap:8px;min-width:0}
.model-stock--photo .model-stock__main{grid-column:2}
.model-stock__shop{flex:none}
.model-stock__title{margin-top:0;flex:1;min-width:0}
.model-stock__aside,.model-stock--photo .model-stock__aside{grid-column:2;grid-row:1;flex-direction:row;flex-wrap:nowrap;align-items:center;justify-content:flex-end;gap:8px 10px;text-align:right;white-space:nowrap}
.model-stock--photo .model-stock__aside{grid-column:3}
.model-stock__title{-webkit-line-clamp:1}
}
@media(min-width:860px){
.model-hero{grid-template-columns:minmax(220px,.78fr) minmax(0,1.22fr);gap:20px}
.model-hero__stage{max-height:420px}
}
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
%s
<section class="panel model-page">
<article class="model-hero">
%s
<div class="model-hero__info">
%s
<h1>%s</h1>
%s
%s
%s
%s
</div>
</article>
%s
<section class="model-block">
<h2>香港店舖庫存</h2>
<ul class="model-stock-list">
%s
</ul>
%s
</section>
</section>
</div>
%s
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            model_public_path(code),
            indexable=True,
            image_url=images[0] if images else None,
            og_type="product",
            keywords=model_keywords,
            json_ld=model_product_json_ld(
                code,
                title,
                desc,
                page_url,
                images,
                product,
                listed,
                name=visible_name,
            ),
        ),
        page_theme_css(),
        site_nav_html(),
        crumbs,
        _model_gallery_html(images, visible_name),
        chips_html,
        html.escape(visible_name),
        verdict_html,
        stats_html,
        _model_official_shops_html(detail.get("shops")),
        desc_html,
        parts_html,
        stock_rows,
        history_html,
        install_hint_block(),
        gallery_script,
    )


def model_offer_html(item):
    item = item or {}
    title = str(item.get("title") or item.get("sku") or "")
    url = str(item.get("url") or "").strip()
    name = html.escape(title)
    if url:
        name = "<a href='%s' target='_blank' rel='noopener'>%s</a>" % (
            outbound_href(url),
            name,
        )
    shop = str(item.get("shop_label") or item.get("shop_id") or "").strip()
    price = _offer_price_html(item)
    changed = _listing_stamp(item.get("stock_changed_at"))
    bits = [part for part in (html.escape(shop) if shop else "", price, html.escape(changed[:16]) if changed else "") if part]
    status = offer_status_html(item)
    if status:
        bits.append(status)
    return (
        "<article class='model-offer'>%s<div class='meta'><div class='name'>%s</div>%s"
        "<div class='sub'>%s</div></div></article>"
        % (product_thumb_html(item), name, sale_tags_html(item), " · ".join(bits))
    )


def catalog_id_label(model):
    parts = [part for part in str(model or "").split("+") if part]
    if len(parts) > 1:
        return " · ".join(parts)
    return str(model or "")


def model_grid_card_html(group):
    group = group or {}
    items = sorted(list(group.get("items") or []), key=listing_display_rank)
    if not items:
        return ""
    primary = items[0]
    model = str(group.get("model") or "")
    face = catalog_face_for_model(model) or {}
    title = str(face.get("name") or primary.get("title") or model or primary.get("sku") or "")
    tag = group_tag_key(group)
    priced = current_price_items(items)
    price_label = listing_price_label(priced)
    price_class = {"in_stock": "price-in", "out_of_stock": "price-out"}.get(group_stock_key(priced), "")
    sku = str(primary.get("sku") or "")
    shop_id = str(primary.get("shop_id") or "")
    brand = str(primary.get("shop_label") or shop_id)
    code = (
        "<code class='catalog-card__id'>%s</code>" % html.escape(catalog_id_label(model))
        if model
        else ""
    )
    range_html = (
        "<p class='catalog-card__subtitle%s'>%s</p>"
        % ((" " + price_class) if price_class else "", html.escape(price_label))
        if price_label
        else ""
    )
    mall_items = [
        item
        for item in items
        if str(item.get("shop_id") or "") == "takaratomymall"
    ]
    tags_html = sale_tags_html_for_items(mall_items)
    placeholder = model or title or "?"
    image_html = notify_card_image_html(primary, title, placeholder, src=face.get("image") or "")
    body = (
        "<div class='catalog-card__body'>%s<h2 class='catalog-card__name'>%s</h2>%s%s</div>"
        % (code, html.escape(title), range_html, tags_html)
    )
    stock = group_stock_key(items)
    stock_label = group_shown_stock_label(items, stock)
    stock_class = {"in_stock": "stock-in", "out_of_stock": "stock-out"}.get(stock, "")
    badge_class = "catalog-card__badge catalog-card__badge--out" if stock == "out_of_stock" else "catalog-card__badge"
    media = (
        "<div class='catalog-card__image'>"
        "<span class='%s'><span class='%s'>%s</span></span>%s</div>"
        % (badge_class, stock_class, html.escape(stock_label), image_html)
    )
    offers = "\n".join(model_offer_html(item) for item in items)
    display_name = title if title and title != model else ""
    label = " · ".join(part for part in (model, display_name) if part)
    shops = []
    for item in items:
        shop = str(item.get("shop_label") or item.get("shop_id") or "").strip()
        if shop and shop not in shops:
            shops.append(shop)
    published, published_label = group_publish_info(group)
    detail_bits = []
    if price_label:
        detail_bits.append(price_label)
    if shops:
        detail_bits.append("%d 間店" % len(shops))
    if published and published_label:
        detail_bits.append("%s %s" % (published_label, published[:10]))
    if model:
        hit = (
            "<a class='catalog-card__hit' href='%s' aria-haspopup='dialog' aria-label='%s'>%s%s</a>"
            % (
                html.escape(model_public_path(model), quote=True),
                html.escape(label, quote=True),
                media,
                body,
            )
        )
    else:
        hit = (
            "<button type='button' class='catalog-card__hit' aria-haspopup='dialog' aria-label='%s'>%s%s</button>"
            % (html.escape(label, quote=True), media, body)
        )
    return (
        "<article class='catalog-card product-card' data-shop='%s' data-sku='%s' data-tag='%s'"
        " data-model='%s' data-name='%s' data-detail='%s' data-price='%s' data-brand='%s'>"
        "%s<div class='model-offer-list' hidden>%s</div></article>"
        % (
            html.escape(shop_id, quote=True),
            html.escape(sku, quote=True),
            html.escape(tag, quote=True),
            html.escape(model, quote=True),
            html.escape(title, quote=True),
            html.escape(" · ".join(detail_bits), quote=True),
            html.escape(price_label, quote=True),
            html.escape(brand, quote=True),
            hit,
            offers,
        )
    )


def model_modal_html():
    return (
        '<div class="model-modal" id="model-modal" hidden>'
        '<button type="button" class="model-modal__backdrop" data-model-close aria-label="關閉"></button>'
        '<div class="model-modal__panel" role="dialog" aria-modal="true" aria-labelledby="model-modal-title">'
        '<div class="model-modal__head"><div>'
        '<h2 class="model-modal__title" id="model-modal-title"></h2>'
        '<p class="model-modal__detail" id="model-modal-detail"></p></div>'
        '<button type="button" class="model-modal__close" data-model-close aria-label="關閉">×</button></div>'
        '<div class="model-modal__scroll"><div class="model-modal__body"></div></div>'
        '<a class="model-modal__page" id="model-modal-page" hidden>查看詳情</a>'
        '</div></div>'
        "<script>(function(){"
        'var modal=document.getElementById("model-modal");'
        "if(!modal)return;"
        'var body=modal.querySelector(".model-modal__body");'
        'var title=modal.querySelector(".model-modal__title");'
        'var detail=modal.querySelector(".model-modal__detail");'
        'var pageLink=document.getElementById("model-modal-page");'
        "var last=null;"
        "function close(){modal.hidden=true;document.body.classList.remove('model-open');if(last)last.focus();}"
        "function open(card,trigger){"
        'var src=card.querySelector(".model-offer-list");'
        "if(!src||!body||!title)return;"
        "body.innerHTML=src.innerHTML;"
        'var code=card.getAttribute("data-model")||"";'
        'var name=card.getAttribute("data-name")||"";'
        'if(name&&name!==code){title.textContent=code?code+" · "+name:name;}'
        'else{title.textContent=code||name||"";}'
        'if(detail){var text=card.getAttribute("data-detail")||"";'
        'var sub=card.querySelector(".catalog-card__subtitle");'
        'var tone=sub&&sub.classList.contains("price-out")?"price-out":(sub&&sub.classList.contains("price-in")?"price-in":"");'
        'var split=text.indexOf(" · ");'
        'if(tone&&text.indexOf("HK$")===0&&split>0){detail.textContent="";'
        'var span=document.createElement("span");span.className=tone;span.textContent=text.slice(0,split);'
        'detail.appendChild(span);detail.appendChild(document.createTextNode(text.slice(split)));}'
        'else detail.textContent=text;}'
        "modal.hidden=false;document.body.classList.add('model-open');last=trigger;"
        "if(pageLink){var href=trigger&&trigger.getAttribute?trigger.getAttribute('href'):'';"
        "if(href){pageLink.hidden=false;pageLink.setAttribute('href',href);}else pageLink.hidden=true;}"
        'var btn=modal.querySelector(".model-modal__close");if(btn)btn.focus();'
        "}"
        'document.addEventListener("click",function(e){'
        'var hit=e.target.closest&&e.target.closest(".catalog-card__hit");'
        "if(hit){var card=hit.closest('.catalog-card');"
        "if(card){e.preventDefault();open(card,hit);}return;}"
        'if(e.target.closest&&e.target.closest("[data-model-close]"))close();'
        "});"
        'document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!modal.hidden)close();});'
        "})();</script>"
    )


def _tagged_buckets(entries, tag_fn):
    buckets = {"CX": [], "BX": [], "UX": [], "BXG": [], "kuji": [], "other": []}
    for entry in entries or []:
        tag = tag_fn(entry)
        buckets.get(tag, buckets["other"]).append(entry)
    return buckets


def model_list_row_html(group):
    group = group or {}
    items = sorted(list(group.get("items") or []), key=listing_display_rank)
    if not items:
        return ""
    primary = items[0]
    model = str(group.get("model") or "")
    face = catalog_face_for_model(model) or {}
    title = str(face.get("name") or primary.get("title") or model or primary.get("sku") or "")
    tag = group_tag_key(group)
    priced = current_price_items(items)
    price_label = listing_price_label(priced)
    stock = group_stock_key(items)
    stock_label = group_shown_stock_label(items, stock)
    stock_class = {"in_stock": "stock-in", "out_of_stock": "stock-out"}.get(stock, "")
    stock_html = (
        "<span class='%s'>%s</span>" % (stock_class, html.escape(stock_label))
        if stock_class
        else html.escape(stock_label)
    )
    shops = []
    for item in items:
        shop = str(item.get("shop_label") or item.get("shop_id") or "").strip()
        if shop and shop not in shops:
            shops.append(shop)
    bits = []
    shown_model = catalog_id_label(model)
    if shown_model and shown_model != title:
        bits.append(html.escape(shown_model))
    if shops:
        shown_shops = shops[:4]
        shop_text = "、".join(shown_shops)
        if len(shops) > len(shown_shops):
            shop_text += "…"
        bits.append(html.escape(shop_text))
    if stock_html:
        bits.append(stock_html)
    if price_label:
        bits.append(html.escape(price_label))
    mall_items = [item for item in items if str(item.get("shop_id") or "") == "takaratomymall"]
    tags_html = sale_tags_html_for_items(mall_items)
    name = html.escape(title)
    if model:
        name = "<a href='%s'>%s</a>" % (html.escape(model_public_path(model), quote=True), name)
    thumb_item = dict(primary)
    if face.get("image") and not product_image_url(thumb_item):
        thumb_item["image"] = face.get("image")
    prices = listing_price_values(priced)
    price_attr = str(int(prices[0])) if prices and float(prices[0]).is_integer() else (
        str(prices[0]) if prices else ""
    )
    sku = str(primary.get("sku") or "")
    shop_id = str(primary.get("shop_id") or "")
    brand = str(primary.get("shop_label") or shop_id)
    return (
        "<article class='sku-row product-card' data-shop='%s' data-sku='%s' data-tag='%s'"
        " data-model='%s' data-name='%s' data-price='%s' data-brand='%s'>"
        "%s<div class='meta'><div class='name'>%s</div>%s<div class='sub'>%s</div></div></article>"
        % (
            html.escape(shop_id, quote=True),
            html.escape(sku, quote=True),
            html.escape(tag, quote=True),
            html.escape(model, quote=True),
            html.escape(title, quote=True),
            html.escape(price_attr, quote=True),
            html.escape(brand, quote=True),
            product_thumb_html(thumb_item),
            name,
            tags_html,
            " · ".join(bits),
        )
    )


def _model_cards_html(groups):
    cards = [model_grid_card_html(group) for group in groups or []]
    cards = [card for card in cards if card]
    if not cards:
        return ""
    return "<div class='model-grid'>\n%s\n</div>" % "\n".join(cards)


def _model_block_html(groups, layout="grid"):
    if layout == "list":
        rows = [model_list_row_html(group) for group in groups or []]
        rows = [row for row in rows if row]
        return "\n".join(rows)
    return _model_cards_html(groups)


def _model_sections_html(groups, sort_filter="", layout="grid"):
    buckets = _tagged_buckets(groups, group_tag_key)
    parts = []
    main = []
    for tag in ("CX", "BX", "UX"):
        main.extend(buckets[tag])
    if sort_filter == "new":
        main = _sort_groups_newest(main)
    main_html = _model_block_html(main, layout)
    if main_html:
        parts.append(main_html)
    for tag, label in (("BXG", "BX+"), ("kuji", "一番賞"), ("other", "other")):
        block = _model_block_html(
            _sort_groups_newest(buckets[tag]) if sort_filter == "new" else buckets[tag],
            layout,
        )
        if not block:
            continue
        parts.append(
            "<section class='model-section' id='models-%s'><h2>%s</h2>%s</section>"
            % (html.escape(tag.lower()), html.escape(label), block)
        )
    return "\n".join(parts)


_FEATURED_SHOP_SECTIONS = (
    ("tclub", "TClub"),
    ("takaratomymall", "Takara Tomy Mall"),
    ("amazon-us-retail", "美版"),
)


def _shop_ids_for_filter(shop_filter):
    shop_filter = str(shop_filter or "")
    if not shop_filter or shop_filter == "all":
        return None
    allowed = {str(source.get("id") or "") for source in sources_for_shop_page(shop_filter)}
    allowed.discard("")
    if not allowed:
        allowed = {shop_filter}
    return allowed


def _product_shop_options(
    shops, current, tag_filter, stock_filter, sort_filter, include_all=False, layout="grid"
):
    options = []
    if include_all:
        options.append(
            (
                models_href(
                    tag_filter or None,
                    stock_filter or None,
                    sort_filter or None,
                    layout=layout,
                ),
                "全部現貨",
                not current,
            )
        )
    for shop in shops or []:
        shop_id = str(shop.get("id") or "")
        if not shop_id or shop_id == "all":
            continue
        options.append(
            (
                models_href(
                    tag_filter or None,
                    stock_filter or None,
                    sort_filter or None,
                    shop_id,
                    layout=layout,
                ),
                str(shop.get("label") or shop_id),
                shop_id == current,
            )
        )
    return options


def models_shop_grid_html(
    shops, current_id="", tag_filter="", stock_filter="", sort_filter="", layout="grid"
):
    current = str(current_id or "")
    ordered = []
    overseas = []
    for shop in shops or []:
        if shop_is_overseas(shop):
            overseas.append(shop)
        else:
            ordered.append(shop)
    ordered.extend(overseas)
    return (
        '<div id="all-stock">%s</div>'
        % filter_options_html(
            _product_shop_options(
                ordered,
                current,
                tag_filter,
                stock_filter,
                sort_filter,
                include_all=True,
                layout=layout,
            ),
            wrap_class="shop-chips",
            force_combo=True,
            empty_label="全部現貨",
        )
    )


def _filter_model_groups(groups, stock_filter="", tag_filter="", sort_filter=""):
    shown = list(groups or [])
    if stock_filter in ("in_stock", "out_of_stock"):
        shown = [
            group
            for group in shown
            if any(product_stock_key(item) == stock_filter for item in group.get("items") or [])
        ]
    if tag_filter:
        shown = [group for group in shown if group_tag_key(group) == tag_filter]
    if sort_filter == "new":
        shown = _sort_groups_newest(shown)
    return shown


def _tclub_special_model(code):
    """Umbrella lines and BX+ products, the only models kept in the TClub section."""
    text = str(code or "").upper()
    if re.match(r"^(BX|CX|UX)-00(?:$|[^A-Z0-9])", text):
        return True
    return bool(re.match(r"^BX[A-Z]", text))


def _listing_identity(item):
    item = item or {}
    return (
        str(item.get("shop_id") or ""),
        str(item.get("sku") or ""),
        str(item.get("title") or ""),
    )


def _tclub_exclusive_items(items):
    """TClub BX-00 / CX-00 / UX-00 / BX+ listings that no other shop carries."""
    tclub_ids = set(_shop_ids_for_filter("tclub") or {"tclub"})
    other_codes = set()
    for item in items or []:
        if str(item.get("shop_id") or "") in tclub_ids:
            continue
        code = listing_model_code(item).upper()
        if code:
            other_codes.add(code)
    kept = []
    for item in items or []:
        if str(item.get("shop_id") or "") not in tclub_ids:
            continue
        code = listing_model_code(item).upper()
        if not _tclub_special_model(code) or code in other_codes:
            continue
        kept.append(item)
    return kept


def _shop_filter_is(shop_filter, shop_id):
    allowed = _shop_ids_for_filter(shop_filter)
    if not allowed:
        return False
    ids = set(_shop_ids_for_filter(shop_id) or {shop_id})
    return bool(allowed) and allowed <= ids


def _featured_shop_sections_html(items, stock_filter="", tag_filter="", sort_filter="", layout="grid"):
    mall_ids = set(_shop_ids_for_filter("takaratomymall") or {"takaratomymall"})
    us_ids = set(_shop_ids_for_filter("amazon-us-retail") or {"amazon-us-retail"})
    scoped_by_shop = {
        "tclub": _tclub_exclusive_items(items),
        "takaratomymall": [
            item
            for item in items or []
            if str(item.get("shop_id") or "") in mall_ids
        ],
        "amazon-us-retail": [
            item
            for item in items or []
            if str(item.get("shop_id") or "") in us_ids
        ],
    }
    parts = []
    for shop_id, label in _FEATURED_SHOP_SECTIONS:
        shown = _filter_model_groups(
            group_listings_by_model(scoped_by_shop.get(shop_id) or []),
            stock_filter,
            tag_filter,
            sort_filter,
        )
        cards = _model_block_html(shown, layout)
        if not cards:
            continue
        parts.append(
            "<section class='model-section' id='models-%s'><h2>%s</h2>%s</section>"
            % (html.escape(shop_id), html.escape(label), cards)
        )
    return "\n".join(parts)


def render_models_html(
    items, tag_filter="", stock_filter="", sort_filter="", shop_filter="", shops=None, layout="grid"
):
    items = list(items or [])
    if shops is None:
        shops = shop_chip_shops()
    allowed_shops = _shop_ids_for_filter(shop_filter)
    if allowed_shops is not None:
        items = [
            item
            for item in items
            if str(item.get("shop_id") or "") in allowed_shops
        ]
    gallery_items = items
    if not shop_filter:
        hidden = {_listing_identity(item) for item in _tclub_exclusive_items(items)}
        mall_ids = set(_shop_ids_for_filter("takaratomymall") or {"takaratomymall"})
        us_ids = set(_shop_ids_for_filter("amazon-us-retail") or {"amazon-us-retail"})
        gallery_items = [
            item
            for item in items
            if str(item.get("shop_id") or "") not in mall_ids
            and str(item.get("shop_id") or "") not in us_ids
            and _listing_identity(item) not in hidden
        ]
    groups = group_listings_by_model(items)
    tag_counts = {"CX": 0, "BX": 0, "UX": 0, "BXG": 0, "kuji": 0, "other": 0}
    in_count = 0
    out_count = 0
    for group in groups:
        tag = group_tag_key(group)
        if tag in tag_counts:
            tag_counts[tag] += 1
        keys = {product_stock_key(item) for item in group.get("items") or []}
        if "in_stock" in keys:
            in_count += 1
        if "out_of_stock" in keys:
            out_count += 1
    shown = _filter_model_groups(groups, stock_filter, tag_filter, sort_filter if tag_filter else "")
    gallery_shown = _filter_model_groups(
        group_listings_by_model(gallery_items),
        stock_filter,
        tag_filter,
        sort_filter if tag_filter else "",
    )
    if _shop_filter_is(shop_filter, "amazon-us-retail"):
        us_groups = _filter_model_groups(
            group_listings_by_model(gallery_items),
            stock_filter,
            "",
            sort_filter,
        )
        cards = _model_block_html(us_groups, layout)
        if cards:
            cards = (
                "<section class='model-section' id='models-amazon-us-retail'>"
                "<h2>美版</h2>%s</section>" % cards
            )
    elif tag_filter:
        cards = _model_block_html(gallery_shown, layout)
    else:
        cards = _model_sections_html(gallery_shown, sort_filter, layout)
    if not shop_filter:
        featured = _featured_shop_sections_html(
            items, stock_filter, tag_filter, sort_filter, layout
        )
        cards = "\n".join(part for part in (cards, featured) if part)
    if not cards:
        cards = "<p>暫時沒有型號</p>"

    def stock_link(kind, text):
        on = " on" if (kind or "") == (stock_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(
                models_href(
                    tag_filter or None,
                    kind or None,
                    sort_filter or None,
                    shop_filter or None,
                    layout=layout,
                ),
                quote=True,
            ),
            text,
        )

    def tag_link(tag, text):
        on = " on" if (tag or "") == (tag_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(
                models_href(
                    tag or None,
                    stock_filter or None,
                    sort_filter or None,
                    shop_filter or None,
                    layout=layout,
                ),
                quote=True,
            ),
            text,
        )

    def sort_link(kind, text):
        on = " on" if (kind or "") == (sort_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(
                models_href(
                    tag_filter or None,
                    stock_filter or None,
                    kind or None,
                    shop_filter or None,
                    layout=layout,
                ),
                quote=True,
            ),
            text,
        )

    line_filters = ""
    if not _shop_filter_is(shop_filter, "amazon-us-retail"):
        line_filters = (
            '<p class="filters">%s %s %s %s %s %s %s</p>'
            % (
                tag_link("", "All"),
                tag_link("CX", "CX [%s]" % tag_counts["CX"]),
                tag_link("BX", "BX [%s]" % tag_counts["BX"]),
                tag_link("UX", "UX [%s]" % tag_counts["UX"]),
                tag_link("BXG", "BX+ [%s]" % tag_counts["BXG"]),
                tag_link("kuji", "一番賞 [%s]" % tag_counts["kuji"]),
                tag_link("other", "other [%s]" % tag_counts["other"]),
            )
        )
    filters = (
        '<p class="filters">%s %s %s</p>'
        '<p class="filters">%s %s</p>'
        "%s"
        % (
            stock_link("", "全部 %s" % len(groups)),
            stock_link("in_stock", "有貨 %s" % in_count),
            stock_link("out_of_stock", "缺貨 %s" % out_count),
            sort_link("", "型號"),
            sort_link("new", "最新發售"),
            line_filters,
        )
    )
    title = "全部現貨 · %s" % SITE_BRAND
    focus = []
    if shop_filter:
        focus.append(str(shop_filter))
    if tag_filter:
        focus.append(str(tag_filter))
    if stock_filter == "in_stock":
        focus.append("有貨")
    elif stock_filter == "out_of_stock":
        focus.append("缺貨")
    desc = "香港爆旋陀螺型號現貨，按 BX、CX、UX 型號列出價錢同舖頭貨況。"
    if focus:
        desc = desc + " 篩選：%s。" % "、".join(focus)
    model_keywords = page_keywords(*(focus + ["爆旋陀螺型號", "BX", "CX", "UX", "香港現貨", "價錢"]))
    indexable = (
        layout != "list"
        and not tag_filter
        and not stock_filter
        and not sort_filter
        and not shop_filter
    )
    shop_grid = models_shop_grid_html(
        shops,
        shop_filter,
        tag_filter,
        stock_filter,
        sort_filter,
        layout=layout,
    )
    view_switch = (
        '<p class="filters">'
        '<a class="filter%s" href="/product">圖庫</a> '
        '<a class="filter%s" href="/shop/all?stock=in">列表</a>'
        "</p>"
        % ("" if layout == "list" else " on", " on" if layout == "list" else "")
    )
    index_ld = None
    if indexable:
        index_ld = models_index_json_ld(shown, title, desc)
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">全部現貨</h1>
<section class="panel" data-item-list-id="models" data-item-list-name="全部現貨">
<div class="model-filters">
%s
%s
%s
</div>
<p class="kicker">%s models</p>
%s
%s
</section>
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            "/shop/all" if layout == "list" else "/product",
            indexable=indexable,
            keywords=model_keywords,
            json_ld=index_ld,
        ),
        page_theme_css(),
        site_nav_html(),
        shop_grid,
        view_switch,
        filters,
        html.escape(str(len(shown))),
        cards,
        model_modal_html(),
        install_hint_block(),
    )


def threads_subscribe_desc_html(shops_href="/shops"):
    return (
        "香港爆旋陀螺到貨通知。"
        '<a href="%s">Online舖頭</a> '
        "有新品、補貨、缺貨就出帖。非官方。"
    ) % html.escape(shops_href or "/shops", quote=True)


def subscribe_widget_html(label, button_class="", extra_class="", widget_id="subscribe"):
    wrap = "subscribe"
    if extra_class:
        wrap += " " + extra_class
    btn_class = (' class="%s"' % html.escape(button_class, quote=True)) if button_class else ""
    menu_id = html.escape(widget_id + "-menu", quote=True)
    btn_id = html.escape(widget_id + "-btn", quote=True)
    list_id = html.escape(widget_id + "-list", quote=True)
    markup = (
        '<div class="%s" id="%s">'
        '<button type="button" id="%s"%s aria-expanded="false" aria-controls="%s">%s</button>'
        '<div class="subscribe-list" id="%s" hidden>'
        '<p class="subscribe-kicker">%s</p>'
        '<a class="subscribe-method" data-method="Telegram" href="%s" target="_blank" rel="noopener">'
        '<span class="subscribe-name">Telegram</span>'
        '<span class="subscribe-hint">加入群組 · 有貨即時通知</span></a>'
        '<a class="subscribe-method" data-method="Discord" href="%s" target="_blank" rel="noopener">'
        '<span class="subscribe-name">Discord</span>'
        '<span class="subscribe-hint">加入頻道 · 有貨即時通知</span></a>'
        '<a class="subscribe-method" data-method="Threads" href="%s" target="_blank" rel="noopener">'
        '<span class="subscribe-name">Threads</span>'
        '<span class="subscribe-hint">%s</span></a>'
        "</div></div>"
    )
    return markup % (
        html.escape(wrap, quote=True),
        menu_id,
        btn_id,
        btn_class,
        list_id,
        label,
        list_id,
        threads_subscribe_desc_html(),
        outbound_href(TELEGRAM_INVITE_URL),
        outbound_href(DISCORD_INVITE_URL),
        outbound_href(THREADS_PROFILE_URL),
        html.escape(THREADS_SUBSCRIBE_HINT),
    )


def go_visitor_redirect_script(dest):
    """Leave in-app browsers for the system browser, then open the shop."""
    return """<script>
(function(){
  var dest=%s;
  var gone=false;
  function inApp(){
    var ua=navigator.userAgent||"";
    return /Telegram|Instagram|FBAN|FBAV|FB_IAB|Barcelona|Threads|Line\\/|MicroMessenger|Bytedance|musical_ly|TikTok|Twitter|Discord/i.test(ua);
  }
  function outside(url){
    if(!inApp()) return url;
    var ua=navigator.userAgent||"";
    if(/iPhone|iPad|iPod/i.test(ua) && /^https:\\/\\//i.test(url)) return "x-safari-"+url;
    if(/Android/i.test(ua) && /^https?:\\/\\//i.test(url)){
      var scheme=url.slice(0, url.indexOf(":"));
      var bare=url.replace(/^https?:\\/\\//i, "");
      return "intent://"+bare+"#Intent;scheme="+scheme+";action=android.intent.action.VIEW;S.browser_fallback_url="+encodeURIComponent(url)+";end";
    }
    return url;
  }
  function go(){
    if(gone||!dest)return;
    gone=true;
    var next=outside(dest);
    if(next===dest){
      location.replace(dest);
      return;
    }
    location.replace(next);
  }
  var link=document.querySelector(".go-loading a");
  if(link){
    link.addEventListener("click", function(event){
      if(!dest)return;
      event.preventDefault();
      go();
    });
  }
  if(window.gtag){
    gtag('config','G-19VVZP9R25',{transport_type:'beacon',send_page_view:false});
    gtag('event','page_view',{transport_type:'beacon'});
  }
  setTimeout(go, 500);
})();
</script>""" % json.dumps(str(dest or ""))


def render_go_bounce_html(target, shop_id, sku, page_url=None):
    target = target or {}
    dest = str(target.get("dest") or "")
    title = str(target.get("title") or SITE_BRAND)
    og_image = str(target.get("og_image") or seo_image_url())
    dest_attr = html.escape(dest, quote=True)
    desc = product_seo_description(target, THREADS_SUBSCRIBE_DESC)
    go_keywords = page_keywords(title, shop_id, sku, "爆旋陀螺 X", "香港現貨")
    if desc == home_seo_description():
        go_keywords = SITE_META_KEYWORDS
    og_w, og_h = (
        (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT)
        if OG_IMAGE_PATH in og_image
        else (None, None)
    )
    return """<!DOCTYPE html>
<html lang="zh-Hant" prefix="og: https://ogp.me/ns#">
<head>
%s
<link rel="preconnect" href="https://www.googletagmanager.com">
<link rel="preconnect" href="https://www.google-analytics.com">
<style>
body{margin:0;min-height:100vh;background:#1a1aff;color:#fff;font-family:Inter,system-ui,sans-serif}
.slash{position:fixed;right:0;top:12%%;width:120px;height:70%%;pointer-events:none;
background:repeating-linear-gradient(-32deg,transparent,transparent 10px,#fff 10px,#fff 11px);opacity:.35}
.go-loading{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;position:relative;z-index:1}
.go-loading svg{width:56px;height:56px}
.go-loading p{margin:0;font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.12em;text-transform:uppercase}
.go-loading a{color:#fff}
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="go-loading">
<svg viewBox="0 0 56 56" aria-hidden="true">
<circle cx="28" cy="28" r="18" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="4"/>
<circle cx="28" cy="28" r="18" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-dasharray="28 86">
<animateTransform attributeName="transform" type="rotate" from="0 28 28" to="360 28 28" dur="0.7s" repeatCount="indefinite"/>
</circle>
</svg>
<p><a href="%s">前往商店</a></p>
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            go_path(shop_id, sku),
            indexable=True,
            canonical_url=page_url or go_canonical_url(shop_id, sku),
            image_url=og_image,
            image_width=og_w,
            image_height=og_h,
            keywords=go_keywords,
        ),
        dest_attr,
        go_visitor_redirect_script(dest),
    )


def render_go_html(target, shop_id, sku, page_url=None, auto_redirect=False):
    target = target or {}
    dest = str(target.get("dest") or "")
    title = str(target.get("title") or SITE_BRAND)
    image = str(target.get("image") or seo_image_url())
    og_image = str(target.get("og_image") or seo_image_url())
    desc = product_seo_description(target, THREADS_SUBSCRIBE_DESC)
    go_keywords = page_keywords(title, shop_id, sku, "爆旋陀螺 X", "香港現貨")
    if desc == home_seo_description():
        go_keywords = SITE_META_KEYWORDS
    dest_attr = html.escape(dest, quote=True)
    og_w, og_h = (
        (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT)
        if OG_IMAGE_PATH in og_image
        else (None, None)
    )
    card = product_card_html(
        {
            "title": title,
            "url": dest,
            "image": image,
            "image_path": target.get("image_path") or "",
            "price": target.get("price") or "",
            "status_label": target.get("status") or "",
        }
    )
    return """<!DOCTYPE html>
<html lang="zh-Hant" prefix="og: https://ogp.me/ns#">
<head>
%s
<style>
%s
.go-card{max-width:520px;margin:48px auto 0}
.go-actions{display:flex;flex-direction:column;gap:8px;margin:20px 0 8px}
.go-actions a,.go-actions button{text-decoration:none!important}
.go-store{background:var(--ink);color:#fff!important;text-align:center;padding:12px 16px;
font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.12em;text-transform:uppercase;
border:0;cursor:pointer;width:100%%;display:block}
.go-note{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.04em;color:#555;line-height:1.6}
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<section class="panel go-card">
%s
<p>%s</p>
<p class="go-note">%s</p>
<div class="go-actions">
<a class="subscribe-method" data-method="Threads" href="%s" target="_blank" rel="noopener">
<span class="subscribe-name">Threads</span>
<span class="subscribe-hint">%s</span></a>
<a class="subscribe-method" data-method="Telegram" href="%s" target="_blank" rel="noopener">
<span class="subscribe-name">Telegram</span>
<span class="subscribe-hint">加入群組 · 有貨即時通知</span></a>
<a class="subscribe-method" data-method="Discord" href="%s" target="_blank" rel="noopener">
<span class="subscribe-name">Discord</span>
<span class="subscribe-hint">加入頻道 · 有貨即時通知</span></a>
<a class="go-store" href="%s">前往商店</a>
</div>
</section>
</div>
%s
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            go_path(shop_id, sku),
            indexable=True,
            canonical_url=page_url or go_canonical_url(shop_id, sku),
            image_url=og_image,
            image_width=og_w,
            image_height=og_h,
            keywords=go_keywords,
        ),
        page_theme_css(),
        site_nav_html(),
        card,
        threads_subscribe_desc_html(),
        html.escape(THREADS_SUBSCRIBE_HINT),
        outbound_href(THREADS_PROFILE_URL),
        html.escape(THREADS_SUBSCRIBE_HINT),
        outbound_href(TELEGRAM_INVITE_URL),
        outbound_href(DISCORD_INVITE_URL),
        dest_attr,
        ga_events_script()
        + (go_visitor_redirect_script(dest) if auto_redirect else ""),
    )


def subscribe_script():
    return (
        "<script>"
        "(function(){"
        'var menus=document.querySelectorAll(".subscribe");'
        "function closeAll(){"
        "menus.forEach(function(menu){"
        'var btn=menu.querySelector("button");'
        'var list=menu.querySelector(".subscribe-list");'
        'menu.classList.remove("open");'
        'if(btn)btn.setAttribute("aria-expanded","false");'
        'if(list)list.setAttribute("hidden","");'
        "});"
        "}"
        "menus.forEach(function(menu){"
        'var btn=menu.querySelector("button");'
        'var list=menu.querySelector(".subscribe-list");'
        "if(!btn||!list)return;"
        "btn.onclick=function(e){"
        "e.stopPropagation();"
        'var open=!menu.classList.contains("open");'
        "closeAll();"
        "if(open){"
        'menu.classList.add("open");'
        'btn.setAttribute("aria-expanded","true");'
        'list.removeAttribute("hidden");'
        "}"
        "};"
        'list.addEventListener("click",function(e){e.stopPropagation();});'
        "});"
        'document.addEventListener("click",closeAll);'
        "})();"
        "</script>"
    )


def filter_combo_script():
    return (
        "<script>"
        "(function(){"
        'var combos=document.querySelectorAll(".filter-combo");'
        "function closeAll(except){"
        "combos.forEach(function(box){"
        "if(box===except)return;"
        'var list=box.querySelector(".filter-combo-list");'
        'if(list)list.setAttribute("hidden","");'
        "});"
        "}"
        "combos.forEach(function(box){"
        'var input=box.querySelector(".filter-combo-input");'
        'var list=box.querySelector(".filter-combo-list");'
        'var arrow=box.querySelector(".filter-combo-arrow");'
        "if(!input||!list)return;"
        'var links=[].slice.call(list.querySelectorAll("a"));'
        "function openList(){closeAll(box);list.removeAttribute('hidden');}"
        "function applyFilter(){"
        "var q=(input.value||'').toLowerCase();"
        "links.forEach(function(a){"
        "var label=(a.getAttribute('data-label')||a.textContent||'').toLowerCase();"
        "a.hidden=!!q && label.indexOf(q)<0;"
        "});"
        "}"
        "input.addEventListener('focus',function(){input.select();openList();});"
        "input.addEventListener('input',function(){openList();applyFilter();});"
        "if(arrow){"
        "arrow.addEventListener('click',function(e){"
        "e.preventDefault();e.stopPropagation();"
        "if(list.hasAttribute('hidden')){openList();input.focus();}"
        "else{list.setAttribute('hidden','');}"
        "});"
        "}"
        "input.addEventListener('keydown',function(e){"
        "if(e.key==='Enter'){"
        "e.preventDefault();"
        "var vis=links.filter(function(a){return !a.hidden;})[0];"
        "if(vis) location.href=vis.getAttribute('href');"
        "}"
        "});"
        "});"
        "document.addEventListener('click',function(e){"
        "if(!e.target.closest || !e.target.closest('.filter-combo')) closeAll();"
        "});"
        "})();"
        "</script>"
    )


def nav_drawer_script():
    return (
        "<script>"
        "(function(){"
        'var btn=document.getElementById("site-nav-menu-btn");'
        'var drawer=document.getElementById("site-nav-drawer");'
        'var backdrop=document.getElementById("site-nav-backdrop");'
        'var closeBtn=document.getElementById("site-nav-close");'
        "if(!btn||!drawer||!backdrop)return;"
        "var closeTimer=null;"
        "function setOpen(open){"
        "if(closeTimer){clearTimeout(closeTimer);closeTimer=null;}"
        "if(open){"
        'drawer.removeAttribute("hidden");backdrop.removeAttribute("hidden");'
        "requestAnimationFrame(function(){"
        'drawer.classList.add("is-open");backdrop.classList.add("is-open");'
        "});"
        'btn.setAttribute("aria-expanded","true");'
        'btn.classList.add("is-open");'
        'document.body.classList.add("nav-open");'
        'var links=drawer.querySelectorAll(".nav-drawer-links a");'
        "for(var i=0;i<links.length;i++){"
        'links[i].classList.toggle("is-active", links[i].getAttribute("href")===location.pathname'
        '|| links[i].pathname===location.pathname);'
        "}"
        "}else{"
        'drawer.classList.remove("is-open");backdrop.classList.remove("is-open");'
        'btn.setAttribute("aria-expanded","false");'
        'btn.classList.remove("is-open");'
        'document.body.classList.remove("nav-open");'
        "closeTimer=setTimeout(function(){"
        'drawer.setAttribute("hidden","");backdrop.setAttribute("hidden","");'
        "closeTimer=null;},260);"
        "}"
        "}"
        'btn.addEventListener("click",function(e){e.stopPropagation();'
        'setOpen(btn.getAttribute("aria-expanded")!=="true");});'
        'backdrop.addEventListener("click",function(){setOpen(false);});'
        'if(closeBtn)closeBtn.addEventListener("click",function(){setOpen(false);});'
        'document.addEventListener("keydown",function(e){'
        'if(e.key==="Escape")setOpen(false);});'
        "})();"
        "</script>"
    )


def site_nav_html(subscribe=True):
    extra = subscribe_widget_html(SUBSCRIBE_BUTTON_LABEL) if subscribe else ""
    drawer_subscribe = (
        subscribe_widget_html(
            SUBSCRIBE_BUTTON_LABEL,
            extra_class="subscribe-drawer",
            widget_id="subscribe-drawer",
        )
        if subscribe
        else ""
    )
    in_stock_href = "/shop/all?stock=in"
    return (
        '<nav class="site-nav">'
        '<div class="nav-start">'
        '<button type="button" class="menu-btn" id="site-nav-menu-btn"'
        ' aria-label="開啟選單" aria-expanded="false" aria-controls="site-nav-drawer">'
        '<span class="menu-icon" aria-hidden="true"><span></span><span></span><span></span></span>'
        "</button>"
        "%s"
        "</div>"
        '<div class="nav-end">%s</div></nav>'
        '<button type="button" class="nav-backdrop" id="site-nav-backdrop" hidden aria-label="關閉選單"></button>'
        '<aside class="nav-drawer" id="site-nav-drawer" hidden aria-label="選單">'
        '<div class="nav-drawer-head">'
        '<a class="nav-drawer-brand" href="/">'
        '<img class="nav-drawer-brand-mark" src="%s" alt="">'
        '<span class="nav-drawer-brand-name">%s</span></a>'
        '<button type="button" class="nav-drawer-close" id="site-nav-close" aria-label="關閉">×</button>'
        "</div>"
        '<nav class="nav-drawer-links">'
        '<a href="/shops">店舖現況</a>'
        '<a href="/product">全部現貨</a>'
        '<a href="%s">列表</a>'
        '<a href="/history">最新通知</a>'
        "</nav>"
        '<div class="nav-drawer-subscribe">%s</div>'
        "</aside>"
    ) % (
        brand_link_html(),
        extra,
        html.escape(cdn_image_url(LOGO_PATH), quote=True),
        html.escape(SITE_BRAND),
        in_stock_href,
        drawer_subscribe,
    )


def filter_options_html(items, wrap_class="filters", combo_label="", force_combo=False, empty_label="All"):
    items = list(items or [])
    heading = ""
    if combo_label:
        heading = '<p class="filter-store-label">%s</p>' % html.escape(combo_label)
    if not force_combo and len(items) <= FILTER_COMBO_THRESHOLD:
        body = '<p class="%s">%s</p>' % (
            html.escape(wrap_class, quote=True),
            " ".join(
                '<a class="filter%s" href="%s">%s</a>'
                % (
                    " on" if selected else "",
                    html.escape(href, quote=True),
                    html.escape(str(label)),
                )
                for href, label, selected in items
            ),
        )
        if not combo_label:
            return body
        return '<div class="filter-store">%s%s</div>' % (heading, body)
    current_label = empty_label
    for href, label, selected in items:
        if selected:
            current_label = str(label)
            break
    options = "".join(
        '<a class="filter%s" href="%s" data-label="%s">%s</a>'
        % (
            " on" if selected else "",
            html.escape(href, quote=True),
            html.escape(str(label), quote=True),
            html.escape(str(label)),
        )
        for href, label, selected in items
    )
    aria = html.escape(combo_label or empty_label or "Filter", quote=True)
    combo = (
        '<div class="filter-combo %s">'
        '<div class="filter-combo-field">'
        '<input type="search" class="filter-combo-input" placeholder="%s" value="%s"'
        ' autocomplete="off" spellcheck="false" aria-label="%s">'
        '<button type="button" class="filter-combo-arrow" tabindex="-1" aria-label="%s">▾</button>'
        '<div class="filter-combo-list" hidden>%s</div></div></div>'
    ) % (
        html.escape(wrap_class, quote=True),
        html.escape(empty_label, quote=True),
        html.escape(current_label, quote=True),
        aria,
        aria,
        options,
    )
    if not combo_label:
        return combo
    return '<div class="filter-store">%s%s</div>' % (heading, combo)


def _shop_chip_items(shops, current_id, include_all=False):
    items = []
    if include_all:
        items.append((shop_products_href("all"), "All", current_id == "all"))
    for shop in shops or []:
        shop_id = str(shop.get("id") or "")
        items.append(
            (
                shop_products_href(shop_id),
                str(shop.get("label") or shop_id or "Shop"),
                bool(shop_id and shop_id == current_id),
            )
        )
    return items


def shop_chips_html(shops, current_id=""):
    current = str(current_id or "")
    hk = []
    overseas = []
    for shop in shops or []:
        if shop_is_overseas(shop):
            overseas.append(shop)
        else:
            hk.append(shop)
    blocks = []
    if hk:
        blocks.append(
            filter_options_html(
                _shop_chip_items(hk, current, include_all=True),
                wrap_class="shop-chips",
                combo_label="Store",
            )
        )
    if overseas:
        blocks.append(
            filter_options_html(
                _shop_chip_items(overseas, current, include_all=not hk),
                wrap_class="shop-chips shop-chips-overseas",
                combo_label="海外店舖",
            )
        )
    if not blocks:
        blocks.append(
            filter_options_html(
                _shop_chip_items([], current, include_all=True),
                wrap_class="shop-chips",
                combo_label="Store",
            )
        )
    return "".join(blocks)


def render_products_html(shop, items, key_query="", stock_filter="", tag_filter="", shops=None):
    shop = shop or {}
    if shops is None:
        shops = [shop]
    chips = shop_chips_html(shops, shop.get("id") or "")
    label = html.escape(str(shop.get("label") or shop.get("id") or "Shop"))
    us_shop = _shop_filter_is(shop.get("id") or "", "amazon-us-retail")
    shown = filter_shop_products(items, stock_filter, "" if us_shop else tag_filter)

    def shop_row(item):
        row = dict(item)
        if shop.get("label") and not row.get("shop_label"):
            row["shop_label"] = shop.get("label")
        if us_shop and not row.get("shop_id"):
            row["shop_id"] = shop.get("id") or ""
        return product_card_html(row, shop.get("id") or "")

    if us_shop:
        cards = "\n".join(shop_row(item) for item in shown) or "<p>這個商店暫時沒有商品</p>"
    elif tag_filter or not shown:
        cards = "\n".join(shop_row(item) for item in shown) or "<p>這個商店暫時沒有商品</p>"
    else:
        buckets = _tagged_buckets(shown, product_tag_key)
        parts = []
        main = []
        for tag in ("CX", "BX", "UX"):
            main.extend(buckets[tag])
        if main:
            parts.append("\n".join(shop_row(item) for item in main))
        for tag, label in (("kuji", "一番賞"), ("other", "other")):
            block = "\n".join(shop_row(item) for item in buckets[tag])
            if block:
                parts.append("<h2 class='list-section' id='shop-%s'>%s</h2>\n%s" % (tag, html.escape(label), block))
        cards = "\n".join(parts) or "<p>這個商店暫時沒有商品</p>"
    shop_id = shop.get("id") or ""
    in_count = sum(1 for item in (items or []) if product_stock_key(item) == "in_stock")
    out_count = sum(1 for item in (items or []) if product_stock_key(item) == "out_of_stock")
    tag_counts = {"CX": 0, "BX": 0, "UX": 0, "kuji": 0, "other": 0}
    for item in items or []:
        tag = product_tag_key(item)
        if tag in tag_counts:
            tag_counts[tag] += 1

    def filter_link(kind, text):
        on = " on" if (kind or "") == (stock_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(shop_products_href(shop_id, kind or None, tag_filter or None), quote=True),
            text,
        )

    def tag_link(tag, text):
        on = " on" if tag == (tag_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(shop_products_href(shop_id, stock_filter or None, tag or None), quote=True),
            text,
        )

    line_filters = ""
    if not us_shop:
        line_filters = (
            '<p class="filters">%s %s %s %s %s %s</p>'
            % (
                tag_link("", "All"),
                tag_link("CX", "CX [%s]" % tag_counts["CX"]),
                tag_link("BX", "BX [%s]" % tag_counts["BX"]),
                tag_link("UX", "UX [%s]" % tag_counts["UX"]),
                tag_link("kuji", "一番賞 [%s]" % tag_counts["kuji"]),
                tag_link("other", "other [%s]" % tag_counts["other"]),
            )
        )
    filters = (
        '<p class="filters">%s %s %s</p>'
        "%s"
        % (
            filter_link("", "全部 %s" % len(items or [])),
            filter_link("in_stock", "有貨 %s" % in_count),
            filter_link("out_of_stock", "缺貨 %s" % out_count),
            line_filters,
        )
    )
    indexable = not stock_filter and not tag_filter
    seo_title, seo_desc = shop_page_seo(shop, items, indexable=indexable)
    shop_keywords = page_keywords(
        shop.get("label") or shop.get("id"),
        stock_filter,
        tag_filter,
        "爆旋陀螺庫存",
        "有貨",
        "缺貨",
        "爆旋陀螺開訂",
    )
    shop_path = shop_products_href(shop_id)
    list_id = html.escape(str(shop_id), quote=True)
    list_name = html.escape(str(shop.get("label") or shop.get("id") or "Shop"), quote=True)
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">%s</h1>
%s
<section class="panel" data-item-list-id="%s" data-item-list-name="%s">
%s
<p class="kicker">%s items</p>
%s
</section>
</div>
%s
</body>
</html>
""" % (
        page_seo_head(seo_title, seo_desc, shop_path, indexable=indexable, keywords=shop_keywords),
        page_theme_css(),
        site_nav_html(),
        label,
        chips,
        list_id,
        list_name,
        filters,
        html.escape(str(len(shown))),
        cards,
        install_hint_block(),
    )


def render_admin_login_html(error=False):
    title = "Admin login"
    desc = "Admin login for Beyblade watch notify tools."
    err = (
        '<p class="gate-error">用戶名稱或密碼不正確</p>' if error else ""
    )
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
<nav class="site-nav">
<a class="brand" href="%s"><img class="brand-mark" src="%s" alt="%s"><span class="brand-name">%s</span></a>
</nav>
<h1 class="page-title">Admin</h1>
<section class="panel">
<h2>登入</h2>
%s
<form class="gate-form" method="post" action="/login">
<input type="text" name="username" autocomplete="username" required>
<input type="password" name="password" autocomplete="current-password" required>
<button type="submit">登入</button>
</form>
</section>
</div>
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            "/login",
            indexable=False,
            keywords=page_keywords("admin login", "HK BeybladeX Watch"),
        ),
        page_theme_css(),
        html.escape(SITE_ORIGIN, quote=True),
        html.escape(cdn_image_url(LOGO_PATH), quote=True),
        html.escape(SITE_BRAND, quote=True),
        html.escape(SITE_BRAND),
        err,
    )


def render_notify_test_html():
    title = "Notify"
    desc = "Send a message to Discord, Telegram, and Threads."
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
<nav class="site-nav">
<a class="brand" href="%s"><img class="brand-mark" src="%s" alt="%s"><span class="brand-name">%s</span></a>
</nav>
<h1 class="page-title">Notify</h1>
<section class="panel">
<h2>發送通知</h2>
<textarea id="notify-message" class="notify-message" maxlength="2000"></textarea>
<div class="notify-send">
<div class="subscribe" id="notify-actions-menu">
<button type="button" id="notify-actions-btn" aria-expanded="false" aria-controls="notify-actions-list">Actions</button>
<div class="subscribe-list" id="notify-actions-list" hidden>
<button type="button" class="subscribe-method" id="notify-send-all"><span class="subscribe-name">Send all</span></button>
<button type="button" class="subscribe-method" id="discord-test-btn"><span class="subscribe-name">Discord</span></button>
<button type="button" class="subscribe-method" id="telegram-test-btn"><span class="subscribe-name">Telegram</span></button>
<button type="button" class="subscribe-method" id="threads-test-btn"><span class="subscribe-name">Threads</span></button>
</div>
</div>
</div>
<p class="kicker" id="notify-result"></p>
</section>
</div>
%s
<script>
(function(){
  var result = document.getElementById("notify-result");
  var box = document.getElementById("notify-message");
  function postNotify(channel){
    var message = (box && box.value) || "";
    return fetch("/notify-test", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({channel: channel, message: message})
    }).then(function(r){
      return r.json().then(function(j){ return {ok: r.ok, j: j}; });
    });
  }
  function showMsg(text){
    if (result) result.textContent = text || "";
  }
  function sendChannel(channel){
    postNotify(channel).then(function(res){
      showMsg((res.j && res.j.message) || (res.ok ? "Sent" : "Failed"));
    }).catch(function(){ showMsg("Failed to send"); });
  }
  var all = document.getElementById("notify-send-all");
  if (all) all.onclick = function(){ sendChannel("all"); };
  var dbtn = document.getElementById("discord-test-btn");
  if (dbtn) dbtn.onclick = function(){ sendChannel("discord"); };
  var tbtn = document.getElementById("telegram-test-btn");
  if (tbtn) tbtn.onclick = function(){ sendChannel("telegram"); };
  var thbtn = document.getElementById("threads-test-btn");
  if (thbtn) thbtn.onclick = function(){ sendChannel("threads"); };
})();
</script>
</body>
</html>
""" % (
        page_seo_head(
            title,
            desc,
            "/notify-test",
            indexable=False,
            keywords=page_keywords("notify test", "Discord", "Telegram", "Threads"),
        ),
        page_theme_css(),
        html.escape(SITE_ORIGIN, quote=True),
        html.escape(cdn_image_url(LOGO_PATH), quote=True),
        html.escape(SITE_BRAND, quote=True),
        html.escape(SITE_BRAND),
        subscribe_script(),
    )


def bundle_items_html(item):
    rows = []
    for line in item_bundle_lines(item):
        name = html.escape(str(line.get("name") or ""))
        price = str(line.get("price") or "").strip()
        price_html = (
            " <span class='bundle-price'>HK$%s</span>" % html.escape(price) if price else ""
        )
        rows.append("<li>%s%s</li>" % (name, price_html))
    if not rows:
        return ""
    return "<ul class='bundle-items'>%s</ul>" % "".join(rows)


def notify_rows_html(rows, today=None):
    if not rows:
        return "<p>尚未有通知。</p>"
    today = today or datetime.now(HKT_TZ).date()
    parts = []
    last_day = object()
    for row in rows:
        day = notify_at_date(row)
        if day != last_day:
            last_day = day
            heading = notify_day_label(day, today)
            if heading:
                parts.append('<p class="notify-day">%s</p>' % html.escape(heading))
        item = history_row_for_display(row)
        kind = NOTIFY_EVENT_LABELS.get(item.get("event"), str(item.get("event") or ""))
        title = html.escape(str(item.get("title") or item.get("sku") or ""))
        url = item.get("url") or ""
        if url:
            name = "<a href='%s' target='_blank' rel='noopener'>%s</a>" % (
                outbound_href(url),
                title,
            )
        else:
            name = title
        price = shown_price_text(item)
        meta = " · ".join(
            part
            for part in (
                html.escape(str(item.get("shop") or "")),
                html.escape(kind),
                html.escape(str(item.get("model") or "")),
                html.escape(price) if price else "",
                html.escape(str(item.get("change") or "")),
                html.escape(str(item.get("at") or "")),
            )
            if part
        )
        parts.append(
            "<article class='notify-row'>"
            "%s<div class='meta'><div class='name'>%s</div>%s<div class='sub'>%s</div></div></article>"
            % (product_thumb_html(item), name, bundle_items_html(item), meta)
        )
    return "".join(parts)


