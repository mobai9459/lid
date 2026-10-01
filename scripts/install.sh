#!/bin/bash
# 一键构建并安装 Lid 到 /Applications
# 用法: ./scripts/install.sh
set -e
cd "$(dirname "$0")/.."

echo "==> 构建 release 版本…"
npx tauri build --bundles app

APP="src-tauri/target/release/bundle/macos/Lid.app"
DEST="/Applications/Lid.app"
DMG="src-tauri/target/release/bundle/dmg/Lid_0.1.0_aarch64.dmg"

echo "==> 停止正在运行的实例…"
pkill -x Lid 2>/dev/null || true
sleep 1

echo "==> 安装到 $DEST…"
rm -rf "$DEST"
cp -R "$APP" "$DEST"

echo "==> 更新 DMG 安装包…"
hdiutil create -volname Lid -srcfolder "$APP" -ov -format UDZO "$DMG" >/dev/null
echo "    $DMG"

echo "==> 完成！启动方式：Spotlight 搜 Lid，或 open -a Lid"
open "$DEST"
