/* story.js: the trade in plain trader language, generated from the recorded row (nothing here
   computes a trade: every price, day and fill is read off the row the engine wrote), the book
   ladder for one trade, and the Playbook (what the trade is, how it leaves, what each book does). */
window.DV = window.DV || {};
(function (DV) {
  "use strict";
  const C = DV.core;
  const { iso, longDate, shortDate, weekdayOf, fmtPrice, fmtPct, fmtUsd, cls, esc, TF_LABEL, TF_WORD, KIND_LABEL, CLS_LABEL, BOOKS, BOOK_RET, BOOK_NAME, BOOK_LINE, BOOK_COL, settle, tradeSpan, stackLevels, htfType, btChip, BT_WORD, oneR, stackWords } = C;

  function words(long) {
    return { side: long ? "long" : "short", hi: long ? "high" : "low", lo: long ? "low" : "high", up: long ? "up" : "down", down: long ? "down" : "up",
      above: long ? "above" : "below", below: long ? "below" : "above", redWord: long ? "red" : "green" };
  }
  const n2 = (x) => x == null ? "?" : Number(x).toFixed(2);

  // ---------------------------------------------------------------- the setup, in words
  function setupWords(t) {
    const long = t.direction === "up", w = words(long);
    const inner = t.tf === "D" ? "bar" : TF_WORD[t.tf];
    const bar = "setup " + inner;
    const before = "the " + inner + " before it";
    const trig = "breaking the " + bar + "'s " + w.hi;
    if (t.kind === "reversal") return "A 2-2 reversal: the " + bar + " had gone " + w.down + " through the " + w.lo + " of " + before + "; " + trig + " flips the direction.";
    if (t.kind === "continuation") return "A 2-2 continuation: the " + bar + " had already broken the " + w.hi + " of " + before + "; " + trig + " carries the move on.";
    if (t.kind === "inside") {
      let s = "An inside-" + inner + " break: the " + bar + " stayed inside the range of " + before + "; " + trig + " is the trigger.";
      if (t.anchor === "anchor") s += " The " + inner + " before the inside " + inner + " had gone the other way or outside, so the pattern has a magnitude of its own: that " + inner + "'s far side.";
      else if (t.anchor === "ladder") s += " The " + inner + " before the inside " + inner + " had gone the same way, so this is a with-trend break with no magnitude of its own.";
      else if (t.anchor === "stacked") s += " The " + inner + " before it was inside too (a stack of inside " + inner + "s), so there is no magnitude of its own.";
      return s;
    }
    if (t.kind === "outside") return "An outside-" + inner + " break (3-2): the " + bar + " had gone through both sides of " + before + "; " + trig + " is the trigger, and a 3-2 has no magnitude of its own.";
    return "";
  }

  function targetWords(t, p, cal, i) {
    const inner = t.tf === "D" ? "bar" : TF_WORD[t.tf];
    const parts = [];
    const src = t.t1_src;
    const touched = (k, verb) => k == null ? " (never " + (verb || "touched") + " inside the window)" : " (" + (verb || "touched") + " " + dayWord(k, cal, i).replace(" (", ", ").replace(")", "") + ")";
    if (t.t1 != null) {
      const why = src === "anchor" ? "the pattern's own magnitude, the far side of the " + inner + " before the setup " + inner
        : src === "W" ? "the first unbroken weekly level beyond the entry" : src === "M" ? "the first unbroken monthly level beyond the entry" : src === "mm" ? "the measured move" : "";
      parts.push("T1 " + fmtPrice(t.t1, p) + (why ? " is " + why : "") + touched(t.t1_k) + ".");
      const rungs = [];
      const srcWord = (s) => s === "W" ? "weekly" : s === "M" ? "monthly" : s || "";
      if (t.t2 != null) rungs.push("T2 " + fmtPrice(t.t2, p) + " (" + srcWord(t.t2_src) + touched(t.t2_k).replace(" (", ", ").replace(/\)$/, "") + ")");
      if (t.t3 != null) rungs.push("T3 " + fmtPrice(t.t3, p) + " (" + srcWord(t.t3_src) + touched(t.t3_k).replace(" (", ", ").replace(/\)$/, "") + ")");
      if (rungs.length) parts.push(rungs.join(" and ") + (rungs.length > 1 ? " are the next unbroken levels beyond it, fixed at entry." : " is the next unbroken level beyond it, fixed at entry."));
      else parts.push("No further unbroken weekly or monthly level sits beyond it, so there is no T2.");
    } else if (src === "none") parts.push("No unbroken weekly or monthly level sat beyond the entry, so this trade has no T1: the target books can only leave on the exit.");
    else if (src === "zero") parts.push("The pattern's anchor sits at the entry price itself, so there is no T1.");
    else parts.push("The " + inner + " before the setup " + inner + " is missing from the data, so T1 is unknown.");
    if (t.stop != null) {
      parts.push("One R is " + (t.r_pct != null ? n2(t.r_pct) + "% of price" : "the setup range") + ": the setup " + inner + "'s far side at " + fmtPrice(t.stop, p) +
        " is the chance book's stop" + touched(t.stop_k, "hit") + " and only a yardstick for the management books (they have no stop), so one R sits at " + fmtPrice(oneR(t), p) + touched(t.one_r_k) + ".");
    }
    if (t.mm_t1 != null) parts.push("The measured move (the two-" + inner + " range projected from the entry) sits at " + fmtPrice(t.mm_t1, p) + touched(t.mm1_k) + ".");
    return parts.join(" ");
  }

  // ---------------------------------------------------------------- the clocks, in words
  function dayWord(k, cal, i) {
    if (k == null) return "";
    if (k === 0) return "on the entry day";
    const j = Math.min(i + k, cal.daily.length - 1);
    return "on day " + k + " (" + shortDate(iso(cal.daily[j][0])) + ")";
  }
  function clockWords(t, cal, i, p) {
    const long = t.direction === "up", w = words(long);
    if (t.status === "exit") {
      const k = t.exit_k, j = Math.min(i + k, cal.daily.length - 1), b = cal.daily[j], wo = cal.weekOpenAt(b[0]);
      const monday = C.weekStart(b[0]) === b[0];
      const colour = b[4] < b[1] ? "red" : b[4] > b[1] ? "green" : "flat";
      return "The daily clock fired " + (k === 0 ? "on the entry day" : "on day " + k) + ", " + weekdayOf(iso(b[0])) + " " + shortDate(iso(b[0])) + ": the day closed " + colour + " at " + fmtPrice(b[4], p) +
        ", " + w.below + " its open " + fmtPrice(b[1], p) + (monday ? " (a Monday, so the day's open is the week's open and the two tests are one)" : " and " + w.below + " the week's open " + fmtPrice(wo, p)) + ".";
    }
    if (t.status === "open") return "No daily close went against the trade with the week against it inside the 20-day cap, so the row is marked at the day-20 close.";
    return "The data ends before the 20-day cap, so the row is censored: no result is recorded.";
  }
  function bookWords(t, book, cal, i, p, size) {
    const st = settle(t, book);
    const money = (r) => r == null ? "no result" : '<b class="' + cls(r) + '">' + fmtPct(r) + "</b> (" + fmtUsd(r, size) + " on " + size.toLocaleString("en-US") + ")";
    const when = (k) => dayWord(k, cal, i);
    const clock = clockWords(t, cal, i, p);
    const touchOrder = (k) => t.exit_k != null && k === t.exit_k ? "on the exit day itself (a touch on the exit day fills first)" : "before the exit";
    // what happened when the book's own target never came: the row's status says it, not an assumed clock exit (TVB-40 audit F3)
    const noTarget = t.status === "exit" ? "so it left with the daily clock. " + clock : t.status === "open" ? "and no daily exit fired inside the 20-day cap either, so the row is marked at the day-20 close." : "and the data ends inside the window, so the row is censored.";
    if (book !== "C" && st.missing) return (book === "ref" ? "The chance book has " : "Book " + book + " has ") + st.how + ". " + clock;
    if (book === "C") return "Book C has no target: it holds until the daily clock, a close against the trade with the week also against it at that close. " + clock +
      (t.status === "exit" ? " Filled at that close: " + money(st.ret) + "." : t.status === "open" ? " Marked: " + money(st.ret) + "." : "");
    if (book === "A") {
      if (t.t1 == null) return "Book A takes everything at T1, but this trade has no T1, so it rides the exit like book C. " + clock + " Result " + money(st.ret) + ".";
      if (t.hit_A) return "Book A takes everything at T1. T1 " + fmtPrice(t.t1, p) + " was touched " + when(t.t1_k) + ", " + touchOrder(t.t1_k) + ", so the book left there: " + money(st.ret) + ".";
      return "Book A would take everything at T1, but T1 " + (t.t1_k == null ? "was never touched inside the window" : "was only touched " + when(t.t1_k) + ", after the exit") + ", " + noTarget + " Result " + money(st.ret) + ".";
    }
    if (book === "B") {
      if (t.t2 == null) return "Book B holds through T2 with the exit live, but this trade has no T2, so it rides the exit like book C. " + clock + " Result " + money(st.ret) + ".";
      if (t.hit_B) return "Book B holds through T2 with the exit live (T1 is not a decision). T2 " + fmtPrice(t.t2, p) + " was touched " + when(t.t2_k) + ", " + touchOrder(t.t2_k) + ", so the book left there: " + money(st.ret) + ".";
      return "Book B holds through T2 with the exit live, but T2 " + (t.t2_k == null ? "never came inside the window" : "only came " + when(t.t2_k) + ", after the exit") + ", " + noTarget + " Result " + money(st.ret) + ".";
    }
    if (book === "D") {
      const r1 = oneR(t);
      if (r1 == null) return "Book D takes one R or the exit, but this row has no setup range, so it rides the exit. " + clock + " Result " + money(st.ret) + ".";
      if (t.hit_D) return "Book D takes one R or the exit, whichever first, inside the 20-day cap. One R at " + fmtPrice(r1, p) + " was touched " + when(t.one_r_k) + ", " + touchOrder(t.one_r_k) + ", so the book left there: " + money(st.ret) + ".";
      return "Book D takes one R or the exit, whichever first. One R at " + fmtPrice(r1, p) + " " + (t.one_r_k == null ? "was never touched inside the window" : "was only touched " + when(t.one_r_k) + ", after the exit") + ", " + noTarget + " Result " + money(st.ret) + ".";
    }
    if (book === "D5") {
      const r1 = oneR(t);
      if (st.book !== "D5") return "Book D5 has no result on this row (the five-bar window is incomplete). " + clock;
      if (t.hit_D5) return "Book D5 takes one R or the exit inside five bars, the chance book's own horizon. One R at " + fmtPrice(r1, p) + " was touched " + when(t.one_r_k) + ", so the book left there: " + money(st.ret) + ".";
      if (st.how === "daily-close exit") return "Book D5 takes one R or the exit inside five bars. The daily clock fired first. " + clock + " Result " + money(st.ret) + ".";
      return "Book D5 takes one R or the exit inside five bars. Neither came: the row is marked at the bar-5 close, " + money(st.ret) + ".";
    }
    // the chance book
    if (st.book !== "ref") return "The chance book has no result on this row (the five-bar window is incomplete).";
    if (t.out5 === "stop") {
      const tie = t.one_r_k != null && t.one_r_k === t.stop_k;
      return "The chance book keeps the setup-" + (t.tf === "D" ? "bar" : TF_WORD[t.tf]) + " stop at " + fmtPrice(t.stop, p) + ". It was hit " + when(t.stop_k) +
        (tie ? ", the same " + (t.tf === "D" ? "day" : TF_WORD[t.tf]) + " one R was touched: the bar cannot say which came first, and the engine takes the stop (pessimistic)" : ", before one R") + ", so the book is out there: " + money(st.ret) + ".";
    }
    if (t.out5 === "one_r") return "The chance book keeps the setup stop at " + fmtPrice(t.stop, p) + " and takes one R. One R came first, " + when(t.one_r_k) + ": " + money(st.ret) + ".";
    if (t.out5 === "neither") return "The chance book keeps the setup stop at " + fmtPrice(t.stop, p) + " and takes one R. Neither came inside five bars, so the row is marked at the bar-5 close: " + money(st.ret) + ".";
    return "The chance book is censored on this row (the data ends inside its five bars).";
  }
  function otherClocks(t, cal, i, p) {
    const out = [], w = words(t.direction === "up");
    if (t.status_u === "exit" && t.exit_k_u != null) {
      out.push("Reading <i>against</i> as under water instead (a close through the entry price with the week against it), the exit " +
        (t.exit_k_u === t.exit_k ? "fires on the same day" : "moves to " + dayWord(t.exit_k_u, cal, i).replace(/^on /, "")) + ": " + fmtPct(t.ret_C_u) + " on the exit-only book.");
    } else if (t.status_u === "open") out.push("Read as under water, the exit never fires inside the cap: " + fmtPct(t.ret_C_u) + " marked at the cap.");
    if (t.status_h === "exit" && t.entry_h != null && t.exit_h != null) {
      out.push("On the hourly clock (out on the first " + w.redWord + " hour while the day is " + w.redWord + ", both against the trade; the entry is the same level, hour " + t.entry_h + " of the entry day), the trade is off " + t.exit_h + " hours later: " + fmtPct(t.ret_C_h) + ".");
    }
    if (t.tf !== "D") {
      const own = t.tf === "W" ? "a weekly close against the week's open with the month also against it" : "a monthly close against the month's open";
      if (t.status_own === "exit" && t.ret_C_own != null) out.push("On the " + TF_WORD[t.tf] + "'s own clock (" + own + "), it leaves after " + t.days_own + " days: " + fmtPct(t.ret_C_own) +
        (t.status_long === "exit" && t.ret_C_long != null ? "; the daily clock run to the same cap of 20 " + TF_WORD[t.tf] + "s gives " + fmtPct(t.ret_C_long) + " after " + t.days_long + " days" : "") + ".");
      else if (t.status_own === "open") out.push("On the " + TF_WORD[t.tf] + "'s own clock it is still open at the cap of 20 " + TF_WORD[t.tf] + "s: " + fmtPct(t.ret_C_own) + " marked.");
    }
    return out;
  }

  // ---------------------------------------------------------------- the whole story for one trade
  function narrate(c) {
    const { t, coin, cal, book, size, p } = c;
    const long = t.direction === "up", w = words(long);
    const i = cal.dayIdx.get(t.date);
    if (i == null) return "<p>This trade's entry day is not in the coin's daily bars.</p>";
    const levels = stackLevels(t, i, cal);
    let stack = "";
    if (levels.length > 1) {
      const sw = stackWords(t, levels);
      const name = (l) => "the " + TF_WORD[l.tf] + "'s level " + fmtPrice(l.price, p);
      const convOthers = sw.conv.filter((l) => l.tf !== t.tf);
      if (convOthers.length) {
        const prices = sw.conv.map((l) => l.price), gap = (Math.max(...prices) - Math.min(...prices)) / Math.min(...prices) * 100;
        stack += " The same day broke " + convOthers.map(name).join(" and ") + " (" + (CLS_LABEL[t.cls] || t.cls) + ", a " + gap.toFixed(2) + "% gap between the triggers" + (t.cls !== "spread" ? ": a domino, the levels converged" : "") + ").";
      }
      if (sw.far.length) stack += " " + sw.far.map((l) => name(l) + " also broke the same day, " + (l.gap >= 0 ? "+" : "") + l.gap.toFixed(2) + "% beyond the entry").join("; ") + (convOthers.length ? ": not part of the converged stack, the entry-time class does not describe it." : ": too far from the entry to be a domino (the entry-time class is " + (CLS_LABEL[t.cls] || t.cls) + ").");
    }
    const week = t.w_support === "with" ? "The week was on the trade's side at entry (price " + w.above + " Monday's open)." : t.w_support === "against" ? "The week was against the trade at entry (price " + w.below + " Monday's open)." : "";
    const paras = [];
    paras.push("<p><b>" + esc(coin) + " " + w.side + ", " + TF_LABEL[t.tf] + " " + KIND_LABEL[t.kind] + ".</b> " + setupWords(t) + " Entered " + longDate(t.date) + " at " + fmtPrice(t.level, p) +
      ", the instant the " + TF_WORD[t.tf] + "'s level broke." + stack + (week ? " " + week : "") + "</p>");
    paras.push("<p><b>The plan at entry.</b> " + targetWords(t, p, cal, i) + "</p>");
    paras.push("<p><b>What book " + esc(book) + " did.</b> " + bookWords(t, book, cal, i, p, size) + "</p>");
    const others = otherClocks(t, cal, i, p);
    if (others.length) paras.push("<p><b>The other clocks.</b> " + others.join(" ") + "</p>");
    const travel = [];
    if (t.mfe_x != null || t.mae_x != null) travel.push("Between the entry and book C's exit (the headline window, whatever book is selected; the engine records travel once) the trade got +" + n2(t.mfe_x) + "% in its favour at best and " + n2(t.mae_x) + "% against it at worst" +
      (t.r_pct != null && t.mae_x != null ? " (" + (t.mae_x / t.r_pct).toFixed(1) + " R of adverse travel)" : "") + ".");
    const nb = { with: "went with the trade", against: "went against it", inside: "stayed inside the entry " + TF_WORD[t.tf], outside: "went through both sides (an outside bar)" }[t.next_bar];
    if (nb) travel.push("The " + TF_WORD[t.tf] + " after the entry " + nb + ".");
    if (travel.length) paras.push("<p><b>Travel.</b> " + travel.join(" ") + "</p>");
    paras.push('<p class="fine">Levels, targets, touch days and book fills are the recorded row; the words only read them back. Context chips describe candles and do not change the trade.</p>');
    return paras.join("");
  }

  // ---------------------------------------------------------------- the book ladder for one trade
  function ladder(c) {
    const { t, cal, book, size, p } = c;
    const i = cal.dayIdx.get(t.date);
    const rows = BOOKS.map((b) => {
      const st = settle(t, b);
      const has = t[BOOK_RET[b]] != null && (b === "C" || st.book === b);
      const day = has && st.k != null ? (st.k === 0 ? "entry day" : "day " + st.k) : "";
      const date = has && i != null && st.k != null ? iso(cal.daily[Math.min(i + st.k, cal.daily.length - 1)][0]) : "";
      return '<tr class="' + (b === book ? "sel" : "") + '" data-book="' + b + '" title="' + esc(BOOK_LINE[b] + (date ? " Settled " + date + "." : "")) + '"><td><span class="dot" style="background:' + BOOK_COL[b] + '"></span>' + esc(b === "ref" ? "chance" : b) + "</td>" +
        "<td>" + (has ? esc(st.how) : "no result") + "</td><td>" + day + "</td>" +
        '<td class="num"><b class="' + cls(has ? st.ret : null) + '">' + (has ? fmtPct(st.ret) : "-") + "</b></td></tr>";
    });
    return '<table class="ladder"><thead><tr><th>Book</th><th>How it left</th><th>When</th><th class="num">Result</th></tr></thead><tbody>' + rows.join("") + "</tbody></table>" +
      '<div class="fine">Fill = the entry level moved by the recorded return; book ' + esc(book) + " fills at " + (settle(t, book).price != null ? fmtPrice(settle(t, book).price, p) : "-") + " for " + fmtUsd(settle(t, book).ret, size) + " at the size box. Click a book to make it the page's book.</div>";
  }

  // ---------------------------------------------------------------- context chips for one trade
  function context(c) {
    const { t, cal } = c;
    const i = cal.dayIdx.get(t.date);
    const wt = i != null ? htfType(cal, "W", i) : { code: "?", title: "" }, mt = i != null ? htfType(cal, "M", i) : { code: "?", title: "" };
    const items = [];
    items.push(["Last closed week", btChip("W", wt) + " " + BT_WORD[wt.code], "the complete week before the entry, typed as a STRAT bar against the week before it (R10: strict breaks). An inside week is the owner's hazard."]);
    items.push(["Last closed month", btChip("M", mt) + " " + BT_WORD[mt.code], "the complete month before the entry, typed the same way."]);
    items.push(["Week at entry", t.w_support === "with" ? '<span class="chip ok">with the trade</span>' : '<span class="chip warn">against the trade</span>', "price above Monday's open for a long (below for a short) at the moment of entry."]);
    items.push(["Stack", t.stack && t.stack !== t.tf ? '<span class="chip flag">' + esc(stackWords(t, i != null ? stackLevels(t, i, cal) : []).text) + "</span>" : '<span class="chip tf">' + TF_LABEL[t.tf] + " alone</span>", "the converged stack (the daily level plus the levels inside its class band of it) and, after the semicolon, the other levels that broke the same day with their distance beyond the entry."]);
    items.push(["Hammer flag", t.flag && t.flag !== "none" ? '<span class="chip flag">' + (t.flag === "strict" ? "strict (detector)" : "third (range test)") + "</span>" : '<span class="chip dim">none</span>', "the setup bar closed in the far third of its own range (THIRD), or passed the strict hammer / shooter detector."]);
    items.push(["Liquidity", t.liquid ? '<span class="chip tf">liquid</span>' : '<span class="chip dim">thin</span>', "the coin passed the census's liquidity screen on the entry day."]);
    items.push(["Venue", '<span class="chip dim">' + esc(t.dex || "") + "</span>", "main = the venue's own perps; xyz = the HIP-3 dex."]);
    return items.map((x) => '<div class="ctx" title="' + esc(x[2]) + '"><span class="cl">' + x[0] + "</span><span class=\"cv\">" + x[1] + "</span></div>").join("");
  }

  // ---------------------------------------------------------------- the Playbook
  function playbook() {
    const books = BOOKS.map((b) => "<tr><td><span class=\"dot\" style=\"background:" + BOOK_COL[b] + "\"></span><b>" + esc(BOOK_NAME[b]) + "</b></td><td>" + esc(BOOK_LINE[b]) + "</td><td>" + esc({
      C: "What the exit alone is worth. The right tail lives here and so does the worst drawdown.",
      A: "The near target. Wins most often, nets least: the one-in-three losers are bigger than the winners.",
      B: "The structure hold. Few trades reach T2; the ones that do carry the average.",
      D: "The chance book's target with the close exit in place of its stop: the stop-swap read over 20 days.",
      D5: "The same swap settled at the chance book's own horizon: the cleanest like-for-like line (this is the owner's H2).",
      ref: "The yardstick: what these trades did with the setup-bar stop in place.",
    }[b]) + "</td></tr>").join("");
    return [
      "<h1>Playbook</h1>",
      '<p class="lead">What every trade on this page is, how it is managed, and what each book means. Written for a trader; the numbers come from the management receipt (built 2026-10-11) and the rows on this page are the engine\'s own.</p>',
      "<h2>The trade</h2>",
      "<p>Every row is a level break: the first time price trades through the previous day's, week's or month's high (long) or low (short), on one of the 292 live perps, in the venue era. The entry is at the level the instant it breaks; there is no waiting for a close. The setup bar is the bar whose level broke, and the pattern name says what that setup bar had done against the bar before it:</p>",
      "<ul><li><b>2-2 reversal</b>: the setup bar had gone one way (a 2 down for a long), the break goes the other way. Its magnitude is the far side of the bar before the setup bar, where the compound 3 completes.</li>",
      "<li><b>2-2 continuation</b>: the setup bar had already broken in the trade's direction and breaks again. No magnitude of its own.</li>",
      "<li><b>Inside break</b>: the setup bar stayed inside the bar before it. If that earlier bar went the other way or outside, the pattern's magnitude is its far side; if it went the same way (a with-trend inside) or was inside too (a stack), there is none.</li>",
      "<li><b>Outside break (3-2)</b>: the setup bar went through both sides of the bar before it. No magnitude of its own.</li></ul>",
      "<p>Weekly and monthly rows are the same thing one level up: the week's or month's level breaks on some day, and that day is the entry day. A <b>stack</b> is a day on which more than one timeframe's level broke; the chips say how far apart those triggers sat (same price, near, within 1%, spread). Converged triggers are the domino the census was built to find.</p>",
      "<h2>How a trade leaves: the daily clock</h2>",
      "<p>There is no price stop. The management books leave at the close of a day that closed against the trade (a red candle for a long, green for a short) with the week also against it at that close (price under Monday's open for a long). The fill is that close. The entry day counts, a Monday is one test (the day's open is the week's open), and equality is not against. This is the exit on every management book; the targets sit on top of it.</p>",
      "<p>Two readings of <i>against</i> sit beside it on every row. <b>Under water</b>: a close through the entry price (instead of a red candle) with the week against. <b>The hourly clock</b>: out on the first hour that closes against the trade while the day is against it (a red hour in a red day for a long, a green hour in a green day for a short), entry at the same daily level. Weekly and monthly rows also carry their <b>own-bar clock</b>: a weekly close against the trade with the month also against it (a monthly close against the trade for a month), run to a cap of 20 of their own bars.</p>",
      "<h2>Targets</h2>",
      "<p><b>T1</b> is the pattern's own magnitude where it has one (reversal, inside break off a bar against or outside), otherwise the first unbroken weekly or monthly level beyond the entry. <b>T2</b> and <b>T3</b> are the next unbroken weekly or monthly levels beyond T1. The ladder is fixed at entry and a target fills on touch. <b>One R</b> is the setup bar's far side measured from the entry: the chance book's stop distance, kept only as a yardstick. The <b>measured move</b> is the two-bar range (setup bar plus the bar before it) projected from the entry; it is a declared variant, drawn but not traded by these books.</p>",
      "<h2>The books</h2>",
      '<table class="pb"><thead><tr><th>Book</th><th>Rule</th><th>What it is for</th></tr></thead><tbody>' + books + "</tbody></table>",
      "<p>Every book is one unit per trade, percent of notional, no leverage, no fees, no funding. The dollar figures on this page are sums of equal-size trades at the size box, never an account balance. The cap is 20 trading days after the entry day; a trade still open there is marked at that close; a trade the data ends on is censored and carries no result.</p>",
      "<h2>Where the books stand (the receipt, plain daily rows)</h2>",
      "<p>Taking the stop away and managing the STRAT way turned every plain daily pattern from a loser into roughly flat: the chance book lost 0.27 to 0.84 percent per trade; the management books sit between -0.24 and +0.24. On the same trades at the same five-bar horizon, the stop swap alone (D5 against the chance book) is worth +0.48 to +0.92 per trade, intervals clear of zero. It is not a money machine: the median trade still loses on the books that hold for structure, two trades in three close red on the exit-only book, and the averages are carried by the right tail. The price of no stop is that tail: two trades in five travel more than one R against you before the close exit, one in ten more than two R. Weekly and monthly rows on the daily clock get cut short and lose to the chance book's five-bar hold. After the venue's taker fee, three lines keep an interval over zero: the reversal held to the exit (C), and the inside break managed to one R (D, D5). Nothing is promoted.</p>",
      "<h2>Reading the chart</h2>",
      "<ul><li>Grey candles are outside any trade; the <b>amber</b> candle is the setup bar, the darker amber the bar before it; the trade's own candles are green or red by their close.</li>",
      "<li><b>Position opened</b> is the entry level; dashed blue lines are the other timeframes' triggers that broke the same day, with the gap band between them. <b>Position closed</b> is the selected book's fill.</li>",
      "<li>Green dashed lines are T1 / T2 / T3; violet is one R; grey is the chance book's setup-bar stop; amber dashes the measured move. The dotted light-blue step line is the week's open, the exit test's second half.</li>",
      "<li>Arrows mark the entry and the book's exit on the first bar that touched the price; circles mark target, one-R and stop touches; small squares mark the other clocks (daily clock out when the book left elsewhere, under water, hourly).</li>",
      "<li>System levels are read-only (they are axis ranges, not drawings). Your own drawings come from the toolbar and are saved per coin and per pane in this browser; the save control in the toolbar can also restore or clear them.</li></ul>",
      "<h2>The chips</h2>",
      "<ul><li><b>W 2U / M 2D</b>: the STRAT type of the last closed week and month before the entry, each typed against the bar before it with strict breaks (an equal high or low never breaks). An inside week or month (amber, bordered) is the owner's hazard: the break is happening inside a coil one level up.</li>",
      "<li><b>Week at entry</b>: with = price on the trade's side of Monday's open at the moment of entry; against = the trade is fighting the week.</li>",
      "<li><b>Hammer flag</b>: the setup bar closed in the far third of its own range (third), or passed the strict hammer / shooter detector (strict).</li>",
      "<li><b>Liquid</b>: the coin passed the census's liquidity screen that day. <b>Venue</b>: main perps or the xyz dex.</li></ul>",
      "<h2>What this page never does</h2>",
      "<p>It re-runs no trade logic. Every level, target, touch day and fill is the row the engine wrote (results/manage_trades.csv.gz); the chart only draws it, and a chart that disagrees with a row is evidence against the engine. Weekly and monthly candles are bucketed from the daily bars with the census's calendar (Monday 00:00 UTC weeks, calendar months); nothing is aggregated on zoom.</p>",
    ].join("\n");
  }

  DV.story = { narrate, ladder, context, playbook, setupWords };
})(window.DV);
