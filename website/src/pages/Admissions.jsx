import { Link } from 'react-router-dom';
import { ArrowRight, CalendarDays, CheckCircle2, ClipboardCheck, Download, FileText, ListOrdered, Megaphone, Search } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { Accordion, AsyncBlock, Reveal, SectionHeading } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { formatDate } from '../utils/format';

export default function Admissions() {
  const { settings, t } = useSite();
  const adm = settings?.admissions || {};
  const ann = useFetch('/public/announcements', { type: 'admission', limit: 5 });
  const faqs = useFetch('/public/faqs', { category: 'admission' });

  const steps = [
    [Search, 'Choose a program', 'Review eligibility, duration and fees on the program page.', '/academics'],
    [ClipboardCheck, 'Apply online', 'Fill the form and upload your photo, CNIC and academic documents.', '/admissions/apply'],
    [FileText, 'Track your application', 'Use your application number and CNIC to view status updates.', '/admissions/track'],
    [ListOrdered, 'Check merit lists', 'Merit lists are published here once finalised.', '/admissions/merit-lists'],
  ];

  return (
    <>
      <Seo title="Admissions" description="Admission information, schedule, requirements and online application for UMS." />
      <PageHero title="Admissions" subtitle={adm.intro} crumbs={[{ label: t('admissions') }]}>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/admissions/apply" className="btn-gold">{t('applyOnline')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>
          <Link to="/admissions/track" className="btn-ghost-light">{t('trackApplication')}</Link>
          {adm.prospectusUrl && <Link to="/downloads?category=prospectus" className="btn-ghost-light"><Download className="h-4 w-4" /> Prospectus</Link>}
        </div>
      </PageHero>

      {!settings?.admissionsOpen && (
        <div className="bg-amber-50 py-3 text-center text-sm font-medium text-amber-800">Online admissions are currently closed. Please check back for the next intake.</div>
      )}

      <section className="section bg-white">
        <div className="container-x">
          <SectionHeading eyebrow="How to apply" title="Four simple steps" />
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {steps.map(([Icon, title, text, to], i) => (
              <Reveal key={title} delay={i * 0.06}>
                <Link to={to} className="card card-hover relative block h-full p-7">
                  <span className="absolute end-6 top-5 font-display text-5xl font-bold text-primary-100">{i + 1}</span>
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gold-400 text-primary-950"><Icon className="h-6 w-6" /></span>
                  <h3 className="mt-5 font-sans text-lg font-semibold text-primary-900">{title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{text}</p>
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="section bg-surface">
        <div className="container-x grid gap-8 lg:grid-cols-2">
          <Reveal className="card p-8">
            <h2 className="flex items-center gap-3 font-sans text-xl font-semibold"><CalendarDays className="h-6 w-6 text-gold-500" />Admission Schedule</h2>
            {adm.schedule?.length ? (
              <ol className="relative mt-6 space-y-6 border-s-2 border-primary-100 ps-6">
                {adm.schedule.map((s, i) => (
                  // eslint-disable-next-line react/no-array-index-key
                  <li key={i} className="relative">
                    <span className="absolute -start-[33px] top-1 h-4 w-4 rounded-full border-4 border-white bg-gold-400 ring-2 ring-gold-200" />
                    <p className="font-semibold text-primary-900">{s.step}</p>
                    <p className="text-sm text-slate-500">{s.date}{s.note ? ` · ${s.note}` : ''}</p>
                  </li>
                ))}
              </ol>
            ) : <p className="mt-4 text-sm text-slate-500">The admission schedule will be announced soon.</p>}
          </Reveal>

          <div className="space-y-8">
            <Reveal className="card p-8">
              <h2 className="flex items-center gap-3 font-sans text-xl font-semibold"><FileText className="h-6 w-6 text-gold-500" />Required Documents</h2>
              <ul className="mt-5 space-y-3">
                {(adm.generalRequirements || []).map((r) => (
                  <li key={r} className="flex gap-3 text-sm text-slate-700"><CheckCircle2 className="h-5 w-5 shrink-0 text-primary-500" />{r}</li>
                ))}
              </ul>
              <p className="mt-5 text-xs text-slate-500">Every applicant must agree to the Jamia’s rules & regulations.</p>
              <Link to="/pages/rules-and-regulations" className="btn-outline btn-sm mt-4"><FileText className="h-4 w-4" />Read the rules & regulations</Link>
            </Reveal>

            <Reveal className="card p-8">
              <h2 className="flex items-center gap-3 font-sans text-xl font-semibold"><Megaphone className="h-6 w-6 text-gold-500" />Admission Announcements</h2>
              <AsyncBlock loading={ann.loading} error={ann.error} onRetry={ann.reload} empty={!ann.data?.length} loaderClass="py-8"
                emptyProps={{ title: 'No announcements yet', className: 'py-8' }}>
                <ul className="mt-4 divide-y divide-slate-100">
                  {ann.data?.map((a) => (
                    <li key={a._id} className="py-3">
                      <p className="font-medium text-primary-900">{a.title}</p>
                      <p className="text-xs text-slate-500">{formatDate(a.publishDate)}</p>
                      {a.content && <p className="mt-1 text-sm text-slate-600">{a.content}</p>}
                    </li>
                  ))}
                </ul>
              </AsyncBlock>
            </Reveal>
          </div>
        </div>
      </section>

      {faqs.data?.length > 0 && (
        <section className="section bg-white">
          <div className="container-x max-w-4xl">
            <SectionHeading eyebrow="FAQ" title="Admission FAQs" />
            <Accordion items={faqs.data} />
          </div>
        </section>
      )}
    </>
  );
}
