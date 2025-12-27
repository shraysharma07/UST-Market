# sprint7.py

import csv
import curses
import sys
import time

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


def load_changes(path, instrument):
    with open(path, "r", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise ValueError("missing header")

        need = [COL_TS, COL_RT, COL_INST, COL_POS, COL_QDIFF, COL_CMD, COL_ID, COL_PX, COL_SIDE, COL_SEQ]
        missing = [c for c in need if c not in r.fieldnames]
        if missing:
            raise ValueError("missing columns: " + ", ".join(missing))

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
                    "ts": row[COL_TS],
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


def run_ui(path, instrument, depth):
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


def bench(path, instrument, n):
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    instrument = "2_YEAR"
    depth = 12

    if sys.argv[1] == "--bench":
        if len(sys.argv) < 3:
            usage()
            sys.exit(1)

        path = sys.argv[2]
        n = 5000
        if len(sys.argv) >= 4 and sys.argv[3].isdigit():
            n = int(sys.argv[3])

        if "--instrument" in sys.argv:
            i = sys.argv.index("--instrument")
            instrument = sys.argv[i + 1]

        bench(path, instrument, n)
        sys.exit(0)

    path = sys.argv[1]

    if "--instrument" in sys.argv:
        i = sys.argv.index("--instrument")
        instrument = sys.argv[i + 1]

    if "--depth" in sys.argv:
        i = sys.argv.index("--depth")
        depth = int(sys.argv[i + 1])

    run_ui(path, instrument, depth)
