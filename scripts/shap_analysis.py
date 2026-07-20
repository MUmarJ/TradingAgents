#!/usr/bin/env python3
"""SHAP feature importance analysis for the XGBoost trading signal model.

Builds the full training set, trains XGBoost, computes exact SHAP values
via TreeExplainer, and identifies the top N features for pruning.

Outputs:
  - results/shap_analysis/shap_bar.png         - Mean |SHAP| bar chart
  - results/shap_analysis/shap_summary.png     - Beeswarm plot
  - results/shap_analysis/shap_fold_stability.png - Stability across CV folds
  - results/shap_analysis/feature_ranking.csv   - Full ranking table
  - tradingagents/models/selected_features.json - Top N features for pruning

Usage:
    python -m scripts.shap_analysis --top-n 20 --tickers AMBA
    python -m scripts.shap_analysis --top-n 15  # all available tickers
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.models.feature_engineering import FeatureExtractor
from tradingagents.models.ml_trainer import MLTrainer
from tradingagents.models.sentiment import FinancialSentimentModel


def build_full_dataset(results_dir: str, tickers: list):
    """Build the complete feature matrix using all available data."""
    print("Loading sentiment model...")
    sentiment_model = FinancialSentimentModel("deberta-finance")
    extractor = FeatureExtractor(sentiment_model=sentiment_model)
    trainer = MLTrainer("xgboost")

    print(f"Building training set from {len(tickers)} ticker(s)...")
    df = trainer.build_training_set(
        results_dir=results_dir,
        tickers=tickers,
        feature_extractor=extractor,
    )
    return df, trainer


def analyze_fold_stability(trainer: MLTrainer, df: pd.DataFrame, top_n: int):
    """Compute SHAP rankings for each TimeSeriesSplit fold.

    Returns a DataFrame with fold columns and feature rows showing rank.
    """
    from sklearn.model_selection import TimeSeriesSplit
    import xgboost as xgb

    feature_names = trainer.feature_names
    X = df[feature_names].fillna(0)
    y = df["_label"]

    n_splits = min(3, len(df) // 5)
    if n_splits < 2:
        print("  Too few samples for fold stability analysis")
        return None

    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_rankings = {}

    for fold_idx, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]

        if len(y_train.unique()) < 2:
            continue

        model = xgb.XGBClassifier(
            n_estimators=150, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            eval_metric="logloss", random_state=42,
        )
        model.fit(X_train, y_train)

        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_train)
        if isinstance(sv, list):
            sv = sv[1]

        mean_abs = np.abs(sv).mean(axis=0)
        ranked = sorted(
            zip(feature_names, mean_abs),
            key=lambda x: x[1], reverse=True,
        )

        for rank, (name, _) in enumerate(ranked, 1):
            if name not in fold_rankings:
                fold_rankings[name] = {}
            fold_rankings[name][f"fold_{fold_idx}"] = rank

    if not fold_rankings:
        return None

    stability_df = pd.DataFrame(fold_rankings).T
    stability_df["mean_rank"] = stability_df.mean(axis=1)
    fold_cols = [c for c in stability_df.columns if c.startswith("fold_")]
    stability_df["rank_std"] = stability_df[fold_cols].std(axis=1)
    stability_df = stability_df.sort_values("mean_rank")

    print(f"\n  Top {top_n} by mean rank across {n_splits} folds:")
    print(f"  {'Feature':<40s} {'Mean Rank':>10s} {'Std':>8s} {'Stable?':>8s}")
    for name, row in stability_df.head(top_n).iterrows():
        stable = "YES" if row["rank_std"] < top_n else "no"
        print(f"  {name:<40s} {row['mean_rank']:>10.1f} {row['rank_std']:>8.1f} {stable:>8s}")

    return stability_df


def plot_fold_stability(stability_df: pd.DataFrame, top_n: int):
    """Create a heatmap showing feature rankings across folds."""
    fold_cols = [c for c in stability_df.columns if c.startswith("fold_")]
    top_features = stability_df.head(top_n).index.tolist()

    data = stability_df.loc[top_features, fold_cols].values

    fig, ax = plt.subplots(figsize=(max(6, len(fold_cols) * 1.5), max(8, top_n * 0.4)))
    im = ax.imshow(data, cmap="YlOrRd_r", aspect="auto")

    ax.set_xticks(range(len(fold_cols)))
    ax.set_xticklabels(fold_cols)
    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features)

    for i in range(len(top_features)):
        for j in range(len(fold_cols)):
            ax.text(j, i, f"{int(data[i, j])}", ha="center", va="center", fontsize=8)

    ax.set_title(f"Feature Rank Stability Across {len(fold_cols)} CV Folds\n(lower rank = more important)")
    fig.colorbar(im, ax=ax, label="Rank")
    plt.tight_layout()
    return fig


def analyze_shap(trainer: MLTrainer, df: pd.DataFrame, top_n: int, output_dir: Path):
    """Run full SHAP analysis and generate all outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    feature_names = trainer.feature_names
    X = df[feature_names].fillna(0)
    y = df["_label"]

    print(f"\nDataset: {len(df)} samples, {len(feature_names)} features")
    print(f"Feature-to-sample ratio: {len(feature_names)/len(df):.1f}:1")
    print(f"Label distribution: {int(y.sum())} up, {int(len(y) - y.sum())} down")

    # 1. Train final model on all data
    metrics = trainer.train(df)
    print(f"CV accuracy: {metrics['cv_accuracy']:.2%} +/- {metrics['cv_std']:.2%}")

    # 2. Compute SHAP values
    print("\nComputing SHAP values (TreeExplainer)...")
    sv, explainer, X = trainer.shap_values_raw()

    mean_abs_shap = np.abs(sv).mean(axis=0)

    # 3. Rank features
    ranking = sorted(
        zip(feature_names, mean_abs_shap),
        key=lambda x: x[1],
        reverse=True,
    )

    print(f"\n{'=' * 60}")
    print(f"Top {top_n} features by mean |SHAP value|:")
    print(f"{'=' * 60}")
    for i, (name, val) in enumerate(ranking[:top_n], 1):
        print(f"  {i:>2}. {name:<40s} {val:.6f}")

    print(f"\n{'=' * 60}")
    print(f"Bottom 10 features (candidates for removal):")
    print(f"{'=' * 60}")
    for name, val in ranking[-10:]:
        print(f"      {name:<40s} {val:.6f}")

    # 4. Save full ranking CSV
    ranking_df = pd.DataFrame(ranking, columns=["feature", "mean_abs_shap"])
    ranking_df["rank"] = range(1, len(ranking_df) + 1)
    ranking_df.to_csv(output_dir / "feature_ranking.csv", index=False)
    print(f"\nFull ranking saved to {output_dir / 'feature_ranking.csv'}")

    # 5. Bar plot
    fig, ax = plt.subplots(figsize=(10, max(8, top_n * 0.4)))
    top_names = [r[0] for r in ranking[:top_n]][::-1]
    top_vals = [r[1] for r in ranking[:top_n]][::-1]
    ax.barh(top_names, top_vals)
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(f"Top {top_n} Features \u2014 SHAP TreeExplainer (n={len(df)} samples)")
    plt.tight_layout()
    fig.savefig(output_dir / "shap_bar.png", dpi=150)
    plt.close(fig)
    print(f"Bar plot saved to {output_dir / 'shap_bar.png'}")

    # 6. Beeswarm / summary plot
    plt.figure(figsize=(10, max(8, top_n * 0.4)))
    shap.summary_plot(sv, X, feature_names=feature_names,
                      max_display=top_n, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / "shap_summary.png", dpi=150)
    plt.close("all")
    print(f"Summary plot saved to {output_dir / 'shap_summary.png'}")

    # 7. Fold stability analysis
    print("\nAnalyzing SHAP stability across CV folds...")
    fold_stability = analyze_fold_stability(trainer, df, top_n)

    if fold_stability is not None:
        fig = plot_fold_stability(fold_stability, top_n)
        fig.savefig(output_dir / "shap_fold_stability.png", dpi=150)
        plt.close(fig)
        print(f"Fold stability heatmap saved to {output_dir / 'shap_fold_stability.png'}")

    # 8. Write selected_features.json
    selected = [name for name, _ in ranking[:top_n]]

    features_json = {
        "version": 1,
        "generated_at": datetime.now().isoformat(),
        "method": "shap_treexplainer",
        "n_samples": len(df),
        "n_original_features": len(feature_names),
        "top_n": top_n,
        "feature_to_sample_ratio": round(top_n / len(df), 2),
        "cv_accuracy": round(metrics["cv_accuracy"], 4),
        "features": selected,
        "ranking": [{"feature": n, "mean_abs_shap": round(float(v), 6)}
                    for n, v in ranking],
    }

    features_path = Path(__file__).parent.parent / "tradingagents" / "models" / "selected_features.json"
    with open(features_path, "w") as f:
        json.dump(features_json, f, indent=2)
    print(f"\nSelected features written to {features_path}")

    return ranking


def main():
    parser = argparse.ArgumentParser(description="SHAP feature importance analysis")
    parser.add_argument("--top-n", type=int, default=20,
                        help="Number of top features to select (default: 20)")
    parser.add_argument("--tickers", type=str, default=None,
                        help="Comma-separated tickers (default: all available)")
    parser.add_argument("--results-dir", type=str, default="./results",
                        help="Results directory (default: ./results)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: results/shap_analysis)")
    args = parser.parse_args()

    results_dir = args.results_dir
    output_dir = Path(args.output_dir or f"{results_dir}/shap_analysis")

    # Discover tickers
    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",")]
    else:
        datasets_dir = Path(results_dir) / "datasets"
        if not datasets_dir.exists():
            print(f"ERROR: No datasets directory at {datasets_dir}")
            sys.exit(1)
        tickers = sorted([
            d.name for d in datasets_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

    print("SHAP Analysis")
    print(f"{'=' * 60}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Top N: {args.top_n}")
    print(f"Results dir: {results_dir}")
    print(f"Output dir: {output_dir}")

    df, trainer = build_full_dataset(results_dir, tickers)

    if df.empty:
        print("ERROR: No training data found. Ensure cached datasets exist.")
        sys.exit(1)

    ranking = analyze_shap(trainer, df, args.top_n, output_dir)

    print(f"\nDone. Selected {args.top_n} features from {len(trainer.feature_names)} original.")
    print(f"New feature-to-sample ratio: {args.top_n}/{len(df)} = {args.top_n / len(df):.1f}:1")


if __name__ == "__main__":
    main()
