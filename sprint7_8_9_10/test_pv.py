import sys
sys.path.insert(0, '.')

from sprint7 import pv_cash_flows, present_value, solve_ytm, price_from_ytm, premium_to_price

def test_pv_basic():
    flows = pv_cash_flows(years=2, coupon_rate=0.04, face=100, freq=2)
    assert len(flows) == 4
    assert flows[0] == 2.0
    assert flows[1] == 2.0
    assert flows[2] == 2.0
    assert flows[3] == 102.0

def test_price_at_par():
    ytm = 0.04
    price = price_from_ytm(ytm)
    assert abs(price - 100.0) < 0.01

def test_solve_ytm():
    market_price = 100.0
    ytm = solve_ytm(market_price)
    assert abs(ytm - 0.04) < 0.001

if __name__ == "__main__":
    test_pv_basic()
    test_price_at_par()
    test_solve_ytm()
    print("All sanity checks passed")
