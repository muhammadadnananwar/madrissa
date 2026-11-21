import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import PublicLayout from './layouts/PublicLayout';
import { ProtectedRoute, ScrollToTop } from './components/common';
import { PageLoader } from './components/ui';
import { STAFF_ROLE_OPTIONS } from './utils/roles';

import Home from './pages/Home';
import About from './pages/About';
import Academics from './pages/Academics';
import ProgramDetail from './pages/ProgramDetail';
import Admissions from './pages/Admissions';
import ApplyOnline from './pages/ApplyOnline';
import TrackApplication from './pages/TrackApplication';
import { MeritListDetail, MeritListIndex } from './pages/MeritLists';
import { DepartmentDetail, DepartmentList } from './pages/Departments';
import CampusLife from './pages/CampusLife';
import { EventDetail, EventsList, NewsDetail, NewsEventsHub, NewsList } from './pages/NewsEvents';
import Downloads from './pages/Downloads';
import { FacultyDirectory, FacultyProfile } from './pages/Faculty';
import Contact from './pages/Contact';
import { PageView, SearchPage } from './pages/Misc';
import Login from './pages/Login';
import NotFound from './pages/NotFound';

// Admin & student areas are code-split so public visitors never download them.
const AdminLayout = lazy(() => import('./layouts/AdminLayout'));
const Dashboard = lazy(() => import('./admin/Dashboard'));
const ResourcePage = lazy(() => import('./admin/ResourcePage'));
const AdmissionsList = lazy(() => import('./admin/Admissions').then((m) => ({ default: m.AdmissionsList })));
const AdmissionDetail = lazy(() => import('./admin/Admissions').then((m) => ({ default: m.AdmissionDetail })));
const AttendanceMarker = lazy(() => import('./admin/AttendanceMarker'));
const Settings = lazy(() => import('./admin/Settings'));
const AccountSettings = lazy(() => import('./components/AccountSettings'));

const StudentLayout = lazy(() => import('./layouts/StudentLayout'));
const sp = (name) => lazy(() => import('./student/StudentPages').then((m) => ({ default: m[name] })));
const StudentDashboard = sp('StudentDashboard');
const StudentProfile = sp('StudentProfile');
const StudentCourses = sp('StudentCourses');
const StudentTimetable = sp('StudentTimetable');
const StudentAttendance = sp('StudentAttendance');
const StudentResults = sp('StudentResults');
const StudentFees = sp('StudentFees');
const FeeChallan = sp('FeeChallan');
const StudentAssignments = sp('StudentAssignments');
const StudentNotifications = sp('StudentNotifications');
const StudentDocuments = sp('StudentDocuments');
const StudentAccount = sp('StudentAccount');

// Staff panel: every staff role EXCEPT super admin (restricted, per-role modules).
const STAFF = STAFF_ROLE_OPTIONS.map((r) => r.value).filter((r) => r !== 'super_admin');
// Admin panel: super admin only (complete access).
const ADMIN = ['super_admin'];

/* Same management screens are mounted under /admin and /staff; menus, pages and the API all enforce role permissions. */
const dashboardRoutes = (
  <>
    <Route index element={<Dashboard />} />
    <Route path="admissions" element={<AdmissionsList />} />
    <Route path="admissions/:id" element={<AdmissionDetail />} />
    <Route path="attendance/mark" element={<AttendanceMarker />} />
    <Route path="profile" element={<AccountSettings />} />
    <Route path=":resource" element={<ResourcePage />} />
    <Route path="*" element={<NotFound />} />
  </>
);

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Suspense fallback={<PageLoader className="min-h-screen" />}>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route index element={<Home />} />
            <Route path="about" element={<About />} />
            <Route path="academics" element={<Academics />} />
            <Route path="academics/programs/:slug" element={<ProgramDetail />} />
            <Route path="admissions" element={<Admissions />} />
            <Route path="admissions/apply" element={<ApplyOnline />} />
            <Route path="admissions/track" element={<TrackApplication />} />
            <Route path="admissions/merit-lists" element={<MeritListIndex />} />
            <Route path="admissions/merit-lists/:id" element={<MeritListDetail />} />
            <Route path="departments" element={<DepartmentList />} />
            <Route path="departments/:slug" element={<DepartmentDetail />} />
            <Route path="campus-life" element={<CampusLife />} />
            <Route path="news-events" element={<NewsEventsHub />} />
            <Route path="news" element={<NewsList />} />
            <Route path="news/:slug" element={<NewsDetail />} />
            <Route path="events" element={<EventsList />} />
            <Route path="events/:slug" element={<EventDetail />} />
            <Route path="downloads" element={<Downloads />} />
            <Route path="faculty" element={<FacultyDirectory />} />
            <Route path="faculty/:slug" element={<FacultyProfile />} />
            <Route path="contact" element={<Contact />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="privacy-policy" element={<PageView slug="privacy-policy" />} />
            <Route path="terms" element={<PageView slug="terms-of-use" />} />
            <Route path="pages/:slug" element={<PageView />} />
            <Route path="*" element={<NotFound />} />
          </Route>

          <Route path="login" element={<Login portal="staff" />} />
          <Route path="admin/login" element={<Login portal="admin" />} />
          <Route path="student/login" element={<Login portal="student" />} />

          <Route path="admin" element={<ProtectedRoute roles={ADMIN} redirectTo="/admin/login"><AdminLayout /></ProtectedRoute>}>
            <Route path="settings" element={<Settings />} />
            {dashboardRoutes}
          </Route>

          <Route path="staff" element={<ProtectedRoute roles={STAFF} redirectTo="/login"><AdminLayout /></ProtectedRoute>}>
            {dashboardRoutes}
          </Route>

          <Route path="student" element={<ProtectedRoute roles={['student']} redirectTo="/student/login"><StudentLayout /></ProtectedRoute>}>
            <Route index element={<StudentDashboard />} />
            <Route path="profile" element={<StudentProfile />} />
            <Route path="courses" element={<StudentCourses />} />
            <Route path="timetable" element={<StudentTimetable />} />
            <Route path="attendance" element={<StudentAttendance />} />
            <Route path="results" element={<StudentResults />} />
            <Route path="fees" element={<StudentFees />} />
            <Route path="fees/:id" element={<FeeChallan />} />
            <Route path="assignments" element={<StudentAssignments />} />
            <Route path="notifications" element={<StudentNotifications />} />
            <Route path="documents" element={<StudentDocuments />} />
            <Route path="account" element={<StudentAccount />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  );
}
