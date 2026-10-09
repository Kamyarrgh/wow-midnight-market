import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def calculate_time_window_stats(prices: List[int], current_price: int) -> Dict[str, Any]:
    if not prices:
        return {
            "current": current_price,
            "high": current_price,
            "low": current_price,
            "average": current_price,
            "change_percent": 0.0,
            "distance_from_high": 0.0,
            "distance_from_low": 0.0,
            "percentile": 50.0
        }

    high = max(prices)
    low = min(prices)
    avg = int(sum(prices) / len(prices))
    first_price = prices[0]
    
    change_pct = ((current_price - first_price) / first_price * 100.0) if first_price > 0 else 0.0
    dist_high = ((high - current_price) / high * 100.0) if high > 0 else 0.0
    dist_low = ((current_price - low) / low * 100.0) if low > 0 else 0.0

    percentile = float(np.percentile(prices, [current_price])[0]) if len(prices) > 1 else 50.0
    # Safe percentile calculation: rank of current within window
    smaller_count = sum(1 for p in prices if p <= current_price)
    percentile = round((smaller_count / len(prices)) * 100.0, 1)

    return {
        "current": current_price,
        "high": high,
        "low": low,
        "average": avg,
        "change_percent": round(change_pct, 2),
        "distance_from_high": round(dist_high, 2),
        "distance_from_low": round(dist_low, 2),
        "percentile": percentile
    }

def calculate_moving_average(prices: List[int], window: int) -> Optional[float]:
    if len(prices) < window or window == 0:
        return None
    return float(np.mean(prices[-window:]))

def calculate_volatility(prices: List[int]) -> float:
    if len(prices) < 2:
        return 0.0
    returns = np.diff(prices) / prices[:-1]
    return round(float(np.std(returns) * 100.0), 2)
