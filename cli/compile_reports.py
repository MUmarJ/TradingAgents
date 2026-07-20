#!/usr/bin/env python3
"""
Compile all trading agent reports into a single consolidated PDF.

Creates a PDF with:
1. Summary table showing all symbols, their decisions, and analysis dates
2. Detailed reports for each symbol (in order specified by REPORT_ORDER)

Usage:
    python cli/compile_reports.py                         # Compile all results into single PDF
    python cli/compile_reports.py --output report.pdf     # Custom output filename
    python cli/compile_reports.py --date 2026-01-18       # Filter to specific date (auto-names output)
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import markdown2
from playwright.sync_api import sync_playwright

# Report order (top to bottom for each symbol's section)
REPORT_ORDER = [
    ("final_trade_decision.md", "Final Trade Decision"),
    ("trader_investment_plan.md", "Trader Investment Plan"),
    ("investment_plan.md", "Investment Plan"),
    ("fundamentals_report.md", "Fundamentals Analysis"),
    ("news_report.md", "News Analysis"),
    ("sentiment_report.md", "Sentiment Analysis"),
    ("market_report.md", "Market Analysis"),
]

# Clean GitHub-style markdown CSS
CSS_STYLES = """
@page {
    size: A4;
    margin: 0.75in;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #24292f;
    max-width: 100%;
    margin: 0;
    padding: 0;
}

h1 {
    font-size: 2em;
    font-weight: 600;
    border-bottom: 1px solid #d0d7de;
    padding-bottom: 0.3em;
    margin-top: 24px;
    margin-bottom: 16px;
}

h2 {
    font-size: 1.5em;
    font-weight: 600;
    border-bottom: 1px solid #d0d7de;
    padding-bottom: 0.3em;
    margin-top: 24px;
    margin-bottom: 16px;
}

h3 {
    font-size: 1.25em;
    font-weight: 600;
    margin-top: 24px;
    margin-bottom: 16px;
}

h4 {
    font-size: 1em;
    font-weight: 600;
    margin-top: 24px;
    margin-bottom: 16px;
}

p {
    margin-top: 0;
    margin-bottom: 16px;
}

ul, ol {
    padding-left: 2em;
    margin-top: 0;
    margin-bottom: 16px;
}

li {
    margin-bottom: 4px;
}

li + li {
    margin-top: 4px;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 0;
    margin-bottom: 16px;
}

th, td {
    padding: 6px 13px;
    border: 1px solid #d0d7de;
}

th {
    background-color: #f6f8fa;
    font-weight: 600;
}

tr:nth-child(2n) {
    background-color: #f6f8fa;
}

hr {
    border: 0;
    border-top: 1px solid #d0d7de;
    margin: 24px 0;
}

code {
    background-color: rgba(175, 184, 193, 0.2);
    padding: 0.2em 0.4em;
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    font-size: 85%;
}

pre {
    background-color: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
    margin-bottom: 16px;
    font-size: 85%;
    line-height: 1.45;
}

pre code {
    padding: 0;
    background: none;
    font-size: 100%;
}

blockquote {
    border-left: 0.25em solid #d0d7de;
    padding: 0 1em;
    margin: 0 0 16px 0;
    color: #57606a;
}

strong {
    font-weight: 600;
}

/* Decision color styling */
.decision-buy { color: #1a7f37; font-weight: 700; }
.decision-sell { color: #cf222e; font-weight: 700; }
.decision-hold { color: #9a6700; font-weight: 700; }

/* Symbol section - page break before each new symbol */
.symbol-section {
    page-break-before: always;
}

.symbol-section:first-of-type {
    page-break-before: avoid;
}

/* Report title styling */
.report-title {
    color: #0969da;
    font-size: 1.3em;
    font-weight: 600;
    margin-top: 32px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #0969da;
}

.report-title:first-of-type {
    margin-top: 16px;
}
"""


def extract_decision(content: str) -> str:
    """Extract BUY/SELL/HOLD decision from final trade decision content."""
    content_lower = content.lower()

    patterns = [
        r"recommendation[:\s]*\*{0,2}(buy|sell|hold)\*{0,2}",
        r"\*{0,2}(buy|sell|hold)\*{0,2}[:\s]*recommendation",
        r"final.*?decision[:\s]*\*{0,2}(buy|sell|hold)\*{0,2}",
        r"recommend.*?(buy|sell|hold)",
        r"action[:\s]*\*{0,2}(buy|sell|hold)\*{0,2}",
    ]

    for pattern in patterns:
        match = re.search(pattern, content_lower)
        if match:
            return match.group(1).upper()

    # Try the canonical signal_processing extractor (same patterns used in backtest)
    try:
        from tradingagents.graph.signal_processing import extract_decision_from_text
        return extract_decision_from_text(content)
    except (ValueError, ImportError):
        pass

    # Keyword frequency fallback — only return if one keyword clearly dominates
    buy_count = len(re.findall(r"\bbuy\b", content_lower))
    sell_count = len(re.findall(r"\bsell\b", content_lower))
    hold_count = len(re.findall(r"\bhold\b", content_lower))

    counts = {"BUY": buy_count, "SELL": sell_count, "HOLD": hold_count}
    max_count = max(counts.values())
    if max_count > 0:
        winners = [k for k, v in counts.items() if v == max_count]
        if len(winners) == 1:
            return winners[0]
        # Tied — cannot determine decision
        return "N/A"

    return "N/A"


def markdown_to_html(md_content: str) -> str:
    """Convert markdown to HTML with extras."""
    return markdown2.markdown(
        md_content,
        extras=[
            "tables",
            "fenced-code-blocks",
            "strike",
            "task_list",
            "cuddled-lists",
        ],
    )


def find_all_reports(
    results_dir: Path,
    date_filter: str | None = None,
    ticker_filter: str | None = None,
) -> list[dict]:
    """Find all report directories and extract their data.

    Args:
        results_dir: Path to the results directory
        date_filter: Optional date string (YYYY-MM-DD) to filter reports
        ticker_filter: Optional ticker symbol to filter reports
    """
    all_reports = []

    if not results_dir.exists():
        return all_reports

    for symbol_dir in sorted(results_dir.iterdir()):
        if not symbol_dir.is_dir():
            continue

        symbol = symbol_dir.name
        if symbol.startswith(".") or " " in symbol:
            continue

        # Skip if ticker doesn't match filter
        if ticker_filter and symbol.upper() != ticker_filter.upper():
            continue

        for date_dir in sorted(symbol_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            date = date_dir.name

            # Skip if date doesn't match filter
            if date_filter and date != date_filter:
                continue

            reports_dir = date_dir / "reports"

            if not reports_dir.exists():
                continue

            report_files = []
            decision = "N/A"

            for filename, title in REPORT_ORDER:
                file_path = reports_dir / filename
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8")
                    html_content = markdown_to_html(content)
                    report_files.append((filename, title, html_content))

                    if filename == "final_trade_decision.md":
                        decision = extract_decision(content)

            if report_files:
                all_reports.append({
                    "symbol": symbol,
                    "date": date,
                    "decision": decision,
                    "reports_dir": reports_dir,
                    "reports": report_files,
                })

    return all_reports


def find_recall_reports(
    results_dir: Path,
    date_filter: str | None = None,
    ticker_filter: str | None = None,
    recall_filter: str | None = None,
) -> list[dict]:
    """Find all Recall report directories and extract their data.

    Handles structure: results/{SYMBOL}/{DATE}/Recall_{period}/reports/

    Args:
        results_dir: Path to the results directory
        date_filter: Optional date string (YYYY-MM-DD) to filter reports
        ticker_filter: Optional ticker symbol to filter reports
        recall_filter: Optional recall period ("3mo", "6mo", "12mo") or None for all
    """
    all_reports = []

    if not results_dir.exists():
        return all_reports

    for symbol_dir in sorted(results_dir.iterdir()):
        if not symbol_dir.is_dir():
            continue

        symbol = symbol_dir.name
        if symbol.startswith(".") or " " in symbol:
            continue

        # Skip if ticker doesn't match filter
        if ticker_filter and symbol.upper() != ticker_filter.upper():
            continue

        for date_dir in sorted(symbol_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            date = date_dir.name

            # Skip if date doesn't match filter
            if date_filter and date != date_filter:
                continue

            # Look for Recall_* subdirectories
            for recall_dir in sorted(date_dir.iterdir()):
                if not recall_dir.is_dir():
                    continue

                if not recall_dir.name.startswith("Recall_"):
                    continue

                # Extract period (e.g., "3mo" from "Recall_3mo")
                period = recall_dir.name.replace("Recall_", "")

                if recall_filter and period != recall_filter:
                    continue

                reports_dir = recall_dir / "reports"
                if not reports_dir.exists():
                    continue

                report_files = []
                decision = "N/A"

                for filename, title in REPORT_ORDER:
                    file_path = reports_dir / filename
                    if file_path.exists():
                        content = file_path.read_text(encoding="utf-8")
                        html_content = markdown_to_html(content)
                        report_files.append((filename, title, html_content))

                        if filename == "final_trade_decision.md":
                            decision = extract_decision(content)

                if report_files:
                    all_reports.append({
                        "symbol": symbol,
                        "date": date,
                        "period": period,
                        "decision": decision,
                        "reports_dir": reports_dir,
                        "reports": report_files,
                        "is_recall": True,
                    })

    return all_reports


def build_html_document(all_reports: list[dict]) -> str:
    """Build complete HTML document with summary table and all reports."""

    # Detect if we have recall reports
    has_recall = any(r.get("is_recall", False) for r in all_reports)

    # Period display mapping
    period_display_map = {"3mo": "3 Month", "6mo": "6 Month", "12mo": "12 Month"}

    # Sort reports for logical grouping (symbol, date, period)
    sorted_reports = sorted(
        all_reports,
        key=lambda r: (r["symbol"], r["date"], r.get("period", "")),
    )

    # Build summary table rows with visual grouping
    summary_rows = []
    current_symbol = None

    for report_data in sorted_reports:
        decision = report_data["decision"]
        decision_class = f"decision-{decision.lower()}" if decision in ["BUY", "SELL", "HOLD"] else ""

        # Show symbol only on first row of each group
        symbol_display = report_data["symbol"]
        if report_data["symbol"] == current_symbol and has_recall:
            symbol_display = ""
        else:
            current_symbol = report_data["symbol"]

        if has_recall:
            period = report_data.get("period", "N/A")
            period_text = period_display_map.get(period, period)
            summary_rows.append(f'''<tr>
            <td><strong>{symbol_display}</strong></td>
            <td>{report_data["date"]}</td>
            <td>{period_text}</td>
            <td class="{decision_class}">{decision}</td>
            <td>{len(report_data["reports"])} reports</td>
        </tr>''')
        else:
            summary_rows.append(f'''<tr>
            <td><strong>{symbol_display}</strong></td>
            <td>{report_data["date"]}</td>
            <td class="{decision_class}">{decision}</td>
            <td>{len(report_data["reports"])} reports</td>
        </tr>''')

    summary_table = "\n".join(summary_rows)

    # Build table header based on report type
    if has_recall:
        table_header = """<tr>
            <th>Symbol</th>
            <th>Analysis Date</th>
            <th>Period</th>
            <th>Decision</th>
            <th>Reports</th>
        </tr>"""
    else:
        table_header = """<tr>
            <th>Symbol</th>
            <th>Analysis Date</th>
            <th>Decision</th>
            <th>Reports</th>
        </tr>"""

    # Build symbol sections
    symbol_sections = []
    for report_data in sorted_reports:
        symbol = report_data["symbol"]
        date = report_data["date"]
        decision = report_data["decision"]
        decision_class = f"decision-{decision.lower()}" if decision in ["BUY", "SELL", "HOLD"] else ""

        # Include period in title for Recall reports
        if report_data.get("is_recall"):
            period = report_data.get("period", "")
            period_text = period_display_map.get(period, period)
            title = f"{symbol} Trading Analysis Report ({period_text} Recall)"
        else:
            title = f"{symbol} Trading Analysis Report"

        # Build report content - simple flowing structure
        reports_html_parts = []
        for _, report_title, html_content in report_data["reports"]:
            reports_html_parts.append(f'''<div class="report-title">{report_title}</div>
{html_content}''')

        reports_html = "\n".join(reports_html_parts)

        symbol_sections.append(f'''<div class="symbol-section">
<h1>{title}</h1>
<p><strong>Date:</strong> {date} &nbsp;|&nbsp; <strong>Recommendation:</strong> <span class="{decision_class}">{decision}</span></p>
<hr>
{reports_html}
</div>''')

    all_symbols_html = "\n".join(symbol_sections)

    generated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Analysis Report</title>
    <style>
{CSS_STYLES}
    </style>
</head>
<body>
<h1>Trading Analysis Report</h1>
<p><em>Generated: {generated_date}</em></p>

<h2>Summary of Recommendations</h2>
<table>
    <thead>
        {table_header}
    </thead>
    <tbody>
        {summary_table}
    </tbody>
</table>

<hr>

{all_symbols_html}

<hr>
<p><em>Report generated by TradingAgents</em></p>
</body>
</html>'''
    return html


def compile_to_pdf(html_content: str, output_path: Path) -> bool:
    """Generate PDF from HTML using Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content, wait_until="networkidle")

            page.pdf(
                path=str(output_path),
                format="A4",
                margin={
                    "top": "0.5in",
                    "bottom": "0.5in",
                    "left": "0.5in",
                    "right": "0.5in",
                },
                print_background=True,
            )
            browser.close()
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Compile all trading agent reports into a single consolidated PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python cli/compile_reports.py
    python cli/compile_reports.py --output my_report.pdf
    python cli/compile_reports.py --date 2026-01-18
    python cli/compile_reports.py --ticker RAPT
    python cli/compile_reports.py --ticker RAPT --recall all
    python cli/compile_reports.py --ticker RAPT --recall 6mo --date 2026-01-20
        """,
    )
    parser.add_argument(
        "--output", "-o",
        default="./results/trading_analysis_report.pdf",
        help="Output PDF filename (default: ./results/trading_analysis_report.pdf)",
    )
    parser.add_argument(
        "--results-dir", "-r",
        default="./results",
        help="Results directory (default: ./results)",
    )
    parser.add_argument(
        "--date", "-d",
        help="Filter reports to a specific date (format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "--ticker", "-t",
        help="Filter reports to a specific ticker symbol (e.g., RAPT)",
    )
    parser.add_argument(
        "--recall", "-R",
        choices=["3mo", "6mo", "12mo", "all"],
        help="Filter to Recall period reports. Use 'all' to include all periods.",
    )

    args = parser.parse_args()

    # Validate date format if provided
    if args.date:
        import re as re_module
        if not re_module.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
            print(f"Error: Invalid date format '{args.date}'. Expected YYYY-MM-DD")
            sys.exit(1)

    results_dir = Path(args.results_dir)
    default_output = "./results/trading_analysis_report.pdf"

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    # Build scan message
    scan_filters = []
    if args.ticker:
        scan_filters.append(f"ticker {args.ticker}")
    if args.date:
        scan_filters.append(f"date {args.date}")
    if args.recall:
        scan_filters.append(f"Recall period {args.recall}")

    if scan_filters:
        print(f"Scanning {results_dir} for reports ({', '.join(scan_filters)})...")
    else:
        print(f"Scanning {results_dir} for reports...")

    # Choose which scanner to use based on --recall flag
    if args.recall:
        recall_filter = None if args.recall == "all" else args.recall
        all_reports = find_recall_reports(
            results_dir,
            date_filter=args.date,
            ticker_filter=args.ticker,
            recall_filter=recall_filter,
        )
    else:
        all_reports = find_all_reports(
            results_dir,
            date_filter=args.date,
            ticker_filter=args.ticker,
        )

    if not all_reports:
        filter_desc = []
        if args.ticker:
            filter_desc.append(f"ticker {args.ticker}")
        if args.date:
            filter_desc.append(f"date {args.date}")
        if args.recall:
            filter_desc.append(f"Recall_{args.recall}")
        if filter_desc:
            print(f"No reports found for {', '.join(filter_desc)}")
        else:
            print("No reports found")
        sys.exit(1)

    print(f"Found {len(all_reports)} report(s):\n")

    # Period display mapping for console output
    period_display_map = {"3mo": "3mo", "6mo": "6mo", "12mo": "12mo"}

    for report_data in all_reports:
        decision_indicator = {
            "BUY": "[BUY]",
            "SELL": "[SELL]",
            "HOLD": "[HOLD]",
        }.get(report_data["decision"], "[N/A]")

        if report_data.get("is_recall"):
            period = report_data.get("period", "")
            period_str = period_display_map.get(period, period)
            print(f"  {report_data['symbol']:6} | {report_data['date']} | {period_str:4} | {decision_indicator:6} | {len(report_data['reports'])} reports")
        else:
            print(f"  {report_data['symbol']:6} | {report_data['date']} | {decision_indicator:6} | {len(report_data['reports'])} reports")

    # Determine output path
    if args.output == default_output:
        # Generate dynamic filename
        symbols = sorted(set(r["symbol"] for r in all_reports))[:5]
        symbols_str = "_".join(symbols)

        if args.date and args.recall:
            recall_suffix = f"Recall_{args.recall}"
            output_path = Path(f"./results/trading_report_{args.date}_{symbols_str}_{recall_suffix}.pdf")
        elif args.date:
            output_path = Path(f"./results/trading_report_{args.date}_{symbols_str}.pdf")
        elif args.recall:
            recall_suffix = f"Recall_{args.recall}"
            output_path = Path(f"./results/trading_report_{symbols_str}_{recall_suffix}.pdf")
        else:
            output_path = Path(default_output)
    else:
        output_path = Path(args.output)

    print("\nGenerating PDF...")

    html_document = build_html_document(all_reports)

    if compile_to_pdf(html_document, output_path):
        print(f"\n+ PDF created: {output_path}")
    else:
        print("\n- Failed to create PDF")
        sys.exit(1)


if __name__ == "__main__":
    main()
