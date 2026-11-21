/** Program categories & delivery modes (must match backend PROGRAM_LEVELS / DELIVERY_MODES). */
export const LEVEL_LABELS = {
  quran: { en: 'Quran Studies', ur: 'تعلیم القرآن' },
  dars_nizami: { en: 'Dars-e-Nizami', ur: 'درسِ نظامی' },
  specialization: { en: 'Takhassus (Specialisation)', ur: 'تخصص' },
  short_course: { en: 'Short Courses', ur: 'شارٹ کورسز' },
  undergraduate: { en: 'Undergraduate', ur: 'انڈر گریجویٹ' },
  graduate: { en: 'Graduate', ur: 'گریجویٹ' },
  postgraduate: { en: 'Postgraduate', ur: 'پوسٹ گریجویٹ' },
  diploma: { en: 'Diploma', ur: 'ڈپلومہ' },
  certificate: { en: 'Certificate', ur: 'سرٹیفکیٹ' },
};

export const MODE_LABELS = {
  on_campus: { en: 'On campus', ur: 'جامعہ میں' },
  online: { en: 'Online', ur: 'آن لائن' },
  both: { en: 'On campus & online', ur: 'جامعہ و آن لائن' },
};

export const levelLabel = (level, lang = 'en') => LEVEL_LABELS[level]?.[lang] || LEVEL_LABELS[level]?.en || level;
export const modeLabel = (mode, lang = 'en') => MODE_LABELS[mode]?.[lang] || MODE_LABELS[mode]?.en || mode;

/** True when a string contains Arabic-script (Urdu) characters. */
export const hasUrdu = (s) => typeof s === 'string' && /[؀-ۿ]/.test(s);
