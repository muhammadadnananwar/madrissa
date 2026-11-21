import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, Globe, GraduationCap, LogIn, Mail, Menu, Phone, Search, X } from 'lucide-react';
import Logo from './Logo';
import SearchModal from './SearchModal';
import { useSite } from '../context/SiteContext';
import { isPlaceholderText } from '../utils/format';
import { PORTAL_URL } from '../services/api';

export const NAV = [
  { key: 'home', to: '/' },
  { key: 'about', to: '/about', children: [
    { label: 'About the Jamia', to: '/about' }, { label: 'Islah-e-Batin', to: '/departments/department-of-islah-e-batin-spiritual-reformation' }, { label: 'Leadership', to: '/about#leadership' }, { label: 'Rules & Regulations', to: '/pages/rules-and-regulations' },
  ] },
  { key: 'academics', to: '/academics', children: [
    { label: 'All Programs & Courses', to: '/academics' }, { label: 'Hifz & Tajweed (Quran)', to: '/academics?level=quran' }, { label: 'Dars-e-Nizami', to: '/academics?level=dars_nizami' },
    { label: 'Takhassus fil Fiqh al-Hanafi', to: '/academics?level=specialization' }, { label: 'Online Courses', to: '/academics?mode=online' }, { label: 'Short Courses (Men & Women)', to: '/academics?level=short_course' },
    { label: 'Academic Calendar', to: '/news-events?tab=calendar' },
  ] },
  { key: 'admissions', to: '/admissions', children: [
    { label: 'Admission Information', to: '/admissions' }, { label: 'Apply Online', to: '/admissions/apply' }, { label: 'Track Application', to: '/admissions/track' },
    { label: 'Merit Lists', to: '/admissions/merit-lists' }, { label: 'Rules & Regulations', to: '/pages/rules-and-regulations' }, { label: 'Download Prospectus', to: '/downloads?category=prospectus' },
  ] },
  { key: 'departments', to: '/departments' },
  { key: 'campusLife', to: '/campus-life' },
  { key: 'newsEvents', to: '/news-events', children: [
    { label: 'News', to: '/news' }, { label: 'Events', to: '/events' }, { label: 'Announcements', to: '/news-events?tab=announcements' },
    { label: 'Examination Notices', to: '/news-events?tab=examination' }, { label: 'Academic Calendar', to: '/news-events?tab=calendar' }, { label: 'Download Center', to: '/downloads' },
  ] },
  { key: 'faculty', to: '/faculty' },
  { key: 'contact', to: '/contact' },
];

function TopBar({ onSearch }) {
  const { settings, t, toggleLang } = useSite();
  const phone = settings?.contact?.phones?.find((p) => !isPlaceholderText(p));
  const email = settings?.contact?.emails?.find((e) => !isPlaceholderText(e));

  return (
    <div className="hidden bg-primary-950 text-xs text-primary-100 lg:block">
      <div className="container-x flex h-10 items-center justify-between">
        <div className="flex items-center gap-5">
          {phone && <a href={`tel:${phone.replace(/\s/g, '')}`} className="flex items-center gap-1.5 hover:text-gold-300"><Phone className="h-3.5 w-3.5" />{phone}</a>}
          {email && <a href={`mailto:${email}`} className="flex items-center gap-1.5 hover:text-gold-300"><Mail className="h-3.5 w-3.5" />{email}</a>}
          {!phone && !email && <span className="text-primary-300">{settings?.tagline}</span>}
        </div>
        <div className="flex items-center gap-5">
          <Link to="/downloads" className="hover:text-gold-300">{t('downloads')}</Link>
          <Link to="/admissions/track" className="hover:text-gold-300">{t('trackApplication')}</Link>
          <button type="button" onClick={onSearch} className="flex items-center gap-1.5 hover:text-gold-300"><Search className="h-3.5 w-3.5" />{t('search')}</button>
          <button type="button" onClick={toggleLang} className="flex items-center gap-1.5 hover:text-gold-300" aria-label="Switch language"><Globe className="h-3.5 w-3.5" />{t('language')}</button>
          <a href={`${PORTAL_URL}/login`} className="flex items-center gap-1.5 hover:text-gold-300"><GraduationCap className="h-3.5 w-3.5" />{t('studentPortal')}</a>
          <a href={`${PORTAL_URL}/login`} className="flex items-center gap-1.5 hover:text-gold-300"><LogIn className="h-3.5 w-3.5" />{t('staffLogin')}</a>
        </div>
      </div>
    </div>
  );
}

function DesktopItem({ item, t }) {
  const [open, setOpen] = useState(false);
  const linkCls = ({ isActive }) => `relative flex items-center gap-1 px-2.5 py-2 text-[13px] font-semibold transition 2xl:px-3.5 2xl:text-sm ${isActive ? 'text-primary-700' : 'text-slate-700 hover:text-primary-700'}`;
  if (!item.children) {
    return <NavLink to={item.to} end={item.to === '/'} className={linkCls}>{t(item.key)}</NavLink>;
  }
  return (
    <div className="relative" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <NavLink to={item.to} className={linkCls} aria-haspopup="true" aria-expanded={open} onFocus={() => setOpen(true)}>
        {t(item.key)} <ChevronDown className={`h-3.5 w-3.5 transition ${open ? 'rotate-180' : ''}`} />
      </NavLink>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} transition={{ duration: 0.15 }}
            className="absolute start-0 top-full z-50 w-60 pt-2">
            <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white p-2 shadow-lift">
              {item.children.map((c) => (
                <Link key={c.to} to={c.to} onClick={() => setOpen(false)} onBlur={() => setOpen(false)}
                  className="block rounded-xl px-3.5 py-2.5 text-sm text-slate-700 transition hover:bg-primary-50 hover:text-primary-700">
                  {c.label}
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Navbar() {
  const { t, toggleLang, settings } = useSite();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => { setMobileOpen(false); }, [location.pathname, location.search]);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setSearchOpen(true); }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('scroll', onScroll); window.removeEventListener('keydown', onKey); };
  }, []);

  const banner = settings?.admissionBanner;

  return (
    <>
      {banner?.enabled && banner.text && (
        <Link to={banner.link || '/admissions'} className="block bg-gradient-to-r from-gold-500 via-gold-400 to-gold-500 py-2 text-center text-xs font-semibold text-primary-950 sm:text-sm">
          <span className="container-x block truncate">{banner.text} →</span>
        </Link>
      )}
      <TopBar onSearch={() => setSearchOpen(true)} />
      <header className={`sticky top-0 z-50 border-b transition-all duration-300 ${scrolled ? 'border-slate-200/70 bg-white/90 shadow-soft backdrop-blur-xl' : 'border-transparent bg-white'}`}>
        <div className="container-x flex h-20 items-center justify-between gap-4">
          <Logo compact={scrolled} />
          <nav className="hidden items-center xl:flex" aria-label="Main navigation">
            {NAV.filter((i) => i.key !== 'home').map((item) => <DesktopItem key={item.key} item={item} t={t} />)}
          </nav>
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setSearchOpen(true)} className="btn-icon xl:hidden" aria-label={t('search')}><Search className="h-5 w-5" /></button>
            <Link to="/admissions/apply" className="btn-gold hidden sm:inline-flex">{t('applyNow')}</Link>
            <button type="button" onClick={() => setMobileOpen(true)} className="btn-icon xl:hidden" aria-label="Open menu"><Menu className="h-6 w-6" /></button>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div className="fixed inset-0 z-[70] bg-primary-950/60 backdrop-blur-sm xl:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setMobileOpen(false)}>
            <motion.aside className="absolute inset-y-0 end-0 flex w-[86%] max-w-sm flex-col bg-white shadow-2xl" initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 28, stiffness: 260 }} onClick={(e) => e.stopPropagation()} aria-label="Mobile navigation">
              <div className="flex items-center justify-between border-b px-5 py-4">
                <Logo compact />
                <button type="button" onClick={() => setMobileOpen(false)} className="btn-icon" aria-label="Close menu"><X className="h-6 w-6" /></button>
              </div>
              <nav className="flex-1 overflow-y-auto px-3 py-4">
                {NAV.map((item) => (
                  <div key={item.key}>
                    <div className="flex items-center">
                      <NavLink to={item.to} end={item.to === '/'} className={({ isActive }) => `flex-1 rounded-xl px-4 py-3 font-semibold ${isActive ? 'bg-primary-50 text-primary-700' : 'text-slate-800'}`}>{t(item.key)}</NavLink>
                      {item.children && (
                        <button type="button" className="btn-icon" onClick={() => setExpanded(expanded === item.key ? null : item.key)} aria-label={`Expand ${t(item.key)}`}>
                          <ChevronDown className={`h-5 w-5 transition ${expanded === item.key ? 'rotate-180' : ''}`} />
                        </button>
                      )}
                    </div>
                    {item.children && expanded === item.key && (
                      <div className="mb-2 ms-4 border-s-2 border-gold-300 ps-3">
                        {item.children.map((c) => <Link key={c.to} to={c.to} className="block rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-primary-50">{c.label}</Link>)}
                      </div>
                    )}
                  </div>
                ))}
              </nav>
              <div className="space-y-2 border-t p-4">
                <Link to="/admissions/apply" className="btn-gold w-full">{t('applyNow')}</Link>
                <div className="grid grid-cols-2 gap-2">
                  <a href={`${PORTAL_URL}/login`} className="btn-outline">{t('studentPortal')}</a>
                  <a href={`${PORTAL_URL}/login`} className="btn-outline">{t('staffLogin')}</a>
                </div>
                <button type="button" onClick={toggleLang} className="btn w-full text-primary-700"><Globe className="h-4 w-4" />{t('language')}</button>
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
