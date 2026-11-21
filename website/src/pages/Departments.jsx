import { Link, useParams } from 'react-router-dom';
import { ArrowRight, BookOpen, Mail, Phone, Quote } from 'lucide-react';
import Seo from '../components/Seo';
import { FacultyCard, PageHero } from '../components/common';
import { AsyncBlock, ErrorState, Img, PageLoader, PlaceholderBadge, Reveal, RichText, SectionHeading } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import { levelLabel, modeLabel } from '../utils/programs';
import NotFound from './NotFound';

export function DepartmentList() {
  const { t, pick, lang } = useSite();
  const { data, loading, error, reload } = useFetch('/public/departments');
  return (
    <>
      <Seo title="Departments" description="Departments (shuba jaat) of Jamia Muhammadia Saifia, Ravi Rayyan Sharif." />
      <PageHero title={t('ourDepartments')} subtitle="From Hifz and Dars-e-Nizami to Darul Ifta and Islah-e-Batin — the departments (shuba jaat) of the Jamia." crumbs={[{ label: t('departments') }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x">
          <AsyncBlock loading={loading} error={error} onRetry={reload} empty={!data?.length} emptyProps={{ title: 'No departments yet' }}>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data?.map((d, i) => (
                <Reveal key={d._id} delay={(i % 3) * 0.05}>
                  <Link to={`/departments/${d.slug}`} className="card card-hover group flex h-full flex-col overflow-hidden">
                    <div className="relative h-52 overflow-hidden">
                      <Img src={d.image} alt={d.name} className="h-full w-full object-cover transition duration-700 group-hover:scale-110" />
                      <div className="absolute inset-0 bg-gradient-to-t from-primary-950/70 to-transparent" />
                      <span className="badge absolute start-4 top-4 bg-gold-400 font-semibold text-primary-950">{d.code}</span>
                      <PlaceholderBadge show={d.isPlaceholder} className="absolute end-4 top-4" />
                    </div>
                    <div className="flex flex-1 flex-col p-6">
                      {d.faculty && <p className="text-xs font-semibold uppercase tracking-wider text-gold-600">{d.faculty}</p>}
                      <h2 className={`mt-2 font-display text-2xl font-bold ${lang === 'ur' && d.nameUr ? 'urdu' : ''}`}>{pick(d, 'name')}</h2>
                      {lang !== 'ur' && d.nameUr && <p dir="rtl" className="urdu text-start text-base text-primary-600">{d.nameUr}</p>}
                      <p className={`mt-2 line-clamp-3 text-sm text-slate-600 ${lang === 'ur' && d.shortDescriptionUr ? 'urdu' : ''}`}>{pick(d, 'shortDescription')}</p>
                      <div className="mt-auto flex items-center justify-between pt-5 text-sm">
                        <span className="flex items-center gap-1.5 text-slate-500"><BookOpen className="h-4 w-4" />{d.programCount} programs</span>
                        <ArrowRight className="h-5 w-5 text-gold-500 transition group-hover:translate-x-1 rtl:rotate-180" />
                      </div>
                    </div>
                  </Link>
                </Reveal>
              ))}
            </div>
          </AsyncBlock>
        </div>
      </section>
    </>
  );
}

export function DepartmentDetail() {
  const { slug } = useParams();
  const { t, pick, lang } = useSite();
  const { data: d, loading, error, status, reload } = useFetch(`/public/departments/${slug}`);
  if (loading && !d) return <PageLoader className="min-h-[60vh]" />;
  if (status === 404) return <NotFound />;
  if (error) return <ErrorState message={error} onRetry={reload} className="min-h-[60vh]" />;

  const gallery = [...(d.gallery || []).map((g) => ({ image: g, title: d.name })), ...(d.galleryItems || [])];

  return (
    <>
      <Seo title={d.name} description={d.shortDescription} image={d.image} />
      <PageHero title={pick(d, 'name')} subtitle={d.shortDescription} image={d.image} crumbs={[{ label: t('departments'), to: '/departments' }, { label: d.name }]}>
        {lang !== 'ur' && d.nameUr && <p dir="rtl" className="urdu mt-3 text-start text-2xl text-gold-300">{d.nameUr}</p>}
        <div className="mt-6 flex flex-wrap gap-3 text-sm text-primary-100">
          {d.contactEmail && <a href={`mailto:${d.contactEmail}`} className="flex items-center gap-2 hover:text-gold-300"><Mail className="h-4 w-4" />{d.contactEmail}</a>}
          {d.contactPhone && <span className="flex items-center gap-2"><Phone className="h-4 w-4" />{d.contactPhone}</span>}
          <PlaceholderBadge show={d.isPlaceholder} />
        </div>
      </PageHero>

      <section className="section bg-white">
        <div className="container-x grid gap-12 lg:grid-cols-3">
          <Reveal className="lg:col-span-2">
            <span className="eyebrow">{t('introduction')}</span>
            <RichText text={d.introduction || d.shortDescription} className="mt-4 text-lg" />
          </Reveal>
          {(d.headName || d.headMessage) && (
            <Reveal delay={0.1} className="rounded-3xl bg-primary-900 p-8 text-white">
              <Quote className="h-8 w-8 text-gold-400" />
              {d.headMessage && <p className="mt-4 font-display text-xl leading-relaxed">{d.headMessage}</p>}
              <p className="mt-6 font-semibold">{d.headName}</p>
              <p className="text-sm text-gold-300">{d.headDesignation || 'Head of Department'}</p>
            </Reveal>
          )}
        </div>
      </section>

      <section className="section bg-surface">
        <div className="container-x">
          <SectionHeading eyebrow={t('programs')} title="Programs Offered" align="left" />
          {d.programs?.length ? (
            <div className="grid gap-4 md:grid-cols-2">
              {d.programs.map((p) => (
                <Link key={p._id} to={`/academics/programs/${p.slug}`} className="card card-hover flex items-center justify-between gap-4 p-6">
                  <div>
                    <span className="badge bg-primary-50 text-primary-700">{levelLabel(p.level, lang)}</span>
                    {p.deliveryMode === 'online' && <span className="badge ms-2 bg-gold-50 text-gold-700">{modeLabel('online', lang)}</span>}
                    <h3 className="mt-2 font-sans text-lg font-semibold text-primary-900">{pick(p, 'title')}</h3>
                    {lang !== 'ur' && p.titleUr && <p dir="rtl" className="urdu text-start text-sm text-primary-600">{p.titleUr}</p>}
                    <p className="text-sm text-slate-500">{p.duration}</p>
                  </div>
                  <ArrowRight className="h-5 w-5 shrink-0 text-gold-500 rtl:rotate-180" />
                </Link>
              ))}
            </div>
          ) : <p className="text-slate-500">No programs listed yet.</p>}
        </div>
      </section>

      {d.faculty?.length > 0 && (
        <section className="section bg-white">
          <div className="container-x">
            <SectionHeading eyebrow={t('faculty')} title="Faculty Members" align="left"
              action={<Link to={`/faculty?department=${d._id}`} className="btn-outline">{t('viewAll')}</Link>} />
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {d.faculty.map((f) => <FacultyCard key={f._id} member={{ ...f, department: { name: d.name, nameUr: d.nameUr } }} />)}
            </div>
          </div>
        </section>
      )}

      {gallery.length > 0 && (
        <section className="section bg-surface">
          <div className="container-x">
            <SectionHeading eyebrow="Gallery" title="Department Gallery" align="left" />
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {gallery.map((g, i) => (
                // eslint-disable-next-line react/no-array-index-key
                <Img key={i} src={g.image} alt={g.title} className="h-48 w-full rounded-2xl object-cover" />
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
