import { Route, Routes } from 'react-router-dom';
import PublicLayout from './layouts/PublicLayout';
import { PortalRedirect, ScrollToTop } from './components/common';

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
import NotFound from './pages/NotFound';

/*
 * Public website only. Staff, students and administrators sign in to the separate management
 * portal (VITE_PORTAL_URL); the old login URLs below simply forward there.
 */
export default function App() {
  return (
    <>
      <ScrollToTop />
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
        {['login', 'admin/*', 'staff/*', 'student/*'].map((p) => <Route key={p} path={p} element={<PortalRedirect />} />)}
      </Routes>
    </>
  );
}
