class TradeStateMachine:

    def __init__(self, entry, sl, tp):
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.state = "OPEN"
        self.be = entry

    def update(self, price):
        if self.state == "OPEN" and price >= self.entry + (self.entry - self.sl):
            self.state = "BREAK_EVEN"
            self.sl = self.entry

        if price >= self.tp:
            self.state = "TP_HIT"

        if price <= self.sl:
            self.state = "SL_HIT"

        return self.state
