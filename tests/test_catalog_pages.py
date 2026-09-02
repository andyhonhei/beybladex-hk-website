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
    is_internal_phstudy_id,
    is_set_product,
    merge_phstudy_data,
    merge_phstudy_products_multilang,
    phstudy_retail_product_key,
    parse_combo_from_name,
    parse_hub_combo_page,
    parse_hub_sitemap,
    parse_phstudy_series,
    part_image_url,
    phstudy_image_url,
    display_parts_for_product,
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

    def test_cx18_uses_own_570_release_not_ux03(self):
        catalog = {
            "products": {
                "CX-18": {
                    "id": "CX-18",
                    "part_ids": ["5-70", "Nr"],
                    "variant_ids": ["CX-18-01"],
                },
                "CX-18-01": {
                    "id": "CX-18-01",
                    "base_set_id": "CX-18",
                    "part_ids": ["5-70"],
                },
                "UX-03": {"id": "UX-03", "part_ids": ["5-70"]},
            },
            "parts": {
                "5-70": {
                    "id": "5-70",
                    "slot": "ratchet",
                    "name_zh": "固鎖",
                    "first_seen_in": "UX-03",
                    "image_path": "images/parts/5-70.jpg",
                    "release_ids": ["RC-UX-03", "RC-CX-18-01"],
                    "used_in": ["UX-03", "CX-18"],
                },
                "Nr": {
                    "id": "Nr",
                    "slot": "bit",
                    "first_seen_in": "CX-18-01",
                    "used_in": ["CX-18"],
                },
            },
            "part_releases": {
                "RC-UX-03": {
                    "id": "RC-UX-03",
                    "part_id": "5-70",
                    "set_id": "UX-03",
                    "base_set_id": "UX-03",
                    "image_path": "images/releases/ux03-570.jpg",
                    "name_zh": "UX-03 5-70",
                },
                "RC-CX-18-01": {
                    "id": "RC-CX-18-01",
                    "part_id": "5-70",
                    "set_id": "CX-18-01",
                    "base_set_id": "CX-18",
                    "image_path": "images/releases/cx18-570.jpg",
                    "name_zh": "CX-18-01 5-70",
                },
            },
        }
        rows = display_parts_for_product(catalog, catalog["products"]["CX-18"])
        by_id = {row["part_id"]: row for row in rows}
        self.assertEqual(by_id["5-70"]["image_path"], "images/releases/cx18-570.jpg")
        self.assertEqual(by_id["5-70"]["set_id"], "CX-18-01")
        self.assertNotEqual(by_id["5-70"].get("first_seen_in"), "UX-03")
        self.assertIn("Nr", by_id)

    def test_omits_shared_part_without_own_release(self):
        catalog = {
            "products": {
                "CX-18": {"id": "CX-18", "part_ids": ["5-70", "cx-over-O"]},
                "UX-03": {"id": "UX-03", "part_ids": ["5-70"]},
            },
            "parts": {
                "5-70": {
                    "id": "5-70",
                    "slot": "ratchet",
                    "first_seen_in": "UX-03",
                    "release_ids": ["RC-UX-03"],
                    "used_in": ["UX-03", "CX-18"],
                },
                "cx-over-O": {
                    "id": "cx-over-O",
                    "slot": "over_blade",
                    "first_seen_in": "CX-18",
                    "used_in": ["CX-18"],
                },
            },
            "part_releases": {
                "RC-UX-03": {
                    "id": "RC-UX-03",
                    "part_id": "5-70",
                    "set_id": "UX-03",
                    "base_set_id": "UX-03",
                },
            },
        }
        rows = display_parts_for_product(catalog, catalog["products"]["CX-18"])
        ids = [row["part_id"] for row in rows]
        self.assertNotIn("5-70", ids)
        self.assertIn("cx-over-O", ids)

    def test_cx18_assist_uses_own_release_not_cx08(self):
        catalog = {
            "products": {
                "CX-18": {
                    "id": "CX-18",
                    "part_ids": ["cx-assist-W"],
                    "variant_ids": ["CX-18-01"],
                },
                "CX-18-01": {"id": "CX-18-01", "base_set_id": "CX-18"},
                "CX-08": {"id": "CX-08", "part_ids": ["cx-assist-W"]},
            },
            "parts": {
                "cx-assist-W": {
                    "id": "cx-assist-W",
                    "slot": "assist_blade",
                    "first_seen_in": "CX-08",
                    "image_path": "images/parts/cx-assist-W.jpg",
                    "used_in": ["CX-08", "CX-18"],
                },
            },
            "part_releases": {
                "AB-CX-08": {
                    "id": "AB-CX-08",
                    "part_id": "W",
                    "slot": "assist_blade",
                    "set_id": "CX-08-01",
                    "base_set_id": "CX-08",
                    "image_path": "images/releases/cx08-w.jpg",
                },
                "AB-CX-18": {
                    "id": "AB-CX-18",
                    "part_id": "W",
                    "slot": "assist_blade",
                    "set_id": "CX-18-01",
                    "base_set_id": "CX-18",
                    "image_path": "images/releases/cx18-w.jpg",
                    "name_zh": "CX-18-01 W",
                },
            },
        }
        rows = display_parts_for_product(catalog, catalog["products"]["CX-18"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["image_path"], "images/releases/cx18-w.jpg")
        self.assertEqual(rows[0]["set_id"], "CX-18-01")
        self.assertNotEqual(rows[0].get("image_path"), "images/parts/cx-assist-W.jpg")

    def test_select_set_uses_family_ratchet_not_hub_pollution(self):
        catalog = {
            "products": {
                "BX-36": {
                    "id": "BX-36",
                    "part_ids": ["WhWv", "5-60"],
                    "variant_ids": ["BX-36-01"],
                },
                "BX-36-01": {
                    "id": "BX-36-01",
                    "base_set_id": "BX-36",
                    "part_ids": ["5-80", "E"],
                },
                "BX-15": {"id": "BX-15", "part_ids": ["5-60"]},
            },
            "parts": {
                "WhWv": {"id": "WhWv", "slot": "blade", "first_seen_in": "BX-36"},
                "5-60": {
                    "id": "5-60",
                    "slot": "ratchet",
                    "first_seen_in": "BX-15",
                    "release_ids": ["RC-BX-15"],
                },
                "5-80": {"id": "5-80", "slot": "ratchet"},
                "E": {"id": "E", "slot": "bit"},
            },
            "part_releases": {
                "RC-BX-15": {
                    "id": "RC-BX-15",
                    "part_id": "5-60",
                    "set_id": "BX-15",
                    "base_set_id": "BX-15",
                    "slot": "ratchet",
                },
                "RC-BX-36-01": {
                    "id": "RC-BX-36-01",
                    "part_id": "5-80",
                    "set_id": "BX-36-01",
                    "base_set_id": "BX-36",
                    "slot": "ratchet",
                    "image_path": "images/releases/bx36-580.jpg",
                },
                "BT-BX-36-01": {
                    "id": "BT-BX-36-01",
                    "part_id": "E",
                    "set_id": "BX-36-01",
                    "base_set_id": "BX-36",
                    "slot": "bit",
                    "image_path": "images/releases/bx36-e.jpg",
                },
            },
        }
        rows = display_parts_for_product(catalog, catalog["products"]["BX-36"])
        by_id = {row["part_id"]: row for row in rows}
        self.assertNotIn("5-60", by_id)
        self.assertEqual(by_id["5-80"]["image_path"], "images/releases/bx36-580.jpg")
        self.assertEqual(by_id["E"]["image_path"], "images/releases/bx36-e.jpg")
        self.assertIn("WhWv", by_id)

    def test_random_booster_lists_named_family_blades_not_hub_code(self):
        catalog = {
            "products": {
                "UX-12": {
                    "id": "UX-12",
                    "name_zh": "UX-12 隨機強化組 Vol.5",
                    "part_ids": ["GhCr"],
                    "variant_ids": ["UX-12-01", "UX-12-03"],
                },
                "UX-12-01": {
                    "id": "UX-12-01",
                    "base_set_id": "UX-12",
                    "part_ids": ["GHOSTCIRCLE"],
                },
                "UX-12-03": {
                    "id": "UX-12-03",
                    "base_set_id": "UX-12",
                    "part_ids": ["SHINOBISHADOW"],
                },
            },
            "parts": {
                "GhCr": {"id": "GhCr", "slot": "blade", "first_seen_in": "UX-12"},
                "GHOSTCIRCLE": {
                    "id": "GHOSTCIRCLE",
                    "slot": "blade",
                    "name_zh": "BX-50-04 幽靈元魂",
                },
                "SHINOBISHADOW": {
                    "id": "SHINOBISHADOW",
                    "slot": "blade",
                    "name_zh": "UX-05-01 忍者闇影",
                },
            },
            "part_releases": {
                "BL-UX-12-01": {
                    "id": "BL-UX-12-01",
                    "part_id": "GHOSTCIRCLE",
                    "slot": "blade",
                    "set_id": "UX-12-01",
                    "base_set_id": "UX-12",
                    "name_zh": "幽靈元魂",
                },
                "BL-UX-12-03": {
                    "id": "BL-UX-12-03",
                    "part_id": "SHINOBISHADOW",
                    "slot": "blade",
                    "set_id": "UX-12-03",
                    "base_set_id": "UX-12",
                    "name_zh": "忍者闇影",
                },
            },
        }
        rows = display_parts_for_product(catalog, catalog["products"]["UX-12"])
        ids = [row["part_id"] for row in rows]
        self.assertNotIn("GhCr", ids)
        self.assertEqual(
            {row["part_id"]: row["name_zh"] for row in rows},
            {"GHOSTCIRCLE": "幽靈元魂", "SHINOBISHADOW": "忍者闇影"},
        )

    def test_product_keeps_named_phstudy_blade(self):
        catalog = {
            "products": {
                "BXA-01": {
                    "id": "BXA-01",
                    "part_ids": ["BL-PRD-939672-00", "3-60", "F"],
                }
            },
            "parts": {
                "BL-PRD-939672-00": {
                    "id": "BL-PRD-939672-00",
                    "slot": "blade",
                    "name_zh": "BXA-01 蒼龍神劍",
                    "first_seen_in": "BXA-01",
                    "release_ids": ["BL-PRD-939672-00"],
                },
                "3-60": {"id": "3-60", "slot": "ratchet", "name_zh": "固鎖"},
                "F": {"id": "F", "slot": "bit", "name_zh": "軸心"},
            },
            "part_releases": {
                "BL-PRD-939672-00": {
                    "id": "BL-PRD-939672-00",
                    "part_id": "BL-PRD-939672-00",
                    "slot": "blade",
                    "set_id": "BXA-01",
                    "name_zh": "BXA-01 蒼龍神劍",
                },
            },
        }
        rows = display_parts_for_product(catalog, catalog["products"]["BXA-01"])
        by_id = {row["part_id"]: row for row in rows}
        self.assertIn("BL-PRD-939672-00", by_id)
        self.assertEqual(by_id["BL-PRD-939672-00"]["slot"], "blade")
        self.assertEqual(by_id["BL-PRD-939672-00"]["name_zh"], "BXA-01 蒼龍神劍")
        self.assertIn("3-60", by_id)
        self.assertIn("F", by_id)

    def test_keeps_listed_blade_first_seen_on_another_set(self):
        catalog = {
            "products": {
                "CX-00-bxg51": {
                    "id": "CX-00-bxg51",
                    "part_ids": ["cx-main-Br", "6-60", "V"],
                },
                "CX-04": {"id": "CX-04", "part_ids": ["cx-main-Br"]},
            },
            "parts": {
                "cx-main-Br": {
                    "id": "cx-main-Br",
                    "slot": "blade",
                    "name_zh": "勇氣",
                    "first_seen_in": "CX-04",
                },
                "6-60": {
                    "id": "6-60",
                    "slot": "ratchet",
                    "name_zh": "固鎖",
                    "first_seen_in": "UX-03",
                    "release_ids": ["RC-UX-03"],
                },
                "V": {"id": "V", "slot": "bit", "name_zh": "軸心"},
            },
            "part_releases": {
                "RC-UX-03": {
                    "id": "RC-UX-03",
                    "part_id": "6-60",
                    "set_id": "UX-03",
                    "slot": "ratchet",
                },
            },
        }
        rows = display_parts_for_product(
            catalog, catalog["products"]["CX-00-bxg51"]
        )
        ids = [row["part_id"] for row in rows]
        self.assertIn("cx-main-Br", ids)

    def test_unnamed_hub_blade_kept_when_only_named_parts_are_ratchet(self):
        catalog = {
            "products": {
                "BXG-29": {
                    "id": "BXG-29",
                    "part_ids": ["Iron", "4-80", "B"],
                }
            },
            "parts": {
                "Iron": {
                    "id": "Iron",
                    "slot": "blade",
                    "name_zh": "",
                    "label": "上蓋 鋼鐵人",
                    "first_seen_in": "BXG-29",
                },
                "4-80": {"id": "4-80", "slot": "ratchet", "name_zh": "固鎖"},
                "B": {"id": "B", "slot": "bit", "name_zh": "軸心"},
            },
            "part_releases": {},
        }
        rows = display_parts_for_product(catalog, catalog["products"]["BXG-29"])
        ids = [row["part_id"] for row in rows]
        self.assertIn("Iron", ids)

    def test_limited_hub_page_gets_sibling_blade(self):
        catalog = {
            "products": {
                "BX-00-bxg47": {
                    "id": "BX-00-bxg47",
                    "part_ids": ["3-70", "RA"],
                },
                "BXG-47": {
                    "id": "BXG-47",
                    "part_ids": ["STORMPEGASIS", "3-70", "RA"],
                },
            },
            "parts": {
                "STORMPEGASIS": {
                    "id": "STORMPEGASIS",
                    "slot": "blade",
                    "name_zh": "暴風天馬",
                },
                "3-70": {"id": "3-70", "slot": "ratchet", "name_zh": "固鎖"},
                "RA": {"id": "RA", "slot": "bit", "name_zh": "軸心"},
            },
            "part_releases": {},
        }
        rows = display_parts_for_product(
            catalog, catalog["products"]["BX-00-bxg47"]
        )
        ids = [row["part_id"] for row in rows]
        self.assertIn("STORMPEGASIS", ids)

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
        self.assertTrue(
            is_display_part({"id": "GHOSTCIRCLE", "name_zh": "幽靈元魂"})
        )
        self.assertFalse(is_display_part({"id": "■"}))
        self.assertTrue(is_display_part({"id": "GN"}))
        urls = _product_image_urls(
            {
                "id": "BX-50-02",
                "name_zh": "BX-50-02 天國日輪 6-60TP",
                "image": "https://img.beybladehub.app/combos/BX5002.webp",
                "phstudy_ids": {"blade": "BL-PRD-084174-02"},
            }
        )
        self.assertEqual(
            urls[0],
            "https://beyblade.phstudy.org/images/site/Blade/BL-PRD-084174-02.png",
        )
        urls = _product_image_urls(
            {
                "id": "BX-20",
                "name_zh": "蒼龍利刃改造組",
                "image": "https://img.beybladehub.app/blades-db/DrDg.webp",
                "variant_ids": ["BX-20-02"],
            }
        )
        self.assertEqual(urls[0], "https://img.beybladehub.app/combos/BX20.webp")

    def test_phstudy_retail_product_key_strips_variant_suffix(self):
        self.assertEqual(phstudy_retail_product_key("CX-18"), "CX18")
        self.assertEqual(phstudy_retail_product_key("CX-18-01"), "CX18")
        self.assertEqual(phstudy_retail_product_key("BXG-12"), "BXG12")

    def test_merge_phstudy_products_multilang_sets_box_image(self):
        catalog = {
            "products": {
                "CX-18": {"id": "CX-18"},
                "CX-18-01": {"id": "CX-18-01", "base_set_id": "CX-18"},
            }
        }
        merge_phstudy_products_multilang(
            catalog,
            [
                {
                    "product_id": "CX18",
                    "images": ["images/products/CX-18/096177_00.jpg"],
                }
            ],
        )
        box = "https://beyblade.phstudy.org/images/products/CX-18/096177_00.jpg"
        self.assertEqual(catalog["products"]["CX-18"]["box_image"], box)
        self.assertEqual(catalog["products"]["CX-18-01"]["box_image"], box)

    def test_merge_skips_phstudy_internal_series_id(self):
        self.assertTrue(is_internal_phstudy_id("SR-PRD-995678-00R"))
        self.assertFalse(is_internal_phstudy_id("CX-09"))
        catalog = {
            "products": {
                "CX-09": {"id": "CX-09", "part_ids": [], "source": "hub"},
            },
            "parts": {},
            "variants": {},
            "relations": {"contains": [], "variant_of": [], "first_seen_in": []},
            "part_releases": {},
        }
        merge_phstudy_data(
            catalog,
            {
                "data": {
                    "BeybladeSeries": {
                        "SR-PRD-995678-00R": {
                            "id": "SR-PRD-995678-00R",
                            "en_name": "SOLECLIPSED",
                            "name": {"zh-TW": "CX-09 焰神滅世 D5-70TK"},
                            "tags": ["cx"],
                        }
                    }
                }
            },
        )
        self.assertNotIn("SR-PRD-995678-00R", catalog["products"])
        self.assertIn("CX-09", catalog["products"])

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
        self.assertEqual(
            phstudy_image_url("blade", "HB-G1677-MAINBLADE"),
            "https://beyblade.phstudy.org/images/site/MainBlade/HB-G1677-MAINBLADE.png",
        )
        self.assertEqual(
            phstudy_image_url("blade", "BL-PRD-084174-02"),
            "https://beyblade.phstudy.org/images/site/Blade/BL-PRD-084174-02.png",
        )


from catalog_pages import (
    browser_items,
    catalog_image_href,
    filter_catalog_products,
    handle_catalog_http,
    package_bey_entries,
    package_box_image_path,
    render_browser_html,
    render_catalog_html,
    render_catalog_product_html,
    render_part_detail_html,
)


class CatalogBrandFilterTests(unittest.TestCase):
    def setUp(self):
        self.products = {
            "CX-18": {"id": "CX-18", "line": "CX", "name_zh": "腕龍鞭打選集（CX-18）"},
            "F9324": {
                "id": "F9324",
                "line": "HASBRO",
                "source": "hasbro",
                "name_zh": "Soar Phoenix",
            },
        }

    def test_brand_filter_separates_tt_and_hasbro(self):
        all_ids = [r["id"] for r in filter_catalog_products(self.products)]
        self.assertEqual(all_ids, ["CX-18", "F9324"])
        hasbro_ids = [
            r["id"]
            for r in filter_catalog_products(self.products, brand="hasbro")
        ]
        self.assertEqual(hasbro_ids, ["F9324"])
        tt_ids = [r["id"] for r in filter_catalog_products(self.products, brand="tt")]
        self.assertEqual(tt_ids, ["CX-18"])

    def test_catalog_page_has_all_hasbro_tt_chips(self):
        page = render_catalog_html({"products": self.products}, brand="tt")
        self.assertIn(">全部</a>", page)
        self.assertIn(">孩之寶</a>", page)
        self.assertIn(">TT</a>", page)
        self.assertIn("brand=hasbro", page)
        self.assertIn("brand=tt", page)
        self.assertIn("腕龍鞭打選集（CX-18）", page)
        self.assertNotIn("Soar Phoenix", page)

    def test_catalog_http_reads_brand_query(self):
        result = handle_catalog_http(
            "/catalog",
            "brand=hasbro",
            catalog={"products": self.products},
        )
        self.assertEqual(result["status"], 200)
        self.assertIn("Soar Phoenix", result["html"])
        self.assertNotIn("腕龍鞭打選集（CX-18）", result["html"])

    def test_internal_phstudy_series_ids_are_hidden(self):
        products = {
            "CX-09": {"id": "CX-09", "line": "CX", "name_zh": "焰神滅世（CX-09）"},
            "SR-PRD-995678-00R": {
                "id": "SR-PRD-995678-00R",
                "name_zh": "CX-09 焰神滅世 D5-70TK",
                "source": "takara",
            },
        }
        ids = [r["id"] for r in filter_catalog_products(products)]
        self.assertEqual(ids, ["CX-09"])
        result = handle_catalog_http(
            "/catalog/SR-PRD-995678-00R",
            "",
            catalog={"products": products},
        )
        self.assertEqual(result["status"], 404)


class CatalogProductPageTests(unittest.TestCase):
    def test_package_box_prefers_phstudy_box_over_hub_combo(self):
        product = {
            "id": "CX-18",
            "name_zh": "腕龍鞭打選集（CX-18）",
            "image_path": "images/products/CX-18.jpg",
            "box_image_path": "images/boxes/CX-18.jpg",
            "box_image": "https://beyblade.phstudy.org/images/products/CX-18/096177_00.jpg",
            "variant_ids": ["CX-18-01", "CX-18-02"],
        }
        self.assertEqual(package_box_image_path(product), "images/boxes/CX-18.jpg")
        remote = dict(product)
        remote.pop("box_image_path")
        self.assertEqual(
            package_box_image_path(remote),
            "https://beyblade.phstudy.org/images/products/CX-18/096177_00.jpg",
        )
        self.assertEqual(
            catalog_image_href(remote["box_image"]),
            remote["box_image"],
        )

    def test_bey_prefers_phstudy_blade_over_hub_local_image(self):
        product = {
            "id": "BX-50-02",
            "name_zh": "BX-50-02 天國日輪 6-60TP",
            "image_path": "images/products/BX-50-02.jpg",
            "phstudy_ids": {"blade": "BL-PRD-084174-02"},
        }
        self.assertEqual(
            package_box_image_path(product),
            "https://beyblade.phstudy.org/images/site/Blade/BL-PRD-084174-02.png",
        )
        listing = render_catalog_html({"products": {product["id"]: product}})
        self.assertIn("BL-PRD-084174-02.png", listing)
        self.assertNotIn("images/products/BX-50-02.jpg", listing)

    def test_package_page_shows_box_and_all_beys(self):
        catalog = {
            "products": {
                "CX-18": {
                    "id": "CX-18",
                    "name_zh": "腕龍鞭打選集（CX-18）",
                    "image_path": "images/products/CX-18.jpg",
                    "box_image_path": "images/boxes/CX-18.jpg",
                    "variant_ids": ["CX-18-01", "CX-18-02", "CX-18-03"],
                    "part_ids": ["5-70"],
                }
            },
            "variants": {
                "CX-18-01": {
                    "id": "CX-18-01",
                    "name_zh": "腕龍鞭打 OW5-70Nr（標準色）",
                    "image_path": "images/variants/CX-18-01.jpg",
                },
                "CX-18-02": {
                    "id": "CX-18-02",
                    "name_zh": "腕龍鞭打 OW5-70Nr（黃金）",
                    "image_path": "images/variants/CX-18-02.jpg",
                },
                "CX-18-03": {
                    "id": "CX-18-03",
                    "name_zh": "腕龍鞭打 OW5-70Nr（黑色）",
                    "image_path": "images/variants/CX-18-03.jpg",
                },
            },
            "parts": {
                "5-70": {"id": "5-70", "slot": "ratchet", "first_seen_in": "CX-18"},
            },
            "part_releases": {},
        }
        beys = package_bey_entries(catalog, catalog["products"]["CX-18"])
        self.assertEqual(len(beys), 3)
        self.assertEqual(beys[2]["id"], "CX-18-03")
        page = render_catalog_product_html(catalog, "CX-18")
        self.assertIn("images/boxes/CX-18.jpg", page)
        self.assertNotIn("images/products/CX-18.jpg", page)
        self.assertIn("<h2>陀螺</h2>", page)
        self.assertIn("腕龍鞭打 OW5-70Nr（標準色）", page)
        self.assertIn("腕龍鞭打 OW5-70Nr（黃金）", page)
        self.assertIn("腕龍鞭打 OW5-70Nr（黑色）", page)
        self.assertEqual(page.count("陀螺 · "), 3)

    def test_set_beys_prefer_child_products_over_hub_image_slots(self):
        catalog = {
            "products": {
                "UX-12": {
                    "id": "UX-12",
                    "name_zh": "UX-12 隨機強化組 Vol.5",
                    "variant_ids": [
                        "UX-12-01",
                        "UX-12-02",
                        "UX-12-03",
                        "UX-12-04",
                        "UX-12-05",
                        "UX-12-06",
                        "UX-12-07",
                    ],
                },
                "UX-12-01": {
                    "id": "UX-12-01",
                    "base_set_id": "UX-12",
                    "name_zh": "UX-12-01 幽靈元魂 0-80GB",
                },
                "UX-12-06": {
                    "id": "UX-12-06",
                    "base_set_id": "UX-12",
                    "name_zh": "UX-12-06 飛龍旋翼 0-80C",
                },
            },
            "variants": {
                "UX-12-07": {
                    "id": "UX-12-07",
                    "name_zh": "UX-12 隨機強化組 Vol.5 飛龍旋翼 0-80C（variant 06 / BX）",
                },
            },
            "parts": {},
            "part_releases": {},
        }
        beys = package_bey_entries(catalog, catalog["products"]["UX-12"])
        ids = [row["id"] for row in beys]
        self.assertEqual(ids, ["UX-12-01", "UX-12-06"])
        self.assertNotIn("UX-12-07", ids)
        self.assertEqual(beys[1]["name"], "UX-12-06 飛龍旋翼 0-80C")
        page = render_catalog_product_html(catalog, "UX-12")
        self.assertNotIn("variant 06 / BX", page)
        self.assertNotIn("陀螺 · UX-12-07", page)

    def test_reprint_series_uses_phstudy_blade_when_no_local_image(self):
        product = {
            "id": "SR-PRD-084174-02R",
            "name_zh": "BX-50 天國日輪 6-60TP",
            "phstudy_ids": {"blade": "BL-PRD-084174-02R"},
        }
        self.assertEqual(
            package_box_image_path(product),
            "https://beyblade.phstudy.org/images/site/Blade/BL-PRD-084174-02R.png",
        )
        self.assertIsNone(
            render_catalog_product_html(
                {
                    "products": {product["id"]: product},
                    "variants": {},
                    "parts": {},
                    "part_releases": {},
                },
                product["id"],
            )
        )
        listing = render_catalog_html({"products": {product["id"]: product}})
        self.assertNotIn("/catalog/SR-PRD-084174-02R", listing)

    def test_hasbro_cx_page_uses_mainblade_folder(self):
        catalog = {
            "products": {
                "G1677": {
                    "id": "G1677",
                    "name_zh": "G1677 蒼龍勇氣 S6-60V",
                    "part_ids": ["BRAVE"],
                    "phstudy_ids": {"blade": "HB-G1677-MAINBLADE"},
                    "source": "hasbro",
                }
            },
            "parts": {
                "BRAVE": {
                    "id": "BRAVE",
                    "slot": "blade",
                    "name_zh": "勇氣",
                    "release_ids": ["HB-G1677-MAINBLADE"],
                }
            },
            "part_releases": {
                "HB-G1677-MAINBLADE": {
                    "id": "HB-G1677-MAINBLADE",
                    "part_id": "BRAVE",
                    "slot": "blade",
                    "set_id": "G1677",
                }
            },
            "variants": {},
        }
        page = render_catalog_product_html(catalog, "G1677")
        self.assertIn(
            "https://beyblade.phstudy.org/images/site/MainBlade/HB-G1677-MAINBLADE.png",
            page,
        )
        self.assertNotIn(
            "https://beyblade.phstudy.org/images/site/Blade/HB-G1677-MAINBLADE.png",
            page,
        )

    def test_hasbro_dual_pack_uses_child_image_and_sorts_parts(self):
        catalog = {
            "products": {
                "G2763": {
                    "id": "G2763",
                    "name_zh": "Brace Triceratops and Dagger Dran Dual Pack",
                    "name_en": "Brace Triceratops and Dagger Dran Dual Pack",
                    "source": "hasbro",
                    "kind": "beyblade",
                    "part_ids": [],
                    "variant_ids": [],
                },
                "G2763-01": {
                    "id": "G2763-01",
                    "base_set_id": "G2763",
                    "name_zh": "G2763-01 三角強襲M-85BS",
                    "image_path": "images/products/G2763-01.jpg",
                    "part_ids": ["TRICERAPRESS", "M-85", "BS"],
                },
                "G2763-02": {
                    "id": "G2763-02",
                    "base_set_id": "G2763",
                    "name_zh": "G2763-02 蒼龍利刃 7-55K",
                    "image_path": "images/products/G2763-02.jpg",
                    "part_ids": ["DRANDAGGER", "7-55", "K"],
                },
            },
            "parts": {
                "TRICERAPRESS": {
                    "id": "TRICERAPRESS",
                    "slot": "blade",
                    "name_zh": "三角強襲",
                },
                "M-85": {"id": "M-85", "slot": "ratchet", "name_zh": "M-85"},
                "BS": {"id": "BS", "slot": "bit", "name_zh": "BS"},
                "DRANDAGGER": {
                    "id": "DRANDAGGER",
                    "slot": "blade",
                    "name_zh": "蒼龍利刃",
                },
                "7-55": {"id": "7-55", "slot": "ratchet", "name_zh": "7-55"},
                "K": {"id": "K", "slot": "bit", "name_zh": "K"},
            },
            "part_releases": {
                "HB-01-B": {
                    "id": "HB-01-B",
                    "part_id": "TRICERAPRESS",
                    "slot": "blade",
                    "set_id": "G2763-01",
                    "image_path": "images/releases/01b.jpg",
                },
                "HB-01-R": {
                    "id": "HB-01-R",
                    "part_id": "M-85",
                    "slot": "ratchet",
                    "set_id": "G2763-01",
                    "image_path": "images/releases/01r.jpg",
                },
                "HB-01-T": {
                    "id": "HB-01-T",
                    "part_id": "BS",
                    "slot": "bit",
                    "set_id": "G2763-01",
                    "image_path": "images/releases/01t.jpg",
                },
                "HB-02-B": {
                    "id": "HB-02-B",
                    "part_id": "DRANDAGGER",
                    "slot": "blade",
                    "set_id": "G2763-02",
                    "image_path": "images/releases/02b.jpg",
                },
                "HB-02-R": {
                    "id": "HB-02-R",
                    "part_id": "7-55",
                    "slot": "ratchet",
                    "set_id": "G2763-02",
                    "image_path": "images/releases/02r.jpg",
                },
                "HB-02-T": {
                    "id": "HB-02-T",
                    "part_id": "K",
                    "slot": "bit",
                    "set_id": "G2763-02",
                    "image_path": "images/releases/02t.jpg",
                },
            },
            "variants": {},
        }
        self.assertTrue(is_set_product(catalog["products"]["G2763"]))
        self.assertEqual(
            package_box_image_path(catalog["products"]["G2763"], catalog),
            "images/products/G2763-01.jpg",
        )
        rows = display_parts_for_product(catalog, catalog["products"]["G2763"])
        self.assertEqual(
            [(row.get("set_id"), row.get("part_id")) for row in rows],
            [
                ("G2763-01", "TRICERAPRESS"),
                ("G2763-01", "M-85"),
                ("G2763-01", "BS"),
                ("G2763-02", "DRANDAGGER"),
                ("G2763-02", "7-55"),
                ("G2763-02", "K"),
            ],
        )
        page = render_catalog_product_html(catalog, "G2763")
        self.assertIn("G2763-01.jpg", page)
        self.assertIn("<h2>陀螺</h2>", page)

    def test_part_colorways_keep_same_slot_only(self):
        catalog = {
            "products": {},
            "parts": {
                "K": {
                    "id": "K",
                    "slot": "bit",
                    "name_zh": "軸心 K",
                    "release_ids": [
                        "BT-K-1",
                        "AB-K-ASSIST",
                    ],
                }
            },
            "part_releases": {
                "BT-K-1": {
                    "id": "BT-K-1",
                    "part_id": "K",
                    "slot": "bit",
                    "set_id": "CX-05-01",
                    "name_zh": "CX-05-01 K",
                },
                "AB-K-ASSIST": {
                    "id": "AB-K-ASSIST",
                    "part_id": "K",
                    "slot": "assist_blade",
                    "set_id": "CX-13",
                    "name_zh": "CX-13 K assist",
                },
            },
        }
        page = render_part_detail_html(catalog, "K")
        self.assertIn("CX-05-01 K", page)
        self.assertNotIn("CX-13 K assist", page)
        self.assertNotIn("data-add-release=\"AB-K-ASSIST\"", page)

    def test_part_used_in_keeps_same_slot_only(self):
        catalog = {
            "products": {
                "CX-05-01": {
                    "id": "CX-05-01",
                    "name_zh": "K bit set",
                    "part_ids": ["K"],
                },
                "CX-13": {
                    "id": "CX-13",
                    "name_zh": "K assist set",
                    "part_ids": ["K"],
                },
            },
            "parts": {
                "K": {
                    "id": "K",
                    "slot": "bit",
                    "name_zh": "軸心 K",
                    "used_in": ["CX-05-01", "CX-13"],
                    "first_seen_in": "CX-13",
                    "release_ids": ["BT-K-1", "AB-K-ASSIST"],
                }
            },
            "part_releases": {
                "BT-K-1": {
                    "id": "BT-K-1",
                    "part_id": "K",
                    "slot": "bit",
                    "set_id": "CX-05-01",
                    "name_zh": "CX-05-01 K",
                },
                "AB-K-ASSIST": {
                    "id": "AB-K-ASSIST",
                    "part_id": "K",
                    "slot": "assist_blade",
                    "set_id": "CX-13",
                    "name_zh": "CX-13 K assist",
                },
            },
        }
        page = render_part_detail_html(catalog, "K")
        self.assertIn("K bit set", page)
        self.assertNotIn("K assist set", page)


class CatalogBrowserTests(unittest.TestCase):
    def sample(self):
        return {
            "products": {
                "CX-18": {
                    "id": "CX-18",
                    "line": "CX",
                    "name_zh": "腕龍鞭打選集（CX-18）",
                    "released_on": "2025-06-01",
                    "price_jpy": 1600,
                },
                "F9324": {
                    "id": "F9324",
                    "line": "HASBRO",
                    "source": "hasbro",
                    "name_zh": "Soar Phoenix",
                    "tags": ["hasbro"],
                },
                "BX-01": {
                    "id": "BX-01",
                    "line": "BX",
                    "name_zh": "鑽擊獅王",
                    "tags": ["reprint"],
                },
                "SR-PRD-995678-00R": {
                    "id": "SR-PRD-995678-00R",
                    "name_zh": "hidden",
                },
            },
            "parts": {
                "GN": {
                    "id": "GN",
                    "slot": "bit",
                    "name_zh": "軸心 GN",
                    "used_in": ["CX-18"],
                },
            },
        }

    def test_browser_items_include_products_and_parts(self):
        items = browser_items(self.sample())
        by_id = {row["id"]: row for row in items}
        self.assertEqual(by_id["CX-18"]["href"], "/catalog/CX-18")
        self.assertEqual(by_id["CX-18"]["kind"], "product")
        self.assertEqual(by_id["GN"]["href"], "/parts/GN")
        self.assertEqual(by_id["GN"]["slot"], "bit")
        self.assertIn("CX", by_id["GN"]["lines"])
        self.assertNotIn("SR-PRD-995678-00R", by_id)

    def test_browser_page_embeds_items_and_controls(self):
        page = render_browser_html(self.sample())
        self.assertIn('id="browser-app"', page)
        self.assertIn("腕龍鞭打選集（CX-18）", page)
        self.assertIn(">圖示</button>", page)
        self.assertIn(">表格</button>", page)
        self.assertIn(">系列</button>", page)
        self.assertIn(">軸心</button>", page)
        self.assertIn("href=\"/catalog\"", page)

    def test_browser_http_accepts_slash_alias(self):
        catalog = self.sample()
        slash = handle_catalog_http("/browser/", "", catalog=catalog)
        bare = handle_catalog_http("/browser", "", catalog=catalog)
        self.assertEqual(slash["status"], 200)
        self.assertEqual(bare["status"], 200)
        self.assertIn('id="browser-app"', slash["html"])


if __name__ == "__main__":
    unittest.main()
