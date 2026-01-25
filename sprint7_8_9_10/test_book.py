"""
Test Suite for the Order Book Module
====================================

This module contains unit tests for the Book class, verifying that
order book operations work correctly.

Tests cover:
- Adding orders and position shifts
- Partial and full deletions
- Order alterations and repositioning

Run with: python -m pytest test_book.py -v
Or simply: python test_book.py
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orderbook import Book


def create_change(cmd, side, pos, oid, px=100, qty=5, seq=1):
    """
    Helper function to create order book change events for testing.
    
    Parameters
    ----------
    cmd : str
        Command type: 'ADD', 'ALTER', or 'DELETE'
    side : str
        Side of book: 'B' (bid) or 'A' (ask)
    pos : int
        Position in book (1-indexed)
    oid : str
        Order ID
    px : int, optional
        Price in 256ths (default: 100)
    qty : int, optional
        Quantity (default: 5)
    seq : int, optional
        Sequence number (default: 1)
    
    Returns
    -------
    dict
        A properly formatted change event
    """
    return {
        "cmd": cmd,
        "side": side,
        "pos": pos,
        "oid": oid,
        "px": px,
        "qdiff": qty,
        "seq": seq,
        "ts": "",
    }


def test_add_shifts_existing_orders():
    """
    Test that adding an order at position 1 shifts existing orders down.
    
    Scenario:
    1. Add order A at position 1 → Book: [A]
    2. Add order B at position 1 → Book: [B, A]
    
    The new order should be at the top, pushing A down.
    """
    book = Book()
    
    # Add first order
    book.apply(create_change("ADD", "B", 1, "A", seq=1))
    
    # Add second order at position 1 (top)
    book.apply(create_change("ADD", "B", 1, "B", seq=2))
    
    # Verify order: B should be first, A second
    bids, _ = book.snapshot()
    order_ids = [order[0] for order in bids]
    
    assert order_ids == ["B", "A"], f"Expected ['B', 'A'], got {order_ids}"
    print("✓ test_add_shifts_existing_orders passed")


def test_delete_partial():
    """
    Test partial deletion reduces quantity but keeps order in book.
    
    Scenario:
    1. Add order X with quantity 10
    2. Delete 4 from order X
    3. Order X should remain with quantity 6
    """
    book = Book()
    
    # Add order with quantity 10
    book.apply(create_change("ADD", "A", 1, "X", qty=10))
    
    # Partial delete: remove 4
    book.apply(create_change("DELETE", "A", 1, "X", qty=4))
    
    # Verify order still exists with reduced quantity
    _, asks = book.snapshot()
    assert len(asks) == 1, "Order should still exist"
    assert asks[0][2] == 6, f"Expected quantity 6, got {asks[0][2]}"
    print("✓ test_delete_partial passed")


def test_delete_full():
    """
    Test that deleting full quantity removes order from book.
    
    Scenario:
    1. Add order X with quantity 5
    2. Delete 5 from order X
    3. Order X should be completely removed
    """
    book = Book()
    
    # Add order with quantity 5
    book.apply(create_change("ADD", "A", 1, "X", qty=5))
    
    # Full delete
    book.apply(create_change("DELETE", "A", 1, "X", qty=5))
    
    # Verify order is gone
    _, asks = book.snapshot()
    assert asks == [], f"Expected empty asks, got {asks}"
    print("✓ test_delete_full passed")


def test_alter_repositions_order():
    """
    Test that ALTER moves an order to a new position.
    
    Scenario:
    1. Add order A at position 1 → Book: [A]
    2. Add order B at position 2 → Book: [A, B]
    3. Alter order A to position 2 → Book: [B, A]
    
    The ALTER should move A from position 1 to position 2.
    """
    book = Book()
    
    # Add two orders
    book.apply(create_change("ADD", "B", 1, "A"))
    book.apply(create_change("ADD", "B", 2, "B"))
    
    # Verify initial order
    bids, _ = book.snapshot()
    assert [o[0] for o in bids] == ["A", "B"], "Initial order should be [A, B]"
    
    # Alter A to position 2
    book.apply(create_change("ALTER", "B", 2, "A"))
    
    # Verify new order: B should be first, A second
    bids, _ = book.snapshot()
    order_ids = [order[0] for order in bids]
    
    assert order_ids == ["B", "A"], f"Expected ['B', 'A'], got {order_ids}"
    print("✓ test_alter_repositions_order passed")


def test_best_bid_ask():
    """
    Test that best_bid_ask returns correct top-of-book prices.
    """
    book = Book()
    
    # Initially empty
    bid, ask = book.best_bid_ask()
    assert bid is None and ask is None, "Empty book should return (None, None)"
    
    # Add a bid
    book.apply(create_change("ADD", "B", 1, "bid1", px=9950))
    bid, ask = book.best_bid_ask()
    assert bid == 9950, f"Expected bid 9950, got {bid}"
    assert ask is None, "Ask should still be None"
    
    # Add an ask
    book.apply(create_change("ADD", "A", 1, "ask1", px=9975))
    bid, ask = book.best_bid_ask()
    assert bid == 9950, f"Expected bid 9950, got {bid}"
    assert ask == 9975, f"Expected ask 9975, got {ask}"
    
    print("✓ test_best_bid_ask passed")


def test_multiple_orders_same_side():
    """
    Test adding multiple orders to the same side at different positions.
    """
    book = Book()
    
    # Add three bids at different positions
    book.apply(create_change("ADD", "B", 1, "order1", px=100, seq=1))
    book.apply(create_change("ADD", "B", 2, "order2", px=99, seq=2))
    book.apply(create_change("ADD", "B", 3, "order3", px=98, seq=3))
    
    bids, _ = book.snapshot()
    assert len(bids) == 3, f"Expected 3 bids, got {len(bids)}"
    
    # Verify order
    prices = [o[1] for o in bids]
    assert prices == [100, 99, 98], f"Expected [100, 99, 98], got {prices}"
    
    print("✓ test_multiple_orders_same_side passed")


def run_all_tests():
    """Run all tests and report results."""
    print("\nRunning Order Book Tests")
    print("=" * 40)
    
    tests = [
        test_add_shifts_existing_orders,
        test_delete_partial,
        test_delete_full,
        test_alter_repositions_order,
        test_best_bid_ask,
        test_multiple_orders_same_side,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("=" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)