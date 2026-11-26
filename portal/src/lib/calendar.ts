/**
 * Interactive calendar (month / week / day / agenda) in the style of Google / Teams calendar.
 *
 * Reads GET /communication/calendar/?start&end → {items, can}. Events, holidays and website-calendar
 * entries can be created (click a day or time slot), opened, edited, deleted and dragged to a new date/time
 * right here; exams and live classes are shown read-only with a link to their own screens.
 */
import { del, get, patch, post } from "./api";
import { getMeta } from "./crud";
import { iconSvg } from "./icons";
import { $, busy, clear, confirmDialog, h, modal, toast, toastError } from "./ui";

type Type = "event" | "holiday" | "web" | "exam" | "live";
type Raw = { type: Type; id: number; title: string; start: string; end?: string | null; editable?: boolean; [k: string]: any };
type Item = { key: string; type: Type; title: string; start: Date; end: Date; allDay: boolean; editable: boolean; raw: Raw };
type View = "month" | "week" | "day" | "agenda";
type Can = { event: boolean; holiday: boolean; web: boolean };

const LAYERS: { type: Type; label: string }[] = [
  { type: "event", label: "Events" },
  { type: "holiday", label: "Holidays" },
  { type: "exam", label: "Exams" },
  { type: "live", label: "Live classes" },
  { type: "web", label: "Website calendar" },
];
const TYPE_LABEL: Record<Type, string> = { event: "Event", holiday: "Holiday", web: "Website calendar", exam: "Exam", live: "Live class" };
const ENDPOINT: Partial<Record<Type, string>> = { event: "events/", holiday: "holidays/", web: "web-calendar/" };
const META_KEY: Partial<Record<Type, string>> = { event: "events", holiday: "holidays", web: "web-calendar" };
const HOUR_PX = 48;
const DAY_MS = 86400000;

// ------------------------------------------------------------------ date helpers
const iso = (d: Date) => d.toLocaleDateString("en-CA");
const parse = (v: string) => new Date(String(v).length === 10 ? `${v}T00:00:00` : v);
const midnight = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const addDays = (d: Date, n: number) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const startOfWeek = (d: Date) => addDays(midnight(d), -((d.getDay() + 6) % 7)); // Monday
const dayDiff = (a: Date, b: Date) => Math.round((+midnight(b) - +midnight(a)) / DAY_MS);
const sameDay = (a: Date, b: Date) => iso(a) === iso(b);
const pad = (n: number) => String(n).padStart(2, "0");
const hm = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
const fmtTime = (d: Date) => d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
const fmtDay = (d: Date, o: Intl.DateTimeFormatOptions = { weekday: "short", day: "numeric", month: "short" }) => d.toLocaleDateString(undefined, o);
function hijri(d: Date, o: Intl.DateTimeFormatOptions) {
  try { return new Intl.DateTimeFormat("en-u-ca-islamic-umalqura", o).format(d).replace(/\s?AH$/, ""); } catch { return ""; }
}

function toItem(r: Raw): Item {
  const start = parse(r.start);
  let end = r.end ? parse(r.end) : null;
  let allDay = String(r.start).length === 10;
  if (r.type === "event") {
    // Events created as "all day" are stored 00:00 → 23:59.
    allDay = hm(start) === "00:00" && !!end && hm(end) === "23:59";
    if (!end) end = new Date(+start + 3600000);
  }
  if (!end) end = start;
  return { key: `${r.type}:${r.id}`, type: r.type, title: r.title, start, end, allDay, editable: !!r.editable && !!ENDPOINT[r.type], raw: r };
}
/** Shown in the all-day row: date-only items and timed items lasting a day or more. */
const isBanner = (it: Item) => it.allDay || +it.end - +it.start >= DAY_MS;
const covers = (it: Item, d: Date) => {
  const day0 = midnight(d), day1 = addDays(day0, 1);
  if (it.allDay) return midnight(it.start) <= day0 && midnight(it.end) >= day0;
  return it.start < day1 && (it.end > day0 || +it.end === +it.start && it.start >= day0);
};
const sortItems = (a: Item, b: Item) => Number(isBanner(b)) - Number(isBanner(a)) || +a.start - +b.start || a.title.localeCompare(b.title);

function whenText(it: Item) {
  if (it.allDay) {
    return sameDay(it.start, it.end) ? fmtDay(it.start, { weekday: "long", day: "numeric", month: "long", year: "numeric" })
      : `${fmtDay(it.start, { day: "numeric", month: "short" })} – ${fmtDay(it.end, { day: "numeric", month: "short", year: "numeric" })}`;
  }
  const s = `${fmtDay(it.start, { weekday: "long", day: "numeric", month: "long" })} · ${fmtTime(it.start)}`;
  if (!it.raw.end && it.type === "event") return s;
  return sameDay(it.start, it.end) ? `${s} – ${fmtTime(it.end)}` : `${s} – ${fmtDay(it.end, { day: "numeric", month: "short" })} ${fmtTime(it.end)}`;
}

// ------------------------------------------------------------------ state
const LS_VIEW = "cal.view", LS_LAYERS = "cal.layers";
const store = {
  get(k: string) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k: string, v: string) { try { localStorage.setItem(k, v); } catch { /* ignore */ } },
};
const qp = new URLSearchParams(location.search);
let view: View = (qp.get("view") as View) || (store.get(LS_VIEW) as View) || (matchMedia("(max-width: 700px)").matches ? "agenda" : "month");
if (!["month", "week", "day", "agenda"].includes(view)) view = "month";
let cursor = qp.get("date") ? parse(qp.get("date")!) : midnight(new Date());
if (isNaN(+cursor)) cursor = midnight(new Date());
let hidden = new Set<string>((() => { try { const v = JSON.parse(store.get(LS_LAYERS) || "[]"); return Array.isArray(v) ? v : []; } catch { return []; } })());
let can: Can = { event: false, holiday: false, web: false };
let items: Item[] = [];
let loadToken = 0;

function range(): [Date, Date] {
  if (view === "month") { const s = startOfWeek(new Date(cursor.getFullYear(), cursor.getMonth(), 1)); return [s, addDays(s, 41)]; }
  if (view === "week") { const s = startOfWeek(cursor); return [s, addDays(s, 6)]; }
  if (view === "day") return [midnight(cursor), midnight(cursor)];
  return [midnight(cursor), addDays(midnight(cursor), 29)];
}
function step(dir: number) {
  if (view === "month") cursor = new Date(cursor.getFullYear(), cursor.getMonth() + dir, 1);
  else cursor = addDays(cursor, dir * (view === "week" ? 7 : view === "day" ? 1 : 30));
  load();
}
function setView(v: View, date?: Date) {
  view = v;
  if (date) cursor = midnight(date);
  store.set(LS_VIEW, v);
  load();
}

// ------------------------------------------------------------------ loading + top-level render
let root: HTMLElement;
let titleEl: HTMLElement;
let subEl: HTMLElement;

async function load() {
  const [s, e] = range();
  const token = ++loadToken;
  history.replaceState(null, "", `?view=${view}&date=${iso(cursor)}`);
  renderToolbarState();
  try {
    const data = await get("communication/calendar/", { start: iso(s), end: iso(e) });
    if (token !== loadToken) return;
    can = data.can || can;
    items = (data.items || data).map(toItem);
  } catch (err) {
    if (token !== loadToken) return;
    toastError(err);
    items = [];
  }
  render();
}

function visible() { return items.filter((i) => !hidden.has(i.type)).sort(sortItems); }

function renderToolbarState() {
  const [s, e] = range();
  let t: string;
  if (view === "month") t = cursor.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  else if (view === "day") t = fmtDay(cursor, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  else t = s.getMonth() === e.getMonth() ? `${fmtDay(s, { day: "numeric" })} – ${fmtDay(e, { day: "numeric", month: "long", year: "numeric" })}`
    : `${fmtDay(s, { day: "numeric", month: "short" })} – ${fmtDay(e, { day: "numeric", month: "short", year: "numeric" })}`;
  titleEl.textContent = t;
  const h1 = hijri(s, { month: "long", year: "numeric" }), h2 = hijri(view === "month" ? addDays(s, 20) : e, { month: "long", year: "numeric" });
  subEl.textContent = h1 ? (h1 === h2 ? `${h1} AH` : `${h1} – ${h2} AH`) : "";
  document.querySelectorAll<HTMLButtonElement>("[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === view)));
}

function renderLayers() {
  const box = $("#cal-layers");
  clear(box, LAYERS.filter((l) => l.type !== "web" || can.web).map((l) => h("button", {
    class: `gc-layer ${l.type}`, type: "button", "aria-pressed": String(!hidden.has(l.type)), title: `Show or hide ${l.label.toLowerCase()}`,
    onclick: () => { hidden.has(l.type) ? hidden.delete(l.type) : hidden.add(l.type); store.set(LS_LAYERS, JSON.stringify([...hidden])); render(); },
  }, h("i", {}), l.label)));
  $("#cal-create").classList.toggle("hidden", !(can.event || can.holiday || can.web));
}

function render() {
  renderLayers();
  renderToolbarState();
  if (view === "month") renderMonth();
  else if (view === "agenda") renderAgenda();
  else renderTimeGrid(view === "week" ? 7 : 1);
}

// ------------------------------------------------------------------ chips + drag/drop
let dragging: { it: Item; grabMin: number } | null = null;

function chip(it: Item, opts: { day?: Date; compact?: boolean } = {}) {
  const banner = isBanner(it);
  const cont = opts.day && banner && !sameDay(it.start, opts.day) && opts.day.getDay() !== 1;
  const label = banner ? it.title : `${fmtTime(it.start)} ${it.title}`;
  const el = h("button", {
    type: "button", class: `gc-chip ${it.type} ${banner ? "bar" : "dot"} ${cont ? "cont" : ""}`, title: `${it.title} — ${whenText(it)}`,
    draggable: it.editable ? "true" : undefined,
    onclick: (e: Event) => { e.stopPropagation(); openDetails(it); },
  }, banner ? null : h("i", {}), h("span", {}, cont ? `↳ ${it.title}` : label));
  if (it.editable) {
    el.addEventListener("dragstart", (e: DragEvent) => {
      dragging = { it, grabMin: 0 };
      e.dataTransfer?.setData("text/plain", it.key);
      if (e.dataTransfer) e.dataTransfer.effectAllowed = "move";
      el.classList.add("dragging");
    });
    el.addEventListener("dragend", () => { el.classList.remove("dragging"); dragging = null; root.querySelectorAll(".drop").forEach((x) => x.classList.remove("drop")); });
  }
  return el;
}

function dropZone(el: HTMLElement, onDrop: (e: DragEvent) => void) {
  el.addEventListener("dragover", (e) => { if (dragging) { e.preventDefault(); el.classList.add("drop"); } });
  el.addEventListener("dragleave", () => el.classList.remove("drop"));
  el.addEventListener("drop", (e) => { e.preventDefault(); el.classList.remove("drop"); if (dragging) onDrop(e); });
}

/** Move an item so it starts on `day` (and optionally at `minutes` after midnight), keeping its length. */
async function moveItem(it: Item, day: Date, minutes?: number) {
  const r = it.raw;
  let body: Record<string, any>;
  if (it.type === "event") {
    const ns = new Date(midnight(day));
    if (minutes === undefined) ns.setHours(it.start.getHours(), it.start.getMinutes());
    else ns.setMinutes(minutes);
    if (+ns === +it.start) return;
    const dur = +it.end - +it.start;
    body = { start: ns.toISOString(), end: r.end ? new Date(+ns + dur).toISOString() : null };
  } else {
    const d = dayDiff(it.start, day);
    if (!d) return;
    body = { start_date: iso(addDays(it.start, d)) };
    if (r.end) body.end_date = iso(addDays(it.end, d));
  }
  try {
    await patch(`${ENDPOINT[it.type]}${r.id}/`, body);
    toast(`Moved “${it.title}”`);
  } catch (e) { toastError(e); }
  load();
}

// ------------------------------------------------------------------ month view
function renderMonth() {
  const [s] = range();
  const now = new Date();
  const vis = visible();
  const heads = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => h("div", { class: "gc-hd" }, d));
  const cells: HTMLElement[] = [];
  for (let i = 0; i < 42; i++) {
    const d = addDays(s, i);
    const its = vis.filter((it) => covers(it, d));
    const max = 3;
    const hd = hijri(d, { day: "numeric" });
    const cell = h("div", {
      class: `gc-cell ${d.getMonth() !== cursor.getMonth() ? "out" : ""} ${sameDay(d, now) ? "today" : ""}`,
      onclick: () => quickCreate(d),
    },
      h("div", { class: "gc-date" },
        h("button", { type: "button", class: "gc-num", title: "Open day", onclick: (e: Event) => { e.stopPropagation(); setView("day", d); } }, d.getDate()),
        hd ? h("span", { class: "gc-hijri", title: hijri(d, { day: "numeric", month: "long", year: "numeric" }) }, hd) : null),
      its.slice(0, its.length > max + 1 ? max : max + 1).map((it) => chip(it, { day: d })),
      its.length > max + 1 ? h("button", { type: "button", class: "gc-more", onclick: (e: Event) => { e.stopPropagation(); dayList(d, its); } }, `+${its.length - max} more`) : null);
    if (can.event || can.holiday || can.web) cell.title = "Click to add";
    dropZone(cell, () => moveItem(dragging!.it, d));
    cells.push(cell);
  }
  clear(root, h("div", { class: "gc-month" }, heads, cells));
}

function dayList(d: Date, its: Item[]) {
  const m = modal(fmtDay(d, { weekday: "long", day: "numeric", month: "long", year: "numeric" }),
    h("div", { class: "gc-daylist" }, its.map((it) => { const c = chip(it); c.addEventListener("click", () => m.close()); return c; })), {
      actions: [h("button", { class: "btn", onclick: () => { m.close(); setView("day", d); } }, "Open day"),
        ...(can.event || can.holiday || can.web ? [h("button", { class: "btn primary", onclick: () => { m.close(); quickCreate(d); } }, "Add")] : [])],
    });
}

// ------------------------------------------------------------------ week / day time grid
function layoutDay(its: Item[], day: Date) {
  const day0 = +midnight(day), day1 = day0 + DAY_MS;
  const segs = its.map((it) => {
    const s = Math.max(+it.start, day0), e = Math.min(Math.max(+it.end, +it.start + 30 * 60000), day1);
    return { it, top: (s - day0) / 60000, bottom: (e - day0) / 60000, lane: 0, lanes: 1 };
  }).sort((a, b) => a.top - b.top || b.bottom - a.bottom);
  // Greedy lanes within clusters of overlapping events.
  let cluster: typeof segs = [], clusterEnd = -1;
  const flush = () => { const n = Math.max(1, ...cluster.map((c) => c.lane + 1)); cluster.forEach((c) => (c.lanes = n)); cluster = []; };
  for (const sg of segs) {
    if (sg.top >= clusterEnd) { flush(); clusterEnd = -1; }
    const used = new Set(cluster.filter((c) => c.bottom > sg.top).map((c) => c.lane));
    while (used.has(sg.lane)) sg.lane++;
    cluster.push(sg);
    clusterEnd = Math.max(clusterEnd, sg.bottom);
  }
  flush();
  return segs;
}

function renderTimeGrid(days: number) {
  const [s] = range();
  const now = new Date();
  const vis = visible();
  const dates = Array.from({ length: days }, (_, i) => addDays(s, i));
  const cols = `56px repeat(${days}, minmax(0, 1fr))`;
  const editableAny = can.event || can.holiday || can.web;

  const head = h("div", { class: "gc-tg-head", style: { gridTemplateColumns: cols } }, h("div", {}),
    dates.map((d) => h("button", { type: "button", class: `gc-tg-day ${sameDay(d, now) ? "today" : ""}`, onclick: () => days > 1 && setView("day", d) },
      h("span", {}, fmtDay(d, { weekday: "short" })), h("strong", {}, d.getDate()), h("span", { class: "gc-hijri" }, hijri(d, { day: "numeric", month: "short" })))));

  const allday = h("div", { class: "gc-tg-allday", style: { gridTemplateColumns: cols } }, h("div", { class: "gc-tg-label" }, "All day"),
    dates.map((d) => {
      const cell = h("div", { class: "gc-tg-adcell", onclick: () => quickCreate(d, undefined, true) },
        vis.filter((it) => isBanner(it) && covers(it, d)).map((it) => chip(it, { day: d })));
      dropZone(cell, () => moveItem(dragging!.it, d));
      return cell;
    }));

  const hours = h("div", { class: "gc-tg-hours" }, Array.from({ length: 24 }, (_, i) =>
    h("div", { class: "gc-tg-hour" }, i ? new Date(2000, 0, 1, i).toLocaleTimeString(undefined, { hour: "numeric" }) : "")));
  const columns = dates.map((d) => {
    const col = h("div", { class: `gc-tg-col ${sameDay(d, now) ? "today" : ""}`, title: editableAny ? "Click to add" : "" });
    const minuteAt = (e: MouseEvent, snap: number) => {
      const y = e.clientY - col.getBoundingClientRect().top;
      return Math.max(0, Math.min(24 * 60 - snap, Math.round((y / HOUR_PX) * 60 / snap) * snap));
    };
    col.addEventListener("click", (e) => { if (e.target === col) quickCreate(d, Math.floor(minuteAt(e, 30) / 30) * 30); });
    dropZone(col, (e) => {
      const it = dragging!.it;
      const m = Math.max(0, minuteAt(e, 15) - dragging!.grabMin);
      if (isBanner(it)) moveItem(it, d);
      else moveItem(it, d, Math.round(m / 15) * 15);
    });
    for (const sg of layoutDay(vis.filter((it) => !isBanner(it) && covers(it, d)), d)) {
      const it = sg.it;
      const c = chip(it);
      c.classList.add("block");
      c.replaceChildren(h("strong", {}, it.title), h("span", {}, it.raw.end || it.type !== "event" ? `${fmtTime(it.start)} – ${fmtTime(it.end)}` : fmtTime(it.start)),
        it.raw.location ? h("span", {}, it.raw.location) : null);
      Object.assign(c.style, {
        top: `${(sg.top / 60) * HOUR_PX}px`, height: `${Math.max(20, ((sg.bottom - sg.top) / 60) * HOUR_PX - 2)}px`,
        left: `calc(${(sg.lane / sg.lanes) * 100}% + 2px)`, width: `calc(${100 / sg.lanes}% - 4px)`,
      });
      c.addEventListener("dragstart", (e: DragEvent) => {
        if (dragging) dragging.grabMin = Math.round(((e.clientY - c.getBoundingClientRect().top) / HOUR_PX) * 60);
      });
      col.appendChild(c);
    }
    if (sameDay(d, now)) col.appendChild(h("div", { class: "gc-now", style: { top: `${((now.getHours() * 60 + now.getMinutes()) / 60) * HOUR_PX}px` } }));
    return col;
  });
  const scroller = h("div", { class: "gc-tg-scroll" }, h("div", { class: "gc-tg-body", style: { gridTemplateColumns: cols } }, hours, columns));
  clear(root, h("div", { class: "gc-tg" }, head, allday, scroller));
  const firstTimed = vis.filter((it) => !isBanner(it) && dates.some((d) => covers(it, d))).map((it) => it.start.getHours()).sort((a, b) => a - b)[0];
  scroller.scrollTop = Math.max(0, Math.min(firstTimed ?? 8, 8) - 0.5) * HOUR_PX;
}

// ------------------------------------------------------------------ agenda
function renderAgenda() {
  const [s, e] = range();
  const vis = visible();
  const groups: HTMLElement[] = [];
  for (let d = new Date(s); d <= e; d = addDays(d, 1)) {
    const its = vis.filter((it) => covers(it, d));
    if (!its.length) continue;
    groups.push(h("div", { class: `gc-ag-day ${sameDay(d, new Date()) ? "today" : ""}` },
      h("div", { class: "gc-ag-date" }, h("strong", {}, d.getDate()), h("span", {}, fmtDay(d, { weekday: "short", month: "short" })),
        h("span", { class: "gc-hijri" }, hijri(d, { day: "numeric", month: "short" }))),
      h("div", { class: "gc-ag-list" }, its.map((it) => h("button", { type: "button", class: `gc-ag-item ${it.type}`, onclick: () => openDetails(it) },
        h("i", {}), h("span", { class: "gc-ag-time" }, isBanner(it) ? "All day" : fmtTime(it.start)),
        h("span", { class: "gc-ag-title" }, it.title, it.raw.kind ? h("span", { class: "muted" }, ` · ${it.raw.kind}`) : null))))));
  }
  clear(root, groups.length ? h("div", { class: "gc-agenda" }, groups)
    : h("div", { class: "empty" }, "Nothing scheduled in the next 30 days.", (can.event || can.holiday || can.web) ? h("div", {}, h("button", { class: "btn primary", style: { marginTop: ".75rem" }, onclick: () => quickCreate(s) }, "Add something")) : null));
}

// ------------------------------------------------------------------ details popup
function openDetails(it: Item) {
  const r = it.raw;
  const rows: [string, any][] = [
    ["When", whenText(it)],
    ["Type", `${TYPE_LABEL[it.type]}${r.kind ? ` · ${r.kind}` : ""}`],
  ];
  if (r.location) rows.push(["Where", r.location]);
  if (r.term) rows.push(["Term", r.term]);
  if (it.type === "event") {
    rows.push(["Audience", r.audience?.length ? r.audience.map((a: string) => a.replace(/_/g, " ")).join(", ") : "Everyone"]);
    rows.push(["Public website", r.is_public ? "Shown" : "Not shown"]);
  }
  if (it.type === "web") rows.push(["Status", r.is_published ? "Published on website" : "Draft (not on website)"]);
  const actions: HTMLElement[] = [];
  if (it.type === "exam") actions.push(h("a", { class: "btn", href: "/m/exam-papers" }, "Open exam papers"));
  if (it.type === "live") actions.push(h("a", { class: "btn primary", href: `/live/room?id=${r.id}` }, "Open class"));
  let m: ReturnType<typeof modal>;
  if (it.editable) {
    actions.push(h("button", { class: "btn danger", html: "Delete", onclick: async (e: Event) => {
      if (!(await confirmDialog(`Delete “${it.title}”? This cannot be undone.`, "Delete", true))) return;
      const ok = await busy(e.currentTarget as HTMLButtonElement, () => del(`${ENDPOINT[it.type]}${r.id}/`), "Deleted");
      if (ok !== undefined) { m.close(); load(); }
    } }));
    actions.push(h("button", { class: "btn primary", html: `${iconSvg("edit")} Edit`, onclick: () => { m.close(); openEditor(it.type, { item: it }); } }));
  }
  m = modal(it.title, h("div", {},
    h("dl", { class: "kv" }, rows.flatMap(([k, v]) => [h("dt", {}, k), h("dd", {}, v)])),
    r.description ? h("p", { class: "gc-desc" }, r.description) : null,
    it.editable ? h("p", { class: "small muted" }, "Tip: drag it on the calendar to move it to another day or time.") : null), { actions });
}

// ------------------------------------------------------------------ create / edit
function quickCreate(day: Date, minutes?: number, allDay = false) {
  const type: Type | null = can.event ? "event" : can.holiday ? "holiday" : can.web ? "web" : null;
  if (!type) return;
  // Like Google Calendar: clicking a day (month view / all-day row) starts an all-day item, a time slot a timed one.
  openEditor(type, { day, minutes, allDay: allDay || minutes === undefined });
}

const choiceCache = new Map<string, Promise<{ value: any; label: string }[]>>();
function choices(type: Type, field: string) {
  const k = `${type}.${field}`;
  if (!choiceCache.has(k)) choiceCache.set(k, getMeta(META_KEY[type]!).then((m) => m.fields.find((f) => f.name === field)?.choices || []).catch(() => []));
  return choiceCache.get(k)!;
}
let rolesP: Promise<{ value: string; label: string }[]> | null = null;
const roles = () => (rolesP ??= get("meta/").then((m) => m.roles || []).catch(() => []));

function field(label: string, input: HTMLElement, opts: { full?: boolean; help?: string; name?: string } = {}) {
  return h("div", { class: `field ${opts.full ? "full" : ""}`, dataset: { name: opts.name || "" } }, h("label", {}, label), input, opts.help ? h("div", { class: "help" }, opts.help) : null);
}
function selectFrom(p: Promise<{ value: any; label: string }[]>, value: any) {
  const s = h("select", {});
  p.then((cs) => cs.forEach((c) => s.appendChild(h("option", { value: String(c.value), selected: String(c.value) === String(value ?? "") }, c.label))));
  return s;
}

type EditorOpts = { item?: Item; day?: Date; minutes?: number; allDay?: boolean };

function openEditor(type: Type, o: EditorOpts) {
  const it = o.item;
  const editing = !!it;
  const types = (["event", "holiday", "web"] as Type[]).filter((t) => can[t as keyof Can]);
  const day = o.day || (it ? it.start : midnight(new Date()));
  const body = h("div", {});
  let save: () => Promise<any> = async () => {};
  let firstInput: HTMLInputElement | null = null;

  const switcher = editing ? null : h("div", { class: "gc-seg", role: "tablist" }, types.map((t) => h("button", {
    type: "button", role: "tab", class: t, "aria-selected": String(t === type),
    onclick: () => { const title = firstInput?.value; type = t; draw(); if (firstInput && title) firstInput.value = title; switcher!.querySelectorAll("button").forEach((b, i) => b.setAttribute("aria-selected", String(types[i] === t))); },
  }, TYPE_LABEL[t] === "Website calendar" ? "Website" : TYPE_LABEL[t])));

  function draw() {
    more.href = `/m/${META_KEY[type]}`;
    const r: any = it?.raw || {};
    const title = h("input", { type: "text", value: r.title || "", placeholder: "Add title", class: "gc-title-input", required: true }) as HTMLInputElement;
    firstInput = title;
    const desc = h("textarea", { rows: 3, placeholder: "Add description" }, r.description || "") as HTMLTextAreaElement;
    const grid = h("div", { class: "form-grid" });

    if (type === "event") {
      const start = it ? it.start : (() => { const d = new Date(day); d.setHours(0, 0, 0, 0); d.setMinutes(o.minutes ?? 9 * 60); return d; })();
      const end = it ? (it.raw.end ? it.end : new Date(+start + 3600000)) : new Date(+start + 3600000);
      const allDay = h("input", { type: "checkbox", checked: it ? it.allDay : !!o.allDay }) as HTMLInputElement;
      const sd = h("input", { type: "date", value: iso(start), required: true }) as HTMLInputElement;
      const st = h("input", { type: "time", value: hm(start), step: 300 }) as HTMLInputElement;
      const ed = h("input", { type: "date", value: iso(end) }) as HTMLInputElement;
      const et = h("input", { type: "time", value: hm(end), step: 300 }) as HTMLInputElement;
      const syncAllDay = () => { st.classList.toggle("hidden", allDay.checked); et.classList.toggle("hidden", allDay.checked); };
      allDay.addEventListener("change", syncAllDay);
      sd.addEventListener("change", () => { if (ed.value < sd.value) ed.value = sd.value; });
      st.addEventListener("change", () => { if (ed.value === sd.value && et.value <= st.value) { const [hh, mm] = st.value.split(":").map(Number); et.value = `${pad(Math.min(23, hh + 1))}:${pad(mm)}`; } });
      syncAllDay();
      const kind = selectFrom(choices("event", "kind"), r.kind_value || "other");
      const loc = h("input", { type: "text", value: r.location || "", placeholder: "e.g. Main hall" }) as HTMLInputElement;
      const pub = h("input", { type: "checkbox", checked: !!r.is_public }) as HTMLInputElement;
      const chosen = new Set<string>(r.audience || []);
      const aud = h("div", { class: "gc-aud" });
      roles().then((rs) => rs.forEach((ro) => aud.appendChild(h("label", {},
        h("input", { type: "checkbox", checked: chosen.has(ro.value), onchange: (e: any) => (e.target.checked ? chosen.add(ro.value) : chosen.delete(ro.value)) }),
        " ", ro.label.split(" (")[0]))));
      grid.append(
        h("div", { class: "field full gc-when" }, h("label", {}, "When"),
          h("div", { class: "gc-when-row" }, sd, st, h("span", { class: "muted" }, "to"), ed, et),
          h("label", { class: "gc-inline" }, allDay, " All day")),
        field("Kind", kind), field("Location", loc),
        field("Description", desc, { full: true }),
        h("details", { class: "field full gc-aud-wrap", open: chosen.size ? true : undefined }, h("summary", {}, "Who can see it", h("span", { class: "muted small" }, chosen.size ? ` · ${chosen.size} role(s)` : " · Everyone")),
          aud, h("div", { class: "help" }, "Leave all unchecked to show it to everyone.")),
        h("div", { class: "field full check" }, h("label", {}, pub, "Also show on the public website")));
      save = () => {
        let s: Date, e: Date;
        if (!sd.value) throw new Error("Pick a start date.");
        if (allDay.checked) { s = parse(sd.value); e = parse(ed.value || sd.value); e.setHours(23, 59); }
        else { s = new Date(`${sd.value}T${st.value || "09:00"}`); e = new Date(`${ed.value || sd.value}T${et.value || st.value || "10:00"}`); }
        if (e < s) throw new Error("The end must be after the start.");
        const data = { title: title.value.trim(), kind: kind.value || "other", start: s.toISOString(), end: e.toISOString(), location: loc.value.trim(),
          description: desc.value, audience: [...chosen], is_public: pub.checked };
        return editing ? patch(`events/${r.id}/`, data) : post("events/", data);
      };
    } else {
      const isWeb = type === "web";
      const sd = h("input", { type: "date", value: it ? iso(it.start) : iso(day), required: true }) as HTMLInputElement;
      const ed = h("input", { type: "date", value: it ? (r.end ? iso(it.end) : "") : isWeb ? "" : iso(day) }) as HTMLInputElement;
      sd.addEventListener("change", () => { if (ed.value && ed.value < sd.value) ed.value = sd.value; });
      const kindField = isWeb ? "category" : "kind";
      const kind = selectFrom(choices(type, kindField), r.kind_value || (isWeb ? "holiday" : "other"));
      grid.append(
        h("div", { class: "field full gc-when" }, h("label", {}, "Dates"),
          h("div", { class: "gc-when-row" }, sd, h("span", { class: "muted" }, "to"), ed),
          h("div", { class: "help" }, isWeb ? "Leave the end empty for a single day." : "Use the same date twice for a one-day holiday.")),
        field(isWeb ? "Category" : "Kind", kind));
      const term = h("input", { type: "text", value: r.term || "", placeholder: "e.g. Spring 2026" }) as HTMLInputElement;
      const published = h("input", { type: "checkbox", checked: it ? !!r.is_published : true }) as HTMLInputElement;
      const alsoWeb = h("input", { type: "checkbox", checked: true }) as HTMLInputElement;
      if (isWeb) grid.append(field("Term", term));
      grid.append(field("Description", desc, { full: true }));
      if (isWeb) grid.append(h("div", { class: "field full check" }, h("label", {}, published, "Published on the website")));
      if (!isWeb) grid.append(h("div", { class: "help full", style: { gridColumn: "1 / -1", marginBottom: ".6rem" } }, "Holidays are days off: attendance and finance don't count them as working days."));
      if (!isWeb && !editing && can.web) grid.append(h("div", { class: "field full check" }, h("label", {}, alsoWeb, "Also add to the public website calendar")));
      save = async () => {
        if (!sd.value) throw new Error("Pick a start date.");
        const base = { title: title.value.trim(), start_date: sd.value, description: desc.value };
        if (isWeb) {
          const data = { ...base, end_date: ed.value || null, category: kind.value || "holiday", term: term.value.trim(), is_published: published.checked };
          return editing ? patch(`web-calendar/${r.id}/`, data) : post("web-calendar/", data);
        }
        const data = { ...base, end_date: ed.value || sd.value, kind: kind.value || "other" };
        if (editing) return patch(`holidays/${r.id}/`, data);
        const res = await post("holidays/", data);
        if (can.web && alsoWeb.checked) {
          try { await post("web-calendar/", { ...base, end_date: data.end_date === sd.value ? null : data.end_date, category: "holiday", is_published: true }); }
          catch (e) { toastError(e); }
        }
        return res;
      };
    }
    clear(body, switcher, h("form", { onsubmit: (e: Event) => { e.preventDefault(); saveBtn.click(); } }, title, grid, h("button", { type: "submit", class: "hidden" })));
    setTimeout(() => title.focus(), 0);
  }

  const saveBtn = h("button", { class: "btn primary", onclick: async () => {
    if (!firstInput?.value.trim()) { firstInput?.focus(); return toast("Add a title first.", "error"); }
    const r = await busy(saveBtn, async () => save(), editing ? "Saved" : `${TYPE_LABEL[type]} added`);
    if (r !== undefined) { m.close(); load(); }
  } }, "Save") as HTMLButtonElement;
  const more = h("a", { class: "btn ghost", title: "Images, website page content and other advanced fields" }, "More options");
  const m = modal(editing ? `Edit ${TYPE_LABEL[type].toLowerCase()}` : "Add to calendar", body,
    { actions: [more, h("button", { class: "btn", onclick: () => m.close() }, "Cancel"), saveBtn] });
  m.el.classList.add("gc-editor");
  draw();
}

// ------------------------------------------------------------------ boot
export function mountCalendar() {
  root = $("#cal");
  titleEl = $("#title");
  subEl = $("#subtitle");
  $("#prev").onclick = () => step(-1);
  $("#next").onclick = () => step(1);
  $("#today").onclick = () => { cursor = midnight(new Date()); load(); };
  document.querySelectorAll<HTMLButtonElement>("[data-view]").forEach((b) => (b.onclick = () => setView(b.dataset.view as View)));
  $("#cal-create").onclick = () => quickCreate(view === "month" && cursor.getMonth() !== new Date().getMonth() ? cursor : new Date());
  document.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement;
    if (e.ctrlKey || e.metaKey || e.altKey || /INPUT|TEXTAREA|SELECT/.test(t.tagName) || t.isContentEditable || document.querySelector(".overlay")) return;
    const k = e.key.toLowerCase();
    const map: Record<string, () => void> = {
      t: () => { cursor = midnight(new Date()); load(); }, j: () => step(1), n: () => step(1), k: () => step(-1), p: () => step(-1),
      m: () => setView("month"), w: () => setView("week"), d: () => setView("day"), a: () => setView("agenda"),
      c: () => $("#cal-create").click(),
    };
    if (map[k]) { e.preventDefault(); map[k](); }
  });
  load();
}
