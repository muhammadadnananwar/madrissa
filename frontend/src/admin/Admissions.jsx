import { useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Copy, Eye, FileText, GraduationCap, KeyRound, Trash2, UserPlus } from 'lucide-react';
import ResourceManager from './ResourceManager';
import { ConfirmDialog, ErrorState, Modal, PageLoader, Spinner, StatusBadge } from '../components/ui';
import { Select, Textarea } from '../components/form';
import { useFetch } from '../hooks/useFetch';
import { useAuth } from '../context/AuthContext';
import api, { errorMessage, openProtectedFile } from '../services/api';
import { formatDate, formatDateTime, titleCase } from '../utils/format';
import { canWrite, dashBase } from '../utils/roles';

const STATUSES = ['submitted', 'under_review', 'documents_required', 'approved', 'waitlisted', 'rejected', 'enrolled'];
const opt = (a) => a.map((v) => ({ value: v, label: titleCase(v) }));

const CONFIG = {
  key: 'admissions', title: 'Applications', singular: 'Application', endpoint: '/admin/admissions', labelKey: 'applicationNumber',
  creatable: false, editable: false,
  columns: [
    { key: 'applicationNumber', label: 'Application #', type: 'title', sortable: true },
    { key: 'personal.fullName', label: 'Applicant', sortable: true },
    { key: 'program', label: 'Program', value: (r) => r.program?.code || r.program?.title },
    { key: 'aggregate', label: 'Aggregate', value: (r) => (r.aggregate != null ? `${r.aggregate}%` : '—'), sortable: true },
    { key: 'createdAt', label: 'Submitted', type: 'date', sortable: true },
    { key: 'status', label: 'Status', type: 'status' },
  ],
  filters: [
    { key: 'status', label: 'Status', options: opt(STATUSES) },
    { key: 'program', label: 'Program', endpoint: '/admin/programs', optionLabel: 'title' },
  ],
};

export function AdmissionsList() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const base = dashBase(user.role);
  return (
    <ResourceManager config={CONFIG} initialFilters={params.get('status') ? { status: params.get('status') } : {}}
      rowActions={(row) => (
        <button type="button" className="btn-icon h-8 w-8" onClick={() => navigate(`${base}/admissions/${row._id}`)} aria-label="Review application"><Eye className="h-4 w-4" /></button>
      )} />
  );
}

function Section({ title, children }) {
  return (
    <div className="card p-6">
      <h3 className="mb-4 font-sans text-base font-semibold text-primary-900">{title}</h3>
      {children}
    </div>
  );
}

const Row = ({ label, value }) => (
  <div><dt className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</dt><dd className="mt-0.5 text-sm text-slate-800">{value || '—'}</dd></div>
);

export function AdmissionDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const writable = canWrite(user.role, 'admissions');
  const base = dashBase(user.role);
  const { data: a, loading, error, reload } = useFetch(`/admin/admissions/${id}`);
  const [status, setStatus] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [notes, setNotes] = useState(null);
  const [saving, setSaving] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [credentials, setCredentials] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  if (loading && !a) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  const p = a.personal;
  const currentStatus = status ?? a.status;
  const currentNotes = notes ?? a.internalNotes ?? '';

  const saveStatus = async () => {
    setSaving(true);
    try {
      await api.patch(`/admin/admissions/${id}/status`, { status: currentStatus, remarks, internalNotes: currentNotes });
      toast.success('Application updated');
      setRemarks('');
      setStatus(null);
      reload();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const enroll = async () => {
    setEnrolling(true);
    try {
      const { data } = await api.post(`/admin/admissions/${id}/enroll`);
      setCredentials(data.data.credentials);
      toast.success('Student account created');
      reload();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setEnrolling(false);
    }
  };

  const remove = async () => {
    setDeleting(true);
    try {
      await api.delete(`/admin/admissions/${id}`);
      toast.success('Application deleted');
      navigate(`${base}/admissions`);
    } catch (e) {
      toast.error(errorMessage(e));
      setDeleting(false);
    }
  };

  const viewDoc = (doc) => openProtectedFile(`/admin/admissions/${id}/documents/${doc._id}`).catch((e) => toast.error(errorMessage(e)));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to={`${base}/admissions`} className="btn-outline btn-sm"><ArrowLeft className="h-4 w-4" />All applications</Link>
        {writable && !a.student && (
          <button type="button" className="btn btn-sm text-red-600 hover:bg-red-50" onClick={() => setConfirmDelete(true)}><Trash2 className="h-4 w-4" />Delete</button>
        )}
      </div>

      <div className="card flex flex-col gap-4 bg-primary-900 p-6 text-white sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-mono text-sm text-gold-300">{a.applicationNumber}</p>
          <h2 className="mt-1 font-display text-3xl font-bold text-white">{p.fullName}</h2>
          <p className="text-sm text-primary-200">{p.fatherName ? `s/o ${p.fatherName} · ` : ''}{a.program?.title} · {a.session} · submitted {formatDate(a.createdAt)}</p>
        </div>
        <div className="flex items-center gap-4">
          {a.aggregate !== undefined && a.aggregate !== null && <div className="text-end"><p className="text-xs uppercase tracking-wider text-primary-300">Aggregate</p><p className="font-display text-3xl font-bold text-gold-300">{a.aggregate}%</p></div>}
          <StatusBadge status={a.status} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Section title="Applicant details">
            <dl className="grid gap-4 sm:grid-cols-3">
              <Row label="CNIC / B-Form" value={p.cnic} />
              <Row label="Date of birth" value={formatDate(p.dateOfBirth)} />
              <Row label="Gender" value={titleCase(p.gender)} />
              <Row label="Mobile" value={p.phone} />
              <Row label="Home phone" value={p.homePhone} />
              <Row label="Email" value={p.email} />
              <Row label="City / Province" value={[p.city, p.province].filter(Boolean).join(', ')} />
              <Row label="Nationality" value={p.nationality} />
              <div className="sm:col-span-3"><Row label="Permanent address" value={p.address} /></div>
              <div className="sm:col-span-3"><Row label="Temporary address" value={p.temporaryAddress} /></div>
            </dl>
          </Section>

          <Section title="Family & guardian">
            <dl className="grid gap-4 sm:grid-cols-3">
              <Row label="Father's name" value={p.fatherName} />
              <Row label="Father's CNIC" value={p.fatherCnic} />
              <Row label="Father's occupation" value={p.fatherOccupation} />
              <Row label="Guardian" value={a.guardian?.name} />
              <Row label="Guardian's occupation" value={a.guardian?.occupation} />
              <Row label="Guardian's phone" value={p.guardianPhone} />
            </dl>
          </Section>

          <Section title="Educational background">
            <dl className="mb-4 grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-3"><Row label="Qualification & institution" value={a.qualification} /></div>
              <Row label="Hifz / Nazira" value={a.quranStatus && titleCase(a.quranStatus)} />
              <Row label="Previous madrasa" value={a.previousMadrasa} />
            </dl>
            {a.education.length > 0 && <div className="overflow-x-auto">
              <table className="w-full min-w-[560px]">
                <thead><tr className="border-b border-slate-100"><th className="table-th">Level</th><th className="table-th">Degree</th><th className="table-th">Board / Institution</th><th className="table-th">Year</th><th className="table-th">Marks</th><th className="table-th">%</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {a.education.map((e, i) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <tr key={i}>
                      <td className="table-td font-medium">{titleCase(e.level)}</td><td className="table-td">{e.degreeTitle || '—'}</td>
                      <td className="table-td">{[e.board, e.institution].filter(Boolean).join(' / ')}</td><td className="table-td">{e.passingYear}</td>
                      <td className="table-td">{e.totalMarks ? `${e.obtainedMarks}/${e.totalMarks}` : '—'}</td><td className="table-td font-semibold">{e.percentage !== undefined ? `${e.percentage}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>}
          </Section>

          <Section title="Uploaded documents">
            {a.documents.length ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {a.documents.map((d) => (
                  <button key={d._id} type="button" onClick={() => viewDoc(d)} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-start transition hover:border-primary-300 hover:bg-primary-50">
                    <FileText className="h-5 w-5 shrink-0 text-primary-600" />
                    <span className="min-w-0 flex-1"><span className="block text-sm font-medium text-primary-900">{titleCase(d.type)}</span><span className="block truncate text-xs text-slate-500">{d.originalName}</span></span>
                    <Eye className="h-4 w-4 text-slate-400" />
                  </button>
                ))}
              </div>
            ) : <p className="text-sm text-slate-500">No documents uploaded.</p>}
            <p className="mt-3 text-xs text-slate-400">Documents are stored privately and open only for authorised staff.</p>
          </Section>

          <Section title="Status history">
            <ol className="space-y-4">
              {[...a.statusHistory].reverse().map((h) => (
                <li key={h._id} className="flex gap-3">
                  <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-gold-400" />
                  <div>
                    <p className="text-sm font-medium text-primary-900">{titleCase(h.status)} <span className="font-normal text-slate-500">· {formatDateTime(h.at)}{h.changedBy ? ` · ${h.changedBy.name}` : ''}</span></p>
                    {h.remarks && <p className="text-sm text-slate-600">{h.remarks}</p>}
                  </div>
                </li>
              ))}
            </ol>
          </Section>
        </div>

        <div className="space-y-6">
          {writable && a.status !== 'enrolled' && (
            <Section title="Review decision">
              <div className="space-y-4">
                <Select label="Status" value={currentStatus} onChange={(e) => setStatus(e.target.value)} options={opt(STATUSES.filter((s) => s !== 'enrolled'))} />
                <Textarea label="Remarks for applicant" rows={3} value={remarks} onChange={(e) => setRemarks(e.target.value)} hint="Visible to the applicant on the tracking page." />
                <Textarea label="Internal notes" rows={3} value={currentNotes} onChange={(e) => setNotes(e.target.value)} hint="Only visible to staff." />
                <button type="button" className="btn-primary w-full" onClick={saveStatus} disabled={saving}>{saving && <Spinner className="h-4 w-4" />}Save decision</button>
              </div>
            </Section>
          )}
          <Section title="Program choice">
            <dl className="space-y-3">
              <Row label="First choice" value={a.program?.title} />
              <Row label="Second choice" value={a.secondChoice?.title} />
              <Row label="Darjah applied for" value={a.classLevel} />
              <Row label="Residence" value={a.residence === 'day_scholar' ? 'Day scholar (خارج دارالاقامہ)' : 'Dar-ul-Iqama — boarding'} />
              <Row label="Agreed to rules" value={a.rulesAccepted ? 'Yes' : 'No'} />
              <Row label="Reviewed by" value={a.reviewedBy?.name} />
              {a.remarks && <Row label="Current remarks" value={a.remarks} />}
            </dl>
          </Section>
          <Section title="Enrolment">
            {a.student ? (
              <div className="flex items-center gap-3 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">
                <GraduationCap className="h-5 w-5" /> Enrolled as <b>{a.student.rollNumber}</b>
              </div>
            ) : a.status === 'approved' && writable ? (
              <>
                <p className="text-sm text-slate-600">Create a student record and portal login for this approved applicant.</p>
                <button type="button" className="btn-gold mt-4 w-full" onClick={enroll} disabled={enrolling}>{enrolling ? <Spinner className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}Enrol & create account</button>
              </>
            ) : <p className="text-sm text-slate-500">Approve the application to enable enrolment.</p>}
          </Section>
        </div>
      </div>

      <Modal open={Boolean(credentials)} onClose={() => setCredentials(null)} title="Student account created" size="sm"
        footer={<button type="button" className="btn-primary" onClick={() => setCredentials(null)}>Done</button>}>
        {credentials && (
          <div className="space-y-3 text-sm">
            <p className="text-slate-600">Share these credentials with the student securely. The temporary password will not be shown again.</p>
            <div className="space-y-2 rounded-xl bg-primary-50 p-4 font-mono">
              <p>Roll no: <b>{credentials.rollNumber}</b></p>
              <p>Email: <b>{credentials.email}</b></p>
              <p className="flex items-center gap-2"><KeyRound className="h-4 w-4" /> <b>{credentials.temporaryPassword}</b></p>
            </div>
            <button type="button" className="btn-outline btn-sm" onClick={() => navigator.clipboard?.writeText(`Roll: ${credentials.rollNumber}\nEmail: ${credentials.email}\nPassword: ${credentials.temporaryPassword}`).then(() => toast.success('Copied'))}>
              <Copy className="h-4 w-4" />Copy
            </button>
          </div>
        )}
      </Modal>
      <ConfirmDialog open={confirmDelete} onClose={() => setConfirmDelete(false)} onConfirm={remove} loading={deleting} title="Delete application?"
        message={`Application ${a.applicationNumber} and its uploaded documents will be permanently deleted.`} />
    </div>
  );
}
