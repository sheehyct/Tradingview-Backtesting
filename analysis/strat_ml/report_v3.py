"""Phase 3 of the STRAT trigger research: the section-5 fixes, the cost model, the 15-minute
trigger-hour check, and test 1 (raw forward drift, no exits) with its gate.

Spec: docs/experiments/strat_ml_phase3_brief.md (the owner's brief, 2026-10-21). This file EXTENDS
analysis/strat_ml/report.py, which is imported and left untouched: the phase-1 event table is read
through the phase-1 loader unchanged, the phase-1 helpers (Wilson band, cell stats, palette, CSS,
model parameters) are reused, and every new test is a section here. Tests 2-5 and the HIP-3 branch
are NOT in this file yet: the brief says build in stages and stop at the test-1 gate to report.

Reporting rules enforced in code: every table goes through `Doc.table`, which refuses to render
without a "What this means" paragraph and a verdict line; every R number from the cost model on is
after costs and carries a cost column; every z is clustered by trigger date (triggers on the same
day across hundreds of coins are one observation of the market, not hundreds).

Outputs (analysis/strat_ml/reports/): "STRAT Trigger Research v3.html" (self-contained, charts
inline), the same as .md (charts as PNG files under v3_charts/), report_v3_numbers.json (every
table as data), and docs/experiments/strat_ml_phase3_results.md (the gate line and the summary).

CLI:
  uv run python -m analysis.strat_ml.report_v3 [--events PATH] [--skip-15m] [--m15-rows 20000]
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

from analysis.domino.census import DAY, HOUR  # noqa: E402
from analysis.strat_ml import report as p1  # noqa: E402  phase 1, imported and untouched
from analysis.strat_ml.binance_vision import parquet_path  # noqa: E402
from analysis.strat_ml.events import EVENTS_PATH, funding_frame  # noqa: E402

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
CHART_DIR = "v3_charts"
TITLE = "STRAT Trigger Research v3"
BRIEF = HERE.parent.parent / "docs" / "experiments" / "strat_ml_phase3_brief.md"
RESULTS_DOC = HERE.parent.parent / "docs" / "experiments" / "strat_ml_phase3_results.md"
STABLES_LOG = HERE / "stablecoins_dropped.json"  # committed: the dropped list (brief section 5)
PHASE1_NUMBERS = REPORTS / "report_numbers_2026-10-20.json"  # the published phase-1 headline
SPLIT_DATE = p1.SPLIT_DATE
SPLIT = pd.Timestamp(SPLIT_DATE, tz="UTC")
MIN_CELL = 300  # brief rule 5: cells under 300 rows are greyed and never quoted in a verdict
HORIZONS = (1, 3, 5, 10)
FAMILIES = ("continuation", "inside", "outside", "reversal")
RNG = 0

# ------------------------------------------------------------------ cost model (brief section 5)
# Fractions of notional. Entry is a stop-market at the break (taker). The phase-1 target exit is a
# resting limit (maker); the stop exit, the 10-bar timeout mark and the test-1 "hold N bars, then
# close" exits are taker. Slippage on taker legs only, by the phase-1 liquidity tier (a row with
# no tier is charged tier 3). Funding = the archive's actual rate series for that symbol, charged
# at every funding mark the trade is open across, signed by direction (longs pay positive funding),
# on the entry notional. All four parameters sit here so a reader can change them.
COSTS = {
    "binance": {"taker": 0.0005, "maker": 0.0002, "slip": {1: 0.0002, 2: 0.0003, 3: 0.0005}},
    "hip3": {"taker": 0.00045, "maker": 0.00015, "slip": {1: 0.0005, 2: 0.0005, 3: 0.0005}},
}
FUNDING = "archive"  # per-symbol fundingRate parquet; the HIP-3 snapshot has no series (0, flagged)
STABLE_BASES = ("USDC", "BUSD", "TUSD", "FDUSD", "USDP", "DAI", "USDD")
STABLE_BAND = 0.01  # a pair whose hourly close sits inside +-1% of 1.00 ...
STABLE_SHARE = 0.90  # ... for 90% of its history is a stablecoin perp and leaves the universe
R_CLIP = (-5.0, 10.0)  # phase 1's "mean R no stop" clip (equity_perps.py, ticker_census.py), reused
WINSOR_Q = (0.005, 0.995)  # train-period quantiles that bound the % and ATR units (phase-1 habit)
M15_ROWS = 20_000  # the section-5 check sample

# ------------------------------------------------------------------ glossary (brief section 3)
# Reproduced VERBATIM from the brief's glossary table; tests/test_strat_ml_report_v3.py checks the
# copy against the brief. The intro sentence is the brief's own.
GLOSSARY_INTRO = (
    "Every term below must be used with this meaning in the report, and the report's own glossary "
    "block (top of the page) reproduces these definitions verbatim. The running convention: "
    "<b>size every trade so the stop costs $100.</b> Then every number in R reads as dollars per "
    "$100 risked."
)
GLOSSARY_HEAD = ("term", "what it means", "example")
GLOSSARY_ROWS = [
    (
        "R",
        "Your risk per trade, in dollars. 1R = what the stop costs.",
        "Stop costs $100, so 1R = $100.",
    ),
    (
        "+0.5R",
        "The trade is up half your risk.",
        'Up $50 on a $100 risk. "Move stop to breakeven at +0.5R" = once up $50, stop goes to entry so the trade can\'t lose.',
    ),
    ("−1R", "Stopped out.", "Lost $100."),
    (
        "Mean R",
        "Average result per trade. What the account does over many trades.",
        "Mean R −0.032 = lost $3.20 per $100 risked, on average, before fees.",
    ),
    (
        "Median R",
        "The middle trade. What a typical trade feels like.",
        "Median +0.056 = typical trade made $5.60. Mean −0.032 at the same time = losers big enough to drag the average under zero.",
    ),
    ("Target at 0.4R", "Aiming to make 40% of what you're risking.", "Make $40, risk $100."),
    (
        "Reward-to-risk (R:R)",
        "Target distance divided by stop distance.",
        "T1 0.4R away, stop 1R away: R:R 0.4.",
    ),
    (
        "Fair hit rate",
        "The win rate a coin-flip market gives for that stop and target. Nearer target = hit more often, with no edge involved. Formula: 1 ÷ (1 + R:R).",
        "R:R 0.4 → fair = 71%. You need to hit the target more than 71 times in 100 to make money.",
    ),
    (
        "Excess over fair",
        "Observed target-first % minus fair hit rate. The only hit-rate number that isn't geometry.",
        "Reversals: 69% observed vs 71% fair = −2 points. No edge.",
    ),
    (
        "Target-first %",
        "Share of trades that touched the target before the stop. Not the same as win %.",
        "",
    ),
    ("Win %", "Share of trades that closed above zero after 10 bars, however they got there.", ""),
    (
        "MFE / MAE",
        "Best and worst the trade got during the window if you had never exited.",
        "Median MFE 1.6R = half the trades were up at least $160 at some point. Median MAE 1.58R = half were also down at least $158 at some point. Exits at +$40 and −$100 sit inside that swing.",
    ),
    (
        "Drift",
        "Whether price keeps going the break's way, on average, if you just hold. The only thing any exit rule can harvest.",
        "No drift = no stop or target or trail can help; the trade is a coin flip whatever you do with it.",
    ),
    (
        "Expectancy",
        "Mean R after fees, funding and slippage. The number that decides whether to trade it.",
        "",
    ),
    (
        "Walk-forward / train–test",
        "Rules found on 2020–24, judged on 2025–26 which the rules never saw.",
        'A rule that holds on both is real. One that only holds on 2020–24 was fitted to noise: that is what "overfit" means.',
    ),
    (
        "Decile",
        "Sort trades by a model's score, cut into 10 equal buckets.",
        "Decile 1 = the model's least-favourite 10%. If decile 1 loses and decile 10 wins, the model can rank.",
    ),
    (
        "ATR",
        "Average true range: the coin's normal daily swing. Used to compare moves across coins that move at different speeds.",
        "Stop at 0.6 ATR = stop set at 60% of a normal day's range.",
    ),
    (
        "z vs own noise",
        "Mean R divided by how much that cell's results bounce around. Below 2 = could be luck.",
        "A coin with +0.08R and z 1.8 is at the edge of noise.",
    ),
]

# ------------------------------------------------------------------ small statistics


def clustered_mean(x: np.ndarray, cluster: np.ndarray) -> dict:
    """Mean, median and the standard error of the mean with residuals summed inside each cluster
    (trigger date): se = sqrt(sum_g (sum_{i in g} (x_i - mean))^2) / n. z = mean / se."""
    x = np.asarray(x, dtype=float)
    ok = ~np.isnan(x)
    x, cluster = x[ok], np.asarray(cluster)[ok]
    n = len(x)
    if n == 0:
        return {"n": 0, "days": 0, "mean": np.nan, "median": np.nan, "se": np.nan, "z": np.nan}
    m = float(x.mean())
    s = pd.Series(x - m).groupby(cluster).sum().to_numpy()
    se = float(np.sqrt((s**2).sum()) / n)
    return {
        "n": n,
        "days": int(len(s)),
        "mean": m,
        "median": float(np.median(x)),
        "se": se,
        "z": m / se if se > 0 else np.nan,
    }


def winsor_bounds(s: pd.Series, train: pd.Series) -> tuple[float, float]:
    lo, hi = s[train].quantile(list(WINSOR_Q))
    return float(lo), float(hi)


# ------------------------------------------------------------------ stablecoin drop (section 5)


def base_asset(symbol: str) -> str:
    return symbol[:-4] if symbol.endswith("USDT") else symbol


def share_near_one(symbol: str) -> float:
    """Share of the symbol's hourly closes inside +-STABLE_BAND of 1.00 (NaN if no cache)."""
    try:
        close = pd.read_parquet(parquet_path("klines", symbol), columns=["close"])["close"]
    except (FileNotFoundError, OSError):
        return np.nan
    close = close.dropna()
    if not len(close):
        return np.nan
    return float(((close - 1.0).abs() <= STABLE_BAND).mean())


def stablecoin_table(ev: pd.DataFrame, log=print) -> pd.DataFrame:
    """Every symbol in the table that is a stablecoin perp by base name or by price band, with its
    phase-1 rows and managed mean R, written to STABLES_LOG (the brief: log the dropped list)."""
    rows = []
    for sym, g in ev.groupby("symbol", observed=True):
        base = base_asset(str(sym))
        share = share_near_one(str(sym))
        by_name = base in STABLE_BASES
        by_band = (not np.isnan(share)) and share >= STABLE_SHARE
        if by_name or by_band:
            rows.append(
                {
                    "symbol": str(sym),
                    "reason": "base name" + (" + price band" if by_band else "")
                    if by_name
                    else "price band",
                    "share_near_1": share,
                    "rows": int(len(g)),
                    "mean_r_phase1": float(g["r10_w"].mean()),
                    "win_pct": 100 * float(g["win"].mean()),
                }
            )
    tab = pd.DataFrame(
        rows, columns=["symbol", "reason", "share_near_1", "rows", "mean_r_phase1", "win_pct"]
    )
    doc = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": f"base in {list(STABLE_BASES)} or hourly close within +-{STABLE_BAND} of 1.00 for"
        f" >= {STABLE_SHARE:.0%} of its history",
        "symbols_checked": int(ev["symbol"].nunique()),
        "dropped": tab.round(4).to_dict(orient="records"),
    }
    STABLES_LOG.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    log(f"  stablecoins dropped: {tab['symbol'].tolist()} -> {STABLES_LOG.name}")
    return tab


# ------------------------------------------------------------------ cost columns (section 5)


def funding_sums(ev: pd.DataFrame, exits: dict[str, np.ndarray], log=print) -> tuple[dict, set]:
    """Per row and per exit clock: the sum of the symbol's funding rates at marks inside
    (trigger hour open, exit hour open]. A mark at the trigger hour's own open is before the
    entry (not charged); a mark at the exit hour's open is while the trade is still open (charged).
    Symbols without a funding series get 0 and are returned in `missing`."""
    out = {k: np.zeros(len(ev)) for k in exits}
    missing: set[str] = set()
    trig = ev["trigger_time"].to_numpy()
    for sym, idx in ev.groupby("symbol", observed=True).indices.items():
        f = funding_frame(str(sym))
        if not len(f):
            missing.add(str(sym))
            continue
        f = f.sort_values("t")
        t = f["t"].to_numpy()
        cum = np.concatenate([[0.0], np.cumsum(f["rate"].to_numpy(float))])
        a = np.searchsorted(t, trig[idx], side="right")
        for k, ex in exits.items():
            b = np.searchsorted(t, ex[idx], side="right")
            out[k][idx] = cum[b] - cum[a]
    if missing:
        log(f"  no funding series for {len(missing)} symbols (charged 0): {sorted(missing)[:8]}")
    return out, missing


def add_costs(ev: pd.DataFrame, log=print) -> pd.DataFrame:
    """fees_r / slip_r / funding_r / cost_r for the phase-1 managed trade, and cost_r_{h},
    net_r_{h}, net_pct_{h}, net_atr_{h} for the test-1 holds (close of day D+h, taker exit).
    All in R using the row's own stop distance as a fraction of price (R per 1% of price =
    level / r / 100)."""
    ev = ev.copy()
    venue = np.where(ev["asset_class"].astype(str) == "equity_perp", "hip3", "binance")
    tier = ev["liq_tier"].fillna(3).astype(int).clip(1, 3).to_numpy()
    taker = np.array([COSTS[v]["taker"] for v in venue])
    maker = np.array([COSTS[v]["maker"] for v in venue])
    slip = np.array([COSTS[v]["slip"][t] for v, t in zip(venue, tier)])
    rpf = (ev["level"] / ev["r"]).to_numpy(float)  # R per unit fraction of price
    sign = np.where(ev["direction"].astype(str) == "long", 1.0, -1.0)
    ft = ev["first_touch"].astype(str).to_numpy()
    touched = np.isin(ft, ["stop", "target"])
    touch_h = ev["touch_hours"].fillna(0).to_numpy(float)
    day = ev["day"].to_numpy(np.int64)
    trig = ev["trigger_time"].to_numpy(np.int64)
    exit_p1 = np.where(touched, trig + touch_h.astype(np.int64) * HOUR, day + 10 * DAY + 23 * HOUR)
    exits = {"p1": exit_p1}
    for h in HORIZONS:
        exits[f"h{h}"] = day + h * DAY + 23 * HOUR
    fsum, missing = funding_sums(ev, exits, log)
    ev["funding_known"] = ~ev["symbol"].astype(str).isin(missing)
    exit_fee = np.where(ft == "target", maker, taker)
    exit_slip = np.where(ft == "target", 0.0, slip)
    ev["fees_r"] = (taker + exit_fee) * rpf
    ev["slip_r"] = (slip + exit_slip) * rpf
    ev["funding_r"] = sign * fsum["p1"] * rpf
    ev["cost_r"] = ev["fees_r"] + ev["slip_r"] + ev["funding_r"]
    ev["cost_pct"] = 100 * (taker + exit_fee + slip + exit_slip + sign * fsum["p1"])
    ev["r10_net"] = (ev["r10"] - ev["cost_r"]).clip(*R_CLIP)
    ev["ret_pct"] = (ev["r10"] * ev["r"] / ev["level"] * 100).clip(-50, 50)  # phase-1 convention
    ev["ret_pct_net"] = (ev["ret_pct"] - ev["cost_pct"]).clip(-50, 50)
    level = ev["level"].to_numpy(float)
    atr = ev["atr"].to_numpy(float)
    rr = ev["r"].to_numpy(float)
    for h in HORIZONS:
        cost_frac = 2 * taker + 2 * slip + sign * fsum[f"h{h}"]
        ev[f"cost_r_{h}"] = cost_frac * rpf
        fwd = ev[f"r_close_{h}"].to_numpy(float) * rr / level  # fraction of price, signed
        net = fwd - cost_frac
        ev[f"net_pct_{h}"] = 100 * net
        ev[f"net_atr_{h}"] = net * level / atr
        ev[f"net_r_{h}"] = (ev[f"r_close_{h}"] - ev[f"cost_r_{h}"]).clip(*R_CLIP)
        ev[f"gross_r_{h}"] = ev[f"r_close_{h}"].clip(*R_CLIP)
    return ev


# ------------------------------------------------------------------ loading


def load_corrected(
    events: Path = EVENTS_PATH, log=print
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(published, corrected, stables): the phase-1 table through the phase-1 loader (unchanged),
    then the stablecoin drop and the cost columns. Train = triggers before SPLIT_DATE."""
    pub = p1.load_events(events)
    log(f"  phase-1 table as published: {len(pub):,} rows, {pub['symbol'].nunique()} coins")
    stables = stablecoin_table(pub, log)
    ev = pub[~pub["symbol"].astype(str).isin(stables["symbol"].tolist())].copy()
    ev["symbol"] = ev["symbol"].astype(str)
    ev = add_costs(ev, log)
    ev["train"] = ev["day_ts"] < SPLIT
    ev["period"] = np.where(ev["train"], "train 2020-24", "test 2025-26")
    # winsorized % and ATR units, bounds from the train period only
    for h in HORIZONS:
        for u in ("pct", "atr"):
            lo, hi = winsor_bounds(ev[f"net_{u}_{h}"], ev["train"])
            ev[f"net_{u}_w_{h}"] = ev[f"net_{u}_{h}"].clip(lo, hi)
    lo, hi = winsor_bounds(ev["cost_r"], ev["train"])
    ev["cost_r_w"] = ev["cost_r"].clip(lo, hi)
    for h in HORIZONS:
        lo, hi = winsor_bounds(ev[f"cost_r_{h}"], ev["train"])
        ev[f"cost_r_w_{h}"] = ev[f"cost_r_{h}"].clip(lo, hi)
    # BTC 30-day realized-vol terciles, cut points from the train period only
    q = ev.loc[ev["train"], "btc_rv30_pct"].quantile([1 / 3, 2 / 3]).to_numpy()
    ev["btc_vol_tercile"] = pd.cut(
        ev["btc_rv30_pct"], [-np.inf, q[0], q[1], np.inf], labels=["low", "mid", "high"]
    )
    ev.attrs["btc_vol_cuts"] = [float(q[0]), float(q[1])]
    log(
        f"  corrected table: {len(ev):,} rows, {ev['symbol'].nunique()} coins; train {int(ev['train'].sum()):,}, test {int((~ev['train']).sum()):,}"
    )
    return pub, ev, stables


# ------------------------------------------------------------------ formatting and the Doc


def fmt(v, kind: str) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)) or (isinstance(v, str) and v == ""):
        return ""
    if kind == "int":
        return f"{int(v):,}"
    if kind == "pct":
        return f"{v:.1f}%"
    if kind == "pct2":
        return f"{v:+.2f}%"
    if kind == "r":
        return f"{v:+.3f}"
    if kind == "f2":
        return f"{v:.2f}"
    if kind == "f3":
        return f"{v:.3f}"
    if kind == "z":
        return f"{v:+.1f}"
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.3g}"
    return str(v)


def kind_of(col: str) -> str:
    explicit = {
        "n": "int",
        "days": "int",
        "rows": "int",
        "coins": "int",
        "n_train": "int",
        "n_test": "int",
        "horizon": "int",
        "year": "int",
        "rows_fired": "int",
        "share_near_1": "f2",
        "mean_abs_interaction": "f3",
        "median_rr": "f2",
    }
    if col in explicit:
        return explicit[col]
    if col.startswith("z"):
        return "z"
    if (
        col.startswith("mean_pct")
        or col.startswith("cost_pct")
        or col.startswith("median_pct")
        or col.startswith("mean_ret_pct")
    ):
        return "pct2"
    if col.endswith("_pct") or col.startswith("win_pct") or col.startswith("tgt_pct"):
        return "pct"
    if (
        "mean_r" in col
        or "median_r" in col
        or "_atr" in col
        or "cost_r" in col
        or col.endswith("_r")
        or "_r_" in col
    ):
        return "r"
    return "s"


HEAD = {
    **p1.HEAD,
    "days": "trigger days",
    "mean_pct": "mean ret (% of price)",
    "mean_atr": "mean ret (ATR)",
    "median_atr": "median ret (ATR)",
    "z": "z (clustered)",
    "mean_r": "mean R no stop",
    "cost_r": "cost (R)",
    "mean_r_phase1": "mean R (phase 1)",
    "share_near_1": "share of hours within 1% of 1.00",
    "btc_vol_tercile": "BTC vol tercile",
    "liq_tier": "liquidity tier",
    "mean_atr_train": "train: mean ret (ATR)",
    "z_train": "train: z",
    "n_train": "train: n",
    "mean_atr_test": "test: mean ret (ATR)",
    "z_test": "test: z",
    "n_test": "test: n",
    "mean_pct_test": "test: mean ret (% of price)",
    "mean_r_test": "test: mean R no stop",
    "cost_r_test": "test: cost (R)",
    "mean_pct_train": "train: mean ret (% of price)",
    "mean_r_train": "train: mean R no stop",
    "win_pct_train": "train: win %",
    "win_pct_test": "test: win %",
    "fees_r": "fees (R)",
    "slip_r": "slippage (R)",
    "funding_r": "funding (R)",
    "mean_r_gross": "mean R before costs",
    "mean_r_net": "mean R after costs",
    "cost_pct": "cost (% of price)",
    "mean_ret_pct": "mean ret (% of price)",
}
BAND_PAIRS = {
    "win_pct": ("win_lo", "win_hi"),
    "tgt_pct": ("tgt_lo", "tgt_hi"),
    "fav_first_pct": ("fav_lo", "fav_hi"),
    "win_pct_train": ("win_lo_train", "win_hi_train"),
    "win_pct_test": ("win_lo_test", "win_hi_test"),
}


def _cell_text(r: pd.Series, c: str, df_cols) -> str:
    txt = fmt(r[c], kind_of(c))
    lo, hi = BAND_PAIRS.get(c, (None, None))
    if lo in df_cols and pd.notna(r[lo]) and txt:
        txt += f" ({r[lo]:.1f}-{r[hi]:.1f})"
    return txt


class Doc:
    """The page as blocks; renders HTML (phase-1 CSS, charts inline) and Markdown (charts as
    files). `table` is the only way a table gets onto the page and it needs both texts."""

    def __init__(self, title: str):
        self.title = title
        self.blocks: list[tuple] = []
        self.tables: dict[str, pd.DataFrame] = {}
        self.verdicts: list[tuple[str, str]] = []
        self.pngs: dict[str, bytes] = {}

    def h2(self, t: str):
        self.blocks.append(("h2", t))

    def h3(self, t: str):
        self.blocks.append(("h3", t))

    def p(self, t: str):
        self.blocks.append(("p", t))

    def note(self, t: str):
        self.blocks.append(("note", t))

    def gate(self, t: str):
        self.blocks.append(("gate", t))

    def bullets(self, items: list[str]):
        self.blocks.append(("ul", items))

    def glossary(self):
        self.blocks.append(("glossary", None))

    def table(
        self,
        key: str,
        df: pd.DataFrame,
        what: str,
        verdict: str,
        cols: list[str] | None = None,
        grey_n: str | None = "n",
        heading: str | None = None,
    ):
        if not what or not what.strip():
            raise ValueError(f"table {key}: a 'What this means' paragraph is required")
        if not verdict or not verdict.strip():
            raise ValueError(f"table {key}: a verdict line is required")
        if not verdict.startswith("Verdict:"):
            raise ValueError(f"table {key}: the verdict must start with 'Verdict:'")
        skip = {lo for pair in BAND_PAIRS.values() for lo in pair}
        cols = cols or [c for c in df.columns if c not in skip]
        self.tables[key] = df
        self.verdicts.append((heading or key, verdict))
        self.blocks.append(("table", key, df, what, verdict, cols, grey_n, heading))

    def chart(self, fig, name: str, caption: str):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        self.pngs[name] = buf.getvalue()
        self.blocks.append(("chart", name, caption))

    # ---- HTML

    def html(self) -> str:
        css = p1.CSS + (
            ".verdict{font-weight:600;margin:.3em 0 1em}.gate{font-size:1.05rem;font-weight:700;"
            "background:var(--box);border-left:4px solid var(--accent);padding:10px 12px;border-radius:6px;margin:.6em 0}"
            ".what{background:var(--box);padding:10px 12px;border-radius:6px;margin:.8em 0 .3em}"
            "table.gl td{white-space:normal;text-align:left;vertical-align:top}"
        )
        out = [
            f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{html.escape(self.title)}</title><style>{css}</style></head><body><main>"
            f"<h1>{html.escape(self.title)}</h1>"
        ]
        for b in self.blocks:
            k = b[0]
            if k == "h2":
                out.append(f"<h2>{b[1]}</h2>")
            elif k == "h3":
                out.append(f"<h3>{b[1]}</h3>")
            elif k == "p":
                out.append(f"<p>{b[1]}</p>")
            elif k == "note":
                out.append(f"<div class=plain>{b[1]}</div>")
            elif k == "gate":
                out.append(f"<div class=gate>{b[1]}</div>")
            elif k == "ul":
                out.append("<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>")
            elif k == "glossary":
                out.append(self._glossary_html())
            elif k == "table":
                _, key, df, what, verdict, cols, grey_n, heading = b
                if heading:
                    out.append(f"<h3>{heading}</h3>")
                out.append(f"<div class=what><b>What this means.</b> {what}</div>")
                out.append(self._table_html(df, cols, grey_n))
                out.append(f"<p class=verdict>{html.escape(verdict)}</p>")
            elif k == "chart":
                _, name, caption = b
                b64 = base64.b64encode(self.pngs[name]).decode()
                out.append(
                    f'<img src="data:image/png;base64,{b64}" alt="{html.escape(caption)}"><p class=muted>{caption}</p>'
                )
        out.append("</main></body></html>")
        return "".join(out)

    def _glossary_html(self) -> str:
        head = "".join(f"<th>{html.escape(h)}</th>" for h in GLOSSARY_HEAD)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>"
            for row in GLOSSARY_ROWS
        )
        return (
            f"<h2>Glossary in trader terms</h2><div class=plain>{GLOSSARY_INTRO}</div>"
            f"<div class=tw><table class=gl><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
        )

    def _table_html(self, df: pd.DataFrame, cols: list[str], grey_n: str | None) -> str:
        head = "".join(f"<th>{html.escape(HEAD.get(c, c.replace('_', ' ')))}</th>" for c in cols)
        body = []
        for _, r in df.iterrows():
            grey = grey_n in df.columns and pd.notna(r[grey_n]) and r[grey_n] < MIN_CELL
            cells = "".join(f"<td>{html.escape(_cell_text(r, c, df.columns))}</td>" for c in cols)
            body.append(f"<tr class={'grey' if grey else ''}>{cells}</tr>")
        return f"<div class=tw><table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"

    # ---- Markdown

    def md(self) -> str:
        out = [f"# {self.title}", ""]
        for b in self.blocks:
            k = b[0]
            if k == "h2":
                out += [f"## {_strip(b[1])}", ""]
            elif k == "h3":
                out += [f"### {_strip(b[1])}", ""]
            elif k == "p":
                out += [_strip(b[1]), ""]
            elif k == "note":
                out += ["> " + _strip(b[1]), ""]
            elif k == "gate":
                out += ["**" + _strip(b[1]) + "**", ""]
            elif k == "ul":
                out += [f"- {_strip(x)}" for x in b[1]] + [""]
            elif k == "glossary":
                out += ["## Glossary in trader terms", "", _strip(GLOSSARY_INTRO), ""]
                out += ["| " + " | ".join(GLOSSARY_HEAD) + " |", "| --- | --- | --- |"]
                out += ["| " + " | ".join(row) + " |" for row in GLOSSARY_ROWS] + [""]
            elif k == "table":
                _, key, df, what, verdict, cols, grey_n, heading = b
                if heading:
                    out += [f"### {_strip(heading)}", ""]
                out += ["**What this means.** " + _strip(what), ""]
                out += self._table_md(df, cols, grey_n) + [""]
                out += [f"*{verdict}*", ""]
            elif k == "chart":
                _, name, caption = b
                out += [f"![{caption}]({CHART_DIR}/{name}.png)", "", f"*{caption}*", ""]
        return "\n".join(out)

    def _table_md(self, df: pd.DataFrame, cols: list[str], grey_n: str | None) -> list[str]:
        lines = ["| " + " | ".join(HEAD.get(c, c.replace("_", " ")) for c in cols) + " |"]
        lines.append("|" + "|".join(" --- " for _ in cols) + "|")
        for _, r in df.iterrows():
            grey = grey_n in df.columns and pd.notna(r[grey_n]) and r[grey_n] < MIN_CELL
            cells = [_cell_text(r, c, df.columns).replace("|", "/") for c in cols]
            if grey:
                cells = [f"({c})" if c else "" for c in cells]
            lines.append("| " + " | ".join(cells) + " |")
        return lines


def _strip(t: str) -> str:
    """HTML to Markdown-ish plain text for the .md twin."""
    return (
        t.replace("<b>", "**")
        .replace("</b>", "**")
        .replace("<i>", "*")
        .replace("</i>", "*")
        .replace("&amp;", "&")
        .replace("&plusmn;", "+-")
        .replace("<br>", " ")
        .replace("<span class=muted>", "")
        .replace("</span>", "")
    )


# ------------------------------------------------------------------ verdicts


def verdict_line(
    hypothesis: str, cells: list[tuple[str, float, float, int]], unit: str = "ATR", fmt_num=None
) -> str:
    """Verdict: supports / contradicts / inconclusive -- <hypothesis>, because <one number>.
    A cell (label, mean, z, n) supports when mean > 0 with z >= 2; contradicts when mean <= 0 and
    z <= -2 (the drift is significantly against) or when it is flat with |z| < 2 on a large cell
    (reads as 'no drift'); cells under MIN_CELL are never quoted."""
    fmt_num = fmt_num or (lambda m: f"{m:+.3f} {unit}")
    big = [c for c in cells if c[3] >= MIN_CELL and not np.isnan(c[2])]
    if not big:
        return f"Verdict: inconclusive -- {hypothesis}, because no cell reaches {MIN_CELL} rows."
    sup = [c for c in big if c[1] > 0 and c[2] >= 2]
    con = [c for c in big if (c[1] <= 0 and c[2] <= -2)]
    flat = [c for c in big if abs(c[2]) < 2]

    def say(c):
        return f"{c[0]} {fmt_num(c[1])}, z {c[2]:+.1f}, n {c[3]:,}"

    if sup and not con:
        return f"Verdict: supports -- {hypothesis}, because {'; '.join(say(c) for c in sup)}" + (
            f" (inconclusive for {', '.join(c[0] for c in flat)})." if flat else "."
        )
    if con and not sup:
        return f"Verdict: contradicts -- {hypothesis}, because {'; '.join(say(c) for c in con)}" + (
            f" (inconclusive for {', '.join(c[0] for c in flat)})." if flat else "."
        )
    if sup and con:
        return (
            f"Verdict: supports for {', '.join(c[0] for c in sup)}; contradicts for {', '.join(c[0] for c in con)}"
            f" -- {hypothesis}, because {'; '.join(say(c) for c in sup + con)}."
        )
    worst = max(flat, key=lambda c: abs(c[2])) if flat else big[0]
    return f"Verdict: inconclusive -- {hypothesis}, because every cell is inside its own noise, e.g. {say(worst)}."


# ------------------------------------------------------------------ section 0: phase 1 corrected


def headline(ev: pd.DataFrame) -> dict:
    cs = p1.cell_stats(ev)
    out = {
        "rows": len(ev),
        "coins": int(ev["symbol"].nunique()),
        "rows in test (2025-26)": int((ev["day_ts"] >= SPLIT).sum()),
        "win %": f"{cs['win_pct']:.1f}% ({cs['win_lo']:.1f}-{cs['win_hi']:.1f})",
        "target-first %": f"{cs['tgt_pct']:.1f}%",
        "mean R (winsorized)": f"{cs['mean_r']:+.4f}",
        "median R": f"{cs['median_r']:+.4f}",
        "median MFE / MAE (R)": f"{cs['mfe_med']:.2f} / {cs['mae_med']:.2f}",
        "mean ret (% of price)": f"{(ev['r10'] * ev['r'] / ev['level'] * 100).clip(-50, 50).mean():+.3f}%",
    }
    return out


def phase1_corrected_table(pub: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    old = headline(pub)
    new = headline(ev)
    net = {
        "mean R (winsorized)": f"{ev['r10_net'].mean():+.4f}",
        "median R": f"{ev['r10_net'].median():+.4f}",
        "mean ret (% of price)": f"{ev['ret_pct_net'].mean():+.3f}%",
        "win %": f"{100 * (ev['r10_net'] > 0).mean():.1f}%",
    }
    rows = []
    for k in old:
        rows.append(
            {
                "metric": k,
                "phase 1 as published (before fees)": fmt(old[k], "int")
                if isinstance(old[k], int)
                else old[k],
                "corrected: stablecoins dropped (before fees)": fmt(new[k], "int")
                if isinstance(new[k], int)
                else new[k],
                "corrected, after costs": net.get(k, ""),
            }
        )
    return pd.DataFrame(rows)


def interactions_fixed(ev: pd.DataFrame, log=print) -> pd.DataFrame:
    """Phase-1 section 3f, re-rendered. The published call crashed because SHAP's interaction
    routine converts the frame to floats and met the category strings ('alt'). Fix per the brief:
    encode the categoricals (ordinal integer codes) BEFORE the interaction call. LightGBM's own
    categorical splits are not what SHAP's interaction walker expects either, so the interaction
    model is a refit of model A (same parameters, same context features, same train rows) on the
    coded frame with every column numeric; its pair ranking is the table."""
    import lightgbm as lgb
    import shap

    x = ev[p1.CONTEXT_CAT + p1.CONTEXT_NUM].copy()
    for c in p1.CONTEXT_CAT:
        x[c] = x[c].astype("category").cat.codes.astype("float64")
    train = ev["train"].to_numpy()
    y = ev["r10_w"].to_numpy()
    t0 = time.time()
    reg = lgb.LGBMRegressor(**p1._lgb_params()).fit(x[train], y[train])
    small = x[~train].sample(min(1500, int((~train).sum())), random_state=RNG)
    iv = shap.TreeExplainer(reg).shap_interaction_values(small)
    m = np.abs(iv).mean(axis=0)
    np.fill_diagonal(m, 0)
    cols = list(small.columns)
    pairs = sorted(
        ((m[i, j], cols[i], cols[j]) for i in range(len(cols)) for j in range(i + 1, len(cols))),
        reverse=True,
    )
    log(f"  3f interactions: {len(small)} test rows, {time.time() - t0:.0f}s")
    return pd.DataFrame(
        [
            {
                "feature_a": p1.PLAIN.get(a, a),
                "feature_b": p1.PLAIN.get(b, b),
                "mean_abs_interaction": float(v),
            }
            for v, a, b in pairs[:10]
        ]
    )


# ------------------------------------------------------------------ section 1: the cost model


def cost_param_table() -> pd.DataFrame:
    rows = []
    for name, binance, hip3 in (
        ("taker fee, each side", COSTS["binance"]["taker"], COSTS["hip3"]["taker"]),
        ("maker fee (resting target exit)", COSTS["binance"]["maker"], COSTS["hip3"]["maker"]),
        (
            "slippage, tier 1 (top 10), taker legs",
            COSTS["binance"]["slip"][1],
            COSTS["hip3"]["slip"][1],
        ),
        ("slippage, tier 2 (11-50)", COSTS["binance"]["slip"][2], COSTS["hip3"]["slip"][2]),
        ("slippage, tier 3 (rest)", COSTS["binance"]["slip"][3], COSTS["hip3"]["slip"][3]),
    ):
        rows.append(
            {
                "component": name,
                "Binance USDT-M": f"{100 * binance:.3f}%",
                "HIP-3 (Hyperliquid)": f"{100 * hip3:.3f}%",
            }
        )
    rows.append(
        {
            "component": "funding",
            "Binance USDT-M": "actual series, per mark the trade is open across, signed",
            "HIP-3 (Hyperliquid)": "none in the frozen snapshot: charged 0, flagged",
        }
    )
    return pd.DataFrame(rows)


def cost_by_tier(ev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (tier, fam), g in ev.groupby(
        [ev["liq_tier"].fillna(3).astype(int), "family"], observed=True
    ):
        rows.append(
            {
                "liq_tier": tier,
                "family": fam,
                "n": len(g),
                "fees_r": g["fees_r"].clip(upper=g["fees_r"].quantile(0.995)).mean(),
                "slip_r": g["slip_r"].clip(upper=g["slip_r"].quantile(0.995)).mean(),
                "funding_r": g["funding_r"].clip(*g["funding_r"].quantile([0.005, 0.995])).mean(),
                "cost_r": g["cost_r_w"].mean(),
                "cost_pct": g["cost_pct"].clip(*g["cost_pct"].quantile([0.005, 0.995])).mean(),
                "mean_r_gross": g["r10_w"].mean(),
                "mean_r_net": g["r10_net"].mean(),
                "mean_ret_pct": g["ret_pct"].mean(),
            }
        )
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ section 3: test 1


def drift_cell(g: pd.DataFrame, h: int) -> dict:
    atr = g[f"net_atr_w_{h}"].to_numpy(float)
    pct = g[f"net_pct_w_{h}"].to_numpy(float)
    rr = g[f"net_r_{h}"].to_numpy(float)
    cost = g[f"cost_r_w_{h}"].to_numpy(float)
    cl = g["day"].to_numpy()
    ok = ~np.isnan(atr)
    cs = clustered_mean(atr[ok], cl[ok])
    n = int(ok.sum())
    wins = int((rr[ok] > 0).sum())
    lo, hi = p1.wilson(wins, n)
    return {
        "n": n,
        "days": cs["days"],
        "win_pct": 100 * wins / n if n else np.nan,
        "win_lo": 100 * lo,
        "win_hi": 100 * hi,
        "mean_pct": float(np.nanmean(pct[ok])) if n else np.nan,
        "mean_atr": cs["mean"],
        "median_atr": cs["median"],
        "z": cs["z"],
        "mean_r": float(np.nanmean(rr[ok])) if n else np.nan,
        "cost_r": float(np.nanmean(cost[ok])) if n else np.nan,
    }


def drift_table(
    ev: pd.DataFrame, keys: list[str], horizons=HORIZONS, with_all: bool = False
) -> pd.DataFrame:
    rows = []
    if with_all:
        for h in horizons:
            rows.append({**{k: "all" for k in keys}, "horizon": h, **drift_cell(ev, h)})
    for key, g in ev.groupby(keys, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        for h in horizons:
            rows.append({**dict(zip(keys, key)), "horizon": h, **drift_cell(g, h)})
    return pd.DataFrame(rows)


def drift_train_test(
    ev: pd.DataFrame, keys: list[str], h: int, with_all: bool = False
) -> pd.DataFrame:
    a = drift_table(ev[ev["train"]], keys, [h], with_all).drop(columns=["horizon"])
    b = drift_table(ev[~ev["train"]], keys, [h], with_all).drop(columns=["horizon"])
    keep = ["n", "mean_atr", "z", "mean_pct", "mean_r", "cost_r", "win_pct", "win_lo", "win_hi"]
    a = a[keys + keep].rename(columns={c: f"{c}_train" for c in keep})
    b = b[keys + keep].rename(columns={c: f"{c}_test" for c in keep})
    m = a.merge(b, on=keys, how="outer")
    m["horizon"] = h
    return m


def gate_result(tt_family: pd.DataFrame) -> tuple[bool, list[str], str]:
    """The brief's gate: on the test period, net 5-bar forward return above zero with clustered
    z >= 2 in at least one family (cells under MIN_CELL rows never pass)."""
    passed, parts = [], []
    for _, r in tt_family[tt_family["family"] != "all"].iterrows():
        ok = (r["n_test"] >= MIN_CELL) and (r["mean_atr_test"] > 0) and (r["z_test"] >= 2)
        if ok:
            passed.append(str(r["family"]))
        parts.append(
            f"{r['family']} {r['mean_atr_test']:+.3f} ATR ({r['mean_pct_test']:+.2f}% of price,"
            f" {r['mean_r_test']:+.3f}R), z {r['z_test']:+.1f}, n {int(r['n_test']):,}"
        )
    numbers = "; ".join(parts)
    if passed:
        line = f"Gate: PASSED for {', '.join(passed)} / not for the rest. Test period (2025-26), net 5-bar forward return after costs, z clustered by trigger date: {numbers}."
    else:
        line = f"Gate: FAILED. No family clears net 5-bar forward return > 0 with clustered z >= 2 on the test period (2025-26) after costs: {numbers}."
    return bool(passed), passed, line


def chart_drift(ev: pd.DataFrame):
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.4), sharey=False)
    panels = [("whole book", ev)] + [(f, ev[ev["family"] == f]) for f in FAMILIES]
    for ax, (name, g) in zip(axes.ravel(), panels):
        for period, col in (("train 2020-24", p1.C1), ("test 2025-26", p1.C2)):
            gg = g[g["period"] == period]
            means, los, his = [], [], []
            for h in HORIZONS:
                cs = clustered_mean(gg[f"net_atr_w_{h}"].to_numpy(float), gg["day"].to_numpy())
                means.append(cs["mean"])
                los.append(cs["mean"] - 1.96 * cs["se"])
                his.append(cs["mean"] + 1.96 * cs["se"])
            ax.plot(
                HORIZONS,
                means,
                color=col,
                linewidth=2,
                marker="o",
                markersize=4,
                label=f"{period} (n {len(gg):,})",
            )
            ax.fill_between(HORIZONS, los, his, color=col, alpha=0.15, linewidth=0)
        ax.axhline(0, color=p1.MUTED, linewidth=1)
        ax.set_xticks(HORIZONS)
        ax.set_title(name, fontsize=10, color=p1.INK, loc="left")
        ax.legend(frameon=False, fontsize=7.5)
        p1.style_axes(ax)
    axes.ravel()[-1].axis("off")
    fig.supxlabel(
        "daily bars held after the trigger (no stop, no target, costs paid)",
        color=p1.MUTED,
        fontsize=9,
    )
    fig.supylabel(
        "mean net forward return, in ATRs (95% band, clustered by trigger date)",
        color=p1.MUTED,
        fontsize=9,
    )
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ the page


def hyp_drift(h: int, scope: str = "") -> str:
    return f"after a daily STRAT trigger price keeps going the break's way on average over {h} bars, net of costs{scope}"


def build(
    events: Path = EVENTS_PATH, skip_15m: bool = False, m15_rows: int = M15_ROWS, log=print
) -> Path:
    t0 = time.time()
    pub, ev, stables = load_corrected(events, log)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = Doc(TITLE)
    numbers: dict = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "events": str(events),
    }

    # ---------------- test 1 first (the gate line goes at the top of the page)
    t_fam = drift_table(ev, ["family"], HORIZONS, with_all=True)
    t_pat = drift_table(ev, ["pattern", "direction"], [10])
    t_vol = drift_table(ev[ev["btc_vol_tercile"].notna()], ["btc_vol_tercile", "family"], [5])
    t_year = drift_table(ev, ["year", "family"], [5])
    t_liq = drift_table(
        ev.assign(liq_tier=ev["liq_tier"].fillna(3).astype(int)), ["liq_tier"], [5], with_all=True
    )
    tt_fam = drift_train_test(ev, ["family"], 5, with_all=True)
    tt_fam_all_h = pd.concat(
        [drift_train_test(ev, ["family"], h, with_all=True) for h in HORIZONS], ignore_index=True
    )
    tt_vol = drift_train_test(ev[ev["btc_vol_tercile"].notna()], ["btc_vol_tercile", "family"], 5)
    gate_ok, gate_fams, gate_line = gate_result(tt_fam)
    log(f"  {gate_line}")
    numbers["gate"] = {"passed": gate_ok, "families": gate_fams, "line": gate_line}

    # ---------------- top of the page: gate line, summary slot, how to read, glossary
    doc.p(
        f"<span class=muted>Binance USDT-M perps, daily triggers, {ev['day_ts'].min():%Y-%m-%d} to {ev['day_ts'].max():%Y-%m-%d};"
        f" {len(ev):,} trigger rows with a 10-bar outcome on {ev['symbol'].nunique()} coins after the stablecoin drop. Built {stamp}."
        f" Spec: docs/experiments/strat_ml_phase3_brief.md. Phase 1 is cited, not re-run.</span>"
    )
    doc.gate(gate_line)
    summary_slot = len(doc.blocks)  # the one-page summary is inserted here at the end
    doc.note(
        "<b>How to read this page.</b> One row of data is one time a coin broke yesterday's high (long) or low (short) on the daily chart. "
        "Phase 1 traded every such break with a stop at the far side of yesterday's bar and a STRAT target, and found the book flat before fees. "
        "This page asks the question underneath that result: if you took every break and simply held, costs paid, does price keep going your way at all? "
        "Every R number here is after fees, slippage and funding, and every table says in plain words what one row is, what to look at, and what it decided. "
        "Size every trade so the stop costs $100 and every R reads as dollars per $100 risked. Grey rows have fewer than 300 samples and are never quoted in a verdict."
    )
    doc.glossary()

    # ---------------- section 0: phase 1, corrected
    doc.h2("0. Phase 1, corrected: the three known bugs and what they changed")
    doc.p(
        "The brief lists three phase-1 bugs to fix before anything runs: the section 3f interaction table crashed on an unencoded categorical, "
        "a stablecoin perp (USDCUSDT) sat in the universe, and the assembled phase-1 page numbered its caveats section 5 after sections 6-10. "
        "All three are handled here without touching the phase-1 outputs: this page is numbered in page order with the caveats last, the stablecoin rule below "
        "removes every stable perp from the corrected table, and 3f is re-rendered in 0c. The phase-1 report and code stay as published."
    )
    corr = phase1_corrected_table(pub, ev)
    delta_r = float(ev["r10_w"].mean() - pub["r10_w"].mean())
    doc.table(
        "phase1_corrected",
        corr,
        what=(
            "One row is one headline number from phase 1. The first column is phase 1 exactly as published (before fees, stablecoins still in); "
            "the second is the same calculation after the stablecoin drop; the third is the second with fees, slippage and funding taken out of every trade "
            "(mean R after costs: dollars per $100 risked once the exchange has been paid). Look at how little the drop moves the numbers, and how much the costs do."
        ),
        verdict=(
            f"Verdict: {'contradicts' if abs(delta_r) < 0.005 else 'supports'} -- dropping the stablecoin perps changes phase 1's headline materially, "
            f"because the whole-book mean R moves by {delta_r:+.4f} ({100 * delta_r:+.2f} dollars per $100 risked) on {len(ev):,} rows."
        ),
        grey_n=None,
        heading="0a. Headline numbers: as published, corrected, and after costs",
    )
    doc.table(
        "stablecoins_dropped",
        stables,
        what=(
            "One row is one symbol removed from the universe. The rule: the base asset is a stablecoin by name (USDC, BUSD, TUSD, FDUSD, USDP, DAI, USDD), "
            "or the hourly close sat within 1% of 1.00 for 90% of the symbol's history. 'Mean R (phase 1)' is what those rows did in the phase-1 book "
            "(a stable perp's 'yesterday's high' is noise with a tiny stop, so the setup-bar stop is hit constantly). Look at whether anything besides USDC was caught."
        ),
        verdict=(
            f"Verdict: supports -- the universe held stablecoin perps that drag the book, because {len(stables)} symbol(s) matched the rule"
            f", worst {stables.sort_values('mean_r_phase1').iloc[0]['symbol']} at mean R {stables['mean_r_phase1'].min():+.3f} on {int(stables.sort_values('mean_r_phase1').iloc[0]['rows']):,} rows."
            if len(stables)
            else "Verdict: contradicts -- the universe held stablecoin perps that drag the book, because no symbol matched the rule."
        ),
        grey_n=None,
        heading="0b. The stablecoin perps dropped (logged to analysis/strat_ml/stablecoins_dropped.json)",
    )
    try:
        inter = interactions_fixed(ev, log)
        err = ""
    except Exception as e:  # the whole page must still render
        inter = pd.DataFrame(
            [{"feature_a": "n/a", "feature_b": str(e)[:80], "mean_abs_interaction": np.nan}]
        )
        err = str(e)
    top_pair = (
        f"{inter.iloc[0]['feature_a']} x {inter.iloc[0]['feature_b']} at {inter.iloc[0]['mean_abs_interaction']:.4f}"
        if not err
        else "the call failed again"
    )
    regime = any(
        "BTC 30-day realized" in str(x) for x in pd.concat([inter["feature_a"], inter["feature_b"]])
    )
    doc.table(
        "interactions_3f",
        inter,
        what=(
            "Phase-1 section 3f, re-rendered. One row is a pair of context features; the number is how much the two move the model's predicted R together, "
            "beyond what each does alone (mean absolute SHAP interaction over 1,500 test-period rows). The phase-1 call crashed because the categorical columns "
            "were passed as text; here they are integer-coded first and model A is refit on the coded frame, same parameters, same features, same train rows. "
            "Look at whether the regime feature (BTC's 30-day realized-vol percentile, the top single feature in phase 1) is in the strongest pairs."
        ),
        verdict=(
            f"Verdict: {'supports' if regime else 'contradicts'} -- the BTC-vol regime feature also drives the strongest feature pairs, because the top pair is {top_pair}"
            + ("." if not err else f" ({err[:60]}).")
        ),
        grey_n=None,
        heading="0c. Section 3f re-rendered: strongest feature pairs (interactions, model A refit on coded categoricals)",
    )

    # ---------------- section 1: the cost model
    doc.h2("1. The cost model: what the exchange takes out of every row")
    params = cost_param_table()
    book_cost_pct = float(ev["cost_pct"].clip(*ev["cost_pct"].quantile([0.005, 0.995])).mean())
    book_loss_pct = float(ev["ret_pct"].mean())
    doc.table(
        "cost_params",
        params,
        what=(
            "The parameters, as the brief sets them and as the config block at the top of report_v3.py holds them. Entry is a stop-market at the break, so it pays the taker fee and slippage; "
            "a target exit is a resting limit (maker, no slippage); a stop exit, a timeout mark and the hold-N-bars exits of test 1 are taker. Funding is the coin's actual rate at every "
            "8-hour mark the trade is open across, paid by longs when positive and by shorts when negative. The brief's claim to check: costs are on the order of half of phase 1's loss."
        ),
        verdict=(
            f"Verdict: inconclusive -- costs are on the order of half the phase-1 loss, because the corrected book is not a loss before costs ({book_loss_pct:+.3f}% of price per trade) while the mean cost is {book_cost_pct:+.3f}%."
            if book_loss_pct >= 0
            else f"Verdict: {'supports' if 0.3 <= abs(book_cost_pct / book_loss_pct) <= 0.8 else 'contradicts'} -- costs are on the order of half the phase-1 loss, "
            f"because the mean cost is {book_cost_pct:+.3f}% of price per trade against a mean managed result of {book_loss_pct:+.3f}% of price ({abs(book_cost_pct / book_loss_pct):.0%} of the loss)."
        ),
        grey_n=None,
        heading="1a. Parameters",
    )
    ct = cost_by_tier(ev)
    big = ct[ct["n"] >= MIN_CELL]
    pos_before = big[big["mean_r_gross"] > 0]
    survivors = pos_before[pos_before["mean_r_net"] > 0]
    doc.table(
        "cost_by_tier",
        ct,
        what=(
            "One row is every phase-1 trade in one liquidity tier (1 = top 10 coins by 30-day volume, 2 = 11-50, 3 = the rest) and one family, under the phase-1 exits. "
            "Fees, slippage and funding are in R: dollars per $100 risked. A tier-3 alt with a tight stop pays more R per trade for the same percent fee, because the stop is a smaller slice of price. "
            "'Mean R before costs' is phase 1's number; 'after costs' is the same trades net. Look at how many positive cells survive."
        ),
        verdict=(
            f"Verdict: {'supports' if len(survivors) == 0 else 'contradicts'} -- any cell that reads positive before fees is at or under zero after them, because "
            f"{len(pos_before)} of {len(big)} cells (300+ rows) were positive before costs and {len(survivors)} stay positive after"
            + (
                f" ({', '.join(f'tier {int(r.liq_tier)} {r.family} {r.mean_r_net:+.3f}R' for r in survivors.itertuples())})"
                if len(survivors)
                else ""
            )
            + f"; the mean cost is {ct['cost_r'].mean():+.3f}R per trade."
        ),
        heading="1b. Cost per trade by liquidity tier and family, phase-1 exits",
    )

    # ---------------- section 2: the 15-minute check
    doc.h2("2. The 15-minute check on the trigger hour (reported, not fixed)")
    m15_note = ""
    if skip_15m:
        m15_note = "Skipped on request (--skip-15m): the 15-minute recomputation needs the archive's 15m klines for the sampled symbol-months."
    else:
        try:
            from analysis.strat_ml import m15_check

            m15_tab, m15_meta = m15_check.run(ev, n_rows=m15_rows, seed=RNG, log=log)
            numbers["m15_meta"] = m15_meta
        except Exception as e:  # the brief: one line saying so, then skip
            m15_note = f"Skipped: the 15-minute recomputation could not run here ({str(e)[:120]})."
            log(f"  15m check skipped: {e}")
    if m15_note:
        doc.p(m15_note)
    else:
        hourly_adv = float(
            m15_tab.loc[m15_tab["clock"] == "hourly (phase 1)", "adv_first_pct"].iloc[0]
        )
        m15_adv = float(
            m15_tab.loc[m15_tab["clock"] == "15-minute, trigger bar counted", "adv_first_pct"].iloc[
                0
            ]
        )
        m15_adv_x = float(
            m15_tab.loc[
                m15_tab["clock"] == "15-minute, trigger bar's adverse print ignored",
                "adv_first_pct",
            ].iloc[0]
        )
        doc.table(
            "m15_first_excursion",
            m15_tab,
            what=(
                f"Phase 1 asked which came first after the break, +0.25R in your favour ($25 on a $100 risk) or 0.25R against ($25 down), and counted the trigger hour's own low against the trade (the low may have printed before the break). "
                f"On a random sample of {m15_meta['rows']:,} rows ({m15_meta['symbol_months']:,} symbol-months of 15-minute bars pulled for it, {m15_meta['coins']} coins) the same question is re-read on 15-minute bars: "
                "the first 15-minute bar that trades through the level is the trigger bar, and the walk starts there. One row is one clock. 'Against first' is the share that went 0.25R against before 0.25R for; "
                "'mean R' and 'win %' are the phase-1 managed result of the rows in each group, after costs. Look at how far the against-first share falls from the hourly 68%."
            ),
            verdict=(
                f"Verdict: {'supports' if m15_adv < hourly_adv - 5 else 'contradicts'} -- the hourly 'against first' majority is an artefact of the trigger hour's own range, because "
                f"against-first is {hourly_adv:.1f}% on the hourly clock and {m15_adv:.1f}% on 15-minute bars with the trigger bar counted ({m15_adv_x:.1f}% ignoring the trigger bar's own adverse print; phase 1 estimated 27%)."
            ),
            grey_n=None,
            heading="2a. Which 0.25R move came first: hourly clock vs 15-minute clock, same rows",
        )
        doc.p(
            "Phase-1 sections 7b-7c should be read with the 15-minute version in mind: the clock itself is not rebuilt for the whole table in this phase (the brief: report, do not fix)."
        )

    # ---------------- section 3: test 1
    doc.h2("3. Test 1: raw forward drift, no exits (the gate)")
    doc.note(
        "<b>What this test is.</b> This is what you would make per $100 risked if you took every break and just held for N days: no stop, no target, fees, slippage and funding paid, "
        "then closed at that day's close. If it is zero, STRAT triggers on daily alts do not predict direction and no exit rule can fix that. If it is positive, the phase-1 exits were the problem "
        "and tests 2-3 go looking for the exit that keeps it. The gate: the alt-coin line continues only if, on 2025-26, the net 5-bar return is above zero with clustered z of 2 or more in at least one family."
    )
    doc.p(
        "Units: 'mean ret (ATR)' is the move in the break's direction in units of the coin's normal daily range, so coins that move at different speeds compare; 'mean ret (% of price)' is the same in percent of price; "
        "'mean R no stop' is the same divided by the row's stop distance, clipped at -5R and +10R exactly as phase 1's 'mean R no stop' column was, so the two reports line up. "
        "The % and ATR units are winsorized at the 2020-24 0.5th and 99.5th percentiles, chosen on the train period only. 'z (clustered)' is the mean divided by its standard error with every trigger on the same day "
        "treated as one observation (the brief: without clustering z inflates several-fold). 'cost (R)' is the mean total cost of that hold in R. 'win %' is the share of rows above zero net of costs, with its 95% band."
    )
    cells = [
        (str(r["family"]), r["mean_atr"], r["z"], int(r["n"]))
        for _, r in t_fam[(t_fam["horizon"] == 5) & (t_fam["family"] != "all")].iterrows()
    ]
    doc.table(
        "t1_family_horizon",
        t_fam,
        what=(
            "One row is every trigger of that family (the 'all' rows are the whole book), held for 1, 3, 5 or 10 daily bars with no stop and no target, costs paid. "
            "'Mean ret (ATR)' is the key column: 0.10 means price was on average a tenth of a normal day further along in the break's direction. Look at whether it is above zero and whether z is above 2; "
            "if both, there is drift to harvest. A number that is positive at 1 bar and gone by 5 is a bounce, not drift."
        ),
        verdict=verdict_line(hyp_drift(5, " (whole sample, by family)"), cells),
        cols=[
            "family",
            "horizon",
            "n",
            "days",
            "win_pct",
            "mean_pct",
            "mean_atr",
            "median_atr",
            "z",
            "mean_r",
            "cost_r",
        ],
        heading="3a. By family and horizon (the headline table)",
    )
    fig = chart_drift(ev)
    doc.chart(
        fig,
        "t1_drift_by_family",
        "Mean net forward return in ATRs against the hold, train (2020-24) and test (2025-26), 95% bands clustered by trigger date. A line rising from zero is drift; flat at zero is no drift; rising in train and flat in test is a regime story.",
    )
    cells = [
        (f"{r['pattern']} {r['direction']}", r["mean_atr"], r["z"], int(r["n"]))
        for _, r in t_pat.iterrows()
    ]
    doc.table(
        "t1_pattern_direction",
        t_pat.sort_values(["pattern", "direction"]),
        what=(
            "One row is one pattern in one direction, held 10 daily bars with no exits, costs paid. The ten pattern names are phase 1's. Look for any pattern-direction cell whose mean ATR return is "
            "above zero with z above 2, and then at whether its longs and shorts agree; a pattern that only works on one side in one regime is the year's trend, not the pattern."
        ),
        verdict=verdict_line(hyp_drift(10, " (by pattern and direction)"), cells),
        cols=[
            "pattern",
            "direction",
            "n",
            "days",
            "win_pct",
            "mean_pct",
            "mean_atr",
            "median_atr",
            "z",
            "mean_r",
            "cost_r",
        ],
        heading="3b. By pattern and direction, 10-bar hold",
    )
    cuts = ev.attrs["btc_vol_cuts"]
    cells = [
        (f"{r['btc_vol_tercile']} vol {r['family']}", r["mean_atr"], r["z"], int(r["n"]))
        for _, r in t_vol.iterrows()
    ]
    doc.table(
        "t1_btc_vol_family",
        t_vol,
        what=(
            f"One row is one BTC-volatility regime and one family, held 5 bars. The regime is BTC's 30-day realized-volatility percentile on the day before the trigger, cut into thirds at the 2020-24 values "
            f"({cuts[0]:.2f} and {cuts[1]:.2f}; the cut points were chosen on the train period and never touched). Phase 1 found this the strongest context feature. Look at whether drift lives in one regime only."
        ),
        verdict=verdict_line(hyp_drift(5, " in some BTC-volatility regime"), cells),
        cols=[
            "btc_vol_tercile",
            "family",
            "n",
            "days",
            "win_pct",
            "mean_pct",
            "mean_atr",
            "median_atr",
            "z",
            "mean_r",
            "cost_r",
        ],
        heading="3c. By BTC 30-day realized-vol tercile and family, 5-bar hold",
    )
    cells = [
        (f"{int(r['year'])} {r['family']}", r["mean_atr"], r["z"], int(r["n"]))
        for _, r in t_year.iterrows()
    ]
    doc.table(
        "t1_year_family",
        t_year,
        what=(
            "One row is one calendar year and one family, held 5 bars. This is the regime-drift check: a drift that exists only in 2021 (longs) or 2022 (shorts) is the year's trend wearing a pattern's name. "
            "Look for a family whose sign holds across years, then at 2025 and 2026, which no threshold on this page has seen."
        ),
        verdict=verdict_line(hyp_drift(5, " consistently across years"), cells),
        cols=[
            "year",
            "family",
            "n",
            "days",
            "win_pct",
            "mean_pct",
            "mean_atr",
            "median_atr",
            "z",
            "mean_r",
            "cost_r",
        ],
        heading="3d. By year and family, 5-bar hold",
    )
    cells = [
        (f"tier {r['liq_tier']}", r["mean_atr"], r["z"], int(r["n"]))
        for _, r in t_liq[t_liq["liq_tier"] != "all"].iterrows()
    ]
    doc.table(
        "t1_liq_tier",
        t_liq,
        what=(
            "One row is one liquidity tier (1 = top 10 coins by 30-day volume on the day before the trigger, 2 = 11-50, 3 = the rest), held 5 bars, costs paid at that tier's slippage. "
            "Look at whether the thin tier 3, where slippage is highest and most of the rows are, behaves differently from the liquid tiers."
        ),
        verdict=verdict_line(hyp_drift(5, " in some liquidity tier"), cells),
        cols=[
            "liq_tier",
            "horizon",
            "n",
            "days",
            "win_pct",
            "mean_pct",
            "mean_atr",
            "median_atr",
            "z",
            "mean_r",
            "cost_r",
        ],
        heading="3e. By liquidity tier, 5-bar hold",
    )
    tt_cols = [
        "family",
        "horizon",
        "n_train",
        "mean_atr_train",
        "z_train",
        "mean_r_train",
        "n_test",
        "mean_atr_test",
        "z_test",
        "mean_pct_test",
        "mean_r_test",
        "cost_r_test",
        "win_pct_test",
    ]
    cells = [
        (
            f"{r['family']} {int(r['horizon'])}-bar",
            r["mean_atr_test"],
            r["z_test"],
            int(r["n_test"]),
        )
        for _, r in tt_fam_all_h[tt_fam_all_h["family"] != "all"].iterrows()
    ]
    doc.table(
        "t1_train_test_family",
        tt_fam_all_h.sort_values(["family", "horizon"]),
        what=(
            "Table 3a split into the period the rules were found on (train, triggers before 2025-01-01) and the period they never saw (test, 2025-26). One row is one family at one hold. "
            "A finding exists only if it holds on both. The test columns are the gate: look for a family whose test mean ATR return is above zero with test z of 2 or more at the 5-bar hold."
        ),
        verdict=verdict_line(
            hyp_drift(5, " on the unseen 2025-26 period (the gate)"),
            [c for c in cells if c[0].endswith("5-bar")],
        ),
        cols=tt_cols,
        grey_n="n_test",
        heading="3f. Train vs test: by family and horizon (the gate table)",
    )
    cells = [
        (
            f"{r['btc_vol_tercile']} vol {r['family']}",
            r["mean_atr_test"],
            r["z_test"],
            int(r["n_test"]),
        )
        for _, r in tt_vol.iterrows()
    ]
    doc.table(
        "t1_train_test_btc_vol",
        tt_vol,
        what=(
            "Table 3c split train vs test, 5-bar hold. One row is one BTC-volatility regime and one family. The cut points come from 2020-24; the 2025-26 columns are an honest out-of-sample read of the same cells. "
            "Look for a regime-family cell that is positive with z above 2 on both sides; one that is positive on train and flat on test fit the past."
        ),
        verdict=verdict_line(
            hyp_drift(5, " in some BTC-volatility regime, on both train and test"), cells
        ),
        cols=["btc_vol_tercile"] + tt_cols[1:],
        grey_n="n_test",
        heading="3g. Train vs test: by BTC-vol tercile and family, 5-bar hold",
    )

    # ---------------- caveats (last)
    doc.h2("4. Caveats that travel with every number above")
    doc.bullets(
        [
            "Fills at the broken level plus the model's slippage, every trigger taken, no sizing beyond the $100-per-stop convention. Funding is charged on the entry notional at the archive's actual marks; the HIP-3 snapshot carries no funding series.",
            "The test-1 exit is 'close at the end of day D+N'; a position opened mid-day on day D is held N full days plus the rest of day D. The trigger hour itself and all hours after it count.",
            "'Mean R no stop' divides a price move by a stop distance the trade never used; a tiny setup bar makes a huge R for an ordinary move, which is why the ATR and percent units carry the verdicts and the R unit is clipped as phase 1 clipped it.",
            "Clustering by trigger date treats every coin's trigger on one day as one draw of the market. It does not remove the overlap between consecutive days (a 10-bar hold spans ten trigger days), so even the clustered z is on the generous side for the 10-bar horizon.",
            "Half the coins listed in 2025-26, so the test period is young alts; dead coins are in; a coin that died inside the window is censored out, as in phase 1.",
            "Nothing on this page was chosen on 2025-26 data: the winsor bounds, the BTC-vol cut points and the cost parameters are from 2020-24 or the brief.",
        ]
    )
    doc.p(
        f"<span class=muted>Built in {time.time() - t0:.0f} s. Code: analysis/strat_ml/report_v3.py (phase 1: report.py, untouched). Definitions: docs/experiments/strat_ml_phase2_events_design.md; spec: strat_ml_phase3_brief.md.</span>"
    )

    # ---------------- the one-page summary under the gate line (brief step 11)
    next_phase = (
        "Next phase: tests 2-5 on the alt-coin table in the brief's order (test 2 continuation exits, test 4 continuity gated on structure, test 3 the fair-line sweep, test 5 time exhaustion), then the HIP-3 session branch."
        if gate_ok
        else "Next phase: the alt-coin line stops here; the HIP-3 session branch (brief section 11: test 1 on the session build clustered by date, leave-one-ticker-out, the gap rule, the fair-line sweep) is the next run, and the underlying-stock control needs an equity feed this environment does not have."
    )
    doc.blocks.insert(
        summary_slot, ("p", "<b>Summary.</b> Each table's verdict, verbatim, in page order:")
    )
    doc.blocks.insert(summary_slot + 1, ("ul", [f"<i>{h}</i>: {v}" for h, v in doc.verdicts]))
    doc.blocks.insert(summary_slot + 2, ("p", next_phase))

    # ---------------- write
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / CHART_DIR).mkdir(exist_ok=True)
    for name, png in doc.pngs.items():
        (REPORTS / CHART_DIR / f"{name}.png").write_bytes(png)
    out_html = REPORTS / f"{TITLE}.html"
    out_html.write_text(doc.html(), encoding="utf-8")
    (REPORTS / f"{TITLE}.md").write_text(doc.md(), encoding="utf-8")
    numbers["tables"] = {k: v.round(5).to_dict(orient="records") for k, v in doc.tables.items()}
    numbers["verdicts"] = doc.verdicts
    numbers["btc_vol_cuts"] = ev.attrs["btc_vol_cuts"]
    numbers["rows"] = int(len(ev))
    numbers["coins"] = int(ev["symbol"].nunique())
    (REPORTS / "report_v3_numbers.json").write_text(
        json.dumps(numbers, indent=1, default=str), encoding="utf-8"
    )
    results = (
        [
            "# STRAT trigger research: phase 3 results (stopped at the test-1 gate)",
            "",
            f"Built {stamp} by analysis/strat_ml/report_v3.py from the corrected phase-1 event table ({len(ev):,} rows, {ev['symbol'].nunique()} coins). Full page: analysis/strat_ml/reports/{TITLE}.md (and .html).",
            "",
            "**" + gate_line + "**",
            "",
            "## Verdicts, verbatim",
            "",
        ]
        + [f"- *{_strip(h)}*: {v}" for h, v in doc.verdicts]
        + ["", "## What the next phase should be", "", _strip(next_phase), ""]
    )
    RESULTS_DOC.write_text("\n".join(results), encoding="utf-8")
    log(
        f"report -> {out_html} ({out_html.stat().st_size / 1e6:.1f} MB), .md, {len(doc.pngs)} charts, numbers json, {RESULTS_DOC.name}; {time.time() - t0:.0f}s"
    )
    return out_html


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--events", default=str(EVENTS_PATH))
    ap.add_argument("--skip-15m", action="store_true")
    ap.add_argument("--m15-rows", type=int, default=M15_ROWS)
    a = ap.parse_args(argv)
    build(events=Path(a.events), skip_15m=a.skip_15m, m15_rows=a.m15_rows)


if __name__ == "__main__":
    main(sys.argv[1:])
