from typing import Dict, Any, List

def evaluate_sell_signal(
    current_price: int,
    percentile_30d: float,
    percentile_7d: float,
    momentum_24h: float,
    momentum_6h: float,
    ma_30d: float,
    supply_percentile: float,
    high_30d: int
) -> Dict[str, Any]:
    """
    Market Opportunity Score (0 - 100)
     analytical estimate.
    """
    reasons = []
    score = 0.0

    # 1. Price percentile contribution (Weight: 35)
    score += (percentile_30d * 0.35)
    if percentile_30d >= 85:
        reasons.append(f"Price is in the top {100 - int(percentile_30d)}% of the last 30 days")

    # 2. Distance from 30-day Moving Average (Weight: 25)
    if ma_30d > 0:
        dist_ma_pct = ((current_price - ma_30d) / ma_30d) * 100.0
        if dist_ma_pct > 0:
            ma_contrib = min(25.0, (dist_ma_pct / 20.0) * 25.0)
            score += ma_contrib
            if dist_ma_pct >= 10:
                reasons.append(f"Price is {round(dist_ma_pct, 1)}% above the 30-day average")

    # 3. Momentum contribution (Weight: 20)
    if momentum_24h > 0:
        mom_contrib = min(20.0, (momentum_24h / 15.0) * 20.0)
        score += mom_contrib
        reasons.append("24h price momentum is strongly positive")

    # 4. Supply condition (Weight: 20)
    # Low supply is bullish for sellers
    if supply_percentile < 30:
        supply_contrib = ((30 - supply_percentile) / 30.0) * 20.0
        score += supply_contrib
        reasons.append("Market supply is significantly below normal")

    final_score = int(min(100, max(0, round(score))))

    if final_score >= 85:
        classification = "EXCELLENT SELL"
    elif final_score >= 70:
        classification = "STRONG SELL"
    elif final_score >= 50:
        classification = "GOOD SELL"
    elif final_score >= 30:
        classification = "WEAK SELL"
    else:
        classification = "HOLD"

    return {
        "score": final_score,
        "classification": classification,
        "disclaimer": "Market Opportunity Score is an analytical estimate and does not guarantee profit.",
        "reasons": reasons
    }
