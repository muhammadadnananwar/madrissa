export const formatDate = (d, opts = { day: 'numeric', month: 'short', year: 'numeric' }) => {
  if (!d) return '—';
  const date = new Date(d);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('en-GB', opts);
};

export const formatDateTime = (d) => {
  if (!d) return '—';
  const date = new Date(d);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

export const formatMoney = (n, currency = 'PKR') => {
  if (n === null || n === undefined || n === '') return 'To be announced';
  return `${currency} ${Number(n).toLocaleString('en-PK')}`;
};

export const titleCase = (s = '') => String(s).replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export const timeAgo = (d) => {
  const diff = (Date.now() - new Date(d).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return formatDate(d);
};

export const toDateInput = (d) => {
  if (!d) return '';
  const date = new Date(d);
  return Number.isNaN(date.getTime()) ? '' : date.toISOString().slice(0, 10);
};

export const isPlaceholderText = (s) => typeof s === 'string' && /\[(Placeholder|Sample)\]/.test(s);

/** Gets a nested value: get(obj, 'fee.tuitionPerSemester') */
export const getPath = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);

/** Immutably sets a nested value. */
export const setPath = (obj, path, value) => {
  const keys = path.split('.');
  const clone = Array.isArray(obj) ? [...obj] : { ...(obj || {}) };
  let cur = clone;
  keys.forEach((k, i) => {
    if (i === keys.length - 1) cur[k] = value;
    else {
      cur[k] = Array.isArray(cur[k]) ? [...cur[k]] : { ...(cur[k] || {}) };
      cur = cur[k];
    }
  });
  return clone;
};

export const STATUS_STYLES = {
  submitted: 'bg-sky-50 text-sky-700',
  under_review: 'bg-amber-50 text-amber-700',
  documents_required: 'bg-orange-50 text-orange-700',
  approved: 'bg-emerald-50 text-emerald-700',
  rejected: 'bg-red-50 text-red-700',
  waitlisted: 'bg-violet-50 text-violet-700',
  enrolled: 'bg-primary-100 text-primary-800',
  paid: 'bg-emerald-50 text-emerald-700',
  unpaid: 'bg-amber-50 text-amber-700',
  overdue: 'bg-red-50 text-red-700',
  partially_paid: 'bg-sky-50 text-sky-700',
  waived: 'bg-slate-100 text-slate-600',
  present: 'bg-emerald-50 text-emerald-700',
  absent: 'bg-red-50 text-red-700',
  late: 'bg-amber-50 text-amber-700',
  leave: 'bg-sky-50 text-sky-700',
  new: 'bg-sky-50 text-sky-700',
  in_progress: 'bg-amber-50 text-amber-700',
  resolved: 'bg-emerald-50 text-emerald-700',
  spam: 'bg-slate-100 text-slate-600',
  active: 'bg-emerald-50 text-emerald-700',
  graduated: 'bg-primary-100 text-primary-800',
  suspended: 'bg-red-50 text-red-700',
  withdrawn: 'bg-slate-100 text-slate-600',
  true: 'bg-emerald-50 text-emerald-700',
  false: 'bg-slate-100 text-slate-600',
};
