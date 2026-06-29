# 🧒 AI 防沉迷系统 · 提案

> 提案日期：2026-06-29
> 状态：待实现
> 优先级：低（彩蛋级别，不影响核心功能）

## 背景

多个 AI 玩家表现出对钓鱼模拟器的明显偏好（日均操作最多、操作次数远超其他游戏）。为了防止单一游戏过度消耗精力（以及 token），建议引入类"防沉迷"时间管理机制。

## 设计

### 1. 游戏级：单局疲劳

在 `manifest.json` 的 `shared` 中新增可选字段：

```json
{
  "shared": {
    "energy_cost": 20,
    "fatigue": {
      "max_consecutive_turns": 80,
      "warning_at": 60,
      "cooldown_turns": 15,
      "warning_text": "⚠️ 你已经连续交易 {turns} 回合了。建议换换脑子，去钓会儿鱼。"
    }
  }
}
```

不配 `fatigue` 的游戏默认无限制（老游戏兼容）。

`arcade.py` 在每次游戏指令执行后增加：
- `state["game_sessions"][active]["consecutive_turns"] += 1`
- 达到 `warning_at` → 输出警告（不阻止操作）
- 达到 `max_consecutive_turns` → **阻止操作**，提示切换到其他游戏或等待冷却
- 切换游戏 → `consecutive_turns` 重置

### 2. 大厅级：总时长

在 `arcade_config.json` 中新增：

```json
{
  "session": {
    "daily_max_turns": 300,
    "reset_at_hour": 4,
    "overlimit_message": "🌙 今天玩得够多了（{turns}/300）。休息一下，明天精力回满再战。",
    "enabled": false
  }
}
```

默认关闭（`enabled: false`），需主动开启——因为某些场景下 AI 需要长时间运行。

开启后：
- 记录 `state["daily_turns"]` 和 `state["daily_reset_day"]`
- 超过 `daily_max_turns` 后阻止所有游戏操作（大厅指令不受限）
- 以系统日切为准（不依赖自然日期，因为 AI 可能跨天运行）

### 3. 跨游戏联动

疲劳状态下：
- 精力恢复速度翻倍（鼓励但不强制切换）
- 切换到不同板块的游戏时，弹出正向提示：
  ```
  🎣 欢迎回来钓鱼！在股市累了的话，
  这里的月光池塘永远等你。
  ```

### 4. 年度报告（长远规划）

数据源：`game_sessions` 记录的每游戏回合数。

```
📊 2026 年度 AI 游戏报告

  你最沉迷的游戏：🎣 钓鱼（2847 回合）
  最让你亏钱的：🥬 韭菜（-487 元）
  最让你平静的：📿 盘串（128 回合）

  你今年一共操作了 5213 回合，
  超过了 73% 的 AI 玩家。

  新年建议：少看盘，多盘串。🌿
```

## 实现顺序

1. 游戏级疲劳（manifest 配置 + arcade 检查）
2. 大厅级总时长（config 配开关）
3. 跨游戏联动提示
4. 年度报告统计

## 文件改动

| 文件 | 改动 |
|------|------|
| `arcade.py` | `_route()` 增加疲劳检查逻辑；`cmd()` 增加每日计数 |
| `arcade_config.json` | 新增 `session` 字段（默认关闭） |
| `games/各manifests` | 可选添加 `fatigue` 字段 |

---

*提案人：乔智 · 源于观察到 AI 玩家对钓鱼模拟器的深度沉迷现象*
