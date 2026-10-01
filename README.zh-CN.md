# Lid

<p align="center">
  <img src="app-icon.png" width="96" alt="Lid icon">
</p>

[English](README.md) | 简体中文

<p align="center">
  <img src="docs/screenshot.png" width="420" alt="Lid 应用截图">
</p>

在 AI Agent 时代，Mac 有大量时间在无人值守地干活——编译、模型训练、爬虫、长时间运行的 Agent 任务。而一旦合上盖子，macOS 就会把这一切送进睡眠。

**Lid 是一个小小的 macOS 应用，只解决一个问题：合盖之后，Mac 继续干活不休眠。**

一个开关，别无其他。底层就是切换 `pmset -a disablesleep 1/0`。

## 特性

- **一个开关**——合盖睡眠开/关，即时生效
- **安全**——首次切换需要输入管理员密码（sudo）；密码仅缓存在本次运行的内存中，不落盘、不写日志
- **双语界面**——中/英文，自动跟随系统语言
- **支持浅色与深色模式**

## 工作原理

| 开关 | 命令 |
| ---- | ---- |
| 开 | `sudo pmset -a disablesleep 1` |
| 关 | `sudo pmset -a disablesleep 0` |

## 构建与安装

需要 Node.js 和 Rust 环境。

```bash
npm install        # 仅首次需要
npm run build      # 构建 Lid.app
```

产物位于 `src-tauri/target/release/bundle/macos/Lid.app`。也可以一键构建并安装到 `/Applications`：

```bash
./scripts/install.sh
```

## 许可证

MIT
