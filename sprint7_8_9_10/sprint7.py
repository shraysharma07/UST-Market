"""
Order Book Replay and Fixed Income Calculator

This module does two things. First, it replays historical order book data
from a CSV file, letting you step through changes one at a time. Second,
it calculates present values for fixed income securities like Treasury bonds.

The order book replay loads market data and applies each change to rebuild
the book state at any point in time. You can use the terminal interface to
step forward and backward, or calculate metrics at regular intervals.

The fixed income calculator handles bond math. Given a yield, it computes
the price. Given a price, it solves for the yield. It also generates cash
flow schedules and calculates present values.
"""

import csv
import curses
import os
import sys
import time

try:
    from orderbook import Book
except ImportError:
    try:
        from .orderbook import Book
    except ImportError:
        from orderbook.book import Book


# Column name constants for the CSV file
COL_TS = "Timestamp"
COL_RT = "Record Type"
COL_INST = "Instrument"
COL_POS = "Ob Position"
COL_QDIFF = "Quantity Diff"
COL_CMD = "Ob Command"
COL_ID = "Order Number"
COL_PX = "Premium (256ths)"
COL_SIDE = "Bid/Ask"
COL_SEQ = "Sequence"


class FixedIncomeCalculator:
    """
    Calculator for bond pricing and yield calculations.
    
    This class handles the math for fixed income securities. A bond pays
    regular coupon payments plus the face value at maturity. The present
    value is what those future payments are worth today, discounted by
    the yield.
    
    Price and yield move in opposite directions. When yields go up, prices
    go down. When yields go down, prices go up.
    
    Parameters
    ----------
    years : float
        Time to maturity in years. Default is 2.
    coupon_rate : float
        Annual coupon rate as a decimal. Default is 0.04 (4%).
    face : float
        Face value of the bond. Default is 100.
    freq : int
        Number of coupon payments per year. Default is 2 (semiannual).
    """
    
    def __init__(self, years=2, coupon_rate=0.04, face=100, freq=2):
        self.years = years
        self.coupon_rate = coupon_rate
        self.face = face
        self.freq = freq
    
    def cash_flows(self):
        """
        Generate the cash flow schedule for this bond.
        
        Each period pays a coupon equal to (annual rate / frequency) * face.
        The final period also includes the face value.
        
        Returns
        -------
        list of float
            Cash flow for each period.
        """
        periods = int(self.years * self.freq)
        coupon = (self.coupon_rate / self.freq) * self.face
        
        flows = [coupon] * periods
        flows[-1] += self.face
        
        return flows
    
    def present_value(self, ytm):
        """
        Calculate the present value of all cash flows.
        
        Each cash flow is discounted back to today using the yield.
        The formula is: PV = sum of (CF / (1 + r)^t) for each period.
        
        Parameters
        ----------
        ytm : float
            Yield to maturity as an annual rate.
        
        Returns
        -------
        float
            Present value of the bond.
        """
        flows = self.cash_flows()
        period_rate = ytm / self.freq
        
        pv = 0.0
        for i, cf in enumerate(flows):
            discount_factor = (1.0 + period_rate) ** (i + 1)
            pv += cf / discount_factor
        
        return pv
    
    def price_from_ytm(self, ytm):
        """
        Calculate bond price from yield to maturity.
        
        This is the same as present_value. The price is what you pay
        to earn that yield.
        
        Parameters
        ----------
        ytm : float
            Yield to maturity as an annual rate.
            
        Returns
        -------
        float
            Bond price.
        """
        return self.present_value(ytm)
    
    def solve_ytm(self, market_price, tolerance=1e-10):
        """
        Find the yield that produces a given price.
        
        This uses the bisection method. It starts with a range of possible
        yields, tests the midpoint, and narrows the range based on whether
        the resulting price is too high or too low.
        
        Parameters
        ----------
        market_price : float
            The observed market price.
        tolerance : float
            How precise the answer needs to be.
            
        Returns
        -------
        float
            The yield to maturity.
        """
        low, high = -0.5, 1.0
        
        while high - low > tolerance:
            mid = (low + high) / 2
            price = self.price_from_ytm(mid)
            diff = price - market_price
            
            if abs(diff) < 1e-8:
                return mid
            
            if diff > 0:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2


class OrderBookReplay:
    """
    Replays historical order book data from a CSV file.
    
    This class loads order book changes and applies them one at a time.
    You can step forward and backward through the history, or jump to
    any point. It also calculates present values at regular intervals.
    
    Parameters
    ----------
    path : str, optional
        Path to the CSV file. If not provided, searches common locations.
    instrument : str, optional
        Which instrument to track. Default is "2_YEAR".
    depth : int, optional
        Number of price levels to display. Default is 12.
    """
    
    DEFAULT_PATHS = [
        "2_20180108_merged.csv",
        os.path.join("sprint2", "2_20180108_merged.csv"),
        os.path.join("..", "sprint2", "2_20180108_merged.csv"),
        os.path.join("data", "2_20180108_merged.csv"),
    ]
    
    def __init__(self, path=None, instrument=None, depth=12):
        self.path = path
        self.instrument = instrument if instrument is not None else "2_YEAR"
        self.depth = depth
        self.changes = []
        self.book = Book()
        self.current_index = 0
    
    @classmethod
    def find_default_csv(cls):
        """Search for the data file in common locations."""
        env_path = os.environ.get("CSV_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        
        for p in cls.DEFAULT_PATHS:
            if os.path.exists(p):
                return p
        
        return None
    
    def load(self):
        """
        Load order book changes from the CSV file.
        
        This reads the file, filters for the specified instrument, and
        sorts by sequence number. The book is reset to empty.
        
        Returns
        -------
        self
            For method chaining.
        """
        if self.path is None:
            self.path = self.find_default_csv()
        
        if self.path is None or not os.path.exists(self.path):
            raise FileNotFoundError(
                "No data file found. Provide a path or set CSV_PATH."
            )
        
        required_columns = [
            COL_RT, COL_INST, COL_POS, COL_QDIFF,
            COL_CMD, COL_ID, COL_PX, COL_SIDE, COL_SEQ
        ]
        
        with open(self.path, "r", newline="") as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                raise ValueError("CSV file has no header row")
            
            missing = [c for c in required_columns if c not in reader.fieldnames]
            if missing:
                raise ValueError(f"CSV missing columns: {', '.join(missing)}")
            
            self.changes = []
            for row in reader:
                if row[COL_RT] != "OB_CHANGE":
                    continue
                if row[COL_INST] != self.instrument:
                    continue
                
                pos_raw = (row.get(COL_POS) or "").strip()
                if pos_raw == "":
                    continue
                
                self.changes.append({
                    "ts": row.get(COL_TS, ""),
                    "pos": int(float(pos_raw)),
                    "qdiff": int(float(row[COL_QDIFF])),
                    "cmd": row[COL_CMD].strip().upper(),
                    "oid": row[COL_ID],
                    "px": int(float(row[COL_PX])),
                    "side": row[COL_SIDE].strip().upper(),
                    "seq": int(float(row[COL_SEQ])),
                })
            
            self.changes.sort(key=lambda x: x["seq"])
        
        self.book = Book()
        self.current_index = 0
        
        return self
    
    def step(self):
        """Apply the next change. Returns the change or None if at end."""
        if self.current_index >= len(self.changes):
            return None
        
        change = self.changes[self.current_index]
        self.book.apply(change)
        self.current_index += 1
        return change
    
    def step_back(self):
        """Go back one step by rebuilding. Returns True if successful."""
        if self.current_index <= 0:
            return False
        
        self.current_index -= 1
        self._rebuild_to_current()
        return True
    
    def _rebuild_to_current(self):
        """Rebuild the book up to the current index."""
        self.book = Book()
        for i in range(self.current_index):
            self.book.apply(self.changes[i])
    
    def jump_to(self, index):
        """Jump to a specific point in history."""
        self.current_index = max(0, min(index, len(self.changes)))
        self._rebuild_to_current()
    
    def calc_pv_at_intervals(self, interval_minutes=10, calculator=None):
        """
        Calculate present value at regular time intervals.
        
        This steps through all changes and records the mid price, yield,
        and present value at each interval.
        
        Parameters
        ----------
        interval_minutes : int
            Minutes between calculations.
        calculator : FixedIncomeCalculator, optional
            Calculator to use. Creates a default one if not provided.
            
        Returns
        -------
        list of dict
            Each entry has ts, mid, ytm, and pv.
        """
        if calculator is None:
            calculator = FixedIncomeCalculator()
        
        results = []
        temp_book = Book()
        last_time = None
        
        for change in self.changes:
            temp_book.apply(change)
            ts_str = change.get("ts", "")
            if not ts_str:
                continue
            
            try:
                ts_clean = ts_str.split(".")[0].strip()
                if "T" in ts_clean:
                    ts_clean = ts_clean.replace("T", " ")
                time_tuple = time.strptime(ts_clean, "%Y-%m-%d %H:%M:%S")
                current_time = time.mktime(time_tuple)
            except (ValueError, OverflowError):
                continue
            
            if last_time is None:
                last_time = current_time
            
            elapsed_minutes = (current_time - last_time) / 60.0
            if elapsed_minutes >= interval_minutes:
                best_bid, best_ask = temp_book.best_bid_ask()
                mid = None
                
                if best_bid is not None and best_ask is not None:
                    mid = (premium_to_price(best_bid) + premium_to_price(best_ask)) / 2.0
                elif best_bid is not None:
                    mid = premium_to_price(best_bid)
                elif best_ask is not None:
                    mid = premium_to_price(best_ask)
                
                if mid is not None:
                    ytm = calculator.solve_ytm(mid)
                    pv = calculator.present_value(ytm)
                    results.append({
                        "ts": ts_str,
                        "mid": mid,
                        "ytm": ytm,
                        "pv": pv
                    })
                
                last_time = current_time
        
        return results
    
    def run_terminal_ui(self):
        """
        Launch the terminal interface.
        
        Use arrow keys to step forward and backward. Press ESC to exit.
        """
        if not self.changes:
            self.load()
        
        def _draw(stdscr, idx):
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            
            header = (f"OB replay ({self.instrument})  "
                     f"idx={idx}/{len(self.changes)}   "
                     f"UP=next DOWN=prev ESC=quit")
            stdscr.addstr(0, 0, header[:w-1])
            
            temp_book = Book()
            for i in range(idx):
                temp_book.apply(self.changes[i])
            
            bids = temp_book.bids[:self.depth]
            asks = temp_book.asks[:self.depth]
            
            stdscr.addstr(2, 0, "BID (Buy)                         | ASK (Sell)")
            stdscr.addstr(3, 0, "pos  qty   px     id tail         | pos  px     qty   id tail")
            stdscr.addstr(4, 0, "-" * min(w-1, 80))
            
            for i in range(self.depth):
                left = " " * 32
                right = ""
                
                if i < len(bids):
                    o = bids[i]
                    left = f"{i+1:<4}{o['qty']:<6}{o['px']:<7}{o['oid'][-8:]:<10}"
                
                if i < len(asks):
                    o = asks[i]
                    right = f"{i+1:<4}{o['px']:<7}{o['qty']:<6}{o['oid'][-8:]:<10}"
                
                stdscr.addstr(5 + i, 0, f"{left:<32}| {right}"[:w-1])
            
            if idx > 0:
                c = self.changes[idx - 1]
                footer = (f"last: seq={c['seq']} ts={c['ts']} cmd={c['cmd']} "
                         f"side={c['side']} pos={c['pos']} px={c['px']} "
                         f"qdiff={c['qdiff']} id={c['oid']}")
                stdscr.addstr(min(h-1, 5 + self.depth + 2), 0, footer[:w-1])
            
            stdscr.refresh()
        
        def _main(stdscr):
            curses.curs_set(0)
            stdscr.nodelay(False)
            stdscr.keypad(True)
            
            idx = 0
            while True:
                _draw(stdscr, idx)
                k = stdscr.getch()
                
                if k == 27:
                    return
                elif k == curses.KEY_UP:
                    if idx < len(self.changes):
                        idx += 1
                elif k == curses.KEY_DOWN:
                    if idx > 0:
                        idx -= 1
        
        curses.wrapper(_main)
    
    def benchmark(self, n=5000):
        """Process n changes and print timing information."""
        if not self.changes:
            self.load()
        
        upto = min(n, len(self.changes))
        
        t0 = time.perf_counter()
        temp_book = Book()
        for i in range(upto):
            temp_book.apply(self.changes[i])
        t1 = time.perf_counter()
        
        elapsed = t1 - t0
        print(f"Processed {upto} changes in {elapsed:.4f}s "
              f"({upto/elapsed:.0f} changes/sec)")
        return elapsed


def premium_to_price(premium_256ths):
    """
    Convert treasury price from 256ths to decimal.
    
    Treasuries are quoted in 256ths of a point. 25600 equals 100.00.
    """
    return premium_256ths / 256.0


# Legacy function wrappers for backward compatibility

def pv_cash_flows(years=2, coupon_rate=0.04, face=100, freq=2):
    calc = FixedIncomeCalculator(years, coupon_rate, face, freq)
    return calc.cash_flows()


def present_value(cash_flows, ytm, freq=2):
    period_rate = ytm / freq
    pv = 0.0
    for i, cf in enumerate(cash_flows):
        pv += cf / ((1.0 + period_rate) ** (i + 1))
    return pv


def price_from_ytm(ytm, years=2, coupon_rate=0.04, face=100, freq=2):
    calc = FixedIncomeCalculator(years, coupon_rate, face, freq)
    return calc.price_from_ytm(ytm)


def solve_ytm(market_price, years=2, coupon_rate=0.04, face=100, freq=2):
    calc = FixedIncomeCalculator(years, coupon_rate, face, freq)
    return calc.solve_ytm(market_price)


def load_changes(path, instrument=None):
    replay = OrderBookReplay(path=path, instrument=instrument)
    replay.load()
    return replay.changes


def build_book(changes, upto):
    b = Book()
    for i in range(upto):
        b.apply(changes[i])
    return b


def calc_pv_at_intervals(changes, interval_minutes=10):
    replay = OrderBookReplay()
    replay.changes = changes
    return replay.calc_pv_at_intervals(interval_minutes)


def print_usage():
    print("""
Order Book Replay and Fixed Income Calculator

Usage:
  python sprint7.py [path.csv] [options]

Options:
  --instrument NAME    Instrument to track (default: 2_YEAR)
  --depth N            Number of book levels to display (default: 12)
  --interval-minutes N Calculate PV every N minutes
  --bench [N]          Benchmark mode (default: 5000 changes)
  --help               Show this message
""")


def main():
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print_usage()
        sys.exit(0)
    
    path = None
    instrument = None
    depth = 12
    
    for arg in args:
        if not arg.startswith("--"):
            path = arg
            break
    
    if "--instrument" in args:
        idx = args.index("--instrument")
        if idx + 1 < len(args):
            instrument = args[idx + 1]
    
    if "--depth" in args:
        idx = args.index("--depth")
        if idx + 1 < len(args):
            depth = int(args[idx + 1])
    
    if "--bench" in args:
        idx = args.index("--bench")
        n = 5000
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            n = int(args[idx + 1])
        
        replay = OrderBookReplay(path=path, instrument=instrument)
        try:
            replay.load()
            replay.benchmark(n)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        sys.exit(0)
    
    if "--interval-minutes" in args:
        idx = args.index("--interval-minutes")
        if idx + 1 < len(args):
            interval = int(args[idx + 1])
            
            replay = OrderBookReplay(path=path, instrument=instrument)
            try:
                replay.load()
                results = replay.calc_pv_at_intervals(interval)
                for r in results:
                    print(f"{r['ts']} mid={r['mid']:.4f} ytm={r['ytm']:.6f} pv={r['pv']:.4f}")
            except FileNotFoundError as e:
                print(f"Error: {e}")
                sys.exit(1)
            sys.exit(0)
    
    replay = OrderBookReplay(path=path, instrument=instrument, depth=depth)
    try:
        replay.load()
        replay.run_terminal_ui()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()