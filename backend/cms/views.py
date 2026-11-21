"""Portal management of the public website content (menu group "Website")."""
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response

from core.audit import audit
from core.roles import ADMISSION, ADMINS, ALL, R, WEBSITE
from core.viewsets import BaseModelViewSet
from people.models import AdmissionApplication

from . import models as m
from . import serializers as s

G = "Website"


class WebBase(BaseModelViewSet):
    read_roles = write_roles = WEBSITE
    group = G


class WebsiteSettingsViewSet(WebBase):
    queryset = m.WebsiteSettings.objects.all()
    serializer_class = s.WebsiteSettingsSerializer
    resource_key = "web-settings"
    label, icon = "Website settings & content", "settings"
    list_fields = ["university_name", "short_name", "current_session", "admissions_open", "updated_at"]


class DepartmentViewSet(WebBase):
    queryset = m.Department.objects.all()
    serializer_class = s.DepartmentSerializer
    resource_key = "web-departments"
    search_fields = ["name", "name_ur", "code"]
    filterset_fields = ["is_active"]
    label, icon = "Departments (website)", "building"
    list_fields = ["name", "code", "faculty", "order", "is_active"]


class ProgramViewSet(WebBase):
    queryset = m.Program.objects.all()
    serializer_class = s.ProgramSerializer
    resource_key = "web-programs"
    search_fields = ["title", "title_ur", "code"]
    filterset_fields = ["level", "delivery_mode", "department", "is_featured", "is_admission_open", "is_active"]
    label, icon = "Programs & courses (website)", "book"
    list_fields = ["title", "level", "delivery_mode", "department", "is_featured", "is_admission_open", "is_active"]


class FacultyViewSet(WebBase):
    queryset = m.Faculty.objects.all()
    serializer_class = s.FacultySerializer
    resource_key = "web-faculty"
    search_fields = ["name", "name_ur", "designation"]
    filterset_fields = ["department", "is_active"]
    label, icon = "Faculty profiles (website)", "users"
    list_fields = ["name", "designation", "department", "order", "is_active"]


class NewsViewSet(WebBase):
    queryset = m.News.objects.all()
    serializer_class = s.NewsSerializer
    resource_key = "web-news"
    search_fields = ["title", "excerpt"]
    filterset_fields = ["category", "is_published"]
    label, icon = "News (website)", "news"
    list_fields = ["title", "category", "published_at", "is_published"]


class AnnouncementViewSet(WebBase):
    queryset = m.Announcement.objects.all()
    serializer_class = s.AnnouncementSerializer
    resource_key = "web-announcements"
    search_fields = ["title"]
    filterset_fields = ["type", "is_published", "is_pinned"]
    label, icon = "Announcements (website)", "megaphone"
    list_fields = ["title", "type", "is_pinned", "publish_date", "expires_at", "is_published"]


class CalendarItemViewSet(WebBase):
    queryset = m.CalendarItem.objects.all()
    serializer_class = s.CalendarItemSerializer
    resource_key = "web-calendar"
    filterset_fields = ["category", "term", "is_published"]
    label, icon = "Academic calendar (website)", "calendar"
    list_fields = ["title", "start_date", "end_date", "category", "term", "is_published"]


class GalleryItemViewSet(WebBase):
    queryset = m.GalleryItem.objects.all()
    serializer_class = s.GalleryItemSerializer
    resource_key = "web-gallery"
    filterset_fields = ["category", "department", "is_published"]
    label, icon = "Gallery (website)", "image"
    list_fields = ["title", "category", "department", "order", "is_published"]


class DocumentViewSet(WebBase):
    queryset = m.Document.objects.all()
    serializer_class = s.DocumentSerializer
    resource_key = "web-documents"
    search_fields = ["title", "description"]
    filterset_fields = ["category", "audience", "is_published"]
    label, icon = "Download center (website)", "download"
    list_fields = ["title", "category", "audience", "downloads", "is_published"]


class TestimonialViewSet(WebBase):
    queryset = m.Testimonial.objects.all()
    serializer_class = s.TestimonialSerializer
    resource_key = "web-testimonials"
    label, icon = "Testimonials (website)", "quote"
    list_fields = ["name", "program", "batch", "order", "is_published"]


class FaqViewSet(WebBase):
    queryset = m.Faq.objects.all()
    serializer_class = s.FaqSerializer
    resource_key = "web-faqs"
    search_fields = ["question"]
    filterset_fields = ["category", "is_published"]
    label, icon = "FAQs (website)", "help"
    list_fields = ["question", "category", "order", "is_published"]


class PageViewSet(WebBase):
    queryset = m.Page.objects.all()
    serializer_class = s.PageSerializer
    resource_key = "web-pages"
    search_fields = ["title", "slug"]
    label, icon = "Pages (website)", "file"
    list_fields = ["title", "slug", "is_published", "updated_at"]


class MeritListViewSet(BaseModelViewSet):
    queryset = m.MeritList.objects.all()
    serializer_class = s.MeritListSerializer
    resource_key = "merit-lists"
    read_roles = write_roles = ADMISSION
    filterset_fields = ["program", "session", "is_published"]
    label, group, icon = "Merit lists", "Admissions", "list"
    list_fields = ["title", "program", "session", "round", "is_published", "published_at"]
    ui_actions = [{"name": "generate", "label": "Generate from applications", "roles": ADMISSION,
                   "confirm": "Replace this list's entries with applicants of its program and session, ranked by aggregate?",
                   "input": [{"name": "limit", "type": "decimal", "label": "Number of candidates (blank = all)"}]}]

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def generate(self, request, pk=None):
        ml = self.get_object()
        apps = AdmissionApplication.objects.filter(program=ml.program).exclude(status__in=["rejected", "enrolled"])
        if ml.session:
            apps = apps.filter(session=ml.session)
        apps = apps.order_by("-aggregate", "created_at")
        try:
            limit = int(float(request.data.get("limit") or 0))
        except ValueError:
            limit = 0
        if limit > 0:
            apps = apps[:limit]
        ml.entries.all().delete()
        m.MeritListEntry.objects.bulk_create([
            m.MeritListEntry(merit_list=ml, application=a, application_number=a.application_no, name=a.full_name,
                             aggregate=a.aggregate, rank=i + 1) for i, a in enumerate(apps)])
        audit(request, "generate", ml, "merit-lists", {"entries": ml.entries.count()})
        return Response({"detail": f"{ml.entries.count()} candidate(s) ranked."})


class MeritListEntryViewSet(BaseModelViewSet):
    queryset = m.MeritListEntry.objects.all()
    serializer_class = s.MeritListEntrySerializer
    resource_key = "merit-list-entries"
    read_roles = write_roles = ADMISSION
    search_fields = ["application_number", "name"]
    filterset_fields = ["merit_list"]
    label, group, icon = "Merit list entries", "Admissions", "list"
    list_fields = ["merit_list", "rank", "application_number", "name", "aggregate"]
