export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMISSION_OFFICER: 'admission_officer',
  EXAMINATION_OFFICER: 'examination_officer',
  DEPARTMENT_ADMIN: 'department_admin',
  CONTENT_EDITOR: 'content_editor',
  STUDENT: 'student',
};

export const STAFF_ROLE_OPTIONS = [
  { value: 'super_admin', label: 'Super Admin' },
  { value: 'admission_officer', label: 'Admission Officer' },
  { value: 'examination_officer', label: 'Examination Officer' },
  { value: 'department_admin', label: 'Department Admin' },
  { value: 'content_editor', label: 'Content Editor' },
];

export const roleLabel = (r) => STAFF_ROLE_OPTIONS.find((o) => o.value === r)?.label || (r === 'student' ? 'Student' : r);

const { SUPER_ADMIN: SA, ADMISSION_OFFICER: AO, EXAMINATION_OFFICER: EO, DEPARTMENT_ADMIN: DA, CONTENT_EDITOR: CE } = ROLES;

/** Mirrors backend/src/config/roles.js (read access). The server is the source of truth. */
export const ACCESS = {
  dashboard: [SA, AO, EO, DA, CE],
  students: [SA, AO, EO, DA],
  faculty: [SA, DA, CE],
  departments: [SA, DA, AO, CE],
  programs: [SA, DA, AO, CE, EO],
  courses: [SA, DA, EO, AO],
  admissions: [SA, AO],
  meritLists: [SA, AO],
  news: [SA, CE],
  announcements: [SA, CE, AO, EO],
  events: [SA, CE],
  gallery: [SA, CE],
  pages: [SA, CE],
  documents: [SA, CE, AO, EO],
  testimonials: [SA, CE],
  faqs: [SA, CE, AO],
  inquiries: [SA, CE],
  calendar: [SA, CE, EO],
  attendance: [SA, EO, DA],
  results: [SA, EO],
  fees: [SA, AO],
  assignments: [SA, EO, DA],
  notifications: [SA, CE, EO, AO],
  settings: [SA],
  users: [SA],
};

export const canAccess = (role, key) => role === SA || (ACCESS[key] || []).includes(role);

/** Roles allowed to create/update/delete (mirrors backend `write`). */
const WRITE = {
  ...ACCESS,
  students: [SA, AO, DA],
  faculty: [SA, DA],
  departments: [SA, DA],
  programs: [SA, DA],
  courses: [SA, DA, EO],
  dashboard: [],
};

export const canWrite = (role, key) => role === SA || (WRITE[key] || []).includes(role);

/** Dashboard area and login page for each kind of account. */
export const homeFor = (role) => (role === SA ? '/admin' : role === ROLES.STUDENT ? '/student' : '/staff');
export const loginFor = (role) => (role === SA ? '/admin/login' : role === ROLES.STUDENT ? '/student/login' : '/login');
/** Base path of the management dashboard for the current user: /admin (super admin) or /staff (other staff). */
export const dashBase = (role) => (role === SA ? '/admin' : '/staff');
