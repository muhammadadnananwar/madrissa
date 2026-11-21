import secrets

from django.db import transaction
from rest_framework import serializers

from accounts.models import User
from core.roles import R
from core.serializers import LabeledModelSerializer

from .models import (AdmissionDocument, Achievement, AdmissionApplication, DisciplinaryRecord, Employee, EmploymentHistory, Guardian,
                     MedicalRecord, PersonDocument, Qualification, Student, StudentPromotion, VisitorLog)

USER_FIELDS = ["first_name", "last_name", "username", "password", "email", "phone", "whatsapp", "gender",
               "date_of_birth", "cnic", "father_name", "name_arabic", "address", "city"]


class PersonSerializerMixin:
    """A Student / Employee profile created and edited together with its User account."""

    default_role = R.STUDENT
    username_prefix = "std"

    def get_fields(self):
        fields = super().get_fields()
        for name in USER_FIELDS + ["role"]:
            if name not in fields:
                fields[name] = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
        fields["user"].required = False
        return fields

    allowed_roles = None  # roles this serializer may assign; None = only default_role

    def _clean_role(self, role):
        if not role:
            return None
        allowed = self.allowed_roles or [self.default_role]
        req = self.context.get("request")
        is_super = req and (req.user.is_superuser or req.user.role == R.SUPER_ADMIN)
        if role not in allowed or (role in (R.SUPER_ADMIN,) and not is_super):
            raise serializers.ValidationError({"role": "This role cannot be assigned here."})
        return role

    def _split(self, validated):
        udata = {k: validated.pop(k) for k in list(validated) if k in USER_FIELDS + ["role"]}
        if "role" in udata:
            udata["role"] = self._clean_role(udata["role"])
        return {k: (v or None) if k == "date_of_birth" else (v if v is not None else "") for k, v in udata.items()}

    @transaction.atomic
    def create(self, validated):
        udata = self._split(validated)
        password = udata.pop("password", "") or ""
        if not validated.get("user"):
            if not udata.get("first_name"):
                raise serializers.ValidationError({"first_name": "First name is required."})
            username = udata.pop("username", "") or f"{self.username_prefix}{secrets.token_hex(3)}"
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({"username": "Username already taken."})
            udata["role"] = udata.get("role") or self.default_role
            user = User(username=username, **udata)
            password = password or secrets.token_urlsafe(6)
            user.set_password(password)
            user.must_change_password = True
            user.save()
            validated["user"] = user
            self._generated_password = password
        return super().create(validated)

    @transaction.atomic
    def update(self, instance, validated):
        udata = self._split(validated)
        password = udata.pop("password", "")
        username = udata.pop("username", "")
        user = instance.user
        for k, v in udata.items():
            if k == "role" and not v:
                continue
            setattr(user, k, v)
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                raise serializers.ValidationError({"username": "Username already taken."})
            user.username = username
        if password:
            user.set_password(password)
        user.save()
        return super().update(instance, validated)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        u = instance.user
        for f in USER_FIELDS:
            if f != "password":
                v = getattr(u, f)
                data[f] = v.isoformat() if hasattr(v, "isoformat") else v
        data["full_name"] = u.display_name
        data["role"] = u.role
        req = self.context.get("request")
        data["photo"] = req.build_absolute_uri(u.photo.url) if u.photo and req else None
        if getattr(self, "_generated_password", None):
            data["generated_password"] = self._generated_password
        return data


class StudentSerializer(PersonSerializerMixin, LabeledModelSerializer):
    default_role = R.STUDENT
    username_prefix = "std"

    class Meta:
        model = Student
        fields = "__all__"


class EmployeeSerializer(PersonSerializerMixin, LabeledModelSerializer):
    default_role = R.TEACHER
    username_prefix = "emp"
    allowed_roles = [r for r in R.values if r not in (R.STUDENT, R.PARENT)]

    class Meta:
        model = Employee
        fields = "__all__"


class GuardianSerializer(LabeledModelSerializer):
    """Optionally creates a parent-portal login for the guardian."""

    create_login = serializers.BooleanField(write_only=True, required=False)
    login_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    login_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Guardian
        fields = "__all__"

    def _maybe_login(self, obj, data):
        if data.get("create_login") and not obj.user_id:
            username = data.get("login_username") or f"par{secrets.token_hex(3)}"
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({"login_username": "Username already taken."})
            pwd = data.get("login_password") or secrets.token_urlsafe(6)
            first, _, last = obj.name.partition(" ")
            u = User(username=username, role=R.PARENT, first_name=first, last_name=last, phone=obj.phone, email=obj.email,
                     cnic=obj.cnic, address=obj.address, must_change_password=True)
            u.set_password(pwd)
            u.save()
            obj.user = u
            obj.save(update_fields=["user"])
            self._generated = {"username": username, "password": pwd}
        return obj

    def _pop(self, validated):
        return {k: validated.pop(k, None) for k in ("create_login", "login_username", "login_password")}

    def create(self, validated):
        data = self._pop(validated)
        return self._maybe_login(super().create(validated), data)

    def update(self, instance, validated):
        data = self._pop(validated)
        return self._maybe_login(super().update(instance, validated), data)

    def to_representation(self, instance):
        d = super().to_representation(instance)
        if getattr(self, "_generated", None):
            d["generated_login"] = self._generated
        d["children"] = [str(x) for x in instance.students.all()]
        return d


class QualificationSerializer(LabeledModelSerializer):
    class Meta:
        model = Qualification
        fields = "__all__"


class EmploymentHistorySerializer(LabeledModelSerializer):
    class Meta:
        model = EmploymentHistory
        fields = "__all__"


class PersonDocumentSerializer(LabeledModelSerializer):
    class Meta:
        model = PersonDocument
        fields = "__all__"


class DisciplinaryRecordSerializer(LabeledModelSerializer):
    class Meta:
        model = DisciplinaryRecord
        fields = "__all__"


class MedicalRecordSerializer(LabeledModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = "__all__"


class AchievementSerializer(LabeledModelSerializer):
    class Meta:
        model = Achievement
        fields = "__all__"


class StudentPromotionSerializer(LabeledModelSerializer):
    class Meta:
        model = StudentPromotion
        fields = "__all__"


class AdmissionApplicationSerializer(LabeledModelSerializer):
    class Meta:
        model = AdmissionApplication
        fields = "__all__"


class AdmissionDocumentSerializer(LabeledModelSerializer):
    class Meta:
        model = AdmissionDocument
        fields = "__all__"


class AdmissionPublicSerializer(serializers.ModelSerializer):
    """Used by the public website's online admission form."""

    class Meta:
        model = AdmissionApplication
        exclude = ["status", "test_date", "test_score", "remarks", "enrolled_student", "source", "aggregate"]


class VisitorLogSerializer(LabeledModelSerializer):
    class Meta:
        model = VisitorLog
        fields = "__all__"


class PromoteSerializer(serializers.Serializer):
    student_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    to_section = serializers.IntegerField(required=False, allow_null=True)
    result = serializers.ChoiceField(choices=StudentPromotion.Result.choices, default="promoted")
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
