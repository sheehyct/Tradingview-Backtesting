/* story.js: the trade in plain trader language, generated from the recorded card (nothing here
   computes a trade: every price, time and fill is read off the card the engine wrote; the clock
   sentences describe the bar at the recorded exit time), the book ladder for one trade, and the
   Playbook (the run's rule card and its books, plus what the chart shows). Every book's words come
   from the run's own book definition (its name, rule and declared target), never from its id. */
window.DV = window.DV || {};
(function (DV) {
  "use strict";
  const C = DV.core;
  const { iso, isoH, longDate, shortDate, weekdayOf, fmtPrice, fmtPct, fmtUsd, cls, esc, tfLabel, tfWord, KIND_LABEL, CLS_LABEL, BT_WORD, settle, stackLevels, htfType, btChip, oneR, stackWords,
    bookName, bookRule, bookRole, bookTarget, bookCol, bookRes, entryRes, bookLabel, ladderBooks, groupNames, groupBooks, headline, getRun, targetName, HOUR } = C;

  function words(long) {
    return { side: long ? "long" : "short", hi: long ? "high" : "low", lo: long ? "low" : "high", up: long ? "up" : "down", down: long ? "down" : "up",
      above: long ? "above" : "below", below: long ? "below" : "above", redWord: long ? "red" : "green" };
  }
  const n2 = (x) => x == null ? "?" : Number(x).toFixed(2);
  const TARGET_WORD = { T1: "T1", T2: "T2", T3: "T3", mm: "the measured move", one_r: "one R" };

  // ---------------------------------------------------------------- the setup, in words
  function setupWords(t) {
    const long = t.direction === "up", w = words(long);
    const inner = t.tf === "D" ? "bar" : tfWord(t.tf);
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
    return esc(t.pattern || "");
  }

  function targetWords(t, p, cal, i) {
    const inner = t.tf === "D" ? "bar" : tfWord(t.tf);
    const parts = [];
    const src = t.t1_src;
    const touched = (k, verb) => k == null ? " (never " + (verb || "touched") + " inside the window)" : " (" + (verb || "touched") + " " + dayWord(k, cal, i).replace(" (", ", ").replace(")", "") + ")";
    if (t.t1 != null) {
      const why = src === "anchor" ? "the pattern's own magnitude, the far side of the " + inner + " before the setup " + inner
        : src === "W" ? "the first unbroken weekly level beyond the entry" : src === "M" ? "the first unbroken monthly level beyond the entry" : src === "mm" ? "the measured move" : src ? esc(src) : "";
      parts.push("T1 " + fmtPrice(t.t1, p) + (why ? " is " + why : "") + touched(t.t1_k) + ".");
      const rungs = [];
      const srcWord = (s) => s === "W" ? "weekly" : s === "M" ? "monthly" : s || "";
      if (t.t2 != null) rungs.push("T2 " + fmtPrice(t.t2, p) + " (" + srcWord(t.t2_src) + touched(t.t2_k).replace(" (", ", ").replace(/\)$/, "") + ")");
      if (t.t3 != null) rungs.push("T3 " + fmtPrice(t.t3, p) + " (" + srcWord(t.t3_src) + touched(t.t3_k).replace(" (", ", ").replace(/\)$/, "") + ")");
      if (rungs.length) parts.push(rungs.join(" and ") + (rungs.length > 1 ? " are the next unbroken levels beyond it, fixed at entry." : " is the next unbroken level beyond it, fixed at entry."));
      else parts.push("No further unbroken weekly or monthly level sits beyond it, so there is no T2.");
    } else if (src === "none") parts.push("No unbroken weekly or monthly level sat beyond the entry, so this trade has no T1: the target books can only leave on the exit.");
    else if (src === "zero") parts.push("The pattern's anchor sits at the entry price itself, so there is no T1.");
    else parts.push("This trade has no T1 on the card" + (t.t1_src ? " (" + esc(t.t1_src) + ")" : "") + ".");
    if (t.stop != null) {
      const r = oneR(t);
      if (r != null) {
        parts.push("One R is " + (t.r_pct != null ? n2(t.r_pct) + "% of price" : "the setup range") + ": the setup " + inner + "'s far side at " + fmtPrice(t.stop, p) +
          " is the reference stop" + touched(t.stop_k, "hit") + " and only a yardstick for the management books (they have no stop), so one R sits at " + fmtPrice(r, p) + touched(t.one_r_k) + ".");
      } else {
        parts.push("The setup " + inner + "'s far side at " + fmtPrice(t.stop, p) + " is the reference stop" + touched(t.stop_k, "hit") + (t.r_pct != null ? ", " + n2(t.r_pct) + "% of price" : "") +
          ": for this " + (t.direction === "up" ? "long" : "short") + " one R would lie at or below zero (the setup range exceeds the price), so no one-R fill is possible" + (t.one_r_raw != null ? " (the engine's figure: " + fmtPrice(t.one_r_raw, p) + ")" : "") + ".");
      }
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
  function hoursHeld(b) { return b && b.entry != null && b.at != null ? Math.round((b.at - b.entry) / HOUR) : null; }
  function whenShort(t, b, hourly) {
    if (!b || b.at == null) return "";
    const h = hourly ? hoursHeld(b) : null;
    if (h != null) return h === 0 ? "on its entry hour" : "after " + h + " h";
    return b.k === 0 ? "on the entry day" : "on day " + b.k;
  }
  const hoursWord = (h) => h + (h === 1 ? " hour" : " hours");
  function clockWords(t, cal, i, p, b, hourly) {
    // the clock sentence for a book entry: a reading of the bar at the recorded exit time (never the rule)
    const long = t.direction === "up", w = words(long);
    if (b.how === "clock") {
      if (hourly && b.at != null) {
        const hb = cal.hourly.find((x) => x[0] === b.at);
        const held = hoursHeld(b);
        const colour = hb ? (hb[4] < hb[1] ? "red" : hb[4] > hb[1] ? "green" : "flat") : null;
        const di = cal.dayIdx.get(iso(b.at)), day = di != null ? cal.daily[di] : null;
        const dayColour = day ? (day[4] < day[1] ? "red" : day[4] > day[1] ? "green" : "flat") : null;
        return "The exit clock fired" + (held != null ? (held === 0 ? " on its entry hour" : " " + hoursWord(held) + " after its entry hour") : "") + ", at " + isoH(b.at) + " UTC" +
          (hb ? ": that hour closed " + colour + " at " + fmtPrice(hb[4], p) + ", " + w.below + " its open " + fmtPrice(hb[1], p) + (dayColour ? ", with the day " + dayColour + " too" : "") : "") + ".";
      }
      const k = b.k == null ? 0 : b.k, j = Math.min(i + k, cal.daily.length - 1), bar = cal.daily[j], wo = cal.weekOpenAt(bar[0]);
      const monday = C.weekStart(bar[0]) === bar[0];
      const colour = bar[4] < bar[1] ? "red" : bar[4] > bar[1] ? "green" : "flat";
      return "The exit clock fired " + (k === 0 ? "on the entry day" : "on day " + k) + ", " + weekdayOf(iso(bar[0])) + " " + shortDate(iso(bar[0])) + ": that day closed " + colour + " at " + fmtPrice(bar[4], p) +
        ", " + w.below + " its open " + fmtPrice(bar[1], p) + (monday ? " (a Monday, so the day's open is the week's open and the two tests are one)" : wo != null ? " and " + w.below + " the week's open " + fmtPrice(wo, p) : "") + ".";
    }
    if (b.how === "cap") {
      if (hourly && b.at != null) return "Nothing fired inside the book's horizon, so the row is marked at the cap hour, " + isoH(b.at) + " UTC.";
      return "Nothing fired inside the book's horizon, so the row is marked at the cap " + dayWord(b.k, cal, i) + ".";
    }
    if (b.how === "censored") return "The data ends inside the book's window, so the row is censored: no result is recorded.";
    return "Not scored" + (b.note ? ": " + esc(b.note) : "") + ".";
  }
  function bookWords(t, book, cal, i, p, size) {
    const st = settle(t, book);
    const b = t.byBook ? t.byBook[book] : null;
    const label = bookLabel(book), name = bookName(book), rule = bookRule(book);
    const money = (r) => r == null ? "no result" : '<b class="' + cls(r) + '">' + fmtPct(r) + "</b> (" + fmtUsd(r, size) + " on " + size.toLocaleString("en-US") + ")";
    const isRef = bookRole(book) === "reference";
    const named = isRef ? label : label + " (" + esc(name) + ")";
    if (st.absent) return named + " does not apply to this trade.";
    if (st.missing) return named + " has " + (b && b.how === "none" ? esc(st.how) : "no result: " + esc(st.how)) + ". Nothing of another book is borrowed here.";
    const hourly = entryRes(book, b) === "hour";
    const lead = (isRef ? label : label + ", " + esc(name)) + ": " + esc(rule) + " ";
    const head = headline(), hb = t.byBook[head];
    const past = book !== head && hb && hb.how === "cap" && b.k != null && hb.k != null && b.k > hb.k ? " That is past the headline's cap (day " + hb.k + "), where " + bookLabel(head).toLowerCase() + " is marked open." : "";
    const when = (k) => dayWord(k, cal, i);
    if (b.how === "target" || b.how === "one_r") {
      const what = b.how === "one_r" ? "One R at " + fmtPrice(b.price, p) : "Its target " + (targetName(t, b.price) || "") + " at " + fmtPrice(b.price, p);
      const sameDay = hb && hb.how === "clock" && hb.k != null && b.k === hb.k ? ", on the exit day itself (a touch on the exit day fills first)" : "";
      const touchedWhen = hourly && b.entry != null ? " " + whenShort(t, b, true) : " " + when(b.k);
      return lead + what + " was touched" + touchedWhen + sameDay + ", so the book left there: " + money(b.ret) + "." + past;
    }
    if (b.how === "stop") {
      const tie = t.one_r_k != null && t.one_r_k === b.k;
      return lead + "Its stop at " + fmtPrice(b.price, p) + " was hit " + when(b.k) +
        (tie ? ", the same day one R was touched: the daily bar cannot say which came first, and the engine takes the stop (pessimistic)" : t.one_r_k == null ? " and one R was never touched inside the window" : t.one_r_k > b.k ? ", before one R" : "") +
        ", so the book is out there: " + money(b.ret) + "." + (b.note ? " " + esc(b.note) + "." : "");
    }
    // a clock exit or a cap mark: a book that takes a target says first why it never got there
    let pre = "";
    const tg = bookTarget(book);
    if (tg) {
      const tgw = TARGET_WORD[tg] || tg;
      const key = tg === "mm" ? "mm_t1" : tg === "one_r" ? null : tg.toLowerCase();
      const tp = tg === "one_r" ? oneR(t) : key && t[key] != null ? t[key] : null;
      const tk = tg === "one_r" ? t.one_r_k : tg === "mm" ? t.mm1_k : t[tg.toLowerCase() + "_k"];
      if (tp == null) pre = "This trade has no " + tgw + (tg === "one_r" && t.stop != null ? " (it lies at or below zero)" : "") + ", so the book rides the exit. ";
      else pre = (tg === "one_r" ? "One R" : tgw.charAt(0).toUpperCase() + tgw.slice(1)) + " at " + fmtPrice(tp, p) + (tk == null ? " was never touched inside the window" : b.k != null && tk > b.k ? " was only touched " + when(tk) + ", after the exit" : " was not touched before the exit") + ", so it rode the exit. ";
    }
    const clock = clockWords(t, cal, i, p, b, hourly);
    if (b.how === "clock") return lead + pre + clock + " Filled at that close: " + money(b.ret) + "." + past;
    return lead + pre + clock + " Marked: " + money(b.ret) + "." + past;
  }
  function otherClocks(t, cal, i, p) {
    // the grouped books (the same book on another clock or target), one sentence per group
    const out = [];
    for (const g of groupNames()) {
      const ids = groupBooks(g).filter((id) => t.byBook && t.byBook[id]);
      if (!ids.length) continue;
      // inside its group a book keeps only what differs: "all out at T1, hourly clock" reads "all out at T1"; the exit-only
      // variant, whose name is the group's, reads "exit only"
      const short = (id) => { const n = bookName(id); return n === g ? "exit only" : n.endsWith(", " + g) ? n.slice(0, -(g.length + 2)) : n; };
      const bits = ids.map((id) => {
        const b = t.byBook[id], hourly = entryRes(id, b) === "hour";
        if (b.how === "none" || b.how === "censored") return esc(short(id)) + ": " + esc(C.howWords(t, b));
        const how = b.how === "clock" ? "out" : b.how === "cap" ? "marked at the cap" : b.how === "target" ? (targetName(t, b.price) || "target") : b.how === "one_r" ? "one R" : "stop";
        return esc(short(id)) + ": " + how + " " + whenShort(t, b, hourly) + ", " + fmtPct(b.ret);
      });
      const first = t.byBook[ids[0]];
      const lead = g.charAt(0).toUpperCase() + g.slice(1) + (entryRes(ids[0], first) === "hour" && first && first.entry != null ? " (entered at " + isoH(first.entry) + " UTC)" : "");
      out.push(lead + ": " + bits.join("; ") + ".");
    }
    return out;
  }

  // ---------------------------------------------------------------- the whole story for one trade
  function narrate(c) {
    const { t, coin, cal, book, size, p } = c;
    const long = t.direction === "up", w = words(long);
    const i = cal.dayIdx.get(t.date);
    if (i == null) return "<p>This trade's entry day is not in the instrument's daily bars.</p>";
    const levels = stackLevels(t, i, cal);
    let stack = "";
    if (levels.length > 1) {
      const sw = stackWords(t, levels);
      const name = (l) => "the " + tfWord(l.tf) + "'s level " + fmtPrice(l.price, p);
      const convOthers = sw.conv.filter((l) => l.tf !== t.tf);
      if (convOthers.length) {
        const prices = sw.conv.map((l) => l.price), gap = (Math.max(...prices) - Math.min(...prices)) / Math.min(...prices) * 100;
        stack += " The same day broke " + convOthers.map(name).join(" and ") + " (" + (CLS_LABEL[t.cls] || t.cls) + ", a " + gap.toFixed(2) + "% gap between the triggers" + (t.cls !== "spread" ? ": a domino, the levels converged" : "") + ").";
      }
      if (sw.far.length) stack += " " + sw.far.map((l) => name(l) + " also broke the same day, " + (l.gap >= 0 ? "+" : "") + l.gap.toFixed(2) + "% beyond the entry").join("; ") + (convOthers.length ? ": not part of the converged stack, the entry-time class does not describe it." : ": too far from the entry to be a domino (the entry-time class is " + (CLS_LABEL[t.cls] || t.cls) + ").");
    }
    const week = t.w_support === "with" ? "The week was on the trade's side at entry (price " + w.above + " Monday's open)." : t.w_support === "against" ? "The week was against the trade at entry (price " + w.below + " Monday's open)." : "";
    const paras = [];
    paras.push("<p><b>" + esc(coin) + " " + w.side + ", " + tfLabel(t.tf) + " " + (KIND_LABEL[t.kind] || esc(t.pattern || t.kind)) + ".</b> " + setupWords(t) + " Entered " + longDate(t.date) + " at " + fmtPrice(t.level, p) +
      ", the instant the " + tfWord(t.tf) + "'s level broke." + stack + (week ? " " + week : "") + "</p>");
    paras.push("<p><b>The plan at entry.</b> " + targetWords(t, p, cal, i) + "</p>");
    paras.push("<p><b>What book " + esc(book) + " did.</b> " + bookWords(t, book, cal, i, p, size) + "</p>");
    const others = otherClocks(t, cal, i, p);
    if (others.length) paras.push("<p><b>The other clocks.</b> " + others.join(" ") + "</p>");
    const travel = [];
    if (t.mfe_x != null || t.mae_x != null) travel.push("Between the entry and book " + esc(t.window) + "'s exit (the headline window, whatever book is selected; the engine records travel once) the trade got +" + n2(t.mfe_x) + "% in its favour at best and " + n2(t.mae_x) + "% against it at worst" +
      (t.r_pct != null && t.mae_x != null ? " (" + (t.mae_x / t.r_pct).toFixed(1) + " R of adverse travel)" : "") + ".");
    const nb = { with: "went with the trade", against: "went against it", inside: "stayed inside the entry " + tfWord(t.tf), outside: "went through both sides (an outside bar)" }[t.next_bar];
    if (nb) travel.push("The " + tfWord(t.tf) + " after the entry " + nb + ".");
    if (travel.length) paras.push("<p><b>Travel.</b> " + travel.join(" ") + "</p>");
    paras.push('<p class="fine">Levels, targets, touch times and book fills are the recorded card; the words only read them back. Clock sentences describe the bar at the recorded exit time; the rule is the book\'s own line. Context chips describe candles and do not change the trade.</p>');
    return paras.join("");
  }

  // ---------------------------------------------------------------- the book ladder for one trade
  function ladder(c) {
    const { t, book, size, p } = c;
    const row = (b) => {
      const st = settle(t, b), e = t.byBook ? t.byBook[b] : null;
      const has = !!e && !st.missing;
      const hourly = entryRes(b, e) === "hour";
      const when = has ? (hourly && e.entry != null ? whenShort(t, e, true) : st.k === 0 ? "entry day" : "day " + st.k) : "";
      const date = has && st.t != null ? (hourly ? isoH(st.t) : iso(st.t)) : "";
      return '<tr class="' + (b === book ? "sel" : "") + '" data-book="' + esc(b) + '" title="' + esc(bookRule(b) + (date ? " Settled " + date + "." : "")) + '"><td><span class="dot" style="background:' + bookCol(b) + '"></span>' + esc(bookRole(b) === "reference" ? bookName(b) : b + ": " + bookName(b)) + "</td>" +
        "<td>" + (e ? esc(st.how) : "n/a") + "</td><td>" + when + "</td>" +
        '<td class="num"><b class="' + cls(has ? st.ret : null) + '">' + (has ? fmtPct(st.ret) : "-") + "</b></td></tr>";
    };
    const rows = ladderBooks().map(row);
    for (const g of groupNames()) {
      const ids = groupBooks(g).filter((id) => t.byBook && t.byBook[id]);
      if (!ids.length) continue;
      rows.push('<tr class="grp"><td colspan="4"><span class="dot" style="background:' + bookCol(ids[0]) + '"></span>' + esc(g) + "</td></tr>");
      for (const id of ids) rows.push(row(id));
    }
    const sel = settle(t, book);
    return '<table class="ladder"><thead><tr><th>Book</th><th>How it left</th><th>When</th><th class="num">Result</th></tr></thead><tbody>' + rows.join("") + "</tbody></table>" +
      '<div class="fine">Fill = the recorded price (a clock exit\'s close is recovered from the recorded return); ' + (sel.price != null ? "book " + esc(book) + " fills at " + fmtPrice(sel.price, p) + " for " + fmtUsd(sel.ret, size) : "book " + esc(book) + " has no fill on this trade") + ". Click a row to select that book.</div>";
  }

  // ---------------------------------------------------------------- context chips for one trade
  function context(c) {
    const { t, cal } = c;
    const i = cal.dayIdx.get(t.date);
    const wt = i != null ? htfType(cal, "W", i) : { code: "?", title: "" }, mt = i != null ? htfType(cal, "M", i) : { code: "?", title: "" };
    const items = [];
    items.push(["Last closed week", btChip("W", wt) + " " + BT_WORD[wt.code], "the complete week before the entry, typed as a STRAT bar against the week before it (R10: strict breaks). An inside week is the owner's hazard."]);
    items.push(["Last closed month", btChip("M", mt) + " " + BT_WORD[mt.code], "the complete month before the entry, typed the same way."]);
    items.push(["Week at entry", t.w_support === "with" ? '<span class="chip ok">with the trade</span>' : t.w_support === "against" ? '<span class="chip warn">against the trade</span>' : '<span class="chip dim">n/a</span>', "price above Monday's open for a long (below for a short) at the moment of entry."]);
    items.push(["Stack", t.stackList && t.stackList.length > 1 ? '<span class="chip flag">' + esc(stackWords(t, i != null ? stackLevels(t, i, cal) : []).text) + "</span>" : '<span class="chip tf">' + tfLabel(t.tf) + " alone</span>", "the converged same-day breaks with their class, then any other level that broke the same day with its distance from the entry."]);
    items.push(["Hammer flag", t.flag && t.flag !== "none" ? '<span class="chip flag">' + (t.flag === "strict" ? "strict (detector)" : "third (range test)") + "</span>" : '<span class="chip dim">none</span>', "the setup bar closed in the far third of its own range (third) or passed the strict hammer / shooter detector (strict)."]);
    items.push(["Liquidity", t.liquid ? '<span class="chip tf">liquid</span>' : '<span class="chip dim">thin</span>', "the instrument passed the census's liquidity screen on the entry day."]);
    items.push(["Venue", '<span class="chip dim">' + esc(t.dex || "") + "</span>", "main = the venue's own perps; xyz = the HIP-3 dex."]);
    return items.map((x) => '<div class="ctx" title="' + esc(x[2]) + '"><span class="cl">' + x[0] + "</span><span class=\"cv\">" + x[1] + "</span></div>").join("");
  }

  // ---------------------------------------------------------------- the Playbook: the run's rule card and its books
  function playbook(run) {
    run = run || getRun() || {};
    const rules = run.rules || {};
    const ruleRows = ["setup", "entry", "stop", "targets", "exit", "continuity", "sizing"].filter((k) => rules[k]).map((k) => "<tr><td><b>" + esc(k) + "</b></td><td>" + esc(rules[k]) + "</td></tr>").join("");
    const books = (run.books || []).map((b) => "<tr><td><span class=\"dot\" style=\"background:" + bookCol(b.id) + "\"></span><b>" + esc(b.id) + ": " + esc(b.name) + "</b></td><td>" + esc(C.ROLE_WORD[b.role] || b.role) + (b.group ? " (" + esc(b.group) + ")" : "") + (b.target ? ", takes " + esc(TARGET_WORD[b.target] || b.target) : "") + "</td><td>" + esc(b.rule) + "</td></tr>").join("");
    const clock = run.clock || {};
    const src = run.source || {};
    return [
      "<h1>" + esc(run.name || "Playbook") + "</h1>",
      '<p class="lead">' + esc(run.notes || "What every trade on this page is, how it is managed, and what each book means.") + "</p>",
      "<h2>The run</h2>",
      "<p>As of <b>" + esc(run.as_of || "?") + "</b>" + (run.built ? ", built " + esc(run.built) : "") + ". The day rolls at <b>" + esc(clock.day_roll || "?") + "</b>; fills are known to the <b>" + esc(clock.resolution || "?") + "</b>" + (clock.weeks ? "; weeks " + esc(clock.weeks) : "") + (clock.months ? ", months " + esc(clock.months) : "") +
        ". Returns are " + esc(run.returns || "percent of price") + "." + (src.repo ? " Source: " + esc(src.repo) + (src.commit ? " at " + esc(src.commit) : "") + (src.command ? " (<code>" + esc(src.command) + "</code>)" : "") + "." : "") + "</p>",
      '<table class="pb"><thead><tr><th>Rule</th><th>In words</th></tr></thead><tbody>' + ruleRows + "</tbody></table>",
      "<h2>The trade</h2>",
      "<p>Every card is a level break on a STRAT bar: the first time price trades through the setup bar's high (long) or low (short). The entry is at the level the instant it breaks; the card carries the levels fixed at entry and what every book did afterwards.</p>",
      "<ul><li><b>2-2 reversal</b>: the setup bar had gone one way (a 2 down for a long), the break goes the other way. Its magnitude is the far side of the bar before the setup bar, where the compound 3 completes.</li>",
      "<li><b>2-2 continuation</b>: the setup bar had already broken in the trade's direction and breaks again. No magnitude of its own.</li>",
      "<li><b>Inside break</b>: the setup bar stayed inside the bar before it. If that earlier bar went the other way or outside, the pattern's magnitude is its far side; if it went the same way (a with-trend inside) or was inside too (a stack), there is no magnitude of its own.</li>",
      "<li><b>Outside break (3-2)</b>: the setup bar went through both sides of the bar before it. No magnitude of its own.</li></ul>",
      "<p>Weekly and monthly cards are the same thing one level up: the week's or month's level breaks on some day, and that day is the entry day. A <b>stack</b> is a day on which more than one timeframe's level broke; the chips say how close the triggers were.</p>",
      "<h2>The books</h2>",
      '<table class="pb"><thead><tr><th>Book</th><th>Role</th><th>Rule</th></tr></thead><tbody>' + books + "</tbody></table>",
      "<p>Every book is one unit per trade, " + esc(run.returns || "percent of price, equal size, no fees, no leverage") + ". The dollar figures on this page are sums of equal-size trades at the size box, never an account balance. A book absent from a card does not apply to that trade; a book marked <i>not scored</i> applied and the engine did not score it, with the reason on the card. Grouped books are the same book on another clock or target: the ladder lists them under their group, the Compare tab leaves them out.</p>",
      "<h2>Reading the chart</h2>",
      "<ul><li>Grey candles are outside any trade; the <b>amber</b> candle is the setup bar, the darker amber the bar before it; the trade's own candles are green or red by their close.</li>",
      "<li><b>Position opened</b> is the entry level; dashed blue lines are the other timeframes' triggers that broke the same day, with the gap band between them. <b>Position closed</b> is the selected book's fill.</li>",
      "<li>Green dashed lines are the targets; violet is one R; grey is the reference stop (the setup bar's far side); amber dashes the measured move. The dotted light-blue step line is the week's open.</li>",
      "<li>Arrows mark the entry and the book's exit on the first bar that touched the recorded price; circles mark target, one-R and stop touches; small squares mark the other clocks (the headline clock when the selected book left elsewhere, and the first book of each group).</li>",
      "<li>System levels are read-only (they are axis ranges, not drawings). Your own drawings come from the toolbar and are saved per instrument and per pane in this browser; the save control in the toolbar can also restore or clear them.</li></ul>",
      "<h2>The chips</h2>",
      "<ul><li><b>W 2U / M 2D</b>: the STRAT type of the last closed week and month before the entry, each typed against the bar before it with strict breaks (an equal high or low never breaks). An inside week or month (amber, bordered) is the hazard the owner watches.</li>",
      "<li><b>Week at entry</b>: with = price on the trade's side of Monday's open at the moment of entry; against = the trade is fighting the week.</li>",
      "<li><b>Hammer flag</b>: the setup bar closed in the far third of its own range (third), or passed the strict hammer / shooter detector (strict).</li>",
      "<li><b>Liquid</b>: the instrument passed the census's liquidity screen that day. <b>Venue</b>: main perps or the xyz dex.</li></ul>",
      "<h2>What this page never does</h2>",
      "<p>It re-runs no trade logic. Every level, target, touch time and fill is the card the run wrote (viewer/CONTRACT.md); the chart only draws it, and a chart that disagrees with a card is evidence against the engine. Weekly and monthly candles are aggregated from the daily bars with the run's calendar rules.</p>",
    ].join("\n");
  }

  DV.story = { narrate, ladder, context, playbook, setupWords, clockWords, bookWords, otherClocks };
})(window.DV);
