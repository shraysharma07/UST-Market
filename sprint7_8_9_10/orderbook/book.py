"""
Order Book Module

This module contains the Book class, which maintains the state of an order
book. An order book has two sides: bids (buy orders) and asks (sell orders).
The best bid is the highest price someone will pay. The best ask is the
lowest price someone will sell at.

The Book class processes three types of events:
- ADD: A new order enters the book
- ALTER: An existing order is modified
- DELETE: An order is canceled or filled

Author: Shray Sharma
Course: Fixed Income Trading Systems
"""


class Book:
    """
    Maintains the state of an order book.
    
    The order book tracks all outstanding buy and sell orders. Bids are
    sorted with the highest price first. Asks are sorted with the lowest
    price first.
    
    Attributes
    ----------
    bids : list
        Buy orders, highest price first.
    asks : list
        Sell orders, lowest price first.
    """
    
    def __init__(self):
        """Create an empty order book."""
        self.bids = []
        self.asks = []

    def _side(self, s):
        """
        Get the list for a given side.
        
        Parameters
        ----------
        s : str
            'B' for bids, 'A' for asks.
            
        Returns
        -------
        list
            The bids or asks list.
        """
        if s == "B":
            return self.bids
        if s == "A":
            return self.asks
        raise ValueError(f"Invalid side '{s}': expected 'B' or 'A'")

    def _find(self, lst, oid):
        """
        Find an order by ID.
        
        Parameters
        ----------
        lst : list
            The list to search.
        oid : str
            The order ID.
            
        Returns
        -------
        int or None
            The index if found, None otherwise.
        """
        for i, order in enumerate(lst):
            if order["oid"] == oid:
                return i
        return None

    def apply(self, change):
        """
        Apply a change to the order book.
        
        This handles ADD, ALTER, and DELETE commands. ADD and ALTER both
        insert an order at a position. DELETE reduces the quantity of an
        order and removes it if the quantity reaches zero.
        
        Parameters
        ----------
        change : dict
            The change event with keys: cmd, side, pos, oid, px, qdiff, seq, ts.
        """
        lst = self._side(change["side"])
        pos = max(0, change["pos"] - 1)
        qty = abs(change["qdiff"])
        cmd = change["cmd"]

        if cmd in ("ADD", "ALTER"):
            existing = self._find(lst, change["oid"])
            if existing is not None:
                lst.pop(existing)

            order = {
                "oid": change["oid"],
                "px": change["px"],
                "qty": qty,
                "seq": change["seq"],
                "ts": change["ts"],
            }

            if pos >= len(lst):
                lst.append(order)
            else:
                lst.insert(pos, order)
            return

        if cmd == "DELETE":
            idx = self._find(lst, change["oid"])
            if idx is None:
                return

            current = lst[idx]
            current["qty"] -= qty

            if current["qty"] <= 0:
                lst.pop(idx)
            else:
                current["seq"] = change["seq"]
                current["ts"] = change["ts"]
            return

        raise ValueError(f"Unknown command '{cmd}'")

    def best_bid_ask(self):
        """
        Get the best bid and ask prices.
        
        Returns
        -------
        tuple
            (best_bid, best_ask). Either can be None if that side is empty.
        """
        best_bid = self.bids[0]["px"] if self.bids else None
        best_ask = self.asks[0]["px"] if self.asks else None
        return best_bid, best_ask

    def snapshot(self):
        """
        Get the full book state.
        
        Returns
        -------
        tuple
            (bids, asks) where each is a list of (oid, px, qty) tuples.
        """
        bids = [(o["oid"], o["px"], o["qty"]) for o in self.bids]
        asks = [(o["oid"], o["px"], o["qty"]) for o in self.asks]
        return bids, asks