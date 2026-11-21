from django.urls import re_path
from rest_framework.routers import SimpleRouter

from . import api, views

router = SimpleRouter()
for vs in (views.WebsiteSettingsViewSet, views.DepartmentViewSet, views.ProgramViewSet, views.FacultyViewSet, views.NewsViewSet,
           views.AnnouncementViewSet, views.CalendarItemViewSet, views.GalleryItemViewSet, views.DocumentViewSet,
           views.TestimonialViewSet, views.FaqViewSet, views.PageViewSet, views.MeritListViewSet, views.MeritListEntryViewSet):
    router.register(vs.resource_key, vs)

urlpatterns = router.urls


def p(route, view):
    """Paths work with or without a trailing slash (the React site calls them without)."""
    return re_path(rf"^{route}/?$", view.as_view())


# Mounted at /api/site/public/
site_urlpatterns = [
    p("settings", api.SettingsView),
    p("home", api.HomeView),
    p("search", api.SearchView),
    p("programs", api.ProgramListView),
    p(r"programs/(?P<slug>[-\w]+)", api.ProgramDetailView),
    p("departments", api.DepartmentListView),
    p(r"departments/(?P<slug>[-\w]+)", api.DepartmentDetailView),
    p("faculty", api.FacultyListView),
    p(r"faculty/(?P<slug>[-\w]+)", api.FacultyDetailView),
    p("news", api.NewsListView),
    p(r"news/(?P<slug>[-\w]+)", api.NewsDetailView),
    p("events", api.EventListView),
    p(r"events/(?P<slug>[-\w]+)", api.EventDetailView),
    p("announcements", api.AnnouncementListView),
    p("calendar", api.CalendarView),
    p("gallery", api.GalleryView),
    p("documents", api.DocumentListView),
    p(r"documents/(?P<pk>\d+)/download", api.DocumentDownloadView),
    p("merit-lists", api.MeritListView),
    p(r"merit-lists/(?P<pk>\d+)", api.MeritDetailView),
    p("testimonials", api.TestimonialView),
    p("faqs", api.FaqView),
    p(r"pages/(?P<slug>[-\w]+)", api.PageView),
    p("contact", api.ContactView),
    p("admissions/track", api.AdmissionTrackView),
    p("admissions", api.AdmissionSubmitView),
]
