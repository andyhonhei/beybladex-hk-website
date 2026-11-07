#!/usr/bin/env python3
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from catalog_pages import (
    add_package_to_collection,
    add_part_to_collection,
    catalog_image_href,
    empty_collection,
    filter_catalog_products,
    handle_catalog_http,
    needs_variant_pick,
    parts_for_variant,
    render_catalog_html,
    render_catalog_product_html,
    render_collection_html,
    render_part_detail_html,
    render_parts_html,
    CATALOG_DETAIL_CACHE_CONTROL,
    render_catalog_shops_html,
)


MINI = {
    "products": {
        "CX-18": {
            "id": "CX-18",
            "name_zh": "腕龍鞭打選集",
            "line": "CX",
            "part_ids": ["cx-over-O", "cx-assist-W", "5-70", "Nr"],
            "variant_ids": ["CX-18-01", "CX-18-02"],
            "image_path": "images/products/CX-18.jpg",
            "description": "三色性能相同，每盒隨機一款。",
            "released_on": "2026-06-13",
            "price_jpy": 1600,
            "source_url": "https://beybladehub.app/parts/combos/CX-18",
            "jan": "4904810096177",
            "tags": [],
        },
        "BX-48": {
            "id": "BX-48",
            "name_zh": "隨機強化組 Vol.9",
            "line": "BX",
            "part_ids": ["CbDg", "9-80", "F", "HlSc"],
            "variant_ids": ["BX-48-01", "BX-48-04"],
            "tags": [],
        },
    },
    "variants": {
        "CX-18-01": {
            "id": "CX-18-01",
            "product_id": "CX-18",
            "name_zh": "腕龍鞭打 OW5-70Nr（標準色）",
        },
        "CX-18-02": {
            "id": "CX-18-02",
            "product_id": "CX-18",
            "name_zh": "腕龍鞭打 OW5-70Nr（黃金）",
        },
        "BX-48-01": {
            "id": "BX-48-01",
            "product_id": "BX-48",
            "name_zh": "蒼穹龍騎士 9-80F",
        },
        "BX-48-04": {
            "id": "BX-48-04",
            "product_id": "BX-48",
            "name_zh": "惡魔紅鐮 3-85GB",
        },
    },
    "parts": {
        "GN": {
            "id": "GN",
            "slot": "bit",
            "name_en": "Gear Needle",
            "used_in": ["CX-18", "CX-19"],
            "first_seen_in": "CX-18",
            "href": "/parts/bits#bit-GN",
            "image_path": "images/parts/GN.jpg",
        },
        "cx-over-O": {"id": "cx-over-O", "slot": "over_blade"},
    },
    "shop_listings": [
        {
            "shop_id": "buymarkettoy",
            "sku": "BY096177",
            "title": "Takara Tomy CX-18",
            "price": "119.00",
            "url": "https://www.buymarkettoy.com/products/x",
            "status": "in_stock",
            "status_label": "有貨",
            "product_ids": ["CX-18"],
        },
        {
            "shop_id": "hobbyland",
            "sku": "HL-CX18",
            "title": "CX-18 腕龍鞭打",
            "price": "128.00",
            "url": "https://www.hobbyland.com.hk/x",
            "status": "out_of_stock",
            "status_label": "缺貨",
            "product_ids": ["CX-18"],
        },
    ],
}


class CatalogPagesTests(unittest.TestCase):
    def test_add_cx18_package_adds_all_parts(self):
        owned = add_package_to_collection(empty_collection(), "CX-18", MINI)
        self.assertIn("CX-18", owned["products"])
        self.assertEqual(
            sorted(owned["parts"]),
            ["5-70", "Nr", "cx-assist-W", "cx-over-O"],
        )

    def test_add_single_part_without_package(self):
        owned = add_part_to_collection(empty_collection(), "GN")
        self.assertEqual(owned["parts"], ["GN"])
        self.assertEqual(owned["products"], [])

    def test_random_booster_needs_variant_cx18_does_not(self):
        self.assertFalse(needs_variant_pick(MINI["products"]["CX-18"], MINI["variants"]))
        self.assertTrue(needs_variant_pick(MINI["products"]["BX-48"], MINI["variants"]))
        self.assertEqual(
            parts_for_variant(MINI["variants"]["BX-48-01"], MINI),
            ["9-80", "F"],
        )

    def test_filter_line_and_image_href(self):
        rows = filter_catalog_products(MINI["products"], line="CX")
        self.assertEqual([row["id"] for row in rows], ["CX-18"])
        self.assertEqual(
            catalog_image_href("images/products/CX-18.jpg"),
            "https://beybladex-cdn.andyhhh.com/parts-images/products/CX-18.jpg?v=w2",
        )

    def test_pages_have_add_actions_and_local_storage_script(self):
        catalog_page = render_catalog_html(MINI, line="CX")
        self.assertIn("腕龍鞭打選集", catalog_page)
        self.assertIn("/catalog/CX-18", catalog_page)
        self.assertIn("catalog-grid", catalog_page)
        self.assertIn("catalog-tile", catalog_page)
        self.assertIn("filter-store", catalog_page)
        self.assertIn("filter-combo-input", catalog_page)
        self.assertIn("repeat(3,minmax(0,1fr))", catalog_page)
        self.assertIn("beyblade-collection-v1", catalog_page)
        product_page = render_catalog_product_html(MINI, "CX-18")
        self.assertIn('data-add-product="CX-18"', product_page)
        self.assertIn("cx-over-O", product_page)
        self.assertIn("2026-06-13", product_page)
        self.assertIn("¥1,600", product_page)
        self.assertIn("三色性能相同", product_page)
        self.assertIn("beybladehub.app/parts/combos/CX-18", product_page)
        self.assertIn("data-src='/catalog/CX-18/shops'", product_page)
        self.assertIn("貨況最多延遲約 30 分鐘", product_page)
        self.assertIn("請訂閱通知", product_page)
        self.assertIn("catalog-subscribe", product_page)
        self.assertNotIn("HK$119.00", product_page)
        shops = render_catalog_shops_html(MINI, "CX-18")
        self.assertIn("HK$119.00", shops)
        self.assertIn("buymarkettoy.com", shops)
        self.assertIn("stock-in", shops)
        self.assertIn("有貨", shops)
        self.assertIn("stock-out", shops)
        self.assertIn("缺貨", shops)
        part_page = render_part_detail_html(MINI, "GN")
        self.assertIn("/catalog/CX-18", part_page)
        self.assertIn("用於這些商品", part_page)
        self.assertIn("首次出現", part_page)
        self.assertIn("Gear Needle", part_page)
        self.assertIn("beybladehub.app/parts/bits", part_page)
        booster = render_catalog_product_html(MINI, "BX-48")
        self.assertIn("data-add-variant", booster)
        self.assertNotIn('data-add-product="BX-48"', booster)
        self.assertIn("thumb-empty", booster)
        self.assertNotIn("thumb-preview", booster)
        parts_page = render_parts_html(MINI)
        self.assertIn("/parts/GN", parts_page)
        self.assertIn("catalog-tile", parts_page)
        collection = render_collection_html()
        self.assertIn("我的庫", collection)
        self.assertIn("beyblade-collection-v1", collection)

    def test_hides_child_products_and_junk_parts(self):
        catalog = {
            "products": dict(MINI["products"]),
            "variants": MINI["variants"],
            "parts": dict(MINI["parts"]),
        }
        catalog["products"]["CX-05"] = {
            "id": "CX-05",
            "name_zh": "隨機強化組 Vol.6",
            "line": "CX",
            "variant_ids": ["CX-05-01", "CX-05-02"],
            "part_ids": ["GN", "DRANSTRIKE", "■"],
        }
        catalog["products"]["CX-05-01"] = {
            "id": "CX-05-01",
            "name_zh": "惡魔獵魂",
            "line": "CX",
            "base_set_id": "CX-05",
            "part_ids": ["REAPER"],
        }
        catalog["parts"]["DRANSTRIKE"] = {"id": "DRANSTRIKE", "slot": "blade"}
        catalog["parts"]["■"] = {"id": "■", "slot": "bit"}
        ids = [row["id"] for row in filter_catalog_products(catalog["products"], line="CX")]
        self.assertIn("CX-18", ids)
        self.assertIn("CX-05", ids)
        self.assertNotIn("CX-05-01", ids)
        parts_page = render_parts_html(catalog)
        self.assertIn("/parts/GN", parts_page)
        self.assertNotIn("DRANSTRIKE", parts_page)
        self.assertNotIn(">■", parts_page)
        product = render_catalog_product_html(catalog, "CX-05")
        self.assertIn("Gear Needle", product)
        self.assertNotIn("DRANSTRIKE", product)
        catalog["products"]["CX-01"] = {
            "id": "CX-01",
            "name_zh": "蒼龍勇氣",
            "line": "CX",
            "part_ids": ["GN"],
        }
        set_ids = [row["id"] for row in filter_catalog_products(catalog["products"], kind="set")]
        bey_ids = [row["id"] for row in filter_catalog_products(catalog["products"], kind="bey")]
        self.assertIn("CX-05", set_ids)
        self.assertIn("CX-18", set_ids)
        self.assertIn("CX-01", bey_ids)
        self.assertNotIn("CX-05", bey_ids)
        catalog_page = render_catalog_html(catalog)
        self.assertIn("套裝", catalog_page)
        self.assertIn("整顆陀螺", catalog_page)
        self.assertIn("上蓋", catalog_page)
        self.assertIn("/catalog?kind=set", catalog_page)
        bits = render_catalog_html(catalog, kind="bit")
        self.assertIn("/parts/GN", bits)
        self.assertNotIn("/catalog/CX-18", bits)

    def test_http_router_uses_local_catalog(self):
        hit = handle_catalog_http("/catalog", "line=CX", catalog=MINI)
        self.assertEqual(hit["status"], 200)
        self.assertIn("腕龍鞭打選集", hit["html"])
        beys = handle_catalog_http("/catalog", "kind=bey", catalog=MINI)
        self.assertEqual(beys["status"], 200)
        self.assertNotIn("/catalog/CX-18", beys["html"])
        self.assertNotIn("/catalog/BX-48", beys["html"])
        bits = handle_catalog_http("/catalog", "kind=bit", catalog=MINI)
        self.assertEqual(bits["status"], 200)
        self.assertIn("/parts/GN", bits["html"])
        self.assertIn("軸心", bits["html"])
        product = handle_catalog_http("/catalog/CX-18", "", catalog=MINI)
        self.assertEqual(product["status"], 200)
        self.assertEqual(product["cache"], CATALOG_DETAIL_CACHE_CONTROL)
        self.assertIn("31536000", product["cache"])
        shops = handle_catalog_http("/catalog/CX-18/shops", "", catalog=MINI)
        self.assertEqual(shops["status"], 200)
        self.assertIn("max-age=1800", shops["cache"])
        self.assertIn("HK$119.00", shops["html"])
        miss = handle_catalog_http("/catalog/NOPE", "", catalog=MINI)
        self.assertEqual(miss["status"], 404)
        self.assertIsNone(handle_catalog_http("/not-catalog", "", catalog=MINI))


if __name__ == "__main__":
    unittest.main()
