import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from academics.models import AcademicYear, ClassLevel, Department
from core.models import TimeStamped
from people.models import Employee, Student

User = settings.AUTH_USER_MODEL
ZERO = Decimal("0")


def _no(prefix):
    return f"{prefix}-{timezone.now():%y%m}-{secrets.token_hex(3).upper()}"


def invoice_no():
    return _no("INV")


def receipt_no():
    return _no("RCP")


def donation_no():
    return _no("DON")


def voucher_no():
    return _no("EXP")


class Fund(models.TextChoices):
    """Islamic finance requires restricted funds to be tracked separately."""

    GENERAL = "general", "General fund"
    ZAKAT = "zakat", "Zakat fund"
    SADAQAH = "sadaqah", "Sadaqah fund"
    LILLAH = "lillah", "Lillah / Atiyyat"
    WAQF = "waqf", "Waqf / endowment"
    FITRAH = "fitrah", "Sadaqat-ul-Fitr"
    CONSTRUCTION = "construction", "Construction fund"
    QURBANI = "qurbani", "Qurbani"


class Method(models.TextChoices):
    CASH = "cash", "Cash"
    BANK = "bank", "Bank transfer"
    CHEQUE = "cheque", "Cheque"
    JAZZCASH = "jazzcash", "JazzCash"
    EASYPAISA = "easypaisa", "Easypaisa"
    CARD = "card", "Card / online"
    OTHER = "other", "Other"


class FeeHead(TimeStamped):
    class Kind(models.TextChoices):
        ADMISSION = "admission", "Admission"
        TUITION = "tuition", "Tuition"
        EXAM = "exam", "Examination"
        HOSTEL = "hostel", "Hostel"
        MESS = "mess", "Mess / Food"
        TRANSPORT = "transport", "Transport"
        LIBRARY = "library", "Library"
        BOOKS = "books", "Books & stationery"
        UNIFORM = "uniform", "Uniform"
        FINE = "fine", "Fine"
        OTHER = "other", "Other"

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.TUITION)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class FeeStructure(TimeStamped):
    class Frequency(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        ONCE = "once", "One time"
        ANNUAL = "annual", "Annual"
        TERM = "term", "Per term"

    name = models.CharField(max_length=150)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.CASCADE)
    class_level = models.ForeignKey(ClassLevel, null=True, blank=True, on_delete=models.CASCADE,
                                    help_text="Leave empty to apply to the whole department")
    fee_head = models.ForeignKey(FeeHead, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.MONTHLY)
    boarders_only = models.BooleanField(default=False, help_text="Only charge hostel boarders")

    class Meta:
        ordering = ["academic_year", "name"]

    def __str__(self):
        return f"{self.name}: {self.fee_head} {self.amount} ({self.get_frequency_display()})"


class Concession(TimeStamped):
    """Scholarships / fee waivers (orphans, zakat-eligible, merit, siblings, staff children...)."""

    class Kind(models.TextChoices):
        PERCENT = "percent", "Percentage"
        FIXED = "fixed", "Fixed amount"

    class Reason(models.TextChoices):
        ORPHAN = "orphan", "Yateem (orphan)"
        NEEDY = "needy", "Needy / Zakat eligible"
        MERIT = "merit", "Merit"
        SIBLING = "sibling", "Sibling"
        STAFF_CHILD = "staff_child", "Staff child"
        HAFIZ = "hafiz", "Hafiz incentive"
        SPONSORED = "sponsored", "Sponsored by donor"
        OTHER = "other", "Other"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="concessions")
    fee_head = models.ForeignKey(FeeHead, null=True, blank=True, on_delete=models.CASCADE, help_text="Empty = all heads")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.PERCENT)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=15, choices=Reason.choices, default=Reason.NEEDY)
    funded_from = models.CharField(max_length=15, choices=Fund.choices, default=Fund.GENERAL,
                                   help_text="Fund that bears the waived amount")
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        unit = "%" if self.kind == self.Kind.PERCENT else ""
        return f"{self.student}: {self.value}{unit} ({self.get_reason_display()})"

    def discount_for(self, head_id, amount):
        if self.fee_head_id and self.fee_head_id != head_id:
            return ZERO
        if self.kind == self.Kind.PERCENT:
            return (amount * self.value / 100).quantize(Decimal("0.01"))
        return min(self.value, amount)


class Invoice(TimeStamped):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partially paid"
        PAID = "paid", "Paid"
        WAIVED = "waived", "Waived"
        CANCELLED = "cancelled", "Cancelled"

    invoice_no = models.CharField(max_length=30, unique=True, default=invoice_no, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    title = models.CharField(max_length=150, help_text="e.g. Fee for November 2026")
    period = models.DateField(null=True, blank=True, help_text="Billing month (first day)")
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fine = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID, db_index=True)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-issue_date", "-id"]

    def __str__(self):
        return f"{self.invoice_no} — {self.student} ({self.total})"

    @property
    def balance(self):
        return self.total - self.paid_amount

    def recalc(self, save=True):
        self.subtotal = self.items.aggregate(s=Sum("amount"))["s"] or ZERO if self.pk else ZERO
        self.total = max(self.subtotal - self.discount + self.fine, ZERO)
        self.paid_amount = (self.payments.filter(status=Payment.Status.VERIFIED).aggregate(s=Sum("amount"))["s"] or ZERO) if self.pk else ZERO
        if self.status not in (self.Status.CANCELLED, self.Status.WAIVED):
            if self.total and self.paid_amount >= self.total:
                self.status = self.Status.PAID
            elif self.paid_amount > 0:
                self.status = self.Status.PARTIAL
            else:
                self.status = self.Status.UNPAID
        if save:
            super().save(update_fields=["subtotal", "total", "paid_amount", "status", "updated_at"])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recalc()


class InvoiceItem(TimeStamped):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    fee_head = models.ForeignKey(FeeHead, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.description}: {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.recalc()

    def delete(self, *args, **kwargs):
        inv = self.invoice
        super().delete(*args, **kwargs)
        inv.recalc()


class Payment(TimeStamped):
    class Status(models.TextChoices):
        VERIFIED = "verified", "Verified / received"
        PENDING = "pending", "Pending verification"
        REJECTED = "rejected", "Rejected"

    receipt_no = models.CharField(max_length=30, unique=True, default=receipt_no, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=100, blank=True, help_text="Transaction ID / cheque no")
    proof = models.FileField(upload_to="finance/proofs/", null=True, blank=True, help_text="Screenshot of bank / mobile transfer")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.VERIFIED)
    notes = models.CharField(max_length=255, blank=True)
    submitted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    received_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.receipt_no}: {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.recalc()

    def delete(self, *args, **kwargs):
        inv = self.invoice
        super().delete(*args, **kwargs)
        inv.recalc()


class Donor(TimeStamped):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    is_recurring = models.BooleanField(default=False, help_text="Monthly sponsor / donor")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Donation(TimeStamped):
    class Status(models.TextChoices):
        PLEDGED = "pledged", "Pledged (online form)"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    receipt_no = models.CharField(max_length=30, unique=True, default=donation_no, editable=False)
    donor = models.ForeignKey(Donor, null=True, blank=True, on_delete=models.SET_NULL, related_name="donations")
    donor_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    fund = models.CharField(max_length=15, choices=Fund.choices, default=Fund.GENERAL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=100, blank=True)
    sponsored_student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL,
                                          help_text="Kafalah: donation sponsoring a specific student")
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RECEIVED)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.receipt_no} {self.get_fund_display()} {self.amount}"


class ExpenseCategory(TimeStamped):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "expense categories"

    def __str__(self):
        return self.name


class Expense(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved / paid"
        REJECTED = "rejected", "Rejected"

    voucher_no = models.CharField(max_length=30, unique=True, default=voucher_no, editable=False)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    fund = models.CharField(max_length=15, choices=Fund.choices, default=Fund.GENERAL,
                            help_text="Fund this expense is paid from (Zakat must go to eligible heads)")
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    paid_to = models.CharField(max_length=150, blank=True)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=100, blank=True)
    attachment = models.FileField(upload_to="finance/expenses/", null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.APPROVED)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.voucher_no}: {self.title} {self.amount}"


class OtherIncome(TimeStamped):
    title = models.CharField(max_length=200, help_text="e.g. Rent, sale of produce, government grant")
    fund = models.CharField(max_length=15, choices=Fund.choices, default=Fund.GENERAL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "other income"

    def __str__(self):
        return f"{self.title}: {self.amount}"


class Budget(TimeStamped):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("academic_year", "category")

    def __str__(self):
        return f"{self.academic_year} {self.category}: {self.amount}"


# ---------------------------------------------------------------- Payroll ---
class SalaryComponent(TimeStamped):
    """Recurring allowance / deduction for an employee (house rent, conveyance, EOBI...)."""

    class Kind(models.TextChoices):
        ALLOWANCE = "allowance", "Allowance"
        DEDUCTION = "deduction", "Deduction"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="salary_components")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee}: {self.title} {self.amount}"


class SalaryAdvance(TimeStamped):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved (recovering)"
        REJECTED = "rejected", "Rejected"
        CLEARED = "cleared", "Fully recovered"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="advances")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2)
    recovered = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    date = models.DateField(default=timezone.localdate)
    reason = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)

    class Meta:
        verbose_name = "salary advance / qarz-e-hasana"

    def __str__(self):
        return f"{self.employee}: {self.amount}"

    @property
    def remaining(self):
        return self.amount - self.recovered


class Payslip(TimeStamped):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        PAID = "paid", "Paid"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payslips")
    month = models.DateField(help_text="First day of the salary month")
    basic = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    absence_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    working_days = models.PositiveSmallIntegerField(default=0)
    present_days = models.PositiveSmallIntegerField(default=0)
    unpaid_leave_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    breakdown = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    paid_on = models.DateField(null=True, blank=True)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.BANK)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-month", "employee"]
        unique_together = ("employee", "month")

    def __str__(self):
        return f"{self.employee} — {self.month:%B %Y}"

    def save(self, *args, **kwargs):
        self.net = (self.basic + self.allowances + self.bonus
                    - self.deductions - self.absence_deduction - self.advance_deduction)
        super().save(*args, **kwargs)
