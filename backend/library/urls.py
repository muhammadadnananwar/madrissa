from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("book-categories", views.BookCategoryViewSet)
router.register("books", views.BookViewSet)
router.register("book-issues", views.BookIssueViewSet)
router.register("book-reservations", views.BookReservationViewSet)

urlpatterns = [path("library/overdue/", views.OverdueBooksView.as_view()), *router.urls]
