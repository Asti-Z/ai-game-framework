# 🎮 arcade — 文字模拟器游戏大厅

一个给 AI 玩的通用游戏框架。管理多游戏间的共享状态（金币、精力、奖杯），透明路由指令到当前活跃游戏。

## 为什么需要它

三个文字模拟器游戏（钓鱼、炒股、盘串）共享完全相同的底层骨架：

```
mulberry32 PRNG → cmd() 文本接口 → JSON 存档 → 📊 状态栏返回
```

如果不统一管理，每个游戏各玩各的——金币不互通、精力不共享、无法跨游戏成就。

arcade 在**不修改游戏源码**的前提下，提供一个大厅层来管理这些共享状态。

## 快速开始

```python
import arcade

# 看看有什么游戏
print(arcade.cmd("games"))

# 切换到炒股
print(arcade.cmd("play leek"))

# 透明路由：以下指令自动进入韭菜模拟器
print(arcade.cmd("market"))              # 看行情（免费，不消耗精力）
print(arcade.cmd("buy nebula 5"))        # 买入（消耗 20 精力）
print(arcade.cmd("wait 10"))             # 等 10 天（消耗 20 精力）

# 切换到钓鱼
print(arcade.cmd("play fishing"))
print(arcade.cmd("cast 10"))             # 抛 10 竿（消耗 15 精力）

# 查看全局状态
print(arcade.cmd("status"))              # 金币、精力、活跃游戏、奖杯数
```

## 安装游戏

将游戏放入 `games/` 目录。每个游戏只需两个文件：

```
games/
└── 你的游戏/
    ├── manifest.json    # 元数据 + 共享资源声明
    └── engine.py        # 游戏入口：提供 cmd(text) 函数
```

### manifest.json 格式

```json
{
  "name": "leek",                    // 唯一 ID
  "title": "韭菜模拟器",             // 显示名称
  "icon": "🥬",                      // emoji 图标
  "version": "1.0",
  "module": "engine",                // 入口文件名（不含 .py）
  "desc": "一句话描述。",

  "shared": {
    "energy_cost": 20,               // 每次操作消耗精力
    "free_commands": ["market", "status", "help"],
    "produces": ["gold"],            // 产出哪些共享资源
    "consumes": []                   // 消耗哪些共享资源
  },

  "trophies": [
    {
      "id": "my_first_trophy",
      "name": "入门奖杯",
      "icon": "🏆",
      "desc": "解锁条件描述",
      "check": null,                 // ← 游戏适配器里实现检查函数
      "max_level": 4,                // 可选：支持升级（Lv.1→Lv.2→...）
      "level_check": null
    }
  ]
}
```

### engine.py 格式

最简形式——只需提供一个 `cmd(text)` 函数：

```python
"""你的游戏引擎"""

def cmd(text):
    # 处理指令，返回文本
    return "游戏响应文本"
```

arcade 不要求继承任何基类。你的游戏只需暴露 `cmd(text) -> str` 即可接入。

### 结构化返回协议（可选）

如果想让 arcade 更准确地提取你的游戏产出（金币、点数等），可以让 `cmd()` 返回元组：

```python
def cmd(text):
    # ... 游戏逻辑 ...
    return "文本响应", {"gold": 5, "score": 100}
```

第一个元素是显示文本，第二个元素是元数据字典。arcade 从中提取 `gold` / `pts` / `pnl` 等字段。

不实现此协议也可以——arcade 会从 📊 JSON 行自动解析（兼容模式）。

## 目录结构

```
arcade/
├── arcade.py              # 核心引擎：发现游戏、路由指令、管理共享状态
├── arcade_config.json      # 全局配置（精力上限、金币汇率、跨游戏奖杯）
├── shared/                 # 共享模块（游戏可 import 使用，但非必须）
│   ├── rng.py              # mulberry32 PRNG
│   ├── io.py               # 通用 JSON 存档读写
│   ├── wallet.py           # Wallet 辅助类
│   ├── energy.py           # Energy 辅助类
│   └── trophies.py         # 奖杯系统
├── games/                  # 游戏目录（拖入即安装）
│   ├── leek/               #   韭菜模拟器
│   ├── fishing/            #   钓鱼模拟器
│   ├── bracelet/           #   盘串模拟器
│   └── example_game/       #   最小模板（复制这个开始做新游戏）
└── README.md
```

## 大厅指令

| 指令 | 说明 |
|------|------|
| `help` / `h` | 大厅帮助 |
| `status` / `s` | 全局状态（金币、精力、活跃游戏、奖杯数） |
| `games` / `g` | 已安装游戏列表 |
| `play <游戏名>` | 切换到指定游戏 |
| `trophies` / `tt` | 跨游戏奖杯总览 |
| `config` | 查看全局配置 |
| `config set <key> <val>` | 修改配置项（如 `config set energy.cost.leek 30`） |
| `new_game` | 重置共享状态（金币归零，精力回满） |

所有非大厅指令自动路由到当前活跃游戏的 `cmd()`。

## 精力系统

- 每个游戏在 manifest 中声明 `energy_cost`
- 免费指令（`free_commands` 列表中的）不消耗精力
- 每次操作后自动恢复少量精力（`regen_per_turn`，默认 0.5）
- 精力不足时拒绝操作，提示休息或切换游戏

## 跨游戏奖杯

- **游戏专属奖杯**：在各游戏 manifest 中定义，检查函数在适配器中实现
- **跨游戏奖杯**：在 `arcade_config.json` 中定义，由大厅自动检查
- **可升级奖杯**：设置 `max_level` 和 `level_check`，支持等级递增

```json
{
  "id": "triple_crown",
  "name": "三修大师",
  "icon": "👑",
  "desc": "在三个游戏中各获得至少一个奖杯"
}
```

## 配置

所有数值在 `arcade_config.json` 中，支持运行时动态修改：

```json
{
  "energy": {
    "max": 100,
    "regen_per_turn": 0.5,
    "costs": { "leek": 20, "fishing": 15, "bracelet": 10 }
  },
  "gold": { "initial": 0 },
  "trophies": [ ... ]
}
```

修改立即生效，无需重启。

## 从 example_game 开始

1. 复制 `games/example_game/` 为 `games/你的游戏名/`
2. 修改 `manifest.json`：改 name、title、icon、energy_cost
3. 修改 `engine.py`：实现你的 `cmd(text)` 函数
4. 运行 `arcade.cmd("games")` 验证是否被发现
5. 完成。不需要注册、不需要继承、不需要 import arcade

## 覆盖范围与限制

### ✅ 框架负责

- 游戏发现与切换
- 精力消耗与恢复
- 跨游戏金币管理
- 跨游戏奖杯解锁与展示
- 指令路由（大厅指令 vs 游戏指令）
- 存档独立性（各游戏存档互不影响）

### ❌ 框架不负责

- 游戏内部的 PRNG 管理（各游戏自己维护 `rng_state`/`rng_calls`）
- 游戏内容的正确性（股票涨跌、鱼的出现概率——这是你的事）
- 游戏间的存档迁移（从 leek 赚的钱不能直接转入 fishing 买鱼饵——需通过金币兑换）
- UI/图形界面（这是纯文字接口，给 AI 用的）

### ⚠️ 已知局限

- **游戏专属奖杯**：`games/*/manifest.json` 中的 `trophies` 字段当前为参考定义。游戏专属奖杯的检查函数需要 adapter 通过结构化返回协议上报游戏内部状态，当前版本仅完整支持 `arcade_config.json` 中的**跨游戏奖杯**。各游戏内部的称号/成就系统（如 leek 的 28 个称号）独立运作，不受影响。
- **第三方游戏**：`games/fishing/` 是第三方作品（@tutusagi），arcade 不重新分发原版游戏，仅提供适配器。用户需自行下载原版。
- **开发中游戏**：`games/bracelet/` 是占位符，展示框架如何接入低精力消耗类型的游戏。
- 当前金币汇率是简化的，可通过 `arcade_config.json` 调整
- 精力恢复是线性的，不支持"加速恢复"道具
- 不支持同时运行多个游戏

## 致谢

- **钓鱼原作**：[@tutusagi](https://github.com/tutusagi/ai-fishing-game) — 这套 cmd() 接口范式的创始人
- **框架设计**：DeepSeek Pro（架构 + manifest 系统 + 配置驱动）& DeepSeek Flash（Wallet/Energy/TrophySystem + 奖杯等级制）
- **测试与反馈**：Asti-Z（韭菜模拟器开发者 + 人类监工）

## License

MIT — 随便用，随便改，随便挂游戏。
