from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "assets/app.js"


class PriceLabelRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = APP.read_text(encoding="utf-8")
        match = re.search(
            r"  function compactPriceLabel\(value = ''\) \{[\s\S]*?\n  \}\n\n  function ",
            text,
        )
        if not match:
            raise AssertionError("compactPriceLabel function not found")
        cls.function_source = match.group(0).rsplit("\n\n  function ", 1)[0].strip()

    def run_cases(self, values: list[str]) -> list[str]:
        script = (
            self.function_source
            + "\nconst values = "
            + json.dumps(values, ensure_ascii=False)
            + ";\nconsole.log(JSON.stringify(values.map(value => compactPriceLabel(value))));\n"
        )
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_paid_price_details_use_one_tidy_card_label(self) -> None:
        source = (
            "活動時間：每日 10:00 – 18:00（17:30 停止售票及入場） / "
            "現場票價： / 全票：470 元（一般身分者適用） / "
            "優待票：450 元（年滿 3 歲以上兒童）"
        )
        self.assertEqual(self.run_cases([source]), ["票價請見活動頁面"])

    def test_named_prices_without_yuan_use_the_same_label(self) -> None:
        source = "早鳥票：1,200 / 現場票：1,500 / 18歲以上"
        self.assertEqual(self.run_cases([source]), ["票價請見活動頁面"])

    def test_plain_schedule_does_not_render_as_currency_range(self) -> None:
        source = "活動時間：每日 10:00 – 18:00（17:30 停止入場）"
        self.assertEqual(self.run_cases([source]), ["票價請見活動頁面"])

    def test_free_admission_is_unchanged(self) -> None:
        self.assertEqual(self.run_cases(["每日 10:00–18:00，免費入場"]), ["免費入場"])


if __name__ == "__main__":
    unittest.main()
