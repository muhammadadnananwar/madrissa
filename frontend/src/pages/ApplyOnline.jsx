import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { ArrowLeft, ArrowRight, BookOpen, Check, CheckCircle2, Copy, FolderUp, GraduationCap, Plus, Printer, Trash2, User } from 'lucide-react';
import Seo from '../components/Seo';
import { PageHero } from '../components/common';
import { Checkbox, FileDrop, Input, Select, Textarea } from '../components/form';
import { PageLoader, Spinner } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import api, { errorMessage, fieldErrors } from '../services/api';
import { levelLabel, modeLabel } from '../utils/programs';

/* Mirrors the Jamia's paper admission form (فارم داخلہ). */
const STEPS = [
  { key: 'personal', label: 'Applicant Details', icon: User },
  { key: 'family', label: 'Family & Education', icon: BookOpen },
  { key: 'program', label: 'Program & Residence', icon: GraduationCap },
  { key: 'documents', label: 'Documents & Declaration', icon: FolderUp },
];

const DOCS = [
  { type: 'photo', label: 'Photograph (تصویر)', required: true, accept: '.jpg,.jpeg,.png', hint: 'JPG or PNG · max 5 MB' },
  { type: 'cnic', label: 'Your CNIC / B-Form copy (شناختی کارڈ / ب فارم)', required: true },
  { type: 'guardianCnic', label: 'Father’s / guardian’s CNIC copy (والد/سرپرست کا شناختی کارڈ)', required: true },
  { type: 'certificates', label: 'Attested copies of certificates (اسناد کی مصدقہ نقول)', hint: 'PDF/JPG/PNG · max 5 MB' },
  { type: 'domicile', label: 'Domicile (optional)' },
  { type: 'other', label: 'Other document (optional)' },
];

// Common darjaat of Dars-e-Nizami plus other sections (free text is also allowed)
const CLASS_LEVELS = ['Hifz', 'Nazira', 'Tajweed', 'Oola (اولیٰ)', 'Saniya (ثانیہ)', 'Salisa (ثالثہ)', 'Rabia (رابعہ)', 'Khamisa (خامسہ)', 'Sadisa (سادسہ)', 'Mauqoof Alaih (موقوف علیہ)', 'Daura-e-Hadith (دورہ حدیث)', 'Takhassus', 'Asri Uloom (عصری علوم)'];
const PROVINCES = ['Punjab', 'Sindh', 'Khyber Pakhtunkhwa', 'Balochistan', 'Islamabad Capital Territory', 'Gilgit-Baltistan', 'Azad Jammu & Kashmir', 'Other'];
const emptyEdu = () => ({ level: 'matric', degreeTitle: '', board: '', institution: '', passingYear: '', totalMarks: '', obtainedMarks: '' });

const formatCnic = (v) => {
  const d = v.replace(/\D/g, '').slice(0, 13);
  if (d.length <= 5) return d;
  if (d.length <= 12) return `${d.slice(0, 5)}-${d.slice(5)}`;
  return `${d.slice(0, 5)}-${d.slice(5, 12)}-${d.slice(12)}`;
};

function validateStep(step, form, files) {
  const e = {};
  const p = form.personal;
  const phoneOk = (v) => /^[+\d][\d\s-]{9,16}$/.test(v);
  if (step === 0) {
    if (p.fullName.trim().length < 3) e['personal.fullName'] = 'Full name is required';
    if (p.cnic.replace(/\D/g, '').length !== 13) e['personal.cnic'] = 'Enter the 13-digit CNIC / B-Form number';
    if (!p.dateOfBirth) e['personal.dateOfBirth'] = 'Date of birth is required';
    if (!p.gender) e['personal.gender'] = 'Select gender';
    if (!phoneOk(p.phone)) e['personal.phone'] = 'Enter a valid mobile number e.g. 03001234567';
    if (p.homePhone && !phoneOk(p.homePhone)) e['personal.homePhone'] = 'Enter a valid phone number';
    if (p.email && !/^\S+@\S+\.\S+$/.test(p.email)) e['personal.email'] = 'Enter a valid email or leave it blank';
    if (p.address.trim().length < 5) e['personal.address'] = 'Permanent address is required';
    if (!p.city.trim()) e['personal.city'] = 'City is required';
  }
  if (step === 1) {
    if (p.fatherName.trim().length < 3) e['personal.fatherName'] = "Father's name is required";
    if (p.fatherCnic.replace(/\D/g, '').length !== 13) e['personal.fatherCnic'] = "Enter the father's 13-digit CNIC";
    if (form.qualification.trim().length < 2) e.qualification = 'Enter your qualification and institution';
    form.education.forEach((ed, i) => {
      if (ed.totalMarks !== '' && !(Number(ed.totalMarks) > 0)) e[`education.${i}.totalMarks`] = 'Must be greater than 0';
      if (ed.totalMarks !== '' && (ed.obtainedMarks === '' || Number(ed.obtainedMarks) < 0 || Number(ed.obtainedMarks) > Number(ed.totalMarks))) e[`education.${i}.obtainedMarks`] = 'Must be ≤ total marks';
    });
  }
  if (step === 2 && !form.program) e.program = 'Please select a program';
  if (step === 3) {
    DOCS.filter((d) => d.required).forEach((d) => { if (!files[d.type]) e[`documents.${d.type}`] = 'This document is required'; });
    if (!form.declarationAccepted) e.declarationAccepted = 'Please confirm the declaration';
    if (!form.rulesAccepted) e.rulesAccepted = 'Please agree to the rules & regulations';
  }
  return e;
}

const stepOfField = (k) => {
  if (k.startsWith('personal.father') || k.startsWith('education') || ['qualification', 'quranStatus', 'previousMadrasa'].includes(k) || k.startsWith('guardian')) return 1;
  if (k.startsWith('personal')) return 0;
  if (['program', 'secondChoice', 'classLevel', 'residence'].includes(k)) return 2;
  return 3;
};

function Success({ result }) {
  const copy = () => navigator.clipboard?.writeText(result.applicationNumber).then(() => toast.success('Application number copied'));
  return (
    <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="card mx-auto max-w-2xl p-10 text-center">
      <span className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-emerald-50 text-emerald-600"><CheckCircle2 className="h-10 w-10" /></span>
      <h2 className="mt-6 text-3xl font-bold">Application submitted!</h2>
      <p className="mt-2 text-slate-600">Your application for <b>{result.program}</b> has been received.</p>
      <div className="mx-auto mt-8 max-w-sm rounded-2xl border-2 border-dashed border-gold-400 bg-gold-50 p-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-gold-700">Your application number (فارم نمبر)</p>
        <p className="mt-2 font-mono text-2xl font-bold tracking-wider text-primary-900">{result.applicationNumber}</p>
        <button type="button" onClick={copy} className="btn-outline btn-sm mt-4"><Copy className="h-4 w-4" />Copy</button>
      </div>
      <p className="mt-6 text-sm text-slate-600">Save this number. You will need it with your CNIC / B-Form number to track your application.</p>
      <div className="no-print mt-8 flex flex-wrap justify-center gap-3">
        <Link to="/admissions/track" className="btn-primary">Track application</Link>
        <button type="button" onClick={() => window.print()} className="btn-outline"><Printer className="h-4 w-4" />Print</button>
      </div>
    </motion.div>
  );
}

export default function ApplyOnline() {
  const { settings, lang } = useSite();
  const [params] = useSearchParams();
  const { data: programs, loading: loadingPrograms } = useFetch('/public/programs', { isAdmissionOpen: true, limit: 100, sort: 'title' });
  const [step, setStep] = useState(0);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [files, setFiles] = useState({});
  const [form, setForm] = useState({
    personal: {
      fullName: '', cnic: '', dateOfBirth: '', gender: '', nationality: 'Pakistani', phone: '', homePhone: '', email: '',
      address: '', temporaryAddress: '', city: '', province: '', fatherName: '', fatherCnic: '', fatherOccupation: '', guardianPhone: '',
    },
    guardian: { name: '', occupation: '' },
    qualification: '',
    quranStatus: '',
    previousMadrasa: '',
    education: [],
    program: params.get('program') || '',
    secondChoice: '',
    classLevel: '',
    residence: 'boarding',
    shift: 'morning',
    declarationAccepted: false,
    rulesAccepted: false,
  });

  const setPersonal = (k) => (e) => {
    const v = ['cnic', 'fatherCnic'].includes(k) ? formatCnic(e.target.value) : e.target.value;
    setForm((f) => ({ ...f, personal: { ...f.personal, [k]: v } }));
  };
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const setGuardian = (k) => (e) => setForm((f) => ({ ...f, guardian: { ...f.guardian, [k]: e.target.value } }));
  const setEdu = (i, k, v) => setForm((f) => ({ ...f, education: f.education.map((ed, j) => (j === i ? { ...ed, [k]: v } : ed)) }));
  const err = (k) => errors[k];

  const programLabel = (p) => `${p.title}${p.titleUr ? ` — ${p.titleUr}` : ''} (${levelLabel(p.level, lang)}${p.deliveryMode === 'online' ? `, ${modeLabel('online', lang)}` : ''})`;
  const programOptions = useMemo(() => (programs || []).map((p) => ({ value: p._id, label: programLabel(p) })), [programs, lang]); // eslint-disable-line react-hooks/exhaustive-deps
  const selected = programs?.find((p) => p._id === form.program);

  const next = () => {
    const e = validateStep(step, form, files);
    setErrors(e);
    if (Object.keys(e).length) { toast.error('Please complete the highlighted fields'); return; }
    setStep((s) => s + 1);
    window.scrollTo({ top: 200, behavior: 'smooth' });
  };

  const submit = async () => {
    const all = [0, 1, 2, 3].reduce((acc, s) => ({ ...acc, ...validateStep(s, form, files) }), {});
    setErrors(all);
    if (Object.keys(all).length) {
      toast.error('Please complete the highlighted fields');
      setStep(Math.min(...Object.keys(all).map(stepOfField)));
      return;
    }
    const digits = (v) => v.replace(/\D/g, '');
    const fd = new FormData();
    fd.append('data', JSON.stringify({
      ...form,
      personal: { ...form.personal, cnic: digits(form.personal.cnic), fatherCnic: digits(form.personal.fatherCnic) },
      session: settings?.currentSession,
    }));
    Object.entries(files).forEach(([type, file]) => file && fd.append(type, file));
    setSubmitting(true);
    try {
      const { data } = await api.post('/public/admissions', fd, { timeout: 120000 });
      setResult(data.data);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (ex) {
      const fe = fieldErrors(ex);
      setErrors(fe);
      toast.error(errorMessage(ex));
      if (Object.keys(fe).length) setStep(Math.min(...Object.keys(fe).map(stepOfField)));
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingPrograms && !programs) return <PageLoader className="min-h-[60vh]" />;

  return (
    <>
      <Seo title="Apply Online" description="Online admission form (فارم داخلہ) of Jamia Muhammadia Saifia, Ravi Rayyan Sharif." />
      <PageHero title="Online Admission Form" subtitle={`${settings?.universityNameUr ? `${settings.universityNameUr} · ` : ''}${settings?.currentSession ? `Admissions — ${settings.currentSession}` : ''}`}
        crumbs={[{ label: 'Admissions', to: '/admissions' }, { label: 'Apply Online' }]} />

      <section className="section bg-surface pt-12">
        <div className="container-x">
          {result ? <Success result={result} /> : !settings?.admissionsOpen ? (
            <div className="card mx-auto max-w-xl p-10 text-center">
              <h2 className="text-2xl font-bold">Admissions are closed</h2>
              <p className="mt-2 text-slate-600">Online applications are not being accepted at the moment.</p>
              <Link to="/admissions" className="btn-primary mt-6">Admission information</Link>
            </div>
          ) : (
            <div className="mx-auto max-w-4xl">
              <ol className="mb-8 grid grid-cols-4 gap-2" aria-label="Application steps">
                {STEPS.map((s, i) => (
                  <li key={s.key} className="flex flex-col items-center gap-2 text-center" aria-current={i === step ? 'step' : undefined}>
                    <span className={`flex h-11 w-11 items-center justify-center rounded-full border-2 transition ${i < step ? 'border-emerald-500 bg-emerald-500 text-white' : i === step ? 'border-primary-700 bg-primary-700 text-white shadow-lift' : 'border-slate-200 bg-white text-slate-400'}`}>
                      {i < step ? <Check className="h-5 w-5" /> : <s.icon className="h-5 w-5" />}
                    </span>
                    <span className={`hidden text-xs font-semibold sm:block ${i === step ? 'text-primary-800' : 'text-slate-500'}`}>{s.label}</span>
                  </li>
                ))}
              </ol>

              <div className="card p-6 sm:p-10">
                <h2 className="mb-6 font-sans text-xl font-semibold">{STEPS[step].label}</h2>
                <AnimatePresence mode="wait">
                  <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.25 }}>
                    {step === 0 && (
                      <div className="grid gap-5 sm:grid-cols-2">
                        <Input label="Full name (نام)" required value={form.personal.fullName} onChange={setPersonal('fullName')} error={err('personal.fullName')} autoComplete="name" />
                        <Input label="CNIC / B-Form number (شناختی کارڈ / ب فارم)" required value={form.personal.cnic} onChange={setPersonal('cnic')} error={err('personal.cnic')} placeholder="35202-1234567-1" inputMode="numeric" />
                        <Input label="Date of birth (تاریخ پیدائش)" type="date" required value={form.personal.dateOfBirth} onChange={setPersonal('dateOfBirth')} error={err('personal.dateOfBirth')} max={new Date().toISOString().slice(0, 10)} />
                        <Select label="Gender" required value={form.personal.gender} onChange={setPersonal('gender')} error={err('personal.gender')} placeholder="Select" options={[{ value: 'male', label: 'Male' }, { value: 'female', label: 'Female' }]} />
                        <Input label="Mobile number (موبائل نمبر)" type="tel" required value={form.personal.phone} onChange={setPersonal('phone')} error={err('personal.phone')} placeholder="03001234567" autoComplete="tel" />
                        <Input label="Home phone (گھر کا فون نمبر)" type="tel" value={form.personal.homePhone} onChange={setPersonal('homePhone')} error={err('personal.homePhone')} />
                        <Input label="Email (optional)" type="email" value={form.personal.email} onChange={setPersonal('email')} error={err('personal.email')} autoComplete="email" />
                        <Input label="Nationality" value={form.personal.nationality} onChange={setPersonal('nationality')} />
                        <Textarea label="Permanent address (مستقل پتہ)" required rows={2} className="sm:col-span-2" value={form.personal.address} onChange={setPersonal('address')} error={err('personal.address')} />
                        <Textarea label="Temporary address (عارضی پتہ)" rows={2} className="sm:col-span-2" value={form.personal.temporaryAddress} onChange={setPersonal('temporaryAddress')} />
                        <Input label="City" required value={form.personal.city} onChange={setPersonal('city')} error={err('personal.city')} />
                        <Select label="Province" value={form.personal.province} onChange={setPersonal('province')} placeholder="Select" options={PROVINCES} />
                      </div>
                    )}

                    {step === 1 && (
                      <div className="space-y-8">
                        <div className="grid gap-5 sm:grid-cols-2">
                          <Input label="Father's name (والد کا نام)" required value={form.personal.fatherName} onChange={setPersonal('fatherName')} error={err('personal.fatherName')} />
                          <Input label="Father's CNIC (والد کا شناختی کارڈ نمبر)" required value={form.personal.fatherCnic} onChange={setPersonal('fatherCnic')} error={err('personal.fatherCnic')} placeholder="35202-1234567-1" inputMode="numeric" />
                          <Input label="Father's occupation (پیشہ)" value={form.personal.fatherOccupation} onChange={setPersonal('fatherOccupation')} />
                          <Input label="Guardian's phone" type="tel" value={form.personal.guardianPhone} onChange={setPersonal('guardianPhone')} />
                          <Input label="Guardian's name (سرپرست کا نام)" value={form.guardian.name} onChange={setGuardian('name')} hint="If different from father" />
                          <Input label="Guardian's occupation (سرپرست کا پیشہ)" value={form.guardian.occupation} onChange={setGuardian('occupation')} />
                        </div>
                        <div className="grid gap-5 border-t border-slate-100 pt-6 sm:grid-cols-2">
                          <Input label="Educational qualification with institution (تعلیمی قابلیت معہ ادارہ کا نام)" required className="sm:col-span-2" value={form.qualification} onChange={set('qualification')} error={err('qualification')} placeholder="e.g. Middle — Govt. High School, Lahore" />
                          <Select label="Hifz / Nazira (حفظ / ناظرہ)" value={form.quranStatus} onChange={set('quranStatus')} placeholder="Select"
                            options={[{ value: 'hafiz', label: 'Hafiz-e-Quran (حافظ)' }, { value: 'hifz_in_progress', label: 'Hifz in progress' }, { value: 'nazira', label: 'Nazira (ناظرہ)' }, { value: 'none', label: 'None' }]} />
                          <Input label="Previous madrasa (مدرسہ کا نام)" value={form.previousMadrasa} onChange={set('previousMadrasa')} />
                        </div>
                        <div className="space-y-4 border-t border-slate-100 pt-6">
                          <p className="text-sm text-slate-600">Results with marks (optional): add your board/university results if you have them.</p>
                          {form.education.map((ed, i) => (
                            // eslint-disable-next-line react/no-array-index-key
                            <fieldset key={i} className="rounded-2xl border border-slate-200 p-5">
                              <legend className="px-2 text-sm font-semibold text-primary-800">Result {i + 1}</legend>
                              <div className="grid gap-4 sm:grid-cols-3">
                                <Select label="Level" value={ed.level} onChange={(e) => setEdu(i, 'level', e.target.value)}
                                  options={[{ value: 'matric', label: 'Matric / SSC' }, { value: 'intermediate', label: 'Intermediate / HSSC' }, { value: 'bachelor', label: 'Bachelor' }, { value: 'master', label: 'Master' }, { value: 'other', label: 'Other (e.g. Wafaq/Tanzeem)' }]} />
                                <Input label="Board / University" value={ed.board} onChange={(e) => setEdu(i, 'board', e.target.value)} />
                                <Input label="Passing year" type="number" value={ed.passingYear} onChange={(e) => setEdu(i, 'passingYear', e.target.value)} />
                                <Input label="Total marks" type="number" min="1" value={ed.totalMarks} onChange={(e) => setEdu(i, 'totalMarks', e.target.value)} error={err(`education.${i}.totalMarks`)} />
                                <Input label="Obtained marks" type="number" min="0" value={ed.obtainedMarks} onChange={(e) => setEdu(i, 'obtainedMarks', e.target.value)} error={err(`education.${i}.obtainedMarks`)} />
                                <div className="flex items-end justify-end">
                                  <button type="button" className="btn btn-sm text-red-600 hover:bg-red-50" onClick={() => setForm((f) => ({ ...f, education: f.education.filter((_, j) => j !== i) }))}>
                                    <Trash2 className="h-4 w-4" />Remove
                                  </button>
                                </div>
                              </div>
                            </fieldset>
                          ))}
                          {form.education.length < 5 && (
                            <button type="button" className="btn-outline btn-sm" onClick={() => setForm((f) => ({ ...f, education: [...f.education, emptyEdu()] }))}>
                              <Plus className="h-4 w-4" />Add a result
                            </button>
                          )}
                        </div>
                      </div>
                    )}

                    {step === 2 && (
                      <div className="grid gap-5 sm:grid-cols-2">
                        <Select label="Program / department (شعبہ)" required className="sm:col-span-2" value={form.program} onChange={set('program')} error={err('program')} placeholder="Select a program" options={programOptions} />
                        <div>
                          <Input label="Class / darjah applied for (درجہ)" list="class-levels" value={form.classLevel} onChange={set('classLevel')} placeholder="e.g. Oola" />
                          <datalist id="class-levels">{CLASS_LEVELS.map((c) => <option key={c} value={c} />)}</datalist>
                        </div>
                        <Select label="Second choice (optional)" value={form.secondChoice} onChange={set('secondChoice')} placeholder="None" options={programOptions.filter((o) => o.value !== form.program)} />
                        <Select label="Residence (رہائش)" required value={form.residence} onChange={set('residence')}
                          options={[{ value: 'boarding', label: 'Dar-ul-Iqama — boarding (دارالاقامہ)' }, { value: 'day_scholar', label: 'Day scholar (خارج دارالاقامہ)' }]} />
                        {selected?.deliveryMode !== 'online' && (
                          <Select label="Preferred shift" value={form.shift} onChange={set('shift')} options={[{ value: 'morning', label: 'Morning' }, { value: 'evening', label: 'Evening' }, { value: 'weekend', label: 'Weekend' }]} />
                        )}
                        {selected && (
                          <div className="rounded-2xl bg-primary-50 p-5 sm:col-span-2">
                            <p className="font-semibold text-primary-900">{selected.title}</p>
                            {selected.titleUr && <p dir="rtl" className="urdu text-start text-primary-700">{selected.titleUr}</p>}
                            <p className="mt-1 text-sm text-slate-600">
                              {[levelLabel(selected.level, lang), modeLabel(selected.deliveryMode, lang), selected.duration, selected.audience, selected.classDays].filter(Boolean).join(' · ')}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {step === 3 && (
                      <div className="space-y-6">
                        <div className="grid gap-5 sm:grid-cols-2">
                          {DOCS.map((d) => (
                            <FileDrop key={d.type} label={d.label} required={d.required} accept={d.accept || '.pdf,.jpg,.jpeg,.png'} hint={d.hint}
                              file={files[d.type]} error={err(`documents.${d.type}`)}
                              onChange={(file, message) => {
                                setFiles((f) => ({ ...f, [d.type]: file }));
                                setErrors((e) => ({ ...e, [`documents.${d.type}`]: message || undefined }));
                              }} />
                          ))}
                        </div>
                        <div className="rounded-2xl bg-surface p-5 text-sm">
                          <p className="font-semibold text-primary-900">Review</p>
                          <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                            <div><dt className="text-slate-500">Applicant</dt><dd className="font-medium">{form.personal.fullName || '—'}</dd></div>
                            <div><dt className="text-slate-500">Father</dt><dd className="font-medium">{form.personal.fatherName || '—'}</dd></div>
                            <div><dt className="text-slate-500">Program</dt><dd className="font-medium">{selected?.title || '—'}</dd></div>
                            <div><dt className="text-slate-500">Darjah / residence</dt><dd className="font-medium">{form.classLevel || '—'} · {form.residence === 'boarding' ? 'Boarding' : 'Day scholar'}</dd></div>
                          </dl>
                        </div>
                        <div className="space-y-4 rounded-2xl border border-gold-300 bg-gold-50/60 p-5">
                          <Checkbox checked={form.rulesAccepted} onChange={(v) => setForm((f) => ({ ...f, rulesAccepted: v }))}
                            label="I have read the Jamia’s rules & regulations and solemnly declare that I will abide by them."
                            description="میں حلفیہ اقرار کرتا ہوں کہ جامعہ کے قواعد و ضوابط کی پابندی کروں گا۔" />
                          <Link to="/pages/rules-and-regulations" target="_blank" className="ms-8 inline-block text-sm font-semibold text-primary-700 underline">Read the rules & regulations (قواعد و ضوابط)</Link>
                          {err('rulesAccepted') && <p className="field-error">{err('rulesAccepted')}</p>}
                          <Checkbox checked={form.declarationAccepted} onChange={(v) => setForm((f) => ({ ...f, declarationAccepted: v }))}
                            label="I solemnly declare that the information given above is completely correct."
                            description="میں حلفیہ اقرار کرتا ہوں۔ مندرجہ بالا کوائف بالکل صحیح ہیں۔" />
                          {err('declarationAccepted') && <p className="field-error">{err('declarationAccepted')}</p>}
                        </div>
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>

                <div className="mt-10 flex items-center justify-between border-t border-slate-100 pt-6">
                  <button type="button" className="btn-outline" disabled={step === 0 || submitting} onClick={() => setStep((s) => s - 1)}>
                    <ArrowLeft className="h-4 w-4 rtl:rotate-180" />Back
                  </button>
                  {step < STEPS.length - 1 ? (
                    <button type="button" className="btn-primary" onClick={next}>Continue <ArrowRight className="h-4 w-4 rtl:rotate-180" /></button>
                  ) : (
                    <button type="button" className="btn-gold" onClick={submit} disabled={submitting}>
                      {submitting ? <><Spinner className="h-4 w-4" />Submitting…</> : <>Submit application <Check className="h-4 w-4" /></>}
                    </button>
                  )}
                </div>
              </div>
              <p className="mt-6 text-center text-xs text-slate-500">Your documents are stored securely and are visible only to authorised admission staff. For help call {settings?.contact?.phones?.join(' / ')}.</p>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
