import { useCallback, useEffect, useRef, useState } from 'react';
import api, { errorMessage } from '../services/api';

/**
 * GET helper with loading / error / reload.
 *   const { data, meta, loading, error, reload } = useFetch('/public/news', { page: 1 });
 * Pass `null` as url to skip fetching.
 */
export function useFetch(url, params, { keepPrevious = true } = {}) {
  const [state, setState] = useState({ data: null, meta: null, loading: Boolean(url), error: null });
  const paramsKey = JSON.stringify(params || {});
  const reqId = useRef(0);

  const load = useCallback(async () => {
    if (!url) return;
    const id = ++reqId.current;
    setState((s) => ({ ...s, data: keepPrevious ? s.data : null, loading: true, error: null }));
    try {
      const { data } = await api.get(url, { params: JSON.parse(paramsKey) });
      if (id === reqId.current) setState({ data: data.data, meta: data.meta || null, loading: false, error: null });
    } catch (e) {
      if (id === reqId.current) setState((s) => ({ ...s, loading: false, error: errorMessage(e), status: e.response?.status }));
    }
  }, [url, paramsKey, keepPrevious]);

  useEffect(() => { load(); }, [load]);

  return { ...state, reload: load, setData: (fn) => setState((s) => ({ ...s, data: typeof fn === 'function' ? fn(s.data) : fn })) };
}

export function useDebounce(value, delay = 400) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return v;
}
