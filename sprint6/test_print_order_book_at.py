import unittest
import time
from print_order_book_at import print_order_book_at

class TestOrderBookAt(unittest.TestCase):

    def test_returns_dict(self):
        # picks a time that should exist in the dataset
        result = print_order_book_at("02:01:19")
        self.assertIsInstance(result, dict)

    def test_keys_exist(self):
        result = print_order_book_at("02:01:19")
        self.assertIn("best_bid", result)
        self.assertIn("best_ask", result)

    def test_performance(self):
        start = time.perf_counter()
        _ = print_order_book_at("02:01:19")
        elapsed = time.perf_counter() - start

        # my benchmark expectations
        self.assertLess(elapsed, 0.50)  # must run under 0.5s
        print(f"\nElapsed: {elapsed:.6f}s")

if __name__ == "__main__":
    unittest.main()
