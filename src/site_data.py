#!/usr/bin/env python3
"""Status-site config, MySQL reads, /go helpers, and admin notify tools."""
from __future__ import print_function

import hashlib
import hmac
import html
import json
import os
import re
import ssl
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

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
CONFIG_DIR = os.path.join(ROOT_DIR, "config")
DATA_DIR = os.path.join(ROOT_DIR, "data")


def resolved_data_dir():
    override = (os.environ.get("BEYBLADE_DATA_DIR") or "").strip()
    return override or DATA_DIR


def image_data_dir():
    return resolved_data_dir()


def state_file_path(rel):
    rel = rel or ""
    if os.path.isabs(rel):
        return rel
    return os.path.join(resolved_data_dir(), rel)
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "watch_config.json")
DEFAULT_ERROR_STATE = os.path.join(DATA_DIR, "watch_errors.json")
STATUS_PATH = os.path.join(DATA_DIR, "watch_status.json")
EVENT_LOG_PATH = os.path.join(DATA_DIR, "watch_events.jsonl")
NOTIFY_HISTORY_PATH = os.path.join(DATA_DIR, "notify_history.jsonl")
CONFIG = {}
DISCORD_INVITE_URL = "https://discord.gg/C8Q5gZf3y5"
TELEGRAM_INVITE_URL = "https://t.me/+mbTPVeGFBalhMjQ9"
THREADS_PROFILE_URL = "https://discord.gg/C8Q5gZf3y5"
THREADS_SUBSCRIBE_DESC = "香港爆旋陀螺到貨通知。Online舖頭 有新品、補貨、缺貨就出帖。非官方。"
THREADS_SUBSCRIBE_HINT = "Follow 我哋 Threads 之後記得撳右上角訂閱／鐘仔掣，訂閱帖文通知"
SUBSCRIBE_BUTTON_LABEL = "訂閱通知"
PAYME_URL = "https://payme.hsbc/andyhuihh"
ALIPAYHK_PATH = "/alipayhk.jpg"
SITE_BRAND = "HK BeybladeX Watch"
SITE_BRAND_SHORT = "HK BeybladeX"
SITE_ORIGIN = "https://hkbeybladex.com"
CDN_ORIGIN = "https://beybladex-cdn.andyhhh.com"
UAT_GO_SHOP = "uat"
UAT_GO_SKU = "test"
GO_HOME_SEO_SHOP = "buymarkettoy"
ADMIN_HOST = "beybladex-admin.andyhhh.com"
ADMIN_USERNAME = "andyhhh"
ADMIN_PASSWORD = "Demo1234!"
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
HTML_CACHE_CONTROL = "public, max-age=60, s-maxage=31536000"
HTML_CACHE_TAG = "beyblade-html"
CLOUDFLARE_ZONE_ID = "87a6123c82ee8531c522e97830661465"
EDGE_PURGE_MIN_GAP = 60
EDGE_PURGE_SHORT_WINDOW = 20 * 60
EDGE_PURGE_SHORT_MAX = 10
EDGE_PURGE_LONG_WINDOW = 4 * 60 * 60
EDGE_PURGE_LONG_MAX = 20
EDGE_PURGE_LOG_KEEP_DAYS = 3
EDGE_PURGE_LOG_NAME = "edge_purge.jsonl"
GO_CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-if-error=604800"
# Bump when /go preview HTML changes. Telegram caches each full URL.
GO_LINK_VERSION = "2"
IMAGE_CACHE_CONTROL = "public, max-age=31536000, s-maxage=31536000, immutable"
PAGE_CACHE_TTL = 30
LISTING_WATCH_INTERVAL = 2
MYSQL_PROBE_TTL = 30
IMAGE_MAX_PX = 800
IMAGE_MIN_CACHE_BYTES = 2000
HOBBYLAND_STATIC_ORIGIN = "https://static.hobbylandeshop.com/"
SHOP_ORIGIN = "https://www.hobbylandeshop.com"
CATEGORY_URL = SHOP_ORIGIN + "/product-category/nproduct_booking"
SEO_DESC_MAX = 300
INDEX_NOTIFY_LIMIT = 5
HISTORY_NOTIFY_DAYS = 7
HISTORY_PAGE_DAYS = 3
INDEX_NOTIFY_SCAN = 400
NOTIFY_SRC_HK = "hk"
NOTIFY_SRC_AMAZON = "amazon"
AMAZON_NOTIFY_SHOP_IDS = frozenset({"amazon", "amazon-jp"})
FILTER_COMBO_THRESHOLD = 7
NOTIFY_EVENT_LABELS = {"new": "新品", "restock": "補貨", "sold_out": "缺貨", "price_drop": "降價"}
NOTIFY_EVENT_KINDS = ("new", "restock", "sold_out", "price_drop")
BUNDLE_DESC_HEADER = "套裝內容"
GO_NOTIFY_ALWAYS_SHOPS = frozenset({"aeoncity", "hobbydigi"})
THREADS_DEFAULT_DAILY_POST_LIMIT = 5
_threads_io_lock = threading.RLock()
THREADS_TOPIC_TAG = "爆旋陀螺X"
THREADS_SUBSCRIBE_ASK = (
    "Thread Follow 之後記得撳右上角鐘仔訂閱帖文，先可以有即時通知！\n"
    "都可以subscribe Telegram and Discord，以免Miss咗！"
)
THREADS_URL_RE = re.compile(r"https?://[^\s]+")
LINE_MODEL_RE = re.compile(
    r"(?<![A-Za-z0-9])((CX|BX|UX)-?[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?)",
    re.I,
)
MYSQL_SEEN_SKUS_SELECT = (
    "SELECT shop_id, sku, category, stock, stock_changed_at, updated_at, "
    "title, url, price, image, image_path, `model`, `tag`, description "
    "FROM seen_skus WHERE shop_id = %s ORDER BY sku"
)
DEFAULT_SKIP_PHRASES = (
    "無限邂逅",
    "MegaloMaria",
    "Megalo Maria",
    "Tomica",
    "Hiace",
    "SANRIO CHARACTERS",
    "Robosen",
    "變形金剛",
    "Transformers",
)
_page_cache = {}
_page_cache_lock = threading.Lock()
_stock_sig_cache = {}
_edge_purge_lock = threading.Lock()
_edge_purge_at = []
_edge_purge_pending = False
_mysql_probe = {"at": 0, "ok": None}
_mysql_probe_lock = threading.Lock()


def watch_config_overlay_path(path):
    root, ext = os.path.splitext(path or DEFAULT_CONFIG_PATH)
    return root + ".local" + ext


def merge_watch_config(base, overlay):
    if not isinstance(base, dict):
        base = {}
    if not isinstance(overlay, dict):
        return base
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_watch_config(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path=None):
    path = path or DEFAULT_CONFIG_PATH
    with open(path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    overlay_path = watch_config_overlay_path(path)
    if os.path.isfile(overlay_path):
        with open(overlay_path, "r", encoding="utf-8") as fh:
            overlay = json.load(fh)
        if isinstance(overlay, dict):
            cfg = merge_watch_config(cfg, overlay)
    return cfg


def apply_config(cfg):
    global CONFIG
    incoming = cfg or {}
    if incoming is CONFIG:
        return
    CONFIG.clear()
    CONFIG.update(incoming)


def skip_phrases(cfg=None):
    cfg = cfg if cfg is not None else CONFIG
    skip = ((cfg or {}).get("filter") or {}).get("skip_phrases")
    if skip is None:
        skip = DEFAULT_SKIP_PHRASES
    return tuple(str(phrase).strip() for phrase in skip if str(phrase).strip())


def scanning_rules(cfg=None):
    cfg = cfg if cfg is not None else CONFIG
    filt = (cfg or {}).get("filter") or {}
    phrases = [str(p).strip() for p in (filt.get("phrases") or ()) if str(p).strip()]
    if not phrases:
        phrases = ["beyblade", "陀螺", "爆旋"]
    codes = [str(c).strip() for c in (filt.get("line_codes") or ("UX", "CX", "BX")) if str(c).strip()]
    return {
        "phrases": phrases,
        "line_codes": codes,
        "skip_phrases": list(skip_phrases(cfg)),
    }


def is_skipped_product(item, cfg=None):
    text = " ".join(
        str((item or {}).get(key) or "")
        for key in ("title", "sku", "name")
    ).strip().lower()
    return any(phrase.lower() in text for phrase in skip_phrases(cfg) if phrase)


def source_config(cfg, source_id):
    for source in cfg.get("sources") or []:
        if source.get("id") == source_id:
            return source
    return {}


def ssl_context():
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


def post_json(url, payload):
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
        with urllib.request.urlopen(req, timeout=60, context=ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
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
            timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "curl failed")
        return json.loads(proc.stdout)


def get_bytes(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "image/*,*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=ssl_context()) as resp:
            return resp.read()
    except Exception:
        proc = subprocess.run(
            ["curl", "-sS", "-f", "-L", "-A", USER_AGENT, url],
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or b"").decode("utf-8", "replace").strip() or "curl failed")
        return proc.stdout


def _strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return " ".join(text.split())


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
                ("pv", GO_LINK_VERSION),
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


def wrap_notify_item_links(items, shop_id="uat", source=None, warm=False, probe=None):
    check = probe if probe is not None else probe_go_url
    source = str(source or "").strip().lower()
    out = []
    for item in items or []:
        row = dict(item)
        sku = str(row.get("sku") or UAT_GO_SKU)
        sid = str(row.get("shop_id") or shop_id or UAT_GO_SHOP)
        hop = go_href(sid, sku, source=source)
        ready = (not warm) or check(hop) or sid in GO_NOTIFY_ALWAYS_SHOPS
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


def go_http_result(path, query="", cookie="", remember=False, force_store=False, skip_path=None, user_agent=""):
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
        item = {
            "sku": sku,
            "image": target.get("image"),
            "image_path": target.get("image_path") or "",
        }
        cache_product_image(shop_id, item, prefetch=True)
        target = dict(target)
        target["og_image"] = go_og_image_url(item, shop_id)
    # Browsers get the loading hop. Preview crawlers get the SEO card and do not
    # redirect, so the link preview stays on this page. Cloudflare does not vary
    # /go on User-Agent, so this response must not be stored at the edge.
    # pv=2 on notify links is unchanged; Telegram still keys its own preview cache
    # by the full URL.
    del remember, force_store
    crawler = is_preview_crawler(user_agent)
    page_url = go_request_url(path, query)
    from site_pages import render_go_bounce_html, render_go_html
    return {
        "status": 200,
        "html": (
            render_go_html(target, shop_id, sku, page_url=page_url)
            if crawler
            else render_go_bounce_html(target, shop_id, sku, page_url=page_url)
        ),
        "location": target["dest"],
        "cache": "private, no-store",
    }


def _absolute_image_url(val):
    text = str(val or "").strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://")):
        return text
    if text.startswith("storage/"):
        return HOBBYLAND_STATIC_ORIGIN + text
    return ""


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


def _safe_image_name(value):
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "item")).strip("._")
    return (text or "item")[:80]


def product_image_path(shop_id, sku):
    return "images/%s/%s.jpg" % (_safe_image_name(shop_id), _safe_image_name(sku))


def usable_cached_image_bytes(data):
    raw = data or b""
    if len(raw) < IMAGE_MIN_CACHE_BYTES:
        return False
    head = raw[:200].lstrip().lower()
    if head.startswith(b"<") or b"<error>" in head or b"<html" in head:
        return False
    return True


def product_image_fetch_urls(item):
    orig = product_image_url(item) or ""
    large = shopline_og_image_url(orig)
    urls = []
    for url in (large, orig):
        if url and url not in urls:
            urls.append(url)
    return urls


def shrink_image_bytes(data, max_px=IMAGE_MAX_PX):
    from io import BytesIO
    from PIL import Image

    img = Image.open(BytesIO(data or b""))
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode in ("RGBA", "LA"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > max_px:
        img.thumbnail((max_px, max_px), Image.Resampling.BILINEAR)
    out = BytesIO()
    img.save(out, format="JPEG", quality=80, optimize=True, subsampling=0)
    return out.getvalue()


def cache_product_image(shop_id, item, prefetch=False, pause=0):
    item = item or {}
    rel = product_image_path(shop_id, item.get("sku") or item.get("link"))
    dest = os.path.join(image_data_dir(), rel)
    has_file = os.path.isfile(dest) and os.path.getsize(dest) >= IMAGE_MIN_CACHE_BYTES
    if has_file:
        item["image_path"] = rel
        return rel
    urls = product_image_fetch_urls(item)
    if not urls or not prefetch:
        return item.get("image_path") or ""
    last_exc = None
    for url in urls:
        try:
            raw = get_bytes(url)
            if not usable_cached_image_bytes(raw):
                continue
            try:
                body = shrink_image_bytes(raw)
            except Exception:
                body = raw
            if not usable_cached_image_bytes(body):
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            tmp = dest + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(body)
            os.replace(tmp, dest)
            item["image_path"] = rel
            if not item.get("image"):
                item["image"] = url
            if pause:
                time.sleep(float(pause))
            return rel
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc:
        print("Image cache failed (%s): %s" % (item.get("sku"), last_exc), file=sys.stderr)
    return item.get("image_path") or ""


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


def now_stamp():
    return datetime.now(HKT_TZ).strftime("%Y-%m-%d %H:%M:%S")


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


def sku_rows_from_state(shop_id, payload):
    payload = payload or {}
    stock = payload.get("stock") or {}
    times = payload.get("stock_changed_at") or {}
    updated = payload.get("updated_at") or ""
    category = payload.get("category") or ""
    by_sku = {}
    for item in payload.get("products") or []:
        sku = item.get("sku")
        if sku:
            by_sku[str(sku)] = item
    rows = []
    for sku in payload.get("skus") or []:
        item = by_sku.get(str(sku)) or {}
        row = {
            "shop_id": shop_id,
            "sku": sku,
            "category": category,
            "stock": stock.get(sku),
            "stock_changed_at": times.get(sku),
            "updated_at": updated,
            "title": item.get("title") or "",
            "url": item.get("url") or item.get("link") or "",
            "price": item.get("price") or "",
            "image": item.get("image") or "",
            "image_path": item.get("image_path") or "",
            "description": item.get("description") or "",
        }
        row.update(product_line_fields(item if item else {"sku": sku}))
        rows.append(row)
    return rows


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


def error_rows_from_state(state):
    rows = []
    for shop_id, rec in (state or {}).items():
        rows.append(
            {
                "shop_id": shop_id,
                "message": (rec or {}).get("message") or "",
                "alerted_at": (rec or {}).get("at") or 0,
            }
        )
    return rows


def error_state_from_rows(rows):
    out = {}
    for row in rows or []:
        out[row["shop_id"]] = {
            "message": row.get("message") or "",
            "at": float(row.get("alerted_at") or 0),
        }
    return out


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


def load_error_state(path=None):
    if not path:
        path = os.path.join(resolved_data_dir(), "watch_errors.json")
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


def _money_text(raw):
    text = re.sub(r"(?i)HKD?\s*\$?\s*", "", _strip_html(raw or "")).replace(",", "").strip()
    return text.split()[0] if text else ""


def _price_number(raw):
    text = _money_text(raw)
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def format_money_amount(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number == int(number):
        return str(int(number))
    return ("%.2f" % number).rstrip("0").rstrip(".")


def price_drop_parts(prev_price, price):
    old_n = _price_number(prev_price)
    new_n = _price_number(price)
    if old_n is None or new_n is None or old_n <= 0 or new_n >= old_n:
        return None
    delta = old_n - new_n
    pct = round(delta / old_n * 100.0, 1)
    return format_money_amount(delta), ("%g" % pct)


def price_value_text(item):
    item = item or {}
    price = item.get("price")
    if not price:
        return "—"
    base = "HK$%s" % price
    parts = price_drop_parts(item.get("prev_price"), price)
    if not parts:
        return base
    amount, pct = parts
    new_price = format_money_amount(_price_number(price)) or price
    return "HK$%s → HK$%s（↓ HK$%s / %s%%）" % (
        item.get("prev_price"),
        new_price,
        amount,
        pct,
    )


def notify_kind_label(event, item=None):
    if event == "new":
        status = stock_status(item)
        if status == "in_stock":
            return "新品有貨"
        if status == "out_of_stock":
            return "新品缺貨"
        return "新品"
    if event == "restock":
        return "補貨"
    if event == "sold_out":
        return "變為缺貨"
    if event == "price_drop":
        return "降價"
    return "新品"


def parse_bundle_description(text):
    text = str(text or "").strip()
    if not text.startswith(BUNDLE_DESC_HEADER):
        return []
    lines = []
    for row in text.splitlines()[1:]:
        row = row.strip()
        if not row:
            continue
        match = re.match(r"^(.*)\s+HK\$(\S+)$", row)
        if match:
            lines.append({"name": match.group(1).strip(), "price": match.group(2)})
        else:
            lines.append({"name": row, "price": ""})
    return lines


def item_bundle_lines(item):
    raw = (item or {}).get("bundle")
    if isinstance(raw, list):
        lines = [
            {"name": str(line.get("name") or "").strip(), "price": str(line.get("price") or "").strip()}
            for line in raw
            if isinstance(line, dict) and str(line.get("name") or "").strip()
        ]
        if lines:
            return lines
    return parse_bundle_description((item or {}).get("description"))


def bundle_notice_lines(item):
    lines = []
    for line in item_bundle_lines(item):
        name = line.get("name") or ""
        price = line.get("price") or ""
        lines.append("%s HK$%s" % (name, price) if price else name)
    return lines


_UMBRELLA_CODE_RE = re.compile(
    r"(?<![A-Za-z])(BX|CX|UX)-00(?![A-Za-z0-9])",
    re.I,
)
_SPECIFIC_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9])((BX|CX|UX)[A-Z]?-?\s?\d{2})(?=$|[^A-Za-z0-9]|(?:BX|CX|UX)(?![A-Za-z]))",
    re.I,
)
_PART_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z]{1,2}\d{1,2}-\d{2}[A-Za-z]{1,3})(?![A-Za-z0-9])"
    r"|(?<![0-9])(\d{1,2}-\d{2}[A-Za-z]{1,3})(?![A-Za-z0-9])",
    re.I,
)
# beyblade.phstudy.org keeps BX-00 / CX-00 / UX-00 as shop umbrella labels.
# Canonical ids are BXG- (retail), BXH- (event prize), BXC- (collab),
# or BXA- (campaign and character collab). BXA-02 is an alias of BXG-25.
_ALIAS_AS_CODE = {
    "EVANGELION": ("BXG-57", "CX"),
    "TIGA": ("BXG-70", "CX"),
    "LAUNCHER": ("BXG-62", "BX"),
    "SUSHIRO": ("BXA-01", "BX"),
    "CAPTAIN": ("BXA-03", "BX"),
    "HULK": ("BXA-03", "BX"),
    "MILES": ("BXA-04", "BX"),
    "GOBLIN": ("BXA-04", "BX"),
    "MARVEL": ("BXA-04", "BX"),
    "KENOBI": ("BXA-05", "BX"),
    "GRIEVOUS": ("BXA-05", "BX"),
    "CHEWBACCA": ("BXA-06", "BX"),
    "TROOPER": ("BXA-06", "BX"),
}
# phstudy viewer.js BOX_PRODUCT_ALIASES
_PROMO_REWRITES = {
    "BXA-02": ("BXG-25", "UX"),
}
_ALIAS_PART_AS_CODE = {
    ("DRAGOON", "2-60C"): ("BXG-09", "BX"),
    ("COBALT", "2-60C"): ("BXG-09", "BX"),
    ("COBALT", "9-60F"): ("BXG-53", "BX"),
    ("DRANZER", "3-80T"): ("BXG-01", "BX"),
    ("GALE", "3-70RA"): ("BXG-47", "BX"),
    ("GALE", "3-70A"): ("BXG-47", "BX"),
    ("MAMMOTH", "2-80E"): ("BXG-32", "BX"),
    ("STORM", "4-60RA"): ("BXG-22", "BX"),
    ("STORM", "2-70M"): ("BXG-21", "BX"),
    ("DRIGER", "4-80P"): ("BXG-04", "BX"),
    ("LEONE", "5-60P"): ("BXG-05", "BX"),
    ("LEONE", "6-80GN"): ("BXG-20", "BX"),
    ("LEONE", "4-60A"): ("BXG-38", "CX"),
    ("XCALIBUR", "3-60GF"): ("BXG-13", "BX"),
    ("HELLS", "4-60T"): ("BXG-03", "BX"),
    ("HELLS", "3-80F"): ("BXC-02", "BX"),
    ("SCORPIO", "0-70Z"): ("BXG-61", "UX"),
    ("WIZARD", "4-55LO"): ("BXG-43", "CX"),
    ("CLOCK", "4-55S"): ("BXC-20", "UX"),
    ("SUSHIRO", "3-60F"): ("BXA-01", "BX"),
    ("CAPTAIN", "4-70GB"): ("BXA-03", "BX"),
    ("HULK", "1-80R"): ("BXA-03", "BX"),
    ("MILES", "1-60GN"): ("BXA-04", "BX"),
    ("GOBLIN", "9-80HT"): ("BXA-04", "BX"),
    ("KENOBI", "4-60P"): ("BXA-05", "BX"),
    ("GRIEVOUS", "3-80HN"): ("BXA-05", "BX"),
    ("CHEWBACCA", "4-80LF"): ("BXA-06", "BX"),
    ("TROOPER", "5-70B"): ("BXA-06", "BX"),
}
_BLACK_VARIANT_RE = re.compile(r"黑色|黑版|(?<![A-Za-z])black(?![A-Za-z])", re.I)
_KUJI_RE = re.compile(r"一番賞|一番くじ|くじ|(?<![A-Za-z])kuji|dmm\s*scratch", re.I)
_NAME_ALIASES = (
    (re.compile(r"福音戰士|evangelion|(?<![A-Za-z])eva(?![A-Za-z])", re.I), "EVANGELION"),
    (re.compile(r"烈風天馬|stormpegasis|storm\s*pegasus", re.I), "GALE"),
    (re.compile(r"暴風戰龍|暴風巨神|dragoon\s*storm|storm\s*sprigan|dragon\s*storm", re.I), "STORM"),
    (re.compile(r"翔空天馬|aero\s*pegasus|藍空力天馬", re.I), "AERO"),
    (re.compile(r"迪加|迪迦|(?<![A-Za-z])tiga(?![A-Za-z])", re.I), "TIGA"),
    (re.compile(r"朱雀戰神|dranzerspiral|(?<![A-Za-z])dranzer(?![A-Za-z])", re.I), "DRANZER"),
    (re.compile(r"鈷藍青龍|鈷藍魔龍|cobaltdragoon|cobalt\s*dragoon", re.I), "COBALT"),
    (re.compile(r"青翼白虎|(?<![A-Za-z])driger(?![A-Za-z])", re.I), "DRIGER"),
    (re.compile(r"神力聖劍|终极骑士|終極騎士|xeno\s*xcalibur|(?<![A-Za-z])xcalibur(?![A-Za-z])", re.I), "XCALIBUR"),
    (re.compile(r"巫師弧光|(?<![A-Za-z])wizard(?![A-Za-z])", re.I), "WIZARD"),
    (re.compile(r"天蠍|scorpiospear|(?<![A-Za-z])scorpio(?![A-Za-z])", re.I), "SCORPIO"),
    (re.compile(r"猛獁|狂象|mammothtusk|(?<![A-Za-z])mammoth(?![A-Za-z])", re.I), "MAMMOTH"),
    (re.compile(r"龍騎士|(?<![A-Za-z])dragoon(?![A-Za-z])", re.I), "DRAGOON"),
    (re.compile(r"獅子|レオーネ|(?<![A-Za-z])leone(?![A-Za-z])", re.I), "LEONE"),
    (re.compile(r"時鐘幻影|時鐘幽景|clock\s*mirage", re.I), "CLOCK"),
    (re.compile(r"地獄尺寸|地獄鐮刀|煉獄魔鐮|hells?\s*s(?:cythe|ize)", re.I), "HELLS"),
    (re.compile(
        r"(?:壽司郎|sushiro).{0,16}(?:翔龍神劍|dransword|dran\s*sword)"
        r"|(?:翔龍神劍|dransword|dran\s*sword).{0,16}(?:壽司郎|sushiro)",
        re.I,
    ), "SUSHIRO"),
    (re.compile(r"美國隊長|captain\s*america", re.I), "CAPTAIN"),
    (re.compile(r"紅浩克|red\s*hulk", re.I), "HULK"),
    (re.compile(r"終極蜘蛛俠|miles\s*morales", re.I), "MILES"),
    (re.compile(r"綠惡魔|green\s*goblin", re.I), "GOBLIN"),
    (re.compile(r"歐比王|obi[-\s]*wan|(?<![A-Za-z])kenobi(?![A-Za-z])", re.I), "KENOBI"),
    (re.compile(r"葛里維斯|(?<![A-Za-z])grievous(?![A-Za-z])", re.I), "GRIEVOUS"),
    (re.compile(r"丘巴卡|(?<![A-Za-z])chewbacca(?![A-Za-z])", re.I), "CHEWBACCA"),
    (re.compile(r"風暴兵|storm\s*trooper", re.I), "TROOPER"),
    (re.compile(r"蜘蛛人|蜘蛛俠|marvel|(?<![A-Za-z])miles(?![A-Za-z])", re.I), "MARVEL"),
    (re.compile(r"旋風發射器|發射器限定|(?<![A-Za-z])launcher(?![A-Za-z])", re.I), "LAUNCHER"),
)


def _canonical_model_code(code):
    code = re.sub(r"\s+", "", (code or "").upper())
    promo = re.fullmatch(r"(BXG|BXH|BXC|BXA)-?(\d{2})(?:-?(\d{2}))?", code)
    if not promo:
        return code
    suffix = ("-%s" % promo.group(3)) if promo.group(3) else ""
    normalized = "%s-%s%s" % (promo.group(1), promo.group(2), suffix)
    rewritten = _PROMO_REWRITES.get(normalized)
    return rewritten[0] if rewritten else normalized


def _specific_line_code(text):
    for match in _SPECIFIC_CODE_RE.finditer(text or ""):
        code = _canonical_model_code(match.group(1))
        if re.search(r"-?00$", code):
            continue
        return code
    return ""


def _part_codes(text):
    found = []
    for match in _PART_CODE_RE.finditer(text or ""):
        code = (match.group(1) or match.group(2) or "").upper()
        if code and code not in found:
            found.append(code)
    return found


def _plain_part(code):
    match = re.match(r"^[A-Z]{1,2}(\d{1,2}-\d{2}[A-Z]{1,3})$", code or "")
    return match.group(1) if match else code


def _part_code(text):
    codes = []
    for code in _part_codes(text):
        plain = _plain_part(code)
        if plain and plain not in codes:
            codes.append(plain)
    return codes[0] if len(codes) == 1 else ""


def _resolve_alias(text):
    alias = _alias_token(text)
    if not alias:
        return None
    part = _part_code(text)
    if alias == "DRANZER" and part == "3-80T" and _BLACK_VARIANT_RE.search(text or ""):
        return {"model": "BXG-15", "tag": "BX"}
    if alias == "AERO" and part == "3-70A" and re.search(r"紅色|紅版|(?<![A-Za-z])red(?![A-Za-z])", text or "", re.I):
        return {"model": "BXG-24", "tag": "UX"}
    resolved = _ALIAS_PART_AS_CODE.get((alias, part))
    if resolved is None:
        resolved = _ALIAS_AS_CODE.get(alias)
    if not resolved:
        return None
    return {"model": resolved[0], "tag": resolved[1]}


def _alias_token(text):
    for pattern, token in _NAME_ALIASES:
        if pattern.search(text or ""):
            return token
    return ""


def _fold_variant(text):
    cleaned = _UMBRELLA_CODE_RE.sub(" ", text or "")
    cleaned = re.sub(r"\[[^\]]*\]|【[^】]*】|（[^）]*）|\([^)]*\)", " ", cleaned)
    cleaned = re.sub(
        r"行版|港版|日版|海外版|限定版|現貨|預訂|訂金|售價|takara\s*tomy|beyblade\s*x|爆旋陀螺\s*x",
        " ",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff:+-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned).strip("-:")
    return "".join(ch.upper() if ch.isascii() else ch for ch in cleaned)


def _kuji_fields(text):
    if not _KUJI_RE.search(text or ""):
        return None
    vol = re.search(r"(?:vol\.?\s*|第\s*)(\d{1,2})", text, re.I)
    whole_case = re.search(r"原箱|\d+\s*pcs", text, re.I) and not re.search(
        r"[A-G]\s*賞", text, re.I
    )
    prize = ""
    if whole_case:
        prize = "CASE"
    else:
        found = re.search(r"([A-G](?:\s*\+\s*[A-G])*)\s*賞", text, re.I)
        if not found:
            found = re.search(r"prize\s*([A-G](?:\s*\+\s*[A-G])*)", text, re.I)
        if found:
            prize = re.sub(r"[^A-G]", "", found.group(1).upper())
        elif re.search(r"最後賞|ラストワン|last\s*賞|last\s*(?:one|chance)", text, re.I):
            prize = "LAST"
    parts = ["KUJI", "DMM"]
    if vol:
        parts.append("V%s" % vol.group(1))
    if prize:
        parts.append(prize)
    return {"model": "-".join(parts), "tag": "other"}


def _mapped_alias_fields(text):
    if _specific_line_code(text) or _UMBRELLA_CODE_RE.search(text or ""):
        return None
    return _resolve_alias(text)


def _umbrella_fields(text):
    umbrellas = list(_UMBRELLA_CODE_RE.finditer(text or ""))
    umbrella = umbrellas[-1] if umbrellas else None
    specific = _specific_line_code(text)
    if specific:
        tag = umbrella.group(1).upper() if umbrella else specific[:2]
        if not umbrella and re.search(r"(?<![A-Za-z0-9])BXA-?\s?02(?![0-9])", text or "", re.I):
            tag = "UX"
        return {"model": specific, "tag": tag}
    if not umbrella:
        return None
    line = umbrella.group(1).upper()
    alias = _alias_token(text)
    part = _part_code(text)
    resolved = _resolve_alias(text)
    if resolved:
        return resolved
    if alias:
        model = "%s-00:%s" % (line, alias)
        if part:
            model = "%s:%s" % (model, part)
        return {"model": model, "tag": line}
    variant = _fold_variant(text)
    if not variant:
        variant = "UNKNOWN"
    return {"model": "%s-00:%s" % (line, variant), "tag": line}


def classify_product_line(text):
    text = text or ""
    text = re.sub(r"\bB0[A-Z0-9]{8}\b", " ", text, flags=re.I)
    text = re.sub(r"\b\d{12,14}\b", " ", text)
    kuji = _kuji_fields(text)
    if kuji:
        return kuji
    umbrella = _umbrella_fields(text)
    if umbrella:
        return umbrella
    mapped = _mapped_alias_fields(text)
    if mapped:
        return mapped
    match = LINE_MODEL_RE.search(text)
    if match:
        return {"model": match.group(1).upper(), "tag": match.group(2).upper()}
    return {"model": "", "tag": "other"}


def product_line_fields(item):
    item = item or {}
    title = " ".join(str(item.get(key) or "") for key in ("title", "name"))
    sku = str(item.get("sku") or "")
    fields = classify_product_line(title)
    if not fields.get("model") and sku:
        fields = classify_product_line(sku)
    return fields


def notify_history_row(item, shop_id="", shop="", event="new", changed_at=""):
    item = item or {}
    line = product_line_fields(item)
    change = status_change_text(item.get("prev_status"), stock_status(item), event)
    if event == "price_drop":
        change = price_value_text(item)
    sku = str(item.get("sku") or "")
    image_path = str(item.get("image_path") or "")
    if not image_path and shop_id and sku:
        image_path = product_image_path(shop_id, sku)
    return {
        "at": changed_at or item.get("changed_at") or now_stamp(),
        "shop_id": str(shop_id or ""),
        "shop": str(shop or ""),
        "event": str(event or "new"),
        "sku": sku,
        "title": str(item.get("title") or item.get("sku") or ""),
        "model": str(line.get("model") or ""),
        "tag": str(line.get("tag") or ""),
        "price": str(item.get("price") or ""),
        "url": str(item.get("url") or product_url(item) or ""),
        "change": change,
        "from": item.get("prev_status"),
        "to": stock_status(item),
        "image": str(item.get("image") or product_image_url(item) or ""),
        "image_path": image_path,
        "description": str(item.get("description") or ""),
    }


def history_href(shop_id="", model="", start="", end="", src=""):
    pairs = []
    if shop_id:
        pairs.append(("shop", shop_id))
    if model:
        pairs.append(("model", model))
    if start:
        pairs.append(("from", str(start)[:10]))
    if end:
        pairs.append(("to", str(end)[:10]))
    if normalize_notify_src(src) == NOTIFY_SRC_AMAZON:
        pairs.append(("src", NOTIFY_SRC_AMAZON))
    path = "/history"
    if pairs:
        path += "?" + urllib.parse.urlencode(pairs)
    return path


def normalize_notify_src(src):
    value = str(src or "").strip().lower()
    if value in (NOTIFY_SRC_AMAZON, "amz"):
        return NOTIFY_SRC_AMAZON
    return NOTIFY_SRC_HK


def is_amazon_notify_row(row):
    shop_id = str((row or {}).get("shop_id") or "").strip()
    if shop_id in AMAZON_NOTIFY_SHOP_IDS:
        return True
    shop = str((row or {}).get("shop") or "").strip().lower()
    return shop_id.startswith("amazon") or shop.startswith("amazon")


def filter_notifies_by_src(rows, src=""):
    want_amazon = normalize_notify_src(src) == NOTIFY_SRC_AMAZON
    return [row for row in rows or [] if is_amazon_notify_row(row) == want_amazon]


def filter_shops_by_notify_src(shops, src=""):
    want_amazon = normalize_notify_src(src) == NOTIFY_SRC_AMAZON
    out = []
    for shop in shops or []:
        sid = str(shop.get("id") or "")
        is_amazon = sid in AMAZON_NOTIFY_SHOP_IDS or sid.startswith("amazon")
        if is_amazon == want_amazon:
            out.append(shop)
    return out


def home_href(src=""):
    if normalize_notify_src(src) == NOTIFY_SRC_AMAZON:
        return "/?src=amazon"
    return "/"


def notify_src_shop_id(shop_id, src=""):
    shop_id = str(shop_id or "")
    if not shop_id:
        return ""
    is_amazon = shop_id in AMAZON_NOTIFY_SHOP_IDS or shop_id.startswith("amazon")
    if (normalize_notify_src(src) == NOTIFY_SRC_AMAZON) == is_amazon:
        return shop_id
    return ""


def parse_history_day(text):
    text = str(text or "").strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def history_query_dates(from_s="", to_s="", now=None):
    now = now or datetime.now(HKT_TZ)
    today = now.date() if hasattr(now, "date") else now
    start = parse_history_day(from_s)
    end = parse_history_day(to_s)
    if start is None and end is None:
        start = today - timedelta(days=HISTORY_PAGE_DAYS - 1)
        end = today
    elif start is None:
        start = end - timedelta(days=HISTORY_PAGE_DAYS - 1)
    elif end is None:
        end = start + timedelta(days=HISTORY_PAGE_DAYS - 1)
    if start > end:
        start, end = end, start
    return start, end


def filter_notify_dates(rows, start, end):
    if start is None or end is None:
        return list(rows or [])
    out = []
    for row in rows or []:
        parsed = parse_history_day(notify_at_date(row))
        if parsed is None or (start <= parsed <= end):
            out.append(row)
    return out


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
        if is_skipped_product(row):
            continue
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
    path = path or os.path.join(resolved_data_dir(), "watch_events.jsonl")
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


def ensure_notify_history_description(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notify_history' "
            "AND COLUMN_NAME = 'description'"
        )
        row = cur.fetchone() or {}
        if int(row.get("n") or 0):
            return
        cur.execute("ALTER TABLE notify_history ADD COLUMN description TEXT NULL")
    conn.commit()


def load_notify_history_mysql(limit=100, shop_id="", model=""):
    conn = mysql_connect()
    try:
        ensure_notify_history_description(conn)
        sql = (
            "SELECT at, shop_id, shop, event, sku, title, `model`, `tag`, price, url, `change`, image, image_path, description "
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
            rows = load_notify_history_mysql(limit, shop_id, model)
            return filter_notify_history(rows, shop_id, model, shops)[:limit]
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


def load_notify_history_mysql_for_day(day):
    conn = mysql_connect()
    try:
        ensure_notify_history_description(conn)
        sql = (
            "SELECT at, shop_id, shop, event, sku, title, `model`, `tag`, price, url, `change`, image, image_path, description "
            "FROM notify_history WHERE `at` LIKE %s AND event IN ('new','restock','sold_out') "
            "ORDER BY id ASC"
        )
        with conn.cursor() as cur:
            cur.execute(sql, (str(day or "")[:10] + "%",))
            return list(cur.fetchall() or [])
    finally:
        conn.close()


def load_notify_history_jsonl_for_day(day, path=None):
    path = path or os.path.join(resolved_data_dir(), "watch_events.jsonl")
    day = str(day or "")[:10]
    if not day or not os.path.isfile(path):
        return []
    out = []
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
            if notify_at_date(event) != day:
                continue
            out.append(notify_event_as_history(event))
    return out


def load_notify_history_for_day(day, path=None):
    day = str(day or "")[:10]
    if path:
        return load_notify_history_jsonl_for_day(day, path=path)
    if mysql_settings().get("enabled"):
        try:
            return load_notify_history_mysql_for_day(day)
        except Exception as exc:
            print("MySQL notify_history day load failed: %s" % exc, file=sys.stderr)
    return load_notify_history_jsonl_for_day(day)


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
    path = state_file_path(rel)
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
        if os.path.isfile(os.path.join(image_data_dir(), rel)):
            item["image_path"] = rel
        else:
            item.pop("image_path", None)
    else:
        item.pop("image_path", None)
    return item


def request_hostname(host):
    return (host or "").split("/")[0].split(":")[0].strip().lower()


def is_admin_host(host):
    return request_hostname(host) == ADMIN_HOST


def admin_credentials_ok(username, password):
    user = "" if username is None else str(username)
    pw = "" if password is None else str(password)
    try:
        return hmac.compare_digest(user, ADMIN_USERNAME) and hmac.compare_digest(
            pw, ADMIN_PASSWORD
        )
    except Exception:
        return False


def admin_session_token():
    return hmac.new(
        ADMIN_PASSWORD.encode("utf-8"),
        ADMIN_USERNAME.encode("utf-8"),
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


def discord_webhook_url():
    notify = (CONFIG.get("notify") or {}).get("discord") or {}
    return (os.environ.get("DISCORD_WEBHOOK_URL") or notify.get("webhook_url") or "").strip()


def discord_dev_webhook_url():
    notify = (CONFIG.get("notify") or {}).get("discord") or {}
    return (
        os.environ.get("DISCORD_DEV_WEBHOOK_URL") or notify.get("dev_webhook_url") or ""
    ).strip()


def discord_notify_enabled(kind):
    notify = (CONFIG.get("notify") or {}).get("discord") or {}
    if notify.get("enabled") is False:
        return False
    if not discord_webhook_url():
        return False
    if kind == "products":
        return notify.get("send_products", True)
    if kind == "errors":
        return notify.get("send_errors", True)
    return True


def discord_mention_fields(kind="products"):
    notify = (CONFIG.get("notify") or {}).get("discord") or {}
    mention = (notify.get("mention") or "").strip()
    if not mention:
        return {}
    if kind == "errors" and not notify.get("mention_errors"):
        return {}
    fields = {"content": mention}
    if mention in ("@everyone", "@here"):
        fields["allowed_mentions"] = {"parse": ["everyone"]}
    return fields


def discord_product_payload(title, items, fallback_url=None, event="new"):
    styles = {
        "new": {"label": "新品", "color": 3901635},
        "restock": {"label": "補貨", "color": 5763719},
        "sold_out": {"label": "變為缺貨", "color": 15548997},
        "price_drop": {"label": "降價", "color": 16750848},
    }
    style = styles.get(event) or styles["new"]
    embeds = []
    first_url = fallback_url
    for item in (items or [])[:10]:
        name = item.get("title") or item.get("sku") or "New product"
        url = product_url(item) if item.get("link") or item.get("origin") else fallback_url
        if url and not first_url:
            first_url = url
        status = stock_status(item)
        if status == "in_stock":
            color = 5763719
        elif status == "out_of_stock":
            color = 15548997
        else:
            color = style["color"]
        if event == "sold_out":
            color = 15548997
        elif event == "restock":
            color = 5763719
        elif event == "price_drop":
            color = 16750848
        price_value = price_value_text(item)
        changed_at = item.get("changed_at") or now_stamp()
        change = status_change_text(item.get("prev_status"), status, event)
        time_label = changed_at if str(changed_at).endswith("HKT") else "%s HKT" % changed_at
        fields = [
            {"name": "庫存", "value": change, "inline": True},
            {"name": "時間", "value": time_label, "inline": True},
            {"name": "價錢", "value": price_value, "inline": True},
        ]
        bundle_text = "\n".join(bundle_notice_lines(item))
        if bundle_text:
            fields.append({"name": "套裝內容", "value": bundle_text[:1024], "inline": False})
        if url:
            fields.append({"name": "連結", "value": "[開啟商品](%s)" % url, "inline": False})
        embed = {
            "author": {"name": "%s · %s" % (title, notify_kind_label(event, item))},
            "title": name[:256],
            "url": url,
            "color": color,
            "fields": fields,
        }
        image = item.get("image") or product_image_url(item)
        if image:
            embed["thumbnail"] = {"url": image}
        embeds.append(embed)
    if len(items or []) > 1 and fallback_url:
        first_url = fallback_url
        if embeds:
            embeds[0]["url"] = first_url
    extra = len(items or []) - 10
    if extra > 0 and embeds:
        embeds[-1]["footer"] = {"text": "另有 %d 件，請看商店頁" % extra}
    payload = {"username": "Beyblade Watch", "embeds": embeds}
    payload.update(discord_mention_fields("products"))
    return payload


def post_discord(payload, webhook_url=None):
    url = (webhook_url or discord_webhook_url()).strip()
    if not url:
        return False
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl_context()) as resp:
            resp.read()
        return True
    except Exception:
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "-A",
                USER_AGENT,
                "-H",
                "Content-Type: application/json",
                "-X",
                "POST",
                url,
                "-d",
                json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "discord webhook failed")
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


def notify_threads_text(text):
    if not threads_notify_enabled("products") or not text:
        return False
    try:
        post_threads(text)
        return True
    except Exception as exc:
        print("Threads text notify failed: %s" % exc, file=sys.stderr)
        return False


def send_admin_channel(channel, message):
    if channel == "discord":
        return notify_discord_text(message)
    if channel == "telegram":
        return notify_telegram_text(message)
    if channel == "threads":
        return notify_threads_text(message)
    return False


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


def send_test_product_discord():
    url = discord_dev_webhook_url() or discord_webhook_url()
    if not url:
        return False
    items = wrap_notify_item_links(test_product_items(), source="discord", warm=True)
    hop = items[0]["link"] if items else CATEGORY_URL
    payload = discord_product_payload(
        "Beyblade Watch test",
        items,
        hop,
        event="new",
    )
    payload.pop("content", None)
    payload.pop("allowed_mentions", None)
    try:
        post_discord(payload, webhook_url=url)
        return True
    except Exception as exc:
        print("Discord product notify failed: %s" % exc, file=sys.stderr)
        return False


def send_test_product_telegram():
    items = wrap_notify_item_links(test_product_items(), source="telegram", warm=True)
    hop = items[0]["link"] if items else CATEGORY_URL
    return notify_telegram_products(
        "Beyblade Watch test",
        items,
        hop,
        event="new",
    )


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


def telegram_cfg():
    return (CONFIG.get("notify") or {}).get("telegram") or {}


def telegram_bot_token():
    return (os.environ.get("TELEGRAM_BOT_TOKEN") or telegram_cfg().get("bot_token") or "").strip()


def telegram_chat_id():
    raw = os.environ.get("TELEGRAM_CHAT_ID")
    if raw is None or str(raw).strip() == "":
        raw = telegram_cfg().get("chat_id")
    return str(raw or "").strip()


def telegram_message_thread_id():
    raw = os.environ.get("TELEGRAM_MESSAGE_THREAD_ID")
    if raw is None or str(raw).strip() == "":
        raw = telegram_cfg().get("message_thread_id")
    text = str(raw or "").strip()
    if not text:
        return 0
    try:
        value = int(text)
    except (TypeError, ValueError):
        return 0
    return value if value > 0 else 0


def telegram_notify_enabled(kind, force=False):
    notify = telegram_cfg()
    if notify.get("enabled") is False and not force:
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


def telegram_product_text(title, items, fallback_url=None, event="new"):
    blocks = []
    for item in (items or [])[:10]:
        name = item.get("title") or item.get("sku") or "New product"
        url = product_url(item) if item.get("link") or item.get("origin") else fallback_url
        status = stock_status(item)
        change = status_change_text(item.get("prev_status"), status, event)
        changed_at = item.get("changed_at") or now_stamp()
        time_label = changed_at if str(changed_at).endswith("HKT") else "%s HKT" % changed_at
        price_value = price_value_text(item)
        if url:
            heading = '<a href="%s">%s</a>' % (telegram_html(url), telegram_html(name))
        else:
            heading = "<b>%s</b>" % telegram_html(name)
        blocks.append(
            "\n".join(
                [
                    "<b>%s · %s</b>"
                    % (telegram_html(title), telegram_html(notify_kind_label(event, item))),
                    heading,
                    "庫存: %s" % telegram_html(change),
                    "時間: %s" % telegram_html(time_label),
                    "價錢: %s" % telegram_html(price_value),
                ]
                + ["套裝: %s" % telegram_html(line) for line in bundle_notice_lines(item)]
            )
        )
    extra = len(items or []) - 10
    if extra > 0:
        blocks.append("另有 %d 件，請看商店頁" % extra)
    return "\n\n".join(blocks)


def send_telegram_payload(method, payload):
    token = telegram_bot_token()
    chat_id = telegram_chat_id()
    if not token or not chat_id or not payload:
        return False
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    raw = ""
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl_context()) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as exc:
        if hasattr(exc, "read"):
            try:
                raw = exc.read().decode("utf-8", errors="replace")
            except Exception:
                raw = ""
        if not raw:
            proc = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "-A",
                    USER_AGENT,
                    "-H",
                    "Content-Type: application/json",
                    "-X",
                    "POST",
                    url,
                    "-d",
                    json.dumps(payload),
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or ("telegram %s failed" % method))
            raw = proc.stdout or ""
    try:
        data = json.loads(raw or "")
    except Exception:
        data = {}
    if not isinstance(data, dict) or not data.get("ok"):
        err = ""
        if isinstance(data, dict):
            err = str((data.get("description") or data.get("error") or "")).strip()
        raise RuntimeError(err or ("telegram %s failed" % method))
    return True


def telegram_message_payload(text, thread_id=None, preview_url=None):
    options = {"is_disabled": False, "prefer_large_media": True}
    preview = str(preview_url or "").strip()
    if preview:
        options["url"] = preview
    payload = {
        "chat_id": telegram_chat_id(),
        "text": str(text or "")[:4096],
        "parse_mode": "HTML",
        "link_preview_options": options,
    }
    if thread_id:
        payload["message_thread_id"] = int(thread_id)
    return payload


def send_telegram_message(text, thread_id=None, preview_url=None):
    chat_id = telegram_chat_id()
    if not chat_id or not text:
        return False
    payload = telegram_message_payload(text, thread_id=thread_id, preview_url=preview_url)
    return send_telegram_payload("sendMessage", payload)


def post_telegram(text, thread_id=None, preview_url=None):
    if thread_id is None:
        thread_id = telegram_message_thread_id()
    if thread_id:
        try:
            return send_telegram_message(text, thread_id=thread_id, preview_url=preview_url)
        except Exception as exc:
            print(
                "Telegram topic %s failed: %s; sending to default chat."
                % (thread_id, exc),
                file=sys.stderr,
            )
    return send_telegram_message(text, thread_id=None, preview_url=preview_url)


def notify_telegram_products(title, items, fallback_url=None, event="new", force=False, thread_id=None):
    if not telegram_notify_enabled("products", force=force) or not items:
        return False
    try:
        post_telegram(
            telegram_product_text(title, items, fallback_url, event=event),
            thread_id=thread_id,
        )
        return True
    except Exception as exc:
        print("Telegram product notify failed: %s" % exc, file=sys.stderr)
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


def threads_topic_tag():
    notify = threads_cfg()
    if "topic_tag" in notify:
        tag = "" if notify.get("topic_tag") is None else str(notify.get("topic_tag")).strip()
    else:
        tag = THREADS_TOPIC_TAG
    tag = tag.replace(".", "").replace("&", "")
    return tag[:50]


def threads_publish_fields(text, reply_to_id=None, link_attachment=None):
    payload = {
        "media_type": "TEXT",
        "text": text,
        "auto_publish_text": "true",
        "access_token": threads_access_token(),
    }
    tag = threads_topic_tag()
    if tag:
        payload["topic_tag"] = tag
    if reply_to_id:
        payload["reply_to_id"] = str(reply_to_id)
    attach = str(link_attachment or threads_first_url(text) or "").strip()
    if attach:
        payload["link_attachment"] = attach
    return payload


def threads_first_url(text):
    match = THREADS_URL_RE.search(str(text or ""))
    return match.group(0) if match else ""


def threads_form_post(url, payload):
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl_context()) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "-A",
                USER_AGENT,
                "-H",
                "Content-Type: application/x-www-form-urlencoded",
                "-X",
                "POST",
                url,
                "-d",
                urllib.parse.urlencode(payload),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "threads request failed")
        return proc.stdout or ""


def threads_media_id_from_response(raw):
    try:
        data = json.loads(raw or "")
    except Exception:
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("id") or "").strip()


def threads_daily_posts_path():
    return os.path.join(resolved_data_dir(), "threads_daily_posts.json")


def threads_daily_post_limit():
    raw = threads_cfg().get("daily_post_limit", THREADS_DEFAULT_DAILY_POST_LIMIT)
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        limit = THREADS_DEFAULT_DAILY_POST_LIMIT
    return max(limit, 0)


def _threads_daily_date_key():
    return datetime.now(HKT_TZ).strftime("%Y-%m-%d")


def load_threads_daily_posts(path=None):
    path = path or threads_daily_posts_path()
    with _threads_io_lock:
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def save_threads_daily_posts(data, path=None):
    path = path or threads_daily_posts_path()
    with _threads_io_lock:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    return True


def threads_daily_posts_used(path=None):
    data = load_threads_daily_posts(path)
    if data.get("date") != _threads_daily_date_key():
        return 0
    try:
        return max(int(data.get("count") or 0), 0)
    except (TypeError, ValueError):
        return 0


def threads_daily_posts_remaining(path=None):
    return max(threads_daily_post_limit() - threads_daily_posts_used(path), 0)


def increment_threads_daily_posts(n=1, path=None):
    n = max(int(n or 0), 0)
    if n <= 0:
        return 0
    path = path or threads_daily_posts_path()
    with _threads_io_lock:
        data = load_threads_daily_posts(path)
        day = _threads_daily_date_key()
        if data.get("date") != day:
            data = {"date": day, "count": 0}
        data["count"] = int(data.get("count") or 0) + n
        save_threads_daily_posts(data, path=path)
        return int(data["count"])


def post_threads(text, reply_to_id=None):
    url = threads_publish_url()
    token = threads_access_token()
    if not url or not token or not text:
        return False
    if threads_daily_posts_remaining() <= 0:
        print(
            "Threads post skipped (daily limit %d reached)."
            % threads_daily_post_limit(),
            file=sys.stderr,
        )
        return False
    payload = threads_publish_fields(text, reply_to_id=reply_to_id)
    raw = threads_form_post(url, payload)
    try:
        data = json.loads(raw or "")
    except Exception:
        data = None
    if isinstance(data, dict) and data.get("error"):
        err = data.get("error")
        if isinstance(err, dict):
            err = err.get("message") or err
        print("Threads post failed: %s" % err, file=sys.stderr)
        return False
    media_id = threads_media_id_from_response(raw)
    if not media_id:
        print("Threads post failed: no media id.", file=sys.stderr)
        return False
    increment_threads_daily_posts(1)
    return media_id


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


def cloudflare_purge_settings():
    cf = (CONFIG or {}).get("cloudflare") or {}
    token = (os.environ.get("BEYBLADE_CF_API_TOKEN") or cf.get("api_token") or "").strip()
    zone_id = (os.environ.get("BEYBLADE_CF_ZONE_ID") or cf.get("zone_id") or CLOUDFLARE_ZONE_ID).strip()
    return {"token": str(token), "zone_id": str(zone_id)}


def edge_purge_log_path(data_dir=None):
    return os.path.join(data_dir or resolved_data_dir(), EDGE_PURGE_LOG_NAME)


def _purge_now(now):
    if now is None:
        return time.time()
    if callable(now):
        return float(now())
    return float(now)


def _purge_stamp(when):
    return datetime.fromtimestamp(when, HKT_TZ).strftime("%Y-%m-%dT%H:%M:%S")


def _parse_purge_stamp(value):
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            local = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return local.replace(tzinfo=HKT_TZ).timestamp()
    return None


def prune_edge_purge_log(path=None, now=None, keep_days=EDGE_PURGE_LOG_KEEP_DAYS):
    path = path or edge_purge_log_path()
    cutoff = _purge_now(now) - int(keep_days) * 86400
    if not os.path.isfile(path):
        return 0
    kept = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except ValueError:
                continue
            stamped = _parse_purge_stamp(row.get("at"))
            if stamped is None or stamped >= cutoff:
                kept.append(text)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        if kept:
            fh.write("\n".join(kept) + "\n")
    os.replace(tmp, path)
    return len(kept)


def append_edge_purge_log(result, path=None, now=None):
    when = _purge_now(now)
    path = path or edge_purge_log_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    row = {
        "at": _purge_stamp(when),
        "ok": bool((result or {}).get("ok")),
        "cloudflare": bool((result or {}).get("cloudflare")),
    }
    for key in ("error", "detail", "http", "response", "reason"):
        value = (result or {}).get(key)
        if value not in (None, ""):
            row[key] = value
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return prune_edge_purge_log(path=path, now=when)


def prune_edge_purge_log_once_per_day(last_day, now=None, path=None):
    when = _purge_now(now)
    day = datetime.fromtimestamp(when, HKT_TZ).strftime("%Y-%m-%d")
    if day == last_day:
        return last_day
    prune_edge_purge_log(path=path, now=when)
    return day


def _edge_purge_http_status(response):
    status = getattr(response, "status", None)
    if status is None:
        status = getattr(response, "code", None)
    return int(status or 200)


def _finish_edge_purge(result, log_path=None, now=None):
    append_edge_purge_log(result, path=log_path, now=now)
    return result


def purge_edge_cache(urlopen=None, log_path=None, now=None):
    reset_status_caches()
    cfg = cloudflare_purge_settings()
    if not cfg["token"] or not cfg["zone_id"]:
        return _finish_edge_purge(
            {"ok": False, "origin": True, "cloudflare": False, "error": "missing_token"},
            log_path=log_path,
            now=now,
        )
    url = "https://api.cloudflare.com/client/v4/zones/%s/purge_cache" % cfg["zone_id"]
    payload = json.dumps({"tags": [HTML_CACHE_TAG]}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": "Bearer " + cfg["token"],
            "Content-Type": "application/json",
        },
    )
    opener = urlopen or urllib.request.urlopen
    try:
        with opener(request, timeout=20) as response:
            raw = response.read()
            status = _edge_purge_http_status(response)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:2000]
        except Exception:
            detail = ""
        return _finish_edge_purge(
            {
                "ok": False,
                "origin": True,
                "cloudflare": False,
                "error": "cloudflare_http_%s" % exc.code,
                "http": exc.code,
                "detail": detail,
            },
            log_path=log_path,
            now=now,
        )
    except Exception as exc:
        return _finish_edge_purge(
            {"ok": False, "origin": True, "cloudflare": False, "error": str(exc)[:300]},
            log_path=log_path,
            now=now,
        )
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        data = {"raw": raw.decode("utf-8", "replace")[:2000]}
    if not isinstance(data, dict):
        data = {"raw": data}
    ok = bool(data.get("success"))
    result = {
        "ok": ok,
        "origin": True,
        "cloudflare": ok,
        "http": status,
        "response": data,
    }
    if not ok:
        result["error"] = "cloudflare_rejected"
    return _finish_edge_purge(result, log_path=log_path, now=now)


def reset_edge_purge_state():
    global _edge_purge_pending
    with _edge_purge_lock:
        _edge_purge_at[:] = []
        _edge_purge_pending = False


def edge_purge_allowed(now, times):
    recent = [t for t in times if now - t < EDGE_PURGE_LONG_WINDOW]
    if recent and now - recent[-1] < EDGE_PURGE_MIN_GAP:
        return False
    short = [t for t in recent if now - t < EDGE_PURGE_SHORT_WINDOW]
    if len(short) >= EDGE_PURGE_SHORT_MAX:
        return False
    if len(recent) >= EDGE_PURGE_LONG_MAX:
        return False
    return True


def request_edge_purge(now=None, urlopen=None):
    global _edge_purge_pending
    with _edge_purge_lock:
        _edge_purge_pending = True
    return flush_edge_purge(now=now, urlopen=urlopen)


def flush_edge_purge(now=None, urlopen=None):
    global _edge_purge_pending
    now = time.time() if now is None else now
    with _edge_purge_lock:
        if not _edge_purge_pending:
            return {"ok": True, "skipped": True, "reason": "idle"}
        if not edge_purge_allowed(now, _edge_purge_at):
            return {"ok": False, "skipped": True, "reason": "rate_limit", "origin": True}
        if not cloudflare_purge_settings()["token"]:
            _edge_purge_pending = False
            result = {"ok": False, "origin": True, "cloudflare": False, "error": "missing_token"}
            append_edge_purge_log(result)
            return result
        _edge_purge_at.append(now)
        _edge_purge_at[:] = [t for t in _edge_purge_at if now - t < EDGE_PURGE_LONG_WINDOW]
    result = purge_edge_cache(urlopen=urlopen)
    with _edge_purge_lock:
        _edge_purge_pending = not result.get("cloudflare")
    return result


def _seen_sku_state_name(name):
    return name == "seen_skus.json" or name.endswith("_seen_skus.json")


def _stock_file_token(path):
    try:
        st = os.stat(path)
    except OSError:
        return ""
    key = (st.st_mtime_ns, st.st_size)
    cached = _stock_sig_cache.get(path)
    if cached and cached[0] == key:
        return cached[1]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        token = ""
    else:
        if not isinstance(data, dict):
            data = {}
        token = json.dumps(
            {
                "stock": data.get("stock") or {},
                "stock_changed_at": data.get("stock_changed_at") or {},
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    _stock_sig_cache[path] = (key, token)
    return token


def listing_state_fingerprint(data_dir=None):
    data_dir = data_dir or resolved_data_dir()
    parts = []
    try:
        names = os.listdir(data_dir)
    except OSError:
        return ""
    for name in sorted(names):
        if not _seen_sku_state_name(name):
            continue
        token = _stock_file_token(os.path.join(data_dir, name))
        parts.append("%s:%s" % (name, token))
    return "|".join(parts)


def refresh_status_pages_if_listings_changed(prev="", data_dir=None, now=None, urlopen=None):
    current = listing_state_fingerprint(data_dir)
    if prev and current != prev:
        reset_status_caches()
        request_edge_purge(now=now, urlopen=urlopen)
    else:
        flush_edge_purge(now=now, urlopen=urlopen)
    return current


def start_listing_watch_loop(interval=None, stop=None, data_dir=None):
    interval = LISTING_WATCH_INTERVAL if interval is None else interval

    def run():
        prev = listing_state_fingerprint(data_dir)
        last_purge_prune_day = ""
        while True:
            last_purge_prune_day = prune_edge_purge_log_once_per_day(last_purge_prune_day)
            if stop is not None and stop.wait(interval):
                return
            if stop is None:
                time.sleep(interval)
            prev = refresh_status_pages_if_listings_changed(prev, data_dir=data_dir)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def cached_bytes(key, builder, ttl=PAGE_CACHE_TTL, now=time.time, revision=None):
    t = now()
    with _page_cache_lock:
        hit = _page_cache.get(key)
        if hit and hit[0] > t:
            return hit[1]
        previous = hit[2] if hit and len(hit) > 2 else None
        stale = hit[1] if hit else None
    current = listing_state_fingerprint() if revision is None else revision()
    if stale is not None and previous == current:
        with _page_cache_lock:
            fresh = _page_cache.get(key)
            if fresh and fresh[0] > t:
                return fresh[1]
            _page_cache[key] = (t + ttl, stale, current)
        return stale
    body = builder()
    with _page_cache_lock:
        _page_cache[key] = (t + ttl, body, current)
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
        path = state_file_path(rel)
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


def page_canonical(path):
    return SITE_ORIGIN + (path or "/")


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
            "threads",
        )
    )


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
    sid = str((source or {}).get("id") or "")
    if sid in ("amazon-jp-retail", "amazon-us-retail"):
        return sid
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


OVERSEAS_SHOP_IDS = frozenset(
    {
        "amazon",
        "amazon-jp",
        "amazon-jp-retail",
        "amazon-us-retail",
        "biccamera",
        "yodobashi",
        "takaratomymall",
    }
)


def shop_is_overseas(shop, cfg=None):
    """Japan and other non-Hong Kong shops, kept apart from local stores."""
    shop = shop or {}
    sid = str(shop.get("id") or "")
    if sid in ("", "all"):
        return False
    source = find_source_by_id(sid, cfg) or {}
    region = str(source.get("region") or shop.get("region") or "").strip().lower()
    if region in ("hk", "hongkong", "hong-kong"):
        return False
    if region in ("jp", "japan", "us", "overseas", "non-hk"):
        return True
    return sid in OVERSEAS_SHOP_IDS


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
    path = state_file_path(rel)
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
            if is_skipped_product(row, cfg):
                continue
            items.append(row)
    return items


def shop_products_href(shop_id, stock=None, tag=None):
    path = "/shop/%s" % urllib.parse.quote(str(shop_id or ""), safe="-")
    query = []
    if stock == "in_stock":
        query.append(("stock", "in"))
    elif stock == "out_of_stock":
        query.append(("stock", "out"))
    if tag in ("CX", "BX", "UX", "kuji", "other"):
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
    if raw.lower() in ("kuji", "ichiban", "一番賞"):
        return "kuji"
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
    model = listing_model_code(item)
    if model.startswith("KUJI"):
        return "kuji"
    tag = str((item or {}).get("tag") or "").strip()
    if tag:
        if tag.lower() in ("other", "kuji"):
            return tag.lower()
        return tag.upper()
    return product_line_fields(item)["tag"]


def listing_model_code(item):
    item = item or {}
    stored = str(item.get("model") or "").strip().upper()
    parsed = str(product_line_fields(item).get("model") or "").strip().upper()
    text = " ".join(str(item.get(key) or "") for key in ("title", "sku", "name"))
    if parsed and (_UMBRELLA_CODE_RE.search(text) or _KUJI_RE.search(text)):
        model = parsed
    else:
        model = stored or parsed
    model = re.sub(r"^(CX|BX|UX)(?=\d)", r"\1-", model)
    return _canonical_model_code(model)


def listing_price_value(item):
    raw = str((item or {}).get("price") or "").replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", raw)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def listing_rank(item):
    price = listing_price_value(item)
    return (
        0 if product_stock_key(item) == "in_stock" else 1,
        price if price is not None else 10 ** 12,
    )


def group_listings_by_model(items):
    groups = []
    index = {}
    for item in items or []:
        model = listing_model_code(item)
        if model:
            key = "model:" + model
        else:
            key = "item:%s:%s:%s" % (
                item.get("shop_id") or "",
                item.get("sku") or "",
                item.get("title") or "",
            )
        group = index.get(key)
        if group is None:
            group = {"model": model, "items": []}
            index[key] = group
            groups.append(group)
        group["items"].append(item)

    def sort_key(group):
        if group["model"]:
            return (0, group["model"])
        title = str((group["items"][0] or {}).get("title") or "")
        return (1, title)

    groups.sort(key=sort_key)
    return groups


def group_tag_key(group):
    model = str((group or {}).get("model") or "")
    if model.startswith("KUJI"):
        return "kuji"
    if re.match(r"^(CX|BX|UX)G", model):
        for item in (group or {}).get("items") or []:
            tag = product_line_fields(item).get("tag")
            if tag in ("CX", "BX", "UX"):
                return tag
    if model.startswith("CX"):
        return "CX"
    if model.startswith("BX"):
        return "BX"
    if model.startswith("UX"):
        return "UX"
    for item in (group or {}).get("items") or []:
        tag = product_tag_key(item)
        if tag in ("CX", "BX", "UX"):
            return tag
    return "other"


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
    recorded = str(item.get("image_path") or "").replace("\\", "/")
    rel = recorded
    if not (rel.startswith("images/") and ".." not in rel):
        sku = item.get("sku") or ""
        rel = product_image_path(shop_id, sku) if shop_id and sku else ""
    if not (rel.startswith("images/") and ".." not in rel):
        return seo_image_url()
    dest = os.path.join(image_data_dir(), rel)
    if os.path.isfile(dest) and os.path.getsize(dest) >= IMAGE_MIN_CACHE_BYTES:
        return cdn_image_url("/" + rel) + "?v=" + str(int(os.path.getmtime(dest)))
    # The website process often does not have the jpeg locally. The CDN still
    # serves images/{shop}/{sku}.jpg when image_path was saved with the product.
    # Guessing that path without image_path would 404, and Telegram then shows
    # the title and description with no picture.
    if recorded.startswith("images/") and ".." not in recorded:
        return cdn_image_url("/" + recorded)
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
    recorded = str(item.get("image_path") or "").replace("\\", "/")
    status = item.get("status_label") or status_text(product_stock_key(item))
    return {
        "title": item.get("title") or item.get("sku") or SITE_BRAND,
        "dest": dest,
        "image": image,
        "image_path": recorded if recorded.startswith("images/") and ".." not in recorded else "",
        "og_image": go_og_image_url(item, shop_id),
        "price": item.get("price") or "",
        "status": status,
        "description": product_seo_description(item),
    }


def _as_stock_status(value):
    if value in (None, ""):
        return None
    if value in ("in_stock", "out_of_stock", "unknown"):
        return value
    return {
        "有貨": "in_stock",
        "缺貨": "out_of_stock",
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


def calendar_day_start(now, tz=None):
    """Deployed 2026-09-02: watch_record.log prune keeps the current HKT day."""
    tz = tz or HKT_TZ
    local = datetime.fromtimestamp(now, tz)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()


