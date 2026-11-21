import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bell, BookOpen, CalendarCheck, CalendarClock, FileBarChart, FolderDown, Home, LayoutDashboard, LogOut, Menu, NotebookPen, Receipt, Settings, User,
} from 'lucide-react';
import crest from '../assets/logo.svg';
import Seo from '../components/Seo';
import { useAuth } from '../context/AuthContext';
import { useFetch } from '../hooks/useFetch';

export const STUDENT_NAV = [
  { to: '/student', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/student/profile', label: 'My Profile', icon: User },
  { to: '/student/courses', label: 'Registered Courses', icon: BookOpen },
  { to: '/student/timetable', label: 'Class Timetable', icon: CalendarClock },
  { to: '/student/attendance', label: 'Attendance', icon: CalendarCheck },
  { to: '/student/results', label: 'Results', icon: FileBarChart },
  { to: '/student/fees', label: 'Fee Challans', icon: Receipt },
  { to: '/student/assignments', label: 'Assignments', icon: NotebookPen },
  { to: '/student/notifications', label: 'Notifications', icon: Bell, badge: true },
  { to: '/student/documents', label: 'Documents', icon: FolderDown },
  { to: '/student/account', label: 'Account Settings', icon: Settings },
];

function Nav({ unread, onNavigate }) {
  return (
    <div className="flex h-full flex-col bg-white">
      <Link to="/student" onClick={onNavigate} className="flex items-center gap-3 border-b border-slate-100 px-5 py-5">
        <img src={crest} alt="" className="h-11 w-auto" />
        <div className="leading-tight"><p className="font-display text-lg font-bold text-primary-900">Student Portal</p><p className="text-[10px] uppercase tracking-[0.25em] text-gold-600">UMS</p></div>
      </Link>
      <nav className="scrollbar-thin flex-1 space-y-1 overflow-y-auto p-3" aria-label="Student portal navigation">
        {STUDENT_NAV.map(({ to, label, icon: Icon, end, badge }) => (
          <NavLink key={to} to={to} end={end} onClick={onNavigate}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-primary-700 text-white shadow-soft' : 'text-slate-600 hover:bg-primary-50 hover:text-primary-800'}`}>
            <Icon className="h-[18px] w-[18px]" /><span className="flex-1">{label}</span>
            {badge && unread > 0 && <span className="rounded-full bg-gold-400 px-2 py-0.5 text-[10px] font-bold text-primary-950">{unread}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-100 p-3">
        <Link to="/" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-600 hover:bg-primary-50"><Home className="h-4 w-4" />University website</Link>
      </div>
    </div>
  );
}

export default function StudentLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const { data: dash, reload } = useFetch('/student/dashboard');
  useEffect(() => { setOpen(false); reload(); /* eslint-disable-next-line */ }, [location.pathname]);
  const unread = dash?.stats?.unreadNotifications || 0;
  const current = STUDENT_NAV.find((n) => (n.end ? location.pathname === n.to : location.pathname.startsWith(n.to)));

  return (
    <div className="min-h-screen bg-surface">
      <Seo title={`${current?.label || 'Student Portal'} · Student Portal`} noIndex />
      <aside className="no-print fixed inset-y-0 start-0 z-40 hidden w-64 border-e border-slate-100 lg:block"><Nav unread={unread} /></aside>
      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-50 bg-primary-950/50 lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(false)}>
            <motion.aside className="h-full w-72" initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }} onClick={(e) => e.stopPropagation()}>
              <Nav unread={unread} onNavigate={() => setOpen(false)} />
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="lg:ps-64">
        <header className="no-print sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200/70 bg-white/90 px-4 backdrop-blur-xl sm:px-6">
          <div className="flex items-center gap-3">
            <button type="button" className="btn-icon lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu className="h-5 w-5" /></button>
            <h1 className="font-sans text-lg font-semibold text-primary-900">{current?.label || 'Student Portal'}</h1>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/student/notifications" className="btn-icon relative" aria-label={`${unread} unread notifications`}>
              <Bell className="h-5 w-5" />{unread > 0 && <span className="absolute end-1 top-1 h-2.5 w-2.5 rounded-full bg-gold-500 ring-2 ring-white" />}
            </Link>
            <div className="hidden text-end sm:block"><p className="text-sm font-semibold text-primary-900">{user.name}</p><p className="text-xs text-slate-500">{user.student?.rollNumber}</p></div>
            <button type="button" onClick={() => { logout(); navigate('/student/login'); }} className="btn-outline btn-sm"><LogOut className="h-4 w-4" /><span className="hidden sm:inline">Log out</span></button>
          </div>
        </header>
        <main className="p-4 sm:p-6 lg:p-8"><Outlet context={{ dash, reloadDash: reload }} /></main>
      </div>
    </div>
  );
}
