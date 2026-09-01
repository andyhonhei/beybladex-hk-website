#!/usr/bin/env python3
"""Catalog and local collection pages for the status site."""
from __future__ import print_function

import html
import json
import os
import urllib.parse

from parts_catalog import (
    HUB_ORIGIN,
    PARTS_DIR,
    attach_shop_listings,
    is_display_part,
    is_set_product,
    load_catalog,
    load_shop_listing_rows,
    parse_combo_from_name,
    parts_from_cx_prefix,
)

COLLECTION_KEY = "beyblade-collection-v1"
PARTS_IMAGE_PREFIX = "/parts-images/"
CATALOG_DETAIL_CACHE_CONTROL = "public, max-age=31536000, s-maxage=31536000"
CATALOG_IMAGE_VERSION = "w2"
CATALOG_SHOPS_CACHE_SECONDS = 1800
CATALOG_SHOPS_CACHE_CONTROL = "public, max-age=%d, s-maxage=%d" % (
    CATALOG_SHOPS_CACHE_SECONDS,
    CATALOG_SHOPS_CACHE_SECONDS,
)

CATALOG_SHOPS_JS = r"""
<script>
(function(){
  var box=document.getElementById("catalog-shops");
  if(!box) return;
  var url=box.getAttribute("data-src");
  if(!url) return;
  fetch(url,{credentials:"same-origin"}).then(function(r){return r.ok?r.text():"";}).then(function(html){
    box.innerHTML=html || "<p class='coffee-copy'>暫時沒有舖頭紀錄</p>";
  }).catch(function(){});
})();
</script>
"""

COLLECTION_JS = r"""
<script>
(function(){
  var KEY=%s;
  function load(){
    try{return JSON.parse(localStorage.getItem(KEY)||"{}");}catch(e){return {};}
  }
  function save(state){
    state.products=state.products||[];
    state.parts=state.parts||[];
    state.variants=state.variants||[];
    state.releases=state.releases||[];
    localStorage.setItem(KEY, JSON.stringify(state));
  }
  function addAll(list, ids){
    ids.forEach(function(id){
      if(id && list.indexOf(id)<0) list.push(id);
    });
  }
  function addFromBtn(btn){
    var state=load();
    state.products=state.products||[];
    state.parts=state.parts||[];
    state.variants=state.variants||[];
    state.releases=state.releases||[];
    var parts=(btn.getAttribute("data-part-ids")||"").split(",").map(function(s){return s.trim();}).filter(Boolean);
    addAll(state.parts, parts);
    var product=btn.getAttribute("data-add-product");
    if(product) addAll(state.products, [product]);
    var variant=btn.getAttribute("data-add-variant");
    if(variant) addAll(state.variants, [variant]);
    var part=btn.getAttribute("data-add-part");
    if(part) addAll(state.parts, [part]);
    var release=btn.getAttribute("data-add-release");
    if(release) addAll(state.releases, [release]);
    save(state);
    btn.textContent="已加入";
    btn.disabled=true;
  }
  document.addEventListener("click", function(ev){
    var btn=ev.target.closest("[data-add-product],[data-add-variant],[data-add-part],[data-add-release]");
    if(!btn) return;
    ev.preventDefault();
    addFromBtn(btn);
  });
  function markOwned(){
    var state=load();
    document.querySelectorAll("[data-add-product]").forEach(function(btn){
      if((state.products||[]).indexOf(btn.getAttribute("data-add-product"))>=0){
        btn.textContent="已加入"; btn.disabled=true;
      }
    });
    document.querySelectorAll("[data-add-part]").forEach(function(btn){
      if((state.parts||[]).indexOf(btn.getAttribute("data-add-part"))>=0){
        btn.textContent="已加入"; btn.disabled=true;
      }
    });
  }
  markOwned();
  var box=document.getElementById("collection-list");
  if(box){
    var state=load();
    var products=(state.products||[]).join(", ")||"—";
    var parts=(state.parts||[]).join(", ")||"—";
    var variants=(state.variants||[]).join(", ")||"—";
    box.innerHTML="<p class='coffee-copy'><strong>整盒</strong> "+products+"</p>"+
      "<p class='coffee-copy'><strong>零件</strong> "+parts+"</p>"+
      "<p class='coffee-copy'><strong>變體</strong> "+variants+"</p>";
  }
})();
</script>
""" % json.dumps(COLLECTION_KEY)


def empty_collection():
    return {"products": [], "parts": [], "variants": [], "releases": []}


def catalog_image_href(rel):
    rel = str(rel or "").replace("\\", "/").lstrip("/")
    if rel.startswith("images/"):
        rel = rel[len("images/") :]
    if not rel:
        return ""
    from site_data import cdn_image_url

    return cdn_image_url(PARTS_IMAGE_PREFIX + rel) + "?v=" + CATALOG_IMAGE_VERSION


def _thumb(rel, alt):
    href = catalog_image_href(rel)
    if not href:
        return "<div class='thumb thumb-empty' aria-hidden='true'></div>"
    return "<img class='thumb' src='%s' alt='%s' loading='lazy' decoding='async'>" % (
        html.escape(href, quote=True),
        html.escape(alt or ""),
    )


CATALOG_GRID_CSS = """
.page-title{font-size:clamp(26px,7vw,40px);margin:16px 0 12px}
.catalog-toolbar{position:sticky;top:0;z-index:6;background:var(--blue);padding:4px 0 10px}
.catalog-toolbar .filter-store{max-width:100%;margin:0 0 10px;padding:12px 12px 12px}
.catalog-toolbar .filter-combo{max-width:100%;margin:0}
.catalog-toolbar .search-row{margin:0;gap:8px;flex-wrap:nowrap;align-items:center}
.catalog-toolbar .search-row input{min-width:0;flex:1;font-size:16px;padding:8px 12px;
border:1px solid var(--ink);background:#fff;color:var(--ink)}
.catalog-toolbar .search-row button{background:transparent;color:var(--ink);border:1px solid var(--ink);
padding:8px 12px;font-size:11px}
.panel.catalog-panel{padding:8px;margin-top:12px}
.catalog-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.catalog-tile{display:flex;flex-direction:column;gap:6px;min-width:0;
text-decoration:none!important;color:inherit;background:#fff;border:1px solid #ececf4;
padding:6px 6px 8px}
.catalog-tile:hover{opacity:1;border-color:var(--ink)}
.catalog-tile .thumb,.catalog-tile .thumb-empty{width:100%;height:auto;aspect-ratio:1;
flex:none;object-fit:contain;background:#fff}
.catalog-tile .name{font-size:11px;line-height:1.25;margin:0;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.catalog-tile .sku{font-family:"IBM Plex Mono",monospace;font-size:10px;color:#666;
letter-spacing:.04em}
@media(min-width:520px){
.catalog-grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.catalog-tile .name{font-size:12px}
}
@media(min-width:800px){
.catalog-grid{grid-template-columns:repeat(5,minmax(0,1fr))}
.wrap{max-width:1180px}
}
@media(min-width:1100px){
.catalog-grid{grid-template-columns:repeat(6,minmax(0,1fr))}
}
.detail-hero{display:flex;flex-direction:column;gap:12px;padding-bottom:16px;
border-bottom:1px solid #d8d8f0;margin-bottom:16px}
.detail-hero .thumb,.detail-hero .thumb-empty{width:min(100%,280px);height:auto;aspect-ratio:1;
flex:none;object-fit:contain;align-self:center;background:#fff}
@media(min-width:640px){
.detail-hero{flex-direction:row;align-items:flex-start}
.detail-hero .thumb,.detail-hero .thumb-empty{align-self:flex-start}
}
.facts{display:grid;gap:8px;margin:12px 0}
.fact{display:grid;grid-template-columns:6.5em 1fr;gap:8px;font-size:13px;align-items:start}
.fact-k{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;
text-transform:uppercase;color:#666;padding-top:2px}
.fact-v{word-break:break-word;line-height:1.4}
.fact-v a{color:inherit}
.desc{font-size:14px;line-height:1.55;margin:0 0 16px}
.related-list{display:flex;flex-direction:column;gap:0}
.related-list .product-card{align-items:flex-start}
.related-list .product-card .thumb,.related-list .product-card .thumb-empty{width:64px;height:64px;flex:0 0 64px;object-fit:contain}
.related-desc{font-size:12px;margin:6px 0 0;color:#444}
.stock-out{color:#888}
"""


def variant_combo_key(variant):
    combo = parse_combo_from_name((variant or {}).get("name_zh") or "")
    if not combo:
        return (variant or {}).get("id") or (variant or {}).get("name_zh") or ""
    return (combo.get("prefix") or "", combo.get("ratchet") or "", combo.get("bit") or "")


def needs_variant_pick(product, variants):
    ids = (product or {}).get("variant_ids") or []
    keys = set()
    for vid in ids:
        keys.add(variant_combo_key((variants or {}).get(vid) or {"id": vid}))
    return len(keys) > 1


def parts_for_variant(variant, catalog):
    combo = parse_combo_from_name((variant or {}).get("name_zh") or "")
    if not combo:
        return []
    ids = list(parts_from_cx_prefix(combo.get("prefix") or ""))
    if combo.get("ratchet"):
        ids.append(combo["ratchet"])
    if combo.get("bit"):
        ids.append(combo["bit"])
    out = []
    for part_id in ids:
        if part_id and part_id not in out:
            out.append(part_id)
    return out


def add_part_to_collection(owned, part_id):
    owned = dict(owned or empty_collection())
    for key in ("products", "parts", "variants", "releases"):
        owned[key] = list(owned.get(key) or [])
    if part_id and part_id not in owned["parts"]:
        owned["parts"].append(part_id)
    return owned


def add_package_to_collection(owned, product_id, catalog, variant_id=None):
    owned = dict(owned or empty_collection())
    for key in ("products", "parts", "variants", "releases"):
        owned[key] = list(owned.get(key) or [])
    product = ((catalog or {}).get("products") or {}).get(product_id) or {}
    part_ids = list(product.get("part_ids") or [])
    if variant_id:
        variant = ((catalog or {}).get("variants") or {}).get(variant_id) or {}
        extra = parts_for_variant(variant, catalog)
        if extra:
            part_ids = extra
        if variant_id not in owned["variants"]:
            owned["variants"].append(variant_id)
    elif product_id and product_id not in owned["products"]:
        owned["products"].append(product_id)
    for part_id in part_ids:
        if part_id and part_id not in owned["parts"]:
            owned["parts"].append(part_id)
    return owned


def filter_catalog_products(products, line="", tag="", q="", kind=""):
    line = (line or "").upper()
    tag = (tag or "").lower()
    q = (q or "").strip().lower()
    rows = []
    for rec in (products or {}).values():
        rec_line = str(rec.get("line") or "").upper()
        if line == "HASBRO" and rec.get("source") != "hasbro" and rec_line != "HASBRO":
            continue
        if line and line != "HASBRO" and rec_line != line:
            continue
        base = rec.get("base_set_id") or ""
        pid = rec.get("id") or ""
        if not q and base and base != pid and base in (products or {}):
            continue
        tags = [str(t).lower() for t in (rec.get("tags") or [])]
        if tag and tag not in tags:
            continue
        blob = " ".join(
            [
                rec.get("id") or "",
                rec.get("name_zh") or "",
                rec.get("name_en") or "",
            ]
        ).lower()
        if q and q not in blob:
            continue
        if kind == "set" and not is_set_product(rec):
            continue
        if kind == "bey" and is_set_product(rec):
            continue
        rows.append(rec)
    rows.sort(key=lambda rec: (rec.get("line") or "", rec.get("id") or ""))
    return rows


def _page(title, path, inner, extra_style="", indexable=False):
    from site_pages import page_seo_head, page_theme_css, site_nav_html, subscribe_script, filter_combo_script

    desc = "Beyblade X 圖鑑與本機零件庫"
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
%s
<style>
%s
.own-btn{flex:0 0 auto;min-height:40px;background:transparent;border:1px solid var(--ink);
padding:8px 12px;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:11px;
letter-spacing:.12em;text-transform:uppercase}
.own-btn:disabled{opacity:.55;cursor:default}
.search-row{display:flex;gap:8px;margin:0 0 16px;flex-wrap:wrap}
.search-row input{flex:1;min-width:160px;padding:8px 12px;border:1px solid #fff;background:transparent;
color:#fff;font-family:"IBM Plex Mono",monospace;font-size:12px}
.search-row button{background:#fff;color:var(--ink);border:1px solid #fff;padding:8px 12px;
font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;cursor:pointer}
%s
</style>
</head>
<body>
<div class="slash" aria-hidden="true"></div>
<div class="wrap">
%s
<h1 class="page-title">%s</h1>
%s
</div>
%s
</body>
</html>
""" % (
        page_seo_head(title, desc, path, indexable=indexable),
        page_theme_css(),
        extra_style,
        site_nav_html(),
        html.escape(title),
        inner,
        subscribe_script() + filter_combo_script() + COLLECTION_JS + CATALOG_SHOPS_JS,
    )


SLOT_LABELS = {
    "blade": "上蓋",
    "ratchet": "固鎖",
    "bit": "軸心",
    "lock_chip": "紋章鎖",
    "assist_blade": "輔助戰刃",
    "over_blade": "超越戰刃",
    "metal_blade": "金屬戰刃",
}


def _catalog_href(line="", tag="", q="", kind=""):
    bits = []
    if kind:
        bits.append("kind=" + urllib.parse.quote(str(kind)))
    if line:
        bits.append("line=" + urllib.parse.quote(str(line)))
    if tag:
        bits.append("tag=" + urllib.parse.quote(str(tag)))
    if q:
        bits.append("q=" + urllib.parse.quote(q))
    return "/catalog" + (("?" + "&".join(bits)) if bits else "")


def _filter_links(current_line, q="", tag="", kind=""):
    from site_pages import filter_options_html

    current_line = current_line or ""
    tag = (tag or "").lower()
    kind = kind or ""
    items = []
    kinds = [("", "全部"), ("set", "套裝"), ("bey", "整顆陀螺")]
    kinds.extend(SLOT_LABELS.items())
    for key, label in kinds:
        keep_line = key in ("", "set", "bey")
        href = _catalog_href(
            kind=key,
            line=current_line if keep_line else "",
            q=q if keep_line else "",
        )
        selected = (key or "") == kind and not tag
        items.append((href, label, selected))
    for line, label in [("CX", "CX"), ("BX", "BX"), ("UX", "UX"), ("HASBRO", "Hasbro")]:
        keep_kind = kind in ("", "set", "bey")
        href = _catalog_href(kind=kind if keep_kind else "", line=line, q=q if keep_kind else "")
        selected = line == current_line and not tag and kind in ("", "set", "bey")
        items.append((href, label, selected))
    items.extend(
        [
            (_catalog_href(tag="reprint"), "復刻", tag == "reprint"),
            (_catalog_href(tag="convention"), "限定", tag == "convention"),
            ("/collection", "我的庫", False),
        ]
    )
    return filter_options_html(items, wrap_class="filters", combo_label="Filter")


def _add_button(label, attrs):
    bits = " ".join(
        '%s="%s"' % (key, html.escape(str(value), quote=True))
        for key, value in attrs.items()
        if value is not None
    )
    return '<button type="button" class="own-btn" %s>%s</button>' % (bits, html.escape(label))


def _format_jpy(value):
    if value in (None, ""):
        return ""
    try:
        return "¥%s" % format(int(value), ",")
    except (TypeError, ValueError):
        return str(value)


def _format_hkd(value):
    text = str(value or "").strip()
    if not text:
        return ""
    if text[:3].upper() == "HK$" or text[:1] == "$":
        return text
    return "HK$%s" % text


def _facts_html(pairs):
    rows = []
    for key, value in pairs:
        if value in (None, ""):
            continue
        rows.append(
            "<div class='fact'><span class='fact-k'>%s</span><span class='fact-v'>%s</span></div>"
            % (html.escape(key), value)
        )
    if not rows:
        return ""
    return "<div class='facts'>%s</div>" % "".join(rows)


def _text_or_link(href, label):
    if not href:
        return html.escape(label) if label else ""
    extra = " target='_blank' rel='noopener'" if str(href).startswith("http") else ""
    return "<a href='%s'%s>%s</a>" % (
        html.escape(href, quote=True),
        extra,
        html.escape(label or href),
    )


def _hub_href(path):
    path = str(path or "")
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return HUB_ORIGIN + (path if path.startswith("/") else "/" + path)


def listings_for_product(catalog, product_id):
    out = []
    for row in catalog.get("shop_listings") or []:
        if product_id in (row.get("product_ids") or []):
            out.append(row)
    return out


def _listing_stock_code(listing):
    raw = listing.get("status")
    if raw in ("in_stock", "out_of_stock", "unknown"):
        return raw
    from site_data import stock_status

    return stock_status(listing)


def _listing_status_html(listing):
    from site_data import status_text

    code = _listing_stock_code(listing)
    label = listing.get("status_label") or status_text(code)
    if not label:
        return ""
    css = {"in_stock": "stock-in", "out_of_stock": "stock-out"}.get(code)
    if css:
        return "<span class='%s'>%s</span>" % (css, html.escape(str(label)))
    return html.escape(str(label))


def _shop_rows_html(catalog, product_id):
    from site_data import go_href

    rows = []
    for listing in listings_for_product(catalog, product_id):
        shop = listing.get("shop_id") or ""
        sku = listing.get("sku") or ""
        title = listing.get("title") or sku or shop
        href = listing.get("url") or ""
        if not href and shop and sku:
            href = go_href(shop, sku)
        price = _format_hkd(listing.get("price"))
        status = _listing_status_html(listing)
        sub = " · ".join(
            part
            for part in (
                html.escape(shop) if shop else "",
                html.escape(sku) if sku else "",
                html.escape(price) if price else "",
                status,
            )
            if part
        )
        rows.append(
            "<article class='product-card'><div class='meta'><div class='name'>%s</div>"
            "<div class='sub'>%s</div></div></article>"
            % (
                _text_or_link(href, title) if href else html.escape(title),
                sub,
            )
        )
    if not rows:
        return "<p class='coffee-copy'>暫時沒有舖頭紀錄</p>"
    return "<div class='related-list'>" + "\n".join(rows) + "</div>"


def _shops_delay_note_html():
    from site_pages import subscribe_widget_html
    from site_data import SUBSCRIBE_BUTTON_LABEL

    minutes = max(1, CATALOG_SHOPS_CACHE_SECONDS // 60)
    note = (
        "<p class='coffee-copy'>貨況最多延遲約 %s 分鐘。"
        "要即時收到補貨／缺貨，請訂閱通知。</p>"
        % minutes
    )
    return note + subscribe_widget_html(
        SUBSCRIBE_BUTTON_LABEL, widget_id="catalog-subscribe"
    )


def render_catalog_shops_html(catalog, product_id):
    return _shop_rows_html(catalog, product_id)


def _product_ref_html(catalog, product_id):
    rec = ((catalog or {}).get("products") or {}).get(product_id) or {"id": product_id}
    name = rec.get("name_zh") or rec.get("name_en") or product_id
    href = "/catalog/" + urllib.parse.quote(str(product_id), safe="-")
    hub = rec.get("source_url") or ""
    sub = " · ".join(
        part
        for part in (
            product_id,
            rec.get("released_on") or "",
            _format_jpy(rec.get("price_jpy")),
        )
        if part
    )
    desc = rec.get("description") or ""
    desc_html = (
        "<p class='desc related-desc'>%s</p>" % html.escape(desc) if desc else ""
    )
    link_html = (
        "<div class='sub'>%s</div>" % _text_or_link(hub, "BeybladeHub") if hub else ""
    )
    return (
        "<article class='product-card'>%s<div class='meta'><div class='name'>"
        "<a href='%s'>%s</a></div><div class='sub'>%s</div>%s%s</div></article>"
        % (
            _thumb(rec.get("image_path") or "", name),
            html.escape(href, quote=True),
            html.escape(str(name)),
            html.escape(sub),
            link_html,
            desc_html,
        )
    )


def _part_tiles_html(catalog, slot=""):
    rows = []
    for rec in sorted((catalog.get("parts") or {}).values(), key=lambda r: r.get("id") or ""):
        if not is_display_part(rec):
            continue
        if slot and (rec.get("slot") or "") != slot:
            continue
        part_id = rec.get("id") or ""
        label = rec.get("name_zh") or rec.get("name_en") or part_id
        href = "/parts/" + urllib.parse.quote(str(part_id), safe="-._")
        rows.append(
            "<a class='catalog-tile' href='%s'>"
            "%s<span class='name'>%s</span><span class='sku'>%s</span></a>"
            % (
                html.escape(href, quote=True),
                _thumb(rec.get("image_path") or "", label),
                html.escape(str(label)),
                html.escape(str(part_id)),
            )
        )
    return rows


def render_catalog_html(catalog, line="", tag="", q="", kind=""):
    catalog = catalog or {}
    kind = kind or ""
    if kind in SLOT_LABELS or kind == "parts":
        cards = _part_tiles_html(catalog, slot="" if kind == "parts" else kind)
    else:
        rows = filter_catalog_products(
            catalog.get("products") or {}, line=line, tag=tag, q=q, kind=kind
        )
        cards = []
        for rec in rows:
            pid = rec.get("id") or ""
            name = rec.get("name_zh") or pid
            href = "/catalog/" + urllib.parse.quote(str(pid), safe="-")
            cards.append(
                "<a class='catalog-tile' href='%s'>"
                "%s<span class='name'>%s</span><span class='sku'>%s</span></a>"
                % (
                    html.escape(href, quote=True),
                    _thumb(rec.get("image_path") or "", name),
                    html.escape(name),
                    html.escape(pid),
                )
            )
    hidden = []
    if kind:
        hidden.append(
            '<input type="hidden" name="kind" value="%s">' % html.escape(kind, quote=True)
        )
    if line and kind not in SLOT_LABELS:
        hidden.append(
            '<input type="hidden" name="line" value="%s">' % html.escape(line, quote=True)
        )
    if tag:
        hidden.append(
            '<input type="hidden" name="tag" value="%s">' % html.escape(tag, quote=True)
        )
    search = (
        '<div class="filter-store"><p class="filter-store-label">Search</p>'
        '<form class="search-row" method="get" action="/catalog">'
        '<input type="search" name="q" value="%s" placeholder="搜尋 CX-18 / 腕龍">'
        "%s"
        "<button type='submit'>搜尋</button></form></div>"
        % (
            html.escape(q or "", quote=True),
            "".join(hidden),
        )
    )
    grid = "\n".join(cards) if cards else "<p>沒有符合的商品</p>"
    inner = (
        '<div class="catalog-toolbar">'
        + _filter_links(line, q=q, tag=tag, kind=kind)
        + search
        + "</div>"
        + "<section class='panel catalog-panel'><div class='catalog-grid'>"
        + grid
        + "</div></section>"
    )
    return _page(
        "圖鑑",
        "/catalog",
        inner,
        extra_style=CATALOG_GRID_CSS,
        indexable=not line and not tag and not q and not kind,
    )


def render_catalog_product_html(catalog, product_id):
    catalog = catalog or {}
    product = (catalog.get("products") or {}).get(product_id)
    if not product:
        return None
    variants = catalog.get("variants") or {}
    parts = catalog.get("parts") or {}
    name = product.get("name_zh") or product_id
    part_ids = product.get("part_ids") or []
    part_rows = []
    for part_id in part_ids:
        rec = parts.get(part_id) or {"id": part_id}
        if not is_display_part(rec):
            continue
        label = rec.get("name_zh") or rec.get("name_en") or part_id
        hub = _hub_href(rec.get("href") or "")
        part_desc = rec.get("description") or rec.get("label") or ""
        part_rows.append(
            "<article class='product-card'>"
            "%s<div class='meta'><div class='name'><a href='/parts/%s'>%s</a></div>"
            "<div class='sub'>%s</div>%s%s</div>%s</article>"
            % (
                _thumb(rec.get("image_path") or "", label),
                html.escape(urllib.parse.quote(str(part_id), safe="-._"), quote=True),
                html.escape(str(label)),
                html.escape(
                    " · ".join(
                        part
                        for part in (
                            SLOT_LABELS.get(rec.get("slot") or "", rec.get("slot") or ""),
                            part_id,
                            rec.get("first_seen_in") or "",
                        )
                        if part
                    )
                ),
                ("<div class='sub'>%s</div>" % _text_or_link(hub, "BeybladeHub") if hub else ""),
                (
                    "<p class='desc related-desc'>%s</p>" % html.escape(str(part_desc))
                    if part_desc
                    else ""
                ),
                _add_button("加入零件", {"data-add-part": part_id}),
            )
        )
    actions = ""
    if needs_variant_pick(product, variants):
        picks = []
        for vid in product.get("variant_ids") or []:
            variant = variants.get(vid) or {"id": vid, "name_zh": vid}
            ids = parts_for_variant(variant, catalog) or part_ids
            ids = [
                part_id
                for part_id in ids
                if is_display_part(parts.get(part_id) or {"id": part_id})
            ]
            picks.append(
                "<article class='product-card'><div class='meta'><div class='name'>%s</div>"
                "<div class='sub'>%s</div></div>%s</article>"
                % (
                    html.escape(variant.get("name_zh") or vid),
                    html.escape(vid),
                    _add_button(
                        "加入此款",
                        {
                            "data-add-variant": vid,
                            "data-part-ids": ",".join(ids),
                        },
                    ),
                )
            )
        actions = "<h2>選擇開到的一款</h2>" + "\n".join(picks)
    else:
        actions = _add_button(
            "加入整盒",
            {
                "data-add-product": product_id,
                "data-part-ids": ",".join(
                    part_id
                    for part_id in part_ids
                    if is_display_part(parts.get(part_id) or {"id": part_id})
                ),
            },
        )
    facts = _facts_html(
        [
            ("系列", html.escape(product.get("line") or "")),
            ("編號", html.escape(product_id)),
            ("JAN", html.escape(product.get("jan") or "")),
            ("發售", html.escape(product.get("released_on") or "")),
            ("價錢", html.escape(_format_jpy(product.get("price_jpy")))),
            ("類型", html.escape(product.get("bey_type") or "")),
            ("原裝配置", html.escape(product.get("stock_combo") or "")),
            (
                "連結",
                _text_or_link(product.get("source_url") or "", "BeybladeHub"),
            ),
        ]
    )
    desc = product.get("description") or ""
    desc_html = (
        "<p class='desc'>%s</p>" % html.escape(desc) if desc else ""
    )
    inner = (
        _filter_links(product.get("line") or "")
        + "<section class='panel'>"
        + "<div class='detail-hero'>%s<div class='meta'><div class='name'>%s</div>"
          "%s%s%s</div></div>"
        % (
            _thumb(product.get("image_path") or "", name),
            html.escape(name),
            facts,
            desc_html,
            actions if not needs_variant_pick(product, variants) else "",
        )
        + (actions if needs_variant_pick(product, variants) else "")
        + "<h2>香港舖頭</h2>"
        + _shops_delay_note_html()
        + "<div id='catalog-shops' data-src='/catalog/%s/shops'>"
          "<p class='coffee-copy'>載入舖頭貨況…</p></div>"
        % html.escape(urllib.parse.quote(str(product_id), safe="-"), quote=True)
        + "<h2>內含零件</h2>"
        + "<div class='related-list'>"
        + ("\n".join(part_rows) or "<p>沒有零件資料</p>")
        + "</div></section>"
    )
    return _page(name, "/catalog/" + product_id, inner, extra_style=CATALOG_GRID_CSS)


def render_parts_html(catalog, slot=""):
    catalog = catalog or {}
    if slot in SLOT_LABELS:
        return render_catalog_html(catalog, kind=slot)
    return render_catalog_html(catalog, kind="parts")


def render_part_detail_html(catalog, part_id):
    catalog = catalog or {}
    rec = (catalog.get("parts") or {}).get(part_id)
    if not rec:
        return None
    label = rec.get("name_zh") or rec.get("name_en") or part_id
    releases = []
    for rid in rec.get("release_ids") or []:
        rel = (catalog.get("part_releases") or {}).get(rid) or {"id": rid}
        set_id = rel.get("set_id") or rel.get("base_set_id") or ""
        set_href = (
            "/catalog/" + urllib.parse.quote(str(set_id), safe="-") if set_id else ""
        )
        releases.append(
            "<article class='product-card'>"
            "%s<div class='meta'><div class='name'>%s</div><div class='sub'>%s</div></div>"
            "%s</article>"
            % (
                _thumb(rel.get("image_path") or "", rel.get("name_zh") or rid),
                _text_or_link(set_href, rel.get("name_zh") or rid) if set_href else html.escape(rel.get("name_zh") or rid),
                html.escape(
                    " · ".join(
                        part
                        for part in (rel.get("color") or "", set_id or rid)
                        if part
                    )
                ),
                _add_button(
                    "加入此配色",
                    {"data-add-release": rid, "data-add-part": part_id},
                ),
            )
        )
    used = rec.get("used_in") or []
    related = [_product_ref_html(catalog, pid) for pid in used]
    first_id = rec.get("first_seen_in") or (used[0] if used else "")
    first_html = ""
    if first_id:
        first_html = _product_ref_html(catalog, first_id)
    first_prod = ((catalog.get("products") or {}).get(first_id) or {}) if first_id else {}
    hub = _hub_href(rec.get("href") or "")
    facts = _facts_html(
        [
            ("零件", html.escape(str(part_id))),
            (
                "類型",
                html.escape(SLOT_LABELS.get(rec.get("slot") or "", rec.get("slot") or "")),
            ),
            ("英文", html.escape(rec.get("name_en") or "")),
            ("發售", html.escape(first_prod.get("released_on") or "")),
            ("價錢", html.escape(_format_jpy(first_prod.get("price_jpy")))),
            (
                "連結",
                _text_or_link(hub, "BeybladeHub") if hub else "",
            ),
        ]
    )
    desc = rec.get("description") or rec.get("label") or ""
    desc_html = "<p class='desc'>%s</p>" % html.escape(str(desc)) if desc else ""
    inner = (
        _filter_links("")
        + "<section class='panel'>"
        + "<div class='detail-hero'>%s<div class='meta'><div class='name'>%s</div>"
          "%s%s%s</div></div>"
        % (
            _thumb(rec.get("image_path") or "", label),
            html.escape(str(label)),
            facts,
            desc_html,
            _add_button("加入零件", {"data-add-part": part_id}),
        )
        + ("<h2>首次出現</h2><div class='related-list'>%s</div>" % first_html if first_html else "")
        + "<h2>用於這些商品</h2><div class='related-list'>"
        + ("\n".join(related) or "<p>未對應盒裝</p>")
        + "</div>"
        + "<h2>配色／出處</h2><div class='related-list'>"
        + ("\n".join(releases) or "<p>沒有配色紀錄</p>")
        + "</div></section>"
    )
    return _page(str(label), "/parts/" + part_id, inner, extra_style=CATALOG_GRID_CSS)


def render_collection_html():
    inner = (
        '<p class="filters"><a class="filter" href="/catalog">圖鑑</a> '
        '<a class="filter" href="/parts">零件</a></p>'
        "<section class='panel'>"
        "<p class='coffee-copy'>倉庫只存在這個瀏覽器。之後登入才能同步。</p>"
        "<div id='collection-list'></div>"
        "</section>"
    )
    return _page("我的庫", "/collection", inner)


def serve_parts_image(path):
    rel = urllib.parse.unquote((path or "")[len(PARTS_IMAGE_PREFIX) :]).lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    full = os.path.realpath(os.path.join(PARTS_DIR, "images", rel))
    root = os.path.realpath(os.path.join(PARTS_DIR, "images"))
    if not (full == root or full.startswith(root + os.sep)) or not os.path.isfile(full):
        return None
    return full


def handle_catalog_http(path, query, catalog=None):
    parsed_q = urllib.parse.parse_qs(query or "")
    if path.startswith(PARTS_IMAGE_PREFIX):
        full = serve_parts_image(path)
        if not full:
            return {"status": 404}
        return {"status": 200, "file": full, "content_type": "image/jpeg"}
    if catalog is None:
        catalog = load_catalog()
        if path.endswith("/shops"):
            attach_shop_listings(catalog, load_shop_listing_rows())
    if path == "/catalog":
        html_page = render_catalog_html(
            catalog,
            line=(parsed_q.get("line") or [""])[0],
            tag=(parsed_q.get("tag") or [""])[0],
            q=(parsed_q.get("q") or [""])[0],
            kind=(parsed_q.get("kind") or [""])[0],
        )
        return {"status": 200, "html": html_page}
    if path.startswith("/catalog/") and path.endswith("/shops"):
        product_id = urllib.parse.unquote(path[len("/catalog/") : -len("/shops")].strip("/"))
        rec = (catalog.get("products") or {}).get(product_id)
        if not rec:
            return {"status": 404}
        return {
            "status": 200,
            "html": render_catalog_shops_html(catalog, product_id),
            "cache": CATALOG_SHOPS_CACHE_CONTROL,
        }
    if path.startswith("/catalog/"):
        product_id = urllib.parse.unquote(path[len("/catalog/") :].strip("/"))
        html_page = render_catalog_product_html(catalog, product_id)
        if not html_page:
            return {"status": 404}
        return {
            "status": 200,
            "html": html_page,
            "cache": CATALOG_DETAIL_CACHE_CONTROL,
        }
    if path == "/parts":
        return {
            "status": 200,
            "html": render_parts_html(catalog, slot=(parsed_q.get("slot") or [""])[0]),
        }
    if path.startswith("/parts/"):
        part_id = urllib.parse.unquote(path[len("/parts/") :].strip("/"))
        html_page = render_part_detail_html(catalog, part_id)
        if not html_page:
            return {"status": 404}
        return {
            "status": 200,
            "html": html_page,
            "cache": CATALOG_DETAIL_CACHE_CONTROL,
        }
    if path == "/collection":
        return {"status": 200, "html": render_collection_html()}
    return None
