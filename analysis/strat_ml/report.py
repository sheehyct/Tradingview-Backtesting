"""Phases 3-5 of the spec: baseline stats, clustering, LightGBM + SHAP, a shallow tree, and one
self-contained HTML report readable on a phone.

Input: analysis/strat_ml/data/events.parquet (Phase 2). Output: analysis/strat_ml/reports/
strat_ml_report_<date>.html plus report_numbers_<date>.json (the tables as data).

Everything here is exploratory. Overfitting and noise are accepted (spec); every table carries
its sample size; the model is scored on a TIME split (fit on triggers before 2025-01-01, read on
2025-2026) so "did it hold up recently" is visible. Findings are hypotheses to look at by eye.

Labels: r10 = r_managed_10 (the trade's result in R after 10 daily bars with the setup-bar stop
and the T1 target, else marked at the close); win = r10 > 0; tgt = target touched before the
stop (rows with a target only).
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.strat_ml.events import EVENTS_PATH  # noqa: E402

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
SPLIT_DATE = "2025-01-01"
MIN_CELL = 100  # cells under this are greyed in every table
RNG = 0

# validated reference palette (dataviz skill): slot 1 blue, 2 orange, 3 aqua; neutral ink
C1, C2, C3, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e"

CAT_FEATURES = [
    "asset_class",
    "direction",
    "pattern",
    "family",
    "t1_source",
    "bar2_type",
    "w_partial_type",
    "m_partial_type",
    "w_prev_type",
    "m_prev_type",
    "h4_partial_type",
    "h1_prev_type",
    "btc_day_partial_type",
]
NUM_FEATURES = [
    "liq_tier",
    "liq_rank",
    "symbol_age_days",
    "setup_range_atr",
    "stop_atr",
    "stop_alt_r",
    "t1_dist_r",
    "t1_dist_atr",
    "has_target",
    "atr_pct_1y",
    "setup_color",
    "setup_dcr",
    "setup_third",
    "setup_strict",
    "w_bias",
    "m_bias",
    "tfc_score",
    "bias_score",
    "breaks_week_too",
    "breaks_month_too",
    "h4_broke_before",
    "relvol_d1",
    "relvol_prev_hour",
    "funding_last",
    "funding_7d",
    "funding_pct_1y",
    "btc_w_bias",
    "btc_m_bias",
    "btc_rv30_pct",
    "day_of_week",
    "hours_since_daily_open",
]
# known at entry but MECHANICAL: a target 0.3R away is touched far more often than one 3R away.
# Model A (the money question) excludes these; model B includes them to show the effect.
GEOMETRY = ["t1_dist_r", "t1_dist_atr", "t1_source", "has_target", "stop_alt_r"]
# LEAK, never a feature: "the same day also broke the other side" is known at the END of the
# day, not at the trigger hour (it was the second strongest feature before it was caught).
LEAKS = ["opposite_also_triggered"]
CONTEXT_CAT = [c for c in CAT_FEATURES if c not in GEOMETRY]
CONTEXT_NUM = [c for c in NUM_FEATURES if c not in GEOMETRY]
PLAIN = {
    "asset_class": "major (BTC/ETH) or alt",
    "direction": "long or short",
    "pattern": "STRAT pattern name",
    "family": "reversal / continuation / inside / outside",
    "t1_source": "where the target came from (bar 0 wick, week level, month level, none)",
    "bar2_type": "type of the bar before the setup bar",
    "w_partial_type": "the week so far, as a bar type, at the trigger hour",
    "m_partial_type": "the month so far, as a bar type",
    "w_prev_type": "last complete week's bar type",
    "m_prev_type": "last complete month's bar type",
    "h4_partial_type": "the 4-hour bar so far at the trigger",
    "h1_prev_type": "the hour before the trigger, as a bar type",
    "btc_day_partial_type": "BTC's day so far, as a bar type",
    "liq_tier": "liquidity tier (1 = top 10 by 30-day volume, 2 = 11-50, 3 = rest)",
    "liq_rank": "liquidity rank (1 = most traded)",
    "symbol_age_days": "days since the perp listed",
    "setup_range_atr": "setup bar range in ATRs",
    "stop_atr": "stop distance in ATRs (same as the setup range here)",
    "stop_alt_r": "the skill's bar-0 stop, in R (1.0 unless an inside break)",
    "t1_dist_r": "distance to the target in R (reward-to-risk)",
    "t1_dist_atr": "distance to the target in ATRs",
    "has_target": "a target exists",
    "atr_pct_1y": "how volatile the coin is vs its own last year (0-1)",
    "setup_color": "setup bar green (+1) or red (-1)",
    "setup_dcr": "where the setup bar closed in its range (0 = low, 1 = high)",
    "setup_third": "setup bar closed in the far third (hammer / shooter shape)",
    "setup_strict": "hammer / shooter shape with a sliver wick",
    "w_bias": "week green (+1) or red (-1) at the trigger",
    "m_bias": "month green (+1) or red (-1) at the trigger",
    "tfc_score": "share of week + month pushing the trade's way (type and colour)",
    "bias_score": "share of week + month coloured the trade's way",
    "breaks_week_too": "the same break also breaks the week's level",
    "breaks_month_too": "the same break also breaks the month's level",
    "h4_broke_before": "the 4-hour bar had already broken its level",
    "relvol_d1": "setup day volume vs the 20-day average",
    "relvol_prev_hour": "previous hour's volume vs the week's hourly average",
    "funding_last": "last funding rate",
    "funding_7d": "7-day average funding",
    "funding_pct_1y": "funding vs the last year (0-1)",
    "btc_w_bias": "BTC's week green / red",
    "btc_m_bias": "BTC's month green / red",
    "btc_rv30_pct": "BTC 30-day realized volatility vs the last year (0-1)",
    "day_of_week": "0 = Monday .. 6 = Sunday",
    "hours_since_daily_open": "hour of the day (UTC) the break happened",
    "opposite_also_triggered": "the same day also broke the other side",
}


# ----------------------------------------------------------------------------- helpers


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return centre - half, centre + half


def load_events(path: Path = EVENTS_PATH) -> pd.DataFrame:
    ev = pd.read_parquet(path)
    ev = ev[ev["r_managed_10"].notna()].copy()  # drop censored rows (no 10-bar outcome)
    ev["r10"] = ev["r_managed_10"]
    # Codex PR #3 P2: bounds from the pre-split rows only, applied to both periods
    train = ev["day_ts"] < pd.Timestamp(SPLIT_DATE, tz="UTC")
    lo, hi = ev.loc[train, "r10"].quantile([0.005, 0.995])
    ev["r10_w"] = ev["r10"].clip(lo, hi)  # winsorized for means
    ev["win"] = ev["r10"] > 0
    ev["tgt"] = ev["first_touch"] == "target"
    ev["year"] = ev["day_ts"].dt.year
    ev["hour_bucket"] = pd.cut(
        ev["hours_since_daily_open"],
        [-1, 0, 5, 11, 17, 23],
        labels=["00", "01-05", "06-11", "12-17", "18-23"],
    )
    for c in CAT_FEATURES:
        ev[c] = ev[c].astype("object").fillna("none").astype("category")
    for c in NUM_FEATURES:
        ev[c] = pd.to_numeric(ev[c], errors="coerce").astype("float64")
    return ev


def cell_stats(g: pd.DataFrame) -> dict:
    n = len(g)
    wins = int(g["win"].sum())
    lo, hi = wilson(wins, n)
    ht = g[g["has_target"] > 0]
    return {
        "n": n,
        "win_pct": 100 * wins / n if n else np.nan,
        "win_lo": 100 * lo,
        "win_hi": 100 * hi,
        "tgt_pct": 100 * ht["tgt"].mean() if len(ht) else np.nan,
        "n_target": len(ht),
        "mean_r": g["r10_w"].mean() if n else np.nan,
        "median_r": g["r10"].median() if n else np.nan,
        "mfe_med": g["mfe_r_10"].median() if n else np.nan,
        "mae_med": g["mae_r_10"].median() if n else np.nan,
    }


def grouped(ev: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in ev.groupby(keys, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        rows.append({**dict(zip(keys, key)), **cell_stats(g)})
    return pd.DataFrame(rows)


def fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)


# ----------------------------------------------------------------------------- phase 1: baseline


def baseline(ev: pd.DataFrame) -> dict:
    out = {}
    out["pattern_class"] = grouped(ev, ["pattern", "asset_class"]).sort_values(
        ["pattern", "asset_class"]
    )
    out["pattern_class_dir"] = grouped(ev, ["pattern", "asset_class", "direction"])
    out["year_class"] = grouped(ev, ["year", "asset_class"])
    out["family_dir"] = grouped(ev, ["family", "direction"])
    out["tfc"] = grouped(ev, ["tfc_score", "asset_class"])
    out["bias"] = grouped(ev, ["bias_score", "asset_class"])
    out["hour"] = grouped(ev, ["hour_bucket", "asset_class"])
    out["liq"] = grouped(ev, ["liq_tier", "direction"])
    out["dow"] = grouped(ev, ["day_of_week"])
    out["t1_source"] = grouped(ev, ["t1_source", "asset_class"])
    out["breaks_week"] = grouped(ev, ["breaks_week_too", "family"])
    out["setup_shape"] = grouped(ev, ["setup_third", "family"])
    ev["rr_bucket"] = pd.cut(
        ev["t1_dist_r"], [0, 0.5, 1, 2, 3, 1e9], labels=["<0.5R", "0.5-1R", "1-2R", "2-3R", ">3R"]
    )
    out["rr"] = grouped(ev[ev["has_target"] > 0], ["rr_bucket", "family"])
    out["overall"] = pd.DataFrame([{"group": "all", **cell_stats(ev)}])
    return out


def chart_pattern_r(tab: pd.DataFrame) -> str:
    pats = sorted(tab["pattern"].unique(), key=lambda p: -tab[tab["pattern"] == p]["n"].sum())
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    y = np.arange(len(pats))
    for off, cls, col in ((-0.2, "major", C1), (0.2, "alt", C2)):
        vals = [
            tab[(tab["pattern"] == p) & (tab["asset_class"] == cls)]["mean_r"].sum() for p in pats
        ]
        ax.barh(y + off, vals, height=0.38, color=col, label=cls, linewidth=0)
    ax.set_yticks(y)
    ax.set_yticklabels(pats, fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.set_xlabel("mean result after 10 daily bars, in R (winsorized)", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title(
        "Mean R by pattern: majors vs alts (hypothesis view, see table for n)",
        fontsize=10,
        color=INK,
        loc="left",
    )
    style_axes(ax)
    ax.xaxis.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.yaxis.grid(False)
    return fig_to_b64(fig)


def chart_year(tab: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for cls, col in (("major", C1), ("alt", C2)):
        t = tab[tab["asset_class"] == cls].sort_values("year")
        ax.plot(
            t["year"], t["win_pct"], color=col, linewidth=2, marker="o", markersize=5, label=cls
        )
        ax.fill_between(t["year"], t["win_lo"], t["win_hi"], color=col, alpha=0.15, linewidth=0)
    ax.axhline(50, color=MUTED, linewidth=1, linestyle=":")
    ax.set_ylabel("% of triggers that ended positive (10 bars)", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title(
        "Win rate by year with 95% bands: the regime question", fontsize=10, color=INK, loc="left"
    )
    style_axes(ax)
    return fig_to_b64(fig)


def chart_hist(ev: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for cls, col in (("major", C1), ("alt", C2)):
        x = ev[ev["asset_class"] == cls]["r10"].clip(-1.5, 6)
        ax.hist(x, bins=60, density=True, histtype="step", color=col, linewidth=2, label=cls)
    ax.set_xlabel(
        "result after 10 daily bars, in R (clipped at -1.5 and +6)", color=MUTED, fontsize=9
    )
    ax.set_ylabel("density", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title(
        "The shape of outcomes: a spike at -1R (stopped) and a long right tail",
        fontsize=10,
        color=INK,
        loc="left",
    )
    style_axes(ax)
    return fig_to_b64(fig)


# ----------------------------------------------------------------------------- phase 2: clustering


def clustering(ev: pd.DataFrame, k: int = 6) -> tuple[pd.DataFrame, pd.DataFrame]:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    feats = [f for f in NUM_FEATURES if f not in ("liq_rank",)]
    x = ev[feats].copy()
    x = x.fillna(x.median(numeric_only=True))
    x = x.clip(x.quantile(0.01), x.quantile(0.99), axis=1)  # one outlier row must not own a cluster
    scaler = StandardScaler().fit(x)
    z = scaler.transform(x)
    fit_idx = ev.sample(min(150_000, len(ev)), random_state=RNG).index
    km = KMeans(n_clusters=k, n_init=4, random_state=RNG).fit(z[ev.index.get_indexer(fit_idx)])
    ev["cluster"] = km.predict(z)
    tab = grouped(ev, ["cluster"]).sort_values("mean_r", ascending=False)
    centres = pd.DataFrame(km.cluster_centers_, columns=feats)
    desc_rows = []
    for c in range(k):
        dev = centres.loc[c].abs().sort_values(ascending=False).head(4)
        words = []
        for f in dev.index:
            raw = scaler.inverse_transform(centres.loc[[c]].to_numpy())[0][feats.index(f)]
            direction = "high" if centres.loc[c, f] > 0 else "low"
            words.append(f"{direction} {PLAIN.get(f, f)} (~{raw:.2f})")
        desc_rows.append({"cluster": c, "what_marks_it": "; ".join(words)})
    return tab, pd.DataFrame(desc_rows)


# ----------------------------------------------------------------------------- phase 3: LightGBM + SHAP


def design_matrix(ev: pd.DataFrame, cats: list[str], nums: list[str]) -> pd.DataFrame:
    x = ev[cats + nums].copy()
    for c in cats:
        x[c] = x[c].astype("category")
    return x


def _lgb_params() -> dict:
    return dict(
        n_estimators=400,
        learning_rate=0.04,
        num_leaves=31,
        min_child_samples=300,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        reg_lambda=2.0,
        random_state=RNG,
        verbose=-1,
    )


def decile_table(df: pd.DataFrame, score: str, by: list[str] | None = None) -> pd.DataFrame:
    df = df.copy()
    df["decile"] = pd.qcut(df[score].rank(method="first"), 10, labels=False) + 1
    keys = (by or []) + ["decile"]
    return (
        df.groupby(keys, observed=True)
        .agg(
            n=(score, "size"),
            model=(score, "mean"),
            win_pct=("win", lambda s: 100 * s.mean()),
            tgt_pct=("tgt", lambda s: 100 * s.mean()),
            mean_r=("r10_w", "mean"),
            median_r=("r10", "median"),
            alt_share=("asset_class", lambda s: 100 * (s == "alt").mean()),
        )
        .reset_index()
    )


def lgbm_phase(ev: pd.DataFrame, log=print) -> dict:
    import lightgbm as lgb
    import shap
    from sklearn.metrics import roc_auc_score

    res: dict = {}
    split = pd.Timestamp(SPLIT_DATE, tz="UTC")
    train = (ev["day_ts"] < split).to_numpy()
    test = ~train
    # ---- model A: the money question. Regression on winsorized R, CONTEXT features only.
    xa = design_matrix(ev, CONTEXT_CAT, CONTEXT_NUM)
    y = ev["r10_w"].to_numpy()
    t0 = time.time()
    reg = lgb.LGBMRegressor(**_lgb_params()).fit(xa[train], y[train])
    pred = reg.predict(xa[test])
    ss_res = float(((y[test] - pred) ** 2).sum())
    ss_tot = float(((y[test] - y[test].mean()) ** 2).sum())
    pred_tr = reg.predict(xa[train])
    r2_tr = 1 - float(((y[train] - pred_tr) ** 2).sum()) / float(
        ((y[train] - y[train].mean()) ** 2).sum()
    )
    res["reg"] = {
        "n_train": int(train.sum()),
        "n_test": int(test.sum()),
        "r2_train": r2_tr,
        "r2_test": 1 - ss_res / ss_tot,
        "corr_test": float(np.corrcoef(pred, y[test])[0, 1]),
        "seconds": round(time.time() - t0),
    }
    te = ev[test].copy()
    te["pred_r"] = pred
    res["decile_reg"] = decile_table(te, "pred_r")
    res["decile_reg_class"] = decile_table(te, "pred_r", ["asset_class"])
    res["decile_reg_year"] = decile_table(te, "pred_r", ["year"])
    log(f"  model A (context -> R): R2 train {r2_tr:.4f} test {res['reg']['r2_test']:.4f}")
    samp = xa[test].sample(min(20_000, int(test.sum())), random_state=RNG)
    explainer = shap.TreeExplainer(reg)
    sv = explainer.shap_values(samp)
    imp = pd.DataFrame(
        {"feature": samp.columns, "mean_abs_shap": np.abs(sv).mean(axis=0)}
    ).sort_values("mean_abs_shap", ascending=False)
    imp["plain"] = imp["feature"].map(PLAIN)
    res["importance"] = imp
    res["shap_chart"] = chart_importance(imp.head(15), "predicted R")
    top = [f for f in imp["feature"].head(6)]
    res["dependence_charts"] = [chart_dependence(samp, sv, f, list(samp.columns), "R") for f in top]
    small = samp.sample(min(1500, len(samp)), random_state=RNG)
    try:
        iv = explainer.shap_interaction_values(small)
        m = np.abs(iv).mean(axis=0)
        np.fill_diagonal(m, 0)
        cols = list(small.columns)
        pairs = sorted(
            (
                (m[i, j], cols[i], cols[j])
                for i in range(len(cols))
                for j in range(i + 1, len(cols))
            ),
            reverse=True,
        )
        res["interactions"] = pd.DataFrame(
            [
                {
                    "feature_a": PLAIN.get(a, a),
                    "feature_b": PLAIN.get(b, b),
                    "mean_abs_interaction": v,
                }
                for v, a, b in pairs[:10]
            ]
        )
    except Exception as e:  # shap versions differ; the report says so instead of dying
        res["interactions"] = pd.DataFrame(
            [{"feature_a": "n/a", "feature_b": str(e)[:80], "mean_abs_interaction": np.nan}]
        )
    # ---- model B: target-before-stop with GEOMETRY included (the mechanical effect, shown on purpose)
    ht = (ev["has_target"] > 0).to_numpy()
    xb = design_matrix(ev, CAT_FEATURES, NUM_FEATURES)
    yb = ev["tgt"].astype(int).to_numpy()
    clf = lgb.LGBMClassifier(**_lgb_params()).fit(xb[train & ht], yb[train & ht])
    p_tr = clf.predict_proba(xb[train & ht])[:, 1]
    p_te = clf.predict_proba(xb[test & ht])[:, 1]
    res["clf"] = {
        "n_train": int((train & ht).sum()),
        "n_test": int((test & ht).sum()),
        "base_rate_test": float(yb[test & ht].mean()),
        "auc_train": float(roc_auc_score(yb[train & ht], p_tr)),
        "auc_test": float(roc_auc_score(yb[test & ht], p_te)),
    }
    teb = ev[test & ht].copy()
    teb["p"] = p_te
    res["decile_clf"] = decile_table(teb, "p")
    sampb = xb[test & ht].sample(min(10_000, int((test & ht).sum())), random_state=RNG)
    svb = shap.TreeExplainer(clf).shap_values(sampb)
    if isinstance(svb, list):
        svb = svb[1]
    impb = pd.DataFrame(
        {"feature": sampb.columns, "mean_abs_shap": np.abs(svb).mean(axis=0)}
    ).sort_values("mean_abs_shap", ascending=False)
    impb["plain"] = impb["feature"].map(PLAIN)
    res["importance_clf"] = impb
    clf_c = lgb.LGBMClassifier(**_lgb_params()).fit(xa[train & ht], yb[train & ht])
    res["clf_context"] = {
        "auc_train": float(
            roc_auc_score(yb[train & ht], clf_c.predict_proba(xa[train & ht])[:, 1])
        ),
        "auc_test": float(roc_auc_score(yb[test & ht], clf_c.predict_proba(xa[test & ht])[:, 1])),
    }
    log(
        f"  model B (all -> target first): AUC test {res['clf']['auc_test']:.3f};"
        f" model C (context -> target first): AUC test {res['clf_context']['auc_test']:.3f}"
    )
    return res


def chart_importance(imp: pd.DataFrame, what: str = "predicted R") -> str:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    y = np.arange(len(imp))
    ax.barh(y, imp["mean_abs_shap"], color=C1, linewidth=0, height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([PLAIN.get(f, f) for f in imp["feature"]], fontsize=8.5, color=INK)
    ax.invert_yaxis()
    ax.set_xlabel(f"mean |SHAP| (how much the feature moves the {what})", color=MUTED, fontsize=9)
    ax.set_title(
        f"What the model leans on ({what}, 2025-26 test rows, context only)",
        fontsize=10,
        color=INK,
        loc="left",
    )
    style_axes(ax)
    ax.xaxis.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.yaxis.grid(False)
    return fig_to_b64(fig)


def chart_dependence(
    samp: pd.DataFrame, sv: np.ndarray, feat: str, cols: list[str], unit: str = "R"
) -> str:
    j = cols.index(feat)
    xv = samp[feat]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    if str(xv.dtype) == "category":
        cats = list(xv.cat.categories)
        vals = [sv[(xv == c).to_numpy(), j] for c in cats]
        pos = np.arange(len(cats))
        ax.boxplot(
            vals,
            positions=pos,
            widths=0.5,
            showfliers=False,
            medianprops={"color": C2, "linewidth": 2},
            boxprops={"color": C1},
            whiskerprops={"color": MUTED},
            capprops={"color": MUTED},
        )
        ax.set_xticks(pos)
        ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8)
    else:
        idx = np.random.default_rng(RNG).choice(len(xv), min(5000, len(xv)), replace=False)
        ax.scatter(xv.to_numpy()[idx], sv[idx, j], s=6, alpha=0.35, color=C1, linewidths=0)
        lo, hi = np.nanpercentile(xv, [0.5, 99.5])
        ax.set_xlim(lo, hi)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set_ylabel(f"SHAP (push on predicted {unit})", color=MUTED, fontsize=8.5)
    ax.set_title(f"{PLAIN.get(feat, feat)}", fontsize=10, color=INK, loc="left")
    style_axes(ax)
    return fig_to_b64(fig)


# ----------------------------------------------------------------------------- phase 4: shallow tree


def shallow_tree(ev: pd.DataFrame, depth: int = 3) -> tuple[str, pd.DataFrame]:
    """Depth-3 regression tree on CONTEXT features, target = winsorized R. Leaves = sayable rules."""
    from sklearn.tree import DecisionTreeRegressor, export_text

    split = pd.Timestamp(SPLIT_DATE, tz="UTC")
    x = pd.get_dummies(ev[CONTEXT_CAT + CONTEXT_NUM], columns=CONTEXT_CAT, dtype=float)
    x = x.fillna(x.median(numeric_only=True))
    y = ev["r10_w"].to_numpy()
    train = (ev["day_ts"] < split).to_numpy()
    tree = DecisionTreeRegressor(max_depth=depth, min_samples_leaf=5000, random_state=RNG).fit(
        x[train], y[train]
    )
    names = [c.replace("_", " ") for c in x.columns]
    text = export_text(tree, feature_names=names, max_depth=depth, decimals=3)
    leaf_tr = tree.apply(x[train])
    leaf_te = tree.apply(x[~train])
    win = ev["win"].to_numpy()
    rows = []
    paths = leaf_paths(tree, list(x.columns), CONTEXT_CAT)
    for leaf in np.unique(leaf_tr):
        mtr = leaf_tr == leaf
        mte = leaf_te == leaf
        rows.append(
            {
                "rule": paths.get(int(leaf), str(leaf)),
                "n_train": int(mtr.sum()),
                "mean_r_train": float(y[train][mtr].mean()),
                "n_test": int(mte.sum()),
                "mean_r_test": float(y[~train][mte].mean()) if mte.sum() else np.nan,
                "win_pct_test": 100 * float(win[~train][mte].mean()) if mte.sum() else np.nan,
            }
        )
    return text, pd.DataFrame(rows).sort_values("mean_r_train", ascending=False)


def leaf_paths(tree, cols: list[str], cats: list[str] = CAT_FEATURES) -> dict[int, str]:
    t = tree.tree_
    out: dict[int, str] = {}

    def walk(node: int, conds: list[str]):
        if t.children_left[node] == -1:
            out[node] = " AND ".join(conds) if conds else "(root)"
            return
        f = cols[t.feature[node]]
        thr = t.threshold[node]
        name = PLAIN.get(f, f)
        if any(f.startswith(c + "_") for c in cats):
            base = next(c for c in cats if f.startswith(c + "_"))
            val = f[len(base) + 1 :]
            walk(t.children_left[node], conds + [f"{PLAIN.get(base, base)} is not {val}"])
            walk(t.children_right[node], conds + [f"{PLAIN.get(base, base)} is {val}"])
        else:
            walk(t.children_left[node], conds + [f"{name} <= {thr:.2f}"])
            walk(t.children_right[node], conds + [f"{name} > {thr:.2f}"])

    walk(0, [])
    return out


# ----------------------------------------------------------------------------- phase 5: HTML


def fmt(v, kind: str) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if kind == "int":
        return f"{int(v):,}"
    if kind == "pct":
        return f"{v:.1f}%"
    if kind == "r":
        return f"{v:+.3f}"
    if kind == "f2":
        return f"{v:.2f}"
    return html.escape(str(v))


KINDS = {
    "n": "int",
    "n_target": "int",
    "n_train": "int",
    "n_test": "int",
    "win_pct": "pct",
    "tgt_pct": "pct",
    "tgt_pct_train": "pct",
    "tgt_pct_test": "pct",
    "alt_share": "pct",
    "mean_r": "r",
    "median_r": "r",
    "mean_r_test": "r",
    "mean_r_train": "r",
    "win_pct_test": "pct",
    "model": "r",
    "mfe_med": "f2",
    "mae_med": "f2",
    "p_mean": "f2",
    "pred_mean": "r",
    "mean_abs_shap": "f2",
    "mean_abs_interaction": "f2",
}
HEAD = {
    "n": "n",
    "n_target": "n with target",
    "win_pct": "win %",
    "win_lo": "ci lo",
    "win_hi": "ci hi",
    "tgt_pct": "target first %",
    "mean_r": "mean R",
    "median_r": "median R",
    "mfe_med": "median MFE (R)",
    "mae_med": "median MAE (R)",
    "p_mean": "model prob",
    "pred_mean": "model R",
    "alt_share": "alt share",
}


def table_html(df: pd.DataFrame, cols: list[str] | None = None, grey_n: str | None = "n") -> str:
    cols = cols or [c for c in df.columns if c not in ("win_lo", "win_hi")]
    head = "".join(f"<th>{html.escape(HEAD.get(c, c.replace('_', ' ')))}</th>" for c in cols)
    body = []
    for _, r in df.iterrows():
        grey = grey_n in df.columns and pd.notna(r[grey_n]) and r[grey_n] < MIN_CELL
        cells = []
        for c in cols:
            v = r[c]
            txt = fmt(v, KINDS.get(c, "s"))
            if c == "win_pct" and "win_lo" in df.columns and pd.notna(r["win_lo"]):
                txt += f" <span class=ci>({r['win_lo']:.0f}-{r['win_hi']:.0f})</span>"
            cells.append(f"<td>{txt}</td>")
        body.append(f"<tr class={'grey' if grey else ''}>{''.join(cells)}</tr>")
    return f"<div class=tw><table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"


def img(b64: str) -> str:
    return f'<img src="data:image/png;base64,{b64}" alt="chart">'


CSS = """
:root{--bg:#fcfcfb;--ink:#0b0b0b;--muted:#52514e;--line:#e6e5e0;--grey:#8b8a84;--accent:#2a78d6;--box:#f3f2ee}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#1a1a19;--ink:#f0efec;--muted:#c3c2b7;--line:#33322f;--grey:#8b8a84;--accent:#3987e5;--box:#242422}}
:root[data-theme="dark"]{--bg:#1a1a19;--ink:#f0efec;--muted:#c3c2b7;--line:#33322f;--grey:#8b8a84;--accent:#3987e5;--box:#242422}
body{margin:0;padding:16px;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:760px;margin:0 auto}
h1{font-size:1.5rem;line-height:1.25;margin:.2em 0}h2{font-size:1.2rem;margin:1.6em 0 .4em;border-top:1px solid var(--line);padding-top:.8em}h3{font-size:1rem;margin:1.2em 0 .3em}
p,li{max-width:70ch}.plain{background:var(--box);border-left:3px solid var(--accent);padding:10px 12px;border-radius:6px;margin:.6em 0}
.tw{overflow-x:auto;margin:.5em 0}table{border-collapse:collapse;font-size:13px;white-space:nowrap}th,td{padding:4px 8px;border-bottom:1px solid var(--line);text-align:right}th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:600}
tr.grey td{color:var(--grey)}.ci{color:var(--muted);font-size:11px}img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff;margin:.4em 0}
pre{background:var(--box);padding:10px;border-radius:6px;overflow-x:auto;font-size:12px}small,.muted{color:var(--muted)}
"""


def build_report(log=print, events: Path = EVENTS_PATH, tag: str = "") -> Path:
    t0 = time.time()
    ev = load_events(events)
    log(f"events loaded: {len(ev):,} rows with a 10-bar outcome")
    base = baseline(ev)
    log("baseline done")
    clus_tab, clus_desc = clustering(ev)
    log("clustering done")
    ml = lgbm_phase(ev, log)
    tree_text, tree_tab = shallow_tree(ev)
    log("tree done")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d") + (f"_{tag}" if tag else "")
    REPORTS.mkdir(parents=True, exist_ok=True)
    ov = base["overall"].iloc[0]
    n_sym = ev["symbol"].nunique()
    split_n = int((ev["day_ts"] >= pd.Timestamp(SPLIT_DATE, tz="UTC")).sum())

    parts = [
        f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>STRAT ML vessel report</title><style>{CSS}</style></head><body><main>"
    ]
    parts.append(
        f"<h1>STRAT trigger research: what the data looks like</h1><p class=muted>Binance USDT-M perps, daily triggers, {ev['day_ts'].min():%Y-%m-%d} to {ev['day_ts'].max():%Y-%m-%d}. Built {stamp}. Exploratory: every number is a hypothesis to check by eye, not a result.</p>"
    )
    parts.append(
        "<div class=plain><b>How to read this page.</b> One row of data = one time a coin broke yesterday's high (long) or low (short) on the daily chart. "
        "We pretend to enter at that level, put the stop at the far side of yesterday's bar, aim at the STRAT target, and watch 10 daily bars. "
        "<b>R</b> = one unit of risk (the stop distance). <b>Win %</b> = share of rows that ended above zero. <b>Target first %</b> = share that touched the target before the stop (only rows that have a target). "
        "<b>MFE / MAE</b> = the best and worst point reached along the way, in R. Numbers in parentheses after a win % are the 95% confidence band. Grey rows have fewer than 100 samples and should be ignored. "
        "No fees, no funding paid, no sizing: these are measuring sticks, not P&amp;L.</div>"
    )
    parts.append(
        f"<h2>0. The sample</h2><div class=tw><table><tr><th>coins</th><td>{n_sym}</td></tr><tr><th>trigger rows with a 10-bar outcome</th><td>{len(ev):,}</td></tr>"
        f"<tr><th>rows with a target</th><td>{int((ev['has_target'] > 0).sum()):,}</td></tr><tr><th>rows in the test period (2025-26)</th><td>{split_n:,}</td></tr>"
        f"<tr><th>overall win %</th><td>{ov['win_pct']:.1f}% ({ov['win_lo']:.1f}-{ov['win_hi']:.1f})</td></tr><tr><th>overall target-first %</th><td>{ov['tgt_pct']:.1f}%</td></tr>"
        f"<tr><th>mean R (winsorized) / median R</th><td>{ov['mean_r']:+.3f} / {ov['median_r']:+.3f}</td></tr></table></div>"
    )
    parts.append(img(chart_hist(ev)))
    parts.append(
        "<div class=plain>The spike at -1R is every trade that hit its stop inside 10 bars. The long tail to the right is the few that ran. "
        "A mean near zero with a median near zero says the typical break is a coin flip before costs; whatever edge exists has to live in the <i>conditions</i>, which is what the rest of the page hunts for.</div>"
    )

    parts.append("<h2>1. Baseline tables (counts on every cell)</h2>")
    parts.append(
        "<h3>1a. Pattern x majors vs alts</h3>"
        + img(chart_pattern_r(base["pattern_class"]))
        + table_html(base["pattern_class"])
    )
    parts.append(
        "<div class=plain>Read across a pattern: do majors and alts behave the same? Read down: is any pattern clearly different from the rest? "
        "A pattern that looks great with 300 rows and ordinary with 30,000 is the classic overfit shape. Remember the charter: the spread is the finding, not the top cell.</div>"
    )
    parts.append("<h3>1b. Pattern x class x direction</h3>" + table_html(base["pattern_class_dir"]))
    parts.append(
        "<h3>1c. By year (regime drift)</h3>"
        + img(chart_year(base["year_class"]))
        + table_html(base["year_class"])
    )
    parts.append(
        "<div class=plain>If the win rate moves year to year more than the bands allow, the <i>market</i> is the biggest feature and any model fit on 2020-24 is being tested on a different animal in 2025-26. That is exactly what the time split below measures.</div>"
    )
    parts.append("<h3>1d. Family x direction</h3>" + table_html(base["family_dir"]))
    parts.append(
        "<h3>1e. Timeframe continuity at the trigger</h3><p class=muted>tfc_score: share of week + month whose bar type AND colour push the trade's way. bias_score: colour only.</p>"
        + table_html(base["tfc"])
        + table_html(base["bias"])
    )
    parts.append("<h3>1f. Hour of the day the break happened (UTC)</h3>" + table_html(base["hour"]))
    parts.append("<h3>1g. Liquidity tier x direction</h3>" + table_html(base["liq"]))
    parts.append("<h3>1h. Day of week (0 = Monday)</h3>" + table_html(base["dow"]))
    parts.append("<h3>1i. Where the target came from</h3>" + table_html(base["t1_source"]))
    parts.append(
        "<h3>1j. The break also broke the week's level</h3>" + table_html(base["breaks_week"])
    )
    parts.append(
        "<h3>1k. Setup bar closed in its far third (hammer / shooter shape)</h3>"
        + table_html(base["setup_shape"])
    )
    parts.append(
        "<h3>1l. Reward-to-risk of the target x family (rows with a target)</h3>"
        + table_html(base["rr"])
        + "<div class=plain>The mechanical fact of this dataset: the closer the target, the more often it is touched first, and mean R barely changes. A 90% target-first rate on a 0.3R target is not an edge, it is a small target. Any claim about a pattern has to be read next to its typical reward-to-risk.</div>"
    )

    parts.append("<h2>2. Clustering: let the features group themselves</h2>")
    parts.append(
        "<div class=plain><b>What this is.</b> K-means puts every trigger into one of 6 buckets using ONLY the 'what it looked like' columns (never the outcome). "
        "Then we look at how each bucket turned out. If some bucket is clearly better or worse, the description column says what that bucket has in common. "
        "Buckets are a lens, not a rule: the algorithm does not know what a trade is.</div>"
    )
    parts.append(table_html(clus_tab) + table_html(clus_desc, grey_n=None))

    parts.append("<h2>3. LightGBM + SHAP: which conditions move the result</h2>")
    r = ml["reg"]
    c = ml["clf"]
    cc = ml["clf_context"]
    parts.append(
        "<div class=plain><b>What this is.</b> A gradient-boosted tree model (LightGBM) is fit on triggers before 2025 and then scored on 2025-26 triggers it never saw. "
        "<b>Model A</b> is the money question: predict the result in R after 10 bars from the <i>context</i> columns only (what the week, month, 4-hour, volume, funding and BTC looked like, which pattern, how volatile, how old and how liquid the coin). "
        "It deliberately does NOT see the target distance, because a target 0.3R away is touched far more often than a target 3R away whatever the chart looks like; that is arithmetic, not edge. "
        "<b>R-squared</b> says how much of the row-to-row variation the model explains (0 = nothing, 1 = everything); for trading data a few hundredths is normal and the decile table is the honest read. "
        "<b>SHAP</b> then asks the model which columns it leaned on and in which direction.</div>"
    )
    parts.append(
        f"<div class=tw><table><tr><th>rows (train / test)</th><td>{r['n_train']:,} / {r['n_test']:,}</td></tr>"
        f"<tr><th>model A: R-squared train / test</th><td>{r['r2_train']:.4f} / {r['r2_test']:.4f}</td></tr>"
        f"<tr><th>model A: correlation of prediction with the result (test)</th><td>{r['corr_test']:.3f}</td></tr></table></div>"
    )
    parts.append(
        "<h3>3a. Model A, test period, sorted by the model's predicted R (decile 10 = most optimistic)</h3>"
        + table_html(ml["decile_reg"])
    )
    parts.append(
        "<div class=plain>This is the table that matters. If mean R climbs steadily from decile 1 to 10 on data the model never saw, the context carries real information about the outcome. "
        "If it is flat or jumbled, the model found nothing that survived the regime change. 'model' is the model's own predicted R for the decile; compare it with 'mean R', what actually happened.</div>"
    )
    parts.append("<h3>3b. The same, split majors vs alts</h3>" + table_html(ml["decile_reg_class"]))
    parts.append("<h3>3c. The same, by test year</h3>" + table_html(ml["decile_reg_year"]))
    parts.append(
        "<h3>3d. Feature importance (SHAP, model A)</h3>"
        + img(ml["shap_chart"])
        + table_html(ml["importance"].head(25), grey_n=None)
    )
    parts.append(
        "<h3>3e. Dependence: how the top features push the predicted R</h3><p class=muted>Each dot (or box) is a test-period trigger. Above the zero line = this value raised the predicted R; below = lowered it. Look for shapes (a step, a slope, a U), not for single dots.</p>"
    )
    for ch in ml["dependence_charts"]:
        parts.append(img(ch))
    parts.append(
        "<h3>3f. Strongest feature pairs (interactions, model A)</h3>"
        + table_html(ml["interactions"], grey_n=None)
    )
    parts.append(
        "<h3>3g. Model B: the geometry effect, shown on purpose</h3>"
        "<div class=plain>Model B predicts <i>target touched before the stop</i> and is allowed to see the target distance. "
        "<b>AUC</b>: 0.50 = coin flip, 1.00 = perfect. Its high score is the arithmetic above, not a trading edge: look at mean R across its deciles, which barely moves. "
        "<b>Model C</b> predicts the same label WITHOUT the geometry columns: the drop between B and C is how much of 'will it reach the target' is just how far the target is.</div>"
    )
    parts.append(
        f"<div class=tw><table><tr><th>rows with a target (train / test)</th><td>{c['n_train']:,} / {c['n_test']:,}</td></tr>"
        f"<tr><th>target-first base rate (test)</th><td>{100 * c['base_rate_test']:.1f}%</td></tr>"
        f"<tr><th>model B (with geometry): AUC train / test</th><td>{c['auc_train']:.3f} / {c['auc_test']:.3f}</td></tr>"
        f"<tr><th>model C (context only): AUC train / test</th><td>{cc['auc_train']:.3f} / {cc['auc_test']:.3f}</td></tr></table></div>"
    )
    parts.append(table_html(ml["decile_clf"]))
    parts.append(table_html(ml["importance_clf"].head(10), grey_n=None))

    parts.append("<h2>4. A three-question tree: readable rules</h2>")
    parts.append(
        "<div class=plain><b>What this is.</b> A decision tree allowed only three yes/no questions, fit on pre-2025 triggers with the context columns, predicting R. Each leaf is a rule you can say out loud. "
        "The test columns show whether the rule still held in 2025-26. Rules are prompts for looking at charts, not trade plans.</div>"
    )
    parts.append(table_html(tree_tab, grey_n="n_test"))
    parts.append(
        f"<details><summary>raw tree text</summary><pre>{html.escape(tree_text)}</pre></details>"
    )

    parts.append("<h2>5. Caveats that travel with every number above</h2><ul>")
    parts.append(
        "<li>No fees, no funding paid, fills at the level, every trigger taken, no sizing. Real trading subtracts costs from every row.</li>"
    )
    parts.append(
        "<li>Ties inside one hourly bar (stop and target in the same hour) are resolved stop-first, and a stop touched in the trigger hour is counted against the trade; both are flagged in the data (about 1% of rows).</li>"
    )
    parts.append(
        "<li>Targets follow the TVB-37 management-book ladder; continuation and outside breaks only have a target when a week or month level sits beyond the entry.</li>"
    )
    parts.append(
        "<li>Half the coins listed in 2025-26, so the test period is dominated by young alts. Dead coins are included (survivorship handled), but a coin that died inside the 10-bar window is simply censored out.</li>"
    )
    parts.append(
        "<li>With 500k rows almost every difference is 'statistically significant'. The question is never significance, it is whether the effect is big enough to survive costs and stable across years.</li></ul>"
    )
    parts.append(
        f"<p class=muted>Built in {time.time() - t0:.0f} s. Code: analysis/strat_ml/report.py. Definitions: docs/experiments/strat_ml_phase2_events_design.md.</p></main></body></html>"
    )
    out = REPORTS / f"strat_ml_report_{stamp}.html"
    out.write_text("".join(parts), encoding="utf-8")
    numbers = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": int(len(ev)),
        "overall": {
            k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in ov.items()
        },
        "clf": ml["clf"],
        "reg": ml["reg"],
        "clf_context": ml["clf_context"],
        "decile_reg": ml["decile_reg"].round(4).to_dict(orient="records"),
        "decile_clf": ml["decile_clf"].round(4).to_dict(orient="records"),
        "rr": base["rr"].round(4).to_dict(orient="records"),
        "importance": ml["importance"].head(25).round(5).to_dict(orient="records"),
        "pattern_class": base["pattern_class"].round(4).to_dict(orient="records"),
        "year_class": base["year_class"].round(4).to_dict(orient="records"),
        "tree": tree_tab.round(3).to_dict(orient="records"),
        "clusters": clus_tab.round(4).to_dict(orient="records"),
    }
    (REPORTS / f"report_numbers_{stamp}.json").write_text(
        json.dumps(numbers, indent=1, default=str), encoding="utf-8"
    )
    log(f"report -> {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", default=str(EVENTS_PATH))
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    build_report(events=Path(a.events), tag=a.tag)


if __name__ == "__main__":
    main(sys.argv[1:])
