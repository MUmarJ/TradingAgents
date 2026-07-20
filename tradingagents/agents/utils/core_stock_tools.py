from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve stock price data (OHLCV) for a given ticker symbol.
    Uses the configured core_stock_apis vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
    """
    return route_to_vendor("get_stock_data", symbol, start_date, end_date)


@tool
def get_current_quote(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Analysis date in yyyy-mm-dd format. When provided, returns historical quote as of that date instead of real-time data."] = "",
) -> str:
    """
    Get quote data for a stock as of a specific date or real-time.

    When curr_date is provided, returns the historical closing price and
    day's OHLC for that date using yfinance history (no look-ahead bias).
    When curr_date is empty, returns real-time quote via fast_info.

    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        curr_date (str): Analysis date in yyyy-mm-dd format (optional)

    Returns:
        str: Quote with price, change, day range
    """
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        ticker = yf.Ticker(symbol.upper())

        if curr_date:
            # Point-in-time mode: use historical data only (no look-ahead)
            curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
            end_dt = curr_dt + timedelta(days=1)
            start_dt = curr_dt - timedelta(days=10)  # buffer for weekends/holidays
            hist = ticker.history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
            )

            if hist.empty:
                return f"No historical data found for {symbol.upper()} around {curr_date}"

            # CRITICAL: Filter to only rows ON OR BEFORE curr_date to prevent look-ahead bias
            hist = hist[hist.index.date <= curr_dt.date()]
            if hist.empty:
                return f"No historical data found for {symbol.upper()} on or before {curr_date}"

            # Last available row is the "current" quote (on or before curr_date)
            current_row = hist.iloc[-1]
            last_price = float(current_row["Close"])
            day_high = float(current_row["High"])
            day_low = float(current_row["Low"])
            day_open = float(current_row["Open"])
            volume = int(current_row["Volume"])
            quote_date = str(hist.index[-1].date())

            # Previous close from the row before
            if len(hist) >= 2:
                prev_close = float(hist.iloc[-2]["Close"])
            else:
                prev_close = day_open  # fallback to open if no prior day

            change = last_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0

            if change_pct > 2:
                trend = "Strongly Up"
            elif change_pct > 0.5:
                trend = "Up"
            elif change_pct > -0.5:
                trend = "Flat"
            elif change_pct > -2:
                trend = "Down"
            else:
                trend = "Strongly Down"

            report = f"# Quote for {symbol.upper()} (as of {quote_date})\n\n"
            report += f"**Date:** {quote_date}\n\n"
            report += f"## Price\n"
            report += f"- **Close:** ${last_price:.2f}\n"
            report += f"- **Open:** ${day_open:.2f}\n"
            report += f"- **Change:** ${change:+.2f} ({change_pct:+.2f}%) - {trend}\n"
            report += f"- **Previous Close:** ${prev_close:.2f}\n\n"
            report += f"## Day's Range\n"
            report += f"- **High:** ${day_high:.2f}\n"
            report += f"- **Low:** ${day_low:.2f}\n"
            day_range = day_high - day_low
            range_pct = (day_range / prev_close * 100) if prev_close else 0
            report += f"- **Range:** ${day_range:.2f} ({range_pct:.2f}%)\n"
            report += f"- **Volume:** {volume:,}\n\n"

            if day_high > day_low:
                position = (last_price - day_low) / (day_high - day_low) * 100
                report += f"**Position in Day's Range:** {position:.0f}% (0%=low, 100%=high)\n"

            return report

        else:
            # Real-time mode: existing behavior for live trading
            info = ticker.fast_info

            last_price = info.last_price
            prev_close = info.previous_close
            day_high = info.day_high
            day_low = info.day_low

            change = last_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0

            if change_pct > 2:
                trend = "Strongly Up"
            elif change_pct > 0.5:
                trend = "Up"
            elif change_pct > -0.5:
                trend = "Flat"
            elif change_pct > -2:
                trend = "Down"
            else:
                trend = "Strongly Down"

            report = f"# Real-Time Quote for {symbol.upper()}\n\n"
            report += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report += f"## Current Price\n"
            report += f"- **Last Price:** ${last_price:.2f}\n"
            report += f"- **Change:** ${change:+.2f} ({change_pct:+.2f}%) - {trend}\n"
            report += f"- **Previous Close:** ${prev_close:.2f}\n\n"
            report += f"## Today's Range\n"
            report += f"- **Day High:** ${day_high:.2f}\n"
            report += f"- **Day Low:** ${day_low:.2f}\n"
            report += f"- **Range:** ${day_high - day_low:.2f} ({((day_high - day_low) / prev_close * 100):.2f}%)\n\n"

            if day_high > day_low:
                position = (last_price - day_low) / (day_high - day_low) * 100
                report += f"**Position in Day's Range:** {position:.0f}% (0%=low, 100%=high)\n"

            return report

    except Exception as e:
        return f"Error fetching quote for {symbol}: {str(e)}"
