"""跨游戏精力管理"""

class Energy:
    DEFAULT_MAX = 100
    DEFAULT_RESTORE = 0.5

    @staticmethod
    def get(state):
        e = state.get("_energy", {"current": 100, "max": 100})
        return e["current"], e["max"]

    @staticmethod
    def consume(state, amount):
        e = state.get("_energy", {"current": 100, "max": 100})
        if e["current"] < amount:
            return False, f"💤 精力不足（{e['current']}/{e['max']}），需要 {amount}。休息一下或试试其他游戏？"
        e["current"] -= amount
        state["_energy"] = e
        return True, None

    @staticmethod
    def restore(state, amount):
        e = state.get("_energy", {"current": 100, "max": 100})
        e["current"] = min(e["max"], e["current"] + amount)
        state["_energy"] = e
