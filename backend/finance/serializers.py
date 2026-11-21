from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import (Budget, Concession, Donation, Donor, Expense, ExpenseCategory, FeeHead, FeeStructure, Fund, Invoice,
                     InvoiceItem, Method, OtherIncome, Payment, Payslip, SalaryAdvance, SalaryComponent)


class FeeHeadSerializer(LabeledModelSerializer):
    class Meta:
        model = FeeHead
        fields = "__all__"


class FeeStructureSerializer(LabeledModelSerializer):
    class Meta:
        model = FeeStructure
        fields = "__all__"


class ConcessionSerializer(LabeledModelSerializer):
    class Meta:
        model = Concession
        fields = "__all__"

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        value = attrs.get("value", getattr(self.instance, "value", 0))
        if kind == Concession.Kind.PERCENT and not 0 < value <= 100:
            raise serializers.ValidationError({"value": "Percentage must be between 0 and 100."})
        return attrs


class InvoiceSerializer(LabeledModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["status"]


class InvoiceItemSerializer(LabeledModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class PaymentSerializer(LabeledModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value


class DonorSerializer(LabeledModelSerializer):
    class Meta:
        model = Donor
        fields = "__all__"


class DonationSerializer(LabeledModelSerializer):
    class Meta:
        model = Donation
        fields = "__all__"


class ExpenseCategorySerializer(LabeledModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = "__all__"


class ExpenseSerializer(LabeledModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"
        read_only_fields = ["status"]


class OtherIncomeSerializer(LabeledModelSerializer):
    class Meta:
        model = OtherIncome
        fields = "__all__"


class BudgetSerializer(LabeledModelSerializer):
    class Meta:
        model = Budget
        fields = "__all__"


class SalaryComponentSerializer(LabeledModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = "__all__"


class SalaryAdvanceSerializer(LabeledModelSerializer):
    remaining = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SalaryAdvance
        fields = "__all__"
        read_only_fields = ["status"]
        extra_kwargs = {"employee": {"required": False}}


class PayslipSerializer(LabeledModelSerializer):
    class Meta:
        model = Payslip
        fields = "__all__"
        read_only_fields = ["status", "paid_on"]


# ---- action payloads ---------------------------------------------------------------
class CollectPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=0)
    method = serializers.ChoiceField(choices=Method.choices, default=Method.CASH)
    reference = serializers.CharField(required=False, allow_blank=True, default="")
    date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class GenerateInvoicesSerializer(serializers.Serializer):
    period = serializers.RegexField(r"^\d{4}-\d{2}$", help_text="YYYY-MM")
    due_date = serializers.DateField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True)
    frequencies = serializers.ListField(child=serializers.ChoiceField(choices=FeeStructure.Frequency.choices),
                                        default=["monthly"])
    section = serializers.IntegerField(required=False, allow_null=True)
    class_level = serializers.IntegerField(required=False, allow_null=True)
    department = serializers.IntegerField(required=False, allow_null=True)
    student_ids = serializers.ListField(child=serializers.IntegerField(), required=False)


class LateFeeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, min_value=0)


class PayrollSerializer(serializers.Serializer):
    month = serializers.RegexField(r"^\d{4}-\d{2}$")
    deduct_absence = serializers.BooleanField(default=True)


class MarkPaidSerializer(serializers.Serializer):
    paid_on = serializers.DateField(required=False, allow_null=True)
    method = serializers.ChoiceField(choices=Method.choices, required=False)


FUND_CHOICES = Fund.choices
