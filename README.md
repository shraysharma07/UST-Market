# Order Book Replay (Sprint 7–10)

This project implements a replayable exchange-style order book using **OB_CHANGE** messages from U.S. Treasury market data.  The program reads a CSV file, filters by a single instrument (default: `2_YEAR`), and applies order-book updates sequentially, allowing the user to move forward and backward through time.

The focus of this project is correctness and transparency: each order book change can be inspected, replayed, and reasoned about.

---

## What this does (current implementation)

- Loads a CSV containing order book change messages
- Filters rows where:
  - `Record Type == OB_CHANGE`
  - `Instrument == selected instrument`
- Sorts events by `Sequence`
- Maintains a **Market-By-Order** order book with two sides:
  - Bids (`B`)
  - Asks (`A`)
- Applies updates using `Ob Position`:
  - **ADD** inserts an order at the given rank and shifts lower-ranked orders down
  - **DELETE** reduces quantity or removes the order entirely, shifting orders up
  - **ALTER** updates an existing order by removing and reinserting it at the new position
- Provides an interactive terminal UI (ncurses):
  - **↑** step forward one event
  - **↓** step backward one event (implemented by rebuilding the book for correctness)
  - **Esc** quit
- Displays the top levels of the bid and ask book side by side
- Includes a simple benchmark mode to time rebuilding the book

Backward navigation is implemented by rebuilding the order book up to the selected index. This approach is slower than maintaining an undo stack, but it guarantees correctness and keeps the logic simple.

### What’s next (planned)
- Replace rebuild-from-start backward navigation with an undo stack (faster ↓ stepping)
- Add unit tests for ADD shifting, partial/full DELETE, and edge cases (missing IDs / position mismatches)
- Add basic input validation + clearer error messages for malformed rows
- Run timing comparisons (rebuild vs undo) and summarize results in the writeup/README
- Optional later: port the same replay model to a React UI (book derived from `(rows, index)`)

---

## How to run
```bash
python sprint7.py /Users/shray/UST_Market/sprint2/2_20180108_merged.csv

