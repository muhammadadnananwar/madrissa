from core.serializers import LabeledModelSerializer

from . import models as m


def _ser(model_cls):
    meta = type("Meta", (), {"model": model_cls, "fields": "__all__"})
    return type(f"{model_cls.__name__}Serializer", (LabeledModelSerializer,), {"Meta": meta})


WebsiteSettingsSerializer = _ser(m.WebsiteSettings)
DepartmentSerializer = _ser(m.Department)
ProgramSerializer = _ser(m.Program)
FacultySerializer = _ser(m.Faculty)
NewsSerializer = _ser(m.News)
AnnouncementSerializer = _ser(m.Announcement)
CalendarItemSerializer = _ser(m.CalendarItem)
GalleryItemSerializer = _ser(m.GalleryItem)
DocumentSerializer = _ser(m.Document)
MeritListSerializer = _ser(m.MeritList)
MeritListEntrySerializer = _ser(m.MeritListEntry)
TestimonialSerializer = _ser(m.Testimonial)
FaqSerializer = _ser(m.Faq)
PageSerializer = _ser(m.Page)
