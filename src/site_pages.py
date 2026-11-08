#!/usr/bin/env python3
"""HTML/CSS/JS page renderers for the Beyblade HK status site."""
from __future__ import print_function

import html
import json
import os
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
    filter_index_notifies,
    filter_notifies_by_src,
    filter_notify_history,
    filter_shops_by_notify_src,
    filter_shop_products,
    find_source_by_id,
    group_listings_by_model,
    group_tag_key,
    listing_price_value,
    listing_rank,
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
    shop_products_href,
    stock_status,
    status_text,
)

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
.notify-day{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
margin:16px 0 4px;padding:4px 0;border-bottom:1px solid #d8d8f0}
.product-card{display:flex;gap:14px;align-items:center;padding:14px 0;border-bottom:1px solid #d8d8f0}
.product-card:last-child{border-bottom:0}
.thumb,.thumb-empty{width:96px;height:96px;object-fit:cover;flex:0 0 96px;background:#ececf8}
.meta{flex:1;min-width:0}
.name{font-size:15px;line-height:1.35;margin:0 0 6px}
.sub{font-family:"IBM Plex Mono",monospace;font-size:12px;color:#555;word-break:break-all}
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
.model-grid .product-card{display:flex;flex-direction:column;align-items:stretch;gap:0;padding:0;border:0;border-bottom:0;background:transparent}
.model-grid .catalog-card{position:relative;background:#fff;color:var(--ink);border:1px solid #e4e4f4;border-radius:8px;overflow:hidden;min-width:0;
transition:transform .15s ease,border-color .15s ease,box-shadow .15s ease}
.model-grid .catalog-card:hover{transform:translateY(-2px);border-color:var(--blue);box-shadow:0 8px 18px rgba(26,26,255,.12)}
.model-grid .catalog-card__hit{display:flex;flex-direction:column;width:100%;margin:0;padding:0;border:0;background:transparent;
color:inherit;font:inherit;text-align:inherit;cursor:pointer}
.model-grid .catalog-card__image{aspect-ratio:1;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;
background:radial-gradient(circle at 50% 40%,#fff 0%,#f4f6fb 58%,#e7edf6 100%)}
.model-grid .catalog-card__image img{width:100%;height:100%;object-fit:cover;display:block}
.model-grid .catalog-card__placeholder{font-family:"IBM Plex Mono",monospace;font-size:13px;color:#8a8aaa}
.model-grid .catalog-card__badge{position:absolute;top:6px;right:6px;z-index:1;background:var(--blue);color:#fff;
font-family:"IBM Plex Mono",monospace;font-size:8px;letter-spacing:.06em;padding:2px 5px;border-radius:999px}
.model-grid .catalog-card__badge--out{background:#6a6a88}
.model-grid .catalog-card__badge .stock-in,.model-grid .catalog-card__badge .stock-out{color:#fff}
.model-grid .catalog-card__body{display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 8px 8px;text-align:center}
.model-grid .catalog-card__id{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.06em;color:#6a6a88}
.model-grid .catalog-card__name{margin:0;font-family:Inter,system-ui,sans-serif;font-size:11px;font-weight:600;line-height:1.3;color:#0a0a2a;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}
.model-grid .catalog-card__subtitle{margin:0;font-family:"IBM Plex Mono",monospace;font-size:10px;line-height:1.3;color:var(--blue)}
.model-offer .stock-in{color:var(--blue)}
.model-offer .stock-out{color:#888}
.model-offer-list[hidden]{display:none}
.model-offer{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #ececf4}
.model-offer:last-child{border-bottom:0}
.model-offer .thumb,.model-offer .thumb-empty{width:52px;height:52px;flex:0 0 52px;object-fit:cover;background:#f4f6fb}
.model-offer .name{font-size:13px;line-height:1.35;margin:0 0 4px}
.model-offer .name a{color:var(--ink);text-decoration:none}
.model-offer .sub{font-size:11px;color:#555}
body.model-open{overflow:hidden}
.model-modal[hidden]{display:none}
.model-modal{position:fixed;inset:0;z-index:40;display:flex;align-items:flex-end;justify-content:center}
.model-modal__backdrop{position:absolute;inset:0;border:0;padding:0;background:rgba(10,10,42,.55);cursor:pointer}
.model-modal__panel{position:relative;z-index:1;width:100%;max-height:min(82vh,720px);overflow:auto;background:#fff;color:var(--ink);
border-radius:12px 12px 0 0;padding:14px 16px 20px;box-shadow:0 -12px 32px rgba(10,10,42,.2)}
.model-modal__head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 4px}
.model-modal__title{margin:0;font-family:"IBM Plex Mono",monospace;font-size:14px;letter-spacing:.04em}
.model-modal__close{width:32px;height:32px;border:0;background:transparent;color:var(--ink);font-size:24px;line-height:1;cursor:pointer}
@media(min-width:700px){
.model-modal{align-items:center;padding:24px}
.model-modal__panel{width:min(520px,100%);border-radius:12px}
}
@media(min-width:640px){.model-grid{grid-template-columns:repeat(5,minmax(0,1fr))}}
@media(min-width:960px){.model-grid{grid-template-columns:repeat(6,minmax(0,1fr))}}
@media(min-width:1200px){.model-grid{grid-template-columns:repeat(8,minmax(0,1fr))}}
""".strip()


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
    ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": str(title or ""),
            "description": str(description or ""),
            "url": page_url,
            "image": img_src,
        },
        ensure_ascii=False,
    )
    return """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<meta name="robots" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="website">
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
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-19VVZP9R25');
</script>
""".strip() % (
        t,
        d,
        robots,
        canon,
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


def robots_txt():
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Sitemap: %s/sitemap.xml" % SITE_ORIGIN,
            "",
        ]
    )


def sitemap_xml(cfg=None):
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
        "/models",
        "/catalog",
        "/parts",
        "/collection",
        SUBSCRIBE_PATH,
        PRIVACY_PATH,
        TERMS_PATH,
        shop_products_href("all"),
    ]
    urls = []
    seen = set()
    for path in paths:
        url = page_canonical(path)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    for shop in shop_chip_shops(cfg):
        shop_id = shop.get("id")
        if not shop_id:
            continue
        url = page_canonical(shop_products_href(shop_id))
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
    href = shop_products_href(shop.get("id"))
    name_cell = "<a href='%s'>%s</a>" % (
        html.escape(href, quote=True),
        html.escape(str(shop.get("label") or "")),
    )
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


def status_shop_table_body(payload, cfg=None, show_updated=False):
    payload = payload or {}
    rows = [
        status_shop_row_html(shop, show_updated=show_updated)
        for shop in display_status_shops(payload.get("shops") or [], cfg)
    ]
    colspan = "6" if show_updated else "5"
    return "\n".join(rows) or ("<tr><td colspan='%s'>沒有商店資料</td></tr>" % colspan)


def status_shops_section_html(payload, cfg=None, title_html=None, show_updated=False):
    payload = payload or {}
    ok = bool(payload.get("ok"))
    if show_updated and not ok:
        health = "<span class='bad'>異常</span>"
    else:
        health = "正常"
    if title_html is None:
        title_html = '<h2><a href="/shops">店舖現況</a></h2>'
    heading = ("%s\n" % title_html) if title_html else ""
    updated_stat = ""
    updated_head = ""
    if show_updated:
        updated_stat = "<span>更新 %s HKT</span>" % html.escape(
            str(payload.get("checked_at") or "—")
        )
        updated_head = "<th>最後更新時間</th>"
    return """<section class="panel">
%s<div class="stats">
<span>整體 <strong>%s</strong></span>
%s
</div>
<table>
<thead><tr><th>商店</th><th>狀態</th><th>SKU</th><th>有貨</th><th>缺貨</th>%s</tr></thead>
<tbody>
%s
</tbody>
</table>
</section>
""" % (
        heading,
        health,
        updated_stat,
        updated_head,
        status_shop_table_body(payload, cfg, show_updated=show_updated),
    )


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
        page_seo_head(title, desc, OG_HOME_PATH, indexable=True),
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
        page_seo_head(title, desc, OG_HOME_PATH, indexable=True),
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
    desc = THREADS_SUBSCRIBE_DESC
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
        ),
        page_theme_css(),
        site_nav_html(),
        status_shops_section_html(payload, cfg, title_html="", show_updated=show_updated),
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


def render_coffee_html():
    title = "請我飲杯咖啡 · %s" % SITE_BRAND
    desc = "呢個係完全免費嘅香港爆旋陀螺到貨通知專案。伺服器同開發都有成本，請我飲杯咖啡可以幫我繼續做落去。"
    payme = html.escape(PAYME_URL, quote=True)
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
        page_seo_head(title, desc, "/coffee", indexable=False),
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
        page_seo_head(title, desc, PRIVACY_PATH, indexable=True),
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
        page_seo_head(title, desc, TERMS_PATH, indexable=True),
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
        page_seo_head(title, desc, SUBSCRIBE_PATH, indexable=True),
        page_theme_css(),
        site_nav_html(),
        threads_subscribe_desc_html(),
        html.escape(THREADS_SUBSCRIBE_ASK.replace("\n", " ")),
        html.escape(TELEGRAM_INVITE_URL, quote=True),
        html.escape(DISCORD_INVITE_URL, quote=True),
        html.escape(THREADS_PROFILE_URL, quote=True),
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
        page_seo_head(title, desc, "/history", indexable=False),
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


def product_card_html(item, shop_id="", extra=""):
    item = item or {}
    sku = str(item.get("sku") or "")
    title = html.escape(str(item.get("title") or sku or ""))
    url = item.get("url") or ""
    if url:
        name = "<a href='%s' target='_blank' rel='noopener'>%s</a>" % (
            html.escape(url, quote=True),
            title,
        )
    else:
        name = title
    price = item.get("price") or ""
    price_html = ("HK$%s" % html.escape(str(price))) if price else ""
    status = html.escape(str(item.get("status_label") or ""))
    if product_stock_key(item) == "in_stock" or status == "有貨":
        status = "<span class='stock-in'>%s</span>" % status
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
        "%s<div class='meta'><div class='name'>%s</div><div class='sub'>%s</div></div>%s</article>"
        % (
            html.escape(str(shop_id or ""), quote=True),
            html.escape(sku, quote=True),
            html.escape(tag, quote=True),
            html.escape(model, quote=True),
            html.escape(str(item.get("title") or sku or ""), quote=True),
            html.escape(str(price or ""), quote=True),
            html.escape(brand, quote=True),
            product_thumb_html(item),
            name,
            " · ".join(bits),
            extra,
        )
    )


def models_href(tag=None, stock=None):
    query = []
    if stock == "in_stock":
        query.append(("stock", "in"))
    elif stock == "out_of_stock":
        query.append(("stock", "out"))
    if tag in ("CX", "BX", "UX", "other"):
        query.append(("tag", tag))
    if query:
        return "/models?" + urllib.parse.urlencode(query)
    return "/models"


def notify_card_image_html(item, alt, placeholder):
    rel = str((item or {}).get("image_path") or "").replace("\\", "/")
    remote = product_image_url(item)
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
        value = listing_price_value(item)
        if value is not None:
            values.append(value)
    return values


def listing_price_label(items):
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


def offer_status_html(item):
    stock = product_stock_key(item)
    label = str((item or {}).get("status_label") or status_text(stock) or "")
    if not label:
        return ""
    css = {"in_stock": "stock-in", "out_of_stock": "stock-out"}.get(stock, "")
    if css:
        return "<span class='%s'>%s</span>" % (css, html.escape(label))
    return html.escape(label)


def model_offer_html(item):
    item = item or {}
    title = str(item.get("title") or item.get("sku") or "")
    url = str(item.get("url") or "").strip()
    name = html.escape(title)
    if url:
        name = "<a href='%s' target='_blank' rel='noopener'>%s</a>" % (
            html.escape(url, quote=True),
            name,
        )
    shop = str(item.get("shop_label") or item.get("shop_id") or "").strip()
    price = format_listing_price(listing_price_value(item))
    bits = [html.escape(part) for part in (shop, price) if part]
    status = offer_status_html(item)
    if status:
        bits.append(status)
    return (
        "<article class='model-offer'>%s<div class='meta'><div class='name'>%s</div>"
        "<div class='sub'>%s</div></div></article>"
        % (product_thumb_html(item), name, " · ".join(bits))
    )


def model_grid_card_html(group):
    group = group or {}
    items = sorted(list(group.get("items") or []), key=listing_rank)
    if not items:
        return ""
    primary = items[0]
    model = str(group.get("model") or "")
    title = str(primary.get("title") or model or primary.get("sku") or "")
    tag = group_tag_key(group)
    priced = current_price_items(items)
    price_label = listing_price_label(priced)
    sku = str(primary.get("sku") or "")
    shop_id = str(primary.get("shop_id") or "")
    brand = str(primary.get("shop_label") or shop_id)
    code = "<code class='catalog-card__id'>%s</code>" % html.escape(model) if model else ""
    range_html = (
        "<p class='catalog-card__subtitle'>%s</p>" % html.escape(price_label) if price_label else ""
    )
    placeholder = model or title or "?"
    image_html = notify_card_image_html(primary, title, placeholder)
    body = (
        "<div class='catalog-card__body'>%s<h2 class='catalog-card__name'>%s</h2>%s</div>"
        % (code, html.escape(title), range_html)
    )
    stock = group_stock_key(items)
    stock_label = status_text(stock)
    stock_class = {"in_stock": "stock-in", "out_of_stock": "stock-out"}.get(stock, "")
    badge_class = "catalog-card__badge catalog-card__badge--out" if stock == "out_of_stock" else "catalog-card__badge"
    media = (
        "<div class='catalog-card__image'>"
        "<span class='%s'><span class='%s'>%s</span></span>%s</div>"
        % (badge_class, stock_class, html.escape(stock_label), image_html)
    )
    offers = "\n".join(model_offer_html(item) for item in items)
    label = model or title
    return (
        "<article class='catalog-card product-card' data-shop='%s' data-sku='%s' data-tag='%s'"
        " data-model='%s' data-name='%s' data-price='%s' data-brand='%s'>"
        "<button type='button' class='catalog-card__hit' aria-haspopup='dialog' aria-label='%s'>%s%s</button>"
        "<div class='model-offer-list' hidden>%s</div></article>"
        % (
            html.escape(shop_id, quote=True),
            html.escape(sku, quote=True),
            html.escape(tag, quote=True),
            html.escape(model, quote=True),
            html.escape(title, quote=True),
            html.escape(price_label, quote=True),
            html.escape(brand, quote=True),
            html.escape(label, quote=True),
            media,
            body,
            offers,
        )
    )


def model_modal_html():
    return (
        '<div class="model-modal" id="model-modal" hidden>'
        '<button type="button" class="model-modal__backdrop" data-model-close aria-label="關閉"></button>'
        '<div class="model-modal__panel" role="dialog" aria-modal="true" aria-labelledby="model-modal-title">'
        '<div class="model-modal__head"><h2 class="model-modal__title" id="model-modal-title"></h2>'
        '<button type="button" class="model-modal__close" data-model-close aria-label="關閉">×</button></div>'
        '<div class="model-modal__body"></div></div></div>'
        "<script>(function(){"
        'var modal=document.getElementById("model-modal");'
        "if(!modal)return;"
        'var body=modal.querySelector(".model-modal__body");'
        'var title=modal.querySelector(".model-modal__title");'
        "var last=null;"
        "function close(){modal.hidden=true;document.body.classList.remove('model-open');if(last)last.focus();}"
        "function open(card,trigger){"
        'var src=card.querySelector(".model-offer-list");'
        "if(!src||!body||!title)return;"
        "body.innerHTML=src.innerHTML;"
        'title.textContent=card.getAttribute("data-model")||card.getAttribute("data-name")||"";'
        "modal.hidden=false;document.body.classList.add('model-open');last=trigger;"
        'var btn=modal.querySelector(".model-modal__close");if(btn)btn.focus();'
        "}"
        'document.addEventListener("click",function(e){'
        'var hit=e.target.closest&&e.target.closest(".catalog-card__hit");'
        "if(hit){var card=hit.closest('.catalog-card');if(card){e.preventDefault();open(card,hit);}return;}"
        'if(e.target.closest&&e.target.closest("[data-model-close]"))close();'
        "});"
        'document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!modal.hidden)close();});'
        "})();</script>"
    )


def render_models_html(items, tag_filter="", stock_filter=""):
    items = list(items or [])
    groups = group_listings_by_model(items)
    tag_counts = {"CX": 0, "BX": 0, "UX": 0, "other": 0}
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
    filtered = items
    if stock_filter == "in_stock":
        filtered = [item for item in items if product_stock_key(item) == "in_stock"]
    elif stock_filter == "out_of_stock":
        filtered = [item for item in items if product_stock_key(item) == "out_of_stock"]
    shown = group_listings_by_model(filtered)
    if tag_filter:
        shown = [group for group in shown if group_tag_key(group) == tag_filter]
    rendered = [model_grid_card_html(group) for group in shown]
    rendered = [card for card in rendered if card]
    if rendered:
        cards = "<div class='model-grid'>\n%s\n</div>" % "\n".join(rendered)
    else:
        cards = "<p>暫時沒有型號</p>"

    def stock_link(kind, text):
        on = " on" if (kind or "") == (stock_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(models_href(tag_filter or None, kind or None), quote=True),
            text,
        )

    def tag_link(tag, text):
        on = " on" if (tag or "") == (tag_filter or "") else ""
        return '<a class="filter%s" href="%s">%s</a>' % (
            on,
            html.escape(models_href(tag or None, stock_filter or None), quote=True),
            text,
        )

    filters = (
        '<p class="filters">%s %s %s</p>'
        '<p class="filters">%s %s %s %s %s</p>'
        % (
            stock_link("", "全部 %s" % len(groups)),
            stock_link("in_stock", "有貨 %s" % in_count),
            stock_link("out_of_stock", "缺貨 %s" % out_count),
            tag_link("", "All"),
            tag_link("CX", "CX [%s]" % tag_counts["CX"]),
            tag_link("BX", "BX [%s]" % tag_counts["BX"]),
            tag_link("UX", "UX [%s]" % tag_counts["UX"]),
            tag_link("other", "other [%s]" % tag_counts["other"]),
        )
    )
    title = "現貨圖庫 · %s" % SITE_BRAND
    desc = "香港爆旋陀螺現貨，按型號列出，圖片與到貨通知相同。"
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
<h1 class="page-title">現貨圖庫</h1>
<section class="panel" data-item-list-id="models" data-item-list-name="現貨圖庫">
%s
<p class="kicker">%s models</p>
%s
%s
</section>
</div>
%s
</body>
</html>
""" % (
        page_seo_head(title, desc, "/models", indexable=not tag_filter and not stock_filter),
        page_theme_css(),
        site_nav_html(),
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
        html.escape(TELEGRAM_INVITE_URL, quote=True),
        html.escape(DISCORD_INVITE_URL, quote=True),
        html.escape(THREADS_PROFILE_URL, quote=True),
        html.escape(THREADS_SUBSCRIBE_HINT),
    )


def render_go_bounce_html(target, shop_id, sku, page_url=None):
    target = target or {}
    dest = str(target.get("dest") or "")
    title = str(target.get("title") or SITE_BRAND)
    image = str(target.get("image") or seo_image_url())
    og_image = str(target.get("og_image") or seo_image_url())
    dest_attr = html.escape(dest, quote=True)
    dest_js = json.dumps(dest)
    desc = product_seo_description(target, THREADS_SUBSCRIBE_DESC)
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
<script>
(function(){
  var dest=%s;
  var gone=false;
  function go(){
    if(gone||!dest)return;
    gone=true;
    location.replace(dest);
  }
  if(window.gtag){
    gtag('config','G-19VVZP9R25',{transport_type:'beacon',send_page_view:false});
    gtag('event','page_view',{transport_type:'beacon'});
  }
  setTimeout(go, 500);
})();
</script>
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
        ),
        dest_attr,
        dest_js,
    )


def render_go_html(target, shop_id, sku, page_url=None):
    target = target or {}
    dest = str(target.get("dest") or "")
    title = str(target.get("title") or SITE_BRAND)
    image = str(target.get("image") or seo_image_url())
    og_image = str(target.get("og_image") or seo_image_url())
    desc = product_seo_description(target, THREADS_SUBSCRIBE_DESC)
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
        ),
        page_theme_css(),
        site_nav_html(),
        card,
        threads_subscribe_desc_html(),
        html.escape(THREADS_SUBSCRIBE_HINT),
        html.escape(THREADS_PROFILE_URL, quote=True),
        html.escape(THREADS_SUBSCRIBE_HINT),
        html.escape(TELEGRAM_INVITE_URL, quote=True),
        html.escape(DISCORD_INVITE_URL, quote=True),
        dest_attr,
        ga_events_script(),
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
    in_stock_href = html.escape(shop_products_href("all", "in_stock"), quote=True)
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
        '<a href="%s">全部現貨</a>'
        '<a href="/models">現貨圖庫</a>'
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


def filter_options_html(items, wrap_class="filters", combo_label="", force_combo=False):
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
    current_label = "All"
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
    aria = html.escape(combo_label or "Filter", quote=True)
    combo = (
        '<div class="filter-combo %s">'
        '<div class="filter-combo-field">'
        '<input type="search" class="filter-combo-input" placeholder="All" value="%s"'
        ' autocomplete="off" spellcheck="false" aria-label="%s">'
        '<button type="button" class="filter-combo-arrow" tabindex="-1" aria-label="%s">▾</button>'
        '<div class="filter-combo-list" hidden>%s</div></div></div>'
    ) % (
        html.escape(wrap_class, quote=True),
        html.escape(current_label, quote=True),
        aria,
        aria,
        options,
    )
    if not combo_label:
        return combo
    return '<div class="filter-store">%s%s</div>' % (heading, combo)


def shop_chips_html(shops, current_id=""):
    current = str(current_id or "")
    items = [(shop_products_href("all"), "All", current == "all")]
    for shop in shops or []:
        shop_id = str(shop.get("id") or "")
        items.append(
            (
                shop_products_href(shop_id),
                str(shop.get("label") or shop_id or "Shop"),
                bool(shop_id and shop_id == current),
            )
        )
    return filter_options_html(items, wrap_class="shop-chips", combo_label="Store")


def render_products_html(shop, items, key_query="", stock_filter="", tag_filter="", shops=None):
    shop = shop or {}
    if shops is None:
        shops = [shop]
    chips = shop_chips_html(shops, shop.get("id") or "")
    label = html.escape(str(shop.get("label") or shop.get("id") or "Shop"))
    shown = filter_shop_products(items, stock_filter, tag_filter)
    rows = []
    for item in shown:
        row = dict(item)
        if shop.get("label") and not row.get("shop_label"):
            row["shop_label"] = shop.get("label")
        rows.append(product_card_html(row, shop.get("id") or ""))
    cards = "\n".join(rows) or "<p>這個商店暫時沒有商品</p>"
    shop_id = shop.get("id") or ""
    in_count = sum(1 for item in (items or []) if product_stock_key(item) == "in_stock")
    out_count = sum(1 for item in (items or []) if product_stock_key(item) == "out_of_stock")
    tag_counts = {"CX": 0, "BX": 0, "UX": 0, "other": 0}
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

    filters = (
        '<p class="filters">%s %s %s</p>'
        '<p class="filters">%s %s %s %s %s</p>'
        % (
            filter_link("", "全部 %s" % len(items or [])),
            filter_link("in_stock", "有貨 %s" % in_count),
            filter_link("out_of_stock", "缺貨 %s" % out_count),
            tag_link("", "All"),
            tag_link("CX", "CX [%s]" % tag_counts["CX"]),
            tag_link("BX", "BX [%s]" % tag_counts["BX"]),
            tag_link("UX", "UX [%s]" % tag_counts["UX"]),
            tag_link("other", "other [%s]" % tag_counts["other"]),
        )
    )
    indexable = not stock_filter and not tag_filter
    seo_title, seo_desc = shop_page_seo(shop, items, indexable=indexable)
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
        page_seo_head(seo_title, seo_desc, shop_path, indexable=indexable),
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
        page_seo_head(title, desc, "/login", indexable=False),
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
        page_seo_head(title, desc, "/notify-test", indexable=True),
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
                html.escape(str(url), quote=True),
                title,
            )
        else:
            name = title
        price = str(item.get("price") or "").strip()
        if price and not price.upper().startswith("HK"):
            price = "HK$%s" % price
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


