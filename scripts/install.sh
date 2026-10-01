#!/bin/bash
# 一键构建并安装 LidSwitch 到 /Applications
# 用法: ./scripts/install.sh
set -e
cd "$(dirname "$0")/.."

echo "==> 构建 release 版本…"
npx tauri build --bundles app

APP="src-tauri/target/release/bundle/macos/LidSwitch.app"
DEST="/Applications/LidSwitch.app"
DMG="src-tauri/target/release/bundle/dmg/LidSwitch_0.1.0_aarch64.dmg"

echo "==> 停止正在运行的实例…"
pkill -x LidSwitch 2>/dev/null || true
sleep 1

echo "==> 安装到 $DEST…"
rm -rf "$DEST"
cp -R "$APP" "$DEST"

echo "==> 更新 DMG 安装包…"
hdiutil create -volname LidSwitch -srcfolder "$APP" -ov -format UDZO "$DMG" >/dev/null
echo "    $DMG"

echo "==> 完成！启动方式：Spotlight 搜 LidSwitch，或 open -a LidSwitch"
open "$DEST"
