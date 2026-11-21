import { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { ArrowDownUp, Eye, Pencil, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';
import FormRenderer, { toFormValues, toPayload } from './FormRenderer';
import { ConfirmDialog, EmptyState, ErrorState, Img, Modal, Pagination, Spinner, StatusBadge } from '../components/ui';
import { useDebounce, useFetch } from '../hooks/useFetch';
import { useAuth } from '../context/AuthContext';
import api, { errorMessage, fieldErrors } from '../services/api';
import { formatDate, formatDateTime, formatMoney, getPath, setPath, titleCase } from '../utils/format';
import { canWrite } from '../utils/roles';

/** Renders a single table cell according to the column type. */
export function Cell({ col, row }) {
  const v = typeof col.value === 'function' ? col.value(row) : getPath(row, col.key);
  switch (col.type) {
    case 'image': return <Img src={v} alt="" className="h-10 w-14 rounded-lg object-cover" />;
    case 'boolean': return <StatusBadge status={String(Boolean(v))} label={v ? col.trueLabel || 'Yes' : col.falseLabel || 'No'} />;
    case 'status': return v ? <StatusBadge status={v} /> : '—';
    case 'date': return formatDate(v);
    case 'datetime': return formatDateTime(v);
    case 'money': return formatMoney(v);
    case 'title': return <span className="font-medium text-primary-900">{v ?? '—'}</span>;
    default: return v === undefined || v === null || v === '' ? '—' : String(v);
  }
}

/**
 * Generic list + CRUD screen driven by a resource config (see resources.js).
 */
export default function ResourceManager({ config, toolbar, rowActions, onChanged, initialFilters = {} }) {
  const { user } = useAuth();
  const writable = canWrite(user?.role, config.permission || config.key) && !config.readOnly;
  const [query, setQuery] = useState({ page: 1, limit: 15, sort: config.defaultSort || '' });
  const [filters, setFilters] = useState(initialFilters);
  const [q, setQ] = useState('');
  const dq = useDebounce(q);
  const params = useMemo(() => ({ ...query, ...filters, q: dq }), [query, filters, dq]);
  const { data, meta, loading, error, reload } = useFetch(config.endpoint, params);

  const [editing, setEditing] = useState(null); // null | { mode, values, id }
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [busyDelete, setBusyDelete] = useState(false);
  const [viewing, setViewing] = useState(null);

  useEffect(() => { setQuery((s) => ({ ...s, page: 1 })); }, [dq, filters]);

  const fields = config.fields || [];
  const openCreate = () => { setErrors({}); setEditing({ mode: 'create', values: toFormValues(config.defaults || {}, fields) }); };
  const openEdit = async (row) => {
    setErrors({});
    try {
      const { data: res } = await api.get(`${config.endpoint}/${row._id}`);
      setEditing({ mode: 'edit', id: row._id, values: toFormValues(res.data, fields) });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const save = async () => {
    const missing = fields.filter((f) => f.required && !(f.createOnly && editing.mode !== 'create') && (!f.showIf || f.showIf(editing.values, editing.mode)))
      .filter((f) => { const v = getPath(editing.values, f.name); return v === '' || v === null || v === undefined || (Array.isArray(v) && !v.length); });
    if (missing.length) {
      setErrors(Object.fromEntries(missing.map((f) => [f.name, `${f.label} is required`])));
      toast.error('Please fill in the required fields');
      return;
    }
    setSaving(true);
    try {
      let payload = toPayload(editing.values, fields);
      if (config.beforeSave) payload = config.beforeSave(payload, editing.mode);
      if (editing.mode === 'create') await api.post(config.endpoint, payload);
      else await api.put(`${config.endpoint}/${editing.id}`, payload);
      toast.success(`${config.singular} ${editing.mode === 'create' ? 'created' : 'updated'}`);
      setEditing(null);
      reload();
      onChanged?.();
    } catch (e) {
      setErrors(fieldErrors(e));
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setBusyDelete(true);
    try {
      await api.delete(`${config.endpoint}/${deleting._id}`);
      toast.success(`${config.singular} deleted`);
      setDeleting(null);
      reload();
      onChanged?.();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusyDelete(false);
    }
  };

  const sortBy = (key) => setQuery((s) => ({ ...s, sort: s.sort === key ? `-${key}` : key }));
  const label = (row) => getPath(row, config.labelKey || 'title') || row.name || row._id;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-1 flex-wrap gap-3">
          {config.searchable !== false && (
            <div className="relative w-full sm:w-72">
              <Search className="pointer-events-none absolute start-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input className="input ps-10" placeholder={`Search ${config.title.toLowerCase()}…`} value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search" />
            </div>
          )}
          {(config.filters || []).map((f) => (
            <FilterSelect key={f.key} filter={f} value={filters[f.key] || ''} onChange={(v) => setFilters((s) => ({ ...s, [f.key]: v }))} />
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {toolbar}
          <button type="button" className="btn-outline" onClick={reload} aria-label="Refresh"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button>
          {writable && config.creatable !== false && <button type="button" className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4" />New {config.singular.toLowerCase()}</button>}
        </div>
      </div>

      <div className="card overflow-hidden">
        {error ? <ErrorState message={error} onRetry={reload} /> : (
          <>
            {/* Desktop table */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full">
                <thead className="border-b border-slate-100 bg-slate-50/70">
                  <tr>
                    {config.columns.map((c) => (
                      <th key={c.key} className="table-th">
                        {c.sortable ? (
                          <button type="button" onClick={() => sortBy(c.sortKey || c.key)} className="inline-flex items-center gap-1 hover:text-primary-700">
                            {c.label}<ArrowDownUp className="h-3 w-3" />
                          </button>
                        ) : c.label}
                      </th>
                    ))}
                    <th className="table-th text-end">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {loading && !data ? (
                    <tr><td colSpan={config.columns.length + 1} className="py-16 text-center"><Spinner className="mx-auto h-6 w-6 text-primary-600" /></td></tr>
                  ) : data?.map((row) => (
                    <tr key={row._id} className="transition hover:bg-primary-50/30">
                      {config.columns.map((c) => <td key={c.key} className="table-td"><Cell col={c} row={row} /></td>)}
                      <td className="table-td">
                        <div className="flex justify-end gap-1">
                          {rowActions?.(row, reload)}
                          {config.viewable && <button type="button" className="btn-icon h-8 w-8" onClick={() => setViewing(row)} aria-label="View"><Eye className="h-4 w-4" /></button>}
                          {writable && config.editable !== false && <button type="button" className="btn-icon h-8 w-8" onClick={() => openEdit(row)} aria-label={`Edit ${label(row)}`}><Pencil className="h-4 w-4" /></button>}
                          {writable && config.deletable !== false && <button type="button" className="btn-icon h-8 w-8 text-red-600 hover:bg-red-50" onClick={() => setDeleting(row)} aria-label={`Delete ${label(row)}`}><Trash2 className="h-4 w-4" /></button>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="divide-y divide-slate-100 md:hidden">
              {loading && !data && <div className="py-12 text-center"><Spinner className="mx-auto h-6 w-6 text-primary-600" /></div>}
              {data?.map((row) => (
                <div key={row._id} className="space-y-2 p-4">
                  {config.columns.map((c) => (
                    <div key={c.key} className="flex items-start justify-between gap-4 text-sm">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{c.label}</span>
                      <span className="text-end"><Cell col={c} row={row} /></span>
                    </div>
                  ))}
                  <div className="flex justify-end gap-1 pt-2">
                    {rowActions?.(row, reload)}
                    {config.viewable && <button type="button" className="btn-outline btn-sm" onClick={() => setViewing(row)}>View</button>}
                    {writable && config.editable !== false && <button type="button" className="btn-outline btn-sm" onClick={() => openEdit(row)}>Edit</button>}
                    {writable && config.deletable !== false && <button type="button" className="btn btn-sm text-red-600 hover:bg-red-50" onClick={() => setDeleting(row)}>Delete</button>}
                  </div>
                </div>
              ))}
            </div>

            {!loading && !data?.length && <EmptyState title={`No ${config.title.toLowerCase()} found`} description={q ? 'Try a different search.' : writable && config.creatable !== false ? `Create the first ${config.singular.toLowerCase()}.` : undefined} />}
          </>
        )}
      </div>
      <Pagination meta={meta} onChange={(page) => setQuery((s) => ({ ...s, page }))} />

      <Modal open={Boolean(editing)} onClose={() => !saving && setEditing(null)} size={config.modalSize || 'lg'}
        title={editing?.mode === 'create' ? `New ${config.singular.toLowerCase()}` : `Edit ${config.singular.toLowerCase()}`}
        footer={(
          <>
            <button type="button" className="btn-outline" onClick={() => setEditing(null)} disabled={saving}>Cancel</button>
            <button type="button" className="btn-primary" onClick={save} disabled={saving}>{saving && <Spinner className="h-4 w-4" />}Save</button>
          </>
        )}>
        {editing && (
          <form onSubmit={(e) => { e.preventDefault(); save(); }}>
            <FormRenderer fields={fields} values={editing.values} errors={errors} mode={editing.mode}
              onChange={(path, v) => setEditing((s) => ({ ...s, values: setPath(s.values, path, v) }))} />
            <button type="submit" className="hidden" aria-hidden="true" tabIndex={-1} />
          </form>
        )}
      </Modal>

      <Modal open={Boolean(viewing)} onClose={() => setViewing(null)} title={viewing ? String(label(viewing)) : ''} size="md">
        {viewing && (config.renderView ? config.renderView(viewing) : (
          <dl className="space-y-3 text-sm">
            {[...config.columns, ...(config.viewFields || [])].map((c) => (
              <div key={c.key}><dt className="text-xs font-semibold uppercase tracking-wider text-slate-400">{c.label}</dt><dd className="mt-1 whitespace-pre-wrap text-slate-700"><Cell col={c} row={viewing} /></dd></div>
            ))}
          </dl>
        ))}
      </Modal>

      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={remove} loading={busyDelete}
        title={`Delete ${config.singular.toLowerCase()}?`}
        message={`"${deleting ? label(deleting) : ''}" will be permanently deleted. This cannot be undone.`} />
    </div>
  );
}

function FilterSelect({ filter, value, onChange }) {
  const { data } = useFetch(filter.endpoint || null, { limit: 100 });
  const options = filter.options || (data || []).map((o) => ({ value: o._id, label: typeof filter.optionLabel === 'function' ? filter.optionLabel(o) : o[filter.optionLabel || 'name'] || o.title }));
  return (
    <select className="input w-full sm:w-auto" value={value} onChange={(e) => onChange(e.target.value)} aria-label={filter.label}>
      <option value="">{filter.label}: All</option>
      {options.map((o) => (typeof o === 'string' ? <option key={o} value={o}>{titleCase(o)}</option> : <option key={String(o.value)} value={o.value}>{o.label}</option>))}
    </select>
  );
}
