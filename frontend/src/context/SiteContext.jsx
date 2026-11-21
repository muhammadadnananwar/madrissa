import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { translations } from '../utils/i18n';

const SiteContext = createContext(null);
const LANG_KEY = 'ums_lang';

/** Provides public website settings + language (English / Urdu with RTL). */
export function SiteProvider({ children }) {
  const [settings, setSettings] = useState(null);
  const [settingsError, setSettingsError] = useState(null);
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem(LANG_KEY) || 'en'; } catch { return 'en'; }
  });

  const loadSettings = useCallback(async () => {
    try {
      const { data } = await api.get('/public/settings');
      setSettings(data.data);
      setSettingsError(null);
    } catch (e) {
      setSettingsError(e);
    }
  }, []);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ur' ? 'rtl' : 'ltr';
    try { localStorage.setItem(LANG_KEY, lang); } catch { /* ignore */ }
  }, [lang]);

  const t = useCallback((key) => translations[lang]?.[key] ?? translations.en[key] ?? key, [lang]);
  const toggleLang = useCallback(() => setLangState((l) => (l === 'en' ? 'ur' : 'en')), []);
  /** Returns the Urdu version of a field (e.g. titleUr) when the site is in Urdu and it exists. */
  const pick = useCallback((obj, field) => (lang === 'ur' && obj?.[`${field}Ur`]) || obj?.[field], [lang]);

  const value = useMemo(() => ({
    settings, settingsError, reloadSettings: loadSettings, lang, setLang: setLangState, toggleLang, t, pick, isRtl: lang === 'ur',
  }), [settings, settingsError, loadSettings, lang, toggleLang, t, pick]);

  return <SiteContext.Provider value={value}>{children}</SiteContext.Provider>;
}

export const useSite = () => useContext(SiteContext);
