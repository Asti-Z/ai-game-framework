"""fishing 适配器 — 桥接到原版钓鱼游戏

⚠️ 此适配器需要用户自行安装原版 fishing.py
   原作者：@tutusagi (github.com/tutusagi/ai-fishing-game)
   arcade 框架不重新分发原版游戏文件。

安装方法：
   将 fishing.py 放入本目录，或将路径加入 sys.path。
"""

import sys, os

# 尝试常见路径
_PATHS = [
    os.path.join(os.path.dirname(__file__), "fishing.py"),
    os.path.expanduser("~/桌面/fishing.py"),
    os.path.expanduser("~/Downloads/fishing.py"),
]

_FOUND = None
for _p in _PATHS:
    _d = os.path.dirname(_p)
    if os.path.isfile(_p):
        _FOUND = _d
        break

if _FOUND and _FOUND not in sys.path:
    sys.path.insert(0, _FOUND)

try:
    import fishing as _fishing
    def cmd(text):
        return _fishing.cmd(text)
except ImportError:
    def cmd(text):
        return "🎣 钓鱼模拟器未安装。请从 github.com/tutusagi/ai-fishing-game 下载 fishing.py，放入本目录后重试。"
