"""Binance Vision public-archive downloader and parquet cache (STRAT ML vessel, Phase 1).

Plan and findings: docs/experiments/strat_ml_phase1_data_plan.md. The short form:

  source    data.binance.vision (a public S3 bucket, `futures/um` = USDT-M perps). The CDN host
            is refused by the cloud session's proxy; the bucket endpoint is not, and it also
            answers S3 ListBucket queries. BASE_URLS is tried in order.
  datasets  klines (monthly + daily files), fundingRate (monthly only), metrics (daily only)
  cache     raw zips, checksum-verified, under data/raw; normalised parquet under data/parquet;
            the parquet build is re-runnable offline from the raw zips.
  universe  every symbol folder in the monthly klines listing, with first / last month and a
            point-in-time delisted flag (last month older than the archive head month).

Research only: no exchange keys, no orders, no live API. The live API is never called.

CLI:
  uv run python -m analysis.strat_ml.binance_vision universe
  uv run python -m analysis.strat_ml.binance_vision fetch --symbols BTCUSDT ETHUSDT \
      --datasets klines fundingRate [--since 2024-01-01] [--workers 4]
  uv run python -m analysis.strat_ml.binance_vision build --symbols BTCUSDT --datasets klines
  uv run python -m analysis.strat_ml.binance_vision status
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HERE = Path(__file__).parent
DATA = HERE / "data"
RAW = DATA / "raw"
PARQUET = DATA / "parquet"

BASE_URLS = (
    "https://data.binance.vision",  # the documented CDN host (workstation)
    "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision",  # the bucket (cloud session)
)
LIST_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
MARKET = "futures/um"

# dataset -> which file periods the archive publishes (checked 2026-10-17; see the plan doc)
PERIODS = {
    "klines": ("monthly", "daily"),
    "fundingRate": ("monthly",),
    "metrics": ("daily",),
}
KLINE_COLS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
]
FUNDING_COLS = ["calc_time", "funding_interval_hours", "last_funding_rate"]
METRICS_COLS = [
    "create_time",
    "symbol",
    "sum_open_interest",
    "sum_open_interest_value",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
    "count_long_short_ratio",
    "sum_taker_long_short_vol_ratio",
]
TIME_KEY = {"klines": "open_time", "fundingRate": "calc_time", "metrics": "create_time"}
THROTTLE_S = 0.05
HOUR_MS = 3_600_000


# ----------------------------------------------------------------------------- paths / keys


def dataset_prefix(dataset: str, period: str, symbol: str, interval: str = "1h") -> str:
    """Archive key prefix of one symbol's files, e.g. data/futures/um/monthly/klines/BTCUSDT/1h/."""
    if period not in PERIODS[dataset]:
        raise ValueError(f"{dataset} has no {period} files in the archive")
    tail = f"{symbol}/{interval}/" if dataset == "klines" else f"{symbol}/"
    return f"data/{MARKET}/{period}/{dataset}/{tail}"


def file_stamp(key: str) -> str:
    """'YYYY-MM' (monthly) or 'YYYY-MM-DD' (daily) from an archive key or file name."""
    m = re.search(r"-(\d{4}-\d{2}(?:-\d{2})?)\.zip$", key)
    if not m:
        raise ValueError(f"not an archive data file: {key}")
    return m.group(1)


def raw_path(dataset: str, symbol: str, key: str) -> Path:
    return RAW / dataset / symbol / key.rsplit("/", 1)[-1]


def parquet_path(dataset: str, symbol: str) -> Path:
    return PARQUET / dataset / f"{symbol}.parquet"


def manifest_path(dataset: str, symbol: str) -> Path:
    return PARQUET / dataset / f"{symbol}.manifest.json"


# ----------------------------------------------------------------------------- HTTP


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=16))
    s.headers["User-Agent"] = "tradingview-backtesting strat_ml phase1 (research)"
    return s


class Archive:
    """One bucket client: listing via the S3 endpoint, downloads via the first base URL that works."""

    def __init__(
        self, session: requests.Session | None = None, base_urls=BASE_URLS, list_url=LIST_URL
    ):
        self.session = session or make_session()
        self.base_urls = tuple(base_urls)
        self.list_url = list_url
        self.base_url: str | None = None  # resolved on first successful download
        self._lock = threading.Lock()

    # listing ------------------------------------------------------------------------------

    def list_keys(self, prefix: str) -> list[str]:
        """Every .zip object key under `prefix` (paged; CHECKSUM sidecars dropped)."""
        keys: list[str] = []
        marker = ""
        while True:
            params = {"prefix": prefix, "max-keys": "1000"}
            if marker:
                params["marker"] = marker
            r = self.session.get(self.list_url, params=params, timeout=60)
            r.raise_for_status()
            page = re.findall(r"<Key>([^<]+)</Key>", r.text)
            keys += [k for k in page if k.endswith(".zip")]
            if "<IsTruncated>true</IsTruncated>" not in r.text or not page:
                break
            marker = page[-1]
            time.sleep(THROTTLE_S)
        return keys

    def list_folders(self, prefix: str) -> list[str]:
        """Immediate sub-folder names under `prefix` (S3 CommonPrefixes, paged)."""
        names: list[str] = []
        marker = ""
        while True:
            params = {"prefix": prefix, "delimiter": "/", "max-keys": "1000"}
            if marker:
                params["marker"] = marker
            r = self.session.get(self.list_url, params=params, timeout=60)
            r.raise_for_status()
            page = re.findall(r"<Prefix>" + re.escape(prefix) + r"([^/<]+)/</Prefix>", r.text)
            names += page
            if "<IsTruncated>true</IsTruncated>" not in r.text or not page:
                break
            marker = prefix + page[-1] + "/"
            time.sleep(THROTTLE_S)
        return names

    # download -----------------------------------------------------------------------------

    def _get_bytes(self, key: str) -> bytes:
        bases = (self.base_url,) if self.base_url else self.base_urls
        last: Exception | None = None
        for base in bases:
            try:
                r = self.session.get(f"{base}/{key}", timeout=120)
                if r.status_code == 404:
                    raise FileNotFoundError(key)
                r.raise_for_status()
                with self._lock:
                    self.base_url = base
                return r.content
            except FileNotFoundError:
                raise
            except requests.RequestException as e:  # proxy refusal, TLS, timeouts
                last = e
        raise RuntimeError(f"no base URL served {key}: {last}")

    def download(self, key: str, dest: Path, verify: bool = True) -> bool:
        """Fetch one object into `dest` (atomic); verify its sha256 sidecar. False if cached."""
        if dest.exists():
            return False
        body = self._get_bytes(key)
        if verify:
            sidecar = self._get_bytes(key + ".CHECKSUM").decode().split()
            check_sha256(body, sidecar[0] if sidecar else "", key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(body)
        tmp.replace(dest)
        time.sleep(THROTTLE_S)
        return True


def check_sha256(body: bytes, expected: str, name: str = "") -> None:
    got = hashlib.sha256(body).hexdigest()
    if expected.lower() != got:
        raise ValueError(f"checksum mismatch for {name}: expected {expected}, got {got}")


# ----------------------------------------------------------------------------- file selection


def select_keys(
    monthly: list[str],
    daily: list[str],
    since: str | None = None,
    until: str | None = None,
) -> list[str]:
    """Monthly files first; daily files only for days AFTER the last monthly month.

    `since` / `until` are 'YYYY-MM-DD' bounds applied on the file stamp (a monthly file is kept
    when any day of its month is in range).
    """
    monthly = sorted(monthly, key=file_stamp)
    daily = sorted(daily, key=file_stamp)
    last_month = file_stamp(monthly[-1]) if monthly else ""
    chosen = list(monthly) + [k for k in daily if file_stamp(k)[:7] > last_month]
    if since:
        chosen = [k for k in chosen if _stamp_end(file_stamp(k)) >= since]
    if until:
        chosen = [k for k in chosen if file_stamp(k) <= until]
    return chosen


def months_after(last_month: str, today: date) -> list[str]:
    """'YYYY-MM' stamps strictly after `last_month` up to and including today's month."""
    y, m = int(last_month[:4]), int(last_month[5:7])
    out = []
    while (y, m) < (today.year, today.month):
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        out.append(f"{y:04d}-{m:02d}")
    return out


def _stamp_end(stamp: str) -> str:
    """Last calendar day covered by a file stamp, as 'YYYY-MM-DD'."""
    if len(stamp) == 10:
        return stamp
    y, m = int(stamp[:4]), int(stamp[5:7])
    nxt = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (nxt - pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def fetch_symbol(
    archive: Archive,
    symbol: str,
    dataset: str,
    interval: str = "1h",
    since: str | None = None,
    until: str | None = None,
    workers: int = 4,
    log=print,
) -> dict:
    """Download every archive file of one symbol / dataset into the raw cache."""
    monthly = daily = []
    if "monthly" in PERIODS[dataset]:
        monthly = archive.list_keys(dataset_prefix(dataset, "monthly", symbol, interval))
    if "daily" in PERIODS[dataset]:
        daily_prefix = dataset_prefix(dataset, "daily", symbol, interval)
        if monthly:
            # only the months after the last monthly file are needed from the daily tree; for a
            # delisted symbol that is normally nothing, for a live one the current 1-2 months
            name = f"{symbol}-{interval}-" if dataset == "klines" else f"{symbol}-{dataset}-"
            daily = []
            for ym in months_after(file_stamp(monthly[-1]), date.today()):
                daily += archive.list_keys(f"{daily_prefix}{name}{ym}-")
        else:
            daily = archive.list_keys(daily_prefix)
    keys = select_keys(monthly, daily, since, until)
    if not keys:
        log(f"  {symbol} {dataset}: nothing in the archive")
        return {"symbol": symbol, "dataset": dataset, "files": 0, "new": 0, "keys": []}
    new = 0
    errors: list[str] = []

    def one(key: str) -> bool:
        return archive.download(key, raw_path(dataset, symbol, key))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, k): k for k in keys}
        for f in as_completed(futs):
            try:
                new += int(f.result())
            except Exception as e:  # keep going; report at the end
                errors.append(f"{futs[f]}: {e}")
    log(
        f"  {symbol} {dataset}: {len(keys)} files ({file_stamp(keys[0])} .. {file_stamp(keys[-1])}),"
        f" {new} downloaded, {len(keys) - new - len(errors)} cached, {len(errors)} errors"
    )
    for e in errors[:10]:
        log("    ERROR " + e)
    return {
        "symbol": symbol,
        "dataset": dataset,
        "files": len(keys),
        "new": new,
        "errors": errors,
        "keys": keys,
    }


# ----------------------------------------------------------------------------- parsing


def _looks_like_header(first_line: str) -> bool:
    return not re.match(r"^\s*[\d.\-]", first_line)


def _epoch_to_utc(s: pd.Series) -> pd.Series:
    """ms (or us, guarded) epoch integers -> tz-aware UTC timestamps."""
    v = pd.to_numeric(s, errors="coerce").astype("float64")
    unit = "us" if v.dropna().gt(1e14).any() else "ms"
    return pd.to_datetime(v.astype("int64"), unit=unit, utc=True)


def read_zip_csv(path: Path | bytes, dataset: str) -> pd.DataFrame:
    """One archive zip -> normalised DataFrame (header sniffed; types fixed; UTC times)."""
    src = io.BytesIO(path) if isinstance(path, bytes) else path
    with zipfile.ZipFile(src) as z:
        names = [n for n in z.namelist() if n.endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"expected one csv in {path}, got {names}")
        text = z.read(names[0]).decode("utf-8")
    first = text.split("\n", 1)[0]
    header = 0 if _looks_like_header(first) else None
    if dataset == "klines":
        df = pd.read_csv(io.StringIO(text), header=header)
        if header is None:
            df.columns = KLINE_COLS[: df.shape[1]]
        df = df.drop(columns=[c for c in ("ignore",) if c in df.columns])
        for c in ("open_time", "close_time"):
            df[c] = _epoch_to_utc(df[c])
        for c in (
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "taker_buy_volume",
            "taker_buy_quote_volume",
        ):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
        df["count"] = pd.to_numeric(df["count"], errors="coerce").astype("Int64")
        return df[[c for c in KLINE_COLS if c in df.columns]]
    if dataset == "fundingRate":
        df = pd.read_csv(io.StringIO(text), header=header)
        if header is None:
            df.columns = FUNDING_COLS if df.shape[1] == 3 else ["calc_time", "last_funding_rate"]
        if "funding_interval_hours" not in df.columns:
            df["funding_interval_hours"] = pd.NA
        df["calc_time"] = _epoch_to_utc(df["calc_time"])
        df["funding_interval_hours"] = pd.to_numeric(
            df["funding_interval_hours"], errors="coerce"
        ).astype("Int64")
        df["last_funding_rate"] = pd.to_numeric(df["last_funding_rate"], errors="coerce").astype(
            "float64"
        )
        return df[FUNDING_COLS]
    if dataset == "metrics":
        df = pd.read_csv(io.StringIO(text), header=header)
        if header is None:
            df.columns = METRICS_COLS[: df.shape[1]]
        df["create_time"] = pd.to_datetime(df["create_time"], utc=True)
        for c in METRICS_COLS[2:]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
        # the 2026-03 backfill wrote every row twice (checked on BTCUSDT 2020-09-01)
        return df.drop_duplicates()[[c for c in METRICS_COLS if c in df.columns]]
    raise ValueError(f"unknown dataset {dataset}")


# ----------------------------------------------------------------------------- parquet build


def build_parquet(symbol: str, dataset: str, log=print, base_url: str | None = None) -> dict:
    """Concatenate the raw zips of one symbol / dataset into a parquet table + manifest."""
    folder = RAW / dataset / symbol
    files = (
        sorted(folder.glob("*.zip"), key=lambda p: file_stamp(p.name)) if folder.exists() else []
    )
    if not files:
        raise FileNotFoundError(f"no raw files for {symbol} {dataset} under {folder}")
    frames = [read_zip_csv(p, dataset) for p in files]
    df = pd.concat(frames, ignore_index=True)
    key = TIME_KEY[dataset]
    raw_rows = len(df)
    df = df.drop_duplicates(subset=[key], keep="last").sort_values(key).reset_index(drop=True)
    if not df[key].is_monotonic_increasing or df[key].duplicated().any():
        raise AssertionError(f"{symbol} {dataset}: time key not strictly increasing after dedupe")
    out = parquet_path(dataset, symbol)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    manifest = {
        "symbol": symbol,
        "dataset": dataset,
        "market": MARKET,
        "rows": int(len(df)),
        "raw_rows": int(raw_rows),
        "first": df[key].iloc[0].isoformat(),
        "last": df[key].iloc[-1].isoformat(),
        "files": [p.name for p in files],
        "source": base_url or "raw cache",
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if dataset == "klines":
        span_h = int((df[key].iloc[-1] - df[key].iloc[0]).total_seconds() // 3600) + 1
        manifest["missing_hours"] = int(span_h - len(df))
        # Binance keeps publishing flat zero-volume files for dead contracts (BTCSTUSDT sits at
        # one price from before 2024-02 to 2026-06): record where real trading ended so the
        # event build can trim the zombie tail. Nothing is trimmed here; the cache stays raw.
        traded = df.index[df["volume"] > 0]
        manifest["zero_volume_hours"] = int((df["volume"] <= 0).sum())
        manifest["last_traded"] = df[key].iloc[traded[-1]].isoformat() if len(traded) else None
        manifest["trailing_dead_hours"] = (
            int(len(df) - 1 - traded[-1]) if len(traded) else int(len(df))
        )
    manifest_path(dataset, symbol).write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log(
        f"  {symbol} {dataset}: {manifest['rows']} rows {manifest['first'][:10]} .. {manifest['last'][:10]}"
        + (
            f", {manifest['missing_hours']} missing hours, {manifest['trailing_dead_hours']} dead tail"
            if dataset == "klines"
            else ""
        )
        + f" -> {_display(out)}"
    )
    return manifest


def _display(p: Path) -> str:
    try:
        return str(p.relative_to(HERE.parent.parent))
    except ValueError:
        return str(p)


def load(symbol: str, dataset: str) -> pd.DataFrame:
    return pd.read_parquet(parquet_path(dataset, symbol))


# ----------------------------------------------------------------------------- universe


SETTLED_RE = re.compile(r"SETTLED$|_SETTLED$")


def classify_folder(name: str) -> str:
    """Archive symbol folder -> 'usdt_perp' | 'settled_stub' | 'other_quote'."""
    if SETTLED_RE.search(name):
        return "settled_stub"
    if name.endswith("USDT") and "_" not in name:
        return "usdt_perp"
    return "other_quote"


def build_universe(
    archive: Archive, interval: str = "1h", log=print, workers: int = 8
) -> pd.DataFrame:
    """Every symbol folder in the monthly klines tree with its first / last month.

    delisted = last month older than the archive head month (the newest month any symbol has).
    That is a point-in-time definition computable from the archive alone (no live API).
    """
    root = f"data/{MARKET}/monthly/klines/"
    names = archive.list_folders(root)
    log(f"  {len(names)} symbol folders under {root}")

    def months(name: str) -> tuple[str, list[str]]:
        return name, [file_stamp(k) for k in archive.list_keys(f"{root}{name}/{interval}/")]

    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for name, stamps in ex.map(months, names):
            rows.append(
                {
                    "symbol": name,
                    "kind": classify_folder(name),
                    "first_month": stamps[0] if stamps else None,
                    "last_month": stamps[-1] if stamps else None,
                    "months": len(stamps),
                }
            )
    df = pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)
    head = df["last_month"].dropna().max()
    df["archive_head_month"] = head
    df["delisted"] = df["last_month"].notna() & (df["last_month"] < head)
    DATA.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DATA / "universe.parquet", index=False)
    (DATA / "universe.json").write_text(
        json.dumps(
            {
                "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "archive_head_month": head,
                "folders": int(len(df)),
                "usdt_perps": int((df["kind"] == "usdt_perp").sum()),
                "usdt_perps_delisted": int(((df["kind"] == "usdt_perp") & df["delisted"]).sum()),
                "settled_stubs": int((df["kind"] == "settled_stub").sum()),
                "other_quote": int((df["kind"] == "other_quote").sum()),
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    return df


SUMMARY_PATH = HERE / "universe_summary.json"  # committable (outside the gitignored data/)


def usdt_universe() -> list[str]:
    """USDT perp folder names from the universe manifest (run `universe` first)."""
    u = pd.read_parquet(DATA / "universe.parquet")
    return sorted(u.loc[u["kind"] == "usdt_perp", "symbol"].tolist())


def summarize(log=print) -> dict:
    """Fold every klines / funding manifest into one small JSON that CAN be committed.

    Per symbol: first / last bar, last traded bar (volume > 0), dead tail, missing hours,
    funding coverage. delisted_by_volume = last traded bar older than 45 days before the
    newest last-traded bar in the set (a dead contract stops printing volume for good; a
    live one never stops for 45 days). Nothing here is a feature; it is the roster.
    """
    rows = {}
    for mp in sorted(PARQUET.glob("klines/*.manifest.json")):
        m = json.loads(mp.read_text())
        rows[m["symbol"]] = {
            "first_bar": m["first"],
            "last_bar": m["last"],
            "last_traded": m.get("last_traded"),
            "bars": m["rows"],
            "missing_hours": m.get("missing_hours"),
            "trailing_dead_hours": m.get("trailing_dead_hours"),
            "zero_volume_hours": m.get("zero_volume_hours"),
        }
    for mp in sorted(PARQUET.glob("fundingRate/*.manifest.json")):
        m = json.loads(mp.read_text())
        rows.setdefault(m["symbol"], {})
        rows[m["symbol"]].update(
            {"funding_first": m["first"], "funding_last": m["last"], "funding_rows": m["rows"]}
        )
    traded = [pd.Timestamp(r["last_traded"]) for r in rows.values() if r.get("last_traded")]
    head = max(traded) if traded else None
    for r in rows.values():
        lt = r.get("last_traded")
        r["delisted_by_volume"] = bool(
            lt and head is not None and pd.Timestamp(lt) < head - pd.Timedelta(days=45)
        )
    doc = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "market": MARKET,
        "symbols": len(rows),
        "delisted_by_volume": sum(r["delisted_by_volume"] for r in rows.values()),
        "head_last_traded": head.isoformat() if head is not None else None,
        "rows": rows,
    }
    SUMMARY_PATH.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
    log(
        f"  {doc['symbols']} symbols, {doc['delisted_by_volume']} delisted by volume"
        f" -> {_display(SUMMARY_PATH)}"
    )
    return doc


# ----------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download raw files, then build parquet")
    f.add_argument("--symbols", nargs="*", default=[])
    f.add_argument("--universe", action="store_true", help="every USDT perp in universe.parquet")
    f.add_argument(
        "--datasets", nargs="+", default=["klines", "fundingRate"], choices=list(PERIODS)
    )
    f.add_argument("--interval", default="1h")
    f.add_argument("--since", default=None, help="YYYY-MM-DD lower bound on file dates")
    f.add_argument("--until", default=None, help="YYYY-MM-DD upper bound on file dates")
    f.add_argument("--workers", type=int, default=4)
    f.add_argument("--no-build", action="store_true")
    b = sub.add_parser("build", help="rebuild parquet from the raw cache (offline)")
    b.add_argument("--symbols", nargs="+", required=True)
    b.add_argument(
        "--datasets", nargs="+", default=["klines", "fundingRate"], choices=list(PERIODS)
    )
    sub.add_parser(
        "universe", help="list every symbol folder with first/last month + delisted flag"
    )
    sub.add_parser("status", help="print the parquet manifests")
    sub.add_parser("summarize", help="fold the manifests into universe_summary.json (committable)")
    a = ap.parse_args(argv)

    if a.cmd == "fetch":
        archive = Archive()
        symbols = list(a.symbols) + (usdt_universe() if a.universe else [])
        if not symbols:
            ap.error("fetch needs --symbols and/or --universe")
        t0 = time.time()
        for n, sym in enumerate(symbols, 1):
            print(f"[{n}/{len(symbols)} {time.time() - t0:.0f}s] {sym}", flush=True)
            for ds in a.datasets:
                try:
                    fetch_symbol(archive, sym, ds, a.interval, a.since, a.until, a.workers)
                    if not a.no_build and (RAW / ds / sym).exists():
                        build_parquet(sym, ds, base_url=archive.base_url)
                except Exception as e:  # one bad symbol must not end a multi-hour pull
                    print(f"  ERROR {sym} {ds}: {e}", flush=True)
        print(f"served by: {archive.base_url}")
    elif a.cmd == "summarize":
        summarize()
    elif a.cmd == "build":
        for sym in a.symbols:
            for ds in a.datasets:
                build_parquet(sym, ds)
    elif a.cmd == "universe":
        df = build_universe(Archive())
        summary = json.loads((DATA / "universe.json").read_text())
        print(json.dumps(summary, indent=1))
        dead = df[(df["kind"] == "usdt_perp") & df["delisted"]]
        print("delisted USDT perps (first 20):")
        print(
            dead[["symbol", "first_month", "last_month", "months"]].head(20).to_string(index=False)
        )
    elif a.cmd == "status":
        for mp in sorted(PARQUET.glob("*/*.manifest.json")):
            m = json.loads(mp.read_text())
            extra = (
                f", missing hours {m['missing_hours']}, dead tail {m['trailing_dead_hours']} h"
                if "missing_hours" in m
                else ""
            )
            print(
                f"{m['dataset']:12s} {m['symbol']:12s} {m['rows']:>8d} rows  {m['first'][:10]} .. {m['last'][:10]}{extra}"
            )


if __name__ == "__main__":
    main(sys.argv[1:])
