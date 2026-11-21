import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Award, BookOpen, GraduationCap, Layers, ScrollText, Search } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero, ProgramCard } from '../components/common';
import { AsyncBlock, Pagination, Reveal, Tabs } from '../components/ui';
import { useDebounce, useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';

// "online" is a delivery mode, the others are program categories
const LEVELS = [
  { value: '', key: 'all', icon: Layers },
  { value: 'quran', key: 'quran', icon: BookOpen },
  { value: 'dars_nizami', key: 'dars_nizami', icon: GraduationCap },
  { value: 'specialization', key: 'specialization', icon: Award },
  { value: 'short_course', key: 'short_course', icon: ScrollText },
  { value: 'online', key: 'online', icon: ScrollText },
];

export default function Academics() {
  const { t } = useSite();
  const [params, setParams] = useSearchParams();
  const mode = params.get('mode') || '';
  const level = mode === 'online' ? 'online' : params.get('level') || '';
  const department = params.get('department') || '';
  const page = Number(params.get('page')) || 1;
  const [q, setQ] = useState(params.get('q') || '');
  const debouncedQ = useDebounce(q);

  const update = (patch) => {
    const next = new URLSearchParams(params);
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    if (!('page' in patch)) next.delete('page');
    setParams(next, { replace: true });
  };

  useEffect(() => { if ((params.get('q') || '') !== debouncedQ) update({ q: debouncedQ }); /* eslint-disable-next-line */ }, [debouncedQ]);

  const { data: departments } = useFetch('/public/departments');
  const { data, meta, loading, error, reload } = useFetch('/public/programs', {
    level: level === 'online' ? '' : level, deliveryMode: mode, department, q: params.get('q') || '', page, limit: 9,
  });

  return (
    <>
      <Seo title="Programs & Courses" description="Hifz-ul-Quran, Tajweed & Qirat, Dars-e-Nizami, Takhassus fil Fiqh al-Hanafi and online short courses at Jamia Muhammadia Saifia." />
      <PageHero title="Programs & Courses" subtitle="Quran, Dars-e-Nizami and Takhassus on campus — plus online Dars-e-Nizami, Quran with Tajweed and short courses for men and women." crumbs={[{ label: t('academics') }]} />

      <section className="section bg-surface pt-12">
        <div className="container-x">
          <Reveal className="grid gap-4 rounded-3xl bg-white p-6 shadow-soft lg:grid-cols-3">
            <div className="lg:col-span-3">
              <Tabs value={level} onChange={(v) => update(v === 'online' ? { mode: 'online', level: '' } : { level: v, mode: '' })} tabs={LEVELS.map((l) => ({ value: l.value, label: t(l.key) }))} />
            </div>
            <div className="relative lg:col-span-2">
              <Search className="pointer-events-none absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input value={q} onChange={(e) => setQ(e.target.value)} className="input ps-11" placeholder="Search programs by name or code…" aria-label="Search programs" />
            </div>
            <select value={department} onChange={(e) => update({ department: e.target.value })} className="input" aria-label="Filter by department">
              <option value="">All departments</option>
              {(departments || []).map((d) => <option key={d._id} value={d._id}>{d.name}{d.nameUr ? ` — ${d.nameUr}` : ''}</option>)}
            </select>
          </Reveal>

          <div className="mt-10">
            <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length}
              emptyProps={{ title: 'No programs found', description: 'Try a different level, department or search term.' }}>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {data?.map((p, i) => <Reveal key={p._id} delay={(i % 3) * 0.05}><ProgramCard program={p} /></Reveal>)}
              </div>
              <Pagination meta={meta} onChange={(p) => update({ page: String(p) })} />
            </AsyncBlock>
          </div>
        </div>
      </section>

      <section className="bg-white py-14">
        <div className="container-x grid gap-6 md:grid-cols-3">
          {[
            ['Academic Calendar', 'Key dates for the semester — classes, exams and holidays.', '/news-events?tab=calendar'],
            ['Admission Requirements', 'Eligibility, documents and how to apply.', '/admissions'],
            ['Departments', 'Explore our academic departments and faculty.', '/departments'],
          ].map(([title, text, to]) => (
            <Link key={to} to={to} className="card card-hover p-7">
              <h3 className="font-sans text-lg font-semibold text-primary-900">{title}</h3>
              <p className="mt-2 text-sm text-slate-600">{text}</p>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}
