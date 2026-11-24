"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const SVG = "http://www.w3.org/2000/svg";
  const SUBJ = { phy: "physics", chem: "chemistry", math: "maths" };
  const SAMPLE_NAMES = {
    line: "one print line", press: "a whole press", small: "a 12-question leak", heavy: "a badly copied leak",
    rewrite70: "a rewritten leak (70% of words dropped)", two: "two leakers", setter: "the setter's copy",
    shared: "shared questions only", null: "no leak at all", photo: "a photographed guess paper", panel: "the chemistry setters and translators (the 2026 pattern)",
  };
  let design = null;
  let truth = null;

  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  const lakh = (n) => (n / 100000).toLocaleString("en-IN", { maximumFractionDigits: 2 }) + " lakh";
  const pct = (x) => (x * 100).toLocaleString("en-IN", { maximumFractionDigits: 1 }) + "%";

  // ---------- custody chain + answer grid ----------
  const colX = (c) => 68 + 72 * c;
  const pressX = (cs) => (colX(cs[0]) + colX(cs[cs.length - 1])) / 2;

  function drawChain(result) {
    const svg = $("chain");
    [...svg.querySelectorAll("g, line, path, text, rect, circle")].forEach((n) => n.remove());
    const g = design.compartments;
    const lit = new Set(result ? result.nodes : []);
    const present = new Set(result ? result.present : []);
    if (lit.has("SETTER")) { Object.keys(design.presses).forEach((p) => lit.add(p)); for (let c = 0; c < g; c++) lit.add("C" + c); }
    for (const [p, cs] of Object.entries(design.presses)) if (lit.has(p)) cs.forEach((c) => lit.add("C" + c));

    const edges = el("g", {}, svg);
    const nodes = el("g", {}, svg);
    const node = (id, label, cx, y, w, h) => {
      const n = el("g", { class: "node" + (lit.has(id) ? " lit" : "") }, nodes);
      el("rect", { x: cx - w / 2, y, width: w, height: h, rx: 3 }, n);
      const t = el("text", { x: cx, y: y + h / 2 + 4.5 }, n);
      t.textContent = label;
    };
    node("SETTER", "Setter", 320, 12, 110, 30);
    for (const [p, cs] of Object.entries(design.presses)) {
      const px = pressX(cs);
      el("path", { d: `M320 42 C320 60 ${px} 58 ${px} 76`, class: "edge" + (lit.has(p) ? " lit" : "") }, edges);
      node(p, "Press " + p.slice(1), px, 76, 70, 28);
      cs.forEach((c) => {
        el("path", { d: `M${px} 104 C${px} 120 ${colX(c)} 118 ${colX(c)} 134`, class: "edge" + (lit.has("C" + c) ? " lit" : "") }, edges);
      });
    }
    const filled = new Map();
    (result ? result.matches : []).forEach((m, i) => filled.set(m.block + ":" + m.slot, i));
    const perSubj = design.unique_per_compartment / design.subjects.length;
    for (let c = 0; c < g; c++) {
      const cx = colX(c);
      node("C" + c, "C" + c, cx, 134, 52, 26);
      design.subjects.forEach((s, k) => {
        const t = el("text", { x: cx + (k - 1) * 14, y: 178, class: "subj" }, svg);
        t.textContent = s[0].toUpperCase();
      });
      el("rect", { x: cx - 24, y: 184, width: 48, height: 146, rx: 4, class: "col-frame" + (present.has(c) ? " present" : "") }, svg);
      for (let slot = 0; slot < design.unique_per_compartment; slot++) {
        const k = Math.floor(slot / perSubj), r = slot % perSubj;
        const i = filled.get(c + ":" + slot);
        const b = el("circle", { cx: cx + (k - 1) * 14, cy: 194 + r * 14, r: 5, class: "bubble" + (i !== undefined ? " on" : "") }, svg);
        if (i !== undefined) b.style.setProperty("--d", Math.min(i * 0.015, 1.2) + "s");
      }
      const t = el("text", { x: cx, y: 350, class: "count" + (present.has(c) ? " present" : "") }, svg);
      t.textContent = result ? result.hits[c] + " found" : "";
    }
    const sharedFound = result ? result.shared_hits : 0;
    const lab = el("text", { x: 20, y: 396, class: "shared-label" }, svg);
    lab.textContent = result ? `Shared, on every form: ${sharedFound} found` : "Shared, on every form";
    for (let slot = 0; slot < design.shared; slot++) {
      const i = filled.get("S:" + slot);
      const b = el("circle", { cx: 226 + slot * 13.4, cy: 392, r: 5, class: "bubble" + (i !== undefined ? " on" : "") }, svg);
      if (i !== undefined) b.style.setProperty("--d", Math.min(i * 0.015, 1.2) + "s");
    }
  }

  // ---------- verdict ----------
  function nodeName(n) {
    if (n === "SETTER") return "the setter";
    if (n.startsWith("P")) return `press ${n.slice(1)} (lines ${design.presses[n].map((c) => "C" + c).join(" and ")})`;
    const c = +n.slice(1);
    const p = Object.keys(design.presses).find((k) => design.presses[k].includes(c));
    return `print line ${n} at press ${p.slice(1)}`;
  }

  function verdictText(r) {
    const own = design.unique_per_compartment;
    const others = (set) => Math.max(0, ...Object.entries(r.hits).filter(([c]) => !set.has(+c)).map(([, v]) => v));
    switch (r.verdict) {
      case "NAMED": {
        const n = r.nodes[0];
        const set = new Set(r.present);
        if (n === "SETTER" && r.panel) {
          const sub = SUBJ[r.panel] || r.panel;
          return [`The leak came from the setting stage: the ${sub} panel.`,
            `Every line's ${sub} questions are in it, and almost nothing else. Start with the ${sub} setters and translators.`];
        }
        if (n === "SETTER") return [`The leak came from the setter.`, `Every line's own questions are in it, so it was copied before the paper split into lines.`];
        const found = r.present.map((c) => `${r.hits[c]} of ${own}`).join(" and ");
        return [`The leak came from ${nodeName(n)}.`,
          `${found} of ${r.present.length > 1 ? "those lines'" : "that line's"} own questions are in this paper. ` +
          (others(set) ? `No other line has more than ${others(set)}.` : "No other line has any.")];
      }
      case "MULTIPLE":
        return [`Two or more sources: ${r.nodes.map(nodeName).join("; ")}.`,
          `Either separate leakers, or one holder upstream of all of them, such as the setter's office.`];
      case "SHARED ONLY":
        return [`No source can be named.`, `Only shared questions are in this paper, and every line held those. Drop them from everyone's score.`];
      default:
        return [`No bank question found in this paper.`, `Nothing to re-sit. If this is a real leak, the paper was not built from this bank.`];
    }
  }

  function truthMatches(r) {
    if (!truth) return null;
    const s = truth.sources;
    if (s[0] === "none") return r.verdict === "NOT FOUND";
    if (s[0] === "SHARED") return r.verdict === "SHARED ONLY";
    if (s[0].startsWith("PANEL:")) return r.nodes.join() === "SETTER" && r.panel === s[0].slice(6);
    return [...s].sort().join() === [...r.nodes].sort().join();
  }

  function render(r) {
    const [main, sub] = verdictText(r);
    const vl = $("verdict-line");
    vl.className = "verdict-line" + (r.verdict === "NAMED" || r.verdict === "MULTIPLE" ? " named" : "");
    vl.querySelector(".verdict-main").textContent = main;
    vl.querySelector(".verdict-sub").textContent = sub;

    const ok = truthMatches(r);
    const tr = $("truth");
    if (ok === null) tr.hidden = true;
    else {
      const s0 = truth.sources[0];
      const src = s0 === "none" ? "nowhere (no leak)" : s0 === "SHARED" ? "the shared questions only"
        : s0.startsWith("PANEL:") ? `the ${SUBJ[s0.slice(6)]} setters' questions` : truth.sources.join(" and ");
      tr.hidden = false;
      tr.textContent = `Simulated answer key: this paper was built from ${src}. Bulkhead's verdict ${ok ? "matches" : "does not match"}.`;
    }

    $("need").textContent = r.rule.presence_needed;
    drawChain(r);

    const resp = r.response;
    $("retest-share").textContent = pct(resp.retest_share);
    $("retest-label").textContent = resp.sections
      ? `of candidates re-sit, ${SUBJ[resp.sections[0]]} section only`
      : "of candidates re-sit with Bulkhead";
    const il = resp.illustration;
    $("illus").textContent = il
      ? (resp.sections
        ? `At an illustrative ${lakh(il.candidates)} candidates: all re-sit one subject instead of the whole paper.`
        : `At an illustrative ${lakh(il.candidates)} candidates: ${il.retest ? "about " + lakh(il.retest) : "nobody"} re-sit, instead of all ${lakh(il.candidates)}.`)
      : "";
    const steps = $("steps");
    steps.replaceChildren(...resp.actions.map((a) => { const li = document.createElement("li"); li.textContent = a; return li; }));

    const body = $("ev-body");
    if (!r.matches.length) {
      const tr2 = document.createElement("tr"), td = document.createElement("td");
      td.colSpan = 5; td.className = "empty"; td.textContent = "No question in this paper matches the bank.";
      tr2.appendChild(td); body.replaceChildren(tr2);
    } else {
      body.replaceChildren(...r.matches.map((m) => {
        const row = document.createElement("tr");
        const cell = (text, cls) => { const td = document.createElement("td"); td.textContent = text; if (cls) td.className = cls; row.appendChild(td); return td; };
        cell("Q" + m.line);
        cell(`${m.bank_id}, ${SUBJ[m.subject] || m.subject}`);
        cell(m.block === "S" ? "Every form (shared)" : `Line C${m.block} only`, m.block === "S" ? "" : "held-own");
        cell(m.score.toFixed(2));
        const src = cell(m.source);
        const ex = document.createElement("span"); ex.className = "excerpt"; ex.textContent = m.excerpt; src.appendChild(ex);
        return row;
      }));
    }
    $("ev-note").textContent = `${r.matched} of ${r.questions_read} questions in the paper match a bank question (similarity ${r.rule.tau.toFixed(2)} or more).`;
  }

  // ---------- actions ----------
  async function loadSample(kind, btn) {
    document.querySelectorAll(".samples button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    const seed = 1 + Math.floor(Math.random() * 9999);
    $("status").textContent = "Building a simulated leak…";
    try {
      const res = await fetch(`/api/sample?kind=${encodeURIComponent(kind)}&seed=${seed}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not build the sample.");
      $("leak").value = data.text;
      truth = data.truth;
      const note = $("sample-note");
      note.hidden = false;
      note.textContent = `Simulated leak from ${SAMPLE_NAMES[kind]}, seed ${seed}: ${data.truth.real_questions} bank questions hidden among ${data.truth.decoys} real JEE questions that are not in the bank. The answer key appears after you run it.`;
      $("status").textContent = "";
    } catch (e) {
      $("status").textContent = e.message;
    }
  }

  async function decode() {
    const text = $("leak").value;
    if (!text.trim()) { $("status").textContent = "Paste a paper or pick a simulated leak first."; return; }
    const btn = $("decode");
    btn.disabled = true;
    $("status").textContent = "Reading the paper…";
    const t0 = performance.now();
    try {
      const res = await fetch("/api/decode", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || "The decoder could not read this text.");
      render(data);
      if (window.matchMedia("(max-width: 980px)").matches) $("verdict-line").scrollIntoView({ block: "start" });
      $("status").textContent = `Read ${data.questions_read} questions in ${((performance.now() - t0) / 1000).toFixed(1)} s.`;
    } catch (e) {
      $("status").textContent = e.message;
    } finally {
      btn.disabled = false;
    }
  }

  // ---------- photos: OCR in the browser (Tesseract.js, self-hosted) ----------
  let ocrWorker = null;
  async function getWorker() {
    if (ocrWorker) return ocrWorker;
    if (!window.Tesseract) {
      await new Promise((ok, fail) => {
        const sc = document.createElement("script");
        sc.src = "/vendor/tesseract/tesseract.min.js";
        sc.onload = ok;
        sc.onerror = () => fail(new Error("Could not load the OCR engine. Refresh and try again."));
        document.head.appendChild(sc);
      });
    }
    $("status").textContent = "Starting the OCR engine (first time only)…";
    ocrWorker = await window.Tesseract.createWorker("eng", 1, {
      workerPath: "/vendor/tesseract/worker.min.js",
      corePath: "/vendor/tesseract/core",
      langPath: "/vendor/tesseract/lang",
      gzip: false,
      workerBlobURL: false,
    });
    return ocrWorker;
  }

  async function readPhotos(sources, label) {
    const btns = document.querySelectorAll("#decode, #sample-photo, .samples button");
    btns.forEach((b) => (b.disabled = true));
    try {
      const w = await getWorker();
      const parts = [];
      for (let i = 0; i < sources.length; i++) {
        $("status").textContent = `Reading ${label} ${i + 1} of ${sources.length}…`;
        const { data } = await w.recognize(sources[i]);
        parts.push(data.text);
      }
      $("leak").value = parts.join("\n\n");
    } finally {
      btns.forEach((b) => (b.disabled = false));
    }
  }

  $("photo").addEventListener("change", async (e) => {
    const files = [...e.target.files];
    if (!files.length) return;
    truth = null;
    document.querySelectorAll(".samples button").forEach((b) => b.setAttribute("aria-pressed", "false"));
    $("sample-note").hidden = false;
    $("sample-note").textContent = `Your ${files.length === 1 ? "photo" : files.length + " photos"}: read on this device, never uploaded. Check the text, then the verdict.`;
    try {
      await readPhotos(files, "photo");
      await decode();
    } catch (err) {
      $("status").textContent = err.message || "Could not read that photo.";
    }
    e.target.value = "";
  });

  $("sample-photo").addEventListener("click", async () => {
    try {
      const meta = await (await fetch("/samples/sample-photo.json")).json();
      document.querySelectorAll(".samples button").forEach((b) => b.setAttribute("aria-pressed", "false"));
      truth = meta.truth;
      const note = $("sample-note");
      note.hidden = false;
      note.textContent = `Sample photo: ${meta.pages.length} pages in a handwriting-style font, formulas removed. ${meta.truth.real_questions} bank questions among ${meta.truth.decoys} real JEE questions that are not in the bank. The answer key appears after the verdict.`;
      await readPhotos(meta.pages.map((p) => "/samples/" + p), "page");
      await decode();
    } catch (err) {
      $("status").textContent = err.message || "Could not read the sample photo.";
    }
  });

  $("leak").addEventListener("input", () => {
    if (truth) { truth = null; $("sample-note").hidden = true; $("truth").hidden = true;
      document.querySelectorAll(".samples button").forEach((b) => b.setAttribute("aria-pressed", "false")); }
  });
  document.querySelectorAll(".samples button").forEach((b) => b.addEventListener("click", () => loadSample(b.dataset.kind, b)));
  $("decode").addEventListener("click", decode);

  fetch("/api/design").then((r) => r.json()).then((d) => {
    design = d;
    $("design-line").textContent =
      `Demo exam: every form has ${d.form_size} questions, ${d.shared} shared and ${d.unique_per_compartment} its own. ` +
      `${d.compartments} print lines at ${Object.keys(d.presses).length} presses. Bank: ${d.bank} real JEE Advanced questions.`;
    $("need").textContent = d.presence_t;
    if (d.commitment) $("commit").textContent =
      `Bank and custody map fingerprint (SHA-256), fixed before the exam and checked on every run: ${d.commitment.slice(0, 16)}…${d.commitment.slice(-8)}`;
    drawChain(null);
  }).catch(() => { $("design-line").textContent = "Could not reach the decoder. Refresh the page to try again."; });
})();
