import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Award, CheckCircle2, Circle, FileText, Search } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { Input } from '../components/form';
import { Spinner, StatusBadge } from '../components/ui';
import api, { errorMessage } from '../services/api';
import { formatDate, formatDateTime, titleCase } from '../utils/format';

const STATUS_HELP = {
  submitted: 'Your application has been received and is waiting for review.',
  under_review: 'The admissions office is reviewing your application.',
  documents_required: 'Additional documents are required. Please read the remarks below.',
  approved: 'Congratulations! Your application has been approved. The admissions office will contact you about enrolment.',
  rejected: 'Unfortunately your application was not successful.',
  waitlisted: 'You are on the waiting list. You will be informed if a seat becomes available.',
  enrolled: 'You have been enrolled. Check your email for student portal credentials.',
};

export default function TrackApplication() {
  const [form, setForm] = useState({ applicationNumber: '', cnic: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.applicationNumber.trim() || form.cnic.replace(/\D/g, '').length !== 13) {
      setError('Enter your application number and the 13-digit CNIC / B-Form number used in the application.');
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post('/public/admissions/track', { applicationNumber: form.applicationNumber.trim(), cnic: form.cnic });
      setResult(data.data);
    } catch (ex) {
      setResult(null);
      setError(errorMessage(ex));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Seo title="Track Application" description="Check the status of your UMS admission application." />
      <PageHero title="Track Your Application" subtitle="Enter your application number and CNIC / B-Form number to view the latest status."
        crumbs={[{ label: 'Admissions', to: '/admissions' }, { label: 'Track Application' }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x grid gap-8 lg:grid-cols-5">
          <form onSubmit={submit} className="card h-fit space-y-5 p-8 lg:col-span-2" noValidate>
            <Input label="Application number" required placeholder="UMS-2026-XXXXXX" value={form.applicationNumber}
              onChange={(e) => setForm((f) => ({ ...f, applicationNumber: e.target.value.toUpperCase() }))} />
            <Input label="CNIC / B-Form number" required placeholder="3520212345671" inputMode="numeric" value={form.cnic}
              onChange={(e) => setForm((f) => ({ ...f, cnic: e.target.value }))} />
            {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? <Spinner className="h-4 w-4" /> : <Search className="h-4 w-4" />} Check status
            </button>
            <p className="text-xs text-slate-500">Lost your application number? <Link to="/contact" className="font-semibold text-primary-700">Contact the admissions office</Link>.</p>
          </form>

          <div className="lg:col-span-3">
            {result ? (
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card overflow-hidden">
                <div className="bg-primary-900 p-8 text-white">
                  <p className="text-xs font-semibold uppercase tracking-widest text-gold-300">Application {result.applicationNumber}</p>
                  <h2 className="mt-2 text-3xl font-bold text-white">{result.name}</h2>
                  <p className="mt-1 text-primary-100">{result.program?.title} · {result.session}</p>
                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <StatusBadge status={result.status} />
                    {result.aggregate != null && <span className="text-sm text-primary-100">Aggregate: <b className="text-white">{result.aggregate}%</b></span>}
                  </div>
                </div>
                <div className="space-y-6 p-8">
                  <p className="text-slate-700">{STATUS_HELP[result.status]}</p>
                  {result.remarks && <div className="rounded-xl border-s-4 border-gold-400 bg-gold-50 p-4 text-sm text-slate-700"><b>Remarks from admissions:</b> {result.remarks}</div>}
                  {result.merit && (
                    <div className="flex items-center gap-4 rounded-2xl bg-emerald-50 p-5">
                      <Award className="h-8 w-8 text-emerald-600" />
                      <div><p className="font-semibold text-emerald-800">Listed in {result.merit.title}</p><p className="text-sm text-emerald-700">Merit position: #{result.merit.rank}</p></div>
                    </div>
                  )}
                  <div>
                    <h3 className="font-sans text-base font-semibold">Timeline</h3>
                    <ol className="mt-4 space-y-4">
                      {result.timeline.map((h, i) => (
                        // eslint-disable-next-line react/no-array-index-key
                        <li key={i} className="flex gap-3">
                          {i === result.timeline.length - 1 ? <CheckCircle2 className="h-5 w-5 shrink-0 text-primary-600" /> : <Circle className="h-5 w-5 shrink-0 text-slate-300" />}
                          <div>
                            <p className="font-medium text-primary-900">{titleCase(h.status)}</p>
                            <p className="text-xs text-slate-500">{formatDateTime(h.at)}</p>
                            {h.remarks && <p className="text-sm text-slate-600">{h.remarks}</p>}
                          </div>
                        </li>
                      ))}
                    </ol>
                  </div>
                  <div>
                    <h3 className="font-sans text-base font-semibold">Documents received</h3>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {result.documents.length ? result.documents.map((d, i) => (
                        // eslint-disable-next-line react/no-array-index-key
                        <span key={i} className="badge bg-slate-100 text-slate-700"><FileText className="h-3.5 w-3.5" />{titleCase(d.type)}</span>
                      )) : <span className="text-sm text-slate-500">No documents on file</span>}
                    </div>
                  </div>
                  <p className="text-xs text-slate-400">Submitted on {formatDate(result.submittedAt)}</p>
                </div>
              </motion.div>
            ) : (
              <div className="card flex h-full min-h-72 flex-col items-center justify-center p-10 text-center">
                <Search className="h-10 w-10 text-primary-200" />
                <p className="mt-4 font-semibold text-primary-900">Your application status will appear here</p>
                <p className="mt-1 max-w-sm text-sm text-slate-500">Haven&apos;t applied yet? <Link to="/admissions/apply" className="font-semibold text-primary-700">Start your application</Link>.</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
