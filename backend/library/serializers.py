from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import Book, BookCategory, BookIssue, BookReservation


class BookCategorySerializer(LabeledModelSerializer):
    class Meta:
        model = BookCategory
        fields = "__all__"


class BookSerializer(LabeledModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"
        extra_kwargs = {"available_copies": {"required": False}}

    def validate(self, attrs):
        total = attrs.get("total_copies", getattr(self.instance, "total_copies", 1))
        if "available_copies" not in attrs and not self.instance:
            attrs["available_copies"] = total
        if attrs.get("available_copies", 0) > total:
            raise serializers.ValidationError({"available_copies": "Cannot exceed total copies."})
        return attrs


class BookIssueSerializer(LabeledModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = BookIssue
        fields = "__all__"
        read_only_fields = ["status", "fine"]


class BookReservationSerializer(LabeledModelSerializer):
    class Meta:
        model = BookReservation
        fields = "__all__"


class IssueBookSerializer(serializers.Serializer):
    borrower = serializers.IntegerField()
    due_date = serializers.DateField(required=False, allow_null=True)
    limit = serializers.IntegerField(required=False, default=5, min_value=1)


class ReturnBookSerializer(serializers.Serializer):
    lost = serializers.BooleanField(default=False)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
