"""Parsers for cached dataset string formats.

Cached datasets store raw data as strings (Python repr dicts, CSV text,
indicator sections). These parsers convert them to structured data for
use by ML models and strategies.
"""

import ast
from typing import Dict, List, Any


def parse_news_articles(news_data_str: str) -> List[Dict[str, Any]]:
    """Parse articles from a cached news_data or global_news_data string.

    The cached format is one or two Python dict repr strings separated by
    newlines. Each dict has a 'feed' key containing an article list.

    Articles may come from Polygon (minimal fields) or Alpha Vantage
    (full fields including overall_sentiment_score/label).

    Returns a flat list of article dicts with at least 'title' and 'summary'.
    """
    if not news_data_str or not news_data_str.strip():
        return []

    articles = []
    for line in news_data_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = ast.literal_eval(line)
            if isinstance(parsed, dict) and 'feed' in parsed:
                for article in parsed['feed']:
                    # Normalize: ensure title and summary exist
                    if isinstance(article, dict) and article.get('title'):
                        articles.append(article)
        except (ValueError, SyntaxError):
            # Malformed line — skip without crashing
            pass

    return articles


def extract_article_text(article: Dict[str, Any]) -> str:
    """Extract scoreable text from an article dict.

    Combines title and summary for sentiment scoring. Falls back to
    title-only if summary is missing.
    """
    title = article.get('title', '')
    summary = article.get('summary', '')
    if summary:
        return f"{title}. {summary}"
    return title


def extract_av_ticker_sentiment(
    news_data_str: str,
    ticker: str,
    min_relevance: float = 0.7,
) -> Dict[str, Any]:
    """Extract Alpha Vantage pre-computed sentiment for a specific ticker.

    AV provides ticker_sentiment_score and relevance_score per article
    per ticker. This function filters articles by ticker and relevance,
    then aggregates the pre-computed scores.

    Returns:
        Dict with: n_articles, avg_sentiment, avg_relevance, n_bearish,
        n_neutral, n_bullish, topic_sentiments, n_tech_articles, etc.
    """
    if not news_data_str or not news_data_str.strip():
        return _empty_av_sentiment()

    ticker_articles = []
    all_topic_sentiments: Dict[str, List[float]] = {}
    n_tech = 0

    for line in news_data_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = ast.literal_eval(line)
        except (ValueError, SyntaxError):
            continue

        if not isinstance(parsed, dict) or 'feed' not in parsed:
            continue

        for article in parsed['feed']:
            # Check for ticker-specific sentiment
            for ts in article.get('ticker_sentiment', []):
                if ts.get('ticker') == ticker:
                    relevance = float(ts.get('relevance_score', 0))
                    if relevance >= min_relevance:
                        ticker_articles.append({
                            'sentiment': float(ts.get('ticker_sentiment_score', 0)),
                            'relevance': relevance,
                            'label': ts.get('ticker_sentiment_label', 'Neutral'),
                            'overall': article.get('overall_sentiment_score', 0),
                        })
                    break

            # Track topic sentiments (technology, earnings, etc.)
            for topic in article.get('topics', []):
                t_name = topic.get('topic', '')
                t_rel = float(topic.get('relevance_score', 0))
                if t_rel >= 0.7:
                    overall = article.get('overall_sentiment_score', 0)
                    if isinstance(overall, (int, float)):
                        if t_name not in all_topic_sentiments:
                            all_topic_sentiments[t_name] = []
                        all_topic_sentiments[t_name].append(overall)
                    if t_name == 'technology':
                        n_tech += 1

    if not ticker_articles:
        result = _empty_av_sentiment()
        # Still include topic-level sentiment
        result['n_tech_articles'] = n_tech
        for topic, scores in all_topic_sentiments.items():
            result[f'topic_{topic}_avg'] = sum(scores) / len(scores) if scores else 0.0
            result[f'topic_{topic}_n'] = len(scores)
        return result

    sentiments = [a['sentiment'] for a in ticker_articles]
    labels = [a['label'] for a in ticker_articles]

    result = {
        'n_ticker_articles': len(ticker_articles),
        'avg_ticker_sentiment': sum(sentiments) / len(sentiments),
        'max_ticker_sentiment': max(sentiments),
        'min_ticker_sentiment': min(sentiments),
        'avg_relevance': sum(a['relevance'] for a in ticker_articles) / len(ticker_articles),
        'n_bearish': sum(1 for l in labels if 'Bearish' in l),
        'n_neutral': sum(1 for l in labels if l == 'Neutral'),
        'n_bullish': sum(1 for l in labels if 'Bullish' in l),
        'n_tech_articles': n_tech,
    }

    # Topic-level sentiments
    for topic, scores in all_topic_sentiments.items():
        result[f'topic_{topic}_avg'] = sum(scores) / len(scores) if scores else 0.0
        result[f'topic_{topic}_n'] = len(scores)

    return result


def _empty_av_sentiment() -> Dict[str, Any]:
    """Return empty AV sentiment dict when no relevant articles found."""
    return {
        'n_ticker_articles': 0,
        'avg_ticker_sentiment': 0.0,
        'max_ticker_sentiment': 0.0,
        'min_ticker_sentiment': 0.0,
        'avg_relevance': 0.0,
        'n_bearish': 0,
        'n_neutral': 0,
        'n_bullish': 0,
        'n_tech_articles': 0,
    }
