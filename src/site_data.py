#!/usr/bin/env python3
"""Read-side helpers for the Beyblade status site."""
from __future__ import print_function

import hashlib
import hmac
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    HKT_TZ = ZoneInfo("Asia/Hong_Kong")
except Exception:
    HKT_TZ = timezone(timedelta(hours=8))

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
CONFIG_DIR = os.path.join(ROOT_DIR, "config")
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "watch_config.json")
DEFAULT_STATE = os.path.join(DATA_DIR, "seen_skus.json")
DEFAULT_ERROR_STATE = os.path.join(DATA_DIR, "watch_errors.json")
STATUS_PATH = os.path.join(DATA_DIR, "watch_status.json")
EVENT_LOG_PATH = os.path.join(DATA_DIR, "watch_events.jsonl")
NOTIFY_HISTORY_PATH = os.path.join(DATA_DIR, "notify_history.jsonl")


def image_data_dir():
    watch_data = os.environ.get("BEYBLADE_WATCH_DATA_DIR", "").strip()
    if not watch_data:
        watch_data = "/home/ubuntu/hobbyland_checknew_product/data"
    if os.path.isdir(os.path.join(watch_data, "images")):
        return watch_data
    return DATA_DIR


CONFIG = {}
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HOBBYLAND_STATIC_ORIGIN = "https://static.hobbylandeshop.com/"
SHOP_ORIGIN = "https://www.hobbylandeshop.com"
CATEGORY = "nproduct_booking"
CATEGORY_URL = SHOP_ORIGIN + "/product-category/" + CATEGORY
DISCORD_INVITE_URL = "https://discord.gg/qpnuMgBv8"
TELEGRAM_INVITE_URL = "https://t.me/+mbTPVeGFBalhMjQ9"
THREADS_PROFILE_URL = "https://www.threads.com/@beybladex_hk_notify"
THREADS_SUBSCRIBE_DESC = "香港爆旋陀螺到貨通知。Online舖頭 有新品、補貨、缺貨就出帖。非官方。"
THREADS_SUBSCRIBE_HINT = "Follow 我哋 Threads 之後記得撳右上角訂閱／鐘仔掣，訂閱帖文通知"
THREADS_SUBSCRIBE_ASK = (
    "Thread Follow 之後記得撳右上角鐘仔訂閱帖文，先可以有即時通知！\n"
    "都可以subscribe Telegram and Discord，以免Miss咗！"
)
SUBSCRIBE_BUTTON_LABEL = "訂閱通知"
PAYME_URL = "https://payme.hsbc/andyhuihh"
ALIPAYHK_PATH = "/alipayhk.jpg"
SITE_BRAND = "HK BeybladeX Watch"
SITE_BRAND_SHORT = "HK BeybladeX"
SITE_ORIGIN = "https://beybladex-watch.andyhhh.com"
CDN_ORIGIN = "https://beybladex-cdn.andyhhh.com"
UAT_GO_SHOP = "uat"
UAT_GO_SKU = "test"
GO_HOME_SEO_SHOP = "buymarkettoy"
ADMIN_HOST = "beybladex-admin.andyhhh.com"
ADMIN_COOKIE_NAME = "bxw_admin"
SEO_IMAGE_PATH = "/seo-image.png"
OG_IMAGE_PATH = "/og-card.jpg"
OG_HOME_PATH = "/share"
SUBSCRIBE_PATH = "/subscribe"
PRIVACY_PATH = "/privacy"
PRIVACY_ALIAS_PATH = "/privacy-policy"
TERMS_PATH = "/terms"
TERMS_ALIAS_PATH = "/terms-of-service"
OG_TEST_PATH = "/og-test-20260830"
OG_GOAL_PATH = "/goal"
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630
LOGO_PATH = "/logo.png"
STATIC_LOGO = os.path.join(ROOT_DIR, "static", "logo.png")
STATIC_PNGS = {
    LOGO_PATH: STATIC_LOGO,
    SEO_IMAGE_PATH: os.path.join(ROOT_DIR, "static", "seo-image.png"),
    OG_IMAGE_PATH: os.path.join(ROOT_DIR, "static", "og-card.jpg"),
    "/favicon.ico": STATIC_LOGO,
    ALIPAYHK_PATH: os.path.join(ROOT_DIR, "static", "alipayhk.jpg"),
}
HTML_CACHE_CONTROL = "public, max-age=30, s-maxage=30"
GO_CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-if-error=604800"
IMAGE_CACHE_CONTROL = "public, max-age=31536000, s-maxage=31536000, immutable"
PAGE_CACHE_TTL = 30
LISTING_WATCH_INTERVAL = 2
MYSQL_PROBE_TTL = 30
IMAGE_MIN_CACHE_BYTES = 2000
NOTIFY_EVENT_KINDS = ("new", "restock", "sold_out")
NOTIFY_EVENT_LABELS = {"new": "新品", "restock": "補貨", "sold_out": "售罄"}
INDEX_NOTIFY_LIMIT = 5
HISTORY_NOTIFY_DAYS = 7
INDEX_NOTIFY_SCAN = 400
FILTER_COMBO_THRESHOLD = 7
SEO_DESC_MAX = 300
LINE_MODEL_RE = re.compile(
    r"(?<![A-Za-z0-9])((CX|BX|UX)-?[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?)",
    re.I,
)
MYSQL_SEEN_SKUS_SELECT = (
    "SELECT shop_id, sku, category, stock, stock_changed_at, updated_at, "
    "title, url, price, image, image_path, `model`, `tag`, description "
    "FROM seen_skus WHERE shop_id = %s ORDER BY sku"
)
_page_cache = {}
_page_cache_lock = threading.Lock()
_mysql_probe = {"at": 0, "ok": None}
_mysql_probe_lock = threading.Lock()


def source_config(cfg, source_id):
    for source in (cfg or {}).get("sources") or []:
        if source.get("id") == source_id:
            return source
    return {}


def load_config(path=None):
    path = path or DEFAULT_CONFIG_PATH
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def apply_config(cfg):
    global CONFIG, CATEGORY, CATEGORY_URL, SHOP_ORIGIN
    CONFIG = cfg or {}
    hobby = source_config(CONFIG, "hobbyland")
    if hobby:
        SHOP_ORIGIN = hobby.get("origin") or SHOP_ORIGIN
        CATEGORY = hobby.get("category") or CATEGORY
        CATEGORY_URL = hobby.get("fallback_url") or CATEGORY_URL


def _strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return " ".join(text.split())


def ssl_context():
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        try:
            ctx.load_default_certs()
        except Exception:
            pass
        return ctx


def stock_status(item):
    if not item:
        return "unknown"
    if item.get("in_stock") is True:
        return "in_stock"
    if item.get("in_stock") is False:
        return "out_of_stock"
    stock = item.get("stock")
    if isinstance(stock, (int, float)) and not isinstance(stock, bool):
        return "in_stock" if stock > 0 else "out_of_stock"
    if item.get("available") is True:
        return "in_stock"
    if item.get("available") is False:
        return "out_of_stock"
    return "unknown"


def _absolute_image_url(val):
    text = str(val or "").strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://")):
        return text
    if text.startswith("storage/"):
        return HOBBYLAND_STATIC_ORIGIN + text
    return ""


def _safe_image_name(value):
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "item")).strip("._")
    return (text or "item")[:80]


class _GoNoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe_go_url(url, timeout=8):
    url = str(url or "").strip()
    if not url.startswith("https://"):
        return False
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
    )
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl_context()),
        _GoNoRedirect(),
    )
    try:
        with opener.open(req, timeout=timeout) as resp:
            return 200 <= int(getattr(resp, "status", 0) or 0) < 400
    except urllib.error.HTTPError as exc:
        if 200 <= int(exc.code) < 400:
            return True
    except Exception:
        pass
    try:
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "-A",
                USER_AGENT,
                "--max-time",
                str(int(timeout)),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
        )
        if proc.returncode != 0:
            return False
        return 200 <= int(proc.stdout.strip() or 0) < 400
    except Exception:
        return False


def cache_product_image(shop_id, item, prefetch=False, pause=0):
    return product_image_path(shop_id, (item or {}).get("sku") or (item or {}).get("link"))


def is_preview_crawler(user_agent):
    ua = (user_agent or "").lower()
    return any(
        token in ua
        for token in (
            "facebookexternalhit",
            "facebot",
            "meta-externalagent",
            "telegrambot",
            "twitterbot",
            "slackbot",
            "discordbot",
        )
    )


def page_canonical(path):
    return SITE_ORIGIN + (path or "/")


def product_seo_description(item, fallback=""):
    raw = (item or {}).get("description") or ""
    text = _strip_html(html.unescape(str(raw)))
    if not text:
        text = str(fallback or "").strip()
    if len(text) > SEO_DESC_MAX:
        text = text[: SEO_DESC_MAX - 1].rstrip() + "…"
    return text


def product_url(item):
    link = item.get("link") or ""
    if link.startswith("http"):
        return link
    return (item.get("origin") or SHOP_ORIGIN) + link


def go_path(shop_id, sku):
    return "/go/%s/%s" % (
        urllib.parse.quote(str(shop_id or ""), safe="-"),
        urllib.parse.quote(str(sku or ""), safe="-._~"),
    )


def go_query(shop_id, sku, source=None):
    params = []
    source = str(source or "").strip().lower()
    if source:
        params.append(("from", source))
        content = "%s-%s" % (shop_id, sku)
        params.extend(
            [
                ("utm_source", source),
                ("utm_medium", "notify"),
                ("utm_campaign", "stock_alert"),
                ("utm_content", content),
            ]
        )
    return urllib.parse.urlencode(params)


def go_href(shop_id, sku, source=None):
    url = SITE_ORIGIN + go_path(shop_id, sku)
    query = go_query(shop_id, sku, source=source)
    if query:
        url += "?" + query
    return url


def parse_go_path(path):
    parsed = urllib.parse.urlparse(path or "")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[0] != "go":
        return None
    shop_id = urllib.parse.unquote(parts[1]).strip()
    sku = urllib.parse.unquote("/".join(parts[2:])).strip()
    if not shop_id or not sku or shop_id == "all":
        return None
    if ".." in shop_id or ".." in sku:
        return None
    return shop_id, sku


def go_shop_landing_id(path):
    parts = [part for part in urllib.parse.urlparse(path or "").path.split("/") if part]
    if len(parts) != 2 or parts[0] != "go":
        return None
    shop_id = urllib.parse.unquote(parts[1]).strip()
    if shop_id != GO_HOME_SEO_SHOP:
        return None
    return shop_id


def home_seo_description():
    return THREADS_SUBSCRIBE_DESC + " 可經 Threads、Discord、Telegram 收通知。"


def home_seo_go_target(shop_id=GO_HOME_SEO_SHOP):
    shop = source_config(CONFIG or {}, shop_id)
    dest = shop.get("fallback_url") or "https://www.buymarkettoy.com/categories/beyblade"
    og = seo_image_url()
    return {
        "title": SITE_BRAND,
        "dest": dest,
        "image": og,
        "og_image": og,
        "price": "",
        "status": "",
        "description": home_seo_description(),
    }


def wrap_notify_item_links(items, shop_id="uat", source=None, warm=False, probe=None):
    check = probe if probe is not None else probe_go_url
    source = str(source or "").strip().lower()
    out = []
    for item in items or []:
        row = dict(item)
        sku = str(row.get("sku") or UAT_GO_SKU)
        sid = str(row.get("shop_id") or shop_id or UAT_GO_SHOP)
        hop = go_href(sid, sku, source=source)
        ready = (not warm) or check(hop)
        if ready:
            row["link"] = hop
        out.append(row)
    return out


def go_canonical_url(shop_id, sku):
    return SITE_ORIGIN + go_path(shop_id, sku)


def go_request_url(path, query=""):
    url = SITE_ORIGIN + path
    qs = str(query or "").strip().lstrip("?")
    if qs:
        url += "?" + qs
    return url


def test_product_items():
    return [
        {
            "title": "Test notification — Discord is connected.",
            "price": "199.00",
            "sku": UAT_GO_SKU,
            "shop_id": UAT_GO_SHOP,
            "link": CATEGORY_URL,
            "in_stock": True,
            "description": "Hobbyland 爆旋陀螺新品預訂分類，官方授權香港代理商品。",
        }
    ]


def go_page_target(shop_id, sku, items=None):
    shop_id = str(shop_id or "")
    sku = str(sku or "")
    if shop_id == UAT_GO_SHOP and sku in (UAT_GO_SKU, "preview", "card"):
        item = dict((test_product_items() or [{}])[0])
        if sku != UAT_GO_SKU:
            item["sku"] = sku
            item["title"] = SITE_BRAND
        return go_target_from_item(item, shop_id)
    products = items if items is not None else load_shop_products_for_shop_id(shop_id)
    for item in products or []:
        if str(item.get("sku") or "") != sku:
            continue
        return go_target_from_item(item, shop_id)
    return None


def shopline_og_image_url(image):
    parsed = urllib.parse.urlparse(str(image or "").strip())
    if parsed.netloc.lower() != "shoplineimg.com":
        return ""
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 3:
        return ""
    shop, image_id = parts[0], parts[1]
    if "." in shop or "." in image_id or ".." in shop or ".." in image_id:
        return ""
    fmt = str(
        (urllib.parse.parse_qs(parsed.query).get("source_format") or [""])[0]
    ).lower()
    last = parts[-1].lower()
    name = "1200x.png" if fmt == "png" or last.endswith(".png") else "1200x.jpeg"
    return "https://shoplineimg.com/%s/%s/%s" % (shop, image_id, name)


def go_og_image_url(item, shop_id=""):
    item = item or {}
    rel = str(item.get("image_path") or "").replace("\\", "/")
    if not (rel.startswith("images/") and ".." not in rel):
        sku = item.get("sku") or ""
        rel = product_image_path(shop_id, sku) if shop_id and sku else ""
    if rel.startswith("images/") and ".." not in rel:
        dest = os.path.join(DATA_DIR, rel)
        if os.path.isfile(dest) and os.path.getsize(dest) >= IMAGE_MIN_CACHE_BYTES:
            return cdn_image_url("/" + rel) + "?v=" + str(int(os.path.getmtime(dest)))
    return seo_image_url()


def go_target_from_item(item, shop_id=""):
    item = item or {}
    dest = item.get("url") or product_url(item)
    if not dest:
        return None
    image = item.get("image") or product_image_url(item) or ""
    if image.startswith("/") and not image.startswith("//"):
        image = SITE_ORIGIN + image
    if not image:
        image = seo_image_url()
    status = item.get("status_label") or status_text(product_stock_key(item))
    return {
        "title": item.get("title") or item.get("sku") or SITE_BRAND,
        "dest": dest,
        "image": image,
        "og_image": go_og_image_url(item, shop_id),
        "price": item.get("price") or "",
        "status": status,
        "description": product_seo_description(item),
    }


def go_http_result(path, query="", cookie="", remember=False, force_store=False, skip_path=None, user_agent=""):
    from site_pages import render_go_bounce_html, render_go_html

    landing = go_shop_landing_id(path)
    if landing:
        shop_id, sku = landing, ""
        target = home_seo_go_target(shop_id)
    else:
        parsed = parse_go_path(path)
        if not parsed:
            return {"status": 404}
        shop_id, sku = parsed
        target = go_page_target(shop_id, sku)
    if not target:
        return {"status": 404}
    if shop_id and shop_id != UAT_GO_SHOP and sku and is_preview_crawler(user_agent):
        item = {"sku": sku, "image": target.get("image")}
        cache_product_image(shop_id, item, prefetch=True)
        target = dict(target)
        target["og_image"] = go_og_image_url(item, shop_id)
    qs = urllib.parse.parse_qs(query or "")
    source = str((qs.get("from") or [""])[0] or "").strip().lower()
    bounce = remember or force_store or source in ("discord", "telegram", "macos")
    page_url = go_request_url(path, query)
    return {
        "status": 200,
        "html": (
            render_go_bounce_html(target, shop_id, sku, page_url=page_url)
            if bounce
            else render_go_html(target, shop_id, sku, page_url=page_url)
        ),
        "location": target["dest"],
        "cache": GO_CACHE_CONTROL,
    }


def product_image_url(item):
    item = item or {}
    for key in (
        "image",
        "image_url",
        "img",
        "pic",
        "pic1",
        "pic2",
        "photo",
        "thumbnail",
        "PicUrl",
        "ImageUrl",
        "PictureUrl",
    ):
        val = item.get(key)
        if isinstance(val, str):
            url = _absolute_image_url(val)
            if url:
                return url
        if isinstance(val, dict):
            src = val.get("src") or val.get("url") or ""
            url = _absolute_image_url(src)
            if url:
                return url
    images = item.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, str):
            url = _absolute_image_url(first)
            if url:
                return url
        if isinstance(first, dict):
            src = first.get("src") or first.get("url") or first.get("thumbnail") or ""
            url = _absolute_image_url(src)
            if url:
                return url
    return ""


def product_image_path(shop_id, sku):
    return "images/%s/%s.jpg" % (_safe_image_name(shop_id), _safe_image_name(sku))


def status_text(status):
    return {
        "in_stock": "有貨",
        "out_of_stock": "缺貨",
        "unknown": "未知",
        None: "無",
    }.get(status, "未知")


def status_change_text(prev, current, event="new"):
    if event == "new" or not prev:
        return "無 → %s" % status_text(current)
    return "%s → %s" % (status_text(prev), status_text(current))


def _as_stock_status(value):
    if value in ("in_stock", "out_of_stock", "unknown", None):
        return value
    return {
        "有貨": "in_stock",
        "缺貨": "out_of_stock",
        "售罄": "out_of_stock",
        "未知": "unknown",
        "無": None,
    }.get(str(value), "unknown")


def crosses_in_stock_statuses(prev, current):
    return (_as_stock_status(prev) == "in_stock") != (_as_stock_status(current) == "in_stock")


def history_row_crosses_in_stock(row):
    row = row or {}
    prev = row.get("from")
    current = row.get("to")
    if prev not in (None, "") or current not in (None, ""):
        return crosses_in_stock_statuses(prev, current)
    change = str(row.get("change") or "")
    if " → " not in change:
        return False
    left, right = change.split(" → ", 1)
    return crosses_in_stock_statuses(left.strip(), right.strip())


def now_stamp():
    return datetime.now(HKT_TZ).strftime("%Y-%m-%d %H:%M:%S")


def product_line_fields(item):
    text = " ".join(
        str(item.get(key) or "")
        for key in ("title", "sku", "name")
    )
    match = LINE_MODEL_RE.search(text)
    if not match:
        return {"model": "", "tag": "other"}
    return {"model": match.group(1).upper(), "tag": match.group(2).upper()}


def shop_id_from_state_path(path):
    name = os.path.splitext(os.path.basename(path or ""))[0]
    if name == "seen_skus":
        return "hobbyland"
    if name.endswith("_seen_skus"):
        return name[: -len("_seen_skus")]
    return name or "unknown"


def mysql_settings():
    storage = (CONFIG or {}).get("storage") or {}
    mysql = storage.get("mysql") or {}
    return {
        "enabled": bool(mysql.get("enabled")),
        "host": mysql.get("host") or "127.0.0.1",
        "port": int(mysql.get("port") or 3306),
        "user": mysql.get("user") or "watch",
        "password": mysql.get("password") or "",
        "database": mysql.get("database") or "beyblade_watch",
    }


def _stamp_text(value):
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    text = str(value).replace("T", " ")
    return text or None


def state_from_sku_rows(rows):
    skus = []
    stock = {}
    times = {}
    products = []
    category = ""
    updated_at = ""
    for row in rows or []:
        sku = row.get("sku")
        if not sku:
            continue
        skus.append(sku)
        if row.get("stock"):
            stock[sku] = row["stock"]
        changed = _stamp_text(row.get("stock_changed_at"))
        if changed:
            times[sku] = changed
        if row.get("category"):
            category = row["category"]
        if row.get("updated_at"):
            updated_at = _stamp_text(row["updated_at"]) or ""
        title = row.get("title") or ""
        url = row.get("url") or ""
        price = row.get("price") or ""
        image = row.get("image") or ""
        image_path = row.get("image_path") or ""
        description = row.get("description") or ""
        line = product_line_fields(
            {
                "title": title,
                "sku": sku,
                "model": row.get("model") or "",
                "tag": row.get("tag") or "",
            }
        )
        model = row.get("model") or line["model"]
        tag = row.get("tag") or line["tag"] or "other"
        if title or url or price or image or image_path or description:
            status = row.get("stock") or "unknown"
            prod = {
                "sku": sku,
                "title": title or sku,
                "price": price,
                "url": url,
                "status": status,
                "status_label": status_text(status),
                "model": model,
                "tag": tag or "other",
            }
            if image:
                prod["image"] = image
            if image_path:
                prod["image_path"] = image_path
            if description:
                prod["description"] = description
            products.append(prod)
    payload = {"skus": skus, "stock": stock, "stock_changed_at": times}
    if category:
        payload["category"] = category
    if updated_at:
        payload["updated_at"] = updated_at
    if products:
        payload["products"] = products
    return payload


def mysql_connect():
    import pymysql

    cfg = mysql_settings()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
    )


def filter_notify_history(rows, shop_id="", model="", shops=None):
    shop_id = str(shop_id or "")
    model = str(model or "").upper()
    label = ""
    if shop_id:
        for shop in shops or []:
            if str(shop.get("id") or "") == shop_id:
                label = str(shop.get("label") or "")
                break
    out = []
    for row in rows or []:
        if shop_id:
            rid = str(row.get("shop_id") or "")
            rshop = str(row.get("shop") or "")
            if rid != shop_id and rshop != shop_id and (not label or rshop != label):
                continue
        if model:
            if str(row.get("model") or "").upper() != model and str(row.get("tag") or "").upper() != model:
                continue
        out.append(row)
    return out


def notify_event_as_history(event):
    event = event or {}
    if not event.get("model"):
        line = product_line_fields({"title": event.get("title") or "", "sku": event.get("sku") or ""})
        event = dict(event)
        event["model"] = line.get("model") or ""
        event.setdefault("tag", line.get("tag") or "")
    return event


def load_notify_history_jsonl(path=None, limit=100, shop_id="", model="", shops=None):
    path = path or EVENT_LOG_PATH
    if not os.path.isfile(path):
        return []
    newest = deque(maxlen=400)
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            text = raw.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except ValueError:
                continue
            if event.get("event") not in NOTIFY_EVENT_KINDS:
                continue
            newest.append(notify_event_as_history(event))
    rows = list(reversed(newest))
    return filter_notify_history(rows, shop_id, model, shops)[:limit]


def load_notify_history_mysql(limit=100, shop_id="", model=""):
    conn = mysql_connect()
    try:
        sql = (
            "SELECT at, shop_id, shop, event, sku, title, `model`, `tag`, price, url, `change`, image, image_path "
            "FROM notify_history"
        )
        args = []
        where = []
        if shop_id:
            where.append("shop_id = %s")
            args.append(shop_id)
        if model:
            where.append("(`model` = %s OR `tag` = %s)")
            args.extend([model, model])
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT %s"
        args.append(int(limit))
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return list(cur.fetchall() or [])
    finally:
        conn.close()


def load_notify_history(limit=100, shop_id="", model="", shops=None):
    if mysql_settings().get("enabled"):
        try:
            return load_notify_history_mysql(limit, shop_id, model)
        except Exception as exc:
            print("MySQL notify_history load failed: %s" % exc, file=sys.stderr)
    return load_notify_history_jsonl(limit=limit, shop_id=shop_id, model=model, shops=shops)


def notify_at_date(row):
    text = str((row or {}).get("at") or "").strip()
    return text[:10] if len(text) >= 10 else ""


def notify_day_label(day, today):
    if not day:
        return ""
    try:
        parsed = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        return day
    if parsed == today:
        return "今天"
    if parsed == today - timedelta(days=1):
        return "昨天"
    return day


def filter_index_notifies(rows, now=None, days=HISTORY_NOTIFY_DAYS, limit=None, in_stock_only=True):
    now = now or datetime.now(HKT_TZ)
    today = now.date() if hasattr(now, "date") else now
    cutoff = today - timedelta(days=int(days) - 1)
    out = []
    for row in rows or []:
        if in_stock_only and not history_row_crosses_in_stock(row):
            continue
        day = notify_at_date(row)
        if day:
            try:
                parsed = datetime.strptime(day, "%Y-%m-%d").date()
            except ValueError:
                out.append(row)
                continue
            if parsed < cutoff or parsed > today:
                continue
        out.append(row)
    if limit is not None:
        return out[: int(limit)]
    return out


def load_index_notifies(shops=None, now=None):
    rows = load_notify_history(limit=INDEX_NOTIFY_SCAN, shops=shops)
    return filter_index_notifies(rows, now=now, limit=INDEX_NOTIFY_LIMIT)


def _blank_image_value(val):
    return str(val or "").strip().lower() in ("", "none", "null", "undefined")


def lookup_sku_image_fields(shop_id, sku, cfg=None):
    shop_id = str(shop_id or "")
    sku = str(sku or "")
    out = {"image": "", "image_path": ""}
    if not shop_id or not sku:
        return out
    if mysql_settings().get("enabled"):
        try:
            conn = mysql_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT image, image_path FROM seen_skus "
                        "WHERE shop_id = %s AND sku = %s LIMIT 1",
                        (shop_id, sku),
                    )
                    row = cur.fetchone() or {}
                    out["image"] = row.get("image") or ""
                    out["image_path"] = row.get("image_path") or ""
                    if out["image"] or out["image_path"]:
                        return out
            finally:
                conn.close()
        except Exception as exc:
            print("MySQL sku image lookup failed: %s" % exc, file=sys.stderr)
    source = find_source_by_id(shop_id, cfg)
    rel = (source or {}).get("state") or ("%s_seen_skus.json" % shop_id)
    path = rel if os.path.isabs(rel) else os.path.join(DATA_DIR, rel)
    for item in shop_products_from_state(load_state(path)):
        if str(item.get("sku") or "") != sku:
            continue
        out["image"] = item.get("image") or product_image_url(item) or ""
        out["image_path"] = item.get("image_path") or ""
        break
    return out


def history_row_for_display(row):
    item = dict(row or {})
    image = item.get("image")
    image_path = item.get("image_path")
    if _blank_image_value(image) or _blank_image_value(image_path):
        found = lookup_sku_image_fields(item.get("shop_id"), item.get("sku"))
        if _blank_image_value(image):
            image = found.get("image") or ""
        if _blank_image_value(image_path):
            image_path = found.get("image_path") or ""
    if not _blank_image_value(image):
        item["image"] = image
    else:
        item.pop("image", None)
    if not _blank_image_value(image_path):
        item["image_path"] = image_path
        return item
    shop_id = str(item.get("shop_id") or "")
    sku = str(item.get("sku") or "")
    if shop_id and sku:
        rel = product_image_path(shop_id, sku)
        if os.path.isfile(os.path.join(DATA_DIR, rel)):
            item["image_path"] = rel
        else:
            item.pop("image_path", None)
    else:
        item.pop("image_path", None)
    return item


def load_state_mysql(shop_id):
    conn = mysql_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(MYSQL_SEEN_SKUS_SELECT, (shop_id,))
            rows = cur.fetchall()
        return state_from_sku_rows(rows)
    finally:
        conn.close()


def load_error_state_mysql():
    conn = mysql_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT shop_id, message, alerted_at FROM shop_errors")
            rows = cur.fetchall()
        return error_state_from_rows(rows)
    finally:
        conn.close()


def load_state(path):
    file_state = {"skus": []}
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        file_state = {"skus": data} if isinstance(data, list) else data
    if not mysql_settings().get("enabled"):
        return file_state
    try:
        db_state = load_state_mysql(shop_id_from_state_path(path))
    except Exception as exc:
        print("MySQL load failed: %s" % exc, file=sys.stderr)
        return file_state
    if db_state.get("skus"):
        if file_state.get("products"):
            db_state["products"] = file_state["products"]
        return db_state
    return file_state


def load_error_state(path=DEFAULT_ERROR_STATE):
    file_state = {}
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        file_state = data if isinstance(data, dict) else {}
    if not mysql_settings().get("enabled"):
        return file_state
    try:
        db_state = load_error_state_mysql()
    except Exception as exc:
        print("MySQL error-state load failed: %s" % exc, file=sys.stderr)
        return file_state
    return db_state or file_state


def is_admin_host(host):
    return request_hostname(host) == ADMIN_HOST


def request_hostname(host):
    return (host or "").split("/")[0].split(":")[0].strip().lower()


def admin_config():
    return (CONFIG.get("admin") or {})


def admin_username():
    return str(admin_config().get("username") or "")


def admin_password():
    return str(admin_config().get("password") or "")


def admin_credentials_ok(username, password):
    user = "" if username is None else str(username)
    pw = "" if password is None else str(password)
    expected_user = admin_username()
    expected_password = admin_password()
    if not expected_user or not expected_password:
        return False
    try:
        return hmac.compare_digest(user, expected_user) and hmac.compare_digest(
            pw, expected_password
        )
    except Exception:
        return False


def admin_session_token():
    user = admin_username()
    password = admin_password()
    if not user or not password:
        return ""
    return hmac.new(
        password.encode("utf-8"),
        user.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def cookie_value(header, name):
    for part in str(header or "").split(";"):
        piece = part.strip()
        if not piece or "=" not in piece:
            continue
        key, val = piece.split("=", 1)
        if key == name:
            return val
    return ""


def admin_session_ok(value):
    token = str(value or "")
    if ADMIN_COOKIE_NAME + "=" in token:
        token = cookie_value(token, ADMIN_COOKIE_NAME)
    expected = admin_session_token()
    if not token or not expected:
        return False
    try:
        return hmac.compare_digest(token, expected)
    except Exception:
        return False


def admin_host_request(host, path, cookie=None):
    parsed_path = urllib.parse.urlparse(path or "").path or "/"
    admin = is_admin_host(host)
    if parsed_path in ("/login", "/notify-test"):
        if not admin:
            return "not_found"
        if parsed_path == "/login":
            return "ok"
        if not admin_session_ok(cookie):
            return "login_required"
        return "ok"
    if admin and parsed_path in ("/", "/index.html"):
        return "login_required"
    if admin and parsed_path not in STATIC_PNGS and parsed_path != "/robots.txt":
        return "not_found"
    return None


def admin_set_cookie(secure=False):
    parts = [
        "%s=%s" % (ADMIN_COOKIE_NAME, admin_session_token()),
        "Path=/",
        "HttpOnly",
        "SameSite=Lax",
        "Max-Age=2592000",
    ]
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def post_json(url, payload, timeout=20):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
            data = resp.read().decode("utf-8", "replace")
        return json.loads(data) if data.strip() else {}
    except Exception:
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "-A",
                USER_AGENT,
                "-H",
                "Content-Type: application/json",
                "-H",
                "Accept: application/json",
                "-X",
                "POST",
                url,
                "-d",
                json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "curl failed")
        return json.loads(proc.stdout) if proc.stdout.strip() else {}


def discord_cfg():
    return (CONFIG.get("notify") or {}).get("discord") or {}


def discord_webhook_url():
    notify = discord_cfg()
    return (os.environ.get("DISCORD_WEBHOOK_URL") or notify.get("webhook_url") or "").strip()


def discord_notify_enabled(kind):
    notify = discord_cfg()
    if notify.get("enabled") is False:
        return False
    if not discord_webhook_url():
        return False
    if kind == "products":
        return notify.get("send_products", True)
    if kind == "errors":
        return notify.get("send_errors", True)
    return True


def post_discord(payload, webhook_url=None):
    url = (webhook_url or discord_webhook_url()).strip()
    if not url:
        return False
    post_json(url, payload, timeout=20)
    return True


def notify_discord_text(text):
    url = discord_webhook_url()
    if not discord_notify_enabled("products") or not url or not text:
        return False
    payload = {"username": "Beyblade Watch", "content": str(text)[:2000]}
    try:
        post_discord(payload, webhook_url=url)
        return True
    except Exception as exc:
        print("Discord text notify failed: %s" % exc, file=sys.stderr)
        return False


def notify_telegram_text(text):
    if not telegram_notify_enabled("products") or not text:
        return False
    try:
        return bool(post_telegram(telegram_html(text)))
    except Exception as exc:
        print("Telegram text notify failed: %s" % exc, file=sys.stderr)
        return False


def telegram_cfg():
    return (CONFIG.get("notify") or {}).get("telegram") or {}


def telegram_bot_token():
    return (os.environ.get("TELEGRAM_BOT_TOKEN") or telegram_cfg().get("bot_token") or "").strip()


def telegram_chat_id():
    raw = os.environ.get("TELEGRAM_CHAT_ID")
    if raw is None or str(raw).strip() == "":
        raw = telegram_cfg().get("chat_id")
    return str(raw or "").strip()


def telegram_notify_enabled(kind):
    notify = telegram_cfg()
    if notify.get("enabled") is False:
        return False
    if not telegram_bot_token() or not telegram_chat_id():
        return False
    if kind == "products":
        return notify.get("send_products", True)
    if kind == "errors":
        return notify.get("send_errors", True)
    return True


def telegram_html(text):
    return html.escape(str(text or ""), quote=True)


def post_telegram(text):
    token = telegram_bot_token()
    chat_id = telegram_chat_id()
    if not token or not chat_id or not text:
        return False
    url = "https://api.telegram.org/bot%s/sendMessage" % token
    payload = {
        "chat_id": chat_id,
        "text": text[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    post_json(url, payload, timeout=20)
    return True


def notify_threads_text(text):
    if not threads_notify_enabled("products") or not text:
        return False
    try:
        post_threads(text)
        return True
    except Exception as exc:
        print("Threads text notify failed: %s" % exc, file=sys.stderr)
        return False


def threads_cfg():
    return (CONFIG.get("notify") or {}).get("threads") or {}


def threads_user_id():
    return (os.environ.get("THREADS_USER_ID") or threads_cfg().get("user_id") or "").strip()


def threads_access_token():
    return (
        os.environ.get("THREADS_ACCESS_TOKEN") or threads_cfg().get("access_token") or ""
    ).strip()


def threads_notify_enabled(kind):
    notify = threads_cfg()
    if kind != "products":
        return False
    if notify.get("enabled") is False:
        return False
    if not threads_user_id() or not threads_access_token():
        return False
    return notify.get("send_products", True)


def threads_publish_url():
    user_id = threads_user_id()
    if not user_id:
        return ""
    return "https://graph.threads.net/v1.0/%s/threads" % urllib.parse.quote(user_id, safe="")


def post_threads(text):
    create = post_json(
        threads_publish_url(),
        {
            "media_type": "TEXT",
            "text": str(text or "")[:500],
            "auto_publish_text": "true",
            "access_token": threads_access_token(),
        },
        timeout=20,
    )
    creation_id = create.get("id") if isinstance(create, dict) else ""
    if not creation_id:
        raise RuntimeError("Threads create did not return id")
    publish_url = threads_publish_url() + "_publish"
    post_json(
        publish_url,
        {"creation_id": creation_id, "access_token": threads_access_token()},
        timeout=20,
    )
    return True


def threads_subscribe_footer():
    return "\n".join([THREADS_SUBSCRIBE_ASK, SITE_ORIGIN.rstrip("/") + SUBSCRIBE_PATH])


def send_admin_channel(channel, message):
    if channel == "discord":
        return notify_discord_text(message)
    if channel == "telegram":
        return notify_telegram_text(message)
    if channel == "threads":
        return notify_threads_text(message)
    return False


def run_web_notify_test(body, authenticated=False):
    body = body or {}
    if not authenticated:
        return 401, {"ok": False, "sent": False, "message": "Login required"}
    message = str(body.get("message") or "").strip()
    if not message:
        return 400, {"ok": False, "sent": False, "message": "Message required"}
    channel = str(body.get("channel") or "all").strip().lower()
    if channel == "all":
        targets = ("discord", "telegram", "threads")
    elif channel in ("discord", "telegram", "threads"):
        targets = (channel,)
    else:
        return 400, {"ok": False, "sent": False, "message": "Unknown channel"}
    names = {"discord": "Discord", "telegram": "Telegram", "threads": "Threads"}
    sent_names = []
    skipped = []
    for target in targets:
        if send_admin_channel(target, message):
            sent_names.append(names[target])
        else:
            skipped.append("%s is not configured" % names[target])
    if sent_names:
        text = "Sent to " + ", ".join(sent_names)
        if skipped:
            text += ". " + "; ".join(skipped)
        return 200, {"ok": True, "sent": True, "message": text}
    return 200, {
        "ok": True,
        "sent": False,
        "message": "; ".join(skipped) or "Not sent",
    }


def status_settings():
    st = (CONFIG or {}).get("status") or {}
    return {
        "enabled": bool(st.get("enabled")),
        "host": st.get("host") or "127.0.0.1",
        "port": int(st.get("port") or 8080),
        "token": str(st.get("token") or "").strip(),
    }


def reset_status_caches():
    with _page_cache_lock:
        _page_cache.clear()
    with _mysql_probe_lock:
        _mysql_probe["at"] = 0
        _mysql_probe["ok"] = None


def listing_state_fingerprint(data_dir=None):
    data_dir = data_dir or DATA_DIR
    parts = []
    try:
        names = os.listdir(data_dir)
    except OSError:
        return ""
    for name in sorted(names):
        if not (
            name == "seen_skus.json"
            or name.endswith("_seen_skus.json")
            or name == os.path.basename(STATUS_PATH)
            or name == os.path.basename(NOTIFY_HISTORY_PATH)
        ):
            continue
        path = os.path.join(data_dir, name)
        try:
            st = os.stat(path)
        except OSError:
            continue
        parts.append("%s:%s:%s" % (name, int(st.st_mtime), st.st_size))
    return "|".join(parts)


def refresh_status_pages_if_listings_changed(prev="", data_dir=None):
    current = listing_state_fingerprint(data_dir)
    if prev and current != prev:
        reset_status_caches()
    return current


def start_listing_watch_loop(interval=None, stop=None, data_dir=None):
    interval = LISTING_WATCH_INTERVAL if interval is None else interval

    def run():
        prev = listing_state_fingerprint(data_dir)
        while True:
            if stop is not None and stop.wait(interval):
                return
            if stop is None:
                time.sleep(interval)
            prev = refresh_status_pages_if_listings_changed(prev, data_dir=data_dir)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def cached_bytes(key, builder, ttl=PAGE_CACHE_TTL, now=time.time):
    t = now()
    with _page_cache_lock:
        hit = _page_cache.get(key)
        if hit and hit[0] > t:
            return hit[1]
    body = builder()
    with _page_cache_lock:
        _page_cache[key] = (t + ttl, body)
    return body


def mysql_ok_cached(now=time.time):
    if not mysql_settings().get("enabled"):
        return None
    t = now()
    with _mysql_probe_lock:
        if t - _mysql_probe["at"] < MYSQL_PROBE_TTL and _mysql_probe["at"]:
            return _mysql_probe["ok"]
    try:
        conn = mysql_connect()
        conn.close()
        ok = True
    except Exception:
        ok = False
    with _mysql_probe_lock:
        _mysql_probe["at"] = t
        _mysql_probe["ok"] = ok
    return ok


def build_watcher_status(cfg=None):
    cfg = cfg if cfg is not None else CONFIG
    errors = load_error_state()
    shops = []
    ok = True
    mysql_ok = mysql_ok_cached()
    if mysql_ok is False:
        ok = False
    for source in cfg.get("sources") or []:
        label = source.get("label") or source.get("id") or "shop"
        rel = source.get("state") or ("%s_seen_skus.json" % (source.get("id") or "source"))
        path = rel if os.path.isabs(rel) else os.path.join(DATA_DIR, rel)
        state = load_state(path)
        stock = state.get("stock") or {}
        in_count = sum(1 for value in stock.values() if value == "in_stock")
        out_count = sum(1 for value in stock.values() if value == "out_of_stock")
        err = errors.get(label)
        enabled = source.get("enabled", True)
        if err and enabled:
            ok = False
        shops.append(
            {
                "id": source.get("id") or "",
                "label": label,
                "enabled": enabled,
                "sku_count": len(state.get("skus") or []),
                "in_stock": in_count,
                "out_of_stock": out_count,
                "updated_at": state.get("updated_at") or "",
                "error": (err or {}).get("message") if err else None,
            }
        )
    return {
        "checked_at": now_stamp(),
        "ok": ok,
        "mysql": mysql_ok,
        "shops": shops,
    }


def status_request_redirect(path):
    parsed = urllib.parse.urlparse(path or "")
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    had_key = any(key == "key" for key, _ in pairs)
    kept = [(key, val) for key, val in pairs if key != "key"]
    dest_path = parsed.path or "/"
    if dest_path in ("/in-stock", "/instock"):
        extra = [(key, val) for key, val in kept if key != "stock"]
        dest = shop_products_href("all", "in_stock")
        if extra:
            dest += "&" + urllib.parse.urlencode(extra)
        return dest
    if not had_key:
        return None
    dest = dest_path
    if kept:
        dest += "?" + urllib.parse.urlencode(kept)
    return dest


def cdn_image_url(path):
    origin = (os.environ.get("BEYBLADE_CDN_ORIGIN") or CDN_ORIGIN).rstrip("/")
    path = "/" + str(path or "").lstrip("/")
    if origin in ("", "local", "-"):
        return path
    return origin + path


def seo_image_url():
    return cdn_image_url(OG_IMAGE_PATH)


def shop_products_from_state(state):
    state = state or {}
    products = state.get("products")
    if products:
        out = []
        for item in products:
            row = dict(item)
            row.update(product_line_fields(row))
            out.append(row)
        return out
    stock = state.get("stock") or {}
    items = []
    for sku in state.get("skus") or []:
        status = stock.get(sku) or "unknown"
        item = {
            "sku": sku,
            "title": sku,
            "price": "",
            "url": "",
            "status": status,
            "status_label": status_text(status),
        }
        item.update(product_line_fields(item))
        items.append(item)
    return items


def find_source_by_id(shop_id, cfg=None):
    for source in (cfg or CONFIG or {}).get("sources") or []:
        if source.get("id") == shop_id:
            return source
    return None


def site_group_key(source):
    origin = str((source or {}).get("origin") or "").strip().rstrip("/").lower()
    if origin:
        return origin
    return str((source or {}).get("id") or "")


def sources_for_shop_page(shop_id, cfg=None):
    cfg = cfg if cfg is not None else CONFIG
    sources = list((cfg or {}).get("sources") or [])
    if shop_id == "all":
        return [source for source in sources if source.get("enabled", True)]
    source = find_source_by_id(shop_id, cfg)
    if not source:
        return []
    key = site_group_key(source)
    return [item for item in sources if site_group_key(item) == key]


def shop_page_meta(shop_id, cfg=None):
    if shop_id == "all":
        return {"id": "all", "label": "全部"}
    sources = sources_for_shop_page(shop_id, cfg)
    if not sources:
        return None
    first = sources[0]
    return {
        "id": first.get("id") or shop_id,
        "label": first.get("label") or first.get("id") or shop_id,
    }


def _sum_count(left, right):
    try:
        return int(left or 0) + int(right or 0)
    except (TypeError, ValueError):
        return left if left is not None else right


def _later_stamp(left, right):
    left = str(left or "")
    right = str(right or "")
    if not left:
        return right
    if not right:
        return left
    return right if right > left else left


def display_status_shops(shops, cfg=None):
    cfg = cfg if cfg is not None else CONFIG
    groups = []
    by_key = {}
    for shop in shops or []:
        if (shop.get("id") or "") == "all":
            continue
        source = find_source_by_id(shop.get("id"), cfg) or {}
        key = site_group_key(source) or shop.get("id") or shop.get("label")
        existing = by_key.get(key)
        if existing is None:
            row = dict(shop)
            grouped = sources_for_shop_page(shop.get("id"), cfg)
            first = grouped[0] if grouped else source
            if first.get("id"):
                row["id"] = first.get("id")
            if first.get("label"):
                row["label"] = first.get("label")
            by_key[key] = row
            groups.append(row)
            continue
        existing["sku_count"] = _sum_count(existing.get("sku_count"), shop.get("sku_count"))
        existing["in_stock"] = _sum_count(existing.get("in_stock"), shop.get("in_stock"))
        existing["out_of_stock"] = _sum_count(existing.get("out_of_stock"), shop.get("out_of_stock"))
        existing["updated_at"] = _later_stamp(existing.get("updated_at"), shop.get("updated_at"))
        if shop.get("error") and not existing.get("error"):
            existing["error"] = shop.get("error")
        if not existing.get("enabled", True) and shop.get("enabled", True):
            existing["enabled"] = True
    all_row = {
        "id": "all",
        "label": "全部",
        "enabled": True,
        "sku_count": 0,
        "in_stock": 0,
        "out_of_stock": 0,
        "updated_at": "",
        "error": None,
    }
    for row in groups:
        all_row["sku_count"] = _sum_count(all_row["sku_count"], row.get("sku_count"))
        all_row["in_stock"] = _sum_count(all_row["in_stock"], row.get("in_stock"))
        all_row["out_of_stock"] = _sum_count(all_row["out_of_stock"], row.get("out_of_stock"))
        all_row["updated_at"] = _later_stamp(all_row["updated_at"], row.get("updated_at"))
    return [all_row] + groups


def load_shop_products_for_source(source):
    rel = (source or {}).get("state") or ("%s_seen_skus.json" % ((source or {}).get("id") or "source"))
    path = rel if os.path.isabs(rel) else os.path.join(DATA_DIR, rel)
    return shop_products_from_state(load_state(path))


def site_display_label(source, cfg=None):
    source = source or {}
    grouped = sources_for_shop_page(source.get("id"), cfg)
    first = grouped[0] if grouped else source
    return str(first.get("label") or source.get("label") or source.get("id") or "shop")


def load_shop_products_for_shop_id(shop_id, cfg=None):
    sources = sources_for_shop_page(shop_id, cfg)
    show_shop = shop_id == "all" or len(sources) > 1
    items = []
    seen = set()
    for source in sources:
        sid = str(source.get("id") or "")
        label = site_display_label(source, cfg)
        for item in load_shop_products_for_source(source):
            row = dict(item)
            if show_shop:
                row["shop_label"] = label
            sku = str(row.get("sku") or "")
            key = "%s::%s" % (sid, sku) if shop_id == "all" else sku
            if key in seen:
                continue
            seen.add(key)
            items.append(row)
    return items


def shop_products_href(shop_id, stock=None, tag=None):
    path = "/shop/%s" % urllib.parse.quote(str(shop_id or ""), safe="-")
    query = []
    if stock == "in_stock":
        query.append(("stock", "in"))
    elif stock == "out_of_stock":
        query.append(("stock", "out"))
    if tag in ("CX", "BX", "UX", "other"):
        query.append(("tag", tag))
    if query:
        return path + "?" + urllib.parse.urlencode(query)
    return path


def stock_filter_from_query(query):
    raw = ""
    for key, val in urllib.parse.parse_qsl(query or "", keep_blank_values=True):
        if key == "stock":
            raw = (val or "").strip().lower()
            break
    if raw in ("in", "in_stock"):
        return "in_stock"
    if raw in ("out", "out_of_stock"):
        return "out_of_stock"
    return ""


def tag_filter_from_query(query):
    raw = ""
    for key, val in urllib.parse.parse_qsl(query or "", keep_blank_values=True):
        if key == "tag":
            raw = (val or "").strip()
            break
    if raw.lower() == "other":
        return "other"
    upper = raw.upper()
    if upper in ("CX", "BX", "UX"):
        return upper
    return ""


def product_stock_key(item):
    item = item or {}
    key = item.get("status") or stock_status(item)
    if key in ("in_stock", "out_of_stock"):
        return key
    label = str(item.get("status_label") or "")
    if label == "有貨":
        return "in_stock"
    if label == "缺貨":
        return "out_of_stock"
    return key


def product_tag_key(item):
    tag = str((item or {}).get("tag") or "").strip()
    if tag:
        if tag.lower() == "other":
            return "other"
        return tag.upper()
    return product_line_fields(item)["tag"]


def filter_shop_products(items, stock_filter="", tag_filter=""):
    items = list(items or [])
    if stock_filter == "in_stock":
        items = [item for item in items if product_stock_key(item) == "in_stock"]
    elif stock_filter == "out_of_stock":
        items = [item for item in items if product_stock_key(item) == "out_of_stock"]
    if tag_filter:
        items = [item for item in items if product_tag_key(item) == tag_filter]
    return sorted(items, key=lambda item: 0 if product_stock_key(item) == "in_stock" else 1)


def shop_chip_shops(cfg=None):
    cfg = cfg if cfg is not None else CONFIG
    shops = []
    for source in (cfg or {}).get("sources") or []:
        if not source.get("enabled", True):
            continue
        shops.append(
            {
                "id": source.get("id") or "",
                "label": source.get("label") or source.get("id") or "shop",
                "sku_count": 0,
                "in_stock": 0,
                "out_of_stock": 0,
                "enabled": True,
            }
        )
    return [row for row in display_status_shops(shops, cfg) if row.get("id") != "all"]



def history_href(shop_id="", model=""):
    pairs = []
    if shop_id:
        pairs.append(("shop", shop_id))
    if model:
        pairs.append(("model", model))
    path = "/history"
    if pairs:
        path += "?" + urllib.parse.urlencode(pairs)
    return path


if os.path.isfile(DEFAULT_CONFIG_PATH):
    apply_config(load_config())
