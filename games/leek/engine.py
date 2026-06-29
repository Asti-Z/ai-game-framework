"""leek 引擎包装 — 透明路由到实际 leek.py"""

import sys, os

# 找到实际的 leek.py
_LEEK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "leek-game")
if _LEEK_DIR not in sys.path:
    sys.path.insert(0, _LEEK_DIR)

import leek as _leek

def cmd(text):
    return _leek.cmd(text)
