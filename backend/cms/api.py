"""
Anonymous JSON API of the public website (React site in /website).

Mounted at /api/site/public/. Responses use the envelope the website expects:
    {"success": true, "message": "OK", "data": ..., "meta": {"total", "page", "limit", "pages"}}
    {"success": false, "message": "...", "errors": [{"field", "message"}]}
Only published / active content is ever returned; private fields (phones of staff, applicant data) never are.
"""
import json
import math
import re
import secrets
from datetime import datetime, time

from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.models import User
from communication.models import Event
from communication.services import notify
from core.roles import R
from people.models import AdmissionApplication, AdmissionDocument
from website.models import ContactMessage

from .models import (Announcement, CalendarItem, Department, Document, Faculty, Faq, GalleryItem, MeritList, MeritListEntry, News,
                     Page, Program, Testimonial, WebsiteSettings)

# --------------------------------------------------------------------------------------------- helpers


def ok(data=None, meta=None, status=200, message="OK"):
    body = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return Response(body, status=status)


def fail(message, status=400, errors=None):
    return Response({"success": False, "message": message, "errors": errors or []}, status=status)


def media(request, file_field, url=""):
    """Absolute URL of an uploaded file, else the fallback URL string."""
    if file_field:
        try:
            return request.build_absolute_uri(file_field.url)
        except ValueError:
            pass
    return url or ""


def iso(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return datetime.combine(v, time()).isoformat()


def num(v):
    return float(v) if v is not None else None


def paginate(request, qs, default_limit=10):
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except ValueError:
        page = 1
    try:
        limit = min(100, max(1, int(request.query_params.get("limit", default_limit))))
    except ValueError:
        limit = default_limit
    total = qs.count()
    items = list(qs[(page - 1) * limit: page * limit])
    return items, {"total": total, "page": page, "limit": limit, "pages": max(1, math.ceil(total / limit))}


def search(qs, request, fields):
    q = (request.query_params.get("q") or "").strip()
    if q:
        cond = Q()
        for f in fields:
            cond |= Q(**{f"{f}__icontains": q})
        qs = qs.filter(cond)
    return qs


def sort(qs, request, allowed):
    s = request.query_params.get("sort") or ""
    if s.lstrip("-") in allowed:
        field = allowed[s.lstrip("-")]
        return qs.order_by(("-" if s.startswith("-") else "") + field)
    return qs


def truthy(v):
    return str(v).lower() in ("1", "true", "yes")


def digits(v):
    return re.sub(r"\D", "", str(v or ""))


class Public(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


class PublicForm(Public):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_forms"
    parser_classes = [JSONParser, MultiPartParser, FormParser]


# ------------------------------------------------------------------------------------------ serialisers


def absolute(request, data):
    """Turn /media/... paths stored inside the settings JSON into absolute URLs (the website may be on another domain)."""
    if isinstance(data, dict):
        return {k: absolute(request, v) for k, v in data.items()}
    if isinstance(data, list):
        return [absolute(request, v) for v in data]
    if isinstance(data, str) and data.startswith("/media/"):
        return request.build_absolute_uri(data)
    return data


def settings_out(request, s):
    s.hero, s.about, s.vice_chancellor, s.chancellor, s.leadership, s.why_choose, s.campus_facilities, s.societies = (
        absolute(request, v) for v in (s.hero, s.about, s.vice_chancellor, s.chancellor, s.leadership, s.why_choose,
                                       s.campus_facilities, s.societies))
    hero = dict(s.hero or {})
    hero["image"] = media(request, s.hero_image, hero.get("image"))
    about = dict(s.about or {})
    about["image"] = media(request, s.about_image, about.get("image"))
    vc = dict(s.vice_chancellor or {})
    vc["photo"] = media(request, s.vice_chancellor_photo, vc.get("photo"))
    return {
        "_id": str(s.pk), "universityName": s.university_name, "universityNameUr": s.university_name_ur,
        "shortName": s.short_name, "tagline": s.tagline, "taglineUr": s.tagline_ur, "logo": "/logo.svg",
        "hero": hero, "admissionBanner": s.admission_banner, "admissionsOpen": s.admissions_open,
        "currentSession": s.current_session, "stats": s.stats, "about": about, "viceChancellor": vc,
        "chancellor": s.chancellor, "leadership": s.leadership, "whyChoose": s.why_choose,
        "campusFacilities": s.campus_facilities, "societies": s.societies, "admissions": s.admissions,
        "contact": s.contact, "social": s.social, "whatsappNumber": s.whatsapp_number, "seo": s.seo,
        "footerText": s.footer_text, "updatedAt": iso(s.updated_at),
    }


def dept_ref(d):
    return {"_id": str(d.pk), "name": d.name, "nameUr": d.name_ur, "slug": d.slug} if d else None


def dept_out(request, d, full=False):
    out = {"_id": str(d.pk), "name": d.name, "nameUr": d.name_ur, "slug": d.slug, "code": d.code, "faculty": d.faculty,
           "shortDescription": d.short_description, "shortDescriptionUr": d.short_description_ur,
           "introduction": d.introduction, "headName": d.head_name, "headDesignation": d.head_designation,
           "image": media(request, d.image, d.image_url), "contactEmail": d.contact_email, "contactPhone": d.contact_phone,
           "order": d.order, "isPlaceholder": d.is_placeholder}
    if full:
        out["headMessage"] = d.head_message
    return out


def program_out(request, p, full=False):
    out = {"_id": str(p.pk), "title": p.title, "titleUr": p.title_ur, "slug": p.slug, "code": p.code, "level": p.level,
           "deliveryMode": p.delivery_mode, "audience": p.audience, "classDays": p.class_days,
           "department": dept_ref(p.department), "duration": p.duration, "semesters": p.semesters,
           "totalCreditHours": p.total_credit_hours, "shift": p.shift, "shortDescription": p.short_description,
           "eligibility": p.eligibility, "admissionRequirements": p.admission_requirements, "fee": p.fee,
           "seats": p.seats, "minimumPercentage": p.minimum_percentage, "image": media(request, p.image, p.image_url),
           "isFeatured": p.is_featured, "isAdmissionOpen": p.is_admission_open, "isPlaceholder": p.is_placeholder}
    if full:
        out.update(overview=p.overview, careerProspects=p.career_prospects)
    return out


def faculty_out(request, f, full=False):
    out = {"_id": str(f.pk), "name": f.name, "nameUr": f.name_ur, "slug": f.slug, "designation": f.designation,
           "designationUr": f.designation_ur, "department": dept_ref(f.department), "photo": media(request, f.photo, f.photo_url),
           "specialization": f.specialization, "qualifications": f.qualifications, "isPlaceholder": f.is_placeholder,
           "order": f.order}
    if full:
        out.update(email=f.email, bio=f.bio, researchInterests=f.research_interests, publications=f.publications)
    return out


def news_out(request, n, full=False):
    out = {"_id": str(n.pk), "title": n.title, "slug": n.slug, "excerpt": n.excerpt,
           "coverImage": media(request, n.cover_image, n.cover_image_url), "category": n.category, "tags": n.tags,
           "publishedAt": iso(n.published_at), "isPlaceholder": n.is_placeholder}
    if full:
        out["content"] = n.content
    return out


def event_out(request, e, full=False):
    out = {"_id": str(e.pk), "title": e.title, "slug": e.slug, "description": (e.description or "")[:500],
           "startDate": iso(e.start), "endDate": iso(e.end), "venue": e.location, "image": media(request, e.image),
           "category": e.kind, "registrationLink": e.registration_link, "isPlaceholder": False}
    if full:
        out["content"] = e.content or e.description
    return out


def announcement_out(request, a):
    return {"_id": str(a.pk), "title": a.title, "content": a.content, "type": a.type, "link": a.link,
            "attachment": media(request, a.attachment), "isPinned": a.is_pinned, "publishDate": iso(a.publish_date),
            "expiresAt": iso(a.expires_at)}


def gallery_out(request, g):
    return {"_id": str(g.pk), "title": g.title, "image": media(request, g.image, g.image_url), "category": g.category,
            "description": g.description}


def document_out(request, d):
    return {"_id": str(d.pk), "title": d.title, "description": d.description, "category": d.category,
            "fileType": "application/pdf" if (d.file and d.file.name.lower().endswith(".pdf")) or d.file_url.lower().endswith(".pdf") else "",
            "downloads": d.downloads, "createdAt": iso(d.created_at)}


def testimonial_out(request, t):
    return {"_id": str(t.pk), "name": t.name, "program": t.program, "batch": t.batch, "quote": t.quote,
            "photo": media(request, t.photo, t.photo_url), "isPlaceholder": t.is_placeholder}


def faq_out(f):
    return {"_id": str(f.pk), "question": f.question, "answer": f.answer, "category": f.category, "order": f.order}


def merit_out(m, entries=False):
    out = {"_id": str(m.pk), "title": m.title, "program": {"_id": str(m.program_id), "title": m.program.title, "code": m.program.code},
           "session": m.session, "round": m.round, "notes": m.notes, "publishedAt": iso(m.published_at)}
    if entries:
        out["entries"] = [{"rank": e.rank, "applicationNumber": e.application_number, "name": e.name, "aggregate": num(e.aggregate)}
                          for e in m.entries.all()]
    else:
        out["count"] = m.entries.count()
    return out


# --------------------------------------------------------------------------------------------- querysets


def programs_qs():
    return Program.objects.filter(is_active=True).select_related("department")


def news_qs():
    return News.objects.filter(is_published=True, published_at__lte=timezone.now())


def events_qs():
    return Event.objects.filter(is_public=True)


def announcements_qs():
    now = timezone.now()
    return Announcement.objects.filter(is_published=True, publish_date__lte=now).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=now))


def documents_qs():
    return Document.objects.filter(is_published=True, audience="public")


# ------------------------------------------------------------------------------------------------- views


class SettingsView(Public):
    def get(self, request):
        return ok(settings_out(request, WebsiteSettings.load()))


class HomeView(Public):
    def get(self, request):
        today = timezone.localdate()
        return ok({
            "programs": [program_out(request, p) for p in programs_qs().filter(is_featured=True)[:6]],
            "departments": [dept_out(request, d) for d in Department.objects.filter(is_active=True)[:8]],
            "news": [news_out(request, n) for n in news_qs()[:3]],
            "events": [event_out(request, e) for e in events_qs().filter(start__date__gte=today).order_by("start")[:4]],
            "gallery": [gallery_out(request, g) for g in GalleryItem.objects.filter(is_published=True)[:8]],
            "testimonials": [testimonial_out(request, t) for t in Testimonial.objects.filter(is_published=True)[:6]],
            "faqs": [faq_out(f) for f in Faq.objects.filter(is_published=True, category__in=["general", "admission"]).order_by("order")[:6]],
            "announcements": [announcement_out(request, a) for a in announcements_qs()[:5]],
        })


class ProgramListView(Public):
    def get(self, request):
        qs = search(programs_qs(), request, ["title", "title_ur", "code", "short_description"])
        p = request.query_params
        if p.get("level"):
            qs = qs.filter(level=p["level"])
        if p.get("deliveryMode"):
            qs = qs.filter(delivery_mode=p["deliveryMode"])
        if p.get("department"):
            qs = qs.filter(department_id=p["department"]) if p["department"].isdigit() else qs.filter(department__slug=p["department"])
        if p.get("isFeatured"):
            qs = qs.filter(is_featured=truthy(p["isFeatured"]))
        if p.get("isAdmissionOpen"):
            qs = qs.filter(is_admission_open=truthy(p["isAdmissionOpen"]))
        qs = sort(qs, request, {"title": "title", "level": "level"})
        items, meta = paginate(request, qs)
        meta["levels"] = Program.Level.values
        return ok([program_out(request, x) for x in items], meta)


class ProgramDetailView(Public):
    def get(self, request, slug):
        p = programs_qs().filter(slug=slug).first()
        if not p:
            return fail("Program not found", 404)
        data = program_out(request, p, full=True)
        related = programs_qs().filter(department=p.department).exclude(pk=p.pk)[:3] if p.department_id else []
        data["related"] = [{"_id": str(r.pk), "title": r.title, "titleUr": r.title_ur, "slug": r.slug, "level": r.level,
                            "duration": r.duration, "deliveryMode": r.delivery_mode} for r in related]
        return ok(data)


class DepartmentListView(Public):
    def get(self, request):
        qs = Department.objects.filter(is_active=True).annotate(n=Count("programs", filter=Q(programs__is_active=True)))
        if request.query_params.get("q"):
            qs = qs.filter(name__icontains=request.query_params["q"])
        out = []
        for d in qs:
            row = dept_out(request, d)
            row["programCount"] = d.n
            out.append(row)
        return ok(out)


class DepartmentDetailView(Public):
    def get(self, request, slug):
        d = Department.objects.filter(slug=slug, is_active=True).first()
        if not d:
            return fail("Department not found", 404)
        data = dept_out(request, d, full=True)
        data["programs"] = [{"_id": str(p.pk), "title": p.title, "titleUr": p.title_ur, "slug": p.slug, "level": p.level,
                             "deliveryMode": p.delivery_mode, "duration": p.duration, "shortDescription": p.short_description}
                            for p in d.programs.filter(is_active=True)]
        data["faculty"] = [faculty_out(request, f) for f in d.faculty_members.filter(is_active=True)]
        data["galleryItems"] = [gallery_out(request, g) for g in d.gallery_items.filter(is_published=True)]
        return ok(data)


class FacultyListView(Public):
    def get(self, request):
        qs = search(Faculty.objects.filter(is_active=True).select_related("department"), request,
                    ["name", "name_ur", "designation", "specialization"])
        p = request.query_params
        if p.get("department"):
            qs = qs.filter(department_id=p["department"]) if p["department"].isdigit() else qs.filter(department__slug=p["department"])
        if p.get("designation"):
            qs = qs.filter(designation=p["designation"])
        items, meta = paginate(request, sort(qs, request, {"name": "name", "order": "order"}))
        return ok([faculty_out(request, f) for f in items], meta)


class FacultyDetailView(Public):
    def get(self, request, slug):
        f = Faculty.objects.filter(slug=slug, is_active=True).select_related("department").first()
        if not f:
            return fail("Faculty member not found", 404)
        return ok(faculty_out(request, f, full=True))


class NewsListView(Public):
    def get(self, request):
        qs = search(news_qs(), request, ["title", "excerpt"])
        if request.query_params.get("category"):
            qs = qs.filter(category=request.query_params["category"])
        items, meta = paginate(request, sort(qs, request, {"publishedAt": "published_at", "title": "title"}))
        return ok([news_out(request, n) for n in items], meta)


class NewsDetailView(Public):
    def get(self, request, slug):
        n = news_qs().filter(slug=slug).first()
        if not n:
            return fail("Article not found", 404)
        data = news_out(request, n, full=True)
        data["recent"] = [{"_id": str(r.pk), "title": r.title, "slug": r.slug, "publishedAt": iso(r.published_at),
                           "coverImage": media(request, r.cover_image, r.cover_image_url)} for r in news_qs().exclude(pk=n.pk)[:4]]
        return ok(data)


class EventListView(Public):
    def get(self, request):
        qs = search(events_qs(), request, ["title", "description", "location"])
        today = timezone.localdate()
        when = request.query_params.get("when")
        if when == "upcoming":
            qs = qs.filter(start__date__gte=today).order_by("start")
        elif when == "past":
            qs = qs.filter(start__date__lt=today).order_by("-start")
        else:
            qs = qs.order_by("start")
        if request.query_params.get("category"):
            qs = qs.filter(kind=request.query_params["category"])
        items, meta = paginate(request, qs)
        return ok([event_out(request, e) for e in items], meta)


class EventDetailView(Public):
    def get(self, request, slug):
        e = events_qs().filter(slug=slug).first()
        if not e:
            return fail("Event not found", 404)
        return ok(event_out(request, e, full=True))


class AnnouncementListView(Public):
    def get(self, request):
        qs = search(announcements_qs(), request, ["title", "content"])
        if request.query_params.get("type"):
            qs = qs.filter(type=request.query_params["type"])
        items, meta = paginate(request, qs)
        return ok([announcement_out(request, a) for a in items], meta)


class CalendarView(Public):
    def get(self, request):
        qs = CalendarItem.objects.filter(is_published=True)
        if request.query_params.get("category"):
            qs = qs.filter(category=request.query_params["category"])
        if request.query_params.get("term"):
            qs = qs.filter(term=request.query_params["term"])
        return ok([{"_id": str(c.pk), "title": c.title, "description": c.description, "startDate": iso(c.start_date),
                    "endDate": iso(c.end_date), "category": c.category, "term": c.term} for c in qs])


class GalleryView(Public):
    def get(self, request):
        qs = GalleryItem.objects.filter(is_published=True)
        cat = request.query_params.get("category")
        if cat and cat != "all":
            qs = qs.filter(category=cat)
        return ok([gallery_out(request, g) for g in qs[:120]])


class DocumentListView(Public):
    def get(self, request):
        qs = search(documents_qs(), request, ["title", "description"])
        if request.query_params.get("category"):
            qs = qs.filter(category=request.query_params["category"])
        items, meta = paginate(request, sort(qs, request, {"title": "title", "downloads": "downloads"}))
        return ok([document_out(request, d) for d in items], meta)


class DocumentDownloadView(Public):
    def get(self, request, pk):
        d = documents_qs().filter(pk=pk).first()
        if not d or not (d.file or d.file_url):
            return fail("Document not found", 404)
        Document.objects.filter(pk=d.pk).update(downloads=d.downloads + 1)
        return HttpResponseRedirect(media(request, d.file, d.file_url))


class MeritListView(Public):
    def get(self, request):
        qs = MeritList.objects.filter(is_published=True).select_related("program")
        if request.query_params.get("program"):
            qs = qs.filter(program_id=request.query_params["program"])
        return ok([merit_out(m) for m in qs])


class MeritDetailView(Public):
    def get(self, request, pk):
        m = MeritList.objects.filter(pk=pk, is_published=True).select_related("program").first()
        if not m:
            return fail("Merit list not found", 404)
        return ok(merit_out(m, entries=True))


class TestimonialView(Public):
    def get(self, request):
        return ok([testimonial_out(request, t) for t in Testimonial.objects.filter(is_published=True)])


class FaqView(Public):
    def get(self, request):
        qs = Faq.objects.filter(is_published=True)
        if request.query_params.get("category"):
            qs = qs.filter(category=request.query_params["category"])
        return ok([faq_out(f) for f in qs])


class PageView(Public):
    def get(self, request, slug):
        p = Page.objects.filter(slug=slug, is_published=True).first()
        if not p:
            return fail("Page not found", 404)
        return ok({"_id": str(p.pk), "title": p.title, "slug": p.slug, "summary": p.summary, "content": p.content,
                   "metaDescription": p.meta_description, "updatedAt": iso(p.updated_at)})


class SearchView(Public):
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if len(q) < 2:
            return ok({"query": q, "results": [], "total": 0})

        def has(*fields):
            cond = Q()
            for f in fields:
                cond |= Q(**{f"{f}__icontains": q})
            return cond

        results = [
            *({"type": "program", "title": p.title, "description": p.short_description, "url": f"/academics/programs/{p.slug}"}
              for p in programs_qs().filter(has("title", "title_ur", "code", "short_description"))[:6]),
            *({"type": "department", "title": d.name, "description": d.short_description, "url": f"/departments/{d.slug}"}
              for d in Department.objects.filter(is_active=True).filter(has("name", "name_ur", "short_description"))[:5]),
            *({"type": "faculty", "title": f.name, "description": f.designation, "url": f"/faculty/{f.slug}"}
              for f in Faculty.objects.filter(is_active=True).filter(has("name", "name_ur", "designation", "specialization"))[:5]),
            *({"type": "news", "title": n.title, "description": n.excerpt, "url": f"/news/{n.slug}"}
              for n in news_qs().filter(has("title", "excerpt"))[:5]),
            *({"type": "event", "title": e.title, "description": (e.description or "")[:200], "url": f"/events/{e.slug}"}
              for e in events_qs().filter(has("title", "description"))[:5]),
            *({"type": "document", "title": d.title, "description": d.description,
               "url": request.build_absolute_uri(f"/api/site/public/documents/{d.pk}/download"), "external": True}
              for d in documents_qs().filter(has("title", "description"))[:5]),
            *({"type": "page", "title": p.title, "description": p.summary, "url": f"/pages/{p.slug}"}
              for p in Page.objects.filter(is_published=True).filter(has("title", "summary"))[:5]),
            *({"type": "announcement", "title": a.title, "description": f"{a.type} announcement", "url": "/news-events?tab=announcements"}
              for a in announcements_qs().filter(has("title"))[:5]),
        ]
        return ok({"query": q, "results": results, "total": len(results)})


def staff_with(*roles):
    return list(User.objects.filter(role__in=roles, is_active=True))


class ContactView(PublicForm):
    def post(self, request):
        d = request.data
        errors = []
        name, email, subject, message = (str(d.get(k) or "").strip() for k in ("name", "email", "subject", "message"))
        if len(name) < 2:
            errors.append({"field": "name", "message": "Please enter your name"})
        if not re.match(r"^\S+@\S+\.\S+$", email):
            errors.append({"field": "email", "message": "Please enter a valid email"})
        if len(subject) < 3:
            errors.append({"field": "subject", "message": "Subject is required"})
        if len(message) < 10:
            errors.append({"field": "message", "message": "Message should be at least 10 characters"})
        if errors:
            return fail("Please correct the highlighted fields", 400, errors)
        m = ContactMessage.objects.create(name=name[:150], email=email, phone=str(d.get("phone") or "")[:30], subject=subject[:200],
                                          department=str(d.get("department") or "")[:150], message=message[:5000])
        notify(staff_with(R.RECEPTIONIST, R.MEDIA_MANAGER), f"Website message: {m.subject}", m.name, "/m/contact-messages")
        return ok({"_id": str(m.pk)}, status=201, message="Thank you! Your message has been received. We will get back to you soon.")


# ------------------------------------------------------------------------------------------- admissions

PHONE_RX = re.compile(r"^[+\d][\d\s-]{9,16}$")
EMAIL_RX = re.compile(r"^\S+@\S+\.\S+$")
DOC_TYPES = AdmissionDocument.Kind.values
REQUIRED_DOCS = ["photo", "cnic", "guardianCnic"]
ALLOWED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".webp")
MAX_UPLOAD = 5 * 1024 * 1024
QURAN_STATUS = {"hafiz": "Hafiz-e-Quran", "hifz_in_progress": "Hifz in progress", "nazira": "Nazira", "none": "None"}
TRACK_STATUS = {"accepted": "approved"}  # portal status -> website wording


def validate_application(data):
    errors = []

    def err(field, message):
        errors.append({"field": field, "message": message})

    p = data.get("personal") or {}
    s = lambda k: str(p.get(k) or "").strip()  # noqa: E731
    if len(s("fullName")) < 3:
        err("personal.fullName", "Full name is required")
    if len(s("fatherName")) < 3:
        err("personal.fatherName", "Father's name is required")
    if len(digits(p.get("cnic"))) != 13:
        err("personal.cnic", "CNIC / B-Form must contain 13 digits")
    if len(digits(p.get("fatherCnic"))) != 13:
        err("personal.fatherCnic", "Father's CNIC must contain 13 digits")
    dob = parse_date(s("dateOfBirth")[:10]) if s("dateOfBirth") else None
    if not dob:
        err("personal.dateOfBirth", "Valid date of birth is required")
    else:
        age = (timezone.localdate() - dob).days / 365.25
        if age < 4 or age > 80:
            err("personal.dateOfBirth", "Please check the date of birth")
    if s("gender") not in ("male", "female"):
        err("personal.gender", "Gender is required")
    if s("email") and not EMAIL_RX.match(s("email")):
        err("personal.email", "Enter a valid email or leave it blank")
    if not PHONE_RX.match(s("phone")):
        err("personal.phone", "Valid mobile number is required")
    if len(s("address")) < 5:
        err("personal.address", "Permanent address is required")
    if not s("city"):
        err("personal.city", "City is required")
    if len(str(data.get("qualification") or "").strip()) < 2:
        err("qualification", "Educational qualification is required")
    if data.get("quranStatus") and data["quranStatus"] not in QURAN_STATUS:
        err("quranStatus", "Invalid value")
    if data.get("residence") and data["residence"] not in ("boarding", "day_scholar"):
        err("residence", "Invalid value")
    for i, e in enumerate(data.get("education") or []):
        if not e.get("level"):
            err(f"education.{i}.level", "Level is required")
        if e.get("totalMarks") not in ("", None):
            try:
                total, got = float(e["totalMarks"]), float(e.get("obtainedMarks"))
                if total <= 0:
                    err(f"education.{i}.totalMarks", "Total marks must be greater than 0")
                if got < 0 or got > total:
                    err(f"education.{i}.obtainedMarks", "Obtained marks must be between 0 and total marks")
            except (TypeError, ValueError):
                err(f"education.{i}.obtainedMarks", "Enter valid marks")
        if e.get("passingYear"):
            try:
                yr = int(e["passingYear"])
                if not 1970 <= yr <= timezone.now().year + 1:
                    raise ValueError
            except (TypeError, ValueError):
                err(f"education.{i}.passingYear", "Valid passing year is required")
    if not data.get("program"):
        err("program", "Please select a program")
    if data.get("declarationAccepted") not in (True, "true"):
        err("declarationAccepted", "You must accept the declaration")
    if data.get("rulesAccepted") not in (True, "true"):
        err("rulesAccepted", "You must agree to the Jamia rules & regulations")
    return errors


class AdmissionSubmitView(PublicForm):
    @transaction.atomic
    def post(self, request):
        try:
            data = json.loads(request.data.get("data") or "{}")
        except (TypeError, ValueError):
            return fail("Malformed application data")
        errors = validate_application(data)
        files = request.FILES
        for t in REQUIRED_DOCS:
            if t not in files:
                errors.append({"field": f"documents.{t}", "message": "This document is required"})
        for t in files:
            f = files[t]
            if t not in DOC_TYPES:
                continue
            if not f.name.lower().endswith(ALLOWED_EXT):
                errors.append({"field": f"documents.{t}", "message": "Only PDF, JPG, PNG or WEBP files are allowed"})
            elif f.size > MAX_UPLOAD:
                errors.append({"field": f"documents.{t}", "message": "File is larger than 5 MB"})
        if errors:
            return fail("Please correct the highlighted fields", 400, errors)

        site = WebsiteSettings.load()
        if not site.admissions_open:
            return fail("Admissions are currently closed")
        program = Program.objects.filter(pk=str(data["program"]) if str(data["program"]).isdigit() else 0, is_active=True).first()
        if not program:
            return fail("Selected program does not exist", 400, [{"field": "program", "message": "Please select a program"}])
        if not program.is_admission_open:
            return fail("Admissions for the selected program are closed")
        second = None
        if str(data.get("secondChoice") or "").isdigit():
            second = Program.objects.filter(pk=data["secondChoice"], is_active=True).exclude(pk=program.pk).first()

        p = data["personal"]
        cnic = digits(p["cnic"])
        session = str(data.get("session") or site.current_session or "")[:40]
        if AdmissionApplication.objects.filter(cnic=cnic, program=program, session=session).exclude(status="rejected").exists():
            return fail('An application for this program has already been submitted with this CNIC. Use "Track Application" to view its status.', 409)

        g = data.get("guardian") or {}
        guardian_name = str(g.get("name") or "").strip()
        education = [{
            "level": e.get("level"), "degreeTitle": e.get("degreeTitle") or "", "board": e.get("board") or "",
            "institution": e.get("institution") or "", "passingYear": int(e["passingYear"]) if e.get("passingYear") else None,
            "totalMarks": float(e["totalMarks"]) if e.get("totalMarks") not in ("", None) else None,
            "obtainedMarks": float(e["obtainedMarks"]) if e.get("totalMarks") not in ("", None) else None,
        } for e in data.get("education") or []][:5]
        cut = lambda v, n: str(v or "").strip()[:n]  # noqa: E731
        number = f"UMS-{timezone.now():%Y}-{secrets.token_hex(3).upper()}"
        while AdmissionApplication.objects.filter(application_no=number).exists():
            number = f"UMS-{timezone.now():%Y}-{secrets.token_hex(3).upper()}"
        app = AdmissionApplication(
            application_no=number, source="website", full_name=cut(p["fullName"], 150), father_name=cut(p["fatherName"], 150), gender=p["gender"],
            date_of_birth=parse_date(str(p["dateOfBirth"])[:10]), cnic=cnic, phone=cut(p["phone"], 30), email=cut(p.get("email"), 254).lower(),
            address=cut(p["address"], 1000), city=cut(p["city"], 80), province=cut(p.get("province"), 60),
            nationality=cut(p.get("nationality") or "Pakistani", 60), temporary_address=cut(p.get("temporaryAddress"), 1000),
            home_phone=cut(p.get("homePhone"), 30), father_cnic=digits(p.get("fatherCnic")), father_occupation=cut(p.get("fatherOccupation"), 100),
            guardian_name=cut(guardian_name or p["fatherName"], 150), guardian_relation="other" if guardian_name else "father",
            guardian_phone=cut(p.get("guardianPhone") or p["phone"], 30), guardian_cnic=digits(p.get("fatherCnic")),
            guardian_occupation=cut(g.get("occupation") or p.get("fatherOccupation"), 100),
            previous_institution=cut(data.get("previousMadrasa"), 200), previous_education=cut(data.get("qualification"), 200),
            quran_status=QURAN_STATUS.get(data.get("quranStatus"), ""), darjah=cut(data.get("classLevel"), 80),
            residence=data.get("residence") or "boarding", needs_hostel=(data.get("residence") or "boarding") == "boarding",
            program=program, second_choice=second, session=session,
            shift=data.get("shift") if data.get("shift") in ("morning", "evening", "weekend") else "morning",
            education=education, declaration_accepted=True, rules_accepted=True,
            submitted_ip=request.META.get("REMOTE_ADDR"),
        )
        app.compute_aggregate()
        if "photo" in files:
            app.photo = files["photo"]
        app.save()
        for t in DOC_TYPES:
            for f in files.getlist(t)[:4]:
                AdmissionDocument.objects.create(application=app, kind=t, file=f, original_name=f.name[:200], size=f.size)
        notify(staff_with(R.ADMISSION_OFFICER, R.PRINCIPAL), f"New online application: {app.full_name}",
               f"{app.application_no} — {program.title}", "/m/admissions", "admission")
        return ok({"applicationNumber": app.application_no, "status": app.status, "program": program.title,
                   "submittedAt": iso(app.created_at)}, status=201, message="Application submitted successfully")


class AdmissionTrackView(PublicForm):
    def post(self, request):
        number = str(request.data.get("applicationNumber") or "").strip().upper()
        app = AdmissionApplication.objects.filter(application_no=number).select_related("program").first()
        # Same answer for "not found" and "CNIC mismatch" so application numbers cannot be probed.
        if not app or not number or digits(app.cnic) != digits(request.data.get("cnic")):
            return fail("No application found for the provided application number and CNIC", 404)
        entry = (MeritListEntry.objects.filter(application=app, merit_list__is_published=True)
                 .select_related("merit_list").order_by("-merit_list__published_at").first())
        status = TRACK_STATUS.get(app.status, app.status)
        timeline = [{"status": TRACK_STATUS.get(h.get("status"), h.get("status")), "remarks": h.get("remarks") or "", "at": h.get("at")}
                    for h in app.status_history or []] or [{"status": "submitted", "remarks": "Application received", "at": iso(app.created_at)}]
        return ok({
            "applicationNumber": app.application_no, "name": app.full_name,
            "program": {"_id": str(app.program_id), "title": app.program.title, "code": app.program.code} if app.program else
                       {"title": str(app.department or app.class_level or "")},
            "session": app.session, "shift": app.shift, "aggregate": num(app.aggregate), "status": status,
            "remarks": app.remarks, "submittedAt": iso(app.created_at), "timeline": timeline,
            "documents": [{"type": d.kind, "originalName": d.original_name} for d in app.documents.all()],
            "merit": {"title": entry.merit_list.title, "round": entry.merit_list.round, "rank": entry.rank} if entry else None,
        })
