# LidSwitch 合盖睡眠助手

Tauri v2 菜单栏小工具：开关切换 `pmset -a disablesleep 1/0`，控制 macOS 合盖是否休眠。首次切换需要输入开机密码授权（sudo），本次运行内免密。

## 开发调试

```bash
npm run dev
```

启动开发模式，带热重载，改动前端或 Rust 代码后自动刷新。

## 构建打包

```bash
npm run build
```

产出：

- App：`src-tauri/target/release/bundle/macos/LidSwitch.app`
- DMG 打包被禁用（`tauri.conf.json` 中 `targets` 已设为 `["app"]`），需要 DMG 时手工打：

```bash
hdiutil create -volname LidSwitch \
  -srcfolder src-tauri/target/release/bundle/macos/LidSwitch.app \
  -ov -format UDZO \
  src-tauri/target/release/bundle/dmg/LidSwitch_0.1.0_aarch64.dmg
```

## 一键构建 + 安装

```bash
./scripts/install.sh
```

依次执行：release 构建 → 停掉运行中的实例 → 安装到 `/Applications/LidSwitch.app` → 更新 DMG → 启动应用。
