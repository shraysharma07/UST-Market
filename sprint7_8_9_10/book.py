class Book:
    def __init__(self):
        self.bids = []
        self.asks = []


    def _side(self, s):
        if s == "B":
            return self.bids
        if s == "A":
            return self.asks
        raise ValueError("bad side")

    def _find(self, lst, oid):
        for i, o in enumerate(lst):
            if o["oid"] == oid:
                return i
        return None

    def apply(self, ch):
        lst = self._side(ch["side"])
        pos = max(0, ch["pos"] - 1)
        qty = abs(ch["qdiff"])
        cmd = ch["cmd"]

        if cmd in ("ADD", "ALTER"):
            idx = self._find(lst, ch["oid"])
            if idx is not None:
                lst.pop(idx)

            order = {
                "oid": ch["oid"],
                "px": ch["px"],
                "qty": qty,
                "seq": ch["seq"],
                "ts": ch["ts"],
            }

            if pos >= len(lst):
                lst.append(order)
            else:
                lst.insert(pos, order)
            return

        if cmd == "DELETE":
            idx = self._find(lst, ch["oid"])
            if idx is None:
                return

            cur = lst[idx]
            cur["qty"] -= qty

            if cur["qty"] <= 0:
                lst.pop(idx)
            else:
                cur["seq"] = ch["seq"]
                cur["ts"] = ch["ts"]
            return

        raise ValueError("unknown cmd")

    def best_bid_ask(self):
        best_bid = self.bids[0]["px"] if self.bids else None
        best_ask = self.asks[0]["px"] if self.asks else None
        return best_bid, best_ask

    def snapshot(self):
        return (
            [(o["oid"], o["px"], o["qty"]) for o in self.bids],
            [(o["oid"], o["px"], o["qty"]) for o in self.asks],
        )
