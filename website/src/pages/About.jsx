import { Link } from 'react-router-dom';
import { Eye, Quote, Target } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { Img, PageLoader, Reveal, SectionHeading } from '../components/ui';
import { useSite } from '../context/SiteContext';
import { getIcon } from '../utils/icons';

function IconGrid({ items, cols = 'lg:grid-cols-3' }) {
  return (
    <div className={`grid gap-6 sm:grid-cols-2 ${cols}`}>
      {items.map((v, i) => {
        const Icon = getIcon(v.icon);
        return (
          // eslint-disable-next-line react/no-array-index-key
          <Reveal key={`${v.title}-${i}`} delay={i * 0.05}>
            <div className="card card-hover h-full p-7">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-50 text-primary-700"><Icon className="h-6 w-6" /></span>
              <h3 className="mt-5 font-sans text-lg font-semibold text-primary-900">{v.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{v.description}</p>
            </div>
          </Reveal>
        );
      })}
    </div>
  );
}

export default function About() {
  const { settings } = useSite();
  if (!settings) return <PageLoader className="min-h-[60vh]" />;
  const about = settings.about || {};
  const leaders = [settings.chancellor, settings.viceChancellor].filter((l) => l?.message);

  return (
    <>
      <Seo title="About UMS" description={about.intro?.slice(0, 160)} />
      <PageHero title={`About ${settings.universityName}`} subtitle={settings.tagline} image={about.image} crumbs={[{ label: 'About' }]} />

      <section className="section bg-white">
        <div className="container-x grid items-center gap-14 lg:grid-cols-2">
          <Reveal>
            <span className="eyebrow">About UMS</span>
            <h2 className="section-title">A legacy of learning and values</h2>
            <p className="mt-6 text-lg leading-relaxed text-slate-600">{about.intro}</p>
            <h3 className="mt-10 text-2xl font-bold">Our History</h3>
            <p className="mt-3 leading-relaxed text-slate-600">{about.history}</p>
          </Reveal>
          <Reveal delay={0.1} className="relative">
            <Img src={about.image || settings.hero?.image} alt="Campus" className="h-[28rem] w-full rounded-[2rem] object-cover shadow-lift" />
            <div className="absolute -bottom-6 -start-6 hidden rounded-3xl bg-gold-400 p-6 shadow-gold sm:block">
              <img src="/logo.svg" alt="" className="h-20 w-auto" />
            </div>
          </Reveal>
        </div>
      </section>

      <section id="vision" className="section scroll-mt-28 bg-primary-900">
        <div className="container-x grid gap-6 md:grid-cols-2">
          {[[Eye, 'Our Vision', about.vision], [Target, 'Our Mission', about.mission]].map(([Icon, title, text]) => (
            <Reveal key={title}>
              <div className="h-full rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur">
                <Icon className="h-10 w-10 text-gold-400" />
                <h2 className="mt-6 text-3xl font-bold text-white">{title}</h2>
                <p className="mt-4 text-lg leading-relaxed text-primary-100">{text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {about.coreValues?.length > 0 && (
        <section className="section bg-surface">
          <div className="container-x">
            <SectionHeading eyebrow="What we stand for" title="Core Values" />
            <IconGrid items={about.coreValues} />
          </div>
        </section>
      )}

      {leaders.length > 0 && (
        <section className="section bg-white">
          <div className="container-x space-y-10">
            {leaders.map((l, i) => (
              <Reveal key={l.title}>
                <div className={`grid items-center gap-10 rounded-[2rem] bg-surface p-8 sm:p-12 lg:grid-cols-3 ${i % 2 ? 'lg:[direction:rtl]' : ''}`}>
                  <Img src={l.photo} alt={l.name} className="h-80 w-full rounded-3xl object-cover lg:[direction:ltr]" />
                  <div className="lg:col-span-2 lg:[direction:ltr]">
                    <span className="eyebrow">{l.title}&apos;s Message</span>
                    <Quote className="mt-4 h-10 w-10 text-gold-400" />
                    <p className="mt-3 font-display text-2xl leading-relaxed text-primary-900">{l.message}</p>
                    <p className="mt-6 font-semibold text-primary-900">{l.name}</p>
                    <p className="text-sm text-gold-600">{l.title}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      {settings.leadership?.length > 0 && (
        <section id="leadership" className="section scroll-mt-28 bg-surface">
          <div className="container-x">
            <SectionHeading eyebrow="Governance" title="University Leadership" />
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {settings.leadership.map((p, i) => (
                // eslint-disable-next-line react/no-array-index-key
                <Reveal key={i} delay={i * 0.05}>
                  <div className="card h-full overflow-hidden text-center">
                    <Img src={p.photo} alt={p.name} className="h-64 w-full object-cover" />
                    <div className="p-5">
                      <p className="font-semibold text-primary-900">{p.name}</p>
                      <p className="text-sm text-gold-600">{p.designation}</p>
                    </div>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      )}

      {about.accreditations?.length > 0 && (
        <section id="accreditation" className="section scroll-mt-28 bg-white">
          <div className="container-x">
            <SectionHeading eyebrow="Recognition" title="Accreditation & Affiliations" description="Official recognition and affiliation details as confirmed by the university." />
            <IconGrid items={about.accreditations} cols="lg:grid-cols-2" />
          </div>
        </section>
      )}

      {about.achievements?.length > 0 && (
        <section className="section bg-surface">
          <div className="container-x">
            <SectionHeading eyebrow="Milestones" title="Achievements" />
            <IconGrid items={about.achievements} />
          </div>
        </section>
      )}

      <section className="bg-primary-800 py-14">
        <div className="container-x flex flex-col items-center justify-between gap-6 text-center sm:flex-row sm:text-start">
          <h2 className="text-3xl font-bold text-white">Ready to become part of UMS?</h2>
          <div className="flex gap-3">
            <Link to="/academics" className="btn-ghost-light">View Programs</Link>
            <Link to="/admissions/apply" className="btn-gold">Apply Now</Link>
          </div>
        </div>
      </section>
    </>
  );
}
