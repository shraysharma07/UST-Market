# sprint7.py

import csv
import curses
import os
import sys
import time

try:
    from .book import Book
except ImportError:
    from book import Book

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


def find_default_csv():
    paths = [
        os.environ.get("CSV_PATH"),
        "2_20180108_merged.csv",
        os.path.join("sprint2", "2_20180108_merged.csv"),
        os.path.join("..", "sprint2", "2_20180108_merged.csv"),
    ]
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def load_changes(path, instrument=None):
    if instrument is None:
        instrument = "2_YEAR"
    with open(path, "r", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise ValueError("missing header")

        critical = [COL_RT, COL_INST, COL_POS, COL_QDIFF, COL_CMD, COL_ID, COL_PX, COL_SIDE, COL_SEQ]
        missing = [c for c in critical if c not in r.fieldnames]
        if missing:
            raise ValueError("missing critical columns: " + ", ".join(missing))

        out = []
        for row in r:
            if row[COL_RT] != "OB_CHANGE":
                continue
            if row[COL_INST] != instrument:
                continue

            pos_raw = (row.get(COL_POS) or "").strip()
            if pos_raw == "":
                continue

            out.append(
                {
                    "ts": row.get(COL_TS, ""),
                    "pos": int(float(pos_raw)),
                    "qdiff": int(float(row[COL_QDIFF])),
                    "cmd": row[COL_CMD].strip().upper(),
                    "oid": row[COL_ID],
                    "px": int(float(row[COL_PX])),
                    "side": row[COL_SIDE].strip().upper(),
                    "seq": int(float(row[COL_SEQ])),
                }
            )

        out.sort(key=lambda x: x["seq"])
        return out


def build_book(changes, upto):
    b = Book()
    for i in range(upto):
        b.apply(changes[i])
    return b


def draw(stdscr, changes, idx, instrument, depth):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    header = f"OB replay ({instrument})  idx={idx}/{len(changes)}   ↑ next  ↓ prev  ESC quit"
    stdscr.addstr(0, 0, header[: w - 1])

    b = build_book(changes, idx)
    bids = b.bids[:depth]
    asks = b.asks[:depth]

    stdscr.addstr(2, 0, "BID (Buy)                         | ASK (Sell)")
    stdscr.addstr(3, 0, "pos  qty   px     id tail         | pos  px     qty   id tail")
    stdscr.addstr(4, 0, "-" * min(w - 1, 80))

    for i in range(depth):
        left = " " * 32
        right = ""

        if i < len(bids):
            o = bids[i]
            left = f"{i+1:<4}{o['qty']:<6}{o['px']:<7}{o['oid'][-8:]:<10}"

        if i < len(asks):
            o = asks[i]
            right = f"{i+1:<4}{o['px']:<7}{o['qty']:<6}{o['oid'][-8:]:<10}"

        stdscr.addstr(5 + i, 0, f"{left:<32}| {right}"[: w - 1])

    if idx > 0:
        c = changes[idx - 1]
        footer = (
            f"last: seq={c['seq']} ts={c['ts']} cmd={c['cmd']} side={c['side']} "
            f"pos={c['pos']} px={c['px']} qdiff={c['qdiff']} id={c['oid']}"
        )
        stdscr.addstr(min(h - 1, 5 + depth + 2), 0, footer[: w - 1])

    stdscr.refresh()


def run_ui(path=None, instrument=None, depth=12):
    if path is None:
        path = find_default_csv()
    if instrument is None:
        instrument = "2_YEAR"
    changes = load_changes(path, instrument)

    def _main(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)

        idx = 0
        while True:
            draw(stdscr, changes, idx, instrument, depth)
            k = stdscr.getch()

            if k == 27:
                return
            if k == curses.KEY_UP:
                if idx < len(changes):
                    idx += 1
            elif k == curses.KEY_DOWN:
                if idx > 0:
                    idx -= 1

    curses.wrapper(_main)


def bench(path=None, instrument=None, n=5000):
    if path is None:
        path = find_default_csv()
    if instrument is None:
        instrument = "2_YEAR"
    changes = load_changes(path, instrument)
    upto = min(n, len(changes))
    t0 = time.perf_counter()
    _ = build_book(changes, upto)
    t1 = time.perf_counter()
    print(f"rebuild upto={upto} took {(t1 - t0):.4f}s")


def usage():
    print("usage:")
    print("  python sprint7.py path.csv [--instrument 2_YEAR] [--depth 12]")
    print("  python sprint7.py --bench path.csv [N] [--instrument 2_YEAR]")


def pv_cash_flows(years=2, coupon_rate=0.04, face=100, freq=2):
    periods = int(years * freq)
    coupon = (coupon_rate / freq) * face
    flows = [coupon] * periods
    flows[-1] += face
    return flows


def present_value(cash_flows, ytm, freq=2):
    period_rate = ytm / freq
    pv = 0.0
    for i, cf in enumerate(cash_flows):
        pv += cf / ((1.0 + period_rate) ** (i + 1))
    return pv


def price_from_ytm(ytm, years=2, coupon_rate=0.04, face=100, freq=2):
    flows = pv_cash_flows(years, coupon_rate, face, freq)
    return present_value(flows, ytm, freq)


def solve_ytm(market_price, years=2, coupon_rate=0.04, face=100, freq=2):
    low, high = -0.5, 1.0
    while high - low > 1e-10:
        mid = (low + high) / 2
        price = price_from_ytm(mid, years, coupon_rate, face, freq)
        diff = price - market_price
        if abs(diff) < 1e-8:
            return mid
        if diff > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def premium_to_price(premium_256ths):
    return premium_256ths / 256.0


def calc_pv_at_intervals(changes, interval_minutes=10):
    results = []
    b = Book()
    last_time = None

    for idx, ch in enumerate(changes):
        b.apply(ch)
        ts_str = ch.get("ts", "")
        if not ts_str:
            continue

        try:
            ts_clean = ts_str.split(".")[0].strip()
            if "T" in ts_clean:
                ts_clean = ts_clean.replace("T", " ")
            time_tuple = time.strptime(ts_clean, "%Y-%m-%d %H:%M:%S")
            current_time = time.mktime(time_tuple)
        except:
            continue

        if last_time is None:
            last_time = current_time

        elapsed_minutes = (current_time - last_time) / 60.0
        if elapsed_minutes >= interval_minutes:
            best_bid, best_ask = b.best_bid_ask()
            mid = None
            if best_bid is not None and best_ask is not None:
                mid = (premium_to_price(best_bid) + premium_to_price(best_ask)) / 2.0
            elif best_bid is not None:
                mid = premium_to_price(best_bid)
            elif best_ask is not None:
                mid = premium_to_price(best_ask)

            if mid is not None:
                ytm = solve_ytm(mid)
                flows = pv_cash_flows()
                pv = present_value(flows, ytm)
                results.append({"ts": ts_str, "mid": mid, "ytm": ytm, "pv": pv})
            last_time = current_time

    return results


if __name__ == "__main__":
    instrument = None
    depth = 12
    path = None

    if "--bench" in sys.argv:
        arg_idx = sys.argv.index("--bench")
        if arg_idx + 1 < len(sys.argv) and not sys.argv[arg_idx + 1].startswith("--"):
            path = sys.argv[arg_idx + 1]
        if path is None:
            path = find_default_csv()
        if path is None:
            usage()
            sys.exit(1)

        n = 5000
        if arg_idx + 2 < len(sys.argv) and sys.argv[arg_idx + 2].isdigit():
            n = int(sys.argv[arg_idx + 2])

        if "--instrument" in sys.argv:
            i = sys.argv.index("--instrument")
            if i + 1 < len(sys.argv):
                instrument = sys.argv[i + 1]

        bench(path, instrument, n)
        sys.exit(0)

    if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        path = sys.argv[1]

    if path is None:
        path = find_default_csv()

    if "--instrument" in sys.argv:
        i = sys.argv.index("--instrument")
        if i + 1 < len(sys.argv):
            instrument = sys.argv[i + 1]

    if "--depth" in sys.argv:
        i = sys.argv.index("--depth")
        if i + 1 < len(sys.argv):
            depth = int(sys.argv[i + 1])

    if "--interval-minutes" in sys.argv:
        i = sys.argv.index("--interval-minutes")
        if i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 1])
            changes = load_changes(path, instrument)
            results = calc_pv_at_intervals(changes, interval)
            for r in results:
                print(f"{r['ts']} mid={r['mid']:.4f} ytm={r['ytm']:.6f} pv={r['pv']:.4f}")
            sys.exit(0)

    if path is None:
        usage()
        sys.exit(1)

    run_ui(path, instrument, depth)
