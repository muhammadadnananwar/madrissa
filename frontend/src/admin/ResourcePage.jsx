import { useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { CalendarCheck, Download, FileText, KeyRound, Megaphone, Sparkles, Users } from 'lucide-react';
import ResourceManager from './ResourceManager';
import { RESOURCES } from './resources';
import { Checkbox, Input, Select } from '../components/form';
import { Modal, PageLoader, Spinner, StatusBadge } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useAuth } from '../context/AuthContext';
import api, { assetUrl, errorMessage, openProtectedFile } from '../services/api';
import { formatDateTime } from '../utils/format';
import { canAccess, canWrite, dashBase } from '../utils/roles';
import NotFound from '../pages/NotFound';

/* ------------------------------ Students ------------------------------ */
function PortalAccountModal({ student, onClose, onSaved }) {
  const [form, setForm] = useState({ email: student?.user?.email || student?.email || '', password: '', isActive: student?.user?.isActive ?? true });
  const [saving, setSaving] = useState(false);
  const hasAccount = Boolean(student?.user);
  const save = async () => {
    setSaving(true);
    try {
      await api.post(`/admin/students/${student._id}/account`, { email: form.email, password: form.password || undefined, isActive: form.isActive });
      toast.success(hasAccount ? 'Portal account updated' : 'Portal account created');
      onSaved();
      onClose();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };
  return (
    <Modal open onClose={onClose} title={`Portal account — ${student.rollNumber}`} size="sm"
      footer={<><button type="button" className="btn-outline" onClick={onClose}>Cancel</button><button type="button" className="btn-primary" disabled={saving} onClick={save}>{saving && <Spinner className="h-4 w-4" />}Save</button></>}>
      <div className="space-y-4">
        <p className="text-sm text-slate-600">{hasAccount ? 'Update login email, reset the password or disable access.' : 'Create a login so this student can access the portal.'}</p>
        <Input label="Login email" type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
        <Input label={hasAccount ? 'New password (optional)' : 'Password'} type="password" autoComplete="new-password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} hint="At least 8 characters" />
        {hasAccount && <Checkbox label="Account active" checked={form.isActive} onChange={(v) => setForm((f) => ({ ...f, isActive: v }))} />}
      </div>
    </Modal>
  );
}

/* --------------------------- Merit lists --------------------------- */
function GenerateMeritModal({ onClose, onDone }) {
  const { data: programs } = useFetch('/admin/programs', { limit: 100 });
  const [form, setForm] = useState({ program: '', session: '', round: 1, title: '', minAggregate: '', limit: '' });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const go = async () => {
    if (!form.program) { toast.error('Select a program'); return; }
    setBusy(true);
    try {
      const { data } = await api.post('/admin/merit-lists/generate', { ...form, round: Number(form.round) || 1 });
      toast.success(data.message);
      onDone();
      onClose();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal open onClose={onClose} title="Generate merit list" size="md"
      footer={<><button type="button" className="btn-outline" onClick={onClose}>Cancel</button><button type="button" className="btn-primary" disabled={busy} onClick={go}>{busy && <Spinner className="h-4 w-4" />}Generate</button></>}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Select label="Program" required className="sm:col-span-2" value={form.program} onChange={set('program')} placeholder="Select program" options={(programs || []).map((p) => ({ value: p._id, label: p.title }))} />
        <Input label="Session (optional)" value={form.session} onChange={set('session')} hint="Must match the session on applications" />
        <Input label="Round" type="number" min="1" value={form.round} onChange={set('round')} />
        <Input label="Minimum aggregate %" type="number" value={form.minAggregate} onChange={set('minAggregate')} />
        <Input label="Number of seats" type="number" value={form.limit} onChange={set('limit')} hint="Defaults to program seats" />
        <Input label="Title (optional)" className="sm:col-span-2" value={form.title} onChange={set('title')} />
        <p className="text-xs text-slate-500 sm:col-span-2">Applicants with status submitted, under review or approved are ranked by aggregate. The list is saved unpublished so you can review it before publishing.</p>
      </div>
    </Modal>
  );
}

/* ------------------------------ Results ------------------------------ */
function PublishResultsModal({ onClose, onDone }) {
  const { data: courses } = useFetch('/admin/courses', { limit: 100 });
  const [form, setForm] = useState({ term: '', course: '', isPublished: true });
  const [busy, setBusy] = useState(false);
  const go = async () => {
    if (!form.term) { toast.error('Enter the term'); return; }
    setBusy(true);
    try {
      const { data } = await api.patch('/admin/results/publish', { ...form, course: form.course || undefined });
      toast.success(data.message);
      onDone();
      onClose();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal open onClose={onClose} title="Publish results" size="sm"
      footer={<><button type="button" className="btn-outline" onClick={onClose}>Cancel</button><button type="button" className="btn-primary" disabled={busy} onClick={go}>{busy && <Spinner className="h-4 w-4" />}Apply</button></>}>
      <div className="space-y-4">
        <Input label="Term" required placeholder="Fall 2026" value={form.term} onChange={(e) => setForm((f) => ({ ...f, term: e.target.value }))} />
        <Select label="Course (optional)" value={form.course} onChange={(e) => setForm((f) => ({ ...f, course: e.target.value }))} placeholder="All courses" options={(courses || []).map((c) => ({ value: c._id, label: `${c.code} — ${c.title}` }))} />
        <Select label="Action" value={String(form.isPublished)} onChange={(e) => setForm((f) => ({ ...f, isPublished: e.target.value === 'true' }))} options={[{ value: 'true', label: 'Publish to students' }, { value: 'false', label: 'Unpublish' }]} />
      </div>
    </Modal>
  );
}

/* ---------------------------- Assignments ---------------------------- */
function SubmissionsModal({ assignment, onClose }) {
  const { data, loading, reload } = useFetch(`/admin/assignments/${assignment._id}/submissions`);
  const [grading, setGrading] = useState({});
  const save = async (sub) => {
    const g = grading[sub._id] || {};
    try {
      await api.patch(`/admin/assignments/${assignment._id}/submissions/${sub._id}`, { marks: g.marks ?? sub.marks, feedback: g.feedback ?? sub.feedback });
      toast.success('Saved');
      reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <Modal open onClose={onClose} title={`Submissions — ${assignment.title}`} size="xl">
      {loading && !data ? <PageLoader className="py-10" /> : !data?.submissions?.length ? <p className="py-8 text-center text-sm text-slate-500">No submissions yet.</p> : (
        <div className="divide-y divide-slate-100">
          {data.submissions.map((s) => (
            <div key={s._id} className="grid items-end gap-3 py-4 md:grid-cols-12">
              <div className="md:col-span-4">
                <p className="font-medium text-primary-900">{s.student?.rollNumber} — {s.student?.name}</p>
                <p className="text-xs text-slate-500">Submitted {formatDateTime(s.submittedAt)}{new Date(s.submittedAt) > new Date(data.dueDate) ? ' · late' : ''}</p>
                <button type="button" className="mt-1 flex items-center gap-1 text-xs font-semibold text-primary-700" onClick={() => openProtectedFile(`/admin/assignments/${assignment._id}/submissions/${s._id}/file`).catch((e) => toast.error(errorMessage(e)))}>
                  <FileText className="h-3.5 w-3.5" />{s.originalName || 'View file'}
                </button>
              </div>
              <Input className="md:col-span-2" label={`Marks /${data.totalMarks}`} type="number" min="0" max={data.totalMarks} defaultValue={s.marks ?? ''} onChange={(e) => setGrading((g) => ({ ...g, [s._id]: { ...g[s._id], marks: e.target.value } }))} />
              <Input className="md:col-span-4" label="Feedback" defaultValue={s.feedback || ''} onChange={(e) => setGrading((g) => ({ ...g, [s._id]: { ...g[s._id], feedback: e.target.value } }))} />
              <button type="button" className="btn-primary md:col-span-2" onClick={() => save(s)}>Save</button>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}

/* ------------------------------ Page ------------------------------ */
export default function ResourcePage() {
  const { resource } = useParams();
  const { user } = useAuth();
  const config = RESOURCES[resource];
  const [modal, setModal] = useState(null);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);

  if (!config) return <NotFound />;
  const perm = config.permission || config.key;
  if (!canAccess(user.role, perm)) return <Navigate to={dashBase(user.role)} replace />;
  const writable = canWrite(user.role, perm);

  let toolbar = null;
  let rowActions;
  if (resource === 'merit-lists' && writable) toolbar = <button type="button" className="btn-gold" onClick={() => setModal({ type: 'merit' })}><Sparkles className="h-4 w-4" />Generate from applications</button>;
  if (resource === 'results' && writable) toolbar = <button type="button" className="btn-gold" onClick={() => setModal({ type: 'publish' })}><Megaphone className="h-4 w-4" />Publish results</button>;
  if (resource === 'attendance') toolbar = <Link to={`${dashBase(user.role)}/attendance/mark`} className="btn-gold"><CalendarCheck className="h-4 w-4" />Mark attendance</Link>;
  if (resource === 'students' && writable) {
    rowActions = (row) => <button type="button" className="btn-icon h-8 w-8" title="Portal account" onClick={() => setModal({ type: 'account', row })} aria-label="Portal account"><KeyRound className="h-4 w-4" /></button>;
  }
  if (resource === 'assignments') {
    rowActions = (row) => <button type="button" className="btn-icon h-8 w-8" title="Submissions" onClick={() => setModal({ type: 'subs', row })} aria-label="View submissions"><Users className="h-4 w-4" /></button>;
  }
  if (resource === 'documents') {
    rowActions = (row) => <a href={assetUrl(row.fileUrl)} target="_blank" rel="noopener noreferrer" className="btn-icon h-8 w-8" aria-label="Open file"><Download className="h-4 w-4" /></a>;
  }
  if (resource === 'merit-lists') {
    rowActions = (row) => (row.isPublished ? <a href={`/admissions/merit-lists/${row._id}`} target="_blank" rel="noopener noreferrer" className="btn-icon h-8 w-8" aria-label="View on website"><StatusBadge status="true" label="Live" /></a> : null);
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="font-display text-3xl font-bold">{config.title}</h2>
        {config.description && <p className="mt-1 text-sm text-slate-500">{config.description}</p>}
      </div>
      <ResourceManager key={`${resource}-${version}`} config={config} toolbar={toolbar} rowActions={rowActions} />
      {modal?.type === 'account' && <PortalAccountModal student={modal.row} onClose={() => setModal(null)} onSaved={refresh} />}
      {modal?.type === 'merit' && <GenerateMeritModal onClose={() => setModal(null)} onDone={refresh} />}
      {modal?.type === 'publish' && <PublishResultsModal onClose={() => setModal(null)} onDone={refresh} />}
      {modal?.type === 'subs' && <SubmissionsModal assignment={modal.row} onClose={() => setModal(null)} />}
    </div>
  );
}
