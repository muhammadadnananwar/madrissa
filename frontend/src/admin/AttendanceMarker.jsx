import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, CheckCheck, Save } from 'lucide-react';
import { Select } from '../components/form';
import { EmptyState, ErrorState, PageLoader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import api, { errorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { dashBase } from '../utils/roles';

const STATUSES = [
  ['present', 'P', 'bg-emerald-500'],
  ['absent', 'A', 'bg-red-500'],
  ['late', 'L', 'bg-amber-500'],
  ['leave', 'LV', 'bg-sky-500'],
];

export default function AttendanceMarker() {
  const { user } = useAuth();
  const { data: courses } = useFetch('/admin/courses', { limit: 100, isActive: true });
  const [course, setCourse] = useState('');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const roster = useFetch(course && date ? '/admin/attendance/roster' : null, { course, date }, { keepPrevious: false });
  const [marks, setMarks] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setMarks(Object.fromEntries((roster.data || []).map((s) => [s._id, s.status || ''])));
  }, [roster.data]);

  const all = (status) => setMarks(Object.fromEntries((roster.data || []).map((s) => [s._id, status])));
  const save = async () => {
    const records = Object.entries(marks).filter(([, s]) => s).map(([student, status]) => ({ student, status }));
    if (!records.length) { toast.error('Mark at least one student'); return; }
    setSaving(true);
    try {
      const { data } = await api.post('/admin/attendance/bulk', { course, date, records });
      toast.success(data.message);
      roster.reload();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };
  const counts = STATUSES.map(([s]) => [s, Object.values(marks).filter((m) => m === s).length]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-3xl font-bold">Mark Attendance</h2>
        <Link to={`${dashBase(user.role)}/attendance`} className="btn-outline btn-sm"><ArrowLeft className="h-4 w-4" />Attendance records</Link>
      </div>
      <div className="card grid gap-4 p-5 sm:grid-cols-3">
        <Select label="Course" className="sm:col-span-2" value={course} onChange={(e) => setCourse(e.target.value)} placeholder="Select course"
          options={(courses || []).map((c) => ({ value: c._id, label: `${c.code} — ${c.title}${c.term ? ` (${c.term})` : ''}` }))} />
        <div>
          <label className="label" htmlFor="att-date">Date</label>
          <input id="att-date" type="date" className="input" value={date} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} />
        </div>
      </div>

      {!course ? <EmptyState title="Select a course" description="Choose a course and date to load the class roster." /> : roster.loading ? <PageLoader /> : roster.error ? <ErrorState message={roster.error} onRetry={roster.reload} /> : !roster.data?.length ? (
        <EmptyState title="No students registered" description="Register students in this course from Students > Registered courses." />
      ) : (
        <div className="card overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 p-4">
            <div className="flex flex-wrap gap-3 text-xs">{counts.map(([s, c]) => <span key={s} className="capitalize text-slate-600">{s}: <b>{c}</b></span>)}</div>
            <div className="flex gap-2">
              <button type="button" className="btn-outline btn-sm" onClick={() => all('present')}><CheckCheck className="h-4 w-4" />All present</button>
              <button type="button" className="btn-primary btn-sm" onClick={save} disabled={saving}>{saving ? <Spinner className="h-4 w-4" /> : <Save className="h-4 w-4" />}Save</button>
            </div>
          </div>
          <ul className="divide-y divide-slate-100">
            {roster.data.map((s) => (
              <li key={s._id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div><p className="font-medium text-primary-900">{s.name}</p><p className="text-xs text-slate-500">{s.rollNumber}</p></div>
                <div className="flex gap-2" role="radiogroup" aria-label={`Attendance for ${s.name}`}>
                  {STATUSES.map(([status, short, color]) => (
                    <button key={status} type="button" role="radio" aria-checked={marks[s._id] === status} title={status}
                      onClick={() => setMarks((m) => ({ ...m, [s._id]: status }))}
                      className={`h-10 min-w-12 rounded-xl px-3 text-sm font-semibold transition ${marks[s._id] === status ? `${color} text-white shadow-soft` : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                      {short}
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
