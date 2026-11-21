import axios from 'axios';

/**
 * Base URL of the website API (Django: /api/site). Accepts either the full base
 * ("https://api.example.com/api/site") or just the backend domain ("https://api.example.com"),
 * in which case /api/site is added.
 */
function apiBase(raw) {
  const v = (raw || '/api/site').trim().replace(/\/+$/, '');
  try {
    const u = new URL(v);
    if (u.pathname === '' || u.pathname === '/') return `${u.origin}/api/site`;
  } catch { /* relative path such as /api/site */ }
  return v;
}

export const API_URL = apiBase(import.meta.env.VITE_API_URL);
export const ASSET_URL = import.meta.env.VITE_ASSET_URL || '';
export const PORTAL_URL = (import.meta.env.VITE_PORTAL_URL || 'http://localhost:4322').replace(/\/$/, '');

/** The public website never authenticates; logins happen in the management portal (PORTAL_URL). */
const api = axios.create({ baseURL: API_URL, timeout: 30000 });

/** Human-readable message from an axios error. */
export const errorMessage = (err, fallback = 'Something went wrong. Please try again.') => {
  if (err?.response?.data?.message) return err.response.data.message;
  if (err?.code === 'ECONNABORTED') return 'The request timed out. Please try again.';
  if (err?.message === 'Network Error') return 'Cannot reach the server. Check your connection.';
  return fallback;
};

/** Field errors as { 'personal.fullName': 'message' } */
export const fieldErrors = (err) => Object.fromEntries((err?.response?.data?.errors || []).map((e) => [e.field, e.message]));

/** Resolves stored file URLs (/uploads/..., absolute URLs) to something the browser can load. */
export const assetUrl = (url) => {
  if (!url) return '';
  if (/^(https?:|data:|blob:)/.test(url)) return url;
  if (url.startsWith('/uploads')) return `${ASSET_URL}${url}`;
  return url;
};

export default api;
