from django.contrib import admin

from .models import (Book, BookCategory, BookIssue, BookReservation)


@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_arabic', 'author', 'publisher', 'isbn', 'category')
    search_fields = ('title', 'title_arabic', 'author')
    list_filter = ('language', 'is_reference_only')
    list_select_related = ('category',)


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'issued_on', 'due_date', 'returned_on', 'status')
    search_fields = ('remarks',)
    list_filter = ('status', 'fine_paid')
    list_select_related = ('book', 'borrower', 'issued_by')


@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'status')
    list_filter = ('status',)
    list_select_related = ('book', 'user')
