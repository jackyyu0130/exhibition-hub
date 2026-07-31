#!/usr/bin/env python3
from pathlib import Path

root = Path.cwd()
tests = root / "tests"

if not tests.is_dir() or not (root / "index.html").is_file():
    raise SystemExit("錯誤：請先在 exhibition-hub 專案根目錄執行此檔案。")

for path in tests.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    updated = text.replace("6.5.0-r10.4", "6.5.0-r10.5")
    if updated != text:
        path.write_text(updated, encoding="utf-8")

path = tests / "test_v650_postcard_carousel.py"
text = path.read_text(encoding="utf-8")
old = '''        self.assertNotIn("heroTicketSlideMarkup(pool[incomingIndex], 4", APP)
        self.assertIn("stack.animate(", APP)
        self.assertIn("renderHeroTickets();", APP)'''
new = '''        self.assertIn("heroTicketSlideMarkup(", APP)
        self.assertIn("incomingSlot", APP)
        self.assertIn("moveSlot(first, 1, 0)", APP)
        self.assertIn("moveSlot(second, 2, 1)", APP)
        self.assertIn("moveSlot(third, 3, 2)", APP)
        self.assertIn("moveSlot(incoming, 4, 3)", APP)
        function = APP.split("function changeHeroPair(direction)", 1)[1].split("const HOME_STATUS_COPY", 1)[0]
        self.assertNotIn("stack.animate(", function)'''
if old not in text:
    raise SystemExit("找不到舊版 postcard carousel 測試內容，請確認目前在 develop 分支最新版本。")
path.write_text(text.replace(old, new), encoding="utf-8")

path = tests / "test_v650_r103_taxonomy_venue_performance.py"
text = path.read_text(encoding="utf-8")
old = '''        marker = 'Exhibition Hub V6.5.0-R10.4'
        self.assertIn(marker, CSS)
        block = CSS.split(marker, 1)[1]
        self.assertIn('transition: none !important', block)
        self.assertIn('will-change: auto !important', block)
        self.assertIn('stack.animate', APP)'''
new = '''        marker = 'Exhibition Hub V6.5.0-R10.5'
        self.assertIn(marker, CSS)
        block = CSS.split(marker, 1)[1]
        self.assertIn('transition: none !important', block)
        self.assertIn('will-change: auto !important', block)
        self.assertIn('is-r105-moving', APP)
        self.assertIn('moveSlot(first, 1, 0)', APP)
        function = APP.split("function changeHeroPair(direction)", 1)[1].split("const HOME_STATUS_COPY", 1)[0]
        self.assertNotIn('stack.animate', function)'''
if old not in text:
    raise SystemExit("找不到舊版 R10.3 Hero 測試內容。")
path.write_text(text.replace(old, new), encoding="utf-8")

path = tests / "test_v650_r104_curated_feed_and_deploy.py"
text = path.read_text(encoding="utf-8")
old = '''        self.assertIn("typeof stack.animate !== 'function'", APP)
        self.assertIn("{duration:220", APP)
        self.assertIn("{duration:480", APP)'''
new = '''        self.assertIn("requestAnimationFrame", APP)
        self.assertIn("is-r105-moving", APP)
        self.assertIn("moveSlot(first, 1, 0)", APP)
        self.assertNotIn("cache:'no-store'", APP)
        self.assertIn("cache:'no-cache'", APP)'''
if old not in text:
    raise SystemExit("找不到舊版 R10.4 效能測試內容。")
path.write_text(text.replace(old, new), encoding="utf-8")

print("舊測試已同步到 V6.5.0-R10.5。")
print("接著執行：python3 -m unittest discover -s tests -v")
