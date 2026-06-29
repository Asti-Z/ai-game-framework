"""🎲 示例游戏 — 最简单的文字模拟器模板

复制这个目录，改 engine.py 和 manifest.json，你的游戏就能接入 arcade 大厅。
"""

import json, os, sys

# 引入共享模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.rng import Rng
from shared.io import SimIO

_SEED = 0xCAFE
_SAVE_FILE = "example_save.json"

def _default_state():
    rng = Rng(_SEED)
    return {
        "score": 0,
        "day": 1,
        "rng_state": rng.state,
        "rng_calls": rng.calls,
    }

_io = SimIO(_SAVE_FILE, _default_state)

def cmd(text):
    state = _io.load()
    rng = Rng(state["rng_state"], state["rng_calls"])

    text = text.strip()
    if not text:
        return _state_json(state)

    parts = [p.strip() for p in text.replace("\n", ";").split(";") if p.strip()]
    outputs = []

    for part in parts:
        words = part.split()
        if not words:
            continue
        c = words[0].lower()

        if c in ("help", "h"):
            outputs.append("🎲 示例游戏\n\n指令：flip（抛硬币）、score（看分数）、new_game（重开）")

        elif c == "flip":
            if rng.random() > 0.5:
                state["score"] += 1
                outputs.append("🪙 正面！+1分")
            else:
                outputs.append("🪙 反面。")
            state["day"] += 1

        elif c == "score":
            outputs.append(f"当前分数：{state['score']} · 第 {state['day']} 天")

        elif c == "new_game":
            state.clear()
            state.update(_default_state())
            outputs.append("🔄 新游戏。")

        else:
            outputs.append(f"未知指令：{c}。试试 flip 抛硬币。")

    state["rng_state"] = rng.state
    state["rng_calls"] = rng.calls
    _io.save(state)

    result = "\n".join(outputs)
    if result:
        result += "\n"
    result += _state_json(state)
    return result

def _state_json(state):
    return f'📊 {{"score": {state["score"]}, "day": {state["day"]}}}'
