/** Auth guard for pages outside the main shell (print views). */
import { type User, get, getSession } from "./api";

export async function requireUser(): Promise<User> {
  if (!getSession()) {
    location.href = `/login?next=${encodeURIComponent(location.pathname + location.search)}`;
    return new Promise(() => {});
  }
  return get("auth/me/");
}
