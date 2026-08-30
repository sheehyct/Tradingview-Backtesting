# TVB-31 HyPaper adoption spike (2026-08-30)

Code-reading spike of github.com/GigabrainGG/HyPaper @ b054fdd (17 commits,
MIT, Node/TS + Redis + Postgres) against the three pre-registered questions
from the TVB-30 HANDOFF assessment. Method: cloned to scratchpad, read the
exchange/info routes, order engine, matcher, price feed, and margin model
line by line against hip3-executor's LiveBroker surface (broker.py). No
live instance was run; every claim below cites the file it was read from.

VERDICT: adoptable for continuous multi-strategy paper on MAIN-DEX CRYPTO
ONLY, and NOT drop-in -- it needs one small executor change, one ~30-line
shim (or tiny upstream PR), and one 2-line upstream patch before our
LiveBroker can talk to it at all. xyz builder-dex arms cannot run on it
today. Nothing here touches the Monday live run; HyPaper is a parallel
lane, not a go-live dependency.

## (a) xyz builder-dex support: NO, end to end

- Worker seeds `{type:"meta"}` and subscribes `{type:"allMids"}` with no
  dex parameter (src/worker/index.ts:41-55) -- main-dex universe only.
  xyz coins never get mids, never enter the stored meta.
- Order placement resolves the SDK's numeric asset id by INDEXING the
  main-dex universe array (src/engine/order.ts:15-21 resolveAssetCoin).
  Builder-dex asset ids are offset (100000+) per the HL protocol, so any
  xyz order returns "Unknown asset".
- Consequence for us: HyPaper arms are crypto-only. Builder-dex support
  is a real upstream feature request (dex-aware meta seeding + offset
  asset mapping + per-dex allMids subscriptions), not a config flag.

## (b) Python-SDK compatibility: three concrete blockers

1. `/exchange` requires a top-level `wallet` field and 400s without it
   (src/api/routes/exchange.ts:12-15). The official SDK sends
   `{action, nonce, signature}` -- no wallet -- so EVERY signed exchange
   action fails. Fix: a ~30-line reverse-proxy shim per wallet that
   injects the field (HyPaper ignores nonce/signature entirely), or an
   upstream PR accepting a wallet header.
2. Trigger orders (venue-resident stop/TP -- our entire bracket safety
   architecture) are UNREACHABLE via the API: the route validation
   rejects any order without `t.limit.tif` (exchange.ts:37), and even
   past that, order.ts:63 reads `wire.t.limit.tif` unguarded and would
   throw on a trigger wire. The engine itself has a full trigger path
   (placeTriggeredOrder, order.ts:165; matcher tp/sl semantics,
   order-matcher.ts:66-112) -- written but dead. Fix: ~2-line patch
   (accept `t.trigger` in validation; guard the tif read). Without it
   place_bracket fails on both protective legs.
3. Error transport differs: HyPaper returns HTTP 400/500 for rejections
   where real HL returns 200-with-err-payload. The SDK raises on
   non-200, so our broker would classify every rejection as ambiguous
   BrokerError (-> reconciliation) instead of definite OrderRejected.
   Safe direction, but noisy; worth normalizing in the shim.

Executor-side prerequisites (small, honest):
- broker.py hardcodes `constants.MAINNET_API_URL` for both Info and
  Exchange (lines 131-132) -- base_url must become config with the
  mainnet default unchanged.
- HyPaper ignores the `dex` param on clearinghouseState/openOrders
  (src/api/routes/info.ts:67-77 never reads body.dex): every per-dex
  sweep returns the same union. With perp_dexs=["","xyz"] configured,
  our defensive re-prefixing would mint PHANTOM `xyz:`-prefixed
  positions from the duplicate sweep and trip the untracked-positions
  entry_block. HyPaper mode MUST run perp_dexs=[""].

What DOES line up (read-side): clearinghouseState / openOrders /
orderStatus / userFills response shapes mirror real HL closely enough
for every read our LiveBroker makes (src/engine/position.ts, fill.ts);
meta/l2Book/candleSnapshot proxy through to real HL with the request
body forwarded verbatim; updateLeverage and cancel/cancelByCloid are
supported; accounts auto-create per wallet on first touch with an
env-set starting balance (middleware/auth.ts) -- which is exactly the
per-wallet parallel-strategies mechanism the user wants.

## (c) Fill realism: better than advertised, with named optimisms

- Fills are detected on MID crossing the limit/trigger price, but PRICED
  by walking the REAL venue L2 book as a VWAP (fetched live per coin,
  2s cache, mid fallback; src/utils/slippage.ts, l2-cache.ts). Depth
  shortfall prices the remainder at the worst level. This is materially
  more realistic than our PaperBroker's mid fills.
- Fees: maker/taker split correctly by resting-vs-immediate (taker
  0.035% / maker 0.01% defaults, env-tunable). Funding applied every 8h
  from live rates with correct sign (funding-worker.ts:72-73).
- Named optimisms: triggers fire on MID where real HL fires stops on
  MARK (oracle-influenced -- matters exactly in the thin/wick moments
  stops exist for); resting makers fill the instant mid touches the
  limit (no queue position, no trade-through requirement -- optimistic
  for maker arms; our IOC-entry taker flow mostly dodges this); fills
  are all-or-nothing (no partials); paper fills consume no liquidity;
  NO liquidation enforcement exists (liq price is display-only,
  position.ts) -- irrelevant at $0.50 risk with venue-resident stops,
  but disqualifying for any leverage-stress question.

## Why bother at all (unchanged from TVB-30)

Our dry-run exercises PaperBroker -- a parallel twin -- so it can never
catch LiveBroker defects; HIGH-1 (dex-blind reads) hid exactly in that
gap. HyPaper runs the REAL LiveBroker code path (SDK wire format,
response parsing, oid/cloid lifecycle, resting-stop verification, fills
polling) continuously, and per-wallet accounts give the multiple-
parallel-strategies comparison the user asked for. Comparison
discipline unchanged: parallel arms = generating data; promotion rules
stay ablation-not-tournament.

## Proposed adoption path (for the discussion -- NOT committed)

1. Self-host (Docker; needs Redis + a Postgres DATABASE_URL despite the
   README's Redis-only framing -- config.ts requires it). Railway is a
   listed deploy target and matches our existing infra.
2. Fork or PR the 2-line trigger-order fix upstream; build the wallet
   shim; add cfg base_url to broker.py; pin perp_dexs=[""] in HyPaper
   mode. Then a live probe: one bracket entry, verify the stop RESTS
   and verify_resting sees it, kill it, requery_flat.
3. Only after that probe: define the parallel paper arms (per-wallet,
   crypto-only) as a prereg, with the mid-vs-mark trigger optimism and
   maker-fill optimism stated as standing caveats on every result read.
