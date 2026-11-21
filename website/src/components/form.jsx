import { forwardRef, useId } from 'react';
import { FileText, UploadCloud, X } from 'lucide-react';

/** Label + control + error/hint wrapper with proper aria wiring. */
export function Field({ label, error, hint, required, children, className = '', id: idProp }) {
  const auto = useId();
  const id = idProp || auto;
  const describedBy = error ? `${id}-err` : hint ? `${id}-hint` : undefined;
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="label">
          {label} {required && <span className="text-red-500" aria-hidden="true">*</span>}
        </label>
      )}
      {children({ id, 'aria-invalid': Boolean(error) || undefined, 'aria-describedby': describedBy, required })}
      {error ? <p id={`${id}-err`} className="field-error" role="alert">{error}</p> : hint ? <p id={`${id}-hint`} className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

export const Input = forwardRef(({ label, error, hint, className = '', required, ...props }, ref) => (
  <Field label={label} error={error} hint={hint} required={required} className={className}>
    {(a11y) => <input ref={ref} {...a11y} {...props} className={`input ${error ? 'input-error' : ''}`} />}
  </Field>
));
Input.displayName = 'Input';

export const Textarea = forwardRef(({ label, error, hint, className = '', required, rows = 4, ...props }, ref) => (
  <Field label={label} error={error} hint={hint} required={required} className={className}>
    {(a11y) => <textarea ref={ref} rows={rows} {...a11y} {...props} className={`input ${error ? 'input-error' : ''}`} />}
  </Field>
));
Textarea.displayName = 'Textarea';

export const Select = forwardRef(({ label, error, hint, className = '', required, options = [], placeholder, ...props }, ref) => (
  <Field label={label} error={error} hint={hint} required={required} className={className}>
    {(a11y) => (
      <select ref={ref} {...a11y} {...props} className={`input ${error ? 'input-error' : ''}`}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => (typeof o === 'string'
          ? <option key={o} value={o}>{o}</option>
          : <option key={o.value} value={o.value}>{o.label}</option>))}
      </select>
    )}
  </Field>
));
Select.displayName = 'Select';

export function Checkbox({ label, checked, onChange, description, name }) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex cursor-pointer items-start gap-3">
      <input id={id} name={name} type="checkbox" checked={Boolean(checked)} onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 h-5 w-5 rounded border-slate-300 text-primary-700 accent-primary-700 focus:ring-primary-500" />
      <span>
        <span className="text-sm font-medium text-primary-900">{label}</span>
        {description && <span className="block text-xs text-slate-500">{description}</span>}
      </span>
    </label>
  );
}

const fmtSize = (b) => (b > 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.ceil(b / 1024)} KB`);

/** Drop-zone style file picker (controlled; value is a File or null). */
export function FileDrop({ label, file, onChange, accept = '.pdf,.jpg,.jpeg,.png', error, required, hint, maxMb = 5 }) {
  const id = useId();
  const pick = (f) => {
    if (!f) return;
    if (f.size > maxMb * 1048576) { onChange(null, `File is larger than ${maxMb} MB`); return; }
    onChange(f, null);
  };
  return (
    <div>
      <span className="label">{label} {required && <span className="text-red-500">*</span>}</span>
      {file ? (
        <div className="flex items-center gap-3 rounded-xl border border-primary-100 bg-primary-50/50 p-3">
          <FileText className="h-5 w-5 shrink-0 text-primary-600" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-primary-900">{file.name}</p>
            <p className="text-xs text-slate-500">{fmtSize(file.size)}</p>
          </div>
          <button type="button" onClick={() => onChange(null, null)} className="btn-icon h-8 w-8" aria-label={`Remove ${label}`}><X className="h-4 w-4" /></button>
        </div>
      ) : (
        <label htmlFor={id}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files?.[0]); }}
          className={`flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed px-4 py-5 text-center transition hover:border-primary-400 hover:bg-primary-50/40 ${error ? 'border-red-300' : 'border-slate-200'}`}>
          <UploadCloud className="h-6 w-6 text-primary-500" />
          <span className="text-sm font-medium text-primary-800">Click or drag file</span>
          <span className="text-xs text-slate-500">{hint || `PDF, JPG or PNG · max ${maxMb} MB`}</span>
          <input id={id} type="file" accept={accept} className="sr-only" onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ''; }} />
        </label>
      )}
      {error && <p className="field-error" role="alert">{error}</p>}
    </div>
  );
}
