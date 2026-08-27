#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

finish() {
  status=$?
  echo
  if [ "$status" -eq 0 ]; then
    echo "更新完成。請依照畫面中的摘要，在 GitHub Desktop 一次提交資料。"
  else
    echo "更新沒有完成，正式資料已保留或還原。請將視窗中的錯誤內容提供給我。"
  fi
  echo "按 Enter 關閉視窗。"
  read -r
  exit "$status"
}
trap finish EXIT

if ! command -v python3 >/dev/null 2>&1; then
  echo "找不到 Python 3。請先安裝 Python 3，再重新雙擊此檔案。"
  exit 1
fi

VENV_DIR="$PROJECT_DIR/.venv-weekly-update"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "第一次執行：建立台灣展覽誌專用執行環境……"
  python3 -m venv "$VENV_DIR"
fi

REQUIREMENTS_HASH="$VENV_DIR/.requirements-sha256"
CURRENT_HASH="$($VENV_DIR/bin/python - <<'PY'
from hashlib import sha256
from pathlib import Path
p = Path('requirements.txt')
print(sha256(p.read_bytes()).hexdigest())
PY
)"

if [ ! -f "$REQUIREMENTS_HASH" ] || [ "$(cat "$REQUIREMENTS_HASH")" != "$CURRENT_HASH" ]; then
  echo "安裝或更新爬蟲所需元件……"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install -r requirements.txt
  printf '%s\n' "$CURRENT_HASH" > "$REQUIREMENTS_HASH"
fi

echo "開始執行每週展覽資料更新。過程可能需要一段時間，請勿關閉視窗或讓 Mac 進入睡眠。"
"$VENV_DIR/bin/python" scripts/run_local_weekly_update.py
