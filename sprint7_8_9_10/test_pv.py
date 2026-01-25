"""
Test Suite for Fixed Income / Present Value Calculations
=========================================================

This module contains unit tests for the fixed income calculation functions,
verifying that bond pricing and yield calculations work correctly.

Tests cover:
- Cash flow generation
- Present value calculation
- Price from YTM
- YTM solving (numerical root finding)

The tests use a standard 2-year Treasury note as the reference instrument:
- Face value: $100
- Coupon rate: 4% annual (2% semiannual)
- Payment frequency: Semiannual (2 times per year)
- Periods: 4 (2 years × 2 payments/year)

Run with: python -m pytest test_pv.py -v
Or simply: python test_pv.py
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import both class-based and legacy function interfaces
from sprint7 import (
    FixedIncomeCalculator,
    pv_cash_flows,
    present_value,
    price_from_ytm,
    solve_ytm,
    premium_to_price
)


def test_cash_flows_basic():
    """
    Test that cash flow generation produces correct payment schedule.
    
    For a 2-year bond with 4% coupon, semiannual payments:
    - 4 periods (2 years × 2 payments/year)
    - Coupon = $2 per period (4% / 2 × $100)
    - Final payment = $102 (coupon + principal)
    
    Expected cash flows: [2.0, 2.0, 2.0, 102.0]
    """
    # Test using legacy function
    flows = pv_cash_flows(years=2, coupon_rate=0.04, face=100, freq=2)
    
    assert len(flows) == 4, f"Expected 4 cash flows, got {len(flows)}"
    assert flows[0] == 2.0, f"First coupon should be 2.0, got {flows[0]}"
    assert flows[1] == 2.0, f"Second coupon should be 2.0, got {flows[1]}"
    assert flows[2] == 2.0, f"Third coupon should be 2.0, got {flows[2]}"
    assert flows[3] == 102.0, f"Final payment should be 102.0, got {flows[3]}"
    
    print("✓ test_cash_flows_basic passed (legacy function)")
    
    # Test using class-based interface
    calc = FixedIncomeCalculator(years=2, coupon_rate=0.04, face=100, freq=2)
    flows_class = calc.cash_flows()
    
    assert flows_class == flows, "Class method should match legacy function"
    print("✓ test_cash_flows_basic passed (class method)")


def test_cash_flows_different_parameters():
    """
    Test cash flow generation with different bond parameters.
    
    For a 5-year bond with 6% coupon:
    - 10 periods (5 years × 2 payments/year)
    - Coupon = $3 per period (6% / 2 × $100)
    """
    calc = FixedIncomeCalculator(years=5, coupon_rate=0.06, face=100, freq=2)
    flows = calc.cash_flows()
    
    assert len(flows) == 10, f"Expected 10 periods, got {len(flows)}"
    assert all(f == 3.0 for f in flows[:-1]), "All coupons except last should be 3.0"
    assert flows[-1] == 103.0, f"Final payment should be 103.0, got {flows[-1]}"
    
    print("✓ test_cash_flows_different_parameters passed")


def test_price_at_par():
    """
    Test that when YTM equals coupon rate, price equals par (face value).
    
    This is a fundamental relationship in bond pricing:
    - If yield = coupon rate, investors get exactly what they require
    - Therefore, they're willing to pay exactly face value
    
    With 4% coupon and 4% yield, price should be $100.
    """
    ytm = 0.04  # 4% yield = 4% coupon
    
    # Test legacy function
    price = price_from_ytm(ytm)
    assert abs(price - 100.0) < 0.01, f"Expected ~100.0, got {price}"
    print("✓ test_price_at_par passed (legacy function)")
    
    # Test class method
    calc = FixedIncomeCalculator(coupon_rate=0.04)
    price_class = calc.price_from_ytm(0.04)
    assert abs(price_class - 100.0) < 0.01, f"Expected ~100.0, got {price_class}"
    print("✓ test_price_at_par passed (class method)")


def test_price_yield_inverse_relationship():
    """
    Test the inverse relationship between price and yield.
    
    When yield goes UP, price goes DOWN (and vice versa).
    This is because higher yields mean future cash flows are
    discounted more heavily, reducing their present value.
    """
    calc = FixedIncomeCalculator(coupon_rate=0.04)
    
    price_low_yield = calc.price_from_ytm(0.03)   # 3% yield
    price_mid_yield = calc.price_from_ytm(0.04)   # 4% yield (at par)
    price_high_yield = calc.price_from_ytm(0.05)  # 5% yield
    
    # Higher yield should mean lower price
    assert price_low_yield > price_mid_yield > price_high_yield, \
        f"Prices should decrease as yield increases: {price_low_yield} > {price_mid_yield} > {price_high_yield}"
    
    # Verify at-par relationship
    assert abs(price_mid_yield - 100.0) < 0.01, "At coupon rate, price should be par"
    
    print(f"  Prices: {price_low_yield:.2f} (3%) > {price_mid_yield:.2f} (4%) > {price_high_yield:.2f} (5%)")
    print("✓ test_price_yield_inverse_relationship passed")


def test_solve_ytm_at_par():
    """
    Test YTM solver when price is at par.
    
    If price = $100 and coupon = 4%, the solver should find YTM = 4%.
    """
    market_price = 100.0
    
    # Test legacy function
    ytm = solve_ytm(market_price)
    assert abs(ytm - 0.04) < 0.001, f"Expected YTM ~0.04, got {ytm}"
    print("✓ test_solve_ytm_at_par passed (legacy function)")
    
    # Test class method
    calc = FixedIncomeCalculator(coupon_rate=0.04)
    ytm_class = calc.solve_ytm(100.0)
    assert abs(ytm_class - 0.04) < 0.001, f"Expected YTM ~0.04, got {ytm_class}"
    print("✓ test_solve_ytm_at_par passed (class method)")


def test_solve_ytm_discount():
    """
    Test YTM solver when bond is trading at a discount.
    
    If price < par, YTM should be > coupon rate.
    """
    calc = FixedIncomeCalculator(coupon_rate=0.04)
    
    # Price below par
    discount_price = 98.0
    ytm = calc.solve_ytm(discount_price)
    
    assert ytm > 0.04, f"Discount bond should have YTM > coupon: {ytm}"
    
    # Verify by computing price from solved YTM
    computed_price = calc.price_from_ytm(ytm)
    assert abs(computed_price - discount_price) < 0.01, \
        f"Round-trip failed: {discount_price} -> YTM {ytm} -> {computed_price}"
    
    print(f"  Price {discount_price} implies YTM {ytm:.4%}")
    print("✓ test_solve_ytm_discount passed")


def test_solve_ytm_premium():
    """
    Test YTM solver when bond is trading at a premium.
    
    If price > par, YTM should be < coupon rate.
    """
    calc = FixedIncomeCalculator(coupon_rate=0.04)
    
    # Price above par
    premium_price = 102.0
    ytm = calc.solve_ytm(premium_price)
    
    assert ytm < 0.04, f"Premium bond should have YTM < coupon: {ytm}"
    
    # Verify by computing price from solved YTM
    computed_price = calc.price_from_ytm(ytm)
    assert abs(computed_price - premium_price) < 0.01, \
        f"Round-trip failed: {premium_price} -> YTM {ytm} -> {computed_price}"
    
    print(f"  Price {premium_price} implies YTM {ytm:.4%}")
    print("✓ test_solve_ytm_premium passed")


def test_premium_to_price_conversion():
    """
    Test conversion from 256ths to decimal price.
    
    Treasury prices are quoted in 256ths:
    - 25600 / 256 = 100.00 (par)
    - 25344 / 256 = 99.00
    - 25856 / 256 = 101.00
    """
    assert premium_to_price(25600) == 100.0, "25600/256 should be 100.0"
    assert premium_to_price(25344) == 99.0, "25344/256 should be 99.0"
    assert premium_to_price(25856) == 101.0, "25856/256 should be 101.0"
    
    # Test fractional values
    assert abs(premium_to_price(25500) - 99.609375) < 0.0001, "Fractional conversion failed"
    
    print("✓ test_premium_to_price_conversion passed")


def test_present_value_calculation():
    """
    Test present value calculation directly.
    
    Manual calculation for verification:
    - Cash flows: [2, 2, 2, 102]
    - YTM: 4.5% annual (2.25% per period)
    - PV = 2/(1.0225)^1 + 2/(1.0225)^2 + 2/(1.0225)^3 + 102/(1.0225)^4
    """
    flows = [2.0, 2.0, 2.0, 102.0]
    ytm = 0.045  # 4.5% annual
    
    pv = present_value(flows, ytm, freq=2)
    
    # Manual calculation
    r = 0.0225  # 4.5% / 2
    expected_pv = (2/(1+r)**1 + 2/(1+r)**2 + 2/(1+r)**3 + 102/(1+r)**4)
    
    assert abs(pv - expected_pv) < 0.01, f"Expected {expected_pv:.4f}, got {pv:.4f}"
    print(f"  PV at 4.5% yield: ${pv:.4f}")
    print("✓ test_present_value_calculation passed")


def run_all_tests():
    """Run all tests and report results."""
    print("\nRunning Fixed Income / PV Tests")
    print("=" * 50)
    
    tests = [
        test_cash_flows_basic,
        test_cash_flows_different_parameters,
        test_price_at_par,
        test_price_yield_inverse_relationship,
        test_solve_ytm_at_par,
        test_solve_ytm_discount,
        test_solve_ytm_premium,
        test_premium_to_price_conversion,
        test_present_value_calculation,
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
            print(f"✗ {test.__name__} ERROR: {type(e).__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)