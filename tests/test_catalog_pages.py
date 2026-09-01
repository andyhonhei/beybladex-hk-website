#!/usr/bin/env python3
import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from parts_catalog import (
    attach_shop_listings,
    build_catalog,
    catalog_ids_for_model,
    fill_missing_parts,
    hub_combo_image_url,
    is_display_part,
    is_set_product,
    merge_phstudy_data,
    parse_combo_from_name,
    parse_hub_combo_page,
    parse_hub_sitemap,
    parse_phstudy_series,
    part_image_url,
    phstudy_image_url,
    write_catalog,
    _product_image_urls,
)


CX19_HTML = """
<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"Product","name":"巨鱷碾壓選集（CX-19）","sku":"CX-19","gtin13":"4904810080626","image":"https://img.beybladehub.app/combos/CX19.webp","description":"Crocotread Select","releaseDate":"2026-09-12","additionalProperty":[{"@type":"PropertyValue","name":"類型","value":"防禦型"},{"@type":"PropertyValue","name":"原裝配置","value":"5-50GN"}],"offers":{"@type":"Offer","price":1600,"priceCurrency":"JPY"}}]}</script>
</head><body>
包含款式（3 款隨機）
<img src="https://img.beybladehub.app/combos/CX19-v01.webp" alt="巨鱷碾壓 TQ5-50GN（金色）"/>
<img src="https://img.beybladehub.app/combos/CX19-v02.webp" alt="巨鱷碾壓 TQ5-50GN（紅色）"/>
<img src="https://img.beybladehub.app/combos/CX19-v03.webp" alt="巨鱷碾壓 TQ5-50GN（灰色）"/>
內含零件
<a href="/parts/blades#blade-cx-chip-Co">鎖定紋章 Co 巨鱷</a>
<a href="/parts/blades#blade-cx-metal-Tr">金屬戰刃 Tr 碾壓</a>
<a href="/parts/blades#blade-cx-over-T">超越戰刃 T</a>
<a href="/parts/blades#blade-cx-assist-Q">輔助戰刃 Q</a>
<a href="/parts/ratchets#ratchet-5-50">固鎖 5-50</a>
<a href="/parts/bits#bit-GN">軸心 GN Gear Needle</a>
</body></html>
"""

UX00_HTML = """
<html><head>
<script type="application/ld+json">{"@graph":[{"@type":"Product","name":"飛龍颶風（UX-00）","sku":"UX-00","releaseDate":"2025-01-01","offers":{"price":1600,"priceCurrency":"JPY"}}]}</script>
</head><body>
<a href="/parts/bits#bit-GN">軸心 GN Gear Needle</a>
<a href="/parts/ratchets#ratchet-2-80">固鎖 2-80</a>
</body></html>
"""

SITEMAP = """
<urlset>
  <loc>https://beybladehub.app/parts/combos</loc>
  <loc>https://beybladehub.app/parts/combos/CX-19</loc>
  <loc>https://beybladehub.app/en/parts/combos/CX-19</loc>
  <loc>https://beybladehub.app/parts/combos/UX-00-wyvern-hover</loc>
</urlset>
"""


class PartsCatalogTests(unittest.TestCase):
    def test_parse_cx19_product_variants_and_parts(self):
        page = parse_hub_combo_page(
            CX19_HTML, "https://beybladehub.app/parts/combos/CX-19"
        )
        self.assertEqual(page["id"], "CX-19")
        self.assertEqual(page["line"], "CX")
        self.assertEqual(page["jan"], "4904810080626")
        self.assertEqual(page["price_jpy"], 1600)
        self.assertEqual(page["released_on"], "2026-09-12")
        self.assertEqual(
            [p["id"] for p in page["parts"]],
            [
                "cx-chip-Co",
                "cx-metal-Tr",
                "cx-over-T",
                "cx-assist-Q",
                "5-50",
                "GN",
            ],
        )
        self.assertEqual(page["parts"][-1]["slot"], "bit")
        self.assertEqual(page["parts"][-1]["name_en"], "Gear Needle")
        self.assertEqual([v["id"] for v in page["variants"]], ["CX-19-01", "CX-19-02", "CX-19-03"])
        self.assertEqual(page["variants"][2]["name_zh"], "巨鱷碾壓 TQ5-50GN（灰色）")

    def test_sitemap_keeps_zh_combo_urls_only(self):
        urls = parse_hub_sitemap(SITEMAP)
        self.assertEqual(
            urls,
            [
                "https://beybladehub.app/parts/combos/CX-19",
                "https://beybladehub.app/parts/combos/UX-00-wyvern-hover",
            ],
        )

    def test_relations_mark_gn_as_part_of_cx19_and_first_seen(self):
        pages = [
            parse_hub_combo_page(UX00_HTML, "https://beybladehub.app/parts/combos/UX-00-wyvern-hover"),
            parse_hub_combo_page(CX19_HTML, "https://beybladehub.app/parts/combos/CX-19"),
        ]
        catalog = build_catalog(pages)
        gn = catalog["parts"]["GN"]
        self.assertEqual(sorted(gn["used_in"]), ["CX-19", "UX-00-wyvern-hover"])
        self.assertEqual(gn["first_seen_in"], "UX-00-wyvern-hover")
        self.assertIn("GN", catalog["products"]["CX-19"]["part_ids"])
        self.assertEqual(catalog["variants"]["CX-19-03"]["product_id"], "CX-19")
        q = catalog["parts"]["cx-assist-Q"]
        self.assertEqual(q["first_seen_in"], "CX-19")
        self.assertEqual(q["slot"], "assist_blade")

    def test_write_catalog_files(self):
        pages = [
            parse_hub_combo_page(CX19_HTML, "https://beybladehub.app/parts/combos/CX-19"),
        ]
        catalog = build_catalog(pages)
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_catalog(catalog, tmp)
            self.assertTrue(os.path.isfile(paths["products"]))
            self.assertTrue(os.path.isfile(paths["variants"]))
            self.assertTrue(os.path.isfile(paths["parts"]))
            self.assertTrue(os.path.isfile(paths["relations"]))

    def test_parse_combo_from_variant_names(self):
        self.assertEqual(
            parse_combo_from_name("腕龍鞭打 OW5-70Nr（標準色）"),
            {"prefix": "OW", "ratchet": "5-70", "bit": "Nr", "label": "腕龍鞭打"},
        )
        self.assertEqual(
            parse_combo_from_name("蒼穹龍騎士 9-80F"),
            {"prefix": "", "ratchet": "9-80", "bit": "F", "label": "蒼穹龍騎士"},
        )
        self.assertEqual(
            parse_combo_from_name("極狐九尾 J9-70GR"),
            {"prefix": "J", "ratchet": "9-70", "bit": "GR", "label": "極狐九尾"},
        )

    def test_fill_missing_parts_from_variants_and_cx07_stock(self):
        catalog = {
            "products": {
                "BX-34": {
                    "id": "BX-34",
                    "name_zh": "蒼穹龍騎士（BX-34）",
                    "part_ids": ["CbDg", "2-60", "C"],
                    "variant_ids": [],
                },
                "BX-48": {
                    "id": "BX-48",
                    "name_zh": "隨機強化組 Vol.9（BX-48）",
                    "part_ids": [],
                    "variant_ids": ["BX-48-01"],
                },
                "CX-18": {
                    "id": "CX-18",
                    "name_zh": "腕龍鞭打選集（CX-18）",
                    "part_ids": [],
                    "variant_ids": ["CX-18-01"],
                },
                "CX-07": {
                    "id": "CX-07",
                    "name_zh": "天馬爆擊（CX-07）",
                    "part_ids": [],
                    "variant_ids": [],
                },
            },
            "variants": {
                "BX-48-01": {
                    "id": "BX-48-01",
                    "product_id": "BX-48",
                    "name_zh": "蒼穹龍騎士 9-80F",
                },
                "CX-18-01": {
                    "id": "CX-18-01",
                    "product_id": "CX-18",
                    "name_zh": "腕龍鞭打 OW5-70Nr（標準色）",
                },
            },
            "parts": {
                "CbDg": {"id": "CbDg", "slot": "blade", "used_in": ["BX-34"]},
                "2-60": {"id": "2-60", "slot": "ratchet", "used_in": ["BX-34"]},
                "C": {"id": "C", "slot": "bit", "used_in": ["BX-34"]},
            },
            "relations": {"contains": [], "variant_of": [], "first_seen_in": []},
        }
        fill_missing_parts(catalog)
        self.assertIn("CbDg", catalog["products"]["BX-48"]["part_ids"])
        self.assertIn("9-80", catalog["products"]["BX-48"]["part_ids"])
        self.assertIn("F", catalog["products"]["BX-48"]["part_ids"])
        self.assertIn("cx-over-O", catalog["products"]["CX-18"]["part_ids"])
        self.assertIn("cx-assist-W", catalog["products"]["CX-18"]["part_ids"])
        self.assertIn("5-70", catalog["products"]["CX-18"]["part_ids"])
        self.assertIn("Nr", catalog["products"]["CX-18"]["part_ids"])
        self.assertIn("cx-main-Bs", catalog["products"]["CX-07"]["part_ids"])
        self.assertIn("Tr", catalog["products"]["CX-07"]["part_ids"])
        self.assertIn("BX-48", catalog["parts"]["CbDg"]["used_in"])

    def test_shop_model_joins_cx19_and_ux00_limited(self):
        products = {
            "CX-19": {"id": "CX-19", "sku": "CX-19"},
            "UX-00-wyvern-hover": {"id": "UX-00-wyvern-hover", "sku": "UX-00"},
            "BX-01": {"id": "BX-01", "sku": "BX-01"},
        }
        self.assertEqual(catalog_ids_for_model("CX-19", products), ["CX-19"])
        self.assertEqual(
            catalog_ids_for_model("UX-00", products), ["UX-00-wyvern-hover"]
        )
        listings = attach_shop_listings(
            {"products": products, "variants": {}, "parts": {}, "relations": {}},
            [
                {
                    "shop_id": "moonroadhk",
                    "sku": "1",
                    "title": "Takara Tomy CX-19 鱷魚戰紋",
                    "model": "CX-19",
                    "status": "out_of_stock",
                    "status_label": "缺貨",
                    "in_stock": False,
                }
            ],
        )
        self.assertEqual(listings[0]["product_ids"], ["CX-19"])
        self.assertEqual(listings[0]["status"], "out_of_stock")
        self.assertEqual(listings[0]["status_label"], "缺貨")
        self.assertIs(listings[0]["in_stock"], False)
        self.assertEqual(
            products["CX-19"]["shop_skus"],
            [{"shop_id": "moonroadhk", "sku": "1"}],
        )

    def test_part_image_url_by_slot(self):
        self.assertEqual(
            part_image_url({"id": "GN", "slot": "bit"}),
            "https://img.beybladehub.app/bits/GN.webp",
        )
        self.assertEqual(
            part_image_url({"id": "5-50", "slot": "ratchet"}),
            "https://img.beybladehub.app/ratchets/5-50.webp",
        )
        self.assertEqual(
            part_image_url({"id": "cx-assist-Q", "slot": "assist_blade"}),
            "https://img.beybladehub.app/blades-cx/assist-Q.webp",
        )
        self.assertEqual(
            part_image_url({"id": "LIGHTNING L-DRAGO", "slot": "blade"}),
            "https://img.beybladehub.app/blades-db/LIGHTNING%20L-DRAGO.webp",
        )
        self.assertEqual(
            hub_combo_image_url("BXG-79"),
            "https://img.beybladehub.app/combos/BXG79.webp",
        )
        self.assertTrue(is_set_product({"name_zh": "隨機強化組 Vol.6", "variant_ids": ["a", "b"]}))
        self.assertFalse(is_display_part({"id": "DRANSTRIKE"}))
        self.assertFalse(is_display_part({"id": "■"}))
        self.assertTrue(is_display_part({"id": "GN"}))
        urls = _product_image_urls(
            {
                "id": "BX-20",
                "name_zh": "蒼龍利刃改造組",
                "image": "https://img.beybladehub.app/blades-db/DrDg.webp",
                "variant_ids": ["BX-20-02"],
            }
        )
        self.assertEqual(urls[0], "https://img.beybladehub.app/combos/BX20.webp")

    def test_parse_phstudy_series_limited_color(self):
        rec = parse_phstudy_series(
            {
                "id": "SR-EVE-077428-01",
                "set_id": "BXH-25-01",
                "base_set_id": "BXH-25",
                "en_name": "DRANSTRIKE",
                "blade_id": "BL-EVE-077428-01",
                "bit_id": "BT-EVE-077428-01",
                "ratchet_id": "RT-EVE-077428-01",
                "tags": ["bx", "convention"],
                "release_at": "2026-05-05T15:00:00.000Z",
                "name": {"zh-TW": "BXH-25-01 蒼龍突擊 金屬塗層:燦金"},
            }
        )
        self.assertEqual(rec["id"], "BXH-25-01")
        self.assertEqual(rec["base_set_id"], "BXH-25")
        self.assertIn("convention", rec["tags"])
        self.assertEqual(rec["released_on"], "2026-05-05")
        self.assertEqual(rec["phstudy_ids"]["blade"], "BL-EVE-077428-01")

    def test_merge_phstudy_adds_color_release_and_hasbro_product(self):
        catalog = {
            "products": {
                "CX-19": {
                    "id": "CX-19",
                    "sku": "CX-19",
                    "part_ids": ["GN"],
                    "source": "hub",
                }
            },
            "parts": {"GN": {"id": "GN", "slot": "bit", "used_in": ["CX-19"]}},
            "variants": {},
            "relations": {"contains": [], "variant_of": [], "first_seen_in": []},
            "part_releases": {},
        }
        payload = {
            "data": {
                "BeybladeSeries": {
                    "SR-1": {
                        "id": "SR-1",
                        "set_id": "BX-27-01",
                        "base_set_id": "BX-27",
                        "bit_id": "BT-GN-1",
                        "tags": ["bx", "reprint"],
                        "name": {"zh-TW": "BX-27-01 幻神護甲"},
                        "release_at": "2024-02-22T00:00:00.000Z",
                    }
                },
                "BeybladePartsBit": {
                    "BT-GN-1": {
                        "id": "BT-GN-1",
                        "group_id": "GN",
                        "en_name": "GN",
                        "set_id": "BX-27-01",
                        "color": "gold",
                        "tags": ["bx"],
                        "name": {"zh-TW": "GN 金色"},
                    }
                },
            }
        }
        hasbro_products = {
            "F9324": {
                "productCode": "F9324",
                "title": "Soar Phoenix Deluxe String Launcher Set",
                "category": "accessory",
            }
        }
        merge_phstudy_data(catalog, payload, source="takara")
        merge_phstudy_data(catalog, {"hasbro_products": hasbro_products}, source="hasbro")
        self.assertIn("BX-27-01", catalog["products"])
        self.assertIn("reprint", catalog["products"]["BX-27-01"]["tags"])
        self.assertEqual(catalog["part_releases"]["BT-GN-1"]["part_id"], "GN")
        self.assertEqual(catalog["part_releases"]["BT-GN-1"]["color"], "gold")
        self.assertIn("BX-27-01", catalog["parts"]["GN"]["used_in"])
        self.assertEqual(catalog["products"]["F9324"]["source"], "hasbro")
        self.assertEqual(
            phstudy_image_url("bit", "BT-GN-1"),
            "https://beyblade.phstudy.org/images/site/Bit/BT-GN-1.png",
        )


if __name__ == "__main__":
    unittest.main()
