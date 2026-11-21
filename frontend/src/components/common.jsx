import { useEffect } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Calendar, ChevronRight, Clock, MapPin, MessageCircle, Users, Wifi } from 'lucide-react';
import { useSite } from '../context/SiteContext';
import { useAuth } from '../context/AuthContext';
import { Img, PageLoader, PlaceholderBadge } from './ui';
import { formatDate, titleCase } from '../utils/format';
import { hasUrdu, levelLabel, modeLabel } from '../utils/programs';
import { homeFor } from '../utils/roles';

/* Scroll to top (or to #hash) on navigation */
export function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      const el = document.getElementById(hash.slice(1));
      if (el) { setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120); return; }
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname, hash]);
  return null;
}

/* Guards authenticated areas by role. */
export function ProtectedRoute({ children, roles, redirectTo = '/login' }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <PageLoader className="min-h-screen" />;
  if (!user) return <Navigate to={redirectTo} replace state={{ from: location }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to={homeFor(user.role)} replace />;
  return children;
}

/* Floating WhatsApp inquiry button (shown only when a number is configured). */
export function WhatsAppButton() {
  const { settings, t } = useSite();
  const number = String(settings?.whatsappNumber || '').replace(/\D/g, '');
  if (!number) return null;
  const text = encodeURIComponent(`Assalam-o-Alaikum, I have an inquiry about ${settings?.shortName || 'UMS'}.`);
  return (
    <a href={`https://wa.me/${number}?text=${text}`} target="_blank" rel="noopener noreferrer" aria-label={t('whatsapp')}
      className="no-print group fixed bottom-6 end-6 z-40 flex items-center gap-2 rounded-full bg-[#25D366] p-4 text-white shadow-lift transition hover:scale-105">
      <MessageCircle className="h-6 w-6" />
      <span className="hidden max-w-0 overflow-hidden whitespace-nowrap text-sm font-semibold transition-all duration-300 group-hover:max-w-xs sm:inline">{t('whatsapp')}</span>
    </a>
  );
}

/* Inner page hero banner with breadcrumbs */
export function PageHero({ title, subtitle, image, crumbs = [], children }) {
  const { settings } = useSite();
  const bg = image || settings?.hero?.image;
  return (
    <section className="relative isolate overflow-hidden bg-primary-900">
      {bg && <Img src={bg} alt="" className="absolute inset-0 -z-10 h-full w-full object-cover opacity-25" />}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-primary-950/95 via-primary-900/85 to-primary-700/70" />
      <div className="absolute inset-0 -z-10 bg-crest-pattern [background-size:26px_26px] opacity-30" />
      <div className="container-x py-16 sm:py-20 lg:py-24">
        <nav aria-label="Breadcrumb" className="mb-5 flex flex-wrap items-center gap-1 text-xs font-medium text-primary-200">
          <Link to="/" className="hover:text-gold-300">Home</Link>
          {crumbs.map((c) => (
            <span key={c.label} className="flex items-center gap-1">
              <ChevronRight className="h-3.5 w-3.5 rtl:rotate-180" />
              {c.to ? <Link to={c.to} className="hover:text-gold-300">{c.label}</Link> : <span className="text-gold-300">{c.label}</span>}
            </span>
          ))}
        </nav>
        <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
          className={`max-w-4xl text-balance text-4xl font-bold text-white sm:text-5xl lg:text-6xl ${hasUrdu(title) ? 'urdu' : ''}`}>{title}</motion.h1>
        {subtitle && (
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
            className={`mt-5 max-w-2xl text-base leading-relaxed text-primary-100 sm:text-lg ${hasUrdu(subtitle) && !/[a-z]/i.test(subtitle) ? 'urdu' : ''}`}>{subtitle}</motion.p>
        )}
        {children}
      </div>
      <div className="gold-rule" />
    </section>
  );
}

/* ---------------------------------- Cards --------------------------------- */
export function ProgramCard({ program }) {
  const { lang, pick } = useSite();
  const title = pick(program, 'title');
  const secondary = lang === 'ur' ? (program.titleUr ? program.title : '') : program.titleUr;
  return (
    <Link to={`/academics/programs/${program.slug}`} className="card card-hover group flex h-full flex-col overflow-hidden">
      <div className="relative h-48 overflow-hidden">
        <Img src={program.image} alt={program.title} className="h-full w-full object-cover transition duration-700 group-hover:scale-110" />
        <div className="absolute inset-0 bg-gradient-to-t from-primary-950/70 to-transparent" />
        <span className="badge absolute start-4 top-4 bg-white/95 text-primary-800">{levelLabel(program.level, lang)}</span>
        {program.deliveryMode === 'online' && <span className="badge absolute bottom-4 start-4 bg-gold-400 font-semibold text-primary-950"><Wifi className="h-3 w-3" />{modeLabel('online', lang)}</span>}
        <PlaceholderBadge show={program.isPlaceholder} className="absolute end-4 top-4" />
      </div>
      <div className="flex flex-1 flex-col p-6">
        {program.department && <p className="text-xs font-semibold uppercase tracking-wider text-gold-600">{pick(program.department, 'name')}</p>}
        <h3 className={`mt-2 font-display text-2xl font-bold leading-snug text-primary-900 group-hover:text-primary-700 ${hasUrdu(title) ? 'urdu' : ''}`}>{title}</h3>
        {secondary && <p className={`text-sm text-primary-600 ${hasUrdu(secondary) ? 'urdu' : ''}`} dir="auto">{secondary}</p>}
        {program.shortDescription && <p className="mt-2 line-clamp-2 text-sm text-slate-600">{program.shortDescription}</p>}
        <div className="mt-auto flex items-center justify-between gap-2 pt-5 text-sm">
          <span className="flex items-center gap-1.5 text-slate-500">
            {program.duration ? <><Clock className="h-4 w-4" />{program.duration}</> : null}
            {program.audience && <span className="badge bg-primary-50 text-primary-700"><Users className="h-3 w-3" />{program.audience}</span>}
          </span>
          <ArrowRight className="h-5 w-5 shrink-0 text-gold-500 transition group-hover:translate-x-1 rtl:rotate-180" />
        </div>
      </div>
    </Link>
  );
}

export function NewsCard({ item }) {
  return (
    <Link to={`/news/${item.slug}`} className="card card-hover group flex h-full flex-col overflow-hidden">
      <div className="relative h-52 overflow-hidden">
        <Img src={item.coverImage} alt={item.title} className="h-full w-full object-cover transition duration-700 group-hover:scale-110" />
        <PlaceholderBadge show={item.isPlaceholder} className="absolute end-4 top-4" />
      </div>
      <div className="flex flex-1 flex-col p-6">
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="badge bg-primary-50 capitalize text-primary-700">{item.category}</span>
          <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{formatDate(item.publishedAt)}</span>
        </div>
        <h3 className="mt-3 line-clamp-2 font-sans text-lg font-semibold leading-snug text-primary-900 group-hover:text-primary-700">{item.title}</h3>
        {item.excerpt && <p className="mt-2 line-clamp-2 text-sm text-slate-600">{item.excerpt}</p>}
        <span className="mt-auto flex items-center gap-1 pt-4 text-sm font-semibold text-primary-700">Read more <ArrowRight className="h-4 w-4 rtl:rotate-180" /></span>
      </div>
    </Link>
  );
}

export function EventCard({ item, horizontal = false }) {
  const d = new Date(item.startDate);
  return (
    <Link to={`/events/${item.slug}`} className={`card card-hover group flex overflow-hidden ${horizontal ? 'flex-row items-stretch' : 'h-full flex-col'}`}>
      <div className={`flex shrink-0 flex-col items-center justify-center bg-primary-800 text-white ${horizontal ? 'w-24' : 'py-5'}`}>
        <span className="font-display text-4xl font-bold leading-none text-gold-300">{d.getDate()}</span>
        <span className="mt-1 text-xs font-semibold uppercase tracking-widest">{d.toLocaleString('en', { month: 'short' })} {d.getFullYear()}</span>
      </div>
      <div className="flex flex-1 flex-col p-5">
        <div className="flex items-center gap-2">
          <span className="badge bg-gold-50 capitalize text-gold-700">{titleCase(item.category)}</span>
          <PlaceholderBadge show={item.isPlaceholder} />
        </div>
        <h3 className="mt-2 line-clamp-2 font-sans text-base font-semibold text-primary-900 group-hover:text-primary-700">{item.title}</h3>
        {item.venue && <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-500"><MapPin className="h-3.5 w-3.5" />{item.venue}</p>}
      </div>
    </Link>
  );
}

export function FacultyCard({ member }) {
  const { lang, pick } = useSite();
  const name = pick(member, 'name');
  const designation = pick(member, 'designation');
  const secondary = lang === 'ur' ? '' : member.nameUr;
  return (
    <Link to={`/faculty/${member.slug}`} className="card card-hover group flex h-full flex-col items-center p-6 text-center">
      <div className="relative">
        <div className="absolute -inset-1 rounded-full bg-gradient-to-br from-gold-300 to-primary-500 opacity-70" />
        <Img src={member.photo} alt={member.name} className="relative h-28 w-28 rounded-full border-4 border-white object-cover" fallbackClass="rounded-full" />
      </div>
      <h3 className={`mt-5 font-sans text-base font-semibold text-primary-900 group-hover:text-primary-700 ${hasUrdu(name) ? 'urdu' : ''}`}>{name}</h3>
      {secondary && <p className="urdu text-sm text-primary-600" dir="rtl">{secondary}</p>}
      <p className={`mt-1 text-sm font-medium text-gold-600 ${hasUrdu(designation) ? 'urdu' : ''}`}>{designation}</p>
      {member.department && <p className="mt-1 text-xs text-slate-500">{pick(member.department, 'name')}</p>}
      <PlaceholderBadge show={member.isPlaceholder} className="mt-3" />
    </Link>
  );
}
