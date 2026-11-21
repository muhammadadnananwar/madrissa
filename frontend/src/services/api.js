import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || '/api';
export const ASSET_URL = import.meta.env.VITE_ASSET_URL || '';
const TOKEN_KEY = 'ums_token';

export const tokenStore = {
  get: () => {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  set: (t) => {
    try { localStorage.setItem(TOKEN_KEY, t); } catch { /* storage unavailable */ }
  },
  clear: () => {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ }
  },
};

const api = axios.create({ baseURL: API_URL, timeout: 30000 });

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && tokenStore.get()) {
      tokenStore.clear();
      window.dispatchEvent(new Event('ums:logout'));
    }
    return Promise.reject(error);
  },
);

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

/** Fetches a protected file with the auth header and opens it in a new tab. */
export async function openProtectedFile(path) {
  const win = window.open('', '_blank');
  try {
    const res = await api.get(path, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    if (win) win.location.href = url;
    else window.location.href = url;
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) {
    if (win) win.close();
    throw e;
  }
}

export async function uploadFile(file, folder = 'images') {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post(`/admin/uploads?folder=${folder}`, fd);
  return data.data;
}

export default api;
