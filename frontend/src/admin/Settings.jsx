import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Info, Save } from 'lucide-react';
import FormRenderer, { toFormValues, toPayload } from './FormRenderer';
import { ErrorState, PageLoader, Spinner, Tabs } from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import { useSite } from '../context/SiteContext';
import api, { errorMessage } from '../services/api';
import { setPath } from '../utils/format';

const item = (extra = []) => [{ name: 'title', label: 'Title' }, { name: 'icon', label: 'Icon', type: 'icon' }, { name: 'description', label: 'Description' }, ...extra];

const SECTIONS = {
  general: {
    label: 'General',
    fields: [
      { name: 'universityName', label: 'Name (English)', required: true },
      { name: 'universityNameUr', label: 'Name (Urdu)' },
      { name: 'shortName', label: 'Short name' },
      { name: 'tagline', label: 'Tagline (English)' },
      { name: 'taglineUr', label: 'Tagline (Urdu)', colSpan: 2 },
      { name: 'currentSession', label: 'Current admission session' },
      { name: 'admissionsOpen', label: 'Online admissions open', type: 'checkbox' },
      { name: 'footerText', label: 'Footer text', type: 'textarea', rows: 2 },
      { name: 'seo.defaultTitle', label: 'Default SEO title' },
      { name: 'seo.defaultDescription', label: 'Default SEO description' },
    ],
  },
  home: {
    label: 'Homepage',
    fields: [
      { name: 'hero.title', label: 'Hero heading', colSpan: 2 },
      { name: 'hero.subtitle', label: 'Hero introduction', type: 'textarea', rows: 3 },
      { name: 'hero.image', label: 'Hero background image', type: 'image', folder: 'settings', colSpan: 2 },
      { name: 'hero.primaryCta.label', label: 'Primary button label' },
      { name: 'hero.primaryCta.link', label: 'Primary button link' },
      { name: 'hero.secondaryCta.label', label: 'Secondary button label' },
      { name: 'hero.secondaryCta.link', label: 'Secondary button link' },
      { name: 'ab', type: 'heading', label: 'Admission announcement banner' },
      { name: 'admissionBanner.enabled', label: 'Show banner', type: 'checkbox' },
      { name: 'admissionBanner.link', label: 'Banner link' },
      { name: 'admissionBanner.text', label: 'Banner text', colSpan: 2 },
      { name: 'stats', label: 'Statistics', type: 'repeater', itemLabel: 'statistic', subfields: [{ name: 'value', label: 'Value', placeholder: 'e.g. 5,000+' }, { name: 'label', label: 'Label' }] },
      { name: 'whyChoose', label: 'Why choose UMS', type: 'repeater', itemLabel: 'reason', subfields: item() },
    ],
  },
  about: {
    label: 'About',
    fields: [
      { name: 'about.intro', label: 'Introduction', type: 'textarea', rows: 4 },
      { name: 'about.history', label: 'History', type: 'textarea', rows: 5 },
      { name: 'about.vision', label: 'Vision', type: 'textarea', rows: 2 },
      { name: 'about.mission', label: 'Mission', type: 'textarea', rows: 2 },
      { name: 'about.image', label: 'About image', type: 'image', folder: 'settings', colSpan: 2 },
      { name: 'about.coreValues', label: 'Core values', type: 'repeater', itemLabel: 'value', subfields: item() },
      { name: 'about.accreditations', label: 'Accreditation & affiliations (verified only)', type: 'repeater', itemLabel: 'entry', subfields: item() },
      { name: 'about.achievements', label: 'Achievements', type: 'repeater', itemLabel: 'achievement', subfields: item() },
    ],
  },
  leadership: {
    label: 'Leadership',
    fields: [
      { name: 'vc', type: 'heading', label: 'Featured message on homepage (Patron / Vice Chancellor)' },
      { name: 'viceChancellor.name', label: 'Name' },
      { name: 'viceChancellor.title', label: 'Title' },
      { name: 'viceChancellor.photo', label: 'Photo', type: 'image', folder: 'settings', colSpan: 2 },
      { name: 'viceChancellor.message', label: 'Message', type: 'textarea', rows: 5 },
      { name: 'ch', type: 'heading', label: 'Chancellor' },
      { name: 'chancellor.name', label: 'Name' },
      { name: 'chancellor.title', label: 'Title' },
      { name: 'chancellor.photo', label: 'Photo', type: 'image', folder: 'settings', colSpan: 2 },
      { name: 'chancellor.message', label: 'Message', type: 'textarea', rows: 4 },
      { name: 'leadership', label: 'University leadership', type: 'repeater', itemLabel: 'person', subfields: [{ name: 'name', label: 'Name' }, { name: 'designation', label: 'Designation' }, { name: 'photo', label: 'Photo', type: 'image', folder: 'settings' }] },
    ],
  },
  campus: {
    label: 'Campus Life',
    fields: [
      { name: 'campusFacilities', label: 'Campus facilities', type: 'repeater', itemLabel: 'facility', subfields: item([{ name: 'image', label: 'Image', type: 'image', folder: 'settings' }]) },
      { name: 'societies', label: 'Societies & clubs', type: 'repeater', itemLabel: 'society', subfields: item() },
    ],
  },
  admissions: {
    label: 'Admissions',
    fields: [
      { name: 'admissions.intro', label: 'Admission information', type: 'textarea', rows: 3 },
      { name: 'admissions.schedule', label: 'Admission schedule', type: 'repeater', itemLabel: 'step', subfields: [{ name: 'step', label: 'Step' }, { name: 'date', label: 'Date' }, { name: 'note', label: 'Note' }] },
      { name: 'admissions.generalRequirements', label: 'General required documents', type: 'list' },
      { name: 'admissions.prospectusUrl', label: 'Prospectus PDF', type: 'file', folder: 'documents', colSpan: 2 },
      { name: 'admissions.feeNote', label: 'Fee disclaimer', colSpan: 2 },
    ],
  },
  contact: {
    label: 'Contact & Social',
    fields: [
      { name: 'contact.address', label: 'Address', colSpan: 2 },
      { name: 'contact.city', label: 'City' },
      { name: 'contact.officeHours', label: 'Office hours' },
      { name: 'contact.phones', label: 'Phone numbers', type: 'list' },
      { name: 'contact.emails', label: 'Email addresses', type: 'list' },
      { name: 'contact.mapQuery', label: 'Map location', colSpan: 2, help: 'Place name or full address used for the Google Maps embed on the Contact page.' },
      { name: 'whatsappNumber', label: 'WhatsApp number', placeholder: '923001234567', help: 'International format, digits only. Leave blank to hide the WhatsApp button.' },
      { name: 'social.facebook', label: 'Facebook URL' },
      { name: 'social.instagram', label: 'Instagram URL' },
      { name: 'social.twitter', label: 'X / Twitter URL' },
      { name: 'social.youtube', label: 'YouTube URL' },
      { name: 'social.linkedin', label: 'LinkedIn URL' },
    ],
  },
};

const ALL_FIELDS = Object.values(SECTIONS).flatMap((s) => s.fields);

export default function Settings() {
  const { reloadSettings } = useSite();
  const { data, loading, error, reload } = useFetch('/admin/settings');
  const [tab, setTab] = useState('general');
  const [values, setValues] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { if (data) setValues(toFormValues(data, ALL_FIELDS)); }, [data]);

  if (loading && !values) return <PageLoader />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!values) return null;

  const save = async () => {
    setSaving(true);
    try {
      const payload = toPayload(values, ALL_FIELDS);
      ['_id', 'key', 'createdAt', 'updatedAt', '__v'].forEach((k) => delete payload[k]);
      await api.put('/admin/settings', payload);
      toast.success('Settings saved');
      reloadSettings();
      reload();
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-3xl font-bold">Website Settings</h2>
          <p className="text-sm text-slate-500">Edit university information shown across the public website.</p>
        </div>
        <button type="button" className="btn-primary" onClick={save} disabled={saving}>{saving ? <Spinner className="h-4 w-4" /> : <Save className="h-4 w-4" />}Save changes</button>
      </div>
      <div className="flex items-start gap-3 rounded-2xl border border-gold-300 bg-gold-50 p-4 text-sm text-gold-700">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>Text marked <b>[Placeholder]</b> is sample content. Replace it with verified, official university information before going live — especially accreditation, statistics, leadership and contact details.</p>
      </div>
      <Tabs value={tab} onChange={setTab} tabs={Object.entries(SECTIONS).map(([value, s]) => ({ value, label: s.label }))} />
      <div className="card p-6 sm:p-8">
        <FormRenderer fields={SECTIONS[tab].fields} values={values} onChange={(path, v) => setValues((s) => setPath(s, path, v))} />
      </div>
      <div className="flex justify-end">
        <button type="button" className="btn-primary" onClick={save} disabled={saving}>{saving ? <Spinner className="h-4 w-4" /> : <Save className="h-4 w-4" />}Save changes</button>
      </div>
    </div>
  );
}
