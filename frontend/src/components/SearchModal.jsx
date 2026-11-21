import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, Building2, Calendar, FileText, Megaphone, Newspaper, Search, User, File } from 'lucide-react';
import api, { API_URL } from '../services/api';
import { useDebounce } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { Modal, Spinner } from './ui';

export const TYPE_ICONS = {
  program: BookOpen, department: Building2, faculty: User, news: Newspaper, event: Calendar, document: FileText, page: File, announcement: Megaphone,
};

export const resultHref = (r) => (r.external ? `${API_URL}${r.url.replace(/^\/api/, '')}` : r.url);

export default function SearchModal({ open, onClose }) {
  const { t } = useSite();
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounced = useDebounce(q, 300);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
    else { setQ(''); setResults([]); }
  }, [open]);

  useEffect(() => {
    let cancelled = false;
    if (debounced.trim().length < 2) { setResults([]); return undefined; }
    setLoading(true);
    api.get('/public/search', { params: { q: debounced } })
      .then(({ data }) => !cancelled && setResults(data.data.results))
      .catch(() => !cancelled && setResults([]))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [debounced]);

  const go = (r) => {
    onClose();
    if (r.external) window.open(resultHref(r), '_blank', 'noopener');
    else navigate(r.url);
  };

  const submit = (e) => {
    e.preventDefault();
    if (q.trim().length >= 2) {
      onClose();
      navigate(`/search?q=${encodeURIComponent(q.trim())}`);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={t('search')} size="md">
      <form onSubmit={submit} className="relative">
        <Search className="pointer-events-none absolute start-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
        <input ref={inputRef} value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('searchPlaceholder')}
          className="input rounded-2xl py-3.5 ps-12 text-base" aria-label={t('search')} />
        {loading && <Spinner className="absolute end-4 top-1/2 h-5 w-5 -translate-y-1/2 text-primary-500" />}
      </form>
      <div className="mt-4 space-y-1">
        {results.slice(0, 8).map((r, i) => {
          const Icon = TYPE_ICONS[r.type] || File;
          return (
            // eslint-disable-next-line react/no-array-index-key
            <button key={i} type="button" onClick={() => go(r)} className="flex w-full items-start gap-3 rounded-xl p-3 text-start transition hover:bg-primary-50">
              <span className="mt-0.5 rounded-lg bg-primary-100 p-2 text-primary-700"><Icon className="h-4 w-4" /></span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium text-primary-900">{r.title}</span>
                <span className="block truncate text-xs capitalize text-slate-500">{r.type} {r.description ? `· ${r.description}` : ''}</span>
              </span>
            </button>
          );
        })}
        {debounced.length >= 2 && !loading && results.length === 0 && <p className="py-6 text-center text-sm text-slate-500">{t('noResults')}</p>}
        {results.length > 8 && (
          <button type="button" onClick={submit} className="flex w-full items-center justify-center gap-2 py-3 text-sm font-semibold text-primary-700">
            See all {results.length} results <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>
      <p className="mt-4 text-center text-xs text-slate-400">Tip: press <kbd className="rounded border px-1">Ctrl</kbd> + <kbd className="rounded border px-1">K</kbd> to search from anywhere</p>
    </Modal>
  );
}
