import pandas as pd
import sys

# use the merged file from sprint2
CSV_PATH = "/Users/shray/UST_Market/sprint2/2_20180108_merged.csv"

# load data once
df = pd.read_csv(CSV_PATH)

# only care about OB_CHANGE messages for the 2_YEAR instrument
ob_df = df[(df["Record Type"] == "OB_CHANGE") & (df["Instrument"] == "2_YEAR")].copy()

# sort so the stream is in real-time order
if "Sequence" in ob_df.columns:
    ob_df = ob_df.sort_values("Sequence").reset_index(drop=True)
else:
    ob_df = ob_df.sort_values("Timestamp").reset_index(drop=True)

# pull out the date chunk so we don't hardcode it
# e.g. "02:01:19:825375 20180108" -> "20180108"
first_ts = ob_df["Timestamp"].iloc[0]
_, date_suffix = first_ts.split()


def print_order_book_at(t, data=ob_df):
    # t is just the time piece, like "02:01:23:187164"
    full_ts = f"{t} {date_suffix}"

    # everything up to and including that timestamp
    sub = data[data["Timestamp"] <= full_ts]

    if sub.empty:
        print(f"No order book data up to {full_ts}")
        return

    bids = {}  # pos -> (price, qty)
    asks = {}

    for _, row in sub.iterrows():
        side = row["Bid/Ask"]
        pos = int(row["Ob Position"])
        cmd = row["Ob Command"]
        price = int(row["Premium (256ths)"])
        qty = int(row["Quantity"])

        book = bids if side == "B" else asks

        if cmd == "DELETE":
            book.pop(pos, None)
        else:
            book[pos] = (price, qty)

    # keep levels in book-position order (1 = top of book)
    bid_positions = sorted(bids.keys())
    ask_positions = sorted(asks.keys())

    print(f"print_order_book_at(t={t}):")
    print("Buy\tSell")

    max_rows = max(len(bid_positions), len(ask_positions))

    for i in range(max_rows):
        if i < len(bid_positions):
            b_price, b_qty = bids[bid_positions[i]]
            b_str = f"{b_qty}@{b_price}"
        else:
            b_str = ""

        if i < len(ask_positions):
            a_price, a_qty = asks[ask_positions[i]]
            a_str = f"{a_qty}@{a_price}"
        else:
            a_str = ""

        print(f"{b_str}\t{a_str}")


def main():
    # if user passes a time on the command line, just run once and exit
    # example:
    #   python market@time.py 02:01:23:187164
    if len(sys.argv) > 1:
        t = sys.argv[1]
        print_order_book_at(t)
        return

    # otherwise, run an interactive loop
    print("Order Book @ Time (2_YEAR)")
    print("Type a timestamp like 02:01:23:187164 (or 'q' to quit).")

    while True:
        t = input("t = ").strip()
        if t.lower() in {"q", "quit", "exit"}:
            break
        if not t:
            continue
        print_order_book_at(t)
        print()  # blank line between queries


if __name__ == "__main__":
    main()
