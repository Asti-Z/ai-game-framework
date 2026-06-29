"""🎮 arcade — 文字模拟器游戏大厅 v2.0

整合设计：
- 目录 + manifest 驱动（零门槛接入，只需 cmd(text) 函数）
- 奖杯等级制（Lv.1 → Lv.2 → ...）
- 结构化返回协议（游戏可返回 (text, metadata) 元组）
- Wallet / Energy / TrophySystem 辅助类
- 所有配置在 arcade_config.json，支持动态修改

大厅指令：
  help / h              大厅帮助
  status / s            全局状态
  games / g             已安装游戏列表
  play <游戏名>          切换到指定游戏
  trophies / tt         跨游戏奖杯总览
  config [set key val]  查看/修改配置
  new_game              重置共享状态

游戏指令透明路由到当前活跃游戏。返回协议：
  游戏 cmd() 返回 str           → 兼容模式
  游戏 cmd() 返回 (str, dict)   → 从 dict 提取 gold/pts/anxiety
"""

import json, os, sys, re, importlib.util

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_FILE = os.path.join(_BASE_DIR, "arcade_config.json")
_STATE_FILE = os.path.join(_BASE_DIR, "data", "arcade_state.json")
_GAMES_DIR = os.path.join(_BASE_DIR, "games")

# 确保 data 目录存在
os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)

from shared.wallet import Wallet
from shared.energy import Energy
from shared.trophies import TrophySystem

# ═══════════════════════════════════════════
# ── 配置与状态 ──
# ═══════════════════════════════════════════

def _load_config():
    with open(_CONFIG_FILE, "r") as f:
        return json.load(f)

def _default_state():
    cfg = _load_config()
    return {
        "version": 2,
        "gold": cfg["gold"]["initial"],
        "energy": cfg["energy"]["max"],
        "max_energy": cfg["energy"]["max"],
        "active_game": None,
        "game_sessions": {},
        "trophies": {},
        "total_turns": 0,
        "_energy": {"current": cfg["energy"]["max"], "max": cfg["energy"]["max"]},
        "_gold": cfg["gold"]["initial"],
        "_trophies": {},
    }

def _load_state():
    try:
        with open(_STATE_FILE, "r") as f:
            state = json.load(f)
        # 确保框架字段存在
        state.setdefault("_energy", {"current": 100, "max": 100})
        state.setdefault("_gold", 0)
        state.setdefault("_trophies", {})
        state.setdefault("game_sessions", {})
        return state
    except:
        state = _default_state()
        _save_state(state)
        return state

def _save_state(state):
    with open(_STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# ── 游戏发现 ──
# ═══════════════════════════════════════════

def _discover_games():
    games = {}
    if not os.path.isdir(_GAMES_DIR):
        return games
    for name in sorted(os.listdir(_GAMES_DIR)):
        manifest_path = os.path.join(_GAMES_DIR, name, "manifest.json")
        engine_path = os.path.join(_GAMES_DIR, name, "engine.py")
        if os.path.isfile(manifest_path) and os.path.isfile(engine_path):
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            manifest["_dir"] = os.path.join(_GAMES_DIR, name)
            games[name] = manifest
    return games

def _load_engine(game_name):
    games = _discover_games()
    if game_name not in games:
        return None
    g = games[game_name]
    engine_path = os.path.join(g["_dir"], g.get("module", "engine") + ".py")
    spec = importlib.util.spec_from_file_location(f"arcade_{game_name}", engine_path)
    mod = importlib.util.module_from_spec(spec)
    old_cwd = os.getcwd()
    os.chdir(g["_dir"])
    try:
        spec.loader.exec_module(mod)
    finally:
        os.chdir(old_cwd)
    return mod

# ═══════════════════════════════════════════
# ── 结构化返回协议 ──
# ═══════════════════════════════════════════

def _exec_game_cmd(engine, text):
    """执行游戏指令，支持两种返回格式：
    - str: 纯文本（兼容模式），从 📊 行解析元数据
    - (str, dict): 文本 + 元数据元组
    返回 (text, metadata_dict)
    """
    try:
        result = engine.cmd(text)
    except Exception as e:
        return f"⚠️ 游戏执行出错：{e}", {}

    if isinstance(result, tuple) and len(result) == 2:
        text_out, meta = result
        return text_out, meta

    # 兼容模式：从 📊 JSON 行提取元数据
    meta = {}
    for line in str(result).split("\n"):
        if line.strip().startswith("📊"):
            try:
                data = json.loads(line.strip()[2:])
                meta.update(data)
            except:
                pass
    return str(result), meta

# ═══════════════════════════════════════════
# ── 跨游戏奖杯 ──
# ═══════════════════════════════════════════

def _check_cross_trophies(state):
    cfg = _load_config()
    earned = TrophySystem.earned_ids(state)
    new_trophies = []
    all_defs = []
    # 收集所有奖杯定义（全局 + 各游戏）
    for t in cfg.get("trophies", []):
        all_defs.append(t)
    for name, m in _discover_games().items():
        for t in m.get("trophies", []):
            if not any(x.get("id") == t.get("id") for x in all_defs):
                all_defs.append(t)
    return TrophySystem.check(state, all_defs)

# ═══════════════════════════════════════════
# ── cmd() 主入口 ──
# ═══════════════════════════════════════════

def cmd(text):
    state = _load_state()
    cfg = _load_config()
    games = _discover_games()

    text = text.strip()
    if not text:
        return _state_json(state)

    parts = [p.strip() for p in text.replace("\n", ";").split(";") if p.strip()]
    if len(parts) > 8:
        parts = parts[:8]

    outputs = []
    for part in parts:
        out = _route(part, state, cfg, games)
        if out is not None:
            outputs.append(out)
        _save_state(state)

    # 跨游戏奖杯
    new_trophies = _check_cross_trophies(state)
    for td in new_trophies:
        lv = td.get("_new_level", 0)
        lv_str = f" Lv.{lv}" if lv else ""
        outputs.append(f"🏆 解锁奖杯：{td.get('icon','')}{td.get('name','?')}{lv_str} — {td.get('desc','')}")

    _save_state(state)

    result = "\n".join(outputs)
    if result:
        result += "\n"
    result += _state_json(state)
    return result


def _route(part, state, cfg, games):
    words = part.split()
    if not words:
        return None
    c = words[0].lower()
    a = words[1:]

    # ── 大厅指令 ──
    if c in ("help", "h"):
        return _cmd_help(games)
    if c in ("status", "s"):
        return _cmd_status(state, cfg, games)
    if c in ("games", "g"):
        return _cmd_list_games(games, state)
    if c == "play":
        return _cmd_play(a, state, games)
    if c in ("trophies", "tt"):
        return _cmd_trophies(state, cfg)
    if c == "config":
        return _cmd_config(a, cfg)
    if c == "new_game":
        return _cmd_reset(state)

    # ── 游戏指令 ──
    active = state.get("active_game")
    if not active:
        return "⚠️ 没有活跃游戏。请先 play <游戏名> 选择一个游戏。"

    manifest = games.get(active)
    if not manifest:
        return f"⚠️ 游戏 '{active}' 未安装。"

    # 免费指令检查
    free_cmds = manifest.get("shared", {}).get("free_commands", [])
    cmd_root = words[0].lower()
    is_free = cmd_root in free_cmds or cmd_root in ("s", "h", "l", "n", "t", "od", "wl", "cp", "ach", "tt", "sm", "cy", "j", "hx")

    # 精力恢复（在上次操作后恢复）
    Energy.restore(state, cfg.get("energy", {}).get("regen_per_turn", 0.5))

    # 精力消耗
    if not is_free:
        energy_cost = cfg.get("energy", {}).get("costs", {}).get(active, 10)
        ok, err = Energy.consume(state, energy_cost)
        if not ok:
            return err

    state["total_turns"] = state.get("total_turns", 0) + 1
    state.setdefault("game_sessions", {}).setdefault(active, {"total_turns": 0})["total_turns"] += 1

    # 执行游戏指令
    engine = _load_engine(active)
    if not engine or not hasattr(engine, "cmd"):
        return f"⚠️ 游戏 '{active}' 引擎加载失败。"

    game_text, meta = _exec_game_cmd(engine, part)

    # 结构化协议：从 meta 收集产物
    if "gold" in meta:
        Wallet.add(state, meta["gold"])
    elif "pnl" in meta:
        # 炒股盈利 → 金币（每100利润 = 1金币）
        pnl_str = str(meta["pnl"]).replace("+", "")
        try:
            pnl = float(pnl_str)
            delta = max(0, int((pnl - state.get("_last_leek_pnl", 0)) / 100))
            if delta > 0:
                Wallet.add(state, delta)
                state["_last_leek_pnl"] = pnl
        except:
            pass
    elif "pts" in meta:
        # 钓鱼点数 → 金币（10点 = 1金币）
        pts = int(meta["pts"])
        delta = (pts - state.get("_last_fishing_pts", 0)) // 10
        if delta > 0:
            Wallet.add(state, delta)
            state["_last_fishing_pts"] = pts

    return game_text


# ═══════════════════════════════════════════
# ── 大厅指令实现 ──
# ═══════════════════════════════════════════

def _cmd_help(games):
    lines = [
        "🎮 arcade v2.0 · 文字模拟器游戏大厅",
        f"已安装：{len(games)} 个游戏",
        "",
        "── 大厅 ──",
        "  help / h · status / s · games / g · play <游戏>",
        "  trophies / tt · config [set k v] · new_game",
        "",
        "── 游戏指令（透明路由）──",
        "  play leek 之后，buy nebula 5 → 韭菜模拟器",
        "  批处理：play leek; buy nebula 5; wait 10; sell nebula all",
    ]
    if games:
        lines.append("")
        lines.append("── 已安装 ──")
        for name, m in games.items():
            icon = m.get("icon", "🎲")
            lines.append(f"  {icon} {m.get('title', name)} — {m.get('desc', '')[:50]}")
    return "\n".join(lines)


def _cmd_status(state, cfg, games):
    active = state.get("active_game", "-")
    active_label = ""
    if active and active in games:
        active_label = f"{games[active].get('icon','')}{games[active].get('title', active)}"

    cur_e, max_e = Energy.get(state)
    lines = [
        "🎮 【大厅】",
        f"金币：{Wallet.balance(state)} 💰",
        f"精力：{cur_e}/{max_e} ⚡",
        f"活跃：{active_label or active}",
        f"回合：{state.get('total_turns', 0)} ｜ 奖杯：{TrophySystem.count(state)}",
    ]

    sessions = state.get("game_sessions", {})
    if sessions:
        lines.append("")
        for gname, sess in sessions.items():
            gm = games.get(gname, {})
            lines.append(f"  {gm.get('icon','🎲')} {gm.get('title', gname)}：{sess.get('total_turns', 0)} 回合")
    return "\n".join(lines)


def _cmd_list_games(games, state):
    if not games:
        return "📭 没有安装任何游戏。请将游戏放入 games/ 目录。"
    active = state.get("active_game")
    cfg = _load_config()
    lines = ["🎲 【游戏列表】"]
    for name, m in games.items():
        mark = " ◀ 当前" if name == active else ""
        cost = cfg.get("energy", {}).get("costs", {}).get(name, "?")
        lines.append(f"  {m.get('icon','🎲')} {m.get('title', name)}{mark} — 精力：{cost}")
        lines.append(f"     {m.get('desc', '')[:60]}")
    return "\n".join(lines)


def _cmd_play(a, state, games):
    if not a:
        return "格式：play <游戏名>。用 games 查看可选游戏。"
    name = a[0].lower()
    if name not in games:
        return f"未安装 '{name}'。可选：{', '.join(games.keys())}"
    state["active_game"] = name
    state.setdefault("game_sessions", {}).setdefault(name, {"total_turns": 0})
    m = games[name]
    return f"🎮 已切换到 {m.get('icon','')}{m.get('title', name)}。\n{m.get('desc','')}"


def _cmd_trophies(state, cfg):
    all_trophies = []
    for t in cfg.get("trophies", []):
        all_trophies.append(t)
    for name, m in _discover_games().items():
        for t in m.get("trophies", []):
            if not any(x.get("id") == t.get("id") for x in all_trophies):
                all_trophies.append(t)

    earned = state.get("_trophies", {})
    lines = [f"🏆 【奖杯】{len(earned)}/{len(all_trophies)}"]
    for t in all_trophies:
        tid = t["id"]
        if tid in earned:
            lv = earned[tid].get("level", 0)
            lv_str = f" Lv.{lv}" if lv else ""
            lines.append(f"  ✅ {t.get('icon','')}{t.get('name','?')}{lv_str}")
        else:
            lines.append(f"  🔒 {t.get('icon','')}{t.get('name','?')} — {t.get('desc','')[:40]}")
    return "\n".join(lines)


def _cmd_config(a, cfg):
    if not a:
        return f"当前配置：\n{json.dumps(cfg, ensure_ascii=False, indent=2)}"
    if a[0] == "set" and len(a) >= 3:
        key = a[1]
        val = a[2]
        keys = key.split(".")
        target = cfg
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        try:
            target[keys[-1]] = float(val) if "." in val else (int(val) if val.lstrip("-").isdigit() else val)
        except:
            target[keys[-1]] = val
        with open(_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return f"⚙️ {key} = {val}"
    return "格式：config 或 config set <key> <val>"


def _cmd_reset(state):
    new_state = _default_state()
    state.clear()
    state.update(new_state)
    _save_state(state)
    return "🔄 共享状态已重置。"


def _state_json(state):
    cur_e, max_e = Energy.get(state)
    return (
        f'📊 {{"gold": {Wallet.balance(state)}, "energy": {cur_e}/{max_e}, '
        f'"active": "{state.get("active_game", "-")}", '
        f'"turns": {state.get("total_turns", 0)}, '
        f'"trophies": {TrophySystem.count(state)}}}'
    )


# ═══════════════════════════════════════════
# ── 入口 ──
# ═══════════════════════════════════════════
if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(cmd(" ".join(sys.argv[1:])))
    else:
        print(cmd("help"))
