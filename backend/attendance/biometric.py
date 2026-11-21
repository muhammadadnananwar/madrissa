"""
Biometric attendance: receive punches from devices, store them, and turn them into attendance.

Supported inputs
* ZKTeco ADMS / "iclock" push protocol (most fingerprint & face terminals sold in Pakistan:
  ZKTeco, Hikvision-ZK, eSSL, Granding...) — see ``attendance/iclock.py``.
* LAN pull from ZK devices on port 4370 (``pip install pyzk``).
* JSON API for any vendor software / middleware.
* CSV / TXT import of exported logs (including ZK ``attlog.dat`` USB exports).
"""
import csv
import io
import re
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Max, Min
from django.utils import timezone

from .models import BiometricDevice, BiometricEnrollment, BiometricPunch, Source, StaffAttendance, Status, StudentAttendance

# ZK status codes → direction
ZK_STATUS = {"0": "in", "1": "out", "2": "out", "3": "in", "4": "in", "5": "out"}
ZK_VERIFY = {"0": "password", "1": "fingerprint", "2": "card", "3": "password", "4": "card", "15": "face", "25": "palm"}
DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p",
                "%d/%m/%Y %I:%M:%S %p", "%d/%m/%Y %I:%M %p", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]


class BiometricError(Exception):
    pass


def parse_datetime(value):
    """Parse device / CSV timestamps (local time unless an offset is given) into an aware datetime."""
    v = str(value).strip().replace("‏", "")
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        dt = None
        for fmt in DATE_FORMATS:
            try:
                dt = datetime.strptime(v, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            raise BiometricError(f"Unrecognised date/time: {value!r}")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _direction(value):
    v = str(value or "").strip().lower()
    if v in ZK_STATUS:
        return ZK_STATUS[v]
    if v in ("in", "check in", "checkin", "c/in", "i", "entry", "duty on"):
        return "in"
    if v in ("out", "check out", "checkout", "c/out", "o", "exit", "duty off"):
        return "out"
    return "unknown"


# ------------------------------------------------------------------ parsers
def parse_zk_attlog(text):
    """ZK ATTLOG lines: PIN<TAB>YYYY-MM-DD HH:MM:SS<TAB>status<TAB>verify<TAB>workcode..."""
    rows = []
    for line in text.splitlines():
        parts = re.split(r"\t+", line.strip())
        if len(parts) < 2 or not parts[0]:
            continue
        rows.append({"pin": parts[0].strip(), "time": parse_datetime(parts[1]),
                     "direction": _direction(parts[2] if len(parts) > 2 else ""),
                     "verify": ZK_VERIFY.get(parts[3].strip(), parts[3].strip()) if len(parts) > 3 else "",
                     "raw": line.strip()[:255]})
    return rows


def parse_csv(content):
    """Flexible CSV/TXT import. Detects columns by header names (PIN/ID/User, Date/Time, Status/Type)."""
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig", errors="ignore")
    sample = content[:2048]
    if "\t" in sample and "," not in sample.splitlines()[0]:
        delimiter = "\t"
    else:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    reader = list(csv.reader(io.StringIO(content), delimiter=delimiter))
    if not reader:
        return [], []
    head = [h.strip().lower() for h in reader[0]]

    def col(*names):
        for i, h in enumerate(head):
            if any(n in h for n in names):
                return i
        return None

    has_header = any(re.search(r"[a-z]", h) for h in head) and not re.match(r"^\d+$", head[0] or "")
    if has_header:
        i_pin = col("pin", "user id", "userid", "enroll", "emp", "ac-no", "ac no", "badge", "id")
        i_dt = col("datetime", "date time", "punch time", "check time", "checktime", "timestamp", "time")
        i_date, i_time = col("date"), col("time")
        i_dir = col("status", "state", "type", "direction", "in/out")
        data = reader[1:]
    else:  # attlog.dat style: PIN, datetime, status...
        i_pin, i_dt, i_date, i_time, i_dir, data = 0, 1, None, None, 2, reader
    if i_pin is None or (i_dt is None and i_date is None):
        raise BiometricError("Could not find the PIN and date/time columns. Expected headers like 'PIN, DateTime, Status'.")
    rows, errors = [], []
    for n, r in enumerate(data, start=2 if has_header else 1):
        if not r or not any(c.strip() for c in r):
            continue
        try:
            if i_dt is not None and i_dt != i_date and i_dt < len(r) and re.search(r"\d{1,2}:\d{2}", r[i_dt]) and re.search(r"\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", r[i_dt]):
                stamp = r[i_dt]
            else:
                stamp = f"{r[i_date]} {r[i_time]}" if i_date is not None and i_time is not None and i_date != i_time else r[i_dt if i_dt is not None else i_date]
            rows.append({"pin": r[i_pin].strip(), "time": parse_datetime(stamp),
                         "direction": _direction(r[i_dir]) if i_dir is not None and i_dir < len(r) else "unknown",
                         "verify": "", "raw": delimiter.join(r)[:255]})
        except (BiometricError, IndexError) as e:
            errors.append(f"Line {n}: {e}")
    return rows, errors


# ------------------------------------------------------------------- storage
@transaction.atomic
def record_punches(device, rows, source):
    """Store punches (deduplicated) and apply them to attendance. Returns counts."""
    created, duplicates = [], 0
    for r in rows:
        punch, new = BiometricPunch.objects.get_or_create(
            device=device, pin=r["pin"], punched_at=r["time"],
            defaults={"direction": r.get("direction", "unknown"), "verify_mode": r.get("verify", ""), "source": source,
                      "raw": r.get("raw", "")})
        if new:
            created.append(punch)
        else:
            duplicates += 1
    results = {"received": len(rows), "new": len(created), "duplicates": duplicates, "applied": 0, "unmatched": 0, "skipped": 0}
    for punch in sorted(created, key=lambda p: p.punched_at):
        results[process_punch(punch)] += 1
    if device:
        device.last_seen = timezone.now()
        if created:
            device.last_punch_at = max(p.punched_at for p in created)
        device.save(update_fields=["last_seen", "last_punch_at", "updated_at"])
    return results


def _settings():
    from website.models import SiteSettings
    return SiteSettings.get()


def _skip(punch, note):
    punch.result, punch.note = BiometricPunch.Result.SKIPPED, note[:200]
    punch.save(update_fields=["result", "note", "user", "updated_at"])
    return "skipped"


def process_punch(punch):
    """Apply one punch to staff or student attendance. Returns 'applied' | 'unmatched' | 'skipped'."""
    enrollment = BiometricEnrollment.objects.select_related("user").filter(pin=punch.pin, is_active=True).first()
    if not enrollment:
        punch.result, punch.note = BiometricPunch.Result.UNMATCHED, "No person is enrolled with this PIN"
        punch.save(update_fields=["result", "note", "updated_at"])
        return "unmatched"
    user = enrollment.user
    punch.user = user
    audience = punch.device.audience if punch.device else "both"
    emp = getattr(user, "employee_profile", None)
    st = getattr(user, "student_profile", None)
    if emp and audience in ("staff", "both"):
        note = _apply_staff(emp, punch)
    elif st and audience in ("students", "both"):
        note = _apply_student(st, punch)
    else:
        return _skip(punch, "Person is not covered by this device (staff/student setting)")
    if note:
        return _skip(punch, note)
    punch.result, punch.note = BiometricPunch.Result.APPLIED, ""
    punch.save(update_fields=["result", "note", "user", "updated_at"])
    return "applied"


def _day_range(d):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(d, datetime.min.time()), tz)
    return start, start + timedelta(days=1)


def _apply_staff(emp, punch):
    local = timezone.localtime(punch.punched_at)
    d = local.date()
    rec = StaffAttendance.objects.filter(employee=emp, date=d).first()
    if rec and rec.status in (Status.LEAVE, Status.HALF_DAY, Status.EXCUSED) and rec.source == Source.LEAVE:
        return "On approved leave — punch kept in log only"
    start, end = _day_range(d)
    day = BiometricPunch.objects.filter(user=emp.user, punched_at__gte=start, punched_at__lt=end).exclude(pk=punch.pk)
    times = [timezone.localtime(t) for t in day.values_list("punched_at", flat=True)] + [local]
    first, last = min(times), max(times)
    # explicit OUT punches win for check-out; otherwise the last punch of the day (if at least 1 minute after first)
    outs = [timezone.localtime(p.punched_at) for p in day if p.direction == "out"] + ([local] if punch.direction == "out" else [])
    ins = [timezone.localtime(p.punched_at) for p in day if p.direction == "in"] + ([local] if punch.direction == "in" else [])
    check_in = min(ins) if ins else first
    check_out = max(outs) if outs else (last if (last - first) >= timedelta(minutes=1) else None)
    status = Status.PRESENT
    if emp.duty_start:
        grace = _settings().attendance_late_after_minutes
        if check_in.time() > (datetime.combine(d, emp.duty_start) + timedelta(minutes=grace)).time():
            status = Status.LATE
    if rec and rec.source == Source.MANUAL and rec.status in (Status.PRESENT, Status.LATE):
        # keep the admin's status, only fill in missing times
        rec.check_in = rec.check_in or check_in.time().replace(microsecond=0)
        rec.check_out = check_out.time().replace(microsecond=0) if check_out else rec.check_out
        rec.save(update_fields=["check_in", "check_out", "updated_at"])
        return ""
    StaffAttendance.objects.update_or_create(employee=emp, date=d, defaults={
        "status": status, "check_in": check_in.time().replace(microsecond=0),
        "check_out": check_out.time().replace(microsecond=0) if check_out else None,
        "source": Source.DEVICE, "remarks": f"Biometric{f' · {punch.device.name}' if punch.device else ''}"})
    return ""


def _student_start_time():
    from academics.models import TimeSlot
    first = TimeSlot.objects.order_by("order", "start_time").first()
    return first.start_time if first else None


def _apply_student(st, punch):
    local = timezone.localtime(punch.punched_at)
    d = local.date()
    rec = StudentAttendance.objects.filter(student=st, date=d, subject__isnull=True).first()
    if rec and rec.status in (Status.LEAVE, Status.EXCUSED, Status.HALF_DAY):
        return "On leave / excused — punch kept in log only"
    if rec and rec.source == Source.DEVICE:
        return ""  # already marked by an earlier punch today
    if rec and rec.source in (Source.MANUAL, Source.LIVE_CLASS) and rec.status in (Status.PRESENT, Status.LATE):
        return "Already marked present by the teacher"
    status = Status.PRESENT
    start = _student_start_time()
    if start:
        grace = _settings().attendance_late_after_minutes
        if local.time() > (datetime.combine(d, start) + timedelta(minutes=grace)).time():
            status = Status.LATE
    StudentAttendance.objects.update_or_create(student=st, date=d, subject=None, defaults={
        "section_id": st.section_id, "status": status, "source": Source.DEVICE,
        "remarks": f"Biometric {local:%H:%M}{f' · {punch.device.name}' if punch.device else ''}"})
    return ""


def reprocess(date=None, include_applied=False):
    qs = BiometricPunch.objects.all()
    if date:
        start, end = _day_range(date)
        qs = qs.filter(punched_at__gte=start, punched_at__lt=end)
    if not include_applied:
        qs = qs.exclude(result=BiometricPunch.Result.APPLIED)
    counts = {"applied": 0, "unmatched": 0, "skipped": 0}
    for p in qs.select_related("device").order_by("punched_at"):
        counts[process_punch(p)] += 1
    return counts


@transaction.atomic
def close_day(date, staff=True, students=False):
    """After the day: enrolled people with no punch and no record are marked absent."""
    from people.models import Employee, Student

    from .services import is_holiday
    if is_holiday(date):
        return {"staff": 0, "students": 0, "detail": "Holiday / weekly off — nothing marked."}
    enrolled = set(BiometricEnrollment.objects.filter(is_active=True).values_list("user_id", flat=True))
    out = {"staff": 0, "students": 0}
    if staff:
        have = set(StaffAttendance.objects.filter(date=date).values_list("employee_id", flat=True))
        for emp in Employee.objects.filter(status="active", user_id__in=enrolled).exclude(id__in=have):
            StaffAttendance.objects.create(employee=emp, date=date, status=Status.ABSENT, source=Source.DEVICE,
                                           remarks="No biometric punch")
            out["staff"] += 1
    if students:
        have = set(StudentAttendance.objects.filter(date=date, subject__isnull=True).values_list("student_id", flat=True))
        for st in Student.objects.filter(status="active", user_id__in=enrolled).exclude(id__in=have):
            StudentAttendance.objects.create(student=st, section_id=st.section_id, date=date, status=Status.ABSENT,
                                             source=Source.DEVICE, remarks="No biometric punch")
            out["students"] += 1
    return out


def pull_device(device):
    """Fetch logs from a ZK device on the LAN (requires ``pip install pyzk``)."""
    try:
        from zk import ZK
    except ImportError:
        raise BiometricError("Pull mode needs the 'pyzk' package: pip install pyzk")
    if not device.ip_address:
        raise BiometricError("Set the device IP address first.")
    conn = None
    try:
        conn = ZK(device.ip_address, port=device.port, timeout=15, password=device.comm_key, force_udp=False).connect()
        since = device.last_punch_at - timedelta(days=1) if device.last_punch_at else None
        rows = []
        for a in conn.get_attendance():
            t = a.timestamp if timezone.is_aware(a.timestamp) else timezone.make_aware(a.timestamp, timezone.get_current_timezone())
            if since and t < since:
                continue
            rows.append({"pin": str(a.user_id), "time": t, "direction": _direction(getattr(a, "punch", "")),
                         "verify": ZK_VERIFY.get(str(getattr(a, "status", "")), ""), "raw": f"{a.user_id} {a.timestamp}"})
    except BiometricError:
        raise
    except Exception as e:
        raise BiometricError(f"Could not read from {device.ip_address}:{device.port} — {e}")
    finally:
        if conn:
            try:
                conn.disconnect()
            except Exception:
                pass
    return record_punches(device, rows, "pull")


def auto_enroll(who="all", scheme="id"):
    """Create PINs for people without one. scheme 'id' = user id; 'number' = digits of employee/admission no."""
    from accounts.models import User
    qs = User.objects.filter(is_active=True, biometric__isnull=True)
    if who == "staff":
        qs = qs.filter(employee_profile__isnull=False)
    elif who == "students":
        qs = qs.filter(student_profile__isnull=False)
    else:
        qs = qs.filter(employee_profile__isnull=False) | qs.filter(student_profile__isnull=False)
    used = set(BiometricEnrollment.objects.values_list("pin", flat=True))
    made = 0
    for u in qs.distinct():
        pin = str(u.id)
        if scheme == "number":
            ref = getattr(getattr(u, "employee_profile", None), "employee_no", "") or getattr(getattr(u, "student_profile", None), "admission_no", "")
            digits = re.sub(r"\D", "", ref or "")
            pin = digits[-9:].lstrip("0") or pin
        while pin in used:
            pin = f"{pin}0"
        BiometricEnrollment.objects.create(user=u, pin=pin)
        used.add(pin)
        made += 1
    return made


def status_summary():
    today = timezone.localdate()
    start, end = _day_range(today)
    devices = []
    for d in BiometricDevice.objects.all():
        agg = d.punches.filter(punched_at__gte=start, punched_at__lt=end).aggregate(first=Min("punched_at"), last=Max("punched_at"))
        online = bool(d.last_seen and timezone.now() - d.last_seen < timedelta(minutes=10))
        devices.append({"id": d.id, "name": d.name, "serial_number": d.serial_number, "protocol": d.get_protocol_display(),
                        "protocol_key": d.protocol, "audience": d.get_audience_display(), "location": d.location,
                        "is_active": d.is_active, "online": online, "last_seen": d.last_seen, "api_key": d.api_key,
                        "today": d.punches.filter(punched_at__gte=start, punched_at__lt=end).count(),
                        "first_today": agg["first"], "last_today": agg["last"]})
    today_qs = BiometricPunch.objects.filter(punched_at__gte=start, punched_at__lt=end)
    return {"devices": devices, "today_total": today_qs.count(),
            "today_unmatched": today_qs.filter(result="unmatched").count(),
            "unmatched_pins": list(today_qs.filter(result="unmatched").values_list("pin", flat=True).distinct()[:50]),
            "enrolled": BiometricEnrollment.objects.filter(is_active=True).count()}
