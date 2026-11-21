import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowRight, BookOpen, Calendar, ChevronLeft, ChevronRight, ClipboardCheck, Download, GraduationCap, ListOrdered, Megaphone, Quote, Search,
} from 'lucide-react';
import Seo from '../components/Seo';
import { EventCard, NewsCard, ProgramCard } from '../components/common';
import { Accordion, AsyncBlock, Img, PlaceholderBadge, Reveal, SectionHeading } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { getIcon } from '../utils/icons';
import { formatDate } from '../utils/format';

function Hero({ settings, t }) {
  const hero = settings?.hero || {};
  const quick = [
    { icon: ClipboardCheck, label: t('applyOnline'), to: '/admissions/apply' },
    { icon: Search, label: t('trackApplication'), to: '/admissions/track' },
    { icon: ListOrdered, label: t('meritLists'), to: '/admissions/merit-lists' },
    { icon: Download, label: 'Prospectus', to: '/downloads?category=prospectus' },
  ];
  return (
    <section className="relative isolate overflow-hidden bg-primary-950">
      <motion.div initial={{ scale: 1.12 }} animate={{ scale: 1 }} transition={{ duration: 8, ease: 'easeOut' }} className="absolute inset-0 -z-20">
        <Img src={hero.image} alt="University campus" className="h-full w-full object-cover" />
      </motion.div>
      <div className="absolute inset-0 -z-10 bg-gradient-to-r from-primary-950 via-primary-900/90 to-primary-800/40 rtl:bg-gradient-to-l" />
      <div className="absolute inset-0 -z-10 bg-crest-pattern [background-size:30px_30px] opacity-25" />
      <div className="absolute -end-40 -top-40 -z-10 h-[30rem] w-[30rem] rounded-full bg-gold-400/20 blur-3xl" />

      <div className="container-x grid min-h-[78vh] items-center gap-12 py-20 lg:grid-cols-12 lg:py-28">
        <div className="lg:col-span-7">
          <motion.span initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 rounded-full border border-gold-400/40 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.25em] text-gold-300 backdrop-blur">
            <GraduationCap className="h-4 w-4" /> {settings?.universityName || 'University of Muhammadia Saifia'}
          </motion.span>
          {settings?.universityNameUr && (
            <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} dir="rtl"
              className="urdu mt-4 text-2xl font-semibold text-gold-300 sm:text-3xl">{settings.universityNameUr}</motion.p>
          )}
          <motion.h1 initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.7 }}
            className="mt-6 text-balance text-5xl font-bold leading-[1.05] text-white sm:text-6xl lg:text-7xl">
            {(hero.title || 'Shape Your Future With Excellence').split(' ').map((w, i, arr) => (
              <span key={`${w}-${i}`} className={i === arr.length - 1 ? 'text-gold-300' : ''}>{w}{i < arr.length - 1 ? ' ' : ''}</span>
            ))}
          </motion.h1>
          <motion.p initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.7 }}
            className="mt-6 max-w-2xl text-lg leading-relaxed text-primary-100">{hero.subtitle}</motion.p>
          {settings?.taglineUr && <p dir="rtl" className="urdu mt-3 text-xl text-white/90">{settings.taglineUr}</p>}
          <motion.div initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="mt-10 flex flex-wrap gap-4">
            <Link to={hero.primaryCta?.link || '/admissions/apply'} className="btn-gold px-7 py-3.5 text-base">
              {hero.primaryCta?.label || t('applyNow')} <ArrowRight className="h-5 w-5 rtl:rotate-180" />
            </Link>
            <Link to={hero.secondaryCta?.link || '/academics'} className="btn-ghost-light px-7 py-3.5 text-base">
              <BookOpen className="h-5 w-5" /> {hero.secondaryCta?.label || t('explorePrograms')}
            </Link>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6, duration: 0.7 }} className="lg:col-span-5 lg:ps-8">
          <div className="rounded-3xl border border-white/15 bg-white/10 p-6 shadow-2xl backdrop-blur-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-300">Quick Access</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {quick.map(({ icon: Icon, label, to }) => (
                <Link key={to} to={to} className="group flex flex-col gap-3 rounded-2xl bg-white/5 p-4 text-white ring-1 ring-white/10 transition hover:bg-white hover:text-primary-900">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gold-400 text-primary-950"><Icon className="h-5 w-5" /></span>
                  <span className="text-sm font-semibold">{label}</span>
                </Link>
              ))}
            </div>
            {settings?.currentSession && (
              <p className="mt-5 border-t border-white/10 pt-4 text-sm text-primary-100">
                Current session: <span className="font-semibold text-white">{settings.currentSession}</span>
                {settings.admissionsOpen && <span className="badge ms-2 bg-emerald-400/20 text-emerald-200">Admissions open</span>}
              </p>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function AnnouncementTicker({ items }) {
  if (!items?.length) return null;
  const loop = [...items, ...items];
  return (
    <div className="border-y border-primary-100 bg-white">
      <div className="container-x flex items-center gap-4 py-3">
        <Link to="/news-events?tab=announcements" className="flex shrink-0 items-center gap-2 rounded-full bg-primary-700 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-white">
          <Megaphone className="h-4 w-4 text-gold-300" /> <span className="hidden sm:inline">Announcements</span>
        </Link>
        <div className="relative flex-1 overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_6%,black_94%,transparent)]">
          <div className="flex w-max animate-marquee gap-10 hover:[animation-play-state:paused]">
            {loop.map((a, i) => (
              <Link key={`${a._id}-${i}`} to={a.link?.startsWith('/') ? a.link : '/news-events?tab=announcements'} className="flex items-center gap-2 whitespace-nowrap text-sm text-slate-700 hover:text-primary-700">
                <span className="h-1.5 w-1.5 rounded-full bg-gold-500" />
                <span className="font-medium">{a.title}</span>
                <span className="text-xs text-slate-400">{formatDate(a.publishDate)}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stats({ stats }) {
  if (!stats?.length) return null;
  return (
    <section className="relative z-10 -mb-16 pt-12">
      <div className="container-x">
        <Reveal className="grid grid-cols-2 overflow-hidden rounded-3xl bg-white shadow-lift ring-1 ring-primary-100 lg:grid-cols-4">
          {stats.map((s, i) => (
            <div key={s.label} className={`p-6 text-center sm:p-8 ${i > 0 ? 'border-primary-100 lg:border-s' : ''} ${i % 2 ? 'border-s' : ''} ${i > 1 ? 'border-t lg:border-t-0' : ''}`}>
              <p className="font-display text-4xl font-bold text-primary-700 sm:text-5xl">{s.value}</p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-widest text-slate-500">{s.label}</p>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}

function Intro({ settings, t }) {
  const about = settings?.about || {};
  return (
    <section className="section bg-surface pt-32">
      <div className="container-x grid items-center gap-14 lg:grid-cols-2">
        <Reveal className="relative">
          <div className="grid grid-cols-5 gap-4">
            <Img src={about.image || settings?.hero?.image} alt="UMS campus" className="col-span-3 h-80 w-full rounded-3xl object-cover shadow-lift sm:h-[26rem]" />
            <div className="col-span-2 flex flex-col gap-4 pt-12">
              <Img src={settings?.campusFacilities?.[0]?.image} alt="Library" className="h-40 w-full rounded-3xl object-cover shadow-soft sm:h-48" />
              <div className="flex flex-1 flex-col justify-center rounded-3xl bg-primary-800 p-5 text-white">
                <img src="/logo.svg" alt="" className="h-12 w-auto self-start" />
                <p className="mt-3 font-display text-xl font-semibold leading-tight">{settings?.tagline}</p>
              </div>
            </div>
          </div>
        </Reveal>
        <div>
          <SectionHeading align="left" eyebrow={t('introduction')} title={`Welcome to ${settings?.universityName || 'UMS'}`} />
          <Reveal delay={0.1}>
            <p className="-mt-6 text-lg leading-relaxed text-slate-600">{about.intro}</p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {[['Vision', about.vision], ['Mission', about.mission]].map(([label, text]) => (
                <div key={label} className="rounded-2xl border-s-4 border-gold-400 bg-white p-5 shadow-soft">
                  <p className="text-xs font-semibold uppercase tracking-widest text-gold-600">{label}</p>
                  <p className="mt-2 line-clamp-4 text-sm text-slate-600">{text}</p>
                </div>
              ))}
            </div>
            <Link to="/about" className="btn-primary mt-8">{t('learnMore')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function Departments({ items, t }) {
  const { pick, lang } = useSite();
  if (!items?.length) return null;
  return (
    <section className="section bg-white">
      <div className="container-x">
        <SectionHeading eyebrow={t('departments')} title={t('ourDepartments')} align="left"
          action={<Link to="/departments" className="btn-outline">{t('viewAll')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>} />
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((d, i) => (
            <Reveal key={d._id} delay={i * 0.05}>
              <Link to={`/departments/${d.slug}`} className="group relative block h-72 overflow-hidden rounded-3xl">
                <Img src={d.image} alt={d.name} className="h-full w-full object-cover transition duration-700 group-hover:scale-110" />
                <div className="absolute inset-0 bg-gradient-to-t from-primary-950 via-primary-900/50 to-transparent" />
                <PlaceholderBadge show={d.isPlaceholder} className="absolute end-4 top-4" />
                <div className="absolute inset-x-0 bottom-0 p-6">
                  <span className="text-xs font-semibold tracking-widest text-gold-300">{d.code}</span>
                  <h3 className={`mt-1 font-display text-2xl font-bold leading-tight text-white ${lang === 'ur' && d.nameUr ? 'urdu' : ''}`}>{pick(d, 'name')}</h3>
                  {lang !== 'ur' && d.nameUr && <p dir="rtl" className="urdu text-start text-base text-gold-200">{d.nameUr}</p>}
                  <span className="mt-3 flex items-center gap-1 text-sm font-medium text-primary-100 opacity-0 transition group-hover:opacity-100">
                    Explore <ArrowRight className="h-4 w-4 rtl:rotate-180" />
                  </span>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function WhyChoose({ items, t }) {
  if (!items?.length) return null;
  return (
    <section className="section relative overflow-hidden bg-primary-900">
      <div className="absolute inset-0 bg-crest-pattern [background-size:28px_28px] opacity-30" />
      <img src="/logo.svg" alt="" className="pointer-events-none absolute -end-24 top-1/2 h-[36rem] -translate-y-1/2 opacity-[0.06]" />
      <div className="container-x relative">
        <SectionHeading light eyebrow={t('whyChoose')} title="An education that shapes character and career" />
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((w, i) => {
            const Icon = getIcon(w.icon);
            return (
              <Reveal key={w.title} delay={i * 0.06}>
                <div className="group h-full rounded-3xl border border-white/10 bg-white/5 p-7 backdrop-blur transition hover:-translate-y-1 hover:border-gold-400/50 hover:bg-white/10">
                  <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gold-400 text-primary-950 shadow-gold transition group-hover:rotate-6"><Icon className="h-7 w-7" /></span>
                  <h3 className="mt-6 font-sans text-lg font-semibold text-white">{w.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-primary-200">{w.description}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function VcMessage({ vc, t }) {
  if (!vc?.message) return null;
  return (
    <section className="section bg-surface">
      <div className="container-x">
        <div className="grid items-center gap-12 overflow-hidden rounded-[2rem] bg-white shadow-lift lg:grid-cols-5">
          <Reveal className="relative h-full min-h-80 lg:col-span-2">
            <Img src={vc.photo} alt={vc.name} className="absolute inset-0 h-full w-full object-cover" />
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-primary-950 to-transparent p-6 text-white">
              <p className="font-display text-2xl font-bold">{vc.name}</p>
              <p className="text-sm text-gold-300">{vc.title}</p>
            </div>
          </Reveal>
          <Reveal delay={0.1} className="p-8 sm:p-12 lg:col-span-3">
            <span className="eyebrow">{vc.title || t('vcMessage')}</span>
            <Quote className="mt-6 h-12 w-12 text-gold-400 rtl:-scale-x-100" />
            <p className="mt-4 font-display text-2xl leading-relaxed text-primary-900 sm:text-[1.75rem]">{vc.message}</p>
            <Link to="/about#leadership" className="btn-outline mt-8">{t('readMore')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function Gallery({ items, t }) {
  if (!items?.length) return null;
  const spans = ['md:col-span-2 md:row-span-2', '', '', 'md:row-span-2', '', 'md:col-span-2', '', ''];
  return (
    <section className="section bg-white">
      <div className="container-x">
        <SectionHeading eyebrow={t('campusLife')} title={t('campusGallery')} align="left"
          action={<Link to="/campus-life#gallery" className="btn-outline">{t('viewAll')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>} />
        <div className="grid auto-rows-[12rem] grid-cols-2 gap-4 md:grid-cols-4">
          {items.slice(0, 8).map((g, i) => (
            <Reveal key={g._id} delay={i * 0.04} className={`group relative overflow-hidden rounded-2xl ${spans[i] || ''}`}>
              <Img src={g.image} alt={g.title} className="h-full w-full object-cover transition duration-700 group-hover:scale-110" />
              <div className="absolute inset-0 flex items-end bg-gradient-to-t from-primary-950/80 to-transparent p-4 opacity-0 transition group-hover:opacity-100">
                <p className="text-sm font-semibold text-white">{g.title}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function Testimonials({ items, t }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (!items?.length) return undefined;
    const id = setInterval(() => setI((x) => (x + 1) % items.length), 7000);
    return () => clearInterval(id);
  }, [items]);
  if (!items?.length) return null;
  const item = items[i];
  return (
    <section className="section relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-gold-50">
      <div className="container-x max-w-4xl text-center">
        <SectionHeading eyebrow={t('testimonials')} title="What our community says" />
        <div className="relative min-h-64">
          <AnimatePresence mode="wait">
            <motion.figure key={item._id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.5 }}>
              <Quote className="mx-auto h-10 w-10 text-gold-400" />
              <blockquote className="mt-6 font-display text-2xl leading-relaxed text-primary-900 sm:text-3xl">“{item.quote}”</blockquote>
              <figcaption className="mt-8 flex flex-col items-center gap-3">
                <Img src={item.photo} alt={item.name} className="h-14 w-14 rounded-full object-cover" fallbackClass="rounded-full" />
                <div>
                  <p className="font-semibold text-primary-900">{item.name}</p>
                  <p className="text-sm text-slate-500">{[item.program, item.batch].filter(Boolean).join(' · ')}</p>
                </div>
                <PlaceholderBadge show={item.isPlaceholder} />
              </figcaption>
            </motion.figure>
          </AnimatePresence>
        </div>
        {items.length > 1 && (
          <div className="mt-8 flex items-center justify-center gap-3">
            <button type="button" className="btn-icon bg-white shadow-soft" onClick={() => setI((i - 1 + items.length) % items.length)} aria-label="Previous testimonial"><ChevronLeft className="h-5 w-5 rtl:rotate-180" /></button>
            {items.map((x, idx) => (
              <button key={x._id} type="button" onClick={() => setI(idx)} aria-label={`Testimonial ${idx + 1}`} className={`h-2 rounded-full transition-all ${idx === i ? 'w-8 bg-primary-700' : 'w-2 bg-primary-200'}`} />
            ))}
            <button type="button" className="btn-icon bg-white shadow-soft" onClick={() => setI((i + 1) % items.length)} aria-label="Next testimonial"><ChevronRight className="h-5 w-5 rtl:rotate-180" /></button>
          </div>
        )}
      </div>
    </section>
  );
}

export default function Home() {
  const { settings, t } = useSite();
  const { data, loading, error, reload } = useFetch('/public/home');

  return (
    <>
      <Seo description={settings?.seo?.defaultDescription} />
      <Hero settings={settings} t={t} />
      <AnnouncementTicker items={data?.announcements} />
      <Stats stats={settings?.stats} />
      <Intro settings={settings} t={t} />

      <AsyncBlock loading={loading && !data} error={!data && error} onRetry={reload}>
        {data?.programs?.length > 0 && (
          <section className="section bg-surface pt-0">
            <div className="container-x">
              <SectionHeading eyebrow={t('academics')} title={t('featuredPrograms')} align="left"
                description="Undergraduate, graduate and postgraduate programs designed to prepare you for meaningful careers."
                action={<Link to="/academics" className="btn-primary">{t('explorePrograms')} <ArrowRight className="h-4 w-4 rtl:rotate-180" /></Link>} />
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {data.programs.map((p, i) => <Reveal key={p._id} delay={i * 0.05}><ProgramCard program={p} /></Reveal>)}
              </div>
            </div>
          </section>
        )}

        <Departments items={data?.departments} t={t} />
        <WhyChoose items={settings?.whyChoose} t={t} />
        <VcMessage vc={settings?.viceChancellor} t={t} />

        <section className="section bg-white">
          <div className="container-x grid gap-12 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <SectionHeading eyebrow={t('news')} title={t('latestNews')} align="left"
                action={<Link to="/news" className="btn-outline btn-sm">{t('viewAll')}</Link>} />
              {data?.news?.length ? (
                <div className="grid gap-6 sm:grid-cols-2">
                  {data.news.slice(0, 2).map((n) => <Reveal key={n._id}><NewsCard item={n} /></Reveal>)}
                </div>
              ) : <p className="text-sm text-slate-500">No news published yet.</p>}
            </div>
            <div>
              <SectionHeading eyebrow={t('events')} title={t('upcomingEvents')} align="left" />
              <div className="space-y-4">
                {data?.events?.length
                  ? data.events.map((e) => <Reveal key={e._id}><EventCard item={e} horizontal /></Reveal>)
                  : <p className="text-sm text-slate-500">No upcoming events.</p>}
                <Link to="/events" className="flex items-center gap-2 text-sm font-semibold text-primary-700 hover:text-primary-900">
                  <Calendar className="h-4 w-4" /> All events <ArrowRight className="h-4 w-4 rtl:rotate-180" />
                </Link>
              </div>
            </div>
          </div>
        </section>

        <Gallery items={data?.gallery} t={t} />
        <Testimonials items={data?.testimonials} t={t} />

        {data?.faqs?.length > 0 && (
          <section className="section bg-surface">
            <div className="container-x grid gap-12 lg:grid-cols-5">
              <div className="lg:col-span-2">
                <SectionHeading align="left" eyebrow="FAQ" title={t('faq')} description="Quick answers about admissions, programs and student services." />
                <Reveal className="rounded-3xl bg-primary-800 p-8 text-white">
                  <h3 className="font-display text-2xl font-bold text-white">Still have questions?</h3>
                  <p className="mt-2 text-sm text-primary-100">Our admissions team is happy to help you choose the right program.</p>
                  <Link to="/contact" className="btn-gold mt-6">{t('contactUs')}</Link>
                </Reveal>
              </div>
              <Reveal className="lg:col-span-3"><Accordion items={data.faqs} /></Reveal>
            </div>
          </section>
        )}
      </AsyncBlock>

      <section className="relative overflow-hidden bg-gradient-to-r from-primary-800 via-primary-700 to-primary-600">
        <div className="absolute inset-0 bg-crest-pattern [background-size:24px_24px] opacity-30" />
        <div className="container-x relative flex flex-col items-center justify-between gap-6 py-14 text-center lg:flex-row lg:text-start">
          <div>
            <h2 className="text-3xl font-bold text-white sm:text-4xl">Begin your journey at {settings?.shortName || 'UMS'}</h2>
            <p className="mt-2 text-primary-100">{settings?.admissionsOpen ? 'Applications are now being accepted online.' : 'Explore our programs and prepare for the next intake.'}</p>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/admissions/apply" className="btn-gold px-7 py-3">{t('applyNow')}</Link>
            <Link to="/contact" className="btn-ghost-light px-7 py-3">{t('contactUs')}</Link>
          </div>
        </div>
      </section>
    </>
  );
}
