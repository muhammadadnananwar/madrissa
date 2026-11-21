import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';
import { ArrowLeft, Eye, EyeOff, GraduationCap, LogIn, ShieldCheck, UserCog } from 'lucide-react';
import Seo from '../components/Seo';
import Logo from '../components/Logo';
import { Input } from '../components/form';
import { Img, Spinner } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useSite } from '../context/SiteContext';
import { errorMessage } from '../services/api';
import { homeFor } from '../utils/roles';

/* Three separate sign-in pages. The server only accepts the matching roles on each one. */
const PORTALS = {
  student: {
    title: 'Student Portal', seo: 'Student Portal Login', icon: GraduationCap, idLabel: 'Email or roll number', hint: 'Sign in with your email or roll number.',
    heading: 'Your academic journey, in one place.', blurb: 'View courses, attendance, results, fee challans, assignments and notifications.', home: '/student', help: 'registrar office',
  },
  staff: {
    title: 'Staff Login', seo: 'Staff Login', icon: UserCog, idLabel: 'Staff email', hint: 'For admission, examination, department and content staff.',
    heading: 'Staff panel.', blurb: 'Access only the modules assigned to your role — admissions, examinations, your department or website content.', home: '/staff', help: 'system administrator',
  },
  admin: {
    title: 'Administrator Login', seo: 'Admin Login', icon: ShieldCheck, idLabel: 'Administrator email', hint: 'Restricted to super administrators.',
    heading: 'Full administration control.', blurb: 'Complete access to every module, website settings, users and roles.', home: '/admin', help: 'system owner',
  },
};

/** Shared login screen. portal = "admin" | "staff" | "student" */
export default function Login({ portal = 'staff' }) {
  const cfg = PORTALS[portal];
  const { user, login } = useAuth();
  const { settings } = useSite();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ identifier: '', password: '' });
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { home } = cfg;
  if (user) return <Navigate to={homeFor(user.role)} replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.identifier.trim() || !form.password) { setError('Please enter your credentials.'); return; }
    setLoading(true);
    try {
      const u = await login(form.identifier.trim(), form.password, portal);
      toast.success(`Welcome, ${u.name}`);
      const from = location.state?.from?.pathname;
      navigate(from && from.startsWith(home) ? from : home, { replace: true });
    } catch (ex) {
      setError(errorMessage(ex, 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <Seo title={cfg.seo} noIndex />
      <div className="relative hidden overflow-hidden bg-primary-900 lg:block">
        <Img src={settings?.hero?.image} alt="" className="absolute inset-0 h-full w-full object-cover opacity-30" />
        <div className="absolute inset-0 bg-gradient-to-br from-primary-950 via-primary-900/90 to-primary-700/80" />
        <div className="absolute inset-0 bg-crest-pattern [background-size:26px_26px] opacity-30" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Logo light />
          <div>
            <img src="/logo.svg" alt="" className="h-28 w-auto" />
            <h1 className="mt-8 max-w-md text-5xl font-bold leading-tight text-white">{cfg.heading}</h1>
            <p className="mt-4 max-w-md text-primary-100">{cfg.blurb}</p>
          </div>
          <p className="text-xs text-primary-300">© {new Date().getFullYear()} {settings?.universityName}</p>
        </div>
      </div>

      <div className="flex items-center justify-center bg-surface px-4 py-12">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="mb-8 lg:hidden"><Logo /></div>
          <div className="card p-8 sm:p-10">
            <span className={`flex h-14 w-14 items-center justify-center rounded-2xl ${portal === 'admin' ? 'bg-gold-400 text-primary-950' : 'bg-primary-700 text-gold-300'}`}>
              <cfg.icon className="h-7 w-7" />
            </span>
            <h2 className="mt-6 font-sans text-2xl font-bold">{cfg.title}</h2>
            <p className="mt-1 text-sm text-slate-500">{cfg.hint}</p>
            <form onSubmit={submit} className="mt-8 space-y-5" noValidate>
              <Input label={cfg.idLabel} value={form.identifier} autoComplete="username" autoFocus
                onChange={(e) => setForm((f) => ({ ...f, identifier: e.target.value }))} />
              <div className="relative">
                <Input label="Password" type={show ? 'text' : 'password'} value={form.password} autoComplete="current-password"
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
                <button type="button" onClick={() => setShow((s) => !s)} className="absolute end-3 top-[34px] p-1 text-slate-400 hover:text-primary-700" aria-label={show ? 'Hide password' : 'Show password'}>
                  {show ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
              <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
                {loading ? <Spinner className="h-4 w-4" /> : <LogIn className="h-4 w-4" />} Sign in
              </button>
            </form>
            <p className="mt-6 text-center text-xs text-slate-500">Forgot your password? Contact the {cfg.help} to reset it.</p>
          </div>
          <div className="mt-6 flex items-center justify-between text-sm">
            <Link to="/" className="flex items-center gap-1 text-primary-700 hover:underline"><ArrowLeft className="h-4 w-4 rtl:rotate-180" />Back to website</Link>
            <span className="flex gap-4">
              {portal !== 'student' && <Link to="/student/login" className="text-primary-700 hover:underline">Student portal</Link>}
              {portal !== 'staff' && <Link to="/login" className="text-primary-700 hover:underline">Staff login</Link>}
            </span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
