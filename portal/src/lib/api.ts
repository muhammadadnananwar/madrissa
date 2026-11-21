/** API client for the Django backend (JWT auth with transparent refresh). */
export const API_URL: string = (import.meta.env.PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
const KEY = "madrasa.portal.session";

export type User = {
  id: number;
  username: string;
  full_name: string;
  role: string;
  role_display: string;
  photo: string | null;
  must_change_password: boolean;
  is_staff_member: boolean;
  student?: { id: number; admission_no: string; section: string | null; section_id: number | null };
  employee?: { id: number; employee_no: string; designation: string };
  children?: { id: number; user_id: number; name: string; admission_no: string; section: string | null }[];
  [k: string]: any;
};
export type Session = { access: string; refresh: string; user: User };

export function getSession(): Session | null {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "null");
  } catch {
    return null;
  }
}
export function setSession(s: Session) {
  localStorage.setItem(KEY, JSON.stringify(s));
}
export function updateUser(user: User) {
  const s = getSession();
  if (s) setSession({ ...s, user });
}
export function clearSession() {
  localStorage.removeItem(KEY);
}

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(status: number, data: any) {
    super(errorText(data) || `Request failed (${status})`);
    this.status = status;
    this.data = data;
  }
}

/** Flatten DRF error payloads into a readable string. */
export function errorText(data: any): string {
  if (!data) return "";
  if (typeof data === "string") return data.slice(0, 300);
  if (Array.isArray(data)) return data.map(errorText).join(" ");
  if (data.detail) return errorText(data.detail);
  return Object.entries(data)
    .map(([k, v]) => (k === "non_field_errors" ? errorText(v) : `${k.replace(/_/g, " ")}: ${errorText(v)}`))
    .join(" · ");
}

let refreshing: Promise<boolean> | null = null;
async function refreshToken(): Promise<boolean> {
  const s = getSession();
  if (!s?.refresh) return false;
  refreshing ??= fetch(`${API_URL}/api/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: s.refresh }),
  })
    .then(async (r) => {
      if (!r.ok) return false;
      const d = await r.json();
      setSession({ ...s, access: d.access, refresh: d.refresh || s.refresh });
      return true;
    })
    .catch(() => false)
    .finally(() => setTimeout(() => (refreshing = null), 0));
  return refreshing;
}

type Opts = { method?: string; body?: any; params?: Record<string, any>; raw?: boolean; auth?: boolean };

export function qs(params?: Record<string, any>): string {
  if (!params) return "";
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") p.append(k, String(v));
  const s = p.toString();
  return s ? `?${s}` : "";
}

export async function api<T = any>(path: string, opts: Opts = {}, retry = true): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_URL}/api/${path.replace(/^\/+/, "")}${qs(opts.params)}`;
  const headers: Record<string, string> = {};
  const s = getSession();
  if (s?.access && opts.auth !== false) headers.Authorization = `Bearer ${s.access}`;
  let body: BodyInit | undefined;
  if (opts.body instanceof FormData) body = opts.body;
  else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, { method: opts.method || (body ? "POST" : "GET"), headers, body });
  if (res.status === 401 && retry && opts.auth !== false) {
    if (await refreshToken()) return api(path, opts, false);
    clearSession();
    if (!location.pathname.startsWith("/login")) location.href = `/login?next=${encodeURIComponent(location.pathname + location.search)}`;
    throw new ApiError(401, { detail: "Session expired" });
  }
  if (opts.raw) {
    if (!res.ok) throw new ApiError(res.status, await res.text());
    return res as any;
  }
  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export const get = <T = any>(path: string, params?: Record<string, any>) => api<T>(path, { params });
export const post = <T = any>(path: string, body: any = {}) => api<T>(path, { method: "POST", body });
export const patch = <T = any>(path: string, body: any) => api<T>(path, { method: "PATCH", body });
export const del = (path: string) => api(path, { method: "DELETE" });

/** Download a file (CSV export etc.) with the auth header. */
export async function download(path: string, params: Record<string, any>, filename: string) {
  const res: Response = await api(path, { params, raw: true });
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

/** Fetch every page of a list endpoint. */
export async function getAll<T = any>(path: string, params: Record<string, any> = {}): Promise<T[]> {
  const first = await get(path, { ...params, page_size: 500 });
  if (Array.isArray(first)) return first;
  let rows: T[] = first.results || [];
  let next = first.next;
  while (next) {
    const page = await api(next);
    rows = rows.concat(page.results);
    next = page.next;
  }
  return rows;
}
