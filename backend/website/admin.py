from django.contrib import admin

from .models import (BoardMember, ContactMessage, Download, FAQ, FatwaQuestion, GalleryAlbum, GalleryImage, NewsPost,
                     Page, Program, SiteSettings, Slide, Stat, Subscriber, Testimonial)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_arabic', 'tagline', 'logo', 'founded_year', 'affiliation')
    search_fields = ('name', 'name_arabic', 'tagline')
    list_filter = ('admissions_open', 'notify_guardian_on_absence')


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'subtitle', 'image', 'order', 'show_in_menu')
    search_fields = ('title', 'subtitle')
    list_filter = ('show_in_menu', 'is_published')


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'image', 'cta_text', 'cta_link', 'order')
    search_fields = ('title', 'subtitle', 'cta_text')
    list_filter = ('is_active',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'title_arabic', 'department', 'summary', 'duration')
    search_fields = ('title', 'title_arabic', 'summary')
    list_filter = ('is_published',)
    list_select_related = ('department',)


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'summary', 'image', 'category', 'published_at')
    search_fields = ('title', 'summary', 'category')
    list_filter = ('is_published',)
    list_select_related = ('author',)


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'cover', 'date', 'is_published')
    search_fields = ('title', 'description')
    list_filter = ('is_published',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('album', 'image', 'caption', 'order')
    search_fields = ('caption',)
    list_select_related = ('album',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'photo', 'is_published')
    search_fields = ('name', 'role')
    list_filter = ('is_published',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order')
    search_fields = ('question', 'category')


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'photo', 'is_founder', 'order')
    search_fields = ('name', 'title')
    list_filter = ('is_founder',)


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ('label', 'value', 'icon', 'order')
    search_fields = ('label', 'value', 'icon')


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ('title', 'file', 'category', 'is_published')
    search_fields = ('title', 'category')
    list_filter = ('is_published',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_resolved')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('is_resolved',)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active')
    search_fields = ('email',)
    list_filter = ('is_active',)


@admin.register(FatwaQuestion)
class FatwaQuestionAdmin(admin.ModelAdmin):
    list_display = ('fatwa_no', 'name', 'email', 'phone', 'city', 'category')
    search_fields = ('fatwa_no', 'name', 'email')
    list_filter = ('status', 'is_public')
    list_select_related = ('assigned_to',)
