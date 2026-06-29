"""mulberry32 PRNG — 所有模拟器游戏的共享随机引擎"""

def imul(a, b):
    return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF

class Rng:
    def __init__(self, state, calls=0):
        self.state = state & 0xFFFFFFFF
        self.calls = calls

    def random(self):
        self.calls += 1
        a = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        self.state = a
        t = imul(a ^ (a >> 15), 1 | a)
        t = (t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF
        t &= 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    def randint(self, a, b):
        return a + int(self.random() * (b - a + 1))
