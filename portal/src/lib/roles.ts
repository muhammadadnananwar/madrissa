/** Role groups mirrored from backend core/roles.py (UI visibility only; the API enforces access). */
export const ADMINS = ["super_admin", "principal", "admin"];
export const ACADEMIC = [...ADMINS, "academic_coordinator"];
export const EXAM = [...ACADEMIC, "exam_controller"];
export const FINANCE = [...ADMINS, "accountant"];
export const HR = [...ADMINS, "hr_manager"];
export const PAYROLL = [...FINANCE, "hr_manager"];
export const ADMISSION = [...ADMINS, "admission_officer", "academic_coordinator"];
export const LIBRARY = [...ADMINS, "librarian"];
export const HOSTEL = [...ADMINS, "hostel_warden"];
export const STUDENT_SIDE = ["student", "parent"];
export const TEACHING = [...ACADEMIC, "teacher"];
export const STUDENT_VIEWERS = [...ACADEMIC, "admission_officer", "exam_controller", "accountant", "hostel_warden",
  "transport_manager", "librarian", "receptionist", "hr_manager"];

export function hasRole(user: { role: string; is_superuser?: boolean } | null, roles: string[] | "*"): boolean {
  if (!user) return false;
  if (roles === "*") return true;
  if (user.is_superuser || user.role === "super_admin") return true;
  return roles.includes(user.role);
}
export const isStaff = (user: { role: string }) => !STUDENT_SIDE.includes(user.role);
