"""跨游戏统一钱包"""

class Wallet:
    @staticmethod
    def balance(state):
        return state.get("_gold", 0)

    @staticmethod
    def add(state, amount):
        state["_gold"] = state.get("_gold", 0) + int(amount)

    @staticmethod
    def spend(state, amount):
        bal = state.get("_gold", 0)
        if amount > bal:
            return False
        state["_gold"] = bal - int(amount)
        return True
