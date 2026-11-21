import { useState } from 'react';
import toast from 'react-hot-toast';
import { CheckCircle2, Clock, Mail, MapPin, MessageCircle, Phone, Send } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { SOCIAL_ICONS } from '../components/Footer';
import { Input, Select, Textarea } from '../components/form';
import { Reveal, Spinner } from '../components/ui';
import { useSite } from '../context/SiteContext';
import { useFetch } from '../hooks/useFetch';
import api, { errorMessage, fieldErrors } from '../services/api';
import { isPlaceholderText } from '../utils/format';

const empty = { name: '', email: '', phone: '', subject: '', department: '', message: '' };

export default function Contact() {
  const { settings, t } = useSite();
  const { data: departments } = useFetch('/public/departments');
  const [form, setForm] = useState(empty);
  const [errors, setErrors] = useState({});
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const c = settings?.contact || {};
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const mapQuery = c.mapQuery || (!isPlaceholderText(c.address) && c.address ? `${c.address} ${c.city || ''}` : '');
  const whatsapp = String(settings?.whatsappNumber || '').replace(/\D/g, '');
  const social = Object.entries(settings?.social || {}).filter(([k, v]) => v && SOCIAL_ICONS[k]);

  const submit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (form.name.trim().length < 2) errs.name = 'Please enter your name';
    if (!/^\S+@\S+\.\S+$/.test(form.email)) errs.email = 'Please enter a valid email';
    if (form.subject.trim().length < 3) errs.subject = 'Subject is required';
    if (form.message.trim().length < 10) errs.message = 'Message must be at least 10 characters';
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setSending(true);
    try {
      const { data } = await api.post('/public/contact', form);
      toast.success(data.message);
      setSent(true);
      setForm(empty);
    } catch (ex) {
      setErrors(fieldErrors(ex));
      toast.error(errorMessage(ex));
    } finally {
      setSending(false);
    }
  };

  const items = [
    [MapPin, 'Address', [c.address, c.city].filter(Boolean).join(', ')],
    [Phone, 'Phone', c.phones?.join(' · ')],
    [Mail, 'Email', c.emails?.join(' · ')],
    [Clock, 'Office hours', c.officeHours],
  ].filter(([, , v]) => v);

  return (
    <>
      <Seo title="Contact Us" description="Get in touch with the University of Muhammadia Saifia." />
      <PageHero title={t('contactUs')} subtitle="Questions about admissions, programs or campus life? We're here to help." crumbs={[{ label: t('contact') }]} />
      <section className="section bg-surface pt-12">
        <div className="container-x grid gap-8 lg:grid-cols-5">
          <Reveal className="space-y-4 lg:col-span-2">
            {items.map(([Icon, label, value]) => (
              <div key={label} className="card flex gap-4 p-6">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary-700 text-gold-300"><Icon className="h-5 w-5" /></span>
                <div><p className="text-xs font-semibold uppercase tracking-widest text-slate-500">{label}</p><p className="mt-1 font-medium text-primary-900">{value}</p></div>
              </div>
            ))}
            {whatsapp && (
              <a href={`https://wa.me/${whatsapp}`} target="_blank" rel="noopener noreferrer" className="card flex items-center gap-4 p-6 transition hover:shadow-lift">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#25D366] text-white"><MessageCircle className="h-5 w-5" /></span>
                <span className="font-semibold text-primary-900">{t('whatsapp')}</span>
              </a>
            )}
            {social.length > 0 && (
              <div className="card p-6">
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">{t('followUs')}</p>
                <div className="mt-3 flex gap-2">
                  {social.map(([k, url]) => {
                    const Icon = SOCIAL_ICONS[k];
                    return <a key={k} href={url} target="_blank" rel="noopener noreferrer" aria-label={k} className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-50 text-primary-700 transition hover:bg-primary-700 hover:text-white"><Icon className="h-4 w-4" /></a>;
                  })}
                </div>
              </div>
            )}
          </Reveal>

          <Reveal delay={0.1} className="card p-8 lg:col-span-3">
            {sent ? (
              <div className="flex h-full flex-col items-center justify-center py-12 text-center">
                <CheckCircle2 className="h-14 w-14 text-emerald-500" />
                <h2 className="mt-4 text-2xl font-bold">Message sent</h2>
                <p className="mt-2 text-slate-600">Thank you for contacting us. Our team will respond as soon as possible.</p>
                <button type="button" className="btn-outline mt-6" onClick={() => setSent(false)}>Send another message</button>
              </div>
            ) : (
              <form onSubmit={submit} noValidate className="grid gap-5 sm:grid-cols-2">
                <h2 className="font-sans text-xl font-semibold sm:col-span-2">Send us a message</h2>
                <Input label="Full name" required value={form.name} onChange={set('name')} error={errors.name} autoComplete="name" />
                <Input label="Email" type="email" required value={form.email} onChange={set('email')} error={errors.email} autoComplete="email" />
                <Input label="Phone" type="tel" value={form.phone} onChange={set('phone')} error={errors.phone} autoComplete="tel" />
                <Select label="Department (optional)" value={form.department} onChange={set('department')} placeholder="General inquiry" options={(departments || []).map((d) => d.name)} />
                <Input label="Subject" required className="sm:col-span-2" value={form.subject} onChange={set('subject')} error={errors.subject} />
                <Textarea label="Message" required rows={6} className="sm:col-span-2" value={form.message} onChange={set('message')} error={errors.message} />
                <div className="sm:col-span-2">
                  <button type="submit" className="btn-primary" disabled={sending}>{sending ? <Spinner className="h-4 w-4" /> : <Send className="h-4 w-4" />} {t('send')}</button>
                </div>
              </form>
            )}
          </Reveal>
        </div>
      </section>

      <section className="bg-white">
        {mapQuery ? (
          <iframe title="University location on Google Maps" className="h-[26rem] w-full border-0" loading="lazy" referrerPolicy="no-referrer-when-downgrade"
            src={`https://www.google.com/maps?q=${encodeURIComponent(mapQuery)}&output=embed`} />
        ) : (
          <div className="flex h-64 flex-col items-center justify-center gap-2 bg-primary-50 text-center text-primary-700">
            <MapPin className="h-8 w-8" />
            <p className="font-semibold">Map will appear here</p>
            <p className="max-w-md text-sm text-slate-500">Set the university location in Admin &gt; Settings &gt; Contact (“Map location”) to enable the Google Maps embed.</p>
          </div>
        )}
      </section>
    </>
  );
}
