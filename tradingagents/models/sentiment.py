"""Financial sentiment analysis using specialized HuggingFace models.

Wraps FinBERT, DeBERTa-v3 Finance, and ModernFinBERT for deterministic,
zero-cost sentiment scoring of financial news and social media text.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ArticleSentiment:
    """Sentiment result for a single article."""
    title: str
    sentiment_label: str    # "positive", "negative", "neutral"
    sentiment_score: float  # -1.0 to +1.0 (negative to positive)
    confidence: float       # model confidence in the chosen label


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment across multiple articles."""
    ticker: str
    date: str
    model_name: str
    num_articles: int
    avg_score: float              # -1.0 to +1.0
    positive_pct: float           # 0.0 to 1.0
    negative_pct: float           # 0.0 to 1.0
    neutral_pct: float            # 0.0 to 1.0
    weighted_score: float         # recency-weighted average (if timestamps available)
    article_sentiments: List[ArticleSentiment] = field(default_factory=list)


# Map from short name to HuggingFace model ID
SENTIMENT_MODELS = {
    "deberta-finance": "mrm8488/deberta-v3-ft-financial-news-sentiment-analysis",
    "modern-finbert": "tabularisai/ModernFinBERT",
    "finbert": "ProsusAI/finbert",
}

# Label normalization: each model uses different label names
_LABEL_MAP = {
    # DeBERTa finance
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    # FinBERT (ProsusAI)
    "Positive": "positive",
    "Negative": "negative",
    "Neutral": "neutral",
    # Some models use lowercase already
    "pos": "positive",
    "neg": "negative",
    "neu": "neutral",
    # ModernFinBERT / others
    "bullish": "positive",
    "bearish": "negative",
    "Bullish": "positive",
    "Bearish": "negative",
}


def _normalize_label(label: str) -> str:
    """Normalize model-specific labels to positive/negative/neutral."""
    return _LABEL_MAP.get(label, label.lower())


def _label_to_sign(label: str) -> float:
    """Convert normalized label to directional sign."""
    if label == "positive":
        return 1.0
    elif label == "negative":
        return -1.0
    return 0.0


class FinancialSentimentModel:
    """Wrapper for HuggingFace financial sentiment classification models.

    Supports DeBERTa-v3 Finance (recommended), FinBERT, and ModernFinBERT.
    Models are lazy-loaded on first use to avoid startup overhead.
    """

    def __init__(self, model_name: str = "deberta-finance"):
        if model_name not in SENTIMENT_MODELS:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Supported: {list(SENTIMENT_MODELS.keys())}"
            )
        self.model_key = model_name
        self.model_id = SENTIMENT_MODELS[model_name]
        self._pipeline = None

    def _load(self):
        """Lazy-load the HuggingFace pipeline."""
        from transformers import pipeline
        self._pipeline = pipeline(
            "text-classification",
            model=self.model_id,
            top_k=None,  # return scores for all classes
            truncation=True,
            max_length=512,
        )

    def score_text(self, text: str) -> ArticleSentiment:
        """Score a single text string for financial sentiment.

        Args:
            text: Financial text (headline, article summary, social post).
                  Will be truncated to 512 tokens by the model.

        Returns:
            ArticleSentiment with normalized label, signed score, and confidence.
        """
        if self._pipeline is None:
            self._load()

        results = self._pipeline(text[:2000])  # pre-truncate to avoid tokenizer overhead

        # results is List[List[Dict]] with top_k=None
        # Each inner list has one dict per class: {"label": "...", "score": float}
        scores = results[0] if results else []

        # Find the top-scoring class
        best = max(scores, key=lambda x: x["score"]) if scores else {"label": "neutral", "score": 0.5}
        label = _normalize_label(best["label"])
        confidence = best["score"]

        # Build a signed score: confidence * direction
        # For a more nuanced score, use the positive-negative differential
        pos_score = 0.0
        neg_score = 0.0
        for s in scores:
            norm = _normalize_label(s["label"])
            if norm == "positive":
                pos_score = s["score"]
            elif norm == "negative":
                neg_score = s["score"]

        # Signed score: ranges from -1.0 to +1.0
        signed_score = pos_score - neg_score

        return ArticleSentiment(
            title=text[:100],
            sentiment_label=label,
            sentiment_score=signed_score,
            confidence=confidence,
        )

    def score_articles(self, articles: List[Dict[str, Any]]) -> List[ArticleSentiment]:
        """Score a list of article dicts from cached datasets.

        Each article should have 'title' and optionally 'summary'.
        Uses batch processing for efficiency.
        """
        from .data_parsers import extract_article_text

        results = []
        for article in articles:
            text = extract_article_text(article)
            if not text.strip():
                continue
            sentiment = self.score_text(text)
            sentiment.title = article.get('title', text[:100])
            results.append(sentiment)
        return results

    def aggregate(
        self,
        ticker: str,
        date: str,
        sentiments: List[ArticleSentiment],
    ) -> AggregatedSentiment:
        """Compute aggregated sentiment metrics from individual article scores.

        Args:
            ticker: Stock ticker or "GLOBAL" for macro news.
            date: Trade date string.
            sentiments: List of per-article sentiment results.

        Returns:
            AggregatedSentiment with averages, percentages, and weighted score.
        """
        if not sentiments:
            return AggregatedSentiment(
                ticker=ticker,
                date=date,
                model_name=self.model_key,
                num_articles=0,
                avg_score=0.0,
                positive_pct=0.0,
                negative_pct=0.0,
                neutral_pct=0.0,
                weighted_score=0.0,
            )

        n = len(sentiments)
        scores = [s.sentiment_score for s in sentiments]
        labels = [s.sentiment_label for s in sentiments]

        avg_score = sum(scores) / n
        positive_pct = labels.count("positive") / n
        negative_pct = labels.count("negative") / n
        neutral_pct = labels.count("neutral") / n

        # Weighted score: give more recent articles higher weight
        # (articles are typically ordered by publish date, most recent first)
        weights = [1.0 / (i + 1) for i in range(n)]
        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight

        return AggregatedSentiment(
            ticker=ticker,
            date=date,
            model_name=self.model_key,
            num_articles=n,
            avg_score=avg_score,
            positive_pct=positive_pct,
            negative_pct=negative_pct,
            neutral_pct=neutral_pct,
            weighted_score=weighted_score,
            article_sentiments=sentiments,
        )
