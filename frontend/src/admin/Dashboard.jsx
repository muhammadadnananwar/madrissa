import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, ArrowRight, BookOpen, Building2, ClipboardList, GraduationCap, Mail, Users } from 'lucide-react';
import { ErrorState, PageLoader, StatusBadge } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useAuth } from '../context/AuthContext';
import { canAccess, dashBase } from '../utils/roles';
import { timeAgo, titleCase } from '../utils/format';

const STATUS_COLORS = {
  submitted: '#0EA5E9', under_review: '#F59E0B', documents_required: '#F97316', approved: '#10B981', rejected: '#EF4444', waitlisted: '#8B5CF6', enrolled: '#3B1E6D',
};

function StatCard({ icon: Icon, label, value, to, accent = 'bg-primary-700', delay }) {
  const body = (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="card card-hover flex items-center gap-4 p-5">
      <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-white ${accent}`}><Icon className="h-6 w-6" /></span>
      <div>
        <p className="text-2xl font-bold text-primary-900">{value ?? '—'}</p>
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
      </div>
    </motion.div>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data, loading, error, reload } = useFetch('/admin/dashboard');
  const base = dashBase(user.role);
  if (loading && !data) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  const { totals, admissions, activities, recentApplications } = data;
  const statusEntries = Object.entries(admissions.byStatus);
  const totalApps = statusEntries.reduce((s, [, c]) => s + c, 0);
  const maxMonth = Math.max(1, ...admissions.monthly.map((m) => m.count));
  const maxProgram = Math.max(1, ...admissions.byProgram.map((p) => p.count));
  const showAdmissions = canAccess(user.role, 'admissions');

  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-primary-900 via-primary-800 to-primary-700 p-6 text-white sm:p-8">
        <img src="/logo.svg" alt="" className="absolute -end-6 -top-6 h-48 opacity-10" />
        <p className="text-sm text-primary-200">Welcome back,</p>
        <h2 className="mt-1 font-display text-3xl font-bold text-white">{user.name}</h2>
        <p className="mt-2 max-w-xl text-sm text-primary-100">Here is an overview of university activity. Use the sidebar to manage admissions, academics and website content.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <StatCard icon={GraduationCap} label="Active students" value={totals.students} to={canAccess(user.role, 'students') ? `${base}/students` : undefined} delay={0} />
        <StatCard icon={Users} label="Faculty" value={totals.faculty} to={canAccess(user.role, 'faculty') ? `${base}/faculty` : undefined} accent="bg-primary-500" delay={0.04} />
        <StatCard icon={BookOpen} label="Programs" value={totals.programs} to={canAccess(user.role, 'programs') ? `${base}/programs` : undefined} accent="bg-primary-600" delay={0.08} />
        <StatCard icon={Building2} label="Departments" value={totals.departments} to={canAccess(user.role, 'departments') ? `${base}/departments` : undefined} accent="bg-primary-800" delay={0.12} />
        <StatCard icon={ClipboardList} label="Pending applications" value={totals.pendingApplications} to={showAdmissions ? `${base}/admissions?status=submitted` : undefined} accent="bg-gold-500" delay={0.16} />
        <StatCard icon={Mail} label="New inquiries" value={totals.newInquiries} to={canAccess(user.role, 'inquiries') ? `${base}/inquiries` : undefined} accent="bg-sky-500" delay={0.2} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="card p-6 xl:col-span-2">
          <div className="flex items-center justify-between">
            <h3 className="font-sans text-base font-semibold">Applications — last 6 months</h3>
            <span className="text-sm text-slate-500">{totalApps} total</span>
          </div>
          <div className="mt-6 flex h-56 items-end gap-3 sm:gap-6" role="img" aria-label="Monthly applications bar chart">
            {admissions.monthly.map((m) => (
              <div key={`${m.label}-${m.year}`} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                <span className="text-xs font-semibold text-primary-800">{m.count}</span>
                <motion.div initial={{ height: 0 }} animate={{ height: `${(m.count / maxMonth) * 100}%` }} transition={{ duration: 0.8, ease: 'easeOut' }}
                  className="w-full max-w-14 rounded-t-xl bg-gradient-to-t from-primary-700 to-primary-500" style={{ minHeight: m.count ? 6 : 2 }} />
                <span className="text-xs text-slate-500">{m.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-sans text-base font-semibold">Applications by status</h3>
          {totalApps ? (
            <>
              <div className="mt-5 flex h-3 overflow-hidden rounded-full bg-slate-100">
                {statusEntries.map(([s, c]) => <div key={s} style={{ width: `${(c / totalApps) * 100}%`, background: STATUS_COLORS[s] }} title={`${titleCase(s)}: ${c}`} />)}
              </div>
              <ul className="mt-5 space-y-2.5">
                {statusEntries.sort((a, b) => b[1] - a[1]).map(([s, c]) => (
                  <li key={s} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: STATUS_COLORS[s] }} />{titleCase(s)}</span>
                    <span className="font-semibold text-primary-900">{c}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : <p className="mt-4 text-sm text-slate-500">No applications yet.</p>}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="card p-6">
          <h3 className="font-sans text-base font-semibold">Top programs by applications</h3>
          <ul className="mt-5 space-y-4">
            {admissions.byProgram.map((p) => (
              <li key={p.program}>
                <div className="flex justify-between text-sm"><span className="truncate pe-3 text-slate-700">{p.program}</span><span className="font-semibold text-primary-900">{p.count}</span></div>
                <div className="mt-1.5 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-gold-400" style={{ width: `${(p.count / maxProgram) * 100}%` }} /></div>
              </li>
            ))}
            {!admissions.byProgram.length && <li className="text-sm text-slate-500">No data yet.</li>}
          </ul>
        </div>

        {showAdmissions && (
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <h3 className="font-sans text-base font-semibold">Recent applications</h3>
              <Link to={`${base}/admissions`} className="text-sm font-semibold text-primary-700">View all</Link>
            </div>
            <ul className="mt-4 divide-y divide-slate-100">
              {recentApplications.map((a) => (
                <li key={a._id}>
                  <Link to={`${base}/admissions/${a._id}`} className="flex items-center justify-between gap-3 py-3 hover:text-primary-700">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-primary-900">{a.personal?.fullName}</p>
                      <p className="text-xs text-slate-500">{a.applicationNumber} · {a.program?.code}</p>
                    </div>
                    <StatusBadge status={a.status} />
                  </Link>
                </li>
              ))}
              {!recentApplications.length && <li className="py-3 text-sm text-slate-500">No applications yet.</li>}
            </ul>
          </div>
        )}

        <div className={`card p-6 ${showAdmissions ? '' : 'xl:col-span-2'}`}>
          <h3 className="flex items-center gap-2 font-sans text-base font-semibold"><Activity className="h-4 w-4 text-gold-500" />Recent activity</h3>
          <ol className="mt-4 space-y-4">
            {activities.map((a) => (
              <li key={a._id} className="flex gap-3">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary-400" />
                <div className="min-w-0">
                  <p className="text-sm text-slate-700">{a.description}</p>
                  <p className="text-xs text-slate-400">{a.userName || 'System'} · {timeAgo(a.createdAt)}</p>
                </div>
              </li>
            ))}
            {!activities.length && <li className="text-sm text-slate-500">No recent activity.</li>}
          </ol>
        </div>
      </div>

      {showAdmissions && (
        <Link to={`${base}/admissions?status=submitted`} className="card card-hover flex items-center justify-between bg-gold-50 p-5">
          <span className="text-sm font-semibold text-primary-900">{totals.pendingApplications} applications are waiting for review</span>
          <ArrowRight className="h-5 w-5 text-gold-600" />
        </Link>
      )}
    </div>
  );
}
