"""奖杯系统 — 支持可升级称号"""

class TrophySystem:
    @staticmethod
    def check(state, trophy_defs):
        """检查所有奖杯，返回新解锁列表。支持 level_check 可升级奖杯。"""
        newly = []
        earned = state.setdefault("_trophies", {})
        for td in trophy_defs:
            tid = td["id"]
            current = earned.get(tid)
            if current is None:
                # 首次检查
                try:
                    if td.get("check", lambda s: False)(state):
                        earned[tid] = {"day": state.get("_day", 0), "level": 0}
                        newly.append(td)
                except Exception:
                    pass
            elif td.get("level_check") and td.get("max_level", 0) > 0:
                # 可升级奖杯
                cur_lv = current.get("level", 0)
                if cur_lv < td["max_level"]:
                    try:
                        if td["level_check"](state, cur_lv + 1):
                            current["level"] = cur_lv + 1
                            newly.append({**td, "_new_level": cur_lv + 1})
                    except Exception:
                        pass
        return newly

    @staticmethod
    def count(state):
        return len(state.get("_trophies", {}))

    @staticmethod
    def earned_ids(state):
        return list(state.get("_trophies", {}).keys())
