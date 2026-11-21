from rest_framework import serializers

AUTO_USER_FIELDS = {
    "created_by", "recorded_by", "marked_by", "entered_by", "received_by",
    "issued_by", "uploaded_by", "author", "applied_by", "sender", "submitted_by",
}


class LabeledModelSerializer(serializers.ModelSerializer):
    """
    Base serializer used by every app.

    * timestamps and "who did it" fields (created_by, marked_by ...) are read-only
      and filled in by the viewset,
    * every FK gets a ``<name>_label`` and every choice field a ``<name>_display``
      so the portal can render tables without extra requests.
    """

    def get_fields(self):
        fields = super().get_fields()
        for name in ("created_at", "updated_at", *AUTO_USER_FIELDS):
            if name in fields:
                fields[name].read_only = True
        view = self.context.get("view")
        owner = getattr(view, "owner_field", None)
        if owner and owner in fields:
            fields[owner].required = False
        return fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for f in instance._meta.concrete_fields:
            if f.is_relation:
                rel = getattr(instance, f.name, None) if getattr(instance, f.attname, None) else None
                data[f"{f.name}_label"] = str(rel) if rel is not None else None
            elif f.choices:
                data[f"{f.name}_display"] = getattr(instance, f"get_{f.name}_display")()
        for f in instance._meta.many_to_many:
            if f.name in data:
                data[f"{f.name}_labels"] = [str(o) for o in getattr(instance, f.name).all()]
        return data
