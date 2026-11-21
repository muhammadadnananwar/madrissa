import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bell, BookOpen, Building2, CalendarCheck, CalendarDays, ClipboardList, Contact, ExternalLink, FileText, FolderOpen, GraduationCap,
  Image, LayoutDashboard, ListOrdered, LogOut, Mail, Megaphone, Menu, MessageSquareQuote, Newspaper, NotebookPen, Receipt, Settings,
  ShieldCheck, UserCog, Users, HelpCircle, FileBarChart, Library, User,
} from 'lucide-react';
import crest from '../assets/logo.svg';
import Seo from '../components/Seo';
import { useAuth } from '../context/AuthContext';
import { canAccess, dashBase, loginFor, roleLabel } from '../utils/roles';

export const ADMIN_NAV = [
  { group: 'Overview', items: [{ to: '', label: 'Dashboard', icon: LayoutDashboard, perm: 'dashboard', end: true }] },
  { group: 'Admissions', items: [
    { to: 'admissions', label: 'Applications', icon: ClipboardList, perm: 'admissions' },
    { to: 'merit-lists', label: 'Merit Lists', icon: ListOrdered, perm: 'meritLists' },
  ] },
  { group: 'Academics', items: [
    { to: 'students', label: 'Students', icon: GraduationCap, perm: 'students' },
    { to: 'faculty', label: 'Faculty', icon: Users, perm: 'faculty' },
    { to: 'departments', label: 'Departments', icon: Building2, perm: 'departments' },
    { to: 'programs', label: 'Programs', icon: BookOpen, perm: 'programs' },
    { to: 'courses', label: 'Courses & Timetable', icon: Library, perm: 'courses' },
    { to: 'attendance', label: 'Attendance', icon: CalendarCheck, perm: 'attendance' },
    { to: 'results', label: 'Results', icon: FileBarChart, perm: 'results' },
    { to: 'assignments', label: 'Assignments', icon: NotebookPen, perm: 'assignments' },
    { to: 'fees', label: 'Fees', icon: Receipt, perm: 'fees' },
    { to: 'calendar', label: 'Academic Calendar', icon: CalendarDays, perm: 'calendar' },
  ] },
  { group: 'Website Content', items: [
    { to: 'news', label: 'News', icon: Newspaper, perm: 'news' },
    { to: 'announcements', label: 'Announcements', icon: Megaphone, perm: 'announcements' },
    { to: 'events', label: 'Events', icon: CalendarDays, perm: 'events' },
    { to: 'gallery', label: 'Gallery', icon: Image, perm: 'gallery' },
    { to: 'pages', label: 'Pages', icon: FileText, perm: 'pages' },
    { to: 'documents', label: 'Documents', icon: FolderOpen, perm: 'documents' },
    { to: 'testimonials', label: 'Testimonials', icon: MessageSquareQuote, perm: 'testimonials' },
    { to: 'faqs', label: 'FAQs', icon: HelpCircle, perm: 'faqs' },
  ] },
  { group: 'Communication', items: [
    { to: 'inquiries', label: 'Inquiries', icon: Mail, perm: 'inquiries' },
    { to: 'notifications', label: 'Notifications', icon: Bell, perm: 'notifications' },
  ] },
  { group: 'System', items: [
    { to: 'settings', label: 'Website Settings', icon: Settings, perm: 'settings' },
    { to: 'users', label: 'Users & Roles', icon: UserCog, perm: 'users' },
  ] },
];

function Sidebar({ role, onNavigate }) {
  const base = dashBase(role);
  const isAdmin = base === '/admin';
  return (
    <div className="flex h-full flex-col bg-primary-950 text-primary-100">
      <Link to={base} className="flex items-center gap-3 border-b border-white/10 px-5 py-5" onClick={onNavigate}>
        <img src={crest} alt="" className="h-11 w-auto" />
        <div className="leading-tight">
          <p className="font-display text-lg font-bold text-white">{isAdmin ? 'UMS Admin' : 'UMS Staff'}</p>
          <p className="text-[10px] uppercase tracking-[0.25em] text-gold-300">{isAdmin ? 'Full Control Panel' : 'Staff Panel'}</p>
        </div>
      </Link>
      <nav className="scrollbar-thin flex-1 space-y-6 overflow-y-auto px-3 py-5" aria-label="Admin navigation">
        {ADMIN_NAV.map((g) => {
          const items = g.items.filter((i) => canAccess(role, i.perm));
          if (!items.length) return null;
          return (
            <div key={g.group}>
              <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary-400">{g.group}</p>
              <ul className="space-y-0.5">
                {items.map(({ to, label, icon: Icon, end }) => (
                  <li key={to}>
                    <NavLink to={to ? `${base}/${to}` : base} end={end} onClick={onNavigate}
                      className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-gold-400 text-primary-950 shadow-gold' : 'text-primary-200 hover:bg-white/5 hover:text-white'}`}>
                      <Icon className="h-[18px] w-[18px] shrink-0" />{label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </nav>
      <div className="border-t border-white/10 p-4">
        <Link to="/" target="_blank" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-primary-200 hover:bg-white/5 hover:text-white">
          <ExternalLink className="h-4 w-4" /> View website
        </Link>
      </div>
    </div>
  );
}

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);
  useEffect(() => { setOpen(false); setMenu(false); }, [location.pathname]);

  const base = dashBase(user.role);
  const current = ADMIN_NAV.flatMap((g) => g.items).find((i) => (i.end ? location.pathname === base : location.pathname.startsWith(`${base}/${i.to}`)));
  const doLogout = () => { const to = loginFor(user.role); logout(); navigate(to); };

  return (
    <div className="min-h-screen bg-surface">
      <Seo title={`${current?.label || 'Dashboard'} · ${base === '/admin' ? 'Admin' : 'Staff'}`} noIndex />
      <aside className="fixed inset-y-0 start-0 z-40 hidden w-72 lg:block"><Sidebar role={user.role} /></aside>
      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-50 bg-primary-950/60 lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(false)}>
            <motion.aside className="h-full w-72" initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }} transition={{ type: 'spring', damping: 30, stiffness: 300 }} onClick={(e) => e.stopPropagation()}>
              <Sidebar role={user.role} onNavigate={() => setOpen(false)} />
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="lg:ps-72">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-slate-200/70 bg-white/90 px-4 backdrop-blur-xl sm:px-6">
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => setOpen(true)} className="btn-icon lg:hidden" aria-label="Open navigation"><Menu className="h-5 w-5" /></button>
            <h1 className="font-sans text-lg font-semibold text-primary-900">{current?.label || 'Admin'}</h1>
          </div>
          <div className="relative">
            <button type="button" onClick={() => setMenu((m) => !m)} className="flex items-center gap-3 rounded-full py-1 pe-3 ps-1 transition hover:bg-primary-50" aria-expanded={menu} aria-haspopup="menu">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-700 text-sm font-semibold text-white">{user.name?.[0]}</span>
              <span className="hidden text-start sm:block">
                <span className="block text-sm font-semibold text-primary-900">{user.name}</span>
                <span className="block text-xs text-slate-500">{roleLabel(user.role)}</span>
              </span>
            </button>
            <AnimatePresence>
              {menu && (
                <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }} role="menu"
                  className="absolute end-0 top-full mt-2 w-56 overflow-hidden rounded-2xl border border-slate-100 bg-white p-2 shadow-lift">
                  <p className="flex items-center gap-2 px-3 py-2 text-xs text-slate-500"><ShieldCheck className="h-4 w-4" />{user.email}</p>
                  <Link to={`${base}/profile`} className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-primary-50" role="menuitem"><User className="h-4 w-4" />My profile</Link>
                  <Link to="/" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-primary-50" role="menuitem"><Contact className="h-4 w-4" />Public website</Link>
                  <button type="button" onClick={doLogout} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-red-600 hover:bg-red-50" role="menuitem"><LogOut className="h-4 w-4" />Log out</button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </header>
        <main className="p-4 sm:p-6 lg:p-8"><Outlet /></main>
      </div>
    </div>
  );
}
