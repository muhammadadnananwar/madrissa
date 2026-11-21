from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("site-settings", views.SiteSettingsViewSet)
router.register("pages", views.PageViewSet)
router.register("slides", views.SlideViewSet)
router.register("programs", views.ProgramViewSet)
router.register("news", views.NewsPostViewSet)
router.register("gallery-albums", views.GalleryAlbumViewSet)
router.register("gallery-images", views.GalleryImageViewSet)
router.register("testimonials", views.TestimonialViewSet)
router.register("faqs", views.FAQViewSet)
router.register("board-members", views.BoardMemberViewSet)
router.register("stats", views.StatViewSet)
router.register("downloads", views.DownloadViewSet)
router.register("contact-messages", views.ContactMessageViewSet)
router.register("subscribers", views.SubscriberViewSet)
router.register("fatwas", views.FatwaQuestionViewSet)

# Anonymous API consumed by the public website (separate Astro site)
public_urlpatterns = [
    path("site/", views.SiteView.as_view()),
    path("home/", views.HomeView.as_view()),
    path("pages/<slug:slug>/", views.PageDetailView.as_view()),
    path("programs/", views.ProgramListView.as_view()),
    path("programs/<slug:slug>/", views.ProgramDetailView.as_view()),
    path("news/", views.NewsListView.as_view()),
    path("news/<slug:slug>/", views.NewsDetailView.as_view()),
    path("events/", views.EventListView.as_view()),
    path("events/<slug:slug>/", views.EventDetailView.as_view()),
    path("gallery/", views.GalleryListView.as_view()),
    path("gallery/<int:pk>/", views.GalleryDetailView.as_view()),
    path("teachers/", views.TeacherListView.as_view()),
    path("teachers/<int:pk>/", views.TeacherDetailView.as_view()),
    path("board/", views.BoardView.as_view()),
    path("faqs/", views.FAQListView.as_view()),
    path("downloads/", views.DownloadListView.as_view()),
    path("fatwas/", views.FatwaListView.as_view()),
    path("fatwas/<int:pk>/", views.FatwaDetailView.as_view()),
    path("library/", views.LibraryCatalogueView.as_view()),
    path("admission-options/", views.AdmissionOptionsView.as_view()),
    path("admission-status/", views.AdmissionStatusView.as_view()),
    path("verify-certificate/", views.VerifyCertificateView.as_view()),
    path("admission/", views.AdmissionApplyView.as_view()),
    path("contact/", views.ContactView.as_view()),
    path("subscribe/", views.SubscribeView.as_view()),
    path("fatwa/ask/", views.AskFatwaView.as_view()),
    path("donate/", views.DonatePledgeView.as_view()),
]

urlpatterns = router.urls
