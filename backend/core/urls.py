from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.HealthView.as_view()),
    path("meta/", views.MetaView.as_view()),
    path("meta/<slug:key>/", views.ResourceMetaView.as_view()),
    path("options/<slug:key>/", views.OptionsView.as_view()),
    path("search/", views.SearchView.as_view()),
    path("dashboard/", views.DashboardView.as_view()),
]
