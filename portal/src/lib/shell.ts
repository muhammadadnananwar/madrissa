/** Portal shell: auth guard, sidebar, top bar, notifications, global search. */
import { type User, clearSession, get, getSession, post, updateUser } from "./api";
import { iconSvg } from "./icons";
import { navFor } from "./nav";
import { $, clear, h, initials } from "./ui";

function avatar(user: User) {
  return h("div", { class: "avatar" }, user.photo ? h("img", { src: user.photo, alt: "" }) : initials(user.full_name || user.username));
}

function link(href: string, label: string, icon: string) {
  const here = location.pathname.replace(/\/$/, "") || "/";
  const active = href === "/" ? here === "/" : here === href || (href !== "/" && here.startsWith(href + "/"));
  return h("a", { href, class: active ? "active" : "", html: `${iconSvg(icon)}<span>${label}</span>` });
}

function group(title: string, items: HTMLElement[], key: string) {
  const collapsed = localStorage.getItem(`nav.${key}`) === "1";
  const g = h("div", { class: `nav-group ${collapsed ? "collapsed" : ""}` },
    h("button", { onclick: () => { g.classList.toggle("collapsed"); localStorage.setItem(`nav.${key}`, g.classList.contains("collapsed") ? "1" : "0"); } }, title),
    h("div", { class: "nav-items" }, items));
  return g;
}

const SIDEBAR_SCROLL = "nav.scrollTop";

/** Keep the sidebar where it was and make sure the current screen's menu item is visible. */
function revealActive(nav: HTMLElement) {
  const sidebar = nav.closest<HTMLElement>(".sidebar");
  // Several links can match by prefix (/attendance and /attendance/biometric): keep only the most specific one.
  const matches = [...nav.querySelectorAll<HTMLAnchorElement>("a.active")];
  const best = matches.sort((x, y) => y.getAttribute("href")!.length - x.getAttribute("href")!.length)[0];
  matches.forEach((m) => m !== best && m.classList.remove("active"));
  const active = best || null;
  if (!sidebar) return;
  active?.closest(".nav-group")?.classList.remove("collapsed"); // expand the group that holds the current page
  const saved = Number(sessionStorage.getItem(SIDEBAR_SCROLL) || 0);
  sidebar.scrollTop = saved; // same position as on the previous page (no jump)
  if (!active) return;
  const box = sidebar.getBoundingClientRect();
  const item = active.getBoundingClientRect();
  if (item.top < box.top + 8 || item.bottom > box.bottom - 8) {
    sidebar.scrollTop += item.top - box.top - (box.height - item.height) / 2; // centre it
  }
}

async function renderNav(user: User) {
  const nav = $("#nav");
  const sidebar = nav.closest<HTMLElement>(".sidebar");
  sidebar?.addEventListener("scroll", () => sessionStorage.setItem(SIDEBAR_SCROLL, String(sidebar.scrollTop)), { passive: true });
  const groups = navFor(user.role, !!user.is_superuser);
  clear(nav, groups.map((g) => group(g.group, g.items.map((i) => link(i.href, i.label, i.icon)), g.group)));
  revealActive(nav); // fixed menu items are known immediately
  try {
    const meta = await get("meta/");
    for (const g of meta.groups) {
      nav.appendChild(group(g.group, g.items.map((i: any) => link(`/m/${i.key}`, i.label, i.icon)), `r.${g.group}`));
    }
  } catch { /* offline */ }
  revealActive(nav); // again once the module screens are in the menu
}

function renderUser(user: User) {
  const chip = $("#user-chip");
  const menu = h("div", { class: "menu hidden" },
    h("div", { class: "small muted", style: { padding: ".4rem .7rem" } }, user.role_display),
    h("a", { href: "/profile" }, "My profile & password"),
    h("a", { href: `/person/${user.id}` }, "My full record"),
    h("a", { href: "/notifications" }, "Notifications"),
    h("button", { onclick: logout }, "Sign out"));
  clear(chip, avatar(user), h("div", { class: "small" }, h("div", { style: { fontWeight: 600 } }, user.full_name), h("div", { class: "muted" }, user.role_display.split(" (")[0])), menu);
  chip.addEventListener("click", (e) => { e.stopPropagation(); menu.classList.toggle("hidden"); });
  document.addEventListener("click", () => menu.classList.add("hidden"));
}

async function logout() {
  const s = getSession();
  try { await post("auth/logout/", { refresh: s?.refresh }); } catch { /* ignore */ }
  clearSession();
  location.href = "/login";
}

async function pollNotifications() {
  const dot = $("#notif-dot");
  try {
    const { count } = await get("notifications/unread_count/");
    dot.textContent = count > 99 ? "99+" : String(count);
    dot.classList.toggle("hidden", !count);
  } catch { /* ignore */ }
}

function setupSearch(user: User) {
  const input = $<HTMLInputElement>("#global-search");
  const box = $("#search-results");
  if (!user.is_staff_member) { input.closest(".search")?.classList.add("hidden"); return; }
  let t: any;
  input.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(async () => {
      const q = input.value.trim();
      if (q.length < 2) return box.classList.add("hidden");
      const rows = await get("search/", { q });
      clear(box, rows.length ? rows.map((r: any) => h("a", { href: `/person/${r.id}` }, h("strong", {}, r.name), " ", h("span", { class: "muted small" }, `${r.role}${r.extra ? " · " + r.extra : ""}`)))
        : h("div", { class: "empty" }, "No people found"));
      box.classList.remove("hidden");
    }, 250);
  });
  document.addEventListener("click", (e) => { if (!box.contains(e.target as Node) && e.target !== input) box.classList.add("hidden"); });
}

async function init(): Promise<User> {
  const s = getSession();
  if (!s) {
    location.href = `/login?next=${encodeURIComponent(location.pathname + location.search)}`;
    return new Promise(() => {});
  }
  let user = s.user;
  try {
    user = await get("auth/me/");
    updateUser(user);
  } catch { /* api() handles 401 */ }
  if (user.must_change_password && location.pathname !== "/profile") {
    location.href = "/profile?force=1";
    return new Promise(() => {});
  }
  document.body.dataset.role = user.role;
  renderUser(user);
  renderNav(user);
  setupSearch(user);
  pollNotifications();
  setInterval(pollNotifications, 60000);
  $("#menu-toggle")?.addEventListener("click", () => $(".sidebar").classList.toggle("open"));
  return user;
}

/** Resolves with the signed-in user once the shell is ready. */
export const ready: Promise<User> = typeof window !== "undefined" ? init() : (new Promise(() => {}) as any);
