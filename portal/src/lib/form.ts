/** Builds create/edit forms from the field metadata returned by /api/meta/<key>/. */
import { get } from "./api";
import { h } from "./ui";

export type FieldMeta = {
  name: string;
  label: string;
  type: string;
  required?: boolean;
  readonly?: boolean;
  hidden?: boolean;
  nullable?: boolean;
  help?: string;
  choices?: { value: any; label: string }[];
  resource?: string | null;
  default?: any;
  extra?: boolean;
};

const ROLES_CACHE: { value: string; label: string }[] = [];
async function roles() {
  if (!ROLES_CACHE.length) ROLES_CACHE.push(...(await get("meta/")).roles);
  return ROLES_CACHE;
}

/** Select whose options come from /api/options/<resource>/, with a search box for large lists. */
export function remoteSelect(resource: string, value: any, opts: { multiple?: boolean; required?: boolean; name?: string; filters?: Record<string, any> } = {}) {
  const sel = h("select", { name: opts.name, multiple: !!opts.multiple, required: !!opts.required, size: opts.multiple ? 6 : undefined });
  const search = h("input", { type: "search", placeholder: "Search…", class: "small", style: { marginBottom: "4px" } });
  const values = new Set((Array.isArray(value) ? value : value != null && value !== "" ? [value] : []).map(String));
  let labels = new Map<string, string>();
  async function load(q = "") {
    try {
      const rows = await get(`options/${resource}/`, { q, limit: 100, ...(opts.filters || {}) });
      const missing = [...values].filter((v) => !rows.some((r: any) => String(r.id) === v) && !labels.has(v));
      if (missing.length) {
        for (const r of await get(`options/${resource}/`, { ids: missing.join(",") })) labels.set(String(r.id), r.label);
      }
      for (const r of rows) labels.set(String(r.id), r.label);
      const ids = new Set(rows.map((r: any) => String(r.id)));
      for (const v of values) ids.add(v);
      sel.replaceChildren(
        ...(opts.multiple ? [] : [h("option", { value: "" }, opts.required ? "— select —" : "— none —")]),
        ...[...ids].map((id) => h("option", { value: id, selected: values.has(id) }, labels.get(id) || `#${id}`)),
      );
    } catch {
      sel.replaceChildren(h("option", { value: "" }, "(unavailable)"));
    }
  }
  sel.addEventListener("change", () => {
    values.clear();
    for (const o of Array.from(sel.selectedOptions)) if (o.value) values.add(o.value);
  });
  let t: any;
  search.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => load(search.value), 250);
  });
  load();
  const wrap = h("div", {}, search, sel);
  (wrap as any).getValue = () => (opts.multiple ? [...values].map(Number) : values.size ? Number([...values][0]) : null);
  return wrap;
}

function toLocalInput(v: any) {
  if (!v) return "";
  const d = new Date(v);
  if (isNaN(+d)) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

type Control = { field: FieldMeta; el: HTMLElement; get: () => any; isFile?: boolean };

export function buildForm(fields: FieldMeta[], values: Record<string, any> = {}, opts: { editing?: boolean; sections?: boolean } = {}) {
  const controls: Control[] = [];
  const grid = h("div", { class: "form-grid" });
  const visible = fields.filter((f) => !f.readonly && !f.hidden);
  let sectionShown = false;
  for (const f of visible) {
    if (opts.sections && f.extra && !sectionShown) {
      grid.appendChild(h("div", { class: "form-section" }, "Personal details & login"));
      sectionShown = true;
    }
    if (opts.sections && !f.extra && sectionShown && !(grid as any)._profile) {
      grid.appendChild(h("div", { class: "form-section" }, "Profile"));
      (grid as any)._profile = true;
    }
    const v = values[f.name] ?? (opts.editing ? undefined : f.default);
    const id = `f_${f.name}_${Math.random().toString(36).slice(2, 7)}`;
    let input: HTMLElement;
    let getter: () => any;
    let isFile = false;
    const full = ["text", "json", "m2m"].includes(f.type);
    switch (f.type) {
      case "boolean": {
        const cb = h("input", { type: "checkbox", id, checked: !!v });
        controls.push({ field: f, el: cb, get: () => cb.checked });
        grid.appendChild(h("div", { class: "field check" }, h("label", { for: id }, cb, f.label), f.help ? h("div", { class: "help" }, f.help) : null));
        continue;
      }
      case "choice": {
        const s = h("select", { id, required: !!f.required }, h("option", { value: "" }, f.required ? "— select —" : "—"),
          (f.choices || []).map((c) => h("option", { value: String(c.value), selected: String(c.value) === String(v ?? "") }, c.label)));
        input = s;
        getter = () => {
          if (s.value === "") return f.required ? "" : null;
          const c = (f.choices || []).find((c) => String(c.value) === s.value);
          return c ? c.value : s.value;
        };
        break;
      }
      case "fk":
      case "m2m": {
        if (f.resource) {
          const rs = remoteSelect(f.resource, v, { multiple: f.type === "m2m", required: f.required });
          input = rs;
          getter = () => (rs as any).getValue();
        } else {
          const i = h("input", { id, type: "number", value: v ?? "" });
          input = i;
          getter = () => (i.value ? Number(i.value) : null);
        }
        break;
      }
      case "text": {
        const t = h("textarea", { id, required: !!f.required }, v ?? "");
        input = t;
        getter = () => t.value;
        break;
      }
      case "json": {
        if (f.name === "audience") {
          const box = h("div", { class: "row", style: { gap: ".4rem .9rem" } });
          const chosen = new Set<string>(Array.isArray(v) ? v : []);
          roles().then((rs) => rs.forEach((r) => box.appendChild(h("label", { style: { fontWeight: 500 } },
            h("input", { type: "checkbox", checked: chosen.has(r.value), onchange: (e: any) => (e.target.checked ? chosen.add(r.value) : chosen.delete(r.value)) }),
            " ", r.label.split(" (")[0]))));
          input = h("div", {}, box, h("div", { class: "help" }, "Leave all unchecked to address everyone."));
          getter = () => [...chosen];
        } else {
          const t = h("textarea", { id, class: "mono" }, v === undefined ? "" : JSON.stringify(v));
          input = t;
          getter = () => {
            if (!t.value.trim()) return f.name === "working_days" ? [] : null;
            try { return JSON.parse(t.value); } catch { throw new Error(`${f.label}: invalid JSON`); }
          };
        }
        break;
      }
      case "file":
      case "image": {
        const i = h("input", { id, type: "file", accept: f.type === "image" ? "image/*" : undefined });
        isFile = true;
        input = h("div", {}, i, v ? h("div", { class: "help" }, "Current: ", h("a", { href: v, target: "_blank" }, "open file")) : null);
        getter = () => i.files?.[0] || undefined;
        break;
      }
      default: {
        const type = ({ date: "date", datetime: "datetime-local", time: "time", integer: "number", decimal: "number", email: "email", url: "url" } as any)[f.type] || "text";
        const val = f.type === "datetime" ? toLocalInput(v) : f.type === "time" ? String(v ?? "").slice(0, 5) : v ?? "";
        const i = h("input", { id, type, value: val, required: !!f.required && !(opts.editing && f.name === "password"), step: f.type === "decimal" ? "any" : undefined });
        input = i;
        getter = () => {
          if (i.value === "") return ["string", "email", "url"].includes(f.type) ? "" : null;
          if (f.type === "integer") return Number(i.value);
          if (f.type === "datetime") return new Date(i.value).toISOString();
          return i.value;
        };
      }
    }
    controls.push({ field: f, el: input!, get: getter!, isFile });
    grid.appendChild(h("div", { class: `field ${full ? "full" : ""}`, dataset: { name: f.name } },
      h("label", { for: id }, f.label, f.required ? " *" : ""), input!, f.help ? h("div", { class: "help" }, f.help) : null));
  }

  const form = h("form", { novalidate: true, onsubmit: (e: Event) => e.preventDefault() }, grid);

  /** Returns JSON object, or FormData when a file was chosen. */
  function getData(): Record<string, any> | FormData {
    const data: Record<string, any> = {};
    let hasFile = false;
    for (const c of controls) {
      const v = c.get();
      if (c.isFile) {
        if (v) { data[c.field.name] = v; hasFile = true; }
        continue;
      }
      if (opts.editing && c.field.name === "password" && !v) continue;
      const blank = v === null || v === undefined || v === "";
      if (blank) {
        if (!opts.editing) continue; // let the server apply its defaults
        const textual = ["string", "text", "email", "url", "choice"].includes(c.field.type);
        if (c.field.nullable) data[c.field.name] = null;
        else if (textual) data[c.field.name] = "";
        // non-nullable dates/numbers with defaults: leave unchanged
        continue;
      }
      data[c.field.name] = v;
    }
    if (!hasFile) return data;
    const fd = new FormData();
    for (const [k, v] of Object.entries(data)) {
      if (v === null || v === undefined || v === "") continue;
      if (Array.isArray(v)) v.forEach((x) => fd.append(k, typeof x === "object" ? JSON.stringify(x) : String(x)));
      else if (v instanceof File) fd.append(k, v);
      else if (typeof v === "object") fd.append(k, JSON.stringify(v));
      else fd.append(k, String(v));
    }
    return fd;
  }

  function showErrors(err: any) {
    form.querySelectorAll(".err").forEach((e) => e.remove());
    if (!err || typeof err !== "object") return;
    for (const [k, msg] of Object.entries(err)) {
      const field = form.querySelector(`.field[data-name="${k}"]`);
      if (field) field.appendChild(h("div", { class: "err" }, Array.isArray(msg) ? msg.join(" ") : String(msg)));
    }
  }

  function validate(): boolean {
    let ok = true;
    form.querySelectorAll(".err").forEach((e) => e.remove());
    for (const c of controls) {
      if (!c.field.required || c.isFile || c.field.type === "boolean") continue;
      if (opts.editing && c.field.name === "password") continue;
      let v: any;
      try { v = c.get(); } catch { v = null; }
      if (v === null || v === "" || (Array.isArray(v) && !v.length)) {
        ok = false;
        form.querySelector(`.field[data-name="${c.field.name}"]`)?.appendChild(h("div", { class: "err" }, "This field is required."));
      }
    }
    return ok;
  }

  return { el: form, getData, showErrors, validate };
}
