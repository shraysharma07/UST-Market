python market@time.py

# Sprint 4 & 5 – Market Book at Time t

This sprint rebuilds the **exchange-side order book** for the `2_YEAR` instrument at any given timestamp using `2_20180108_merged.csv`.

### How It Works
- Reads the merged market data file from Sprint 2.
- Filters to:
  - `Record Type = OB_CHANGE`
  - `Instrument = 2_YEAR`
- Processes messages in time/sequence order and:
  - Uses **Ob Position** to rank book levels
  - Applies **ADD** to insert/update levels
  - Applies **DELETE** to remove levels
- Builds separate **Buy** and **Sell** books and prints them at time **t**.

### Example Output
```text
python market@time.py 02:01:23:187164

print_order_book_at(t=02:01:23:187164):
Buy            Sell
5@25552        5@25562
5@25550        5@25564
5@25548        5@25566
5@25546        5@25568
5@25544
