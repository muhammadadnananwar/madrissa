import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import Seo from '../components/Seo';
import { EventCard, PageHero } from '../components/common';
import { AsyncBlock, Img, Reveal, SectionHeading, Tabs } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { getIcon } from '../utils/icons';

const CATS = ['all', 'campus', 'library', 'labs', 'sports', 'events', 'students'];

export default function CampusLife() {
  const { settings, t } = useSite();
  const [cat, setCat] = useState('all');
  const [lightbox, setLightbox] = useState(null);
  const gallery = useFetch('/public/gallery', { category: cat });
  const events = useFetch('/public/events', { when: 'upcoming', limit: 3 });

  return (
    <>
      <Seo title="Campus Life" description="Facilities, library, laboratories, sports, societies and student activities at UMS." />
      <PageHero title={t('campusLife')} subtitle="Life at UMS goes beyond the classroom — discover our facilities, societies and the vibrant student community."
        image={settings?.campusFacilities?.[0]?.image} crumbs={[{ label: t('campusLife') }]} />

      <section className="section bg-white">
        <div className="container-x">
          <SectionHeading eyebrow="Facilities" title="Spaces to learn, create and grow" />
          <div className="space-y-16">
            {(settings?.campusFacilities || []).map((f, i) => {
              const Icon = getIcon(f.icon);
              return (
                // eslint-disable-next-line react/no-array-index-key
                <Reveal key={i} className={`grid items-center gap-10 lg:grid-cols-2 ${i % 2 ? 'lg:[&>*:first-child]:order-2' : ''}`}>
                  <Img src={f.image} alt={f.title} className="h-80 w-full rounded-[2rem] object-cover shadow-lift" />
                  <div>
                    <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gold-400 text-primary-950"><Icon className="h-7 w-7" /></span>
                    <h2 className="mt-6 text-4xl font-bold">{f.title}</h2>
                    <p className="mt-4 text-lg leading-relaxed text-slate-600">{f.description}</p>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </div>
      </section>

      {settings?.societies?.length > 0 && (
        <section className="section bg-primary-900">
          <div className="container-x">
            <SectionHeading light eyebrow="Student Activities" title="Societies & Clubs" description="Join a society to lead, serve, compete and make lifelong friends." />
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {settings.societies.map((s, i) => {
                const Icon = getIcon(s.icon);
                return (
                  // eslint-disable-next-line react/no-array-index-key
                  <Reveal key={i} delay={i * 0.05}>
                    <div className="h-full rounded-3xl border border-white/10 bg-white/5 p-7 text-white backdrop-blur transition hover:bg-white/10">
                      <Icon className="h-9 w-9 text-gold-400" />
                      <h3 className="mt-5 font-sans text-lg font-semibold text-white">{s.title}</h3>
                      <p className="mt-2 text-sm text-primary-200">{s.description}</p>
                    </div>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>
      )}

      <section className="section bg-surface">
        <div className="container-x">
          <SectionHeading eyebrow={t('events')} title="Upcoming on campus" align="left" action={<Link to="/events" className="btn-outline">{t('viewAll')}</Link>} />
          <AsyncBlock loading={events.loading} error={events.error} onRetry={events.reload} empty={!events.data?.length} emptyProps={{ title: 'No upcoming events' }}>
            <div className="grid gap-6 md:grid-cols-3">{events.data?.map((e) => <EventCard key={e._id} item={e} />)}</div>
          </AsyncBlock>
        </div>
      </section>

      <section id="gallery" className="section scroll-mt-28 bg-white">
        <div className="container-x">
          <SectionHeading eyebrow="Gallery" title={t('campusGallery')} />
          <Tabs className="mb-8 justify-center" value={cat} onChange={setCat} tabs={CATS.map((c) => ({ value: c, label: c === 'all' ? t('all') : c[0].toUpperCase() + c.slice(1) }))} />
          <AsyncBlock loading={gallery.loading} error={gallery.error} onRetry={gallery.reload} empty={!gallery.data?.length} emptyProps={{ title: 'No photos in this category yet' }}>
            <div className="columns-2 gap-4 md:columns-3 lg:columns-4 [&>*]:mb-4">
              {gallery.data?.map((g) => (
                <button key={g._id} type="button" onClick={() => setLightbox(g)} className="group relative block w-full overflow-hidden rounded-2xl" aria-label={`Open ${g.title}`}>
                  <Img src={g.image} alt={g.title} className="w-full transition duration-500 group-hover:scale-105" />
                  <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-primary-950/80 to-transparent p-3 text-start text-sm font-medium text-white opacity-0 transition group-hover:opacity-100">{g.title}</span>
                </button>
              ))}
            </div>
          </AsyncBlock>
        </div>
      </section>

      <AnimatePresence>
        {lightbox && (
          <motion.div className="fixed inset-0 z-[90] flex items-center justify-center bg-primary-950/90 p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setLightbox(null)} role="dialog" aria-label={lightbox.title}>
            <button type="button" className="absolute end-6 top-6 rounded-full bg-white/10 p-2 text-white" aria-label="Close"><X className="h-6 w-6" /></button>
            <motion.figure initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="max-h-full max-w-5xl" onClick={(e) => e.stopPropagation()}>
              <Img src={lightbox.image} alt={lightbox.title} className="max-h-[80vh] w-auto rounded-2xl" />
              <figcaption className="mt-3 text-center text-white">{lightbox.title}{lightbox.description ? ` — ${lightbox.description}` : ''}</figcaption>
            </motion.figure>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
