#!/usr/bin/env bash
set -euo pipefail

WEB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_DIR="$(cd "$WEB_DIR/../server" && pwd)"
TAURI_DIR="$WEB_DIR/src-tauri"
TARGET_TRIPLE="$(rustc --print host-tuple)"
BINARY_DIR="$TAURI_DIR/binaries"
PYINSTALLER_DIR="$TAURI_DIR/target/pyinstaller"

uv sync --dev --project "$SERVER_DIR"
mkdir -p "$BINARY_DIR" "$PYINSTALLER_DIR"

"$SERVER_DIR/.venv/bin/python" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name studio-backend \
  --paths "$SERVER_DIR" \
  --distpath "$BINARY_DIR/.dist" \
  --workpath "$PYINSTALLER_DIR/work" \
  --specpath "$PYINSTALLER_DIR" \
  "$TAURI_DIR/backend_entry.py"

mv "$BINARY_DIR/.dist/studio-backend" "$BINARY_DIR/studio-backend-$TARGET_TRIPLE"
chmod 755 "$BINARY_DIR/studio-backend-$TARGET_TRIPLE"
rm -rf "$BINARY_DIR/.dist"
