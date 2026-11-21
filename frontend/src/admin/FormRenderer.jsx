import { useState } from 'react';
import toast from 'react-hot-toast';
import { FileText, ImagePlus, Plus, Trash2, UploadCloud, X } from 'lucide-react';
import { Checkbox, Field } from '../components/form';
import { Img, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { assetUrl, errorMessage, uploadFile } from '../services/api';
import { getPath, toDateInput } from '../utils/format';
import { ICON_NAMES } from '../utils/icons';

const toLocalDateTime = (d) => {
  if (!d) return '';
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return '';
  const off = date.getTimezoneOffset();
  return new Date(date.getTime() - off * 60000).toISOString().slice(0, 16);
};

/** Prepares an API document for editing (populated refs → ids, dates → input strings). */
export function toFormValues(doc = {}, fields = []) {
  let values = JSON.parse(JSON.stringify(doc || {}));
  const set = (obj, path, v) => {
    const keys = path.split('.');
    let cur = obj;
    keys.slice(0, -1).forEach((k) => { cur[k] = cur[k] && typeof cur[k] === 'object' ? cur[k] : {}; cur = cur[k]; });
    cur[keys[keys.length - 1]] = v;
  };
  fields.forEach((f) => {
    const v = getPath(values, f.name);
    if (f.type === 'ref') set(values, f.name, v && typeof v === 'object' ? v._id : v ?? '');
    else if (f.type === 'multiref') set(values, f.name, (v || []).map((x) => (typeof x === 'object' ? x._id : x)));
    else if (f.type === 'date') set(values, f.name, toDateInput(v));
    else if (f.type === 'datetime') set(values, f.name, toLocalDateTime(v));
    else if (f.type === 'list') set(values, f.name, Array.isArray(v) ? v.join('\n') : v || '');
    else if (f.type === 'checkbox') set(values, f.name, v ?? f.default ?? false);
    else if (f.type === 'password') set(values, f.name, '');
    else if (v === undefined || v === null) set(values, f.name, f.default ?? (f.type === 'repeater' ? [] : ''));
  });
  values = { ...values };
  return values;
}

/** Converts form values to an API payload. */
export function toPayload(values, fields = []) {
  const out = JSON.parse(JSON.stringify(values));
  const set = (obj, path, v) => {
    const keys = path.split('.');
    let cur = obj;
    keys.slice(0, -1).forEach((k) => { cur[k] = cur[k] && typeof cur[k] === 'object' ? cur[k] : {}; cur = cur[k]; });
    cur[keys[keys.length - 1]] = v;
  };
  fields.forEach((f) => {
    const v = getPath(out, f.name);
    if (f.type === 'list') set(out, f.name, String(v || '').split('\n').map((s) => s.trim()).filter(Boolean));
    if (f.type === 'number' && v !== '' && v !== null && v !== undefined) set(out, f.name, Number(v));
    if ((f.type === 'datetime') && v) set(out, f.name, new Date(v).toISOString());
  });
  return out;
}

function RefSelect({ field, value, onChange, a11y, multiple }) {
  const { data, loading } = useFetch(field.endpoint, { limit: 100, ...(field.params || {}) });
  const label = (o) => (typeof field.optionLabel === 'function' ? field.optionLabel(o) : o[field.optionLabel || 'name'] || o.title || o.name);
  if (multiple) {
    const selected = new Set(value || []);
    return (
      <div className="scrollbar-thin max-h-48 space-y-1 overflow-y-auto rounded-xl border border-slate-200 p-3">
        {loading && <Spinner className="h-4 w-4" />}
        {(data || []).map((o) => (
          <label key={o._id} className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="accent-primary-700" checked={selected.has(o._id)}
              onChange={(e) => {
                const next = new Set(selected);
                if (e.target.checked) next.add(o._id); else next.delete(o._id);
                onChange([...next]);
              }} />
            {label(o)}
          </label>
        ))}
        {!loading && !data?.length && <p className="text-xs text-slate-500">No options available</p>}
      </div>
    );
  }
  return (
    <select {...a11y} className="input" value={value || ''} onChange={(e) => onChange(e.target.value)}>
      <option value="">{loading ? 'Loading…' : field.placeholder || '— Select —'}</option>
      {(data || []).map((o) => <option key={o._id} value={o._id}>{label(o)}</option>)}
    </select>
  );
}

function UploadInput({ field, value, onChange }) {
  const [busy, setBusy] = useState(false);
  const isImage = field.type === 'image';
  const handle = async (file) => {
    if (!file) return;
    setBusy(true);
    try {
      const res = await uploadFile(file, field.folder || (isImage ? 'images' : 'documents'));
      onChange(res.url);
      toast.success('File uploaded');
    } catch (e) {
      toast.error(errorMessage(e, 'Upload failed'));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {value && isImage && <Img src={value} alt="" className="h-16 w-24 rounded-lg object-cover" />}
        {value && !isImage && (
          <a href={assetUrl(value)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 truncate rounded-lg bg-primary-50 px-3 py-2 text-xs text-primary-700">
            <FileText className="h-4 w-4" /> {value.split('/').pop()}
          </a>
        )}
        <label className="btn-outline btn-sm cursor-pointer">
          {busy ? <Spinner className="h-4 w-4" /> : isImage ? <ImagePlus className="h-4 w-4" /> : <UploadCloud className="h-4 w-4" />}
          {value ? 'Replace' : 'Upload'}
          <input type="file" className="sr-only" accept={field.accept || (isImage ? '.jpg,.jpeg,.png,.webp' : '.pdf')} onChange={(e) => { handle(e.target.files?.[0]); e.target.value = ''; }} />
        </label>
        {value && <button type="button" className="btn-icon h-8 w-8 text-red-600" onClick={() => onChange('')} aria-label="Remove file"><X className="h-4 w-4" /></button>}
      </div>
      <input className="input text-xs" placeholder={isImage ? 'or paste an image URL' : 'or paste a file URL'} value={value || ''} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function Repeater({ field, value = [], onChange }) {
  const rows = Array.isArray(value) ? value : [];
  const update = (i, key, v) => onChange(rows.map((r, j) => (j === i ? { ...r, [key]: v } : r)));
  return (
    <div className="space-y-3">
      {rows.map((row, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <div key={i} className="relative rounded-2xl border border-slate-200 bg-slate-50/50 p-4 pe-12">
          <div className="grid gap-3 sm:grid-cols-2">
            {field.subfields.map((sf) => (
              <ControlField key={sf.name} field={sf} value={row[sf.name]} onChange={(v) => update(i, sf.name, v)} compact />
            ))}
          </div>
          <button type="button" onClick={() => onChange(rows.filter((_, j) => j !== i))} className="btn-icon absolute end-2 top-2 h-8 w-8 text-red-600" aria-label="Remove row">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <button type="button" className="btn-outline btn-sm" onClick={() => onChange([...rows, Object.fromEntries(field.subfields.map((s) => [s.name, s.default ?? '']))])}>
        <Plus className="h-4 w-4" /> Add {field.itemLabel || 'item'}
      </button>
    </div>
  );
}

function ControlField({ field, value, onChange, error, compact }) {
  if (field.type === 'checkbox') {
    return <div className={compact ? '' : 'pt-7'}><Checkbox label={field.label} description={field.help} checked={value} onChange={onChange} /></div>;
  }
  return (
    <Field label={field.label} error={error} hint={field.help} required={field.required}>
      {(a11y) => {
        switch (field.type) {
          case 'textarea':
          case 'richtext':
          case 'list':
            return <textarea {...a11y} rows={field.rows || (field.type === 'richtext' ? 10 : 4)} className="input font-normal" value={value ?? ''} placeholder={field.placeholder || (field.type === 'list' ? 'One item per line' : '')} onChange={(e) => onChange(e.target.value)} />;
          case 'select':
            return (
              <select {...a11y} className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
                {!field.required && <option value="">{field.placeholder || '— Select —'}</option>}
                {field.options.map((o) => (typeof o === 'string' ? <option key={o} value={o}>{o}</option> : <option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            );
          case 'icon':
            return (
              <select {...a11y} className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
                <option value="">Default</option>
                {ICON_NAMES.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            );
          case 'ref': return <RefSelect field={field} value={value} onChange={onChange} a11y={a11y} />;
          case 'multiref': return <RefSelect field={field} value={value} onChange={onChange} a11y={a11y} multiple />;
          case 'image':
          case 'file': return <UploadInput field={field} value={value} onChange={onChange} />;
          case 'repeater': return <Repeater field={field} value={value} onChange={onChange} />;
          case 'date': return <input {...a11y} type="date" className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)} />;
          case 'datetime': return <input {...a11y} type="datetime-local" className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)} />;
          default:
            return (
              <input {...a11y} type={field.type === 'password' ? 'password' : field.type === 'number' ? 'number' : field.type === 'email' ? 'email' : 'text'}
                className="input" value={value ?? ''} placeholder={field.placeholder} min={field.min} max={field.max} step={field.step}
                readOnly={field.readOnly} autoComplete={field.type === 'password' ? 'new-password' : undefined} onChange={(e) => onChange(e.target.value)} />
            );
        }
      }}
    </Field>
  );
}

/**
 * Renders a list of field configs against a values object.
 * fields: [{ name, label, type, required, options, endpoint, colSpan, showIf, section }]
 */
export default function FormRenderer({ fields, values, onChange, errors = {}, mode = 'create' }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      {fields.filter((f) => (!f.showIf || f.showIf(values, mode)) && !(f.createOnly && mode !== 'create')).map((f) => {
        const wide = f.colSpan === 2 || ['textarea', 'richtext', 'list', 'repeater', 'multiref'].includes(f.type);
        if (f.type === 'heading') {
          return <h4 key={f.key || f.name} className="mt-2 border-b border-slate-100 pb-2 font-sans text-sm font-semibold uppercase tracking-wider text-gold-600 sm:col-span-2">{f.label}</h4>;
        }
        return (
          <div key={f.key || f.name} className={wide ? 'sm:col-span-2' : ''}>
            <ControlField field={f} value={getPath(values, f.name)} onChange={(v) => onChange(f.name, v)} error={errors[f.name]} />
          </div>
        );
      })}
    </div>
  );
}
