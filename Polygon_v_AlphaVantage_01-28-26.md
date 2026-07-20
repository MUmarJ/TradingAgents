# Polygon.io vs Alpha Vantage Data Comparison

**Date**: January 28, 2026
**Test Symbol**: PSTG (Pure Storage)
**Date Range**: 2025-12-15 to 2026-01-15

---

## 1. Stock OHLCV Data

| Metric | Polygon | Alpha Vantage |
|--------|---------|---------------|
| **Rows returned** | 22 | 22 |
| **Response time** | 0.14s | 0.36s |
| **Price accuracy** | All 22 dates match exactly | -- |
| **Column format** | Identical CSV headers | Identical CSV headers |
| **Sort order** | Ascending (oldest first) | Descending (newest first) |

**Sample price comparison** (all 22 dates matched):

| Date | Polygon Close | Alpha Vantage Close | Match |
|------|--------------|-------------------|-------|
| 2025-12-15 | 69.5700 | 69.5700 | MATCH |
| 2025-12-16 | 69.7200 | 69.7200 | MATCH |
| 2025-12-17 | 66.3200 | 66.3200 | MATCH |
| 2025-12-18 | 67.0600 | 67.0600 | MATCH |
| 2025-12-19 | 69.1300 | 69.1300 | MATCH |

**Winner: Polygon** -- 2.5x faster, identical data.

---

## 2. Ticker News (PSTG)

| Metric | Polygon | Alpha Vantage |
|--------|---------|---------------|
| **Articles found** | **3** | **0** |
| **Response time** | 1.81s | 4.63s |
| **Sentiment labels** | Yes (Bullish/Bearish/Neutral) | N/A (no articles) |
| **Summaries** | Yes (rich descriptions) | N/A |
| **Sources** | Motley Fool, Benzinga | -- |

**Polygon articles returned:**

1. "The S&P 500's Best Stock in 2025 May Soar in 2026..." -- *Motley Fool*, Jan 4 -- **Bullish**
2. "A Once-in-a-Decade Investment Opportunity: The 3 Best AI Stocks..." -- *Motley Fool*, Jan 4 -- **Bullish**
3. "This AI Infrastructure Stock Is 'Most Likely' To Be Added To S&P 500..." -- *Benzinga*, Jan 2 -- **Bullish**

Alpha Vantage returned zero articles for PSTG even with monthly bucketing enabled.

**Winner: Polygon** -- significantly better coverage for mid-cap tickers.

---

## 3. Global News

| Metric | Polygon | Alpha Vantage |
|--------|---------|---------------|
| **Articles returned** | 5 (limit=5) | 50 (limit=50) |
| **Response time** | 0.11s | 0.44s |
| **Article quality** | Curated, major outlets | Mixed (includes institutional filing noise) |
| **Ticker tagging** | Yes, relevant tickers per article | Yes, via `ticker_sentiment` |

**Polygon sample:**
- "Tesla Is Struggling -- The Global EV Market Isn't" | TSLA, BYDDY, GM, VWAGY, F
- "90% of Nvidia's Customers Now Buy This -- and It's Not GPUs" | NVDA, ANET, CSCO

**Alpha Vantage sample:**
- "Robeco Schweiz AG Sells 2,888 Shares of Linde PLC $LIN" | LIN
- "Sumitomo Mitsui Trust Group Inc. Grows Holdings in eBay Inc. $EBAY" | EBAY

**Winner: Tie** -- Polygon is 4x faster with higher-quality curation; Alpha Vantage provides more volume.

---

## 4. Technical Indicators

### 4a. SMA (50-day)

| Metric | Polygon | Alpha Vantage |
|--------|---------|---------------|
| **Data points** | 21 | 21 |
| **Response time** | 0.12s | 0.35s |
| **Value accuracy** | Exact match on all 21 dates | -- |

| Date | Polygon | Alpha Vantage | Match |
|------|---------|--------------|-------|
| 2025-12-16 | 86.3724 | 86.3724 | MATCH |
| 2025-12-17 | 85.9408 | 85.9408 | MATCH |
| 2025-12-18 | 85.4192 | 85.4192 | MATCH |
| 2025-12-19 | 84.9294 | 84.9294 | MATCH |
| 2025-12-22 | 84.4884 | 84.4884 | MATCH |

### 4b. RSI (14-day)

| Metric | Polygon | Alpha Vantage |
|--------|---------|---------------|
| **Data points** | 21 | 21 |
| **Response time** | 0.11s | 0.45s |
| **Value accuracy** | ~0.1% difference (negligible) | -- |

| Date | Polygon | Alpha Vantage | Diff |
|------|---------|--------------|------|
| 2025-12-16 | 38.3416 | 38.2998 | 0.11% |
| 2025-12-17 | 35.3289 | 35.2833 | 0.13% |
| 2025-12-18 | 36.4984 | 36.4563 | 0.12% |
| 2025-12-19 | 39.7791 | 39.7464 | 0.08% |
| 2025-12-22 | 37.9337 | 37.8986 | 0.09% |

The ~0.1% RSI difference is due to different intermediate calculation precision. Functionally identical for trading decisions.

### 4c. MACD

| Metric | Polygon | Alpha Vantage |
|--------|---------|---------------|
| **Data points** | 21 | 21 |
| **Response time** | 24.97s (hit rate limit) | 0.43s |
| **Value accuracy** | <0.01% difference (within rounding) | -- |

| Date | Polygon | Alpha Vantage | Match |
|------|---------|--------------|-------|
| 2025-12-16 | -4.5940 | -4.5945 | MATCH |
| 2025-12-17 | -4.8829 | -4.8834 | MATCH |
| 2025-12-18 | -4.9947 | -4.9951 | MATCH |
| 2025-12-19 | -4.8602 | -4.8606 | MATCH |
| 2025-12-22 | -4.8438 | -4.8442 | MATCH |

Note: Polygon hit the 5 req/min rate limit on the 4th API call during this test, adding a 24s sleep. In production, the rate limiter spaces calls automatically.

**Winner: Tie** -- Values are identical/negligible difference. Polygon faster per-call but rate limit can add delays when making many calls in sequence.

---

## 5. Coverage Matrix

| Data Type | Polygon Free Tier | Alpha Vantage Free Tier |
|-----------|:-:|:-:|
| Stock OHLCV | YES | YES |
| News (ticker) | YES (better mid-cap) | YES (weak mid-cap) |
| News (global) | YES | YES |
| SMA / EMA | YES | YES |
| RSI | YES | YES |
| MACD | YES | YES |
| Bollinger Bands | NO (auto-fallback to yfinance) | YES |
| ATR | NO (auto-fallback to yfinance) | YES |
| VWMA | NO (auto-fallback to yfinance) | NOT DIRECT |
| MFI | NO (auto-fallback to yfinance) | NO |
| Fundamentals | NO ($199/mo) | YES |
| Balance Sheet | NO ($199/mo) | YES |
| Income Statement | NO ($199/mo) | YES |
| Cash Flow | NO ($199/mo) | YES |
| Insider Transactions | NO | YES |

---

## 6. Rate Limits

| | Polygon Free | Alpha Vantage Free |
|-|:--:|:--:|
| **Per minute** | 5 requests | 5 requests |
| **Daily cap** | **None** | **500 requests** |
| **History** | 2 years | Full history |

Polygon's lack of a daily cap is a significant advantage when running batch analyses across many symbols.

---

## 7. Current Default Configuration

```
DATA_VENDOR_STOCK=polygon          # Faster, identical data
DATA_VENDOR_INDICATORS=polygon     # Faster, auto-fallback for unsupported (boll, atr)
DATA_VENDOR_NEWS=polygon           # Better mid-cap coverage, faster
DATA_VENDOR_FUNDAMENTALS=alpha_vantage  # Only free option for fundamentals
SOCIAL_SENTIMENT_VENDOR=aggregated      # Combines Stocktwits + ApeWisdom + available APIs
```

---

## 8. Conclusion

The current defaults are optimal:

- **Polygon** for stock data, news, and indicators -- faster response times, no daily rate limit cap, better news coverage for mid/small-cap tickers
- **Alpha Vantage** for fundamentals -- Polygon requires $199/mo for balance sheets, income statements, and cash flow data
- **Automatic fallback** handles edge cases: unsupported Polygon indicators (Bollinger, ATR) automatically fall back to yfinance/stockstats; rate limit errors on either vendor trigger fallback to the other
