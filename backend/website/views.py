"""
Website CMS (managed from the portal) + the PUBLIC API consumed by the separate public website.

Everything under /api/public/ is anonymous, read-only (except a few throttled forms) and only
ever exposes published content.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from academics.models import ClassLevel, Department
from accounts.models import User
from communication.models import Event
from communication.services import notify
from core.audit import audit
from core.roles import ADMINS, ALL, FRONT_DESK, IFTA, R, WEBSITE
from core.viewsets import BaseModelViewSet
from people.models import AdmissionApplication, Employee
from people.serializers import AdmissionPublicSerializer

from . import serializers as s
from .models import (FAQ, BoardMember, ContactMessage, Download, FatwaQuestion, GalleryAlbum, GalleryImage, NewsPost, Page,
                     Program, SiteSettings, Slide, Stat, Subscriber, Testimonial)

G = "Website CMS"


class CmsBase(BaseModelViewSet):
    read_roles = write_roles = WEBSITE
    group = G


class SiteSettingsViewSet(BaseModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = s.SiteSettingsSerializer
    resource_key = "site-settings"
    read_roles, write_roles = ALL, ADMINS
    label, group, icon, menu_roles = "Institution Settings", "Administration", "settings", ADMINS + [R.MEDIA_MANAGER]


class PageViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = Page.objects.all()
    serializer_class = s.PageSerializer
    resource_key = "pages"
    search_fields = ["title", "slug"]
    label, icon = "Pages (History, About...)", "file"
    list_fields = ["title", "slug", "order", "show_in_menu", "is_published"]


class SlideViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = Slide.objects.all()
    serializer_class = s.SlideSerializer
    resource_key = "slides"
    label, icon = "Homepage Slider", "image"
    list_fields = ["title", "order", "is_active"]


class ProgramViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = Program.objects.all()
    serializer_class = s.ProgramSerializer
    resource_key = "programs"
    label, icon = "Programs / Courses", "book"
    list_fields = ["title", "department", "duration", "order", "is_published"]


class NewsPostViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = NewsPost.objects.all()
    serializer_class = s.NewsPostSerializer
    resource_key = "news"
    search_fields = ["title", "summary"]
    label, icon = "News & Articles", "news"
    list_fields = ["title", "category", "published_at", "is_published", "author"]


class GalleryAlbumViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = GalleryAlbum.objects.all()
    serializer_class = s.GalleryAlbumSerializer
    resource_key = "gallery-albums"
    label, icon = "Gallery Albums", "image"
    list_fields = ["title", "date", "is_published"]


class GalleryImageViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = GalleryImage.objects.all()
    serializer_class = s.GalleryImageSerializer
    resource_key = "gallery-images"
    label, icon = "Gallery Images", "image"
    list_fields = ["album", "caption", "order"]


class TestimonialViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = Testimonial.objects.all()
    serializer_class = s.TestimonialSerializer
    resource_key = "testimonials"
    icon = "quote"
    list_fields = ["name", "role", "is_published"]


class FAQViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = FAQ.objects.all()
    serializer_class = s.FAQSerializer
    resource_key = "faqs"
    label, icon = "FAQs", "help"
    list_fields = ["question", "category", "order"]


class BoardMemberViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = BoardMember.objects.all()
    serializer_class = s.BoardMemberSerializer
    resource_key = "board-members"
    label, icon = "Founders & Board", "users"
    list_fields = ["name", "title", "is_founder", "order"]


class StatViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = Stat.objects.all()
    serializer_class = s.StatSerializer
    resource_key = "stats"
    label, icon = "Homepage Statistics", "bar"
    list_fields = ["label", "value", "order"]


class DownloadViewSet(CmsBase):
    menu_roles = []  # superseded by the new website's content screens (cms app)
    queryset = Download.objects.all()
    serializer_class = s.DownloadSerializer
    resource_key = "downloads"
    icon = "download"
    list_fields = ["title", "category", "is_published"]


class ContactMessageViewSet(CmsBase):
    queryset = ContactMessage.objects.all()
    serializer_class = s.ContactMessageSerializer
    resource_key = "contact-messages"
    read_roles = write_roles = WEBSITE + FRONT_DESK
    search_fields = ["name", "email", "subject"]
    label, group, icon = "Contact Messages", "Front Desk", "inbox"
    list_fields = ["name", "subject", "phone", "email", "is_resolved", "created_at"]


class SubscriberViewSet(CmsBase):
    queryset = Subscriber.objects.all()
    serializer_class = s.SubscriberSerializer
    resource_key = "subscribers"
    label, icon = "Newsletter Subscribers", "mail"
    list_fields = ["email", "is_active", "created_at"]


class FatwaQuestionViewSet(BaseModelViewSet):
    queryset = FatwaQuestion.objects.all()
    serializer_class = s.FatwaQuestionSerializer
    resource_key = "fatwas"
    read_roles = write_roles = IFTA
    search_fields = ["title", "question", "fatwa_no", "name"]
    filterset_fields = ["status", "category", "assigned_to", "is_public"]
    label, group, icon = "Dar-ul-Ifta Questions", "Dar-ul-Ifta", "scale"
    list_fields = ["fatwa_no", "title", "category", "status", "assigned_to", "is_public", "created_at"]
    ui_actions = [{"name": "answer", "label": "Publish answer", "style": "success", "roles": IFTA,
                   "input": [{"name": "answer", "type": "text", "label": "Answer (leave empty to use saved answer)"}]}]

    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        f = self.get_object()
        ser = s.FatwaAnswerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        f.answer = ser.validated_data["answer"] or f.answer
        if not f.answer:
            return Response({"detail": "Write the answer first."}, status=400)
        f.status = FatwaQuestion.Status.ANSWERED
        f.answered_at = timezone.now()
        f.assigned_to = f.assigned_to or request.user
        if not f.fatwa_no:
            f.fatwa_no = f"F-{timezone.now():%Y}-{FatwaQuestion.objects.filter(status='answered').count() + 1:04d}"
        f.save()
        if f.email:
            send_mail(f"Answer to your question: {f.title}", f"{f.answer}\n\n— Dar-ul-Ifta, {SiteSettings.get().name}",
                      settings.DEFAULT_FROM_EMAIL, [f.email], fail_silently=True)
        audit(request, "answer", f, "fatwas")
        return Response({"detail": f"Answered ({f.fatwa_no})."})


# ===========================================================================
# PUBLIC API
# ===========================================================================
def _abs(request, f):
    try:
        return request.build_absolute_uri(f.url) if f else None
    except ValueError:
        return None


def site_dict(request):
    x = SiteSettings.get()
    return {"name": x.name, "name_arabic": x.name_arabic, "tagline": x.tagline, "logo": _abs(request, x.logo),
            "founded_year": x.founded_year, "affiliation": x.affiliation, "registration_no": x.registration_no,
            "address": x.address, "city": x.city, "phone": x.phone, "whatsapp": x.whatsapp, "email": x.email,
            "map_embed_url": x.map_embed_url, "facebook": x.facebook, "youtube": x.youtube, "instagram": x.instagram,
            "twitter": x.twitter, "about_short": x.about_short, "donation_bank_details": x.donation_bank_details,
            "admissions_open": x.admissions_open, "prayer_city": x.prayer_city, "prayer_country": x.prayer_country,
            "menu_pages": [{"slug": p.slug, "title": p.title} for p in Page.objects.filter(is_published=True, show_in_menu=True)]}


def teacher_dict(request, e, full=False):
    d = {"id": e.id, "name": e.user.display_name, "name_arabic": e.user.name_arabic, "designation": e.designation,
         "department": e.department.name if e.department else None, "photo": _abs(request, e.user.photo),
         "qualification": e.highest_qualification, "specialization": e.specialization, "kind": e.kind}
    if full:
        d.update({"bio": e.bio, "ijazah": e.ijazah, "experience_years": e.experience_years,
                  "joining_year": e.joining_date.year if e.joining_date else None,
                  "subjects": sorted({a.subject.name for a in e.user.teaching_assignments.select_related("subject")})})
    return d


def news_dict(request, n, full=False):
    d = {"slug": n.slug, "title": n.title, "summary": n.summary, "image": _abs(request, n.image), "category": n.category,
         "published_at": n.published_at}
    if full:
        d["body"] = n.body
    return d


def event_dict(request, e, full=False):
    d = {"slug": e.slug, "title": e.title, "kind": e.get_kind_display(), "start": e.start, "end": e.end,
         "location": e.location, "image": _abs(request, e.image)}
    if full:
        d["description"] = e.description
    return d


def program_dict(request, p, full=False):
    d = {"slug": p.slug, "title": p.title, "title_arabic": p.title_arabic, "summary": p.summary, "duration": p.duration,
         "eligibility": p.eligibility, "timings": p.timings, "image": _abs(request, p.image), "icon": p.icon,
         "department": p.department.name if p.department else None}
    if full:
        d["description"] = p.description
    return d


def public_teachers():
    return Employee.objects.filter(show_on_website=True, status="active").select_related("user", "department")


class PublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


class PublicFormView(PublicView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_forms"
    parser_classes = [JSONParser, MultiPartParser, FormParser]


class SiteView(PublicView):
    def get(self, request):
        return Response(site_dict(request))


class HomeView(PublicView):
    def get(self, request):
        now = timezone.now()
        about = Page.objects.filter(slug="about", is_published=True).first()
        return Response({
            "site": site_dict(request),
            "slides": [{"title": x.title, "subtitle": x.subtitle, "image": _abs(request, x.image), "cta_text": x.cta_text,
                        "cta_link": x.cta_link} for x in Slide.objects.filter(is_active=True)],
            "stats": [{"label": x.label, "value": x.value, "icon": x.icon} for x in Stat.objects.all()],
            "programs": [program_dict(request, p) for p in Program.objects.filter(is_published=True).select_related("department")[:8]],
            "news": [news_dict(request, n) for n in NewsPost.objects.filter(is_published=True, published_at__lte=now)[:3]],
            "events": [event_dict(request, e) for e in Event.objects.filter(
                is_public=True, start__gte=now - timezone.timedelta(days=1)).order_by("start")[:4]],
            "teachers": [teacher_dict(request, e) for e in public_teachers()[:8]],
            "testimonials": [{"name": t.name, "role": t.role, "quote": t.quote, "photo": _abs(request, t.photo)}
                             for t in Testimonial.objects.filter(is_published=True)[:6]],
            "about": {"title": about.title, "subtitle": about.subtitle, "body": about.body,
                      "image": _abs(request, about.image)} if about else None,
        })


class PageDetailView(PublicView):
    def get(self, request, slug):
        p = get_object_or_404(Page, slug=slug, is_published=True)
        return Response({"slug": p.slug, "title": p.title, "subtitle": p.subtitle, "body": p.body,
                         "image": _abs(request, p.image), "updated_at": p.updated_at})


class ProgramListView(PublicView):
    def get(self, request):
        return Response([program_dict(request, p) for p in Program.objects.filter(is_published=True).select_related("department")])


class ProgramDetailView(PublicView):
    def get(self, request, slug):
        return Response(program_dict(request, get_object_or_404(Program, slug=slug, is_published=True), True))


class NewsListView(PublicView):
    def get(self, request):
        qs = NewsPost.objects.filter(is_published=True, published_at__lte=timezone.now())
        if request.query_params.get("category"):
            qs = qs.filter(category=request.query_params["category"])
        page = Paginator(qs, 9).get_page(request.query_params.get("page", 1))
        cats = NewsPost.objects.filter(is_published=True).exclude(category="").values_list("category", flat=True)
        return Response({"results": [news_dict(request, n) for n in page], "page": page.number,
                         "pages": page.paginator.num_pages, "categories": sorted(set(cats))})


class NewsDetailView(PublicView):
    def get(self, request, slug):
        n = get_object_or_404(NewsPost, slug=slug, is_published=True)
        related = NewsPost.objects.filter(is_published=True).exclude(pk=n.pk)[:3]
        return Response({**news_dict(request, n, True), "related": [news_dict(request, r) for r in related]})


class EventListView(PublicView):
    def get(self, request):
        cutoff = timezone.now() - timezone.timedelta(days=1)
        qs = Event.objects.filter(is_public=True)
        return Response({"upcoming": [event_dict(request, e) for e in qs.filter(start__gte=cutoff).order_by("start")[:30]],
                         "past": [event_dict(request, e) for e in qs.filter(start__lt=cutoff).order_by("-start")[:30]]})


class EventDetailView(PublicView):
    def get(self, request, slug):
        return Response(event_dict(request, get_object_or_404(Event, slug=slug, is_public=True), True))


class GalleryListView(PublicView):
    def get(self, request):
        out = []
        for a in GalleryAlbum.objects.filter(is_published=True).prefetch_related("images"):
            imgs = list(a.images.all())
            out.append({"id": a.id, "title": a.title, "description": a.description, "date": a.date, "count": len(imgs),
                        "cover": _abs(request, a.cover) or (_abs(request, imgs[0].image) if imgs else None)})
        return Response(out)


class GalleryDetailView(PublicView):
    def get(self, request, pk):
        a = get_object_or_404(GalleryAlbum, pk=pk, is_published=True)
        return Response({"id": a.id, "title": a.title, "description": a.description, "date": a.date,
                         "images": [{"image": _abs(request, i.image), "caption": i.caption} for i in a.images.all()]})


class TeacherListView(PublicView):
    def get(self, request):
        qs = public_teachers()
        if request.query_params.get("department"):
            qs = qs.filter(department__name=request.query_params["department"])
        return Response({"results": [teacher_dict(request, e) for e in qs],
                         "departments": sorted({e.department.name for e in public_teachers() if e.department})})


class TeacherDetailView(PublicView):
    def get(self, request, pk):
        return Response(teacher_dict(request, get_object_or_404(public_teachers(), pk=pk), True))


class BoardView(PublicView):
    def get(self, request):
        return Response([{"name": b.name, "title": b.title, "photo": _abs(request, b.photo), "bio": b.bio,
                          "is_founder": b.is_founder} for b in BoardMember.objects.all()])


class FAQListView(PublicView):
    def get(self, request):
        return Response([{"question": f.question, "answer": f.answer, "category": f.category} for f in FAQ.objects.all()])


class DownloadListView(PublicView):
    def get(self, request):
        return Response([{"title": d.title, "category": d.category, "file": _abs(request, d.file)}
                         for d in Download.objects.filter(is_published=True)])


class FatwaListView(PublicView):
    def get(self, request):
        qs = FatwaQuestion.objects.filter(status="answered", is_public=True)
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(question__icontains=q) | Q(answer__icontains=q))
        if request.query_params.get("category"):
            qs = qs.filter(category=request.query_params["category"])
        page = Paginator(qs.order_by("-answered_at"), 15).get_page(request.query_params.get("page", 1))
        cats = FatwaQuestion.objects.filter(status="answered", is_public=True).values_list("category", flat=True)
        return Response({"results": [{"id": f.id, "fatwa_no": f.fatwa_no, "title": f.title, "category": f.category,
                                      "answered_at": f.answered_at} for f in page],
                         "page": page.number, "pages": page.paginator.num_pages, "categories": sorted(set(cats))})


class FatwaDetailView(PublicView):
    def get(self, request, pk):
        f = get_object_or_404(FatwaQuestion, pk=pk, status="answered", is_public=True)
        return Response({"id": f.id, "fatwa_no": f.fatwa_no, "title": f.title, "category": f.category,
                         "question": f.question, "answer": f.answer, "answered_at": f.answered_at})


class LibraryCatalogueView(PublicView):
    def get(self, request):
        from library.models import Book
        q = request.query_params.get("q", "")
        qs = Book.objects.select_related("category")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(title_arabic__icontains=q))
        return Response([{"title": b.title, "title_arabic": b.title_arabic, "author": b.author,
                          "category": str(b.category or ""), "language": b.get_language_display(),
                          "available": b.available_copies > 0} for b in qs[:60]])


class AdmissionOptionsView(PublicView):
    def get(self, request):
        return Response({"departments": [{"id": d.id, "name": d.name} for d in Department.objects.filter(is_active=True)],
                         "class_levels": [{"id": c.id, "name": c.name, "department": c.department_id}
                                          for c in ClassLevel.objects.all()],
                         "open": SiteSettings.get().admissions_open})


class AdmissionStatusView(PublicView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_forms"

    def get(self, request):
        no = request.query_params.get("application_no", "").strip()
        phone = request.query_params.get("phone", "").strip()
        app = AdmissionApplication.objects.filter(Q(guardian_phone=phone) | Q(phone=phone), application_no=no).first() \
            if no and phone else None
        if not app:
            return Response({"detail": "No application found with these details."}, status=404)
        show_remarks = app.status in ("accepted", "rejected", "waitlisted", "test_scheduled")
        return Response({"application_no": app.application_no, "name": app.full_name, "status": app.get_status_display(),
                         "test_date": app.test_date, "submitted": app.created_at, "remarks": app.remarks if show_remarks else ""})


class VerifyCertificateView(PublicView):
    def get(self, request):
        from exams.models import Certificate
        code = request.query_params.get("code", "").strip()
        c = Certificate.objects.filter(Q(verification_code=code) | Q(serial_no__iexact=code)).select_related("person").first() \
            if code else None
        if not c:
            return Response({"valid": False, "detail": "No certificate found."}, status=404)
        return Response({"valid": not c.is_revoked, "revoked": c.is_revoked, "serial_no": c.serial_no, "title": c.title,
                         "kind": c.get_kind_display(), "name": c.person.display_name, "father_name": c.person.father_name,
                         "issue_date": c.issue_date, "grade": c.grade})


def staff_with(*roles):
    return list(User.objects.filter(role__in=roles, is_active=True))


class AdmissionApplyView(PublicFormView):
    def post(self, request):
        if not SiteSettings.get().admissions_open:
            return Response({"detail": "Admissions are currently closed."}, status=400)
        ser = AdmissionPublicSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        app = ser.save()
        notify(staff_with(R.ADMISSION_OFFICER, R.PRINCIPAL), f"New admission application: {app.full_name}",
               f"{app.application_no} — {app.department or ''}", "/m/admissions", "admission")
        return Response({"detail": "Application submitted. JazakAllah khair!", "application_no": app.application_no}, status=201)


class ContactView(PublicFormView):
    def post(self, request):
        ser = s.ContactFormSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        m = ser.save()
        notify(staff_with(R.RECEPTIONIST, R.MEDIA_MANAGER), f"Website message: {m.subject}", m.name, "/m/contact-messages")
        return Response({"detail": "Message received. We will contact you soon, in sha Allah."}, status=201)


class SubscribeView(PublicFormView):
    def post(self, request):
        ser = s.SubscribeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        Subscriber.objects.update_or_create(email=ser.validated_data["email"].lower(), defaults={"is_active": True})
        return Response({"detail": "Subscribed."}, status=201)


class AskFatwaView(PublicFormView):
    def post(self, request):
        ser = s.FatwaAskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        f = ser.save()
        notify(staff_with(R.MUFTI), f"New question: {f.title}", f.category, "/m/fatwas", "fatwa")
        return Response({"detail": "Your question has been submitted to Dar-ul-Ifta.", "id": f.id}, status=201)


class DonatePledgeView(PublicFormView):
    def post(self, request):
        from finance.models import Donation
        ser = s.DonationPledgeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.save(status=Donation.Status.PLEDGED)
        notify(staff_with(R.ACCOUNTANT), f"Donation pledge: {d.amount} ({d.get_fund_display()})", d.donor_name,
               "/m/donations", "donation")
        return Response({"detail": "JazakAllah khair! Your pledge was recorded. Please transfer using the details shown.",
                         "receipt_no": d.receipt_no, "bank_details": SiteSettings.get().donation_bank_details}, status=201)
