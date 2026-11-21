import { Link } from 'react-router-dom';
import { Clock, Facebook, Instagram, Linkedin, Mail, MapPin, Phone, Twitter, Youtube } from 'lucide-react';
import Logo from './Logo';
import { useSite } from '../context/SiteContext';

export const SOCIAL_ICONS = { facebook: Facebook, instagram: Instagram, twitter: Twitter, youtube: Youtube, linkedin: Linkedin };

export default function Footer() {
  const { settings, t } = useSite();
  const contact = settings?.contact || {};
  const social = Object.entries(settings?.social || {}).filter(([k, v]) => v && SOCIAL_ICONS[k]);
  const year = new Date().getFullYear();

  const cols = [
    { title: t('quickLinks'), links: [['About the Jamia', '/about'], ['Programs & Courses', '/academics'], ['Online Courses', '/academics?mode=online'], ['Departments', '/departments'], ['Asatiza (Faculty)', '/faculty']] },
    { title: t('admissions'), links: [['Admission Information', '/admissions'], ['Apply Online', '/admissions/apply'], ['Track Application', '/admissions/track'], ['Rules & Regulations', '/pages/rules-and-regulations'], ['Download Center', '/downloads']] },
    { title: 'Resources', links: [['News', '/news'], ['Events', '/events'], ['Academic Calendar', '/news-events?tab=calendar'], ['Student Portal', '/student/login'], ['Staff Login', '/login']] },
  ];

  return (
    <footer className="relative overflow-hidden bg-primary-950 text-primary-100">
      <div className="absolute inset-0 bg-crest-pattern [background-size:28px_28px] opacity-40" aria-hidden="true" />
      <div className="gold-rule relative" />
      <div className="container-x relative grid gap-12 py-16 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <Logo light />
          {settings?.universityNameUr && <p dir="rtl" className="urdu mt-5 text-start text-xl text-gold-300">{settings.universityNameUr}</p>}
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-primary-200">{settings?.footerText}</p>
          {social.length > 0 && (
            <div className="mt-6">
              <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-gold-300">{t('followUs')}</p>
              <div className="flex gap-2">
                {social.map(([k, url]) => {
                  const Icon = SOCIAL_ICONS[k];
                  return (
                    <a key={k} href={url} target="_blank" rel="noopener noreferrer" aria-label={k}
                      className="flex h-10 w-10 items-center justify-center rounded-full border border-white/15 transition hover:border-gold-400 hover:bg-gold-400 hover:text-primary-950">
                      <Icon className="h-4 w-4" />
                    </a>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {cols.map((col) => (
          <div key={col.title} className="lg:col-span-2">
            <h3 className="font-sans text-sm font-semibold uppercase tracking-widest text-gold-300">{col.title}</h3>
            <ul className="mt-5 space-y-3 text-sm">
              {col.links.map(([label, to]) => (
                <li key={to}><Link to={to} className="text-primary-200 transition hover:text-white">{label}</Link></li>
              ))}
            </ul>
          </div>
        ))}

        <div className="lg:col-span-2">
          <h3 className="font-sans text-sm font-semibold uppercase tracking-widest text-gold-300">{t('contactUs')}</h3>
          <ul className="mt-5 space-y-4 text-sm text-primary-200">
            {contact.address && <li className="flex gap-3"><MapPin className="h-4 w-4 shrink-0 text-gold-400" /><span>{contact.address}{contact.city ? `, ${contact.city}` : ''}</span></li>}
            {contact.phones?.map((p) => <li key={p} className="flex gap-3"><Phone className="h-4 w-4 shrink-0 text-gold-400" /><span dir="ltr">{p}</span></li>)}
            {contact.emails?.map((e) => <li key={e} className="flex gap-3"><Mail className="h-4 w-4 shrink-0 text-gold-400" /><span className="break-all">{e}</span></li>)}
            {contact.officeHours && <li className="flex gap-3"><Clock className="h-4 w-4 shrink-0 text-gold-400" /><span>{contact.officeHours}</span></li>}
          </ul>
        </div>
      </div>
      <div className="relative border-t border-white/10">
        <div className="container-x flex flex-col items-center justify-between gap-3 py-6 text-xs text-primary-300 sm:flex-row">
          <p>© {year} {settings?.universityName || 'University of Muhammadia Saifia'}. {t('allRightsReserved')}</p>
          <div className="flex gap-5">
            <Link to="/pages/privacy-policy" className="hover:text-white">{t('privacy')}</Link>
            <Link to="/pages/terms-of-use" className="hover:text-white">{t('terms')}</Link>
            <Link to="/contact" className="hover:text-white">{t('contact')}</Link>
            <Link to="/admin/login" className="hover:text-white">Admin</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
