"""通用 JSON 存档读写 — 自动创建新档、版本迁移"""

import json, os

class SimIO:
    def __init__(self, save_file, default_state_factory):
        self.save_file = save_file
        self.factory = default_state_factory

    def load(self):
        try:
            with open(self.save_file, "r") as f:
                return json.load(f)
        except:
            state = self.factory()
            self.save(state)
            return state

    def save(self, state):
        with open(self.save_file, "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def reset(self):
        if os.path.exists(self.save_file):
            os.remove(self.save_file)
        return self.load()
