# daily_planner

## 简介

`main.py` 是一个面向 macOS 用户的简易桌面日程提醒工具，基于 Tkinter 构建图形界面，并通过 `terminal-notifier` 实现系统通知弹窗。

## 功能特色

- 💡 **轻量本地运行**：不依赖 Homebrew 或 pync，仅需配置 terminal-notifier 路径。
- ⏰ **普通任务提醒**：提前 60/30/15/5/2 分钟发出提醒。
- 🔴 **特殊项目机制**：可创建“特殊项目”，每小时循环提醒，确保重要任务不会遗忘。
- 📆 **启动汇总通知**：启动程序时自动展示未来 24 小时内的最近任务及今日特殊任务。
- ⌨️ **快捷操作支持**：支持 `Command-N` 添加任务，`Command-D` 删除，`Command-A` 显示/隐藏全部任务。
- 🧾 **本地存储**：任务数据保存在 `~/.daily_planner.json` 中，重启后自动恢复。

## 使用说明

- **运行方式**
  在终端中执行以下命令启动程序：
  ```bash
  python main.py
  ```
  若出现缺少依赖库的错误，请使用 `pip install` 安装提示的模块。

- **基本操作**
  - 启动默认显示未来 24 小时内的最近一项任务和今日特殊任务。
  - 任务结束后仍保留，需手动删除。
  - 时间为空时创建为特殊任务，红色高亮，并每小时提醒。

- **任务视图切换**
  - 默认视图：显示未来 24 小时内的普通任务 + 今日特殊任务。
  - Command-A：切换为显示所有任务（未来和过期）
  - 再次 Command-A 或 Ctrl-A：返回默认视图。

- **终端提醒配置**
  请确保 `terminal-notifier` 可在以下路径运行：
  ```
  /Users/ivcylc_lca/Downloads/terminal-notifier-2.0.0/terminal-notifier.app/Contents/MacOS/terminal-notifier
  ```

## 自启动建议

如希望将其设置为开机启动，可使用 Automator 创建应用程序包装器，或将 `.command` 脚本拖入“登录项”。

## 示例界面

启动后将显示图形界面供添加、浏览与删除任务，任务视图支持右键删除与 Command+D 快捷键操作。

---

如需定制提醒内容、提示音或整合浏览器插件，可进一步拓展主程序逻辑。
