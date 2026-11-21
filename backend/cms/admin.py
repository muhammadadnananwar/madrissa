from django.contrib import admin

from . import models as m

for model in (m.WebsiteSettings, m.Department, m.Program, m.Faculty, m.News, m.Announcement, m.CalendarItem, m.GalleryItem,
              m.Document, m.MeritList, m.MeritListEntry, m.Testimonial, m.Faq, m.Page):
    admin.site.register(model)
