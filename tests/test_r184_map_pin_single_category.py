import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class R184MapPinAndSingleCategoryTests(unittest.TestCase):
    def test_map_accepts_an_arbitrary_click_as_a_three_kilometre_origin(self) -> None:
        self.assertIn("state.map.on('click', event =>", APP)
        self.assertIn("source:'map'", APP)
        self.assertIn("搜尋該位置 ${NEARBY_RADIUS_KM} 公里內展場", APP)
        self.assertIn("點擊地圖任意位置插入圖釘", HTML)

    def test_category_url_and_state_keep_only_one_selection(self) -> None:
        self.assertIn("state.categories = new Set(categoryValues.slice(0, 1));", APP)
        self.assertIn("if (values[0]) params.set('category', values[0]);", APP)
        self.assertIn("updateUrl({category:state.categories.has(category) ? null : category});", APP)


if __name__ == "__main__":
    unittest.main()
