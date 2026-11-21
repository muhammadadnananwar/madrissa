/** Feature pages in the sidebar (generic resource screens are added from /api/meta/). */
import { ACADEMIC, EXAM, FINANCE, HOSTEL, HR, PAYROLL, STUDENT_VIEWERS, TEACHING } from "./roles";

export type NavItem = { label: string; href: string; icon: string; roles: string[] | "*"; exclude?: string[] };
export type NavGroup = { group: string; items: NavItem[] };

const STAFF = "staff" as const;
const SP = ["student", "parent"];

export const NAV: NavGroup[] = [
  { group: "Overview", items: [
    { label: "Dashboard", href: "/", icon: "dashboard", roles: "*" },
    { label: "Notice board", href: "/announcements", icon: "megaphone", roles: "*" },
    { label: "Messages", href: "/messages", icon: "mail", roles: "*" },
    { label: "Calendar", href: "/calendar", icon: "calendar", roles: "*" },
    { label: "Timetable", href: "/timetable", icon: "clock", roles: [...TEACHING, ...SP] },
  ] },
  { group: "Attendance & Leave", items: [
    { label: "Mark attendance", href: "/attendance", icon: "check", roles: [...TEACHING, "hostel_warden"] },
    { label: "My attendance", href: "/attendance", icon: "check", roles: SP },
    { label: "Today's overview", href: "/attendance/overview", icon: "dashboard", roles: STUDENT_VIEWERS },
    { label: "Attendance reports", href: "/attendance/report", icon: "chart", roles: [...STUDENT_VIEWERS, "teacher"] },
    { label: "Staff attendance", href: "/attendance/staff", icon: "check-circle", roles: [...HR, ...ACADEMIC] },
    { label: "Biometric devices", href: "/attendance/biometric", icon: "id", roles: [...HR, ...ACADEMIC] },
    { label: "My check-in", href: "/attendance/me", icon: "clock", roles: STAFF as any },
    { label: "Leaves", href: "/leaves", icon: "calendar-off", roles: "*" },
  ] },
  { group: "Learning", items: [
    { label: "Courses (LMS)", href: "/lms", icon: "graduation", roles: [...TEACHING, ...SP] },
    { label: "Live classes", href: "/live", icon: "video", roles: [...TEACHING, ...SP] },
    { label: "Quran programs", href: "/hifz", icon: "quran", roles: [...TEACHING, ...SP] },
    { label: "Homework / diary", href: "/m/homework", icon: "notebook", roles: "*" },
  ] },
  { group: "Exams & Results", items: [
    { label: "Marks entry", href: "/exams/marks", icon: "edit", roles: [...EXAM, "teacher"] },
    { label: "Results", href: "/exams/results", icon: "award", roles: [...EXAM, "teacher", ...SP, "admission_officer"] },
    { label: "Promote students", href: "/promote", icon: "trending", roles: EXAM },
  ] },
  { group: "Fees & Finance", items: [
    { label: "My fees", href: "/fees", icon: "receipt", roles: SP },
    { label: "Finance dashboard", href: "/finance", icon: "chart", roles: FINANCE },
    { label: "Generate invoices", href: "/finance/invoices", icon: "receipt", roles: FINANCE },
    { label: "Fee defaulters", href: "/finance/defaulters", icon: "alert", roles: [...FINANCE, "academic_coordinator"] },
    { label: "Payroll", href: "/finance/payroll", icon: "wallet", roles: PAYROLL },
    { label: "My payslips", href: "/m/payslips", icon: "file", roles: STAFF as any },
  ] },
  { group: "Services", items: [
    { label: "Library", href: "/library", icon: "book", roles: "*" },
    { label: "Hostel desk", href: "/hostel", icon: "bed", roles: HOSTEL },
  ] },
];

export function navFor(role: string, isSuper: boolean): NavGroup[] {
  const staff = !["student", "parent"].includes(role);
  return NAV.map((g) => ({
    group: g.group,
    items: g.items.filter((i) => {
      if (i.roles === "*") return true;
      if ((i.roles as any) === STAFF) return staff;
      return isSuper || role === "super_admin" ? !["My attendance", "My fees"].includes(i.label) : i.roles.includes(role);
    }),
  })).filter((g) => g.items.length);
}
