# Order Book Replay and Fixed Income Calculator

This project replays historical order book data and calculates present values for Treasury bonds.

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Order Book Module](#order-book-module)
- [Fixed Income Calculator](#fixed-income-calculator)
- [Usage](#usage)
- [Testing](#testing)

## Project Structure
```
project/
├── README.md
├── sprint7.py
├── orderbook/
│   ├── __init__.py
│   └── book.py
├── test_book.py
└── test_pv.py
```

| File | Description |
|------|-------------|
| sprint7.py | Main module with replay and calculator classes |
| orderbook/book.py | Book class for order book state |
| orderbook/__init__.py | Package exports |
| test_book.py | Tests for the Book class |
| test_pv.py | Tests for present value calculations |

## Installation

Python 3.7 or newer is required. No external packages are needed.

On Windows, install windows-curses for the terminal UI:
```bash
pip install windows-curses
```

## Order Book Module

The Book class maintains order book state. It has two lists: bids (buy orders) and asks (sell orders). The class processes ADD, ALTER, and DELETE events.
```python
from orderbook import Book

book = Book()
book.apply({
    "cmd": "ADD",
    "side": "B",
    "pos": 1,
    "oid": "order1",
    "px": 25600,
    "qdiff": 100,
    "seq": 1,
    "ts": ""
})

bid, ask = book.best_bid_ask()
```

## Fixed Income Calculator

The FixedIncomeCalculator class handles bond math. It calculates prices from yields, solves for yields from prices, and computes present values.

A bond pays coupon payments plus face value at maturity. Present value is what those future payments are worth today, discounted by the yield. Price and yield move in opposite directions.
```python
from sprint7 import FixedIncomeCalculator

calc = FixedIncomeCalculator(years=2, coupon_rate=0.04, face=100, freq=2)

# Get cash flows
flows = calc.cash_flows()  # [2.0, 2.0, 2.0, 102.0]

# Price from yield
price = calc.price_from_ytm(0.045)  # ~99.14

# Yield from price
ytm = calc.solve_ytm(99.14)  # ~0.045
```

## Usage

### Terminal UI

Step through order book history:
```bash
python sprint7.py 2_20180108_merged.csv
```

Controls:
- UP arrow: step forward
- DOWN arrow: step backward
- ESC: exit

### Calculate PV at Intervals
```bash
python sprint7.py 2_20180108_merged.csv --interval-minutes 10
```

### Benchmark
```bash
python sprint7.py --bench 10000
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| --instrument NAME | Instrument to track | 2_YEAR |
| --depth N | Book levels to display | 12 |
| --interval-minutes N | PV calculation interval | - |
| --bench N | Benchmark N changes | 5000 |

## Testing

Run the tests:
```bash
python test_book.py
python test_pv.py
```

All tests should pass.

## Author

Shray Sharma
