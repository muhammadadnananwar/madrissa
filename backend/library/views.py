from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.services import notify
from core.audit import audit
from core.roles import ALL, LIBRARY, has_role
from core.scopes import by_user, own
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import Book, BookCategory, BookIssue, BookReservation

G = "Library"


class BookCategoryViewSet(BaseModelViewSet):
    queryset = BookCategory.objects.all()
    serializer_class = s.BookCategorySerializer
    resource_key = "book-categories"
    read_roles, write_roles = ALL, LIBRARY
    group, icon = G, "folder"
    list_fields = ["name", "description"]


class BookViewSet(BaseModelViewSet):
    queryset = Book.objects.all()
    serializer_class = s.BookSerializer
    resource_key = "books"
    read_roles, write_roles = ALL, LIBRARY
    search_fields = ["title", "title_arabic", "author", "isbn", "publisher"]
    filterset_fields = ["category", "language", "is_reference_only"]
    label, group, icon, menu_roles = "Books / Catalogue", G, "book", ALL
    list_fields = ["title", "author", "category", "language", "shelf", "available_copies", "total_copies"]
    ui_actions = [
        {"name": "issue", "label": "Issue book", "style": "success", "roles": LIBRARY,
         "input": [{"name": "borrower", "type": "fk", "resource": "users", "label": "Borrower", "required": True},
                   {"name": "due_date", "type": "date", "label": "Due date (default 14 days)"}]},
        {"name": "reserve", "label": "Reserve", "roles": ALL, "confirm": "Reserve this book?"},
    ]

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def issue(self, request, pk=None):
        book = Book.objects.select_for_update().get(pk=self.get_object().pk)
        ser = s.IssueBookSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if book.is_reference_only:
            raise ValidationError({"detail": "Reference-only book cannot be issued."})
        if book.available_copies < 1:
            raise ValidationError({"detail": "No copies available."})
        if BookIssue.objects.filter(borrower_id=d["borrower"], status="issued").count() >= d["limit"]:
            raise ValidationError({"detail": "Borrower has reached the issue limit."})
        issue = BookIssue.objects.create(book=book, borrower_id=d["borrower"], issued_by=request.user,
                                         **({"due_date": d["due_date"]} if d.get("due_date") else {}))
        Book.objects.filter(pk=book.pk).update(available_copies=F("available_copies") - 1)
        BookReservation.objects.filter(book=book, user_id=d["borrower"], status="waiting").update(status="fulfilled")
        notify(issue.borrower, f"Book issued: {book.title}", f"Return by {issue.due_date:%d %b %Y}", "/library", "library")
        audit(request, "issue", issue, "book-issues")
        return Response({"detail": f"Issued. Due {issue.due_date:%d %b %Y}.", "issue_id": issue.id})

    @action(detail=True, methods=["post"])
    def reserve(self, request, pk=None):
        BookReservation.objects.get_or_create(book=self.get_object(), user=request.user, status="waiting")
        return Response({"detail": "Reserved. You will be notified when available."})


class BookIssueViewSet(BaseModelViewSet):
    queryset = BookIssue.objects.all()
    serializer_class = s.BookIssueSerializer
    resource_key = "book-issues"
    read_roles = write_roles = LIBRARY
    scope = by_user("borrower")
    search_fields = ["book__title", "borrower__first_name", "borrower__username"]
    filterset_fields = ["status", "borrower", "book", "fine_paid", "due_date"]
    label, group, icon, menu_roles = "Issued Books", G, "swap", ALL
    list_fields = ["book", "borrower", "issued_on", "due_date", "returned_on", "status", "fine", "fine_paid"]
    ui_actions = [
        {"name": "return_book", "label": "Return", "style": "success", "roles": LIBRARY,
         "input": [{"name": "lost", "type": "boolean", "label": "Mark as lost"},
                   {"name": "remarks", "type": "string", "label": "Remarks"}]},
        {"name": "renew", "label": "Renew 14 days", "roles": LIBRARY},
        {"name": "pay_fine", "label": "Fine paid", "roles": LIBRARY},
    ]

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def return_book(self, request, pk=None):
        issue = self.get_object()
        if issue.status != BookIssue.Status.ISSUED:
            raise ValidationError({"detail": "Already returned."})
        ser = s.ReturnBookSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        from website.models import SiteSettings
        today = timezone.localdate()
        late = max((today - issue.due_date).days, 0)
        issue.fine = Decimal(late) * SiteSettings.get().library_fine_per_day
        issue.status = BookIssue.Status.LOST if ser.validated_data["lost"] else BookIssue.Status.RETURNED
        issue.returned_on = today
        issue.remarks = ser.validated_data["remarks"] or issue.remarks
        issue.save()
        if issue.status == BookIssue.Status.RETURNED:
            Book.objects.filter(pk=issue.book_id).update(available_copies=F("available_copies") + 1)
            nxt = BookReservation.objects.filter(book=issue.book, status="waiting").order_by("created_at").first()
            if nxt:
                notify(nxt.user, f"Reserved book available: {issue.book.title}", "Collect it from the library.", "/library")
        audit(request, "return", issue, "book-issues", {"fine": issue.fine})
        return Response({"detail": f"Returned {late} day(s) late, fine {issue.fine}." if late else "Returned on time.",
                         "fine": issue.fine})

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        issue = self.get_object()
        if issue.status != BookIssue.Status.ISSUED:
            raise ValidationError({"detail": "Not issued."})
        if BookReservation.objects.filter(book=issue.book, status="waiting").exclude(user=issue.borrower).exists():
            raise ValidationError({"detail": "Book is reserved by someone else."})
        issue.due_date = max(issue.due_date, timezone.localdate()) + timedelta(days=14)
        issue.save(update_fields=["due_date"])
        return Response({"detail": f"Renewed until {issue.due_date:%d %b %Y}."})

    @action(detail=True, methods=["post"])
    def pay_fine(self, request, pk=None):
        issue = self.get_object()
        issue.fine_paid = True
        issue.save(update_fields=["fine_paid"])
        return Response({"detail": "Fine marked as paid."})


class BookReservationViewSet(BaseModelViewSet):
    queryset = BookReservation.objects.all()
    serializer_class = s.BookReservationSerializer
    resource_key = "book-reservations"
    read_roles = write_roles = LIBRARY
    create_roles = ALL
    scope = own("user")
    owner_field, owner_edit = "user", True
    label, group, icon = "Reservations", G, "bookmark"
    list_fields = ["book", "user", "status", "created_at"]


class OverdueBooksView(APIView):
    def get(self, request):
        if not has_role(request.user, LIBRARY):
            raise PermissionDenied()
        today = timezone.localdate()
        qs = BookIssue.objects.filter(status="issued", due_date__lt=today).select_related("book", "borrower")
        return Response([{"id": i.id, "book": i.book.title, "borrower": i.borrower.display_name, "phone": i.borrower.phone,
                          "due_date": i.due_date, "days_late": (today - i.due_date).days} for i in qs])

    def post(self, request):
        """Send reminders to all overdue borrowers."""
        if not has_role(request.user, LIBRARY):
            raise PermissionDenied()
        qs = BookIssue.objects.filter(status="issued", due_date__lt=timezone.localdate()).select_related("book", "borrower")
        for i in qs:
            notify(i.borrower, f"Overdue book: {i.book.title}", f"Was due {i.due_date:%d %b %Y}. Please return it.",
                   "/library", "library")
        return Response({"detail": f"{qs.count()} reminder(s) sent."})
