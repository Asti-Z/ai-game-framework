# 更新日志

## v2.1 — AI 防沉迷系统 (2026-06-29)

### ✨ 新增

- **防沉迷：游戏级疲劳**
  - 每游戏可配置连续操作上限（manifest → shared.fatigue）
  - 达到警告回合 → 追加提示信息（不阻止操作）
  - 达到上限 → 阻止操作，提示冷却并建议切换游戏
  - 切换游戏自动重置疲劳计数 + 欢迎语

- **防沉迷：大厅级日上限**
  - `arcade_config.json` → `session.daily_max_turns`（默认关闭）
  - 开启后每日操作达到上限阻止所有游戏操作

- **欢迎语系统**
  - 切换游戏时显示情境欢迎语（leek / fishing / bracelet）

### 🐛 修复

- 修复 `config set` 嵌套键路径解析
- 修复 `arcade_config.json` 中的残留嵌套错误

### ⚙️ 配置

```json
// manifest.json — 游戏级疲劳（可选，不加 = 无限）
"shared": {
  "fatigue": {
    "max_consecutive_turns": 80,
    "warning_at": 50,
    "cooldown_turns": 15,
    "warning_text": "📊 你已经连续交易 {turns} 回合了。"
  }
}

// arcade_config.json — 大厅级日上限（默认关闭）
"session": {
  "daily_max_turns": 300,
  "overlimit_message": "🌙 今天玩得够多了。",
  "enabled": false
}
```

## v2.0 — 框架发布 (2026-06-29)

- 目录 + manifest 驱动架构
- 共享模块：RNG / IO / Wallet / Energy / TrophySystem
- 结构化返回协议（游戏可返回 text + metadata 元组）
- 📊 JSON 兼容模式
- 跨游戏金币/精力/奖杯系统
- 配置驱动（arcade_config.json，修改即时生效）
- 4 个游戏示例：leek / fishing / bracelet / example_game
