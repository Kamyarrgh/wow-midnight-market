import pytest
from app.stats import calculate_time_window_stats, calculate_volatility
from app.signals import evaluate_sell_signal

def test_time_window_stats():
    # Day 1: 10,000g | Day 2: 11,000g | Day 3: 12,000g | Day 4: 15,000g (in copper: * 10,000)
    prices = [100000000, 110000000, 120000000, 150000000]
    current = 150000000

    stats = calculate_time_window_stats(prices, current)
    assert stats["high"] == 150000000
    assert stats["low"] == 100000000
    assert stats["change_percent"] == 50.0
    assert stats["percentile"] == 100.0

def test_sell_signal_strong_sell():
    signal = evaluate_sell_signal(
        current_price=150000000,
        percentile_30d=95.0,
        percentile_7d=90.0,
        momentum_24h=12.5,
        momentum_6h=4.0,
        ma_30d=110000000,
        supply_percentile=15.0,
        high_30d=155000000
    )
    assert signal["score"] >= 70
    assert "STRONG SELL" in signal["classification"] or "EXCELLENT SELL" in signal["classification"]
    assert len(signal["reasons"]) > 0
