#!/usr/bin/env python3
"""Official Beyblade X product / part graph stored under data/parts/.

Primary source is BeybladeHub combo pages (JSON-LD + part anchors + variant
images). Shop SKUs join later via product id (CX-19, BX-01, ...).
"""
from __future__ import print_function

import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
PARTS_DIR = os.path.join(DATA_DIR, "parts")
HUB_ORIGIN = "https://beybladehub.app"
HUB_SITEMAP = HUB_ORIGIN + "/sitemap.xml"
HUB_COMBO_RE = re.compile(
    r"^https://beybladehub\.app/parts/combos/([^/]+)$"
)
JSON_LD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>',
    re.I | re.S,
)
PART_HREF_RE = re.compile(
    r'href="(/parts/(blades|ratchets|bits)#((?:blade-|ratchet-|bit-)[^"]+))"',
    re.I,
)
VARIANT_IMG_RE = re.compile(
    r'src="(https://img\.beybladehub\.app/combos/[^"]+-v(\d{2})\.webp)"'
    r'[^>]*alt="([^"]+)"'
    r'|alt="([^"]+)"[^>]*src="(https://img\.beybladehub\.app/combos/[^"]+-v(\d{2})\.webp)"',
    re.I,
)
LINE_RE = re.compile(r"^(BXA|BXG|BXH|CX|UX|BX)", re.I)
INTERNAL_PHSTUDY_ID_RE = re.compile(r"^[A-Z]{2}-(?:PRD|EVE|CMD|FRB)-", re.I)
HUB_LIMITED_SIBLING_RE = re.compile(
    r"^(?:BX|UX|CX)-00-(bxg|bxh|bxc)(\d+)$", re.I
)
COMBO_RE = re.compile(
    r"([A-Z]{0,3})(\d{1,2}-\d{2,3})([A-Za-z]{1,3})(?:\s|（|\(|$)"
)
HUB_IMG = "https://img.beybladehub.app"
PHSTUDY_ORIGIN = "https://beyblade.phstudy.org"
PHSTUDY_TABLE_SLOT = {
    "BeybladePartsBit": "bit",
    "BeybladePartsRatchet": "ratchet",
    "BeybladePartsBlade": "blade",
    "BeybladePartsLockChip": "lock_chip",
    "BeybladePartsMainBlade": "blade",
    "BeybladePartsMetalBlade": "metal_blade",
    "BeybladePartsOverBlade": "over_blade",
    "BeybladePartsAssistBlade": "assist_blade",
}
PHSTUDY_IMG_FOLDER = {
    "bit": "Bit",
    "ratchet": "Ratchet",
    "blade": "Blade",
    "lock_chip": "LockChip",
    "metal_blade": "MetalBlade",
    "over_blade": "OverBlade",
    "assist_blade": "AssistBlade",
    "main_blade": "MainBlade",
}
SERIES_PART_FIELDS = (
    ("blade_id", "blade"),
    ("main_blade_id", "blade"),
    ("metal_blade_id", "metal_blade"),
    ("over_blade_id", "over_blade"),
    ("assist_blade_id", "assist_blade"),
    ("lock_chip_id", "lock_chip"),
    ("ratchet_id", "ratchet"),
    ("bit_id", "bit"),
)
BLADE_SLOTS = frozenset(
    {"blade", "lock_chip", "metal_blade", "over_blade", "assist_blade"}
)
FAMILY_DISPLAY_SLOTS = BLADE_SLOTS | frozenset({"ratchet", "bit"})
DISPLAY_SLOT_ORDER = (
    "lock_chip",
    "blade",
    "metal_blade",
    "over_blade",
    "assist_blade",
    "ratchet",
    "bit",
)
STOCK_PARTS = {
    "CX-07": ["cx-chip-Pg", "cx-main-Bs", "cx-assist-A", "Tr"],
}

SLOT_FROM_PREFIX = {
    "cx-chip": "lock_chip",
    "cx-metal": "metal_blade",
    "cx-over": "over_blade",
    "cx-assist": "assist_blade",
    "cx-main": "blade",
}


def parse_hub_sitemap(xml_text):
    urls = []
    seen = set()
    for match in re.finditer(r"<loc>([^<]+)</loc>", xml_text or ""):
        url = match.group(1).strip()
        if not HUB_COMBO_RE.match(url) or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def _json_ld_product(html):
    for raw in JSON_LD_RE.findall(html or ""):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        nodes = data.get("@graph") if isinstance(data, dict) else data
        if isinstance(data, dict) and data.get("@type") == "Product":
            nodes = [data]
        if not isinstance(nodes, list):
            continue
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") == "Product":
                return node
    return {}


def _props(product):
    out = {}
    for item in product.get("additionalProperty") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        value = str(item.get("value") or "").strip()
        if name:
            out[name] = value
    return out


def _slot_and_id(kind, token):
    token = (token or "").strip()
    if token.startswith("blade-"):
        part_id = token[len("blade-") :]
        for prefix, slot in SLOT_FROM_PREFIX.items():
            if part_id.startswith(prefix + "-") or part_id == prefix:
                return slot, part_id
        return "blade", part_id
    if token.startswith("ratchet-"):
        return "ratchet", token[len("ratchet-") :]
    if token.startswith("bit-"):
        return "bit", token[len("bit-") :]
    if kind == "ratchets":
        return "ratchet", token
    if kind == "bits":
        return "bit", token
    return "blade", token


def _label_from_anchor(html, href):
    match = re.search(
        r'<a[^>]*href="%s"[^>]*>(.*?)</a>' % re.escape(href),
        html or "",
        re.I | re.S,
    )
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", " ", match.group(1))
    return re.sub(r"\s+", " ", text).strip()


def parse_hub_parts(html):
    parts = []
    seen = set()
    for href, kind, token in PART_HREF_RE.findall(html or ""):
        slot, part_id = _slot_and_id(kind.lower(), token)
        if not part_id or part_id in seen:
            continue
        seen.add(part_id)
        label = _label_from_anchor(html, href)
        name_en = ""
        name_zh = ""
        if slot == "bit":
            en = re.search(
                r"\b((?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+)*)\b", label
            )
            name_en = en.group(1) if en else ""
            name_zh = "軸心"
        elif slot == "ratchet":
            name_zh = "固鎖"
        part = {
            "id": part_id,
            "slot": slot,
            "href": href,
        }
        if name_en:
            part["name_en"] = name_en
        if name_zh:
            part["name_zh"] = name_zh
        if label:
            part["label"] = label
        parts.append(part)
    return parts


def parse_hub_variants(html, product_id):
    variants = []
    seen = set()
    for match in VARIANT_IMG_RE.finditer(html or ""):
        if match.group(2):
            image, index, name_zh = match.group(1), match.group(2), match.group(3)
        else:
            name_zh, image, index = match.group(4), match.group(5), match.group(6)
        variant_id = "%s-%s" % (product_id, index)
        if variant_id in seen:
            continue
        seen.add(variant_id)
        variants.append(
            {
                "id": variant_id,
                "product_id": product_id,
                "index": index,
                "name_zh": html_unescape(name_zh or "").strip(),
                "image": image,
            }
        )
    variants.sort(key=lambda row: row["index"])
    return variants


def html_unescape(text):
    import html as html_lib

    return html_lib.unescape(text or "")


def parse_hub_combo_page(html, url):
    product = _json_ld_product(html)
    sku = str(product.get("sku") or product.get("mpn") or "").strip()
    path_id = url.rstrip("/").rsplit("/", 1)[-1]
    product_id = path_id or sku
    name = html_unescape(str(product.get("name") or "").strip())
    props = _props(product)
    offers = product.get("offers") or {}
    price = offers.get("price") if isinstance(offers, dict) else None
    line_match = LINE_RE.match(product_id or "")
    parts = parse_hub_parts(html)
    return {
        "id": product_id,
        "sku": sku or product_id,
        "path_id": path_id,
        "line": (line_match.group(1) if line_match else "").upper(),
        "name_zh": name,
        "jan": str(product.get("gtin13") or product.get("gtin") or "").strip(),
        "description": html_unescape(str(product.get("description") or "").strip()),
        "released_on": str(product.get("releaseDate") or "").strip(),
        "price_jpy": int(price) if str(price or "").isdigit() else None,
        "bey_type": props.get("類型") or "",
        "stock_combo": props.get("原裝配置") or "",
        "image": str(product.get("image") or "").strip(),
        "source_url": url,
        "parts": parts,
        "variants": parse_hub_variants(html, product_id),
    }


def parse_combo_from_name(name):
    text = html_unescape(name or "").strip()
    match = None
    for found in COMBO_RE.finditer(text):
        match = found
    if not match:
        return None
    label = re.sub(r"\s+", " ", text[: match.start()]).strip()
    return {
        "prefix": match.group(1) or "",
        "ratchet": match.group(2),
        "bit": match.group(3),
        "label": label,
    }


def guess_slot(part_id):
    part_id = part_id or ""
    if re.match(r"^\d{1,2}-\d{2,3}$", part_id) or part_id in ("M-85", "Op"):
        return "ratchet"
    if part_id.startswith("cx-over-"):
        return "over_blade"
    if part_id.startswith("cx-assist-"):
        return "assist_blade"
    if part_id.startswith("cx-chip-"):
        return "lock_chip"
    if part_id.startswith("cx-metal-"):
        return "metal_blade"
    if part_id.startswith("cx-main-"):
        return "blade"
    if re.match(r"^[A-Za-z]{1,3}$", part_id):
        return "bit"
    return "blade"


def parts_from_cx_prefix(prefix):
    prefix = prefix or ""
    if len(prefix) == 1:
        return ["cx-assist-%s" % prefix]
    if len(prefix) >= 2:
        return ["cx-over-%s" % prefix[0], "cx-assist-%s" % prefix[1]]
    return []


def hub_cx_part_key(part_id):
    part_id = str(part_id or "")
    for prefix, slot in SLOT_FROM_PREFIX.items():
        head = prefix + "-"
        if part_id.startswith(head):
            token = part_id[len(head) :]
            if token:
                return slot, token
    return "", ""


def _add_part_to_product(catalog, product_id, part_id, slot=None):
    if not product_id or not part_id:
        return
    slot = slot or guess_slot(part_id)
    parts = catalog.setdefault("parts", {})
    rec = parts.setdefault(
        part_id,
        {"id": part_id, "slot": slot, "used_in": []},
    )
    if not rec.get("slot"):
        rec["slot"] = slot
    used = rec.setdefault("used_in", [])
    if product_id not in used:
        used.append(product_id)
    product = catalog["products"][product_id]
    ids = product.setdefault("part_ids", [])
    if part_id not in ids:
        ids.append(part_id)
    contains = catalog.setdefault("relations", {}).setdefault("contains", [])
    contains.append(
        {"product_id": product_id, "part_id": part_id, "slot": rec.get("slot") or slot}
    )


def _rebuild_first_seen(catalog):
    products = catalog.get("products") or {}

    def sort_key(product_id):
        rec = products.get(product_id) or {}
        return (rec.get("released_on") or "9999-99-99", product_id)

    first_seen = []
    for part in (catalog.get("parts") or {}).values():
        part["used_in"] = sorted(set(part.get("used_in") or []))
        earliest = sorted(part["used_in"], key=sort_key)
        part["first_seen_in"] = earliest[0] if earliest else ""
        if part["first_seen_in"]:
            first_seen.append(
                {"part_id": part["id"], "product_id": part["first_seen_in"]}
            )
    catalog.setdefault("relations", {})["first_seen_in"] = first_seen


def _blade_part_ids_for_label(catalog, label, skip_id):
    if not label:
        return []
    found = []
    for product_id, rec in (catalog.get("products") or {}).items():
        if product_id == skip_id or not (rec.get("part_ids") or []):
            continue
        name = rec.get("name_zh") or ""
        if label not in name:
            continue
        for part_id in rec.get("part_ids") or []:
            slot = ((catalog.get("parts") or {}).get(part_id) or {}).get("slot") or guess_slot(part_id)
            if slot in BLADE_SLOTS:
                found.append(part_id)
    out = []
    for part_id in found:
        if part_id not in out:
            out.append(part_id)
    return out


def fill_missing_parts(catalog):
    catalog = catalog or {}
    products = catalog.get("products") or {}
    variants = catalog.get("variants") or {}
    for product_id, rec in products.items():
        extra = []
        if rec.get("part_ids"):
            continue
        for variant_id in rec.get("variant_ids") or []:
            variant = variants.get(variant_id) or {}
            combo = parse_combo_from_name(variant.get("name_zh") or "")
            if not combo:
                continue
            extra.extend(_blade_part_ids_for_label(catalog, combo["label"], product_id))
            extra.extend(parts_from_cx_prefix(combo["prefix"]))
            extra.append(combo["ratchet"])
            extra.append(combo["bit"])
        extra.extend(STOCK_PARTS.get(product_id) or [])
        seen = set()
        for part_id in extra:
            if not part_id or part_id in seen:
                continue
            seen.add(part_id)
            _add_part_to_product(catalog, product_id, part_id)
    _rebuild_first_seen(catalog)
    return catalog


def product_family_ids(catalog, product):
    product = product or {}
    pid = str(product.get("id") or "")
    base = str(product.get("base_set_id") or pid)
    ids = set()
    if pid:
        ids.add(pid)
    if base:
        ids.add(base)
    ids.update(str(vid) for vid in (product.get("variant_ids") or []) if vid)
    for rec in (catalog.get("products") or {}).values():
        rid = str(rec.get("id") or "")
        rbase = str(rec.get("base_set_id") or "")
        if rid == pid or rid == base or rbase == pid or (base and rbase == base):
            if rid:
                ids.add(rid)
            if rbase:
                ids.add(rbase)
            ids.update(str(vid) for vid in (rec.get("variant_ids") or []) if vid)
    return ids


def own_releases_for_product_part(catalog, product, part_id):
    part_id = str(part_id or "")
    if not part_id:
        return []
    family = product_family_ids(catalog, product)
    slot, token = hub_cx_part_key(part_id)
    rows = []
    for rec in (catalog.get("part_releases") or {}).values():
        rel_id = str(rec.get("part_id") or "")
        rel_slot = rec.get("slot") or guess_slot(rel_id)
        set_id = str(rec.get("set_id") or "")
        base = str(rec.get("base_set_id") or "")
        if set_id not in family and base not in family:
            continue
        if rel_id == part_id:
            rows.append(rec)
            continue
        if slot and token and rel_slot == slot and rel_id == token:
            rows.append(rec)
    rows.sort(key=lambda rec: str(rec.get("set_id") or rec.get("id") or ""))
    return rows


def _display_row_from_release(part_rec, rel, part_id):
    rec = dict(part_rec)
    rel_id = rel.get("id") or ""
    rec["image_path"] = (
        rel.get("image_path")
        or rec.get("image_path")
        or (phstudy_image_url(rel.get("slot") or rec.get("slot"), rel_id) if rel_id else "")
    )
    rec["set_id"] = rel.get("set_id") or ""
    rec["release_id"] = rel.get("id") or ""
    rec["first_seen_in"] = ""
    rec["slot"] = rel.get("slot") or rec.get("slot")
    rec["part_id"] = rec.get("id") or part_id
    if rel.get("name_zh"):
        rec["name_zh"] = rel.get("name_zh")
    return rec


def display_part_sort_key(row):
    row = row or {}
    slot = row.get("slot") or ""
    try:
        slot_i = DISPLAY_SLOT_ORDER.index(slot)
    except ValueError:
        slot_i = len(DISPLAY_SLOT_ORDER)
    return (
        str(row.get("set_id") or ""),
        slot_i,
        str(row.get("part_id") or row.get("id") or ""),
    )


def _foreign_first_seen(rec, part_id, family):
    first = rec.get("first_seen_in") or ""
    if not first or first in family:
        return False
    slot = rec.get("slot") or guess_slot(part_id)
    return slot != "blade"


def hub_limited_sibling_id(product_id):
    match = HUB_LIMITED_SIBLING_RE.match(str(product_id or ""))
    if not match:
        return ""
    return "%s-%s" % (match.group(1).upper(), str(int(match.group(2))))


def _row_is_blade(row):
    slot = row.get("slot") or guess_slot(row.get("part_id") or row.get("id") or "")
    return slot == "blade"


def _add_missing_blades(catalog, product, parts, shown, rows):
    if any(_row_is_blade(row) for row in rows):
        return
    candidates = []
    sibling = (catalog.get("products") or {}).get(
        hub_limited_sibling_id(product.get("id"))
    ) or {}
    candidates.extend(sibling.get("part_ids") or [])
    combo = parse_combo_from_name(product.get("name_zh") or "")
    if combo and combo.get("label"):
        candidates.extend(
            _blade_part_ids_for_label(catalog, combo["label"], product.get("id"))
        )
    for part_id in candidates:
        part_id = str(part_id or "")
        if not part_id or part_id in shown:
            continue
        rec = dict(parts.get(part_id) or {"id": part_id})
        slot = rec.get("slot") or guess_slot(part_id)
        if slot != "blade" or not is_product_display_part(rec):
            continue
        own = own_releases_for_product_part(catalog, product, part_id)
        if own:
            rec = _display_row_from_release(rec, own[0], part_id)
        else:
            rec["part_id"] = rec.get("id") or part_id
        rows.append(rec)
        shown.add(part_id)


def display_parts_for_product(catalog, product):
    catalog = catalog or {}
    product = product or {}
    family = product_family_ids(catalog, product)
    parts = catalog.get("parts") or {}
    rows = []
    for part_id in product.get("part_ids") or []:
        rec = dict(parts.get(part_id) or {"id": part_id})
        if not is_product_display_part(rec):
            continue
        own = own_releases_for_product_part(catalog, product, part_id)
        if own:
            rec = _display_row_from_release(rec, own[0], part_id)
        elif rec.get("release_ids"):
            if _foreign_first_seen(rec, part_id, family):
                continue
            first = rec.get("first_seen_in") or ""
            rec["set_id"] = first if first in family else ""
            rec["first_seen_in"] = rec["set_id"]
            rec["part_id"] = rec.get("id") or part_id
        else:
            if hub_cx_part_key(part_id)[0] and _foreign_first_seen(rec, part_id, family):
                continue
            first = rec.get("first_seen_in") or ""
            rec["set_id"] = first if first in family else ""
            rec["first_seen_in"] = rec["set_id"]
            rec["part_id"] = rec.get("id") or part_id
        rows.append(rec)
    shown = set()
    for row in rows:
        pid = str(row.get("part_id") or row.get("id") or "")
        if pid:
            shown.add(pid)
        _, token = hub_cx_part_key(pid)
        if token:
            shown.add(token)
    extra = []
    for rel in (catalog.get("part_releases") or {}).values():
        slot = rel.get("slot") or guess_slot(rel.get("part_id") or "")
        if slot not in FAMILY_DISPLAY_SLOTS:
            continue
        set_id = str(rel.get("set_id") or "")
        base = str(rel.get("base_set_id") or "")
        if set_id not in family and base not in family:
            continue
        part_id = str(rel.get("part_id") or "")
        if not part_id or part_id in shown:
            continue
        rec = dict(parts.get(part_id) or {"id": part_id, "slot": slot})
        if not is_product_display_part(rec):
            continue
        extra.append(_display_row_from_release(rec, rel, part_id))
        shown.add(part_id)
    extra.sort(key=display_part_sort_key)
    rows.extend(extra)
    _add_missing_blades(catalog, product, parts, shown, rows)
    if any(
        (
            (row.get("slot") in BLADE_SLOTS)
            or (guess_slot(row.get("part_id") or "") in BLADE_SLOTS)
        )
        and (row.get("name_zh") or row.get("name_en"))
        for row in rows
    ):
        rows = [row for row in rows if not _unnamed_blade_row(row)]
    rows.sort(key=display_part_sort_key)
    return rows


def catalog_ids_for_model(model, products):
    model = str(model or "").strip().upper()
    if not model:
        return []
    ids = []
    products = products or {}
    if model in products:
        ids.append(model)
    prefix = model + "-"
    for product_id, rec in products.items():
        if product_id in ids:
            continue
        sku = str((rec or {}).get("sku") or "").strip().upper()
        if product_id.startswith(prefix) or sku == model:
            ids.append(product_id)
    return ids


def attach_shop_listings(catalog, shop_rows):
    products = catalog.get("products") or {}
    listings = []
    for row in shop_rows or []:
        model = str(row.get("model") or "").strip().upper()
        product_ids = catalog_ids_for_model(model, products)
        listing = {
            "shop_id": row.get("shop_id") or "",
            "sku": str(row.get("sku") or ""),
            "title": row.get("title") or "",
            "model": model,
            "price": row.get("price") or "",
            "url": row.get("url") or "",
            "status": row.get("status") or "",
            "status_label": row.get("status_label") or "",
            "in_stock": row.get("in_stock"),
            "product_ids": product_ids,
        }
        listings.append(listing)
        for product_id in product_ids:
            rec = products.get(product_id)
            if not rec:
                continue
            shops = rec.setdefault("shop_skus", [])
            item = {"shop_id": listing["shop_id"], "sku": listing["sku"]}
            if item not in shops:
                shops.append(item)
    catalog["shop_listings"] = listings
    return listings


def load_shop_listing_rows(data_dir=None):
    data_dir = data_dir or DATA_DIR
    rows = []
    if not os.path.isdir(data_dir):
        return rows
    for name in sorted(os.listdir(data_dir)):
        if name == "seen_skus.json":
            shop_id = "hobbyland"
        elif name.endswith("_seen_skus.json"):
            shop_id = name[: -len("_seen_skus.json")]
        else:
            continue
        path = os.path.join(data_dir, name)
        try:
            payload = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in payload.get("products") or []:
            rows.append(
                {
                    "shop_id": shop_id,
                    "sku": item.get("sku") or "",
                    "title": item.get("title") or "",
                    "model": item.get("model") or "",
                    "price": item.get("price") or "",
                    "url": item.get("url") or "",
                    "status": item.get("status") or "",
                    "status_label": item.get("status_label") or "",
                    "in_stock": item.get("in_stock"),
                }
            )
    return rows


SET_HINT_RE = re.compile(
    r"組|套組|對戰|入門|隨機|選集|紀念|multipack|dual pack|\bset\b", re.I
)
JUNK_PART_RE = re.compile(
    r"^(BT|BL|MB|OV|LC|AS|RC|HB|SR|RT)-|RATCHET-integrated|^■$",
    re.I,
)
ENGLISH_PART_RE = re.compile(r"^[A-Z]{5,}(?:\s+[A-Z]{2,})*$")


def is_set_product(rec):
    rec = rec or {}
    if rec.get("kind") in ("crossover_multipack", "accessory"):
        return True
    if len(rec.get("variant_ids") or []) > 1:
        return True
    name = "%s %s" % (rec.get("name_zh") or "", rec.get("name_en") or "")
    return bool(SET_HINT_RE.search(name))


def is_display_part(rec):
    pid = str((rec or {}).get("id") or "")
    if not pid or JUNK_PART_RE.search(pid):
        return False
    if ENGLISH_PART_RE.match(pid):
        return bool((rec or {}).get("name_zh") or (rec or {}).get("name_en"))
    return True


def is_product_display_part(rec):
    rec = rec or {}
    if is_display_part(rec):
        return True
    pid = str(rec.get("id") or "")
    if not pid or not JUNK_PART_RE.search(pid):
        return False
    slot = rec.get("slot") or guess_slot(pid)
    if slot != "blade":
        return False
    return bool(rec.get("name_zh") or rec.get("name_en"))


def _unnamed_blade_row(rec, part_id=""):
    rec = rec or {}
    pid = str(rec.get("part_id") or rec.get("id") or part_id or "")
    slot = rec.get("slot") or guess_slot(pid)
    if slot not in BLADE_SLOTS:
        return False
    return not (rec.get("name_zh") or rec.get("name_en"))


def is_internal_phstudy_id(product_id):
    return bool(INTERNAL_PHSTUDY_ID_RE.match(str(product_id or "").strip()))


def drop_internal_phstudy_products(catalog):
    catalog = catalog or {}
    products = catalog.get("products") or {}
    for pid in list(products):
        if is_internal_phstudy_id(pid):
            products.pop(pid, None)
    return catalog


def _combo_url_without_variant(url):
    url = str(url or "")
    return "combos/" in url and "-v" not in url.lower()


def hub_combo_image_url(product_id):
    slug = str(product_id or "").replace("-", "")
    if not slug:
        return ""
    return "%s/combos/%s.webp" % (HUB_IMG, urllib.parse.quote(slug, safe="._"))


def phstudy_retail_product_key(product_id):
    text = str(product_id or "").strip().upper()
    if not text:
        return ""
    match = re.match(r"^([A-Z]+)[-_]?(\d+)", text)
    if not match:
        return re.sub(r"[^A-Z0-9]", "", text)
    return match.group(1) + match.group(2)


def merge_phstudy_products_multilang(catalog, items):
    catalog = catalog or {}
    products = catalog.setdefault("products", {})
    by_id = {}
    for item in items or []:
        pid = str((item or {}).get("product_id") or "").strip()
        if pid:
            by_id[pid] = item
    for rec in products.values():
        key = phstudy_retail_product_key(rec.get("base_set_id") or rec.get("id"))
        item = by_id.get(key)
        if not item:
            continue
        images = item.get("images") or []
        if not images:
            continue
        rel = str(images[0] or "").lstrip("/")
        if rel:
            rec["box_image"] = "%s/%s" % (PHSTUDY_ORIGIN, rel)
    return catalog


def _product_image_urls(rec):
    rec = rec or {}
    image = rec.get("image") or ""
    hub = hub_combo_image_url(rec.get("id"))
    urls = []
    if is_set_product(rec):
        if rec.get("box_image"):
            urls.append(rec.get("box_image"))
        urls.append(phstudy_product_image_url(rec))
        if _combo_url_without_variant(image):
            urls.append(image)
        if hub:
            urls.append(hub)
        if image:
            urls.append(image)
    else:
        urls.append(phstudy_product_image_url(rec))
        if image:
            urls.append(image)
        if hub:
            urls.append(hub)
    out = []
    seen = set()
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def part_image_url(part):
    part = part or {}
    part_id = part.get("id") or ""
    slot = part.get("slot") or guess_slot(part_id)
    quoted = urllib.parse.quote(part_id, safe="._-")
    if slot == "bit":
        return "%s/bits/%s.webp" % (HUB_IMG, quoted)
    if slot == "ratchet":
        return "%s/ratchets/%s.webp" % (HUB_IMG, quoted)
    if part_id.startswith("cx-"):
        return "%s/blades-cx/%s.webp" % (
            HUB_IMG,
            urllib.parse.quote(part_id[len("cx-") :], safe="._-"),
        )
    if slot in BLADE_SLOTS:
        return "%s/blades-db/%s.webp" % (HUB_IMG, quoted)
    return ""


def phstudy_image_url(slot, item_id):
    item_id = str(item_id or "")
    if "MAINBLADE" in item_id.upper():
        folder = "MainBlade"
    else:
        folder = PHSTUDY_IMG_FOLDER.get(slot or "") or "Blade"
    return "%s/images/site/%s/%s.png" % (PHSTUDY_ORIGIN, folder, item_id)


def phstudy_product_image_url(product):
    ids = (product or {}).get("phstudy_ids") or {}
    for slot in (
        "blade",
        "metal_blade",
        "over_blade",
        "main_blade",
        "lock_chip",
        "assist_blade",
    ):
        item_id = ids.get(slot)
        if item_id:
            return phstudy_image_url(slot, item_id)
    return ""


def _lang_text(value, lang="zh-TW"):
    if isinstance(value, dict):
        return (
            value.get(lang)
            or value.get("zh-TW")
            or value.get("zh-HK")
            or value.get("ja-JP")
            or value.get("en-US")
            or value.get("en-SG")
            or ""
        )
    return str(value or "")


def parse_phstudy_series(rec, source="takara"):
    rec = rec or {}
    set_id = str(rec.get("set_id") or rec.get("base_set_id") or rec.get("id") or "").strip()
    line_match = LINE_RE.match(set_id)
    released = str(rec.get("release_at") or "")[:10]
    phstudy_ids = {}
    for field, slot in SERIES_PART_FIELDS:
        value = rec.get(field)
        if value:
            phstudy_ids[slot] = value
    tags = list(rec.get("tags") or [])
    if source == "hasbro" and "hasbro" not in tags:
        tags.append("hasbro")
    return {
        "id": set_id,
        "sku": set_id,
        "path_id": set_id,
        "line": (line_match.group(1) if line_match else "").upper(),
        "name_zh": _lang_text(rec.get("name") or rec.get("catalog_title")),
        "name_en": rec.get("en_name") or "",
        "base_set_id": rec.get("base_set_id") or set_id,
        "phstudy_id": rec.get("id") or "",
        "phstudy_ids": phstudy_ids,
        "tags": tags,
        "source": source,
        "released_on": released,
        "part_ids": [],
        "variant_ids": [],
    }


def parse_phstudy_part(rec, slot, source="takara"):
    rec = rec or {}
    part_id = str(rec.get("group_id") or rec.get("en_name") or rec.get("id") or "").strip()
    tags = list(rec.get("tags") or [])
    if source == "hasbro" and "hasbro" not in tags:
        tags.append("hasbro")
    return {
        "id": rec.get("id") or "",
        "part_id": part_id,
        "slot": slot,
        "set_id": rec.get("set_id") or "",
        "base_set_id": rec.get("base_set_id") or "",
        "color": rec.get("color") or "",
        "name_zh": _lang_text(rec.get("name") or rec.get("catalog_title")),
        "name_en": rec.get("en_name") or "",
        "tags": tags,
        "source": source,
        "image": phstudy_image_url(slot, rec.get("id") or ""),
    }


def merge_phstudy_data(catalog, payload, source="takara"):
    catalog = catalog or {}
    products = catalog.setdefault("products", {})
    parts = catalog.setdefault("parts", {})
    releases = catalog.setdefault("part_releases", {})
    payload = payload or {}

    hasbro_products = payload.get("hasbro_products")
    if isinstance(hasbro_products, dict):
        for code, rec in hasbro_products.items():
            rec = rec or {}
            product_id = str(rec.get("productCode") or code).strip()
            if not product_id:
                continue
            products.setdefault(
                product_id,
                {
                    "id": product_id,
                    "sku": product_id,
                    "path_id": product_id,
                    "line": "HASBRO",
                    "name_zh": _lang_text(rec.get("title_i18n"), "zh-TW")
                    or rec.get("title")
                    or product_id,
                    "name_en": rec.get("title") or "",
                    "source": "hasbro",
                    "kind": rec.get("category") or "",
                    "part_ids": [],
                    "variant_ids": [],
                    "tags": ["hasbro"],
                },
            )
        return catalog

    data = payload.get("data") or {}
    for table, slot in PHSTUDY_TABLE_SLOT.items():
        rows = data.get(table) or {}
        if not isinstance(rows, dict):
            continue
        for rec in rows.values():
            if rec.get("invalid"):
                continue
            release = parse_phstudy_part(rec, slot, source=source)
            if not release.get("id") or not release.get("part_id"):
                continue
            releases[release["id"]] = release
            part = parts.setdefault(
                release["part_id"],
                {
                    "id": release["part_id"],
                    "slot": slot,
                    "name_en": release.get("name_en") or "",
                    "name_zh": release.get("name_zh") or "",
                    "used_in": [],
                    "release_ids": [],
                },
            )
            if not part.get("slot"):
                part["slot"] = slot
            ids = part.setdefault("release_ids", [])
            if release["id"] not in ids:
                ids.append(release["id"])

    series_rows = data.get("BeybladeSeries") or {}
    if isinstance(series_rows, dict):
        for rec in series_rows.values():
            if rec.get("invalid"):
                continue
            parsed = parse_phstudy_series(rec, source=source)
            product_id = parsed["id"]
            if not product_id or is_internal_phstudy_id(product_id):
                continue
            part_ids = []
            for slot, phstudy_id in (parsed.get("phstudy_ids") or {}).items():
                release = releases.get(phstudy_id) or {}
                part_id = release.get("part_id")
                if part_id:
                    part_ids.append(part_id)
            parsed["part_ids"] = part_ids
            existing = products.get(product_id)
            if existing:
                tags = existing.setdefault("tags", [])
                for tag in parsed.get("tags") or []:
                    if tag not in tags:
                        tags.append(tag)
                if parsed.get("phstudy_id"):
                    existing.setdefault("phstudy_id", parsed["phstudy_id"])
                existing.setdefault("phstudy_ids", {}).update(parsed.get("phstudy_ids") or {})
                if parsed.get("base_set_id"):
                    existing.setdefault("base_set_id", parsed["base_set_id"])
                for part_id in part_ids:
                    _add_part_to_product(catalog, product_id, part_id)
            else:
                products[product_id] = parsed
                for part_id in part_ids:
                    _add_part_to_product(catalog, product_id, part_id)
    _rebuild_first_seen(catalog)
    return catalog


def fetch_phstudy_payloads(get_text):
    payloads = []
    for name, source in (
        ("main.json", "takara"),
        ("hasbro.json", "hasbro"),
        ("hardcoded.json", "hardcoded"),
    ):
        url = "%s/data/%s" % (PHSTUDY_ORIGIN, name)
        print("Phstudy fetch %s" % name)
        payloads.append((source, json.loads(get_text(url))))
    products_url = "%s/data/hasbro_products.json" % PHSTUDY_ORIGIN
    print("Phstudy fetch hasbro_products.json")
    payloads.append(
        ("hasbro", {"hasbro_products": json.loads(get_text(products_url))})
    )
    print("Phstudy fetch products_multilang.json")
    payloads.append(
        (
            "products_multilang",
            json.loads(
                get_text("%s/data/products_multilang.json" % PHSTUDY_ORIGIN)
            ),
        )
    )
    return payloads


def _safe_image_name(value):
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "item")).strip("._")
    return (text or "item")[:80]


def catalog_image_rel(kind, item_id):
    return "images/%s/%s.jpg" % (kind, _safe_image_name(item_id))


def _store_image(dest, url, get_bytes, overwrite=False):
    if not url or not get_bytes:
        return False
    if (not overwrite) and os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return True
    try:
        raw = get_bytes(url)
    except Exception as exc:
        if url.endswith(".png"):
            try:
                raw = get_bytes(url[:-4] + ".jpg")
            except Exception:
                print("Part image failed (%s): %s" % (url, exc), file=sys.stderr)
                return False
        else:
            print("Part image failed (%s): %s" % (url, exc), file=sys.stderr)
            return False
    if not raw or len(raw) < 32:
        return False
    if raw[:15].lstrip().startswith(b"<!DOCTYPE") or raw[:6].lstrip().startswith(b"<html"):
        return False
    if raw[:5].lstrip().startswith(b"<?xml"):
        return False
    body = raw
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, dest)
    return True


def download_catalog_images(catalog, get_bytes, dest_dir=None, overwrite=False):
    dest_dir = dest_dir or PARTS_DIR
    saved = 0
    products = catalog.get("products") or {}
    variants = catalog.get("variants") or {}
    parts = catalog.get("parts") or {}
    jobs = []
    for rec in products.values():
        urls = _product_image_urls(rec)
        if urls:
            jobs.append(("products", rec["id"], urls, rec, "image_path"))
        if rec.get("box_image"):
            jobs.append(("boxes", rec["id"], [rec["box_image"]], rec, "box_image_path"))
    for rec in variants.values():
        if rec.get("image"):
            jobs.append(("variants", rec["id"], [rec["image"]], rec, "image_path"))
    for rec in parts.values():
        url = part_image_url(rec)
        if url:
            jobs.append(("parts", rec["id"], [url], rec, "image_path"))
    for rec in (catalog.get("part_releases") or {}).values():
        url = rec.get("image") or phstudy_image_url(rec.get("slot"), rec.get("id"))
        if url and rec.get("id"):
            jobs.append(("releases", rec["id"], [url], rec, "image_path"))
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def run_job(job):
        kind, item_id, urls, rec, path_key = job
        rel = catalog_image_rel(kind, item_id)
        dest = os.path.join(dest_dir, rel)
        ok = False
        force = overwrite or (kind == "products" and is_set_product(rec))
        for url in urls:
            if _store_image(dest, url, get_bytes, overwrite=force):
                ok = True
                break
        return rec, rel, ok, path_key

    workers = 8 if len(jobs) > 20 else 1
    if workers == 1:
        results = [run_job(job) for job in jobs]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(run_job, job) for job in jobs]
            for fut in as_completed(futs):
                results.append(fut.result())
    for rec, rel, ok, path_key in results:
        if ok:
            rec[path_key] = rel
            saved += 1
    print("Part images saved: %d / %d" % (saved, len(jobs)))
    return saved


def build_catalog(pages):
    products = {}
    variants = {}
    parts = {}
    contains = []
    variant_of = []
    for page in pages or []:
        product_id = page.get("id")
        if not product_id:
            continue
        part_ids = []
        for part in page.get("parts") or []:
            part_id = part["id"]
            part_ids.append(part_id)
            rec = parts.setdefault(
                part_id,
                {
                    "id": part_id,
                    "slot": part.get("slot") or "",
                    "name_en": part.get("name_en") or "",
                    "name_zh": part.get("name_zh") or "",
                    "label": part.get("label") or "",
                    "href": part.get("href") or "",
                    "used_in": [],
                },
            )
            if part.get("name_en") and not rec.get("name_en"):
                rec["name_en"] = part["name_en"]
            if part.get("name_zh") and not rec.get("name_zh"):
                rec["name_zh"] = part["name_zh"]
            if part.get("slot") and not rec.get("slot"):
                rec["slot"] = part["slot"]
            if product_id not in rec["used_in"]:
                rec["used_in"].append(product_id)
            contains.append(
                {
                    "product_id": product_id,
                    "part_id": part_id,
                    "slot": part.get("slot") or rec.get("slot") or "",
                }
            )
        products[product_id] = {
            "id": product_id,
            "sku": page.get("sku") or product_id,
            "path_id": page.get("path_id") or product_id,
            "line": page.get("line") or "",
            "name_zh": page.get("name_zh") or "",
            "jan": page.get("jan") or "",
            "description": page.get("description") or "",
            "released_on": page.get("released_on") or "",
            "price_jpy": page.get("price_jpy"),
            "bey_type": page.get("bey_type") or "",
            "stock_combo": page.get("stock_combo") or "",
            "image": page.get("image") or "",
            "source_url": page.get("source_url") or "",
            "part_ids": part_ids,
            "variant_ids": [row["id"] for row in page.get("variants") or []],
        }
        for row in page.get("variants") or []:
            variants[row["id"]] = dict(row)
            variant_of.append(
                {"variant_id": row["id"], "product_id": row["product_id"]}
            )

    def sort_key(product_id):
        rec = products.get(product_id) or {}
        return (rec.get("released_on") or "9999-99-99", product_id)

    first_seen = []
    for part in parts.values():
        part["used_in"] = sorted(part["used_in"])
        earliest = sorted(part["used_in"], key=sort_key)
        part["first_seen_in"] = earliest[0] if earliest else ""
        if part["first_seen_in"]:
            first_seen.append(
                {"part_id": part["id"], "product_id": part["first_seen_in"]}
            )

    return {
        "meta": {
            "source": HUB_ORIGIN,
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "products": products,
        "variants": variants,
        "parts": parts,
        "relations": {
            "contains": contains,
            "variant_of": variant_of,
            "first_seen_in": first_seen,
        },
    }


def write_catalog(catalog, dest_dir=None):
    dest_dir = dest_dir or PARTS_DIR
    os.makedirs(dest_dir, exist_ok=True)
    paths = {
        "products": os.path.join(dest_dir, "products.json"),
        "variants": os.path.join(dest_dir, "variants.json"),
        "parts": os.path.join(dest_dir, "parts.json"),
        "relations": os.path.join(dest_dir, "relations.json"),
        "meta": os.path.join(dest_dir, "meta.json"),
        "shop_listings": os.path.join(dest_dir, "shop_listings.json"),
        "part_releases": os.path.join(dest_dir, "part_releases.json"),
    }
    drop_internal_phstudy_products(catalog)
    _dump(paths["products"], catalog.get("products") or {})
    _dump(paths["variants"], catalog.get("variants") or {})
    _dump(paths["parts"], catalog.get("parts") or {})
    _dump(paths["relations"], catalog.get("relations") or {})
    _dump(paths["meta"], catalog.get("meta") or {})
    _dump(paths["shop_listings"], catalog.get("shop_listings") or [])
    _dump(paths["part_releases"], catalog.get("part_releases") or {})
    if catalog.get("products_multilang") is not None:
        paths["products_multilang"] = os.path.join(dest_dir, "products_multilang.json")
        _dump(paths["products_multilang"], catalog.get("products_multilang") or [])
    return paths


def load_catalog(dest_dir=None):
    dest_dir = dest_dir or PARTS_DIR
    catalog = {
        "products": _load(os.path.join(dest_dir, "products.json"), {}),
        "variants": _load(os.path.join(dest_dir, "variants.json"), {}),
        "parts": _load(os.path.join(dest_dir, "parts.json"), {}),
        "relations": _load(os.path.join(dest_dir, "relations.json"), {}),
        "meta": _load(os.path.join(dest_dir, "meta.json"), {}),
        "shop_listings": _load(os.path.join(dest_dir, "shop_listings.json"), []),
        "part_releases": _load(os.path.join(dest_dir, "part_releases.json"), {}),
    }
    items = _load(os.path.join(dest_dir, "products_multilang.json"), [])
    if items:
        merge_phstudy_products_multilang(catalog, items)
    drop_internal_phstudy_products(catalog)
    return catalog


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _dump(path, payload):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def refresh_parts_catalog(
    get_text, get_bytes=None, sleep_s=0.15, dest_dir=None, scrape=True
):
    dest_dir = dest_dir or PARTS_DIR
    if scrape:
        xml_text = get_text(HUB_SITEMAP)
        urls = parse_hub_sitemap(xml_text)
        pages = []
        for i, url in enumerate(urls):
            html = get_text(url)
            pages.append(parse_hub_combo_page(html, url))
            print("Parts catalog %d/%d %s" % (i + 1, len(urls), url.rsplit("/", 1)[-1]))
            if sleep_s and i + 1 < len(urls):
                time.sleep(sleep_s)
        catalog = build_catalog(pages)
        catalog["meta"]["combo_pages"] = len(pages)
    else:
        catalog = load_catalog(dest_dir)
    fill_missing_parts(catalog)
    try:
        for source, payload in fetch_phstudy_payloads(get_text):
            if source == "products_multilang":
                catalog["products_multilang"] = payload
                merge_phstudy_products_multilang(catalog, payload)
                continue
            merge_phstudy_data(catalog, payload, source=source)
        catalog.setdefault("meta", {}).setdefault("sources", [])
        if PHSTUDY_ORIGIN not in catalog["meta"]["sources"]:
            catalog["meta"]["sources"].append(PHSTUDY_ORIGIN)
        catalog["meta"]["part_releases"] = len(catalog.get("part_releases") or {})
    except Exception as exc:
        print("Phstudy merge failed: %s" % exc, file=sys.stderr)
    attach_shop_listings(catalog, load_shop_listing_rows())
    if get_bytes:
        download_catalog_images(catalog, get_bytes, dest_dir=dest_dir)
    catalog.setdefault("meta", {})["built_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    paths = write_catalog(catalog, dest_dir)
    empty = [
        pid
        for pid, rec in (catalog.get("products") or {}).items()
        if not rec.get("part_ids")
    ]
    print(
        "Parts catalog done: %d products, %d variants, %d parts, %d part releases, %d shop links."
        % (
            len(catalog.get("products") or {}),
            len(catalog.get("variants") or {}),
            len(catalog.get("parts") or {}),
            len(catalog.get("part_releases") or {}),
            len(catalog.get("shop_listings") or {}),
        )
    )
    if empty:
        print("Missing parts: %s" % ", ".join(empty))
    return paths


def main(argv=None):
    raise SystemExit("parts catalog refresh runs from the watch repository")


if __name__ == "__main__":
    raise SystemExit(main())
