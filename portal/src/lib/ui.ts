/** Tiny DOM + UI helpers (no framework). */
import { ApiError } from "./api";
import { iconSvg } from "./icons";

type Child = Node | string | number | null | undefined | false | Child[];
type Attrs = Record<string, any>;

/** Create an element: h("div", {class: "x", onclick: fn}, "text", child) */
export function h<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Attrs = {}, ...children: Child[]): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
    else if (k === "dataset") Object.assign(el.dataset, v);
    else if (k in el && typeof v !== "string") (el as any)[k] = v;
    else el.setAttribute(k, v === true ? "" : String(v));
  }
  append(el, children);
  return el;
}
function append(el: Node, children: Child[]) {
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    if (Array.isArray(c)) append(el, c);
    else el.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}
export const $ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => root.querySelector(sel) as T;
export const $$ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => Array.from(root.querySelectorAll(sel)) as T[];
export function clear(el: Element, ...children: Child[]) {
  el.replaceChildren();
  append(el, children);
  return el;
}
export const esc = (s: any) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
export const param = (k: string) => new URLSearchParams(location.search).get(k);

// ---------------------------------------------------------------- formatting
export function fmtDate(v: any) {
  if (!v) return "—";
  const d = new Date(String(v).length === 10 ? `${v}T00:00:00` : v);
  return isNaN(+d) ? String(v) : d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
}
export function fmtDateTime(v: any) {
  if (!v) return "—";
  const d = new Date(v);
  return isNaN(+d) ? String(v) : d.toLocaleString(undefined, { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
export function fmtTime(v: any) {
  if (!v) return "—";
  if (/^\d\d:\d\d/.test(String(v))) return String(v).slice(0, 5);
  return new Date(v).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}
export function fmtMoney(v: any, currency = "PKR") {
  const n = Number(v || 0);
  return `${currency} ${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
export const fmtNum = (v: any) => Number(v || 0).toLocaleString();
export const today = () => new Date().toLocaleDateString("en-CA");
export const thisMonth = () => today().slice(0, 7);
export const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join("").toUpperCase();

const TONES: Record<string, string> = {
  active: "good", present: "good", paid: "good", verified: "good", approved: "good", graded: "good", completed: "good",
  answered: "good", returned: "good", received: "good", passed: "good", pass: "good", enrolled: "good", accepted: "good",
  live: "info", scheduled: "info", submitted: "info", in_progress: "info", issued: "info", out: "info", leave: "info",
  pending: "warn", unpaid: "warn", partial: "warn", late: "warn", requested: "warn", draft: "warn", under_review: "warn",
  test_scheduled: "warn", waitlisted: "warn", new: "warn", open: "warn", pledged: "warn", half_day: "warn",
  absent: "bad", rejected: "bad", cancelled: "bad", overdue: "bad", failed: "bad", fail: "bad", lost: "bad",
  suspended: "bad", left: "bad", terminated: "bad", urgent: "bad", important: "warn",
};
export function badge(value: any, label?: string) {
  const key = String(value ?? "").toLowerCase();
  return h("span", { class: `badge ${TONES[key] || ""}` }, label ?? String(value ?? "—").replace(/_/g, " "));
}

// ------------------------------------------------------------------- toasts
export function toast(msg: string, type: "ok" | "error" = "ok") {
  let box = $(".toasts");
  if (!box) document.body.appendChild((box = h("div", { class: "toasts", role: "status" })));
  const t = h("div", { class: `toast ${type === "error" ? "error" : ""}` }, msg);
  box.appendChild(t);
  setTimeout(() => t.remove(), type === "error" ? 7000 : 3500);
}
export function toastError(e: any) {
  toast(e instanceof ApiError ? e.message : e?.message || String(e), "error");
}

// ------------------------------------------------------------------- modals
export type ModalHandle = { el: HTMLElement; body: HTMLElement; foot: HTMLElement; close: () => void };
export function modal(title: string, body: Child, opts: { wide?: boolean; actions?: HTMLElement[]; onClose?: () => void } = {}): ModalHandle {
  const bodyEl = h("div", { class: "modal-body" }, body);
  const foot = h("div", { class: "modal-foot" }, opts.actions || []);
  const close = () => {
    overlay.remove();
    document.removeEventListener("keydown", onKey);
    opts.onClose?.();
  };
  const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
  const box = h("div", { class: `modal ${opts.wide ? "wide" : ""}`, role: "dialog", "aria-modal": "true", "aria-label": title },
    h("div", { class: "modal-head" }, h("h3", {}, title), h("button", { class: "btn ghost sm", onclick: close, "aria-label": "Close" }, "✕")),
    bodyEl, opts.actions?.length ? foot : null);
  const overlay = h("div", { class: "overlay", onclick: (e: Event) => e.target === overlay && close() }, box);
  document.addEventListener("keydown", onKey);
  document.body.appendChild(overlay);
  return { el: box, body: bodyEl, foot, close };
}
export function confirmDialog(message: string, okLabel = "Confirm", danger = false): Promise<boolean> {
  return new Promise((resolve) => {
    let done = false;
    const finish = (v: boolean) => { if (!done) { done = true; m.close(); resolve(v); } };
    const m = modal("Please confirm", h("p", {}, message), {
      actions: [h("button", { class: "btn", onclick: () => finish(false) }, "Cancel"),
        h("button", { class: `btn ${danger ? "danger" : "primary"}`, onclick: () => finish(true) }, okLabel)],
      onClose: () => finish(false),
    });
  });
}
/** Show credentials generated by the server (new student/staff/parent logins). */
export function showCredentials(title: string, rows: [string, string][]) {
  modal(title, h("div", {},
    h("div", { class: "alert warn" }, "Copy these now — the password will not be shown again. The user must change it at first login."),
    h("dl", { class: "kv" }, rows.flatMap(([k, v]) => [h("dt", {}, k), h("dd", {}, h("code", {}, v))]))));
}

export const spinner = () => h("div", { class: "spinner", "aria-label": "Loading" });
export const empty = (msg = "Nothing to show yet.") => h("div", { class: "empty" }, msg);

/** Run an async action on a button with disabled state + toast. */
export async function busy<T>(btn: HTMLButtonElement | null, fn: () => Promise<T>, okMsg?: string | ((r: T) => string)): Promise<T | undefined> {
  if (btn) btn.disabled = true;
  try {
    const r = await fn();
    const msg = typeof okMsg === "function" ? okMsg(r) : okMsg ?? (r as any)?.detail;
    if (msg) toast(msg);
    return r;
  } catch (e) {
    toastError(e);
  } finally {
    if (btn) btn.disabled = false;
  }
}

/** Simple data table. */
export type Col<T> = { label: string; render: (row: T, i: number) => Child; cls?: string };
export function table<T>(cols: Col<T>[], rows: T[], opts: { onRow?: (row: T) => void; emptyText?: string } = {}) {
  if (!rows.length) return empty(opts.emptyText);
  return h("div", { class: "table-wrap" }, h("table", {},
    h("thead", {}, h("tr", {}, cols.map((c) => h("th", { class: c.cls || "" }, c.label)))),
    h("tbody", {}, rows.map((r, i) => h("tr", { class: opts.onRow ? "clickable" : "", onclick: opts.onRow ? () => opts.onRow!(r) : null },
      cols.map((c) => h("td", { class: c.cls || "" }, c.render(r, i))))))));
}

export function tabs(names: { key: string; label: string }[], onChange: (key: string) => void, initial?: string) {
  const bar = h("div", { class: "tabs", role: "tablist" });
  const set = (key: string) => {
    for (const b of $$<HTMLButtonElement>("button", bar)) b.classList.toggle("active", b.dataset.key === key);
    onChange(key);
  };
  for (const n of names) bar.appendChild(h("button", { dataset: { key: n.key }, role: "tab", onclick: () => set(n.key) }, n.label));
  queueMicrotask(() => set(initial || names[0]?.key));
  return bar;
}

export function statCard(label: string, value: Child, icon: string, opts: { href?: string; tone?: string } = {}) {
  const inner = [h("div", { class: "ico", html: iconSvg(icon) }), h("div", {}, h("div", { class: "val" }, value), h("div", { class: "lbl" }, label))];
  return opts.href
    ? h("a", { class: `card stat ${opts.tone || ""}`, href: opts.href }, inner)
    : h("div", { class: `card stat ${opts.tone || ""}` }, inner);
}

export function selectEl(options: { value: any; label: string }[], value?: any, attrs: Attrs = {}, placeholder?: string) {
  const s = h("select", attrs, placeholder !== undefined ? h("option", { value: "" }, placeholder) : null,
    options.map((o) => h("option", { value: String(o.value), selected: String(o.value) === String(value ?? "") }, o.label)));
  return s;
}
