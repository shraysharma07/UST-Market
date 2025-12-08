# Sprint 6 – Testing and Measuring Market Book at Time t

This sprint adds unit testing and performance measurement to the order book reconstruction logic built in Sprints 4 and 5. The purpose is to ensure that `print_order_book_at(t)` produces the correct order book snapshot and executes within an acceptable performance window.

## Overview

- Uses the merged dataset `2_20180108_merged.csv`
- Calls `print_order_book_at(t)` to print the buy and sell books at a timestamp
- Adds tests to validate:
  - Correct return type
  - Required keys ("best_bid", "best_ask")
  - Stable, reproducible execution
- Measures execution time using `time.perf_counter()`
- Ensures the function completes in under 0.5 seconds

## Unit Tests Implemented

### test_returns_dict
Checks that the function returns a dictionary.

### test_keys_exist
Ensures the output includes "best_bid" and "best_ask".

### test_performance
Measures runtime and asserts that execution stays under 0.5 seconds.

## Example Test Output
=== ORDER BOOK @ 02:01:19 ===

BEST BIDS
Sequence Premium (256ths) Quantity
1 25552 5
2 25550 5
3 25548 5
4 25546 5
5 25544 5

BEST ASKS
(no asks available at this timestamp)

Elapsed: 0.0062s
