import { useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, GraduationCap, Mail, Microscope, Search, Users } from 'lucide-react';
import Seo from '../components/Seo';
import { FacultyCard, PageHero } from '../components/common';
import { AsyncBlock, ErrorState, Img, PageLoader, Pagination, PlaceholderBadge, Reveal, RichText } from '../components/ui';
import { useDebounce, useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import NotFound from './NotFound';

export function FacultyDirectory() {
  const { t } = useSite();
  const [params, setParams] = useSearchParams();
  const department = params.get('department') || '';
  const page = Number(params.get('page')) || 1;
  const [q, setQ] = useState('');
  const dq = useDebounce(q);
  const { data: departments } = useFetch('/public/departments');
  const { data, meta, loading, error, reload } = useFetch('/public/faculty', { department, page, q: dq, limit: 12 });
  const set = (k, v) => { const n = new URLSearchParams(params); if (v) n.set(k, v); else n.delete(k); if (k !== 'page') n.delete('page'); setParams(n); };

  return (
    <>
      <Seo title="Asatiza (Faculty)" description="Shuyukh al-Hadith, muftis, ulama and qurra of Jamia Muhammadia Saifia, Ravi Rayyan Sharif." />
      <PageHero title="Our Asatiza (Faculty)" subtitle="The Shuyukh al-Hadith, muftis, ulama and qurra who teach at Jamia Muhammadia Saifia, Ravi Rayyan Sharif." crumbs={[{ label: t('faculty') }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <div className="mb-8 grid gap-4 rounded-3xl bg-white p-5 shadow-soft sm:grid-cols-3">
            <div className="relative sm:col-span-2">
              <Search className="pointer-events-none absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input className="input ps-11" placeholder="Search by name, designation or specialization" value={q} onChange={(e) => { setQ(e.target.value); set('page', ''); }} aria-label="Search faculty" />
            </div>
            <select className="input" value={department} onChange={(e) => set('department', e.target.value)} aria-label="Filter by department">
              <option value="">All departments</option>
              {(departments || []).map((d) => <option key={d._id} value={d._id}>{d.name}{d.nameUr ? ` — ${d.nameUr}` : ''}</option>)}
            </select>
          </div>
          <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: Users, title: 'No faculty members found' }}>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">{data?.map((m, i) => <Reveal key={m._id} delay={(i % 4) * 0.04}><FacultyCard member={m} /></Reveal>)}</div>
            <Pagination meta={meta} onChange={(p) => set('page', String(p))} />
          </AsyncBlock>
        </div>
      </section>
    </>
  );
}

export function FacultyProfile() {
  const { slug } = useParams();
  const { pick, lang } = useSite();
  const { data: m, loading, error, status, reload } = useFetch(`/public/faculty/${slug}`);
  if (loading && !m) return <PageLoader className="min-h-[60vh]" />;
  if (status === 404) return <NotFound />;
  if (error) return <ErrorState message={error} onRetry={reload} className="min-h-[60vh]" />;
  return (
    <>
      <Seo title={m.name} description={`${m.designation}${m.department ? `, ${m.department.name}` : ''}`} />
      <PageHero title={pick(m, 'name')} subtitle={`${pick(m, 'designation')}${m.department ? ` · ${pick(m.department, 'name')}` : ''}`} crumbs={[{ label: 'Faculty', to: '/faculty' }, { label: m.name }]}>
        {lang !== 'ur' && m.nameUr && <p dir="rtl" className="urdu mt-3 text-start text-2xl text-gold-300">{m.nameUr}</p>}
      </PageHero>
      <section className="section bg-surface">
        <div className="container-x grid gap-8 lg:grid-cols-3">
          <aside className="card h-fit p-8 text-center lg:sticky lg:top-28">
            <Img src={m.photo} alt={m.name} className="mx-auto h-48 w-48 rounded-full border-4 border-gold-300 object-cover" fallbackClass="rounded-full" />
            <h2 className="mt-6 font-sans text-xl font-semibold">{m.name}</h2>
            {m.nameUr && <p dir="rtl" className="urdu text-lg text-primary-700">{m.nameUr}</p>}
            <p className="font-medium text-gold-600">{m.designation}</p>
            {m.designationUr && <p dir="rtl" className="urdu text-sm text-slate-600">{m.designationUr}</p>}
            {m.department && <Link to={`/departments/${m.department.slug}`} className="mt-1 block text-sm text-primary-700 hover:underline">{m.department.name}</Link>}
            <PlaceholderBadge show={m.isPlaceholder} className="mt-3" />
            {m.email && <a href={`mailto:${m.email}`} className="btn-outline mt-6 w-full"><Mail className="h-4 w-4" />{m.email}</a>}
          </aside>
          <div className="space-y-6 lg:col-span-2">
            {m.bio && <Reveal className="card p-8"><h2 className="font-sans text-xl font-semibold">Biography</h2><RichText text={m.bio} className="mt-4" /></Reveal>}
            {m.qualifications?.length > 0 && (
              <Reveal className="card p-8">
                <h2 className="flex items-center gap-2 font-sans text-xl font-semibold"><GraduationCap className="h-6 w-6 text-gold-500" />Academic Qualifications</h2>
                <ul className="mt-5 space-y-4">
                  {m.qualifications.map((q, i) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <li key={i} className="border-s-2 border-gold-300 ps-4"><p className="font-semibold text-primary-900">{q.degree}</p><p className="text-sm text-slate-500">{[q.institution, q.year].filter(Boolean).join(' · ')}</p></li>
                  ))}
                </ul>
              </Reveal>
            )}
            {(m.specialization || m.researchInterests?.length > 0) && (
              <Reveal className="card p-8">
                <h2 className="flex items-center gap-2 font-sans text-xl font-semibold"><Microscope className="h-6 w-6 text-gold-500" />Specialization & Research</h2>
                {m.specialization && <p className="mt-4 text-slate-700">{m.specialization}</p>}
                <div className="mt-4 flex flex-wrap gap-2">{m.researchInterests?.map((r) => <span key={r} className="badge bg-primary-50 text-primary-700">{r}</span>)}</div>
              </Reveal>
            )}
            {m.publications?.length > 0 && (
              <Reveal className="card p-8">
                <h2 className="flex items-center gap-2 font-sans text-xl font-semibold"><BookOpen className="h-6 w-6 text-gold-500" />Selected Publications</h2>
                <ol className="mt-4 list-decimal space-y-2 ps-5 text-sm text-slate-700">{m.publications.map((p) => <li key={p}>{p}</li>)}</ol>
              </Reveal>
            )}
            <Link to="/faculty" className="btn-outline"><ArrowLeft className="h-4 w-4 rtl:rotate-180" />Back to directory</Link>
          </div>
        </div>
      </section>
    </>
  );
}
