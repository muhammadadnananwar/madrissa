from rest_framework import serializers

from core.serializers import LabeledModelSerializer
from finance.models import Donation, Fund, Method

from .models import (FAQ, BoardMember, ContactMessage, Download, FatwaQuestion, GalleryAlbum, GalleryImage, NewsPost, Page,
                     Program, SiteSettings, Slide, Stat, Subscriber, Testimonial)


class SiteSettingsSerializer(LabeledModelSerializer):
    class Meta:
        model = SiteSettings
        fields = "__all__"


class PageSerializer(LabeledModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"


class SlideSerializer(LabeledModelSerializer):
    class Meta:
        model = Slide
        fields = "__all__"


class ProgramSerializer(LabeledModelSerializer):
    class Meta:
        model = Program
        fields = "__all__"


class NewsPostSerializer(LabeledModelSerializer):
    class Meta:
        model = NewsPost
        fields = "__all__"


class GalleryAlbumSerializer(LabeledModelSerializer):
    class Meta:
        model = GalleryAlbum
        fields = "__all__"


class GalleryImageSerializer(LabeledModelSerializer):
    class Meta:
        model = GalleryImage
        fields = "__all__"


class TestimonialSerializer(LabeledModelSerializer):
    class Meta:
        model = Testimonial
        fields = "__all__"


class FAQSerializer(LabeledModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"


class BoardMemberSerializer(LabeledModelSerializer):
    class Meta:
        model = BoardMember
        fields = "__all__"


class StatSerializer(LabeledModelSerializer):
    class Meta:
        model = Stat
        fields = "__all__"


class DownloadSerializer(LabeledModelSerializer):
    class Meta:
        model = Download
        fields = "__all__"


class ContactMessageSerializer(LabeledModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"


class SubscriberSerializer(LabeledModelSerializer):
    class Meta:
        model = Subscriber
        fields = "__all__"


class FatwaQuestionSerializer(LabeledModelSerializer):
    class Meta:
        model = FatwaQuestion
        fields = "__all__"


class FatwaAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(required=False, allow_blank=True, default="")


# ---- public (anonymous) form serializers -----------------------------------------
class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()


class FatwaAskSerializer(serializers.ModelSerializer):
    class Meta:
        model = FatwaQuestion
        fields = ["name", "email", "phone", "city", "category", "title", "question"]


class DonationPledgeSerializer(serializers.ModelSerializer):
    method = serializers.ChoiceField(choices=Method.choices, default=Method.BANK)
    fund = serializers.ChoiceField(choices=Fund.choices, default=Fund.GENERAL)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)

    class Meta:
        model = Donation
        fields = ["donor_name", "phone", "email", "fund", "amount", "method", "reference", "notes", "is_anonymous"]
        extra_kwargs = {"donor_name": {"required": True, "allow_blank": False}, "phone": {"required": True, "allow_blank": False}}
