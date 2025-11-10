import pandas as pd

# load the file (I'm assuming we are running in sprint3)
df = pd.read_csv("../files/OC_2_20180108.csv")

# only care about order book changes
df = df[df["Record Type"] == "OB_CHANGE"].copy()

# make sure these are numbers
for col in ["Sequence", "Quantity Diff", "Premium (256ths)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Sequence", "Quantity Diff", "Premium (256ths)"])
df = df[df["Bid/Ask"].isin(["B","A"])]  # focus on valid sides
df = df.sort_values("Sequence").reset_index(drop=True)  # keep event order clean

# signed qty logic (B = buy pressure, A = sell pressure, DELETE flips it)
def signed_qty(row):
    q = row["Quantity Diff"]
    side = row["Bid/Ask"]
    cmd = row["Ob Command"]
    q_signed = q if side == "B" else -q
    if cmd == "DELETE":  # removing that side = opposite effect
        q_signed = -q_signed
    return q_signed

df["qty_signed"] = df.apply(signed_qty, axis=1)
df["Qty"] = df["qty_signed"].abs().astype("Int64")
df["Action"] = df["qty_signed"].apply(lambda x: f"+{abs(int(x))}" if x > 0 else f"-{abs(int(x))}")

# convert price from 256ths (govies life)
df["Price"] = df["Premium (256ths)"] / 256.0

# real impact = qty * price
df["PositionTaken"] = df["qty_signed"] * df["Price"]

# running total = liquidity signal
df["Liquidity"] = df["PositionTaken"].cumsum()

# label direction based on liquidity movement
prev = df["Liquidity"].shift(1)
df["Direction"] = [
    "Up" if cur > prv else ("Down" if cur < prv else "Sideways")
    for cur, prv in zip(df["Liquidity"], prev)
]

# final output
out = df[["Sequence", "Action", "Qty", "Price", "Liquidity", "Direction"]]
out.to_csv("Position_2_20180108.csv", index=False)

print("CSV created:", len(out), "rows")
