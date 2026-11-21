"""Progress summaries and status changes for the Quran programs (Qaida, Nazra, Hifz, Tarjuma, checklists)."""
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import (ChecklistItem, JuzProgress, ParaProgram, QaidaLesson, QaidaProgress, QuranCompletion,
                     StudentChecklist, TarjumaProgress)
from .quran import AYAH_COUNTS, SURAH_CHOICES, TOTAL_AYAHS

DONE = ("memorized", "tested")

CERTIFICATES = {
    "hifz": ("hifz", "Sanad of Hifz-ul-Quran al-Kareem",
             "has completed the memorisation of the entire Holy Quran and has been examined and approved."),
    "nazra": ("nazra", "Certificate of Nazra-tul-Quran",
              "has completed the recitation (Nazra) of the entire Holy Quran with correct pronunciation."),
    "tarjuma": ("tarjuma", "Certificate of Tarjuma-tul-Quran",
                "has completed the translation (Tarjuma) of the entire Holy Quran and has been examined and approved."),
    "qaida": ("qaida", "Certificate of Noorani Qaida",
              "has completed the Noorani Qaida and is ready to begin Nazra of the Holy Quran."),
}


def issue_certificate(student, kind):
    from exams.models import Certificate
    cert_kind, title, details = CERTIFICATES[kind]
    Certificate.objects.get_or_create(person=student.user, kind=cert_kind, defaults={"title": title, "details": details})


def record_completion(student, kind, by=None, remarks="", started_on=None):
    n = (QuranCompletion.objects.filter(student=student, kind=kind).aggregate(m=Max("number"))["m"] or 0) + 1
    return QuranCompletion.objects.create(student=student, kind=kind, number=n, recorded_by=by, remarks=remarks,
                                          started_on=started_on)


# ----------------------------------------------------------------- para grids
def para_grid(student, program):
    rows = {j.juz: j for j in JuzProgress.objects.filter(student=student, program=program)}
    grid = [{"juz": i, "status": rows[i].status if i in rows else "not_started",
             "completed_on": rows[i].completed_on if i in rows else None,
             "test_score": rows[i].test_score if i in rows else None} for i in range(1, 31)]
    done = sum(1 for g in grid if g["status"] in DONE)
    return {"grid": grid, "done": done, "tested": sum(1 for g in grid if g["status"] == "tested"),
            "percentage": round(done / 30 * 100, 1)}


@transaction.atomic
def set_para(student, program, juz, status, by, test_score=None):
    """Update one para; completing all 30 records a khatm and issues the certificate."""
    if status == "not_started":
        JuzProgress.objects.filter(student=student, program=program, juz=juz).delete()
        return None
    obj, _ = JuzProgress.objects.get_or_create(student=student, program=program, juz=juz,
                                               defaults={"started_on": timezone.localdate()})
    obj.status = status
    if status in DONE and not obj.completed_on:
        obj.completed_on = timezone.localdate()
    if status == "tested":
        obj.tested_by = by
        obj.test_score = test_score if test_score is not None else obj.test_score
    obj.save()
    qs = JuzProgress.objects.filter(student=student, program=program)
    # Hifz & Tarjuma certificates need every para tested; Nazra needs every para read.
    finished = qs.filter(status="tested").count() == 30 if program != ParaProgram.NAZRA else qs.filter(status__in=DONE).count() == 30
    if finished:
        first = qs.order_by("started_on").first()
        if program == ParaProgram.NAZRA:
            # every full reading is a khatm; reset the grid so the next khatm can be tracked
            record_completion(student, "nazra", by, started_on=first.started_on if first else None)
            issue_certificate(student, "nazra")
            qs.delete()
        elif not QuranCompletion.objects.filter(student=student, kind=program).exists():
            record_completion(student, program, by, started_on=first.started_on if first else None)
            issue_certificate(student, program)
    return obj


# --------------------------------------------------------------------- Qaida
def qaida_summary(student):
    progress = {p.lesson_id: p for p in QaidaProgress.objects.filter(student=student)}
    lessons = []
    for lesson in QaidaLesson.objects.all():
        p = progress.get(lesson.id)
        lessons.append({"id": lesson.id, "number": lesson.number, "title": lesson.title, "title_arabic": lesson.title_arabic,
                        "status": p.status if p else "not_started", "passed_on": p.passed_on if p else None,
                        "remarks": p.remarks if p else ""})
    passed = sum(1 for x in lessons if x["status"] == "passed")
    current = next((x for x in lessons if x["status"] != "passed"), None)
    return {"lessons": lessons, "passed": passed, "total": len(lessons),
            "percentage": round(passed / len(lessons) * 100, 1) if lessons else 0,
            "current": current["number"] if current else None, "completed": bool(lessons) and passed == len(lessons)}


@transaction.atomic
def set_qaida(student, lesson, status, by, remarks=""):
    if status == "not_started":
        QaidaProgress.objects.filter(student=student, lesson=lesson).delete()
        return
    p, _ = QaidaProgress.objects.get_or_create(student=student, lesson=lesson)
    p.status, p.checked_by = status, by
    p.remarks = remarks or p.remarks
    p.passed_on = timezone.localdate() if status == "passed" else None
    p.save()
    total = QaidaLesson.objects.count()
    if total and QaidaProgress.objects.filter(student=student, status="passed").count() == total \
            and not QuranCompletion.objects.filter(student=student, kind="qaida").exists():
        record_completion(student, "qaida", by)
        issue_certificate(student, "qaida")


# ------------------------------------------------------------------- Tarjuma
def tarjuma_summary(student):
    progress = {p.surah: p for p in TarjumaProgress.objects.filter(student=student)}
    surahs, ayahs_done = [], 0
    for number, label in SURAH_CHOICES:
        p = progress.get(number)
        total = AYAH_COUNTS[number]
        done = total if p and p.status in ("completed", "tested") else min(p.ayahs_done, total) if p else 0
        ayahs_done += done
        surahs.append({"surah": number, "name": label, "ayahs": total, "ayahs_done": done,
                       "status": p.status if p else "not_started", "completed_on": p.completed_on if p else None,
                       "test_score": p.test_score if p else None})
    return {"surahs": surahs, "ayahs_done": ayahs_done, "total_ayahs": TOTAL_AYAHS,
            "percentage": round(ayahs_done / TOTAL_AYAHS * 100, 1),
            "completed": sum(1 for s in surahs if s["status"] in ("completed", "tested")),
            "tested": sum(1 for s in surahs if s["status"] == "tested")}


@transaction.atomic
def set_tarjuma(student, surah, status, by, ayahs_done=None, test_score=None, remarks=""):
    if status == "not_started":
        TarjumaProgress.objects.filter(student=student, surah=surah).delete()
        return
    p, _ = TarjumaProgress.objects.get_or_create(student=student, surah=surah)
    p.status = status
    if ayahs_done is not None:
        p.ayahs_done = min(int(ayahs_done), AYAH_COUNTS[surah])
    if status in ("completed", "tested"):
        p.ayahs_done = AYAH_COUNTS[surah]
        p.completed_on = p.completed_on or timezone.localdate()
    if status == "tested":
        p.tested_by = by
        p.test_score = test_score if test_score is not None else p.test_score
    p.remarks = remarks or p.remarks
    p.save()
    if TarjumaProgress.objects.filter(student=student, status="tested").count() == 114 \
            and not QuranCompletion.objects.filter(student=student, kind="tarjuma").exists():
        record_completion(student, "tarjuma", by)
        issue_certificate(student, "tarjuma")


# ------------------------------------------------------------------ checklists
def checklist_summary(student):
    status = {c.item_id: c for c in StudentChecklist.objects.filter(student=student)}
    groups = {}
    for item in ChecklistItem.objects.filter(is_active=True):
        c = status.get(item.id)
        g = groups.setdefault(item.category, {"category": item.category, "label": item.get_category_display(),
                                              "items": [], "done": 0})
        st = c.status if c else "not_started"
        g["items"].append({"id": item.id, "title": item.title, "arabic": item.arabic, "translation": item.translation,
                           "reference": item.reference, "status": st, "score": c.score if c else None,
                           "date": c.date if c else None})
        g["done"] += st in ("learned", "tested")
    return list(groups.values())


def set_checklist(student, item, status, by, score=None, remarks=""):
    if status == "not_started":
        StudentChecklist.objects.filter(student=student, item=item).delete()
        return
    StudentChecklist.objects.update_or_create(student=student, item=item, defaults={
        "status": status, "score": score, "checked_by": by, "remarks": remarks, "date": timezone.localdate()})


def overview(student):
    """Compact numbers for dashboards and the 360° record."""
    q = qaida_summary(student)
    started = QaidaProgress.objects.filter(student=student).exists()
    return {"qaida": {"passed": q["passed"], "total": q["total"], "current": q["current"] if started else None,
                      "started": started, "completed": q["completed"]},
            "nazra": para_grid(student, "nazra")["done"],
            "nazra_khatms": QuranCompletion.objects.filter(student=student, kind="nazra").count(),
            "hifz": para_grid(student, "hifz")["done"],
            "tarjuma_percentage": tarjuma_summary(student)["percentage"],
            "checklist_done": StudentChecklist.objects.filter(student=student, status__in=["learned", "tested"]).count(),
            "checklist_total": ChecklistItem.objects.filter(is_active=True).count()}
