/**
 * Generic resource screen: list, search, filter, sort, paginate, export, view, create, edit,
 * delete and run workflow actions — all driven by /api/meta/<key>/.
 */
import { ApiError, api, del, download, get, post } from "./api";
import { buildForm, type FieldMeta, remoteSelect } from "./form";
import { iconSvg } from "./icons";
import { badge, busy, clear, confirmDialog, empty, fmtDate, fmtDateTime, h, modal, showCredentials, spinner, toast, toastError } from "./ui";

export type ResourceMeta = {
  key: string;
  label: string;
  singular: string;
  group: string;
  description: string;
  fields: FieldMeta[];
  list_fields: string[];
  search: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
  actions: { name: string; label?: string; confirm?: string; style?: string; input?: FieldMeta[]; row?: boolean }[];
};

const metaCache = new Map<string, Promise<ResourceMeta>>();
export function getMeta(key: string) {
  if (!metaCache.has(key)) metaCache.set(key, get(`meta/${key}/`));
  return metaCache.get(key)!;
}

/** Display a field value in a table cell / detail view. */
export function renderValue(f: FieldMeta | undefined, row: any, name: string): Node | string {
  const v = row[name];
  if (name === "full_name" || !f) return v == null || v === "" ? "—" : String(v);
  if (f.type === "fk") return row[`${name}_label`] ?? "—";
  if (f.type === "m2m") return (row[`${name}_labels`] || []).join(", ") || "—";
  if (f.type === "choice") {
    const label = row[`${name}_display`] ?? v;
    return ["status", "priority", "result", "condition", "kind"].includes(name) || name.endsWith("status") ? badge(v, label) : label ?? "—";
  }
  if (f.type === "boolean") return v ? "✓" : "—";
  if (f.type === "date") return fmtDate(v);
  if (f.type === "datetime") return fmtDateTime(v);
  if (f.type === "time") return v ? String(v).slice(0, 5) : "—";
  if (f.type === "file" || f.type === "image") return v ? h("a", { href: v, target: "_blank", onclick: (e: Event) => e.stopPropagation() }, f.type === "image" ? "image" : "file") : "—";
  if (f.type === "json") return Array.isArray(v) ? v.join(", ") || "all" : v ? JSON.stringify(v) : "—";
  if (f.type === "decimal") return v == null ? "—" : Number(v).toLocaleString();
  if (v === null || v === undefined || v === "") return "—";
  const s = String(v);
  return s.length > 80 ? `${s.slice(0, 80)}…` : s;
}

/** Links shown in the detail view for specific resources. */
function extraLinks(key: string, row: any): HTMLElement[] {
  const L = (href: string, label: string, icon = "file") => h("a", { class: "btn sm", href, html: `${iconSvg(icon)} ${label}` });
  switch (key) {
    case "students":
      return [L(`/person/${row.user}`, "Full record", "id"), L(`/print/id-card?user=${row.user}`, "ID card", "id"),
        L(`/exams/report-card?student=${row.id}`, "Report card", "award"), L(`/hifz?student=${row.id}`, "Hifz progress", "quran"),
        L(`/fees?student=${row.id}`, "Fees", "receipt")];
    case "employees":
      return [L(`/person/${row.user}`, "Full record", "id"), L(`/print/id-card?user=${row.user}`, "ID card", "id")];
    case "users":
      return [L(`/person/${row.id}`, "Full record", "id")];
    case "invoices":
      return [L(`/print/invoice?id=${row.id}`, "Print invoice", "print")];
    case "payments":
      return [L(`/print/receipt?id=${row.id}`, "Print receipt", "print")];
    case "payslips":
      return [L(`/print/payslip?id=${row.id}`, "Print payslip", "print")];
    case "certificates":
      return [L(`/print/certificate?id=${row.id}`, "Print certificate", "print")];
    case "donations":
      return [L(`/print/donation?id=${row.id}`, "Print receipt", "print")];
    case "live-classes":
      return [L(`/live/room?id=${row.id}`, "Open class", "video")];
    case "courses":
      return [L(`/lms/course?id=${row.id}`, "Open course", "graduation")];
    case "exam-papers":
      return [L(`/exams/marks?paper=${row.id}`, "Enter marks", "edit")];
    default:
      return [];
  }
}

/** Show credentials returned by the server after creating accounts. */
function handleGenerated(d: any) {
  if (d?.generated_password) showCredentials("Login created", [["Username", d.username], ["Password", d.generated_password]]);
  else if (d?.generated_login) showCredentials("Parent login created", [["Username", d.generated_login.username], ["Password", d.generated_login.password]]);
  else if (d?.temporary_password) showCredentials("Password reset", [["Temporary password", d.temporary_password]]);
  else if (d?.username && d?.password) showCredentials("Student account created", [["Admission no", d.admission_no || ""], ["Username", d.username], ["Password", d.password]]);
}

export async function openForm(key: string, row: any | null, onSaved: (r: any) => void, presets: Record<string, any> = {}) {
  const meta = await getMeta(key);
  const editing = !!row;
  const form = buildForm(meta.fields, row || presets, { editing, sections: meta.fields.some((f) => f.extra) });
  const save = h("button", { class: "btn primary" }, editing ? "Save changes" : `Create ${meta.singular.toLowerCase()}`);
  const m = modal(`${editing ? "Edit" : "New"} ${meta.singular}`, form.el, { wide: meta.fields.length > 12, actions: [h("button", { class: "btn", onclick: () => m.close() }, "Cancel"), save] });
  save.addEventListener("click", async () => {
    if (!form.validate()) return;
    let data: any;
    try {
      data = form.getData();
    } catch (e) {
      return toastError(e);
    }
    save.disabled = true;
    try {
      const r = editing ? await api(`${key}/${row.id}/`, { method: "PATCH", body: data }) : await api(`${key}/`, { method: "POST", body: data });
      toast(editing ? "Saved." : "Created.");
      m.close();
      handleGenerated(r);
      onSaved(r);
    } catch (e) {
      if (e instanceof ApiError) form.showErrors(e.data);
      toastError(e);
    } finally {
      save.disabled = false;
    }
  });
}

export async function runAction(key: string, row: any, action: ResourceMeta["actions"][number], onDone: () => void) {
  const url = `${key}/${row.id}/${action.name}/`;
  const exec = async (body: any, btn?: HTMLButtonElement) => {
    const r = await busy(btn || null, () => post(url, body));
    if (r !== undefined) {
      handleGenerated(r);
      onDone();
    }
    return r;
  };
  if (action.input?.length) {
    const inputs: Record<string, () => any> = {};
    const body = h("div", {}, action.confirm ? h("p", {}, action.confirm) : null,
      action.input.map((f) => {
        let el: HTMLElement;
        if (f.type === "fk" && f.resource) {
          el = remoteSelect(f.resource, null, { required: f.required });
          inputs[f.name] = () => (el as any).getValue();
        } else if (f.type === "choice") {
          el = h("select", {}, h("option", { value: "" }, "—"), (f.choices || []).map((c) => h("option", { value: c.value }, c.label)));
          inputs[f.name] = () => (el as HTMLSelectElement).value;
        } else if (f.type === "boolean") {
          el = h("input", { type: "checkbox" });
          inputs[f.name] = () => (el as HTMLInputElement).checked;
        } else if (f.type === "text") {
          el = h("textarea", {});
          inputs[f.name] = () => (el as HTMLTextAreaElement).value;
        } else {
          el = h("input", { type: f.type === "date" ? "date" : f.type === "decimal" ? "number" : "text", step: "any" });
          inputs[f.name] = () => (el as HTMLInputElement).value;
        }
        return h("div", { class: "field" }, h("label", {}, f.label), el);
      }));
    const go = h("button", { class: `btn ${action.style === "danger" ? "danger" : "primary"}` }, action.label || action.name);
    const m = modal(action.label || action.name, body, { actions: [h("button", { class: "btn", onclick: () => m.close() }, "Cancel"), go] });
    go.addEventListener("click", async () => {
      const payload: Record<string, any> = {};
      for (const [k, fn] of Object.entries(inputs)) {
        const v = fn();
        if (v !== "" && v !== null && v !== undefined) payload[k] = v;
      }
      if (await exec(payload, go)) m.close();
    });
    return;
  }
  if (action.confirm && !(await confirmDialog(action.confirm, action.label || "Confirm", action.style === "danger"))) return;
  await exec({});
}

export async function openDetail(key: string, id: number, onChange: () => void) {
  const meta = await getMeta(key);
  const m = modal(meta.singular, spinner(), { wide: true });
  let row: any;
  try {
    row = await get(`${key}/${id}/`);
  } catch (e) {
    m.close();
    return toastError(e);
  }
  const fields = meta.fields.filter((f) => f.name !== "password" && !f.hidden);
  const refresh = () => {
    m.close();
    onChange();
  };
  const buttons: HTMLElement[] = [...extraLinks(key, row)];
  for (const a of meta.actions.filter((a) => a.row !== false)) {
    buttons.push(h("button", { class: `btn sm ${a.style || ""}`, onclick: () => runAction(key, row, a, refresh) }, a.label || a.name));
  }
  if (meta.can_edit) buttons.push(h("button", { class: "btn sm", html: `${iconSvg("edit")} Edit`, onclick: () => { m.close(); openForm(key, row, onChange); } }));
  if (meta.can_delete) buttons.push(h("button", {
    class: "btn sm danger", onclick: async () => {
      if (!(await confirmDialog(`Delete this ${meta.singular.toLowerCase()}? This cannot be undone.`, "Delete", true))) return;
      if (await busy(null, () => del(`${key}/${row.id}/`), "Deleted.") !== undefined) refresh();
    },
  }, "Delete"));
  clear(m.body,
    buttons.length ? h("div", { class: "row", style: { marginBottom: "1rem" } }, buttons) : null,
    h("dl", { class: "kv" }, fields.flatMap((f) => [h("dt", {}, f.label), h("dd", {}, renderValue(f, row, f.name))])),
    h("p", { class: "muted small", style: { marginTop: "1rem" } }, `Created ${fmtDateTime(row.created_at)} · Updated ${fmtDateTime(row.updated_at)}`));
}

/** Mount a full CRUD screen into `root`. */
export async function mountCrud(root: HTMLElement, key: string, opts: { filters?: Record<string, any>; title?: boolean; pageSize?: number } = {}) {
  clear(root, spinner());
  let meta: ResourceMeta;
  try {
    meta = await getMeta(key);
  } catch (e) {
    clear(root, h("div", { class: "alert bad" }, e instanceof ApiError && e.status === 403 ? "You do not have access to this section." : String((e as any).message)));
    return;
  }
  const byName = Object.fromEntries(meta.fields.map((f) => [f.name, f]));
  const state = { page: 1, search: "", ordering: "", filters: { ...(opts.filters || {}) } as Record<string, any> };
  for (const [k, v] of new URLSearchParams(location.search)) if (k !== "page") state.filters[k] = v;

  const tbody = h("div", {});
  const pager = h("div", { class: "pager" });
  const searchInput = h("input", { type: "search", placeholder: `Search ${meta.label.toLowerCase()}…` });
  const filterFields = meta.list_fields.map((n) => byName[n]).filter((f) => f && (f.type === "choice" || f.type === "boolean")).slice(0, 4);
  const filterEls = filterFields.map((f) => {
    const s = h("select", { "aria-label": f.label }, h("option", { value: "" }, `All ${f.label.toLowerCase()}`),
      f.type === "boolean" ? [h("option", { value: "true" }, `${f.label}: yes`), h("option", { value: "false" }, `${f.label}: no`)]
        : (f.choices || []).map((c) => h("option", { value: String(c.value) }, c.label)));
    s.value = state.filters[f.name] ?? "";
    s.addEventListener("change", () => { state.filters[f.name] = s.value; state.page = 1; load(); });
    return s;
  });
  let t: any;
  searchInput.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { state.search = searchInput.value; state.page = 1; load(); }, 300); });

  const params = () => ({ ...state.filters, search: state.search, ordering: state.ordering, page: state.page, page_size: opts.pageSize || 25 });

  async function load() {
    clear(tbody, spinner());
    try {
      const data = await get(`${key}/`, params());
      const rows = data.results ?? data;
      if (!rows.length) {
        clear(tbody, empty(state.search || Object.values(state.filters).some(Boolean) ? "No matching records." : `No ${meta.label.toLowerCase()} yet.`));
      } else {
        const cols = meta.list_fields;
        clear(tbody, h("div", { class: "table-wrap" }, h("table", {},
          h("thead", {}, h("tr", {}, cols.map((c) => {
            const f = byName[c];
            const label = f?.label || c.replace(/_/g, " ");
            const dir = state.ordering === c ? " ▲" : state.ordering === `-${c}` ? " ▼" : "";
            return h("th", {
              class: `sortable ${f?.type === "decimal" ? "num" : ""}`,
              onclick: () => { state.ordering = state.ordering === c ? `-${c}` : c; load(); },
            }, label + dir);
          }))),
          h("tbody", {}, rows.map((r: any) => h("tr", { class: "clickable", onclick: () => openDetail(key, r.id, load) },
            cols.map((c) => h("td", { class: byName[c]?.type === "decimal" ? "num" : "" }, renderValue(byName[c], r, c)))))))));
      }
      const count = data.count ?? rows.length;
      const pages = Math.max(1, Math.ceil(count / (opts.pageSize || 25)));
      clear(pager, h("span", {}, `${count} record${count === 1 ? "" : "s"}`),
        h("div", { class: "row" },
          h("button", { class: "btn sm", disabled: state.page <= 1, onclick: () => { state.page--; load(); } }, "‹ Prev"),
          h("span", {}, `Page ${state.page} of ${pages}`),
          h("button", { class: "btn sm", disabled: state.page >= pages, onclick: () => { state.page++; load(); } }, "Next ›")));
    } catch (e) {
      clear(tbody, h("div", { class: "alert bad" }, (e as any).message));
    }
  }

  const head = opts.title === false ? null : h("div", { class: "page-head" },
    h("div", {}, h("h1", {}, meta.label), h("p", {}, meta.description || meta.group)),
    h("div", { class: "row" },
      h("button", { class: "btn", html: `${iconSvg("download")} Export CSV`, onclick: (e: any) => busy(e.currentTarget, () => download(`${key}/export/`, { ...state.filters, search: state.search }, `${key}.csv`)) }),
      meta.can_create ? h("button", { class: "btn primary", html: `${iconSvg("plus")} New ${meta.singular.toLowerCase()}`, onclick: () => openForm(key, null, load, state.filters) }) : null));

  clear(root, head, h("div", { class: "card flush" },
    h("div", { class: "toolbar" }, meta.search ? searchInput : null, filterEls,
      h("button", { class: "btn sm ghost", html: iconSvg("refresh"), title: "Refresh", onclick: load })),
    tbody, pager));
  load();
  return { reload: load };
}
