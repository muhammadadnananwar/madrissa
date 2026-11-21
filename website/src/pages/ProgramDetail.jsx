import { Link, useParams } from 'react-router-dom';
import { ArrowRight, BookOpen, Briefcase, CalendarDays, CheckCircle2, Clock, Coins, FileCheck2, GraduationCap, Layers, MonitorSmartphone, Users } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { ErrorState, PageLoader, PlaceholderBadge, Reveal, RichText } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { formatMoney } from '../utils/format';
import { levelLabel, modeLabel } from '../utils/programs';
import NotFound from './NotFound';

function ListCard({ icon: Icon, title, items }) {
  if (!items?.length) return null;
  return (
    <Reveal className="card p-8">
      <h2 className="flex items-center gap-3 font-sans text-xl font-semibold"><Icon className="h-6 w-6 text-gold-500" />{title}</h2>
      <ul className="mt-5 space-y-3">
        {items.map((e) => (
          <li key={e} className="flex gap-3 text-slate-700"><CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-primary-500" /><span>{e}</span></li>
        ))}
      </ul>
    </Reveal>
  );
}

export default function ProgramDetail() {
  const { slug } = useParams();
  const { t, settings, lang, pick } = useSite();
  const { data: p, loading, error, status, reload } = useFetch(`/public/programs/${slug}`);

  if (loading && !p) return <PageLoader className="min-h-[60vh]" />;
  if (status === 404) return <NotFound />;
  if (error) return <ErrorState message={error} onRetry={reload} className="min-h-[60vh]" />;

  const fee = p.fee || {};
  const facts = [
    [Layers, 'Category', levelLabel(p.level, lang)],
    [MonitorSmartphone, 'Mode', modeLabel(p.deliveryMode || 'on_campus', lang)],
    [Clock, t('duration'), p.duration],
    [Users, 'For', p.audience],
    [CalendarDays, 'Class days', p.classDays],
    [BookOpen, 'Credit Hours', p.totalCreditHours],
    [GraduationCap, 'Seats', p.seats],
  ].filter(([, , v]) => v).slice(0, 5);
  const title = pick(p, 'title');

  return (
    <>
      <Seo title={p.title} description={p.shortDescription} image={p.image} />
      <PageHero title={title} subtitle={p.shortDescription} image={p.image}
        crumbs={[{ label: t('academics'), to: '/academics' }, { label: p.title }]}>
        {lang !== 'ur' && p.titleUr && <p dir="rtl" className="urdu mt-3 text-start text-2xl text-gold-300">{p.titleUr}</p>}
        <div className="mt-8 flex flex-wrap items-center gap-3">
          {p.isAdmissionOpen && settings?.admissionsOpen
            ? <Link to={`/admissions/apply?program=${p._id}`} className="btn-gold">{t('applyNow')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>
            : <span className="badge bg-white/10 px-4 py-2 text-white">Admissions currently closed</span>}
          {p.department && <Link to={`/departments/${p.department.slug}`} className="btn-ghost-light">{pick(p.department, 'name')}</Link>}
          <PlaceholderBadge show={p.isPlaceholder} />
        </div>
      </PageHero>

      <section className="relative z-10 -mt-1 bg-white shadow-soft">
        <div className="container-x grid grid-cols-2 divide-slate-100 sm:grid-cols-3 lg:grid-cols-5 lg:divide-x rtl:lg:divide-x-reverse">
          {facts.map(([Icon, label, value]) => (
            <div key={label} className="flex items-center gap-3 px-4 py-6">
              <Icon className="h-6 w-6 shrink-0 text-gold-500" />
              <div><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="font-semibold text-primary-900">{value}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section className="section bg-surface">
        <div className="container-x grid gap-8 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-2">
            <Reveal className="card p-8">
              <h2 className="font-sans text-xl font-semibold">{t('overview')}</h2>
              <RichText text={p.overview} className="mt-4" />
            </Reveal>
            <ListCard icon={GraduationCap} title={t('eligibility')} items={p.eligibility} />
            <ListCard icon={FileCheck2} title={t('requirements')} items={p.admissionRequirements} />
            <ListCard icon={Briefcase} title="Career Prospects" items={p.careerProspects} />
          </div>

          <aside className="space-y-6 lg:sticky lg:top-28 lg:self-start">
            <Reveal className="overflow-hidden rounded-3xl bg-primary-900 text-white shadow-lift">
              <div className="border-b border-white/10 p-6">
                <h2 className="flex items-center gap-2 font-sans text-lg font-semibold text-white"><Coins className="h-5 w-5 text-gold-400" />{t('feeStructure')}</h2>
              </div>
              <dl className="space-y-4 p-6 text-sm">
                {[['Admission fee (one-time)', fee.admissionFee], ['Tuition per semester', fee.tuitionPerSemester], ['Other charges', fee.otherCharges]].map(([label, v]) => (
                  <div key={label} className="flex items-center justify-between gap-4">
                    <dt className="text-primary-200">{label}</dt>
                    <dd className="font-semibold">{formatMoney(v, fee.currency)}</dd>
                  </div>
                ))}
              </dl>
              {(fee.note || settings?.admissions?.feeNote) && <p className="border-t border-white/10 p-6 text-xs text-primary-200">{fee.note || settings.admissions.feeNote}</p>}
            </Reveal>

            <Reveal className="card p-6">
              <h3 className="font-sans text-base font-semibold">Ready to apply?</h3>
              <p className="mt-2 text-sm text-slate-600">Complete the online form and upload your documents. You can track your application anytime.</p>
              <div className="mt-5 flex flex-col gap-2">
                <Link to={`/admissions/apply?program=${p._id}`} className="btn-primary w-full">{t('applyOnline')}</Link>
                <Link to="/downloads?category=prospectus" className="btn-outline w-full">Download Prospectus</Link>
              </div>
            </Reveal>

            {p.related?.length > 0 && (
              <Reveal className="card p-6">
                <h3 className="font-sans text-base font-semibold">Related programs</h3>
                <ul className="mt-4 space-y-2">
                  {p.related.map((r) => (
                    <li key={r._id}>
                      <Link to={`/academics/programs/${r.slug}`} className="flex items-center justify-between rounded-xl p-3 text-sm transition hover:bg-primary-50">
                        <span className="font-medium text-primary-900">{pick(r, 'title')}</span><ArrowRight className="h-4 w-4 text-gold-500 rtl:rotate-180" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Reveal>
            )}
          </aside>
        </div>
      </section>
    </>
  );
}
