import { useState } from 'react';
import { Link, useOutletContext, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  AlertCircle, ArrowLeft, ArrowRight, Bell, BookOpen, CalendarCheck, CheckCheck, Clock, Download, FileBarChart, FileText, MapPin, Printer, Receipt, Upload, User,
} from 'lucide-react';
import AccountSettings from '../components/AccountSettings';
import { Input } from '../components/form';
import { AsyncBlock, EmptyState, ErrorState, Img, PageLoader, Spinner, StatusBadge } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import api, { assetUrl, errorMessage } from '../services/api';
import { formatDate, formatDateTime, formatMoney, timeAgo, titleCase } from '../utils/format';

const Panel = ({ title, action, children, className = '' }) => (
  <section className={`card p-6 ${className}`}>
    {(title || action) && <div className="mb-4 flex items-center justify-between gap-3"><h2 className="font-sans text-base font-semibold text-primary-900">{title}</h2>{action}</div>}
    {children}
  </section>
);

/* ------------------------------- Dashboard ------------------------------- */
export function StudentDashboard() {
  const { dash } = useOutletContext();
  const { data, loading, error, reload } = useFetch('/student/dashboard');
  const d = data || dash;
  if (!d && loading) return <PageLoader />;
  if (!d && error) return <ErrorState message={error} onRetry={reload} />;
  const s = d.stats;
  const cards = [
    [BookOpen, 'Registered courses', s.courses, '/student/courses'],
    [CalendarCheck, 'Attendance', s.attendancePercentage !== null ? `${s.attendancePercentage}%` : '—', '/student/attendance'],
    [FileBarChart, 'CGPA', d.student.cgpa ?? '—', '/student/results'],
    [Receipt, 'Outstanding fee', formatMoney(s.outstandingFees), '/student/fees'],
  ];
  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-primary-900 to-primary-700 p-6 text-white sm:p-8">
        <img src="/logo.svg" alt="" className="absolute -end-4 -top-6 h-44 opacity-10" />
        <p className="text-sm text-primary-200">Assalam-o-Alaikum,</p>
        <h2 className="mt-1 font-display text-3xl font-bold text-white">{d.student.name}</h2>
        <p className="mt-1 text-sm text-primary-100">{d.student.rollNumber} · Semester {d.student.semester}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(([Icon, label, value, to]) => (
          <Link key={label} to={to} className="card card-hover flex items-center gap-4 p-5">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-50 text-primary-700"><Icon className="h-6 w-6" /></span>
            <div><p className="text-xl font-bold text-primary-900">{value}</p><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p></div>
          </Link>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Upcoming assignments" action={<Link to="/student/assignments" className="text-sm font-semibold text-primary-700">View all</Link>}>
          {d.upcomingAssignments.length ? (
            <ul className="divide-y divide-slate-100">
              {d.upcomingAssignments.map((a) => (
                <li key={a._id} className="flex items-center justify-between gap-3 py-3">
                  <div><p className="text-sm font-medium text-primary-900">{a.title}</p><p className="text-xs text-slate-500">{a.course?.code} · due {formatDateTime(a.dueDate)}</p></div>
                  <Clock className="h-4 w-4 text-gold-500" />
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-slate-500">No upcoming assignments.</p>}
        </Panel>
        <Panel title="Pending fee challans" action={<Link to="/student/fees" className="text-sm font-semibold text-primary-700">View all</Link>}>
          {d.pendingFees.length ? (
            <ul className="divide-y divide-slate-100">
              {d.pendingFees.map((f) => (
                <li key={f._id} className="flex items-center justify-between gap-3 py-3">
                  <div><p className="text-sm font-medium text-primary-900">{f.term} · {f.challanNumber}</p><p className="text-xs text-slate-500">Due {formatDate(f.dueDate)}</p></div>
                  <Link to={`/student/fees/${f._id}`} className="btn-outline btn-sm">Challan</Link>
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-slate-500">No pending fees. 🎉</p>}
        </Panel>
      </div>
      {s.unreadNotifications > 0 && (
        <Link to="/student/notifications" className="card card-hover flex items-center justify-between bg-gold-50 p-5">
          <span className="flex items-center gap-3 text-sm font-semibold text-primary-900"><Bell className="h-5 w-5 text-gold-600" />You have {s.unreadNotifications} unread notification{s.unreadNotifications > 1 ? 's' : ''}</span>
          <ArrowRight className="h-5 w-5 text-gold-600" />
        </Link>
      )}
    </div>
  );
}

/* -------------------------------- Profile -------------------------------- */
export function StudentProfile() {
  const { data: s, loading, error, reload } = useFetch('/student/profile');
  const [edit, setEdit] = useState(null);
  const [saving, setSaving] = useState(false);
  if (loading && !s) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  const save = async () => {
    setSaving(true);
    try {
      await api.put('/student/profile', edit);
      toast.success('Contact details updated');
      setEdit(null);
      reload();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };
  const rows = [
    ['Roll number', s.rollNumber], ['Program', s.program?.title], ['Department', s.department?.name || s.program?.department?.name], ['Session', s.session],
    ['Semester', s.semester], ['Section', s.section], ['Shift', titleCase(s.shift || '')], ['Status', titleCase(s.status)],
    ["Father's name", s.fatherName], ['Date of birth', formatDate(s.dateOfBirth)], ['Gender', titleCase(s.gender || '')], ['Email', s.user?.email || s.email],
  ];
  return (
    <div className="space-y-6">
      <div className="card flex flex-col items-center gap-6 p-6 sm:flex-row">
        <Img src={s.photo} alt={s.name} className="h-28 w-28 rounded-full border-4 border-gold-300 object-cover" fallbackClass="rounded-full" />
        <div className="text-center sm:text-start">
          <h2 className="font-display text-3xl font-bold">{s.name}</h2>
          <p className="text-slate-500">{s.rollNumber} · {s.program?.title}</p>
          <div className="mt-2"><StatusBadge status={s.status} /></div>
        </div>
      </div>
      <Panel title="Academic & personal information">
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map(([k, v]) => <div key={k}><dt className="text-xs font-semibold uppercase tracking-wider text-slate-400">{k}</dt><dd className="mt-0.5 text-sm text-slate-800">{v || '—'}</dd></div>)}
        </dl>
      </Panel>
      <Panel title="Contact details" action={!edit && <button type="button" className="btn-outline btn-sm" onClick={() => setEdit({ phone: s.phone || '', address: s.address || '', city: s.city || '', guardian: { name: s.guardian?.name || '', relation: s.guardian?.relation || '', phone: s.guardian?.phone || '' } })}>Edit</button>}>
        {edit ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Phone" value={edit.phone} onChange={(e) => setEdit((x) => ({ ...x, phone: e.target.value }))} />
            <Input label="City" value={edit.city} onChange={(e) => setEdit((x) => ({ ...x, city: e.target.value }))} />
            <Input label="Address" className="sm:col-span-2" value={edit.address} onChange={(e) => setEdit((x) => ({ ...x, address: e.target.value }))} />
            <Input label="Guardian name" value={edit.guardian.name} onChange={(e) => setEdit((x) => ({ ...x, guardian: { ...x.guardian, name: e.target.value } }))} />
            <Input label="Guardian phone" value={edit.guardian.phone} onChange={(e) => setEdit((x) => ({ ...x, guardian: { ...x.guardian, phone: e.target.value } }))} />
            <div className="flex gap-2 sm:col-span-2">
              <button type="button" className="btn-primary" onClick={save} disabled={saving}>{saving && <Spinner className="h-4 w-4" />}Save</button>
              <button type="button" className="btn-outline" onClick={() => setEdit(null)}>Cancel</button>
            </div>
          </div>
        ) : (
          <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[['Phone', s.phone], ['Address', [s.address, s.city].filter(Boolean).join(', ')], ['Guardian', s.guardian?.name], ['Guardian phone', s.guardian?.phone]].map(([k, v]) => (
              <div key={k}><dt className="text-xs font-semibold uppercase tracking-wider text-slate-400">{k}</dt><dd className="mt-0.5 text-sm text-slate-800">{v || '—'}</dd></div>
            ))}
          </dl>
        )}
        <p className="mt-4 text-xs text-slate-400">To correct your name, CNIC or academic details, contact the registrar office.</p>
      </Panel>
    </div>
  );
}

/* -------------------------------- Courses -------------------------------- */
export function StudentCourses() {
  const { data, loading, error, reload } = useFetch('/student/courses');
  const credits = (data || []).reduce((s, c) => s + (c.creditHours || 0), 0);
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: BookOpen, title: 'No registered courses', description: 'Your courses will appear here once registered by the department.' }}>
      <p className="mb-4 text-sm text-slate-500">{data?.length} courses · {credits} credit hours</p>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data?.map((c) => (
          <div key={c._id} className="card p-6">
            <div className="flex items-start justify-between"><span className="badge bg-primary-50 font-mono text-primary-700">{c.code}</span><span className="text-xs text-slate-500">{c.creditHours} Cr.Hrs</span></div>
            <h3 className="mt-3 font-sans text-lg font-semibold text-primary-900">{c.title}</h3>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-600"><User className="h-4 w-4" />{c.instructor?.name || 'Instructor TBA'}</p>
            {c.term && <p className="mt-1 text-xs text-slate-400">{c.term}</p>}
            {c.schedule?.length > 0 && (
              <ul className="mt-4 space-y-1 border-t border-slate-100 pt-3 text-xs text-slate-600">
                {c.schedule.map((s, i) => (
                  // eslint-disable-next-line react/no-array-index-key
                  <li key={i} className="flex justify-between"><span>{s.day}</span><span>{s.startTime}–{s.endTime} · {s.room}</span></li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </AsyncBlock>
  );
}

/* ------------------------------- Timetable ------------------------------- */
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
export function StudentTimetable() {
  const { data, loading, error, reload } = useFetch('/student/timetable');
  const today = new Date().toLocaleString('en', { weekday: 'long' });
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: Clock, title: 'No timetable available' }}>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {DAYS.map((day) => {
          const slots = (data || []).filter((s) => s.day === day);
          return (
            <div key={day} className={`card p-5 ${day === today ? 'ring-2 ring-gold-400' : ''}`}>
              <h3 className="flex items-center justify-between font-sans text-base font-semibold">{day}{day === today && <span className="badge bg-gold-100 text-gold-700">Today</span>}</h3>
              {slots.length ? (
                <ul className="mt-4 space-y-3">
                  {slots.map((s, i) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <li key={i} className="rounded-xl border-s-4 border-primary-500 bg-primary-50/50 p-3">
                      <p className="text-xs font-semibold text-primary-700">{s.startTime} – {s.endTime}</p>
                      <p className="font-medium text-primary-900">{s.course.code} · {s.course.title}</p>
                      <p className="mt-1 flex flex-wrap gap-3 text-xs text-slate-500"><span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{s.room || '—'}</span>{s.instructor && <span>{s.instructor}</span>}</p>
                    </li>
                  ))}
                </ul>
              ) : <p className="mt-4 text-sm text-slate-400">No classes</p>}
            </div>
          );
        })}
      </div>
    </AsyncBlock>
  );
}

/* ------------------------------- Attendance ------------------------------ */
export function StudentAttendance() {
  const [course, setCourse] = useState('');
  const { data, loading, error, reload } = useFetch('/student/attendance', { course });
  if (loading && !data) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  return (
    <div className="space-y-6">
      {data.summary.length ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.summary.map((s) => {
            const low = s.percentage < 75;
            return (
              <button key={s.course._id} type="button" onClick={() => setCourse(course === s.course._id ? '' : s.course._id)}
                className={`card p-5 text-start transition ${course === s.course._id ? 'ring-2 ring-primary-500' : 'hover:shadow-lift'}`}>
                <div className="flex items-center justify-between"><span className="font-mono text-xs text-slate-500">{s.course.code}</span><span className={`text-2xl font-bold ${low ? 'text-red-600' : 'text-emerald-600'}`}>{s.percentage}%</span></div>
                <p className="mt-1 font-medium text-primary-900">{s.course.title}</p>
                <div className="mt-3 h-2 rounded-full bg-slate-100"><div className={`h-2 rounded-full ${low ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${s.percentage}%` }} /></div>
                <p className="mt-2 text-xs text-slate-500">P {s.present} · L {s.late} · A {s.absent} · Leave {s.leave} · Total {s.total}</p>
                {low && <p className="mt-2 flex items-center gap-1 text-xs font-medium text-red-600"><AlertCircle className="h-3.5 w-3.5" />Below 75%</p>}
              </button>
            );
          })}
        </div>
      ) : <EmptyState icon={CalendarCheck} title="No attendance recorded yet" />}
      {data.records.length > 0 && (
        <Panel title={course ? 'Records for selected course' : 'Recent records'} action={course && <button type="button" className="text-sm font-semibold text-primary-700" onClick={() => setCourse('')}>Show all</button>}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px]">
              <thead><tr className="border-b border-slate-100"><th className="table-th">Date</th><th className="table-th">Course</th><th className="table-th">Status</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {data.records.map((r) => <tr key={r._id}><td className="table-td">{formatDate(r.date, { weekday: 'short', day: 'numeric', month: 'short' })}</td><td className="table-td">{r.course?.code}</td><td className="table-td"><StatusBadge status={r.status} /></td></tr>)}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}

/* -------------------------------- Results -------------------------------- */
export function StudentResults() {
  const { data, loading, error, reload } = useFetch('/student/results');
  if (loading && !data) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  return (
    <div className="space-y-6">
      <div className="card flex items-center justify-between bg-primary-900 p-6 text-white">
        <div><p className="text-xs uppercase tracking-widest text-primary-200">Cumulative GPA</p><p className="font-display text-5xl font-bold text-gold-300">{data.cgpa ?? '—'}</p></div>
        <button type="button" onClick={() => window.print()} className="btn-ghost-light no-print"><Printer className="h-4 w-4" />Print</button>
      </div>
      {data.terms.length ? data.terms.map((t) => (
        <Panel key={t.term} title={t.term} action={<span className="badge bg-gold-50 text-gold-700">GPA {t.gpa ?? '—'}</span>}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px]">
              <thead><tr className="border-b border-slate-100"><th className="table-th">Course</th><th className="table-th">Cr.Hrs</th><th className="table-th">Sessional</th><th className="table-th">Mid</th><th className="table-th">Final</th><th className="table-th">Total</th><th className="table-th">Grade</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {t.results.map((r) => (
                  <tr key={r._id}>
                    <td className="table-td"><span className="font-mono text-xs text-slate-500">{r.course?.code}</span><br /><span className="font-medium text-primary-900">{r.course?.title}</span></td>
                    <td className="table-td">{r.creditHours}</td><td className="table-td">{r.marks?.sessional}</td><td className="table-td">{r.marks?.midterm}</td><td className="table-td">{r.marks?.final}</td>
                    <td className="table-td font-semibold">{r.obtainedMarks}/{r.totalMarks}</td>
                    <td className="table-td"><span className={`badge font-bold ${r.grade === 'F' ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>{r.grade}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )) : <EmptyState icon={FileBarChart} title="No results published yet" description="Results appear here once published by the examination office." />}
    </div>
  );
}

/* ---------------------------------- Fees --------------------------------- */
export function StudentFees() {
  const { data, loading, error, reload } = useFetch('/student/fees');
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: Receipt, title: 'No fee challans issued' }}>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[640px]">
          <thead className="bg-slate-50/70"><tr><th className="table-th">Challan #</th><th className="table-th">Term</th><th className="table-th">Amount</th><th className="table-th">Due date</th><th className="table-th">Status</th><th className="table-th" /></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {data?.map((f) => (
              <tr key={f._id}>
                <td className="table-td font-mono">{f.challanNumber}</td><td className="table-td">{f.term}</td>
                <td className="table-td font-semibold">{formatMoney(f.totalAmount, f.currency)}</td><td className="table-td">{formatDate(f.dueDate)}</td>
                <td className="table-td"><StatusBadge status={f.status} />{f.paidAt && <span className="block text-xs text-slate-400">Paid {formatDate(f.paidAt)}</span>}</td>
                <td className="table-td text-end"><Link to={`/student/fees/${f._id}`} className="btn-outline btn-sm"><Printer className="h-4 w-4" />Challan</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-xs text-slate-500">Payment status is updated by the Accounts Office after your payment is verified.</p>
    </AsyncBlock>
  );
}

export function FeeChallan() {
  const { id } = useParams();
  const { settings } = useSite();
  const { data, loading, error, reload } = useFetch(`/student/fees/${id}`);
  if (loading && !data) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  const { fee, student } = data;
  const copies = ['Student copy', 'Bank copy', 'University copy'];
  return (
    <div className="space-y-4">
      <div className="no-print flex items-center justify-between">
        <Link to="/student/fees" className="btn-outline btn-sm"><ArrowLeft className="h-4 w-4" />Back</Link>
        <button type="button" className="btn-primary btn-sm" onClick={() => window.print()}><Printer className="h-4 w-4" />Print challan</button>
      </div>
      <div className="grid gap-4 lg:grid-cols-3 print:grid-cols-3">
        {copies.map((copy) => (
          <div key={copy} className="card break-inside-avoid border-2 border-dashed border-slate-200 p-5 text-sm print:shadow-none">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <img src="/logo.svg" alt="" className="h-12" />
              <div><p className="font-display text-base font-bold leading-tight text-primary-900">{settings?.universityName}</p><p className="text-[10px] uppercase tracking-widest text-gold-600">{copy}</p></div>
            </div>
            <dl className="mt-3 space-y-1.5">
              {[['Challan #', fee.challanNumber], ['Name', student.name], ['Roll no.', student.rollNumber], ["Father's name", student.fatherName], ['Program', student.program?.title], ['Term', fee.term], ['Issue date', formatDate(fee.issueDate)], ['Due date', formatDate(fee.dueDate)]].map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2"><dt className="text-slate-500">{k}</dt><dd className="text-end font-medium text-slate-800">{v || '—'}</dd></div>
              ))}
            </dl>
            <table className="mt-3 w-full border-t border-slate-100 text-xs">
              <tbody>
                {fee.items.map((i) => <tr key={i.label}><td className="py-1">{i.label}</td><td className="py-1 text-end">{formatMoney(i.amount, fee.currency)}</td></tr>)}
                <tr className="border-t border-slate-200 font-bold"><td className="py-1.5">Total</td><td className="py-1.5 text-end">{formatMoney(fee.totalAmount, fee.currency)}</td></tr>
              </tbody>
            </table>
            {fee.bankDetails && <p className="mt-3 rounded-lg bg-slate-50 p-2 text-xs text-slate-600">{fee.bankDetails}</p>}
            <div className="mt-3 flex items-center justify-between"><StatusBadge status={fee.status} />{fee.remarks && <span className="text-[10px] text-slate-400">{fee.remarks}</span>}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------- Assignments ------------------------------ */
function SubmitButton({ assignment, onDone }) {
  const [busy, setBusy] = useState(false);
  const overdue = new Date(assignment.dueDate) < new Date() && !assignment.allowLateSubmission;
  const graded = assignment.submission?.marks !== undefined && assignment.submission?.marks !== null;
  const upload = async (file) => {
    if (!file) return;
    if (file.type !== 'application/pdf') { toast.error('Please upload a PDF file'); return; }
    if (file.size > 5 * 1048576) { toast.error('File must be smaller than 5 MB'); return; }
    const fd = new FormData();
    fd.append('file', file);
    setBusy(true);
    try {
      await api.post(`/student/assignments/${assignment._id}/submit`, fd);
      toast.success('Assignment submitted');
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  if (graded || overdue) return null;
  return (
    <label className={`btn-primary btn-sm cursor-pointer ${busy ? 'pointer-events-none opacity-60' : ''}`}>
      {busy ? <Spinner className="h-4 w-4" /> : <Upload className="h-4 w-4" />}{assignment.submission ? 'Resubmit' : 'Submit PDF'}
      <input type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ''; }} />
    </label>
  );
}

export function StudentAssignments() {
  const { data, loading, error, reload } = useFetch('/student/assignments');
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: FileText, title: 'No assignments yet' }}>
      <div className="space-y-4">
        {data?.map((a) => {
          const overdue = new Date(a.dueDate) < new Date();
          return (
            <div key={a._id} className="card flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="badge bg-primary-50 font-mono text-primary-700">{a.course?.code}</span>
                  {a.submission ? (a.submission.marks !== undefined && a.submission.marks !== null
                    ? <span className="badge bg-emerald-50 text-emerald-700">Graded: {a.submission.marks}/{a.totalMarks}</span>
                    : <span className="badge bg-sky-50 text-sky-700">Submitted</span>)
                    : overdue ? <span className="badge bg-red-50 text-red-700">Overdue</span> : <span className="badge bg-amber-50 text-amber-700">Pending</span>}
                </div>
                <h3 className="mt-2 font-sans text-lg font-semibold text-primary-900">{a.title}</h3>
                {a.description && <p className="mt-1 text-sm text-slate-600">{a.description}</p>}
                <p className="mt-2 text-xs text-slate-500">Due {formatDateTime(a.dueDate)} · {a.totalMarks} marks{a.submission ? ` · submitted ${timeAgo(a.submission.submittedAt)} (${a.submission.originalName})` : ''}</p>
                {a.submission?.feedback && <p className="mt-2 rounded-lg bg-slate-50 p-2 text-sm text-slate-700"><b>Feedback:</b> {a.submission.feedback}</p>}
              </div>
              <div className="flex shrink-0 gap-2">
                {a.attachment && <a href={assetUrl(a.attachment)} target="_blank" rel="noopener noreferrer" className="btn-outline btn-sm"><Download className="h-4 w-4" />Brief</a>}
                <SubmitButton assignment={a} onDone={reload} />
              </div>
            </div>
          );
        })}
      </div>
    </AsyncBlock>
  );
}

/* ------------------------------ Notifications ----------------------------- */
export function StudentNotifications() {
  const { data, loading, error, reload } = useFetch('/student/notifications');
  const { reloadDash } = useOutletContext();
  const markRead = async (id) => {
    try {
      await api.patch(`/student/notifications/${id}/read`);
      reload();
      reloadDash?.();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const unread = (data || []).filter((n) => !n.isRead).length;
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: Bell, title: 'No notifications' }}>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-slate-500">{unread} unread</p>
        {unread > 0 && <button type="button" className="btn-outline btn-sm" onClick={() => markRead('all')}><CheckCheck className="h-4 w-4" />Mark all as read</button>}
      </div>
      <div className="space-y-3">
        {data?.map((n) => (
          <div key={n._id} className={`card flex gap-4 p-5 ${n.isRead ? 'opacity-75' : 'border-s-4 border-s-gold-400'}`}>
            <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${n.isRead ? 'bg-slate-300' : 'bg-gold-500'}`} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2"><p className="font-semibold text-primary-900">{n.title}</p><StatusBadge status={n.type} /></div>
              <p className="mt-1 text-sm text-slate-600">{n.message}</p>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                <span>{timeAgo(n.createdAt)}</span>
                {n.link && (n.link.startsWith('/') ? <Link to={n.link} className="font-semibold text-primary-700">Open</Link> : <a href={n.link} target="_blank" rel="noopener noreferrer" className="font-semibold text-primary-700">Open</a>)}
                {!n.isRead && <button type="button" className="font-semibold text-primary-700" onClick={() => markRead(n._id)}>Mark as read</button>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </AsyncBlock>
  );
}

/* -------------------------------- Documents ------------------------------- */
export function StudentDocuments() {
  const { data, loading, error, reload } = useFetch('/student/documents');
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: FileText, title: 'No documents available' }}>
      <div className="grid gap-4 md:grid-cols-2">
        {data?.map((d) => (
          <div key={d._id} className="card flex items-center gap-4 p-5">
            <span className="flex h-14 w-12 shrink-0 items-center justify-center rounded-lg bg-red-50 text-xs font-bold text-red-600">PDF</span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold text-primary-900">{d.title}</p>
              <p className="truncate text-xs text-slate-500">{titleCase(d.category)}{d.audience === 'students' ? ' · Students only' : ''}</p>
            </div>
            <a href={assetUrl(d.fileUrl)} target="_blank" rel="noopener noreferrer" className="btn-primary btn-sm"><Download className="h-4 w-4" /></a>
          </div>
        ))}
      </div>
    </AsyncBlock>
  );
}

export function StudentAccount() {
  return <AccountSettings allowNameEdit={false} />;
}
