"""Offline tests for analysis/strat_ml/binance_vision.py (zip fixtures; no network)."""

import hashlib
import io
import zipfile

import pytest

from analysis.strat_ml import binance_vision as bv


def zip_bytes(name: str, text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, text)
    return buf.getvalue()


KLINE_ROWS = (
    "1577836800000,7189.43,7190.52,7170.15,7171.55,2449.049,1577840399999,17576424.43970,3688,996.198,7149370.76353,0\n"
    "1577840400000,7171.43,7225,7171.10,7210.24,3865.038,1577843999999,27838046.00670,6635,2340.878,16860294.05346,0\n"
)
KLINE_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,"
    "taker_buy_quote_volume,ignore\n"
)


def test_klines_without_header():
    df = bv.read_zip_csv(zip_bytes("BTCUSDT-1h-2020-01.csv", KLINE_ROWS), "klines")
    assert list(df.columns) == bv.KLINE_COLS[:-1]
    assert str(df["open_time"].iloc[0]) == "2020-01-01 00:00:00+00:00"
    assert df["high"].iloc[1] == 7225.0
    assert df["count"].iloc[0] == 3688


def test_klines_with_header_matches_headerless():
    a = bv.read_zip_csv(zip_bytes("x.csv", KLINE_ROWS), "klines")
    b = bv.read_zip_csv(zip_bytes("x.csv", KLINE_HEADER + KLINE_ROWS), "klines")
    assert a.equals(b)


def test_microsecond_guard():
    rows = KLINE_ROWS.replace("1577836800000,", "1577836800000000,").replace(
        "1577840400000,", "1577840400000000,"
    )
    df = bv.read_zip_csv(zip_bytes("x.csv", rows), "klines")
    assert str(df["open_time"].iloc[0]) == "2020-01-01 00:00:00+00:00"


def test_funding_with_and_without_interval_column():
    with_h = "calc_time,funding_interval_hours,last_funding_rate\n1704067200000,8,0.00037409\n"
    df = bv.read_zip_csv(zip_bytes("f.csv", with_h), "fundingRate")
    assert list(df.columns) == bv.FUNDING_COLS
    assert df["funding_interval_hours"].iloc[0] == 8
    assert df["last_funding_rate"].iloc[0] == pytest.approx(0.00037409)
    two = bv.read_zip_csv(zip_bytes("f.csv", "1704067200000,0.0001\n"), "fundingRate")
    assert two["funding_interval_hours"].isna().all()
    assert str(two["calc_time"].iloc[0]) == "2024-01-01 00:00:00+00:00"


def test_metrics_dedupes_backfilled_double_rows():
    row = "2020-09-01 00:00:00,BTCUSDT,39080.231,456144339.2,1.175,1.230,1.357,0.783\n"
    text = ",".join(bv.METRICS_COLS) + "\n" + row + row + row.replace("00:00:00", "00:05:00")
    df = bv.read_zip_csv(zip_bytes("m.csv", text), "metrics")
    assert len(df) == 2
    assert str(df["create_time"].iloc[1]) == "2020-09-01 00:05:00+00:00"
    assert df["sum_open_interest"].iloc[0] == pytest.approx(39080.231)


def test_select_keys_monthly_then_daily_tail():
    monthly = ["p/BTCUSDT-1h-2026-08.zip", "p/BTCUSDT-1h-2026-09.zip"]
    daily = [
        "d/BTCUSDT-1h-2026-09-30.zip",  # covered by the monthly file: dropped
        "d/BTCUSDT-1h-2026-10-01.zip",
        "d/BTCUSDT-1h-2026-10-02.zip",
    ]
    assert bv.select_keys(monthly, daily) == monthly + daily[1:]
    assert bv.select_keys(monthly, daily, since="2026-09-15") == monthly[1:] + daily[1:]
    assert bv.select_keys(monthly, daily, until="2026-10-01") == monthly + daily[1:2]
    assert bv.select_keys([], daily) == daily


def test_file_stamp_and_prefix():
    assert bv.file_stamp("data/x/BTCUSDT-1h-2020-01.zip") == "2020-01"
    assert bv.file_stamp("BTCUSDT-metrics-2020-09-01.zip") == "2020-09-01"
    assert (
        bv.dataset_prefix("klines", "monthly", "BTCUSDT")
        == "data/futures/um/monthly/klines/BTCUSDT/1h/"
    )
    assert bv.dataset_prefix("fundingRate", "monthly", "SRMUSDT") == (
        "data/futures/um/monthly/fundingRate/SRMUSDT/"
    )
    with pytest.raises(ValueError):
        bv.dataset_prefix("fundingRate", "daily", "BTCUSDT")


def test_checksum():
    body = b"abc"
    bv.check_sha256(body, hashlib.sha256(body).hexdigest().upper())
    with pytest.raises(ValueError):
        bv.check_sha256(body, "00")


def test_classify_folder():
    assert bv.classify_folder("BTCUSDT") == "usdt_perp"
    assert bv.classify_folder("SRMUSDT") == "usdt_perp"
    assert bv.classify_folder("AERGOUSDTSETTLED") == "settled_stub"
    assert bv.classify_folder("ICPUSDT_SETTLED") == "settled_stub"
    assert bv.classify_folder("ADABUSD") == "other_quote"
    assert bv.classify_folder("AAVEUSDC") == "other_quote"


def test_download_verifies_and_caches(tmp_path, monkeypatch):
    body = zip_bytes("x.csv", KLINE_ROWS)
    good = hashlib.sha256(body).hexdigest()
    store = {"k.zip": body, "k.zip.CHECKSUM": f"{good}  k.zip\n".encode()}
    calls = []

    class FakeArchive(bv.Archive):
        def _get_bytes(self, key):
            calls.append(key)
            return store[key]

    a = FakeArchive(session=object())
    dest = tmp_path / "k.zip"
    assert a.download("k.zip", dest) is True
    assert dest.read_bytes() == body
    assert a.download("k.zip", dest) is False  # cached: no request made
    assert calls == ["k.zip", "k.zip.CHECKSUM"]
    store["k.zip.CHECKSUM"] = b"deadbeef  k.zip\n"
    with pytest.raises(ValueError):
        a.download("k.zip", tmp_path / "other.zip")
    assert not (tmp_path / "other.zip").exists()


def test_build_parquet_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(bv, "RAW", tmp_path / "raw")
    monkeypatch.setattr(bv, "PARQUET", tmp_path / "parquet")
    folder = tmp_path / "raw" / "klines" / "TESTUSDT"
    folder.mkdir(parents=True)
    (folder / "TESTUSDT-1h-2020-01.zip").write_bytes(zip_bytes("a.csv", KLINE_ROWS))
    # the daily tail repeats the second hour (dedupe keeps last) and adds a fourth hour (gap of 1)
    tail = (
        "1577840400000,7171.43,7225,7171.10,7210.24,1,1577843999999,1,1,1,1,0\n"
        "1577847600000,1,2,0.5,1.5,1,1577851199999,1,1,1,1,0\n"
    )
    (folder / "TESTUSDT-1h-2020-01-02.zip").write_bytes(zip_bytes("b.csv", KLINE_HEADER + tail))
    m = bv.build_parquet("TESTUSDT", "klines", log=lambda *_: None)
    assert m["rows"] == 3 and m["raw_rows"] == 4 and m["missing_hours"] == 1
    assert m["zero_volume_hours"] == 0 and m["trailing_dead_hours"] == 0
    assert m["last_traded"] == "2020-01-01T03:00:00+00:00"
    df = bv.load("TESTUSDT", "klines")
    assert df["volume"].iloc[1] == 1.0  # the later file won the duplicate hour
    assert df["open_time"].dt.tz is not None


def test_months_after():
    from datetime import date

    assert bv.months_after("2026-09", date(2026, 10, 17)) == ["2026-10"]
    assert bv.months_after("2025-11", date(2026, 2, 1)) == ["2025-12", "2026-01", "2026-02"]
    assert bv.months_after("2026-10", date(2026, 10, 17)) == []
    assert bv.months_after("2024-05", date(2024, 5, 30)) == []


def test_build_parquet_flags_zombie_tail(tmp_path, monkeypatch):
    monkeypatch.setattr(bv, "RAW", tmp_path / "raw")
    monkeypatch.setattr(bv, "PARQUET", tmp_path / "parquet")
    folder = tmp_path / "raw" / "klines" / "DEADUSDT"
    folder.mkdir(parents=True)
    # one traded hour, then two flat zero-volume hours (the BTCSTUSDT pattern)
    rows = (
        "1577836800000,1,2,0.5,1.5,10,1577840399999,1,1,1,1,0\n"
        "1577840400000,1.5,1.5,1.5,1.5,0,1577843999999,0,0,0,0,0\n"
        "1577844000000,1.5,1.5,1.5,1.5,0,1577847599999,0,0,0,0,0\n"
    )
    (folder / "DEADUSDT-1h-2020-01.zip").write_bytes(zip_bytes("a.csv", rows))
    m = bv.build_parquet("DEADUSDT", "klines", log=lambda *_: None)
    assert m["rows"] == 3 and m["zero_volume_hours"] == 2 and m["trailing_dead_hours"] == 2
    assert m["last_traded"] == "2020-01-01T00:00:00+00:00"


def test_summarize_reads_manifests(tmp_path, monkeypatch):
    import json

    monkeypatch.setattr(bv, "PARQUET", tmp_path / "parquet")
    monkeypatch.setattr(bv, "SUMMARY_PATH", tmp_path / "summary.json")
    (tmp_path / "parquet" / "klines").mkdir(parents=True)
    (tmp_path / "parquet" / "fundingRate").mkdir(parents=True)

    def man(sym, last_traded, dead):
        return json.dumps(
            {
                "symbol": sym,
                "rows": 10,
                "first": "2020-01-01T00:00:00+00:00",
                "last": "2026-10-16T23:00:00+00:00",
                "last_traded": last_traded,
                "missing_hours": 0,
                "trailing_dead_hours": dead,
                "zero_volume_hours": dead,
            }
        )

    (tmp_path / "parquet/klines/LIVEUSDT.manifest.json").write_text(
        man("LIVEUSDT", "2026-10-16T23:00:00+00:00", 0)
    )
    (tmp_path / "parquet/klines/DEADUSDT.manifest.json").write_text(
        man("DEADUSDT", "2022-11-15T04:00:00+00:00", 13443)
    )
    (tmp_path / "parquet/fundingRate/LIVEUSDT.manifest.json").write_text(
        json.dumps({"symbol": "LIVEUSDT", "rows": 3, "first": "a", "last": "b"})
    )
    doc = bv.summarize(log=lambda *_: None)
    assert doc["symbols"] == 2 and doc["delisted_by_volume"] == 1
    assert doc["rows"]["DEADUSDT"]["delisted_by_volume"] is True
    assert doc["rows"]["LIVEUSDT"]["delisted_by_volume"] is False
    assert doc["rows"]["LIVEUSDT"]["funding_rows"] == 3
    assert json.loads((tmp_path / "summary.json").read_text())["symbols"] == 2
