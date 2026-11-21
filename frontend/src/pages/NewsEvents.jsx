import { useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Calendar, CalendarDays, Clock, Download, ExternalLink, MapPin, Megaphone, Pin, Search } from 'lucide-react';
import Seo from '../components/Seo';
import { EventCard, NewsCard, PageHero } from '../components/common';
import { AsyncBlock, ErrorState, Img, PageLoader, Pagination, PlaceholderBadge, Reveal, RichText, StatusBadge, Tabs } from '../components/ui';
import { useDebounce, useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { assetUrl } from '../services/api';
import { formatDate, titleCase } from '../utils/format';
import NotFound from './NotFound';
import { DownloadList } from './Downloads';

/* --------------------------------- News --------------------------------- */
export function NewsList() {
  const { t } = useSite();
  const [params, setParams] = useSearchParams();
  const page = Number(params.get('page')) || 1;
  const category = params.get('category') || '';
  const [q, setQ] = useState('');
  const dq = useDebounce(q);
  const { data, meta, loading, error, reload } = useFetch('/public/news', { page, limit: 9, category, q: dq });
  const set = (k, v) => { const n = new URLSearchParams(params); if (v) n.set(k, v); else n.delete(k); if (k !== 'page') n.delete('page'); setParams(n); };

  return (
    <>
      <Seo title="News" description="Latest news from the University of Muhammadia Saifia." />
      <PageHero title={t('latestNews')} subtitle="Stories, achievements and updates from across the university." crumbs={[{ label: t('newsEvents'), to: '/news-events' }, { label: t('news') }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <Tabs value={category} onChange={(v) => set('category', v)} tabs={[{ value: '', label: t('all') }, ...['news', 'achievement', 'research', 'campus', 'press'].map((c) => ({ value: c, label: titleCase(c) }))]} />
            <div className="relative md:w-72">
              <Search className="pointer-events-none absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input className="input ps-11" placeholder="Search news" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search news" />
            </div>
          </div>
          <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ title: 'No news found' }}>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{data?.map((n, i) => <Reveal key={n._id} delay={(i % 3) * 0.05}><NewsCard item={n} /></Reveal>)}</div>
            <Pagination meta={meta} onChange={(p) => set('page', String(p))} />
          </AsyncBlock>
        </div>
      </section>
    </>
  );
}

export function NewsDetail() {
  const { slug } = useParams();
  const { data: n, loading, error, status, reload } = useFetch(`/public/news/${slug}`);
  if (loading && !n) return <PageLoader className="min-h-[60vh]" />;
  if (status === 404) return <NotFound />;
  if (error) return <ErrorState message={error} onRetry={reload} className="min-h-[60vh]" />;
  return (
    <>
      <Seo title={n.title} description={n.excerpt} image={assetUrl(n.coverImage)} />
      <article>
        <PageHero title={n.title} image={n.coverImage} crumbs={[{ label: 'News', to: '/news' }, { label: titleCase(n.category) }]}>
          <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-primary-100">
            <span className="flex items-center gap-2"><Calendar className="h-4 w-4 text-gold-300" />{formatDate(n.publishedAt, { dateStyle: 'full' })}</span>
            <PlaceholderBadge show={n.isPlaceholder} />
          </div>
        </PageHero>
        <section className="section bg-white">
          <div className="container-x grid gap-12 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Img src={n.coverImage} alt={n.title} className="mb-8 h-[26rem] w-full rounded-3xl object-cover" />
              {n.excerpt && <p className="mb-6 text-xl leading-relaxed text-slate-700">{n.excerpt}</p>}
              <RichText text={n.content} className="text-lg" />
              {n.tags?.length > 0 && <div className="mt-8 flex flex-wrap gap-2">{n.tags.map((tag) => <span key={tag} className="badge bg-primary-50 text-primary-700">#{tag}</span>)}</div>}
              <Link to="/news" className="btn-outline mt-10"><ArrowLeft className="h-4 w-4 rtl:rotate-180" />All news</Link>
            </div>
            <aside className="space-y-4 lg:sticky lg:top-28 lg:self-start">
              <h2 className="font-sans text-lg font-semibold">Recent news</h2>
              {n.recent?.map((r) => (
                <Link key={r._id} to={`/news/${r.slug}`} className="flex gap-4 rounded-2xl p-2 transition hover:bg-primary-50">
                  <Img src={r.coverImage} alt="" className="h-20 w-24 shrink-0 rounded-xl object-cover" />
                  <div><p className="line-clamp-2 text-sm font-semibold text-primary-900">{r.title}</p><p className="mt-1 text-xs text-slate-500">{formatDate(r.publishedAt)}</p></div>
                </Link>
              ))}
            </aside>
          </div>
        </section>
      </article>
    </>
  );
}

/* -------------------------------- Events -------------------------------- */
export function EventsList() {
  const { t } = useSite();
  const [when, setWhen] = useState('upcoming');
  const [page, setPage] = useState(1);
  const { data, meta, loading, error, reload } = useFetch('/public/events', { when, page, limit: 9 });
  return (
    <>
      <Seo title="Events" description="Upcoming and past events at UMS." />
      <PageHero title={t('events')} subtitle="Seminars, workshops, ceremonies, sports and cultural events." crumbs={[{ label: t('newsEvents'), to: '/news-events' }, { label: t('events') }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <Tabs className="mb-8" value={when} onChange={(v) => { setWhen(v); setPage(1); }} tabs={[{ value: 'upcoming', label: 'Upcoming' }, { value: 'past', label: 'Past events' }, { value: '', label: t('all') }]} />
          <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: CalendarDays, title: 'No events to show' }}>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{data?.map((e) => <EventCard key={e._id} item={e} />)}</div>
            <Pagination meta={meta} onChange={setPage} />
          </AsyncBlock>
        </div>
      </section>
    </>
  );
}

export function EventDetail() {
  const { slug } = useParams();
  const { data: e, loading, error, status, reload } = useFetch(`/public/events/${slug}`);
  if (loading && !e) return <PageLoader className="min-h-[60vh]" />;
  if (status === 404) return <NotFound />;
  if (error) return <ErrorState message={error} onRetry={reload} className="min-h-[60vh]" />;
  const facts = [
    [Calendar, 'Date', `${formatDate(e.startDate, { dateStyle: 'full' })}${e.endDate && formatDate(e.endDate) !== formatDate(e.startDate) ? ` – ${formatDate(e.endDate)}` : ''}`],
    [Clock, 'Time', new Date(e.startDate).toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' })],
    [MapPin, 'Venue', e.venue],
  ].filter(([, , v]) => v);
  return (
    <>
      <Seo title={e.title} description={e.description} image={assetUrl(e.image)} />
      <PageHero title={e.title} subtitle={e.description} image={e.image} crumbs={[{ label: 'Events', to: '/events' }, { label: titleCase(e.category) }]} />
      <section className="section bg-white">
        <div className="container-x grid gap-12 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Img src={e.image} alt={e.title} className="mb-8 h-96 w-full rounded-3xl object-cover" />
            <RichText text={e.content || e.description} className="text-lg" />
          </div>
          <aside className="card h-fit space-y-5 p-7 lg:sticky lg:top-28">
            <PlaceholderBadge show={e.isPlaceholder} />
            {facts.map(([Icon, label, value]) => (
              <div key={label} className="flex gap-3"><Icon className="h-5 w-5 shrink-0 text-gold-500" /><div><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="font-medium text-primary-900">{value}</p></div></div>
            ))}
            {e.registrationLink && <a href={e.registrationLink} target="_blank" rel="noopener noreferrer" className="btn-gold w-full">Register <ExternalLink className="h-4 w-4" /></a>}
            <Link to="/events" className="btn-outline w-full"><ArrowLeft className="h-4 w-4 rtl:rotate-180" />All events</Link>
          </aside>
        </div>
      </section>
    </>
  );
}

/* --------------------------- News & Events hub --------------------------- */
function AnnouncementList({ type }) {
  const [page, setPage] = useState(1);
  const { data, meta, loading, error, reload } = useFetch('/public/announcements', { type, page, limit: 10 });
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: Megaphone, title: 'No announcements' }}>
      <div className="space-y-4">
        {data?.map((a) => (
          <Reveal key={a._id} className="card flex flex-col gap-4 p-6 sm:flex-row sm:items-start">
            <div className="flex h-16 w-16 shrink-0 flex-col items-center justify-center rounded-2xl bg-primary-50 text-primary-800">
              <span className="font-display text-2xl font-bold leading-none">{new Date(a.publishDate).getDate()}</span>
              <span className="text-[10px] font-semibold uppercase">{new Date(a.publishDate).toLocaleString('en', { month: 'short' })}</span>
            </div>
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2">
                {a.isPinned && <span className="badge bg-gold-100 text-gold-700"><Pin className="h-3 w-3" />Pinned</span>}
                <StatusBadge status={a.type} />
              </div>
              <h3 className="mt-2 font-sans text-lg font-semibold text-primary-900">{a.title}</h3>
              {a.content && <p className="mt-1 text-sm text-slate-600">{a.content}</p>}
              <div className="mt-3 flex flex-wrap gap-3">
                {a.attachment && <a href={assetUrl(a.attachment)} target="_blank" rel="noopener noreferrer" className="btn-outline btn-sm"><Download className="h-4 w-4" />Attachment</a>}
                {a.link && (a.link.startsWith('/') ? <Link to={a.link} className="btn-outline btn-sm">Open</Link> : <a href={a.link} target="_blank" rel="noopener noreferrer" className="btn-outline btn-sm">Open <ExternalLink className="h-3.5 w-3.5" /></a>)}
              </div>
            </div>
          </Reveal>
        ))}
      </div>
      <Pagination meta={meta} onChange={setPage} />
    </AsyncBlock>
  );
}

function CalendarView() {
  const { data, loading, error, reload } = useFetch('/public/calendar');
  const colors = { academic: 'bg-primary-500', examination: 'bg-red-500', holiday: 'bg-emerald-500', admission: 'bg-gold-500', event: 'bg-sky-500' };
  const grouped = (data || []).reduce((acc, item) => {
    const key = new Date(item.startDate).toLocaleString('en', { month: 'long', year: 'numeric' });
    (acc[key] ||= []).push(item);
    return acc;
  }, {});
  return (
    <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ icon: CalendarDays, title: 'Calendar not published yet' }}>
      <div className="mb-6 flex flex-wrap gap-4 text-xs">{Object.entries(colors).map(([k, c]) => <span key={k} className="flex items-center gap-2"><span className={`h-3 w-3 rounded-full ${c}`} />{titleCase(k)}</span>)}</div>
      <div className="space-y-8">
        {Object.entries(grouped).map(([month, items]) => (
          <div key={month}>
            <h3 className="mb-3 font-display text-2xl font-bold">{month}</h3>
            <div className="card divide-y divide-slate-100">
              {items.map((c) => (
                <div key={c._id} className="flex items-start gap-4 p-5">
                  <span className={`mt-1.5 h-3 w-3 shrink-0 rounded-full ${colors[c.category]}`} />
                  <div className="flex-1">
                    <p className="font-semibold text-primary-900">{c.title}</p>
                    {c.description && <p className="text-sm text-slate-500">{c.description}</p>}
                  </div>
                  <p className="text-end text-sm font-medium text-slate-600">{formatDate(c.startDate)}{c.endDate ? <><br />– {formatDate(c.endDate)}</> : ''}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </AsyncBlock>
  );
}

export function NewsEventsHub() {
  const { t } = useSite();
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') || 'overview';
  const home = useFetch(tab === 'overview' ? '/public/home' : null);
  const tabs = [
    { value: 'overview', label: 'Overview' },
    { value: 'announcements', label: t('announcements') },
    { value: 'examination', label: t('examNotices') },
    { value: 'calendar', label: t('academicCalendar') },
    { value: 'downloads', label: 'Official Notices & PDFs' },
  ];
  return (
    <>
      <Seo title="News & Events" description="News, events, announcements, examination notices and the academic calendar." />
      <PageHero title={t('newsEvents')} subtitle="Everything happening at UMS — in one place." crumbs={[{ label: t('newsEvents') }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <Tabs className="mb-10" value={tab} onChange={(v) => setParams({ tab: v })} tabs={tabs} />
          {tab === 'overview' && (
            <AsyncBlock loading={home.loading} error={home.error} onRetry={home.reload}>
              <div className="grid gap-10 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <div className="mb-5 flex items-center justify-between"><h2 className="text-3xl font-bold">{t('latestNews')}</h2><Link to="/news" className="btn-outline btn-sm">{t('viewAll')}</Link></div>
                  <div className="grid gap-6 md:grid-cols-2">{home.data?.news?.map((n) => <NewsCard key={n._id} item={n} />)}</div>
                </div>
                <div>
                  <div className="mb-5 flex items-center justify-between"><h2 className="text-3xl font-bold">{t('events')}</h2><Link to="/events" className="btn-outline btn-sm">{t('viewAll')}</Link></div>
                  <div className="space-y-4">{home.data?.events?.map((e) => <EventCard key={e._id} item={e} horizontal />)}</div>
                </div>
              </div>
            </AsyncBlock>
          )}
          {tab === 'announcements' && <AnnouncementList />}
          {tab === 'examination' && <AnnouncementList type="examination" />}
          {tab === 'calendar' && <CalendarView />}
          {tab === 'downloads' && <DownloadList />}
        </div>
      </section>
    </>
  );
}
