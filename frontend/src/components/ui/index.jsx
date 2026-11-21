import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, ChevronDown, ChevronLeft, ChevronRight, ImageOff, Inbox, Loader2, RefreshCw, X } from 'lucide-react';
import { assetUrl } from '../../services/api';
import { STATUS_STYLES, titleCase } from '../../utils/format';

/* ------------------------------- Feedback ------------------------------- */
export const Spinner = ({ className = 'h-5 w-5' }) => <Loader2 className={`animate-spin ${className}`} aria-hidden="true" />;

export function PageLoader({ label = 'Loading…', className = 'py-24' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 text-primary-700 ${className}`} role="status" aria-live="polite">
      <Spinner className="h-8 w-8" />
      <span className="text-sm text-slate-500">{label}</span>
    </div>
  );
}

export function ErrorState({ message = 'Something went wrong.', onRetry, className = 'py-16' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 text-center ${className}`} role="alert">
      <div className="rounded-full bg-red-50 p-3 text-red-600"><AlertTriangle className="h-6 w-6" /></div>
      <p className="max-w-md text-sm text-slate-600">{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-outline btn-sm"><RefreshCw className="h-4 w-4" /> Try again</button>
      )}
    </div>
  );
}

export function EmptyState({ title = 'Nothing here yet', description, icon: Icon = Inbox, action, className = 'py-16' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-2 text-center ${className}`}>
      <div className="rounded-2xl bg-primary-50 p-4 text-primary-500"><Icon className="h-7 w-7" /></div>
      <p className="mt-2 font-semibold text-primary-900">{title}</p>
      {description && <p className="max-w-sm text-sm text-slate-500">{description}</p>}
      {action}
    </div>
  );
}

/** Wraps async page sections: loading → error → empty → content */
export function AsyncBlock({ loading, error, onRetry, empty, emptyProps, children, loaderClass }) {
  if (loading) return <PageLoader className={loaderClass} />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (empty) return <EmptyState {...emptyProps} />;
  return children;
}

export function StatusBadge({ status, label }) {
  const key = String(status);
  return <span className={`badge ${STATUS_STYLES[key] || 'bg-slate-100 text-slate-600'}`}>{label || titleCase(key)}</span>;
}

export function PlaceholderBadge({ show = true, className = '' }) {
  if (!show) return null;
  return (
    <span className={`badge border border-dashed border-gold-500 bg-gold-50 text-gold-700 ${className}`} title="Sample content — replace via the admin dashboard">
      Sample
    </span>
  );
}

/* --------------------------------- Image -------------------------------- */
export function Img({ src, alt = '', className = '', fallbackClass = '', ...rest }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  if (!src || failed) {
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-primary-700 via-primary-800 to-primary-950 text-gold-300/70 ${className} ${fallbackClass}`} role="img" aria-label={alt}>
        <ImageOff className="h-8 w-8" />
      </div>
    );
  }
  return <img src={assetUrl(src)} alt={alt} loading="lazy" decoding="async" onError={() => setFailed(true)} className={className} {...rest} />;
}

/* -------------------------------- Motion -------------------------------- */
export function Reveal({ children, delay = 0, y = 24, className = '', as = 'div' }) {
  const Comp = motion[as] || motion.div;
  return (
    <Comp
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </Comp>
  );
}

export function SectionHeading({ eyebrow, title, description, align = 'center', light = false, action }) {
  const alignCls = align === 'center' ? 'mx-auto text-center items-center' : 'items-start';
  return (
    <Reveal className={`mb-12 flex max-w-3xl flex-col ${alignCls} ${action ? 'sm:max-w-none sm:flex-row sm:items-end sm:justify-between' : ''}`}>
      <div className={align === 'center' && !action ? 'flex flex-col items-center' : ''}>
        {eyebrow && <span className={`eyebrow ${light ? 'text-gold-300' : ''}`}>{eyebrow}</span>}
        <h2 className={`section-title text-balance ${light ? 'text-white' : ''}`}>{title}</h2>
        {description && <p className={`mt-4 text-base leading-relaxed sm:text-lg ${light ? 'text-primary-100' : 'text-slate-600'}`}>{description}</p>}
      </div>
      {action && <div className="mt-6 shrink-0 sm:mt-0">{action}</div>}
    </Reveal>
  );
}

/* --------------------------------- Modal -------------------------------- */
export function Modal({ open, onClose, title, children, footer, size = 'lg' }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose?.();
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  const widths = { sm: 'max-w-md', md: 'max-w-xl', lg: 'max-w-3xl', xl: 'max-w-5xl' };
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-[80] flex items-end justify-center bg-primary-950/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}>
          <motion.div role="dialog" aria-modal="true" aria-label={title}
            className={`flex max-h-[92vh] w-full ${widths[size]} flex-col overflow-hidden rounded-t-3xl bg-white shadow-2xl sm:rounded-3xl`}
            initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }} transition={{ type: 'spring', damping: 26, stiffness: 300 }}>
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
              <h3 className="font-sans text-lg font-semibold text-primary-900">{title}</h3>
              <button type="button" onClick={onClose} className="btn-icon" aria-label="Close"><X className="h-5 w-5" /></button>
            </div>
            <div className="scrollbar-thin flex-1 overflow-y-auto px-6 py-5">{children}</div>
            {footer && <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 bg-slate-50/60 px-6 py-4">{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  );
}

export function ConfirmDialog({ open, title = 'Are you sure?', message, confirmLabel = 'Delete', onConfirm, onClose, loading, danger = true }) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm"
      footer={(
        <>
          <button type="button" className="btn-outline" onClick={onClose} disabled={loading}>Cancel</button>
          <button type="button" className={danger ? 'btn-danger' : 'btn-primary'} onClick={onConfirm} disabled={loading}>
            {loading && <Spinner className="h-4 w-4" />} {confirmLabel}
          </button>
        </>
      )}>
      <p className="text-sm text-slate-600">{message}</p>
    </Modal>
  );
}

/* ------------------------------- Pagination ------------------------------ */
export function Pagination({ meta, onChange }) {
  if (!meta || meta.pages <= 1) return null;
  const { page, pages, total, limit } = meta;
  const from = (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);
  const nums = [];
  for (let i = Math.max(1, page - 2); i <= Math.min(pages, page + 2); i += 1) nums.push(i);
  return (
    <nav className="mt-8 flex flex-col items-center justify-between gap-3 sm:flex-row" aria-label="Pagination">
      <p className="text-sm text-slate-500">Showing <b>{from}</b>–<b>{to}</b> of <b>{total}</b></p>
      <div className="flex items-center gap-1">
        <button type="button" className="btn-icon disabled:opacity-40" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Previous page">
          <ChevronLeft className="h-4 w-4 rtl:rotate-180" />
        </button>
        {nums.map((n) => (
          <button key={n} type="button" onClick={() => onChange(n)} aria-current={n === page ? 'page' : undefined}
            className={`h-9 min-w-9 rounded-full px-3 text-sm font-medium transition ${n === page ? 'bg-primary-700 text-white' : 'text-primary-700 hover:bg-primary-50'}`}>
            {n}
          </button>
        ))}
        <button type="button" className="btn-icon disabled:opacity-40" disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Next page">
          <ChevronRight className="h-4 w-4 rtl:rotate-180" />
        </button>
      </div>
    </nav>
  );
}

/* ------------------------------- Accordion ------------------------------- */
export function Accordion({ items, getTitle = (i) => i.question, getBody = (i) => i.answer }) {
  const [open, setOpen] = useState(0);
  return (
    <div className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-soft">
      {items.map((item, i) => (
        <div key={item._id || i}>
          <button type="button" onClick={() => setOpen(open === i ? -1 : i)} aria-expanded={open === i}
            className="flex w-full items-center justify-between gap-4 px-6 py-5 text-start font-semibold text-primary-900 transition hover:bg-primary-50/50">
            <span>{getTitle(item)}</span>
            <ChevronDown className={`h-5 w-5 shrink-0 text-gold-600 transition-transform ${open === i ? 'rotate-180' : ''}`} />
          </button>
          <AnimatePresence initial={false}>
            {open === i && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <p className="px-6 pb-5 text-sm leading-relaxed text-slate-600">{getBody(item)}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}

/* --------------------------------- Tabs ---------------------------------- */
export function Tabs({ tabs, value, onChange, className = '' }) {
  return (
    <div className={`scrollbar-thin flex gap-2 overflow-x-auto pb-1 ${className}`} role="tablist">
      {tabs.map((t) => (
        <button key={t.value} type="button" role="tab" aria-selected={value === t.value} onClick={() => onChange(t.value)}
          className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition ${value === t.value ? 'bg-primary-700 text-white shadow-soft' : 'bg-white text-primary-700 ring-1 ring-primary-100 hover:bg-primary-50'}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ---------------------- Lightweight content renderer --------------------- */
/** Renders editor text safely: blank-line paragraphs, "## " headings and "- " bullet lists. No raw HTML. */
export function RichText({ text, className = '' }) {
  if (!text) return null;
  const blocks = String(text).split(/\n\s*\n/);
  return (
    <div className={`prose-ums ${className}`}>
      {blocks.map((block, i) => {
        const lines = block.split('\n').filter(Boolean);
        if (lines.length && lines.every((l) => /^\s*[-*]\s+/.test(l))) {
          // eslint-disable-next-line react/no-array-index-key
          return <ul key={i}>{lines.map((l, j) => <li key={j}>{l.replace(/^\s*[-*]\s+/, '')}</li>)}</ul>;
        }
        if (/^##\s+/.test(block)) {
          const [head, ...rest] = lines;
          return (
            // eslint-disable-next-line react/no-array-index-key
            <div key={i}>
              <h2>{head.replace(/^##\s+/, '')}</h2>
              {rest.length > 0 && (rest.every((l) => /^\s*[-*]\s+/.test(l))
                ? <ul>{rest.map((l, j) => <li key={j}>{l.replace(/^\s*[-*]\s+/, '')}</li>)}</ul>
                : <p>{rest.join(' ')}</p>)}
            </div>
          );
        }
        // eslint-disable-next-line react/no-array-index-key
        return <p key={i}>{lines.join(' ')}</p>;
      })}
    </div>
  );
}
