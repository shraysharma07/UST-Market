# Order Book Replay (Sprint 7–10)

This project implements a replayable exchange-style order book using **OB_CHANGE** messages from U.S. Treasury market data. The program reads a CSV file, filters by a single instrument (default: `2_YEAR`), and applies order-book updates sequentially, allowing the user to move forward and backward through time.

The project is structured as incremental sprints. Sprint 7 establishes the replay engine and UI, while Sprint 8 focuses on correctness, validation, and testability.

---

## Sprint 7 – Order Book Replay Engine

### What Sprint 7 Does
- Loads a CSV containing order book change messages
- Filters rows where:
  - `Record Type == OB_CHANGE`
  - `Instrument == selected instrument`
- Sorts events by `Sequence`
- Maintains a Market-By-Order order book with two sides:
  - Bids (`B`)
  - Asks (`A`)
- Applies updates using `Ob Position` as the exchange rank:
  - `ADD` inserts an order at the given position and shifts lower-ranked orders
  - `DELETE` reduces quantity or removes the order entirely
  - `ALTER` removes an existing order and reinserts it at the new position
- Provides an interactive terminal UI (ncurses):
  - ↑ step forward one event
  - ↓ step backward one event (implemented by rebuilding the book for correctness)
  - Esc quits
- Displays the top levels of the bid and ask book side-by-side
- Includes a benchmark mode to time rebuilding the book

Sprint 7 prioritizes correctness and clarity over performance, especially for backward navigation.

---

## Sprint 8 – Correctness and Validation

Sprint 8 focuses on verifying that the replay logic behaves correctly across common and edge cases.

### What Sprint 8 Adds
- Refactors core order book logic into a standalone `Book` module
- Introduces unit tests to validate book behavior
- Removes unsafe fallback behavior when DELETE references a missing order
- Makes order identity strictly dependent on `Order Number`
- Preserves the Market-By-Order model and Sprint 7 UI without changes

### Unit Tests
Sprint 8 adds deterministic unit tests using small synthetic change sequences rather than full CSV files. This allows correctness to be tested independently of input size or data quality.

## Questions and Clarifications

The following questions identify specification ambiguities that materially affect correctness rather than implementation style. Different answers to these questions lead to meaningfully different order book behavior.

### Core Ordering Semantics
- Is the expected behavior to recompute price–time priority from price and arrival information, or to treat `Ob Position` as the authoritative exchange rank and replay it directly?
- When multiple orders share the same price level, which field should define time priority (`Sequence` or `Timestamp`)?

### Order Identity and DELETE Behavior
- Should DELETE events always be matched strictly by `Order Number`?
- If a DELETE references a missing or unknown order ID, should the update be ignored, raise an error, or attempt recovery?

### ALTER Semantics
- Does an ALTER operation reset an order’s time priority, or should the original arrival ordering be preserved when position or quantity changes?


#### Covered Cases
- `ADD` correctly inserts orders and shifts existing ones
- Partial `DELETE` reduces quantity without removing the order
- Full `DELETE` removes the order entirely
- `ALTER` repositions an order correctly within the book

Run tests with:
```bash
pytest test_book.py
