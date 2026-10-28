"""Section-5 check of the phase-3 brief: re-read "which 0.25R move came first" on 15-minute bars.

The phase-1 excursion clock walks hourly bars from the trigger hour and counts that hour's own
low (long) / high (short) against the trade, although the adverse print may have come before the
break. The brief asks for the same question on the archive's 15-minute klines for a random
20,000-row sample, reported before / after in one table, and NOT for a rebuild of the clock.

Data: Binance Vision publishes 15m klines in the same layout as the 1h files (one zip per
symbol-month, daily zips for the months without a monthly file yet). They are pulled only for the
symbol-months the sample touches, into their own raw folder (the 1h parquet builder concatenates
every zip in a symbol's folder, so the two intervals must never share one). Nothing is synthesized.

Sample: a two-stage random sample so the pull stays small. Symbol-months (a coin and the month of
the trigger) are drawn uniformly at random until they hold at least n rows, then exactly n rows are
drawn at random from those. Stated in the report.

  uv run python -m analysis.strat_ml.m15_check --rows 2000   # standalone dry run on the event table
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.domino.census import DAY, HOUR
from analysis.strat_ml.binance_vision import (
    DATA,
    Archive,
    dataset_prefix,
    file_stamp,
    read_zip_csv,
)
from analysis.strat_ml.events import EVENTS_PATH, to_ms

RAW15 = DATA / "raw15m" / "klines"
INTERVAL = "15m"
THRESHOLD = 0.25
WINDOW_BARS = 10  # the phase-1 10-daily-bar window


# ----------------------------------------------------------------------------- sampling


def sample_rows(ev: pd.DataFrame, n_rows: int, seed: int = 0) -> pd.DataFrame:
    block = ev["symbol"].astype(str) + "|" + ev["trigger_ts"].dt.strftime("%Y-%m")
    counts = block.value_counts()
    rng = np.random.default_rng(seed)
    order = rng.permutation(counts.index.to_numpy())
    chosen, total = [], 0
    for b in order:
        chosen.append(b)
        total += int(counts[b])
        if total >= n_rows:
            break
    pool = ev[block.isin(chosen)]
    return pool.sample(min(n_rows, len(pool)), random_state=seed)


def months_touched(rows: pd.DataFrame) -> set[tuple[str, str]]:
    """(symbol, 'YYYY-MM') for the trigger month and the month holding the window's last hour."""
    out: set[tuple[str, str]] = set()
    end = pd.to_datetime(
        rows["day"].to_numpy(np.int64) + WINDOW_BARS * DAY + 23 * HOUR, unit="ms", utc=True
    )
    for sym, a, b in zip(rows["symbol"].astype(str), rows["trigger_ts"], end):
        out.add((sym, a.strftime("%Y-%m")))
        out.add((sym, b.strftime("%Y-%m")))
    return out


# ----------------------------------------------------------------------------- pull


def _keys_for_month(archive: Archive, symbol: str, ym: str) -> list[str]:
    monthly = f"{dataset_prefix('klines', 'monthly', symbol, INTERVAL)}{symbol}-{INTERVAL}-{ym}.zip"
    if archive.list_keys(monthly):
        return [monthly]
    # the archive head month has no monthly file yet: every daily file of that month
    return archive.list_keys(
        f"{dataset_prefix('klines', 'daily', symbol, INTERVAL)}{symbol}-{INTERVAL}-{ym}-"
    )


def fetch_months(
    pairs: set[tuple[str, str]], workers: int = 8, log=print
) -> dict[tuple[str, str], list[Path]]:
    """Download the 15m zips of every (symbol, month) into RAW15 (cached, checksum-verified)."""
    archive = Archive()
    out: dict[tuple[str, str], list[Path]] = {}
    t0 = time.time()

    def one(pair):
        sym, ym = pair
        folder = RAW15 / sym
        cached = sorted(folder.glob(f"{sym}-{INTERVAL}-{ym}*.zip")) if folder.exists() else []
        if cached and any(file_stamp(p.name)[:7] == ym for p in cached):  # monthly or daily files
            return pair, cached, 0
        keys = _keys_for_month(archive, sym, ym)
        paths = []
        for k in keys:
            dest = folder / k.rsplit("/", 1)[-1]
            archive.download(k, dest)
            paths.append(dest)
        return pair, paths, len(keys)

    new = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, p): p for p in pairs}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                pair, paths, n = f.result()
                out[pair] = paths
                new += n
            except Exception as e:  # a missing month leaves its rows out, counted below
                log(f"    15m {futs[f]}: {e}")
            if i % 200 == 0 or i == len(futs):
                log(
                    f"    15m pull [{i}/{len(futs)} {time.time() - t0:.0f}s] {new} files downloaded"
                )
    return out


def bars_15m(paths: list[Path]) -> pd.DataFrame:
    frames = [read_zip_csv(p, "klines") for p in paths]
    if not frames:
        return pd.DataFrame(columns=["t", "h", "l"])
    df = pd.concat(frames, ignore_index=True).drop_duplicates("open_time").sort_values("open_time")
    return pd.DataFrame(
        {
            "t": to_ms(df["open_time"]),
            "h": df["high"].to_numpy(float),
            "l": df["low"].to_numpy(float),
            "v": df["volume"].to_numpy(float),
        }
    )


# ----------------------------------------------------------------------------- the read


def first_excursion(
    t: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,  # noqa: E741
    trigger_time: int,
    end_time: int,
    level: float,
    r: float,
    direction: str,
    threshold: float = THRESHOLD,
) -> tuple[str, str]:
    """(counted, ignored): which `threshold`R move came first on these bars, with the trigger
    bar's own adverse print counted (phase 1's pessimistic convention) and with it ignored.

    The trigger bar = the first bar inside the trigger hour that trades through the level. The walk
    runs from it to `end_time` (exclusive). A tie inside one bar reads as against (pessimistic).
    Returns 'fav' / 'adv' / 'none', or 'no_bars' when the trigger hour has no break on these bars."""
    in_hour = (t >= trigger_time) & (t < trigger_time + HOUR)
    if direction == "long":
        broke = in_hour & (h > level)
    else:
        broke = in_hour & (l < level)
    idx = np.flatnonzero(broke)
    if len(idx) == 0:
        return "no_bars", "no_bars"
    k = int(idx[0])
    e = int(np.searchsorted(t, end_time, side="left"))
    hh, ll = h[k:e], l[k:e]
    if direction == "long":
        fav = (hh - level) / r
        adv = (level - ll) / r
    else:
        fav = (level - ll) / r
        adv = (hh - level) / r
    fi = np.flatnonzero(fav >= threshold)
    ai = np.flatnonzero(adv >= threshold)
    f0 = int(fi[0]) if len(fi) else None
    a0 = int(ai[0]) if len(ai) else None

    def which(f, a):
        if f is None and a is None:
            return "none"
        if a is None or (f is not None and f < a):
            return "fav"
        return "adv"

    counted = which(f0, a0)
    ai2 = np.flatnonzero(adv[1:] >= threshold) + 1  # the trigger bar's adverse print ignored
    a1 = int(ai2[0]) if len(ai2) else None
    ignored = which(f0, a1)
    return counted, ignored


def read_sample(
    rows: pd.DataFrame, files: dict[tuple[str, str], list[Path]], log=print
) -> pd.DataFrame:
    out = rows[
        [
            "symbol",
            "trigger_time",
            "day",
            "level",
            "r",
            "direction",
            "first_excursion",
            "r10_net",
            "r10_w",
            "win",
        ]
    ].copy()
    out["symbol"] = out["symbol"].astype(str)
    out["m15_counted"] = "no_bars"
    out["m15_ignored"] = "no_bars"
    end = out["day"].to_numpy(np.int64) + WINDOW_BARS * DAY + 24 * HOUR
    out["end_ms"] = end
    for sym, g in out.groupby("symbol"):
        months = sorted(
            {
                (sym, m)
                for m in pd.to_datetime(g["trigger_time"], unit="ms", utc=True).dt.strftime("%Y-%m")
            }
            | {
                (sym, m)
                for m in pd.to_datetime(g["end_ms"], unit="ms", utc=True).dt.strftime("%Y-%m")
            }
        )
        paths = [p for m in months for p in files.get(m, [])]
        if not paths:
            continue
        bars = bars_15m(paths)
        t, h, l = bars["t"].to_numpy(np.int64), bars["h"].to_numpy(float), bars["l"].to_numpy(float)  # noqa: E741
        counted, ignored = [], []
        for row in g.itertuples(index=False):
            c, i = first_excursion(
                t,
                h,
                l,
                int(row.trigger_time),
                int(row.end_ms),
                float(row.level),
                float(row.r),
                str(row.direction),
            )
            counted.append(c)
            ignored.append(i)
        out.loc[g.index, "m15_counted"] = counted
        out.loc[g.index, "m15_ignored"] = ignored
    return out.drop(columns=["end_ms"])


def split_table(res: pd.DataFrame) -> pd.DataFrame:
    """One row per clock: shares of fav / adv / none first, and the phase-1 managed result
    (after costs) of the rows in the fav-first and adv-first groups."""
    ok = res[(res["m15_counted"] != "no_bars")]
    rows = []
    for clock, col in (
        ("hourly (phase 1)", "first_excursion"),
        ("15-minute, trigger bar counted", "m15_counted"),
        ("15-minute, trigger bar's adverse print ignored", "m15_ignored"),
    ):
        s = ok[col].astype(str)
        n = len(s)
        fav = ok[s == "fav"]
        adv = ok[s == "adv"]
        k = int((s == "fav").sum())
        p = k / n if n else np.nan
        z = 1.96
        d = 1 + z * z / n if n else 1
        centre = (p + z * z / (2 * n)) / d if n else np.nan
        half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d if n else np.nan
        rows.append(
            {
                "clock": clock,
                "n": n,
                "fav_first_pct": 100 * p,
                "fav_lo": 100 * (centre - half),
                "fav_hi": 100 * (centre + half),
                "adv_first_pct": 100 * (s == "adv").mean() if n else np.nan,
                "none_pct": 100 * (s == "none").mean() if n else np.nan,
                "fav_first_mean_r": float(fav["r10_net"].mean()) if len(fav) else np.nan,
                "fav_first_win_pct": 100 * float((fav["r10_net"] > 0).mean())
                if len(fav)
                else np.nan,
                "adv_first_mean_r": float(adv["r10_net"].mean()) if len(adv) else np.nan,
                "adv_first_win_pct": 100 * float((adv["r10_net"] > 0).mean())
                if len(adv)
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def run(
    ev: pd.DataFrame, n_rows: int = 20_000, seed: int = 0, workers: int = 8, log=print
) -> tuple[pd.DataFrame, dict]:
    t0 = time.time()
    rows = sample_rows(ev, n_rows, seed)
    pairs = months_touched(rows)
    log(
        f"  15m check: {len(rows):,} rows, {rows['symbol'].nunique()} coins, {len(pairs)} symbol-months to pull"
    )
    files = fetch_months(pairs, workers, log)
    res = read_sample(rows, files, log)
    tab = split_table(res)
    meta = {
        "rows": int(len(rows)),
        "rows_read": int((res["m15_counted"] != "no_bars").sum()),
        "coins": int(rows["symbol"].nunique()),
        "symbol_months": len(pairs),
        "symbol_months_fetched": len(files),
        "seed": seed,
        "seconds": round(time.time() - t0),
    }
    log(f"  15m check done: {meta}")
    return tab, meta


def main(argv: list[str] | None = None) -> None:
    from analysis.strat_ml import report_v3

    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--events", default=str(EVENTS_PATH))
    ap.add_argument("--rows", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    _, ev, _ = report_v3.load_corrected(Path(a.events))
    tab, meta = run(ev, a.rows, a.seed)
    print(tab.round(3).to_string(index=False))
    print(meta)


if __name__ == "__main__":
    main(sys.argv[1:])
