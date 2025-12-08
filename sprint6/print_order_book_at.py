import pandas as pd

# loads the merged sprint4+5 file (adjust if needed)
DATA_PATH = "/Users/shray/UST_Market/sprint2/2_20180108_merged.csv"

df = pd.read_csv(DATA_PATH)

def print_order_book_at(t: str):
    """
    prints the order book at time t (HH:MM:SS format)
    """
    # filter by exact timestamp prefix
    snap = df[df["Timestamp"].str.startswith(t)]

    if snap.empty:
        print(f"No data for {t}")
        return None

    # best bid = highest premium among B
    bids = snap[snap["Bid/Ask"] == "B"].sort_values("Premium (256ths)", ascending=False)

    # best ask = lowest premium among A
    asks = snap[snap["Bid/Ask"] == "A"].sort_values("Premium (256ths)", ascending=True)

    book = {
        "best_bid": bids.head(10),   # top 10 rows (or fewer)
        "best_ask": asks.head(10)
    }

    print("\n=== ORDER BOOK @", t, "===\n")
    print("BEST BIDS")
    print(book["best_bid"][["Sequence", "Premium (256ths)", "Quantity"]])

    print("\nBEST ASKS")
    print(book["best_ask"][["Sequence", "Premium (256ths)", "Quantity"]])

    return book
