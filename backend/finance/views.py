from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from communication.services import notify
from core.audit import audit
from core.roles import ADMINS, FINANCE, R, STAFF_ROLES, has_role, is_admin
from core.scopes import by_student, visible_student_ids
from core.viewsets import BaseModelViewSet

from . import serializers as s
from . import services
from .models import (ZERO, Budget, Concession, Donation, Donor, Expense, ExpenseCategory, FeeHead, FeeStructure, Invoice,
                     InvoiceItem, Method, OtherIncome, Payment, Payslip, SalaryAdvance, SalaryComponent)

G = "Finance & Accounts"
P = "HR & Payroll"
PAYROLL = FINANCE + [R.HR_MANAGER]
METHOD_CHOICES = [{"value": v, "label": l} for v, l in Method.choices]


class FinanceBase(BaseModelViewSet):
    read_roles = write_roles = FINANCE
    group = G


class FeeHeadViewSet(FinanceBase):
    queryset = FeeHead.objects.all()
    serializer_class = s.FeeHeadSerializer
    resource_key = "fee-heads"
    icon = "tag"
    list_fields = ["name", "kind", "description"]


class FeeStructureViewSet(FinanceBase):
    queryset = FeeStructure.objects.all()
    serializer_class = s.FeeStructureSerializer
    resource_key = "fee-structures"
    read_roles = FINANCE + [R.ADMISSION_OFFICER]
    icon = "layers"
    list_fields = ["name", "academic_year", "department", "class_level", "fee_head", "amount", "frequency", "boarders_only"]


class ConcessionViewSet(FinanceBase):
    queryset = Concession.objects.all()
    serializer_class = s.ConcessionSerializer
    resource_key = "concessions"
    read_roles = FINANCE + [R.ADMISSION_OFFICER]
    scope = by_student()
    search_fields = ["student__admission_no", "student__user__first_name"]
    label, icon = "Scholarships & Concessions", "gift"
    list_fields = ["student", "reason", "kind", "value", "fee_head", "funded_from", "is_active"]


class InvoiceViewSet(FinanceBase):
    queryset = Invoice.objects.all()
    serializer_class = s.InvoiceSerializer
    resource_key = "invoices"
    scope = by_student()
    search_fields = ["invoice_no", "student__admission_no", "student__user__first_name", "title"]
    filterset_fields = ["status", "student", "period", "student__section", "due_date"]
    label, icon, menu_roles = "Fee Invoices", "receipt", FINANCE
    list_fields = ["invoice_no", "student", "title", "due_date", "total", "paid_amount", "status"]
    ui_actions = [
        {"name": "collect", "label": "Collect payment", "style": "success", "roles": FINANCE,
         "input": [{"name": "amount", "type": "decimal", "label": "Amount (empty = full balance)"},
                   {"name": "method", "type": "choice", "label": "Method", "choices": METHOD_CHOICES},
                   {"name": "reference", "type": "string", "label": "Reference"}]},
        {"name": "waive", "label": "Waive", "roles": ADMINS, "input": [{"name": "reason", "type": "string", "label": "Reason"}]},
        {"name": "cancel", "label": "Cancel", "style": "danger", "roles": FINANCE, "confirm": "Cancel this invoice?"},
    ]

    @action(detail=True, methods=["post"])
    def collect(self, request, pk=None):
        inv = self.get_object()
        ser = s.CollectPaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        amount = d.get("amount") or inv.balance
        if amount <= 0:
            raise ValidationError({"amount": "Nothing to collect."})
        if amount > inv.balance:
            raise ValidationError({"amount": f"Amount exceeds balance ({inv.balance})."})
        p = Payment.objects.create(invoice=inv, amount=amount, method=d["method"], reference=d["reference"],
                                   date=d.get("date") or timezone.localdate(), notes=d["notes"],
                                   received_by=request.user, submitted_by=request.user, status=Payment.Status.VERIFIED)
        audit(request, "collect", inv, "invoices", {"amount": amount, "receipt": p.receipt_no})
        services.notify_payment(p)
        return Response({"detail": f"Received {amount}. Receipt {p.receipt_no}.", "payment_id": p.id, "receipt_no": p.receipt_no})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        inv = self.get_object()
        inv.status = Invoice.Status.CANCELLED
        inv.save(update_fields=["status", "updated_at"])
        audit(request, "cancel", inv, "invoices")
        return Response({"detail": "Invoice cancelled."})

    @action(detail=True, methods=["post"])
    def waive(self, request, pk=None):
        inv = self.get_object()
        ser = s.ReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        inv.status = Invoice.Status.WAIVED
        inv.notes = f"{inv.notes} | Waived: {ser.validated_data['reason']}".strip(" |")[:255]
        inv.save(update_fields=["status", "notes", "updated_at"])
        audit(request, "waive", inv, "invoices")
        return Response({"detail": "Invoice waived."})


class InvoiceItemViewSet(FinanceBase):
    queryset = InvoiceItem.objects.all()
    serializer_class = s.InvoiceItemSerializer
    resource_key = "invoice-items"
    scope = staticmethod(lambda qs, u: qs.filter(invoice__student_id__in=visible_student_ids(u)))
    icon, menu = "list", False
    list_fields = ["invoice", "fee_head", "description", "amount"]


class PaymentViewSet(FinanceBase):
    """Accountants record payments; parents/students upload transfer proofs (pending verification)."""

    queryset = Payment.objects.all()
    serializer_class = s.PaymentSerializer
    resource_key = "payments"
    create_roles = [R.PARENT, R.STUDENT]
    scope = staticmethod(lambda qs, u: qs.filter(invoice__student_id__in=visible_student_ids(u)))
    search_fields = ["receipt_no", "reference", "invoice__invoice_no"]
    filterset_fields = ["status", "method", "date", "invoice", "invoice__student"]
    label, icon, menu_roles = "Fee Payments", "cash", FINANCE
    list_fields = ["receipt_no", "invoice", "amount", "date", "method", "status", "received_by"]
    ui_actions = [
        {"name": "verify", "label": "Verify", "style": "success", "roles": FINANCE, "confirm": "Mark this payment as received?"},
        {"name": "reject", "label": "Reject", "style": "danger", "roles": FINANCE,
         "input": [{"name": "reason", "type": "string", "label": "Reason"}]},
    ]

    def validate_create(self, serializer, extra):
        user = self.request.user
        vd = serializer.validated_data
        if not has_role(user, FINANCE):
            if vd["invoice"].student_id not in visible_student_ids(user):
                raise PermissionDenied("Not your invoice.")
            if not vd.get("proof") and not vd.get("reference"):
                raise ValidationError({"proof": "Attach the transfer screenshot or enter the transaction ID."})
            extra["status"] = Payment.Status.PENDING
            extra["received_by"] = None

    def after_save(self, obj, created):
        if not created:
            return
        if obj.status == Payment.Status.PENDING:
            notify(list(User.objects.filter(role=R.ACCOUNTANT, is_active=True)), "Payment proof submitted",
                   f"{obj.invoice.student} — {obj.amount} via {obj.get_method_display()}", "/m/payments", "fee")
        elif obj.status == Payment.Status.VERIFIED:
            services.notify_payment(obj)

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        p = self.get_object()
        p.status, p.received_by = Payment.Status.VERIFIED, request.user
        p.save()
        audit(request, "verify", p, "payments")
        services.notify_payment(p)
        return Response({"detail": "Payment verified."})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        p = self.get_object()
        ser = s.ReasonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        p.status = Payment.Status.REJECTED
        p.notes = ser.validated_data["reason"] or p.notes
        p.save()
        notify(services.family_users(p.invoice.student), "Payment proof rejected",
               p.notes or "Please contact the accounts office.", "/fees", "fee")
        return Response({"detail": "Payment rejected."})


class DonorViewSet(FinanceBase):
    queryset = Donor.objects.all()
    serializer_class = s.DonorSerializer
    resource_key = "donors"
    search_fields = ["name", "phone", "email"]
    icon = "heart"
    list_fields = ["name", "phone", "city", "is_recurring"]


class DonationViewSet(FinanceBase):
    queryset = Donation.objects.all()
    serializer_class = s.DonationSerializer
    resource_key = "donations"
    search_fields = ["receipt_no", "donor_name", "phone", "reference"]
    filterset_fields = ["fund", "status", "method", "date", "donor", "sponsored_student"]
    label, icon = "Donations (Zakat, Sadaqah...)", "hand"
    list_fields = ["receipt_no", "date", "donor_name", "donor", "fund", "amount", "method", "status"]
    ui_actions = [{"name": "mark_received", "label": "Mark received", "style": "success", "roles": FINANCE,
                   "confirm": "Confirm this pledge was received?"}]

    @action(detail=True, methods=["post"])
    def mark_received(self, request, pk=None):
        d = self.get_object()
        d.status, d.received_by = Donation.Status.RECEIVED, request.user
        d.save()
        audit(request, "received", d, "donations")
        return Response({"detail": "Donation marked as received."})


class ExpenseCategoryViewSet(FinanceBase):
    queryset = ExpenseCategory.objects.all()
    serializer_class = s.ExpenseCategorySerializer
    resource_key = "expense-categories"
    icon = "folder"
    list_fields = ["name", "description"]


class ExpenseViewSet(FinanceBase):
    """Expenses entered by accountants need approval by management."""

    queryset = Expense.objects.all()
    serializer_class = s.ExpenseSerializer
    resource_key = "expenses"
    search_fields = ["voucher_no", "title", "paid_to"]
    filterset_fields = ["category", "fund", "status", "date", "method"]
    icon = "wallet"
    list_fields = ["voucher_no", "date", "category", "title", "fund", "amount", "status"]
    ui_actions = [{"name": "approve", "label": "Approve", "style": "success", "roles": ADMINS},
                  {"name": "reject", "label": "Reject", "style": "danger", "roles": ADMINS}]

    def validate_create(self, serializer, extra):
        if is_admin(self.request.user):
            extra["status"], extra["approved_by"] = Expense.Status.APPROVED, self.request.user
        else:
            extra["status"] = Expense.Status.PENDING

    def _set(self, request, status):
        e = self.get_object()
        e.status, e.approved_by = status, request.user
        e.save()
        audit(request, status, e, "expenses")
        return Response({"detail": f"Expense {e.get_status_display().lower()}."})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._set(request, Expense.Status.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set(request, Expense.Status.REJECTED)


class OtherIncomeViewSet(FinanceBase):
    queryset = OtherIncome.objects.all()
    serializer_class = s.OtherIncomeSerializer
    resource_key = "other-income"
    label, icon = "Other Income", "plus"
    list_fields = ["date", "title", "fund", "amount", "method"]


class BudgetViewSet(FinanceBase):
    queryset = Budget.objects.all()
    serializer_class = s.BudgetSerializer
    resource_key = "budgets"
    write_roles = ADMINS
    icon = "pie"
    list_fields = ["academic_year", "category", "amount"]


# ----------------------------------------------------------------- payroll
def own_employee(qs, user):
    return qs.filter(employee__user=user)


class SalaryComponentViewSet(BaseModelViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = s.SalaryComponentSerializer
    resource_key = "salary-components"
    read_roles = write_roles = PAYROLL
    filterset_fields = ["employee", "kind", "is_active"]
    label, group, icon = "Allowances & Deductions", P, "sliders"
    list_fields = ["employee", "kind", "title", "calculation", "amount", "is_active"]


class SalaryAdvanceViewSet(BaseModelViewSet):
    queryset = SalaryAdvance.objects.all()
    serializer_class = s.SalaryAdvanceSerializer
    resource_key = "salary-advances"
    read_roles = write_roles = PAYROLL
    create_roles = STAFF_ROLES
    scope = staticmethod(own_employee)
    label, group, icon, menu_roles = "Advances / Qarz-e-Hasana", P, "cash", STAFF_ROLES
    list_fields = ["employee", "amount", "monthly_installment", "recovered", "date", "status"]
    ui_actions = [{"name": "approve", "label": "Approve", "style": "success", "roles": PAYROLL},
                  {"name": "reject", "label": "Reject", "style": "danger", "roles": PAYROLL}]

    def validate_create(self, serializer, extra):
        user = self.request.user
        if not has_role(user, PAYROLL) or not serializer.validated_data.get("employee"):
            emp = getattr(user, "employee_profile", None)
            if not emp:
                raise ValidationError({"detail": "No employee profile."})
            extra["employee"] = emp
        if serializer.validated_data["monthly_installment"] > serializer.validated_data["amount"]:
            raise ValidationError({"monthly_installment": "Installment cannot exceed the amount."})

    def _set(self, request, status):
        a = self.get_object()
        a.status = status
        a.save()
        notify(a.employee.user, f"Salary advance {a.get_status_display().lower()}",
               f"{a.amount}, installment {a.monthly_installment}/month")
        return Response({"detail": f"Advance {a.get_status_display().lower()}."})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._set(request, SalaryAdvance.Status.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set(request, SalaryAdvance.Status.REJECTED)


class PayslipViewSet(BaseModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = s.PayslipSerializer
    resource_key = "payslips"
    read_roles = write_roles = PAYROLL
    scope = staticmethod(own_employee)
    filterset_fields = ["employee", "month", "status"]
    group, icon, menu_roles = P, "file", STAFF_ROLES
    list_fields = ["employee", "month", "basic", "allowances", "deductions", "absence_deduction", "penalty_deduction", "net", "status", "paid_on"]
    ui_actions = [{"name": "approve", "label": "Approve", "roles": PAYROLL},
                  {"name": "mark_paid", "label": "Mark paid", "style": "success", "roles": FINANCE,
                   "confirm": "Record salary as paid?"}]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        p = self.get_object()
        if p.status != Payslip.Status.DRAFT:
            return Response({"detail": "Only drafts can be approved."}, status=400)
        p.status = Payslip.Status.APPROVED
        p.save()
        return Response({"detail": "Payslip approved."})

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        p = self.get_object()
        if p.status == Payslip.Status.PAID:
            return Response({"detail": "Already paid."}, status=400)
        ser = s.MarkPaidSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.pay_payslip(p, paid_on=ser.validated_data.get("paid_on") or timezone.localdate(),
                             method=ser.validated_data.get("method"), by=request.user)
        audit(request, "mark_paid", p, "payslips")
        return Response({"detail": "Marked as paid and recorded as expense."})


# ------------------------------------------------------------------ APIViews
class FinanceAPIView(APIView):
    roles = FINANCE

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not has_role(request.user, self.roles):
            raise PermissionDenied()


class GenerateInvoicesView(FinanceAPIView):
    def post(self, request):
        ser = s.GenerateInvoicesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        period = services.month_start(d["period"])
        created, skipped = services.generate_invoices(
            period=period, due_date=d.get("due_date") or period + timedelta(days=9), frequencies=d["frequencies"],
            title=d.get("title"), section=d.get("section"), class_level=d.get("class_level"),
            department=d.get("department"), student_ids=d.get("student_ids"), created_by=request.user)
        audit(request, "generate_invoices", Invoice(), "invoices", {"period": period, "created": created})
        return Response({"detail": f"{created} invoice(s) generated, {skipped} skipped.", "created": created, "skipped": skipped})


class ApplyLateFeesView(FinanceAPIView):
    def post(self, request):
        ser = s.LateFeeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fee = ser.validated_data.get("amount") or services.site_settings().late_fee_per_invoice
        if not fee:
            raise ValidationError({"amount": "Set a late fee amount (or configure it in Institution Settings)."})
        n = 0
        for inv in Invoice.objects.filter(status__in=["unpaid", "partial"], due_date__lt=timezone.localdate(), fine=0):
            inv.fine = fee
            inv.save()
            n += 1
        return Response({"detail": f"Late fee applied to {n} invoice(s)."})


class InvoiceDetailView(APIView):
    def get(self, request, pk):
        inv = get_object_or_404(Invoice.objects.select_related("student__user", "student__section"), pk=pk)
        if not (has_role(request.user, FINANCE) or inv.student_id in visible_student_ids(request.user)):
            raise PermissionDenied()
        site = services.site_settings()
        return Response({**services.invoice_dict(inv),
                         "institution": {"name": site.name, "address": site.address, "phone": site.phone,
                                         "currency": site.currency, "bank": site.donation_bank_details}})


class ReceiptView(APIView):
    def get(self, request, pk):
        p = get_object_or_404(Payment.objects.select_related("invoice__student__user", "received_by"), pk=pk)
        if not (has_role(request.user, FINANCE) or p.invoice.student_id in visible_student_ids(request.user)):
            raise PermissionDenied()
        site = services.site_settings()
        return Response({"receipt_no": p.receipt_no, "amount": p.amount, "date": p.date, "method": p.get_method_display(),
                         "reference": p.reference, "status": p.get_status_display(),
                         "received_by": p.received_by.display_name if p.received_by else "",
                         "invoice": services.invoice_dict(p.invoice),
                         "institution": {"name": site.name, "address": site.address, "phone": site.phone,
                                         "currency": site.currency}})


class MyFeesView(APIView):
    def get(self, request):
        user = request.user
        ids = visible_student_ids(user)
        if request.query_params.get("student"):
            sid = int(request.query_params["student"])
            if sid not in ids and not has_role(user, FINANCE):
                raise PermissionDenied()
            ids = {sid}
        invs = Invoice.objects.filter(student_id__in=ids).exclude(status="cancelled") \
            .select_related("student__user", "student__section").prefetch_related("items", "payments")
        data = [services.invoice_dict(i) for i in invs[:60]]
        site = services.site_settings()
        return Response({"invoices": data, "currency": site.currency, "bank_details": site.donation_bank_details,
                         "outstanding": sum((i["balance"] for i in data if i["status"] in ("unpaid", "partial")), ZERO),
                         "methods": METHOD_CHOICES})


class DefaultersView(FinanceAPIView):
    roles = FINANCE + [R.ACADEMIC_COORDINATOR]

    def get(self, request):
        qs = Invoice.objects.filter(status__in=["unpaid", "partial"], due_date__lt=timezone.localdate())
        if request.query_params.get("section"):
            qs = qs.filter(student__section_id=request.query_params["section"])
        rows = {}
        for inv in qs.select_related("student__user", "student__section", "student__guardian"):
            st = inv.student
            r = rows.setdefault(st.id, {"student": st.id, "name": st.user.display_name, "admission_no": st.admission_no,
                                        "section": str(st.section) if st.section else "",
                                        "guardian_phone": st.guardian.phone if st.guardian else "",
                                        "invoices": 0, "balance": ZERO, "oldest_due": inv.due_date})
            r["invoices"] += 1
            r["balance"] += inv.balance
            r["oldest_due"] = min(r["oldest_due"], inv.due_date)
        out = sorted(rows.values(), key=lambda r: -r["balance"])
        return Response({"rows": out, "total": sum((r["balance"] for r in out), ZERO)})


class RemindDefaultersView(FinanceAPIView):
    def post(self, request):
        qs = Invoice.objects.filter(status__in=["unpaid", "partial"], due_date__lt=timezone.localdate()) \
            .select_related("student__user", "student__guardian__user", "student__second_guardian__user")
        for inv in qs:
            notify(services.family_users(inv.student), f"Fee reminder: {inv.title}",
                   f"Balance {inv.balance} was due on {inv.due_date:%d %b %Y}.", "/fees", "fee")
        return Response({"detail": f"Reminders sent for {qs.count()} invoice(s)."})


class FinancialSummaryView(FinanceAPIView):
    def get(self, request):
        today = timezone.localdate()
        parse = lambda v, d: datetime.strptime(v, "%Y-%m-%d").date() if v else d  # noqa: E731
        return Response(services.financial_summary(parse(request.query_params.get("from"), today.replace(day=1)),
                                                   parse(request.query_params.get("to"), today)))


class GeneratePayrollView(FinanceAPIView):
    roles = PAYROLL

    def post(self, request):
        ser = s.PayrollSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        month = services.month_start(ser.validated_data["month"])
        r = services.generate_payroll(month, ser.validated_data["deduct_absence"])
        audit(request, "generate_payroll", Payslip(), "payslips", {"month": month, **r})
        return Response({"detail": f"Payroll {month:%B %Y}: {r['created']} created, {r['updated']} updated, "
                                   f"{r['skipped']} locked.", **r})


class PayslipPrintView(APIView):
    def get(self, request, pk):
        p = get_object_or_404(Payslip.objects.select_related("employee__user", "employee__department"), pk=pk)
        if not (has_role(request.user, PAYROLL) or p.employee.user_id == request.user.id):
            raise PermissionDenied()
        site = services.site_settings()
        e = p.employee
        return Response({"id": p.id, "month": p.month, "status": p.get_status_display(), "paid_on": p.paid_on,
                         "method": p.get_method_display(), "basic": p.basic, "allowances": p.allowances,
                         "deductions": p.deductions, "absence_deduction": p.absence_deduction,
                         "advance_deduction": p.advance_deduction, "penalty_deduction": p.penalty_deduction,
                         "bonus": p.bonus, "net": p.net,
                         "working_days": p.working_days, "present_days": p.present_days,
                         "unpaid_leave_days": p.unpaid_leave_days, "breakdown": p.breakdown,
                         "employee": {"name": e.user.display_name, "employee_no": e.employee_no, "designation": e.designation,
                                      "department": str(e.department) if e.department else "",
                                      "bank": f"{e.bank_name} {e.bank_account}".strip(), "cnic": e.user.cnic},
                         "institution": {"name": site.name, "address": site.address, "currency": site.currency}})


class DonationReceiptView(FinanceAPIView):
    def get(self, request, pk):
        d = get_object_or_404(Donation.objects.select_related("donor", "received_by"), pk=pk)
        site = services.site_settings()
        return Response({"receipt_no": d.receipt_no, "date": d.date, "donor": d.donor.name if d.donor else d.donor_name,
                         "phone": d.phone, "fund": d.get_fund_display(), "amount": d.amount, "method": d.get_method_display(),
                         "reference": d.reference, "notes": d.notes, "status": d.get_status_display(),
                         "received_by": d.received_by.display_name if d.received_by else "",
                         "institution": {"name": site.name, "address": site.address, "phone": site.phone,
                                         "currency": site.currency}})
