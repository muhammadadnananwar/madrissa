/**
 * Small dependency-free SVG charts.
 * Palette validated (light surface): series-1 purple #6b45a8, series-2 gold #b07d00, series-3 teal #0e8f84 (all checks pass, --pairs all).
 * Gold sits just under 3:1 contrast, so every chart ships a legend + tooltip + "View as table".
 */
import { h } from "./ui";

const NS = "http://www.w3.org/2000/svg";
const s = (tag: string, attrs: Record<string, any> = {}) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
};
export const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)"];

function niceMax(v: number) {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  const n = v / p;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p;
}
const compact = (n: number) => (Math.abs(n) >= 1e6 ? `${+(n / 1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `${+(n / 1e3).toFixed(1)}k` : `${+n.toFixed(1)}`);

function frame(title: string, chartEl: HTMLElement, tableEl: HTMLElement, legend?: HTMLElement) {
  let showTable = false;
  const toggle = h("button", { class: "btn sm ghost" }, "View as table");
  const body = h("div", {}, chartEl);
  toggle.addEventListener("click", () => {
    showTable = !showTable;
    body.replaceChildren(showTable ? tableEl : chartEl);
    toggle.textContent = showTable ? "View as chart" : "View as table";
  });
  return h("div", {}, h("div", { class: "card-head" }, h("h3", {}, title), toggle), legend || null, body);
}

/** Single-series line chart (e.g. attendance % over days). Nulls are gaps. */
export function lineChart(title: string, points: { label: string; value: number | null }[], opts: { suffix?: string; max?: number } = {}) {
  const W = 640, H = 220, L = 40, R = 16, T = 12, B = 28;
  const vals = points.map((p) => p.value).filter((v): v is number => v != null);
  const max = opts.max ?? niceMax(Math.max(1, ...vals));
  const x = (i: number) => L + (points.length <= 1 ? (W - L - R) / 2 : (i * (W - L - R)) / (points.length - 1));
  const y = (v: number) => T + (H - T - B) * (1 - v / max);
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
  for (let i = 0; i <= 4; i++) {
    const v = (max * i) / 4;
    svg.append(s("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: "var(--grid)", "stroke-width": 1 }));
    const t = s("text", { x: L - 6, y: y(v) + 4, "text-anchor": "end", "font-size": 11, fill: "var(--muted)" });
    t.textContent = compact(v) + (opts.suffix || "");
    svg.append(t);
  }
  points.forEach((p, i) => {
    if (points.length > 12 && i % Math.ceil(points.length / 12)) return;
    const t = s("text", { x: x(i), y: H - 8, "text-anchor": "middle", "font-size": 11, fill: "var(--muted)" });
    t.textContent = p.label;
    svg.append(t);
  });
  let d = "";
  points.forEach((p, i) => { if (p.value != null) d += `${d && points[i - 1]?.value != null ? "L" : "M"}${x(i)},${y(p.value)}`; });
  svg.append(s("path", { d, fill: "none", stroke: SERIES[0], "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
  const marks = points.map((p, i) => {
    if (p.value == null) return null;
    const c = s("circle", { cx: x(i), cy: y(p.value), r: 4, fill: SERIES[0], stroke: "#fff", "stroke-width": 2 });
    svg.append(c);
    return c;
  });
  const last = [...points].reverse().find((p) => p.value != null);
  if (last) {
    const i = points.lastIndexOf(last);
    const t = s("text", { x: x(i), y: y(last.value!) - 10, "text-anchor": "middle", "font-size": 12, "font-weight": 600, fill: "var(--text)" });
    t.textContent = `${last.value}${opts.suffix || ""}`;
    svg.append(t);
  }
  const cross = s("line", { y1: T, y2: H - B, stroke: "var(--muted)", "stroke-width": 1, opacity: 0 });
  svg.append(cross);
  const wrap = h("div", { class: "chart" });
  const tip = h("div", { class: "tip hidden" });
  wrap.append(svg, tip);
  svg.addEventListener("pointermove", (e) => {
    const r = svg.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    let best = 0;
    points.forEach((_, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i; });
    const p = points[best];
    cross.setAttribute("x1", String(x(best)));
    cross.setAttribute("x2", String(x(best)));
    cross.setAttribute("opacity", "1");
    marks.forEach((m, i) => m?.setAttribute("r", i === best ? "6" : "4"));
    tip.textContent = `${p.label}: ${p.value == null ? "no data" : p.value + (opts.suffix || "")}`;
    tip.style.left = `${(x(best) / W) * 100}%`;
    tip.style.top = `${((p.value == null ? T : y(p.value)) / H) * 100}%`;
    tip.classList.remove("hidden");
  });
  svg.addEventListener("pointerleave", () => { tip.classList.add("hidden"); cross.setAttribute("opacity", "0"); marks.forEach((m) => m?.setAttribute("r", "4")); });
  const tbl = h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Period"), h("th", { class: "num" }, "Value"))),
    h("tbody", {}, points.map((p) => h("tr", {}, h("td", {}, p.label), h("td", { class: "num" }, p.value == null ? "—" : `${p.value}${opts.suffix || ""}`)))));
  return frame(title, wrap, h("div", { class: "table-wrap" }, tbl));
}

/** Grouped column chart, up to 3 series (fixed colour order). */
export function groupedColumns(title: string, categories: string[], series: { name: string; values: number[] }[], opts: { format?: (n: number) => string } = {}) {
  const fmt = opts.format || ((n: number) => n.toLocaleString());
  const W = 680, H = 240, L = 48, R = 12, T = 12, B = 28;
  const max = niceMax(Math.max(1, ...series.flatMap((x) => x.values.map(Number))));
  const y = (v: number) => T + (H - T - B) * (1 - v / max);
  const band = (W - L - R) / Math.max(1, categories.length);
  const gap = 2;
  const barW = Math.min(24, (band * 0.7 - gap * (series.length - 1)) / series.length);
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
  for (let i = 0; i <= 4; i++) {
    const v = (max * i) / 4;
    svg.append(s("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: "var(--grid)", "stroke-width": 1 }));
    const t = s("text", { x: L - 6, y: y(v) + 4, "text-anchor": "end", "font-size": 11, fill: "var(--muted)" });
    t.textContent = compact(v);
    svg.append(t);
  }
  const wrap = h("div", { class: "chart" });
  const tip = h("div", { class: "tip hidden" });
  categories.forEach((c, ci) => {
    const groupW = series.length * barW + (series.length - 1) * gap;
    const x0 = L + ci * band + (band - groupW) / 2;
    const t = s("text", { x: L + ci * band + band / 2, y: H - 8, "text-anchor": "middle", "font-size": 11, fill: "var(--muted)" });
    t.textContent = c;
    svg.append(t);
    series.forEach((sr, si) => {
      const v = Number(sr.values[ci] || 0);
      const bx = x0 + si * (barW + gap);
      const top = y(v), base = y(0), hgt = Math.max(0, base - top), r = Math.min(4, hgt, barW / 2);
      const d = hgt <= 0 ? "" : `M${bx},${base}V${top + r}Q${bx},${top} ${bx + r},${top}H${bx + barW - r}Q${bx + barW},${top} ${bx + barW},${top + r}V${base}Z`;
      const bar = s("path", { d, fill: SERIES[si] });
      // hit target larger than the mark
      const hit = s("rect", { x: bx - 1, y: T, width: barW + 2, height: H - T - B, fill: "transparent" });
      const show = () => {
        tip.textContent = `${c} · ${sr.name}: ${fmt(v)}`;
        tip.style.left = `${((bx + barW / 2) / W) * 100}%`;
        tip.style.top = `${(top / H) * 100}%`;
        tip.classList.remove("hidden");
        bar.setAttribute("opacity", "0.85");
      };
      hit.addEventListener("pointerenter", show);
      hit.addEventListener("pointerleave", () => { tip.classList.add("hidden"); bar.setAttribute("opacity", "1"); });
      svg.append(bar, hit);
    });
  });
  wrap.append(svg, tip);
  const legend = h("div", { class: "legend" }, series.map((sr, i) => h("span", {}, h("i", { style: { background: SERIES[i] } }), sr.name)));
  const tbl = h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Period"), series.map((sr) => h("th", { class: "num" }, sr.name)))),
    h("tbody", {}, categories.map((c, ci) => h("tr", {}, h("td", {}, c), series.map((sr) => h("td", { class: "num" }, fmt(Number(sr.values[ci] || 0))))))));
  return frame(title, wrap, h("div", { class: "table-wrap" }, tbl), legend);
}

/** Horizontal share bars (e.g. expenses by category) — single hue, sorted, labelled. */
export function barList(title: string, rows: { label: string; value: number }[], fmt = (n: number) => n.toLocaleString()) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return h("div", {}, h("div", { class: "card-head" }, h("h3", {}, title)),
    rows.length ? h("div", { class: "stack" }, rows.map((r) => h("div", {},
      h("div", { class: "row between small" }, h("span", {}, r.label), h("strong", {}, fmt(r.value))),
      h("div", { class: "progress", role: "img", "aria-label": `${r.label}: ${fmt(r.value)}` },
        h("span", { style: { width: `${(r.value / max) * 100}%`, background: SERIES[0] } }))))) : h("div", { class: "empty" }, "No data"));
}
