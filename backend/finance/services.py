"""Business logic for fees, payroll and financial reporting."""
import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from academics.models import AcademicYear, Holiday
from communication.services import notify
from people.models import Employee, Student

from .models import (ZERO, Budget, Donation, Expense, ExpenseCategory, FeeHead, FeeStructure, Fund, Invoice, InvoiceItem,
                     OtherIncome, Payment, Payslip, SalaryAdvance)


def site_settings():
    from website.models import SiteSettings
    return SiteSettings.get()


def month_start(value):
    y, m = map(int, (value or timezone.localdate().strftime("%Y-%m")).split("-")[:2])
    return date(y, m, 1)


def family_users(student):
    return [student.user] + [g.user for g in (student.guardian, student.second_guardian) if g and g.user_id]


# ------------------------------------------------------------------ invoices
@transaction.atomic
def generate_invoices(*, period, due_date, frequencies, title=None, section=None, class_level=None, department=None,
                      student_ids=None, created_by=None):
    """Create one invoice per active student from fee structures, transport fares and concessions."""
    year = AcademicYear.current()
    students = Student.objects.filter(status="active").select_related("section__class_level", "department", "user",
                                                                      "guardian__user", "second_guardian__user")
    if section:
        students = students.filter(section_id=section)
    if class_level:
        students = students.filter(section__class_level_id=class_level)
    if department:
        students = students.filter(department_id=department)
    if student_ids:
        students = students.filter(id__in=student_ids)
    structures = list(FeeStructure.objects.filter(academic_year=year, frequency__in=frequencies).select_related("fee_head"))
    title = title or f"Fee for {period:%B %Y}"
    from transport.models import TransportAssignment
    created = skipped = 0
    for st in students:
        if Invoice.objects.filter(student=st, period=period, title=title).exclude(status="cancelled").exists():
            skipped += 1
            continue
        dept_id = st.department_id or (st.section.class_level.department_id if st.section else None)
        cl_id = st.section.class_level_id if st.section else None
        lines = [(fs.fee_head, f"{fs.fee_head.name} ({fs.get_frequency_display()})", fs.amount) for fs in structures
                 if (not fs.department_id or fs.department_id == dept_id)
                 and (not fs.class_level_id or fs.class_level_id == cl_id)
                 and (not fs.boarders_only or st.is_boarder)]
        if "monthly" in frequencies:
            for ta in TransportAssignment.objects.filter(user=st.user, is_active=True).select_related("route"):
                if ta.route.monthly_fare:
                    head, _ = FeeHead.objects.get_or_create(name="Transport", defaults={"kind": "transport"})
                    lines.append((head, f"Transport — {ta.route.name}", ta.route.monthly_fare))
        if not lines:
            skipped += 1
            continue
        concessions = [c for c in st.concessions.filter(is_active=True, valid_from__lte=period)
                       if not c.valid_to or c.valid_to >= period]
        discount = sum((c.discount_for(h.id, amt) for h, _, amt in lines for c in concessions), ZERO)
        inv = Invoice.objects.create(student=st, title=title, period=period, due_date=due_date, discount=discount,
                                     created_by=created_by,
                                     notes=", ".join(str(c.get_reason_display()) for c in concessions)[:255])
        for head, desc, amt in lines:
            InvoiceItem.objects.create(invoice=inv, fee_head=head, description=desc, amount=amt)
        inv.recalc()
        if inv.total == 0:
            inv.status = Invoice.Status.WAIVED
            inv.save(update_fields=["status"])
        created += 1
        notify(family_users(st), f"New fee invoice: {title}", f"Amount {inv.total}, due {due_date:%d %b %Y}", "/fees", "fee")
    return created, skipped


def invoice_dict(inv):
    return {"id": inv.id, "invoice_no": inv.invoice_no, "title": inv.title, "issue_date": inv.issue_date,
            "due_date": inv.due_date, "subtotal": inv.subtotal, "discount": inv.discount, "fine": inv.fine,
            "total": inv.total, "paid": inv.paid_amount, "balance": inv.balance, "status": inv.status,
            "status_display": inv.get_status_display(), "notes": inv.notes,
            "overdue": inv.status in ("unpaid", "partial") and inv.due_date < timezone.localdate(),
            "student": {"id": inv.student_id, "name": inv.student.user.display_name, "admission_no": inv.student.admission_no,
                        "father_name": inv.student.user.father_name,
                        "section": str(inv.student.section) if inv.student.section else ""},
            "items": [{"description": i.description, "amount": i.amount} for i in inv.items.all()],
            "payments": [{"id": p.id, "receipt_no": p.receipt_no, "amount": p.amount, "date": p.date,
                          "method": p.get_method_display(), "status": p.status, "status_display": p.get_status_display(),
                          "reference": p.reference} for p in inv.payments.all()]}


def notify_payment(payment):
    notify(family_users(payment.invoice.student), f"Payment received: {payment.amount}",
           f"Receipt {payment.receipt_no} for {payment.invoice.title}", "/fees", "fee")


# ----------------------------------------------------------------- reporting
def financial_summary(d_from, d_to):
    today = timezone.localdate()
    pay = Payment.objects.filter(status="verified", date__range=(d_from, d_to))
    don = Donation.objects.filter(status="received", date__range=(d_from, d_to))
    exp = Expense.objects.filter(status="approved", date__range=(d_from, d_to))
    oth = OtherIncome.objects.filter(date__range=(d_from, d_to))
    total = lambda qs: qs.aggregate(s=Sum("amount"))["s"] or ZERO  # noqa: E731
    fees, donations, other, expenses = total(pay), total(don), total(oth), total(exp)

    funds = []  # all-time restricted fund balances (zakat must never be mixed with general funds)
    for value, label in Fund.choices:
        income = total(Donation.objects.filter(status="received", fund=value)) + total(OtherIncome.objects.filter(fund=value))
        if value == Fund.GENERAL:
            income += total(Payment.objects.filter(status="verified"))
        spent = total(Expense.objects.filter(status="approved", fund=value))
        if income or spent:
            funds.append({"fund": value, "label": label, "income": income, "spent": spent, "balance": income - spent})

    start12 = (today.replace(day=1) - timedelta(days=330)).replace(day=1)

    def series(qs):
        return {r["m"].strftime("%Y-%m"): r["s"] for r in qs.filter(date__gte=start12).annotate(m=TruncMonth("date"))
                .values("m").annotate(s=Sum("amount"))}

    s_fee = series(Payment.objects.filter(status="verified"))
    s_don = series(Donation.objects.filter(status="received"))
    s_exp = series(Expense.objects.filter(status="approved"))
    months, m = [], start12
    while m <= today:
        k = m.strftime("%Y-%m")
        months.append({"month": k, "fees": s_fee.get(k, 0), "donations": s_don.get(k, 0), "expenses": s_exp.get(k, 0)})
        m = (m + timedelta(days=32)).replace(day=1)

    outstanding = Invoice.objects.filter(status__in=["unpaid", "partial"]).aggregate(t=Sum("total"), p=Sum("paid_amount"))
    budget = []
    year = AcademicYear.current()
    if year:
        for b in Budget.objects.filter(academic_year=year).select_related("category"):
            spent = total(Expense.objects.filter(status="approved", category=b.category,
                                                 date__range=(year.start_date, year.end_date)))
            budget.append({"category": b.category.name, "budget": b.amount, "spent": spent, "remaining": b.amount - spent})
    return {
        "from": d_from, "to": d_to,
        "totals": {"fees": fees, "donations": donations, "other_income": other, "income": fees + donations + other,
                   "expenses": expenses, "net": fees + donations + other - expenses,
                   "outstanding": (outstanding["t"] or ZERO) - (outstanding["p"] or ZERO)},
        "donations_by_fund": list(don.values("fund").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")),
        "expenses_by_category": list(exp.values("category__name").annotate(total=Sum("amount")).order_by("-total")),
        "expenses_by_fund": list(exp.values("fund").annotate(total=Sum("amount")).order_by("-total")),
        "collection_by_method": list(pay.values("method").annotate(total=Sum("amount")).order_by("-total")),
        "funds": funds, "monthly": months, "budget": budget,
        "pending_verifications": Payment.objects.filter(status="pending").count(),
        "pending_expenses": Expense.objects.filter(status="pending").count(),
    }


# -------------------------------------------------------------------- payroll
def working_days(month):
    days = calendar.monthrange(month.year, month.month)[1]
    last = month.replace(day=days)
    weekdays = site_settings().working_weekdays()
    holidays = set()
    for h in Holiday.objects.filter(start_date__lte=last, end_date__gte=month):
        d = max(h.start_date, month)
        while d <= min(h.end_date, last):
            holidays.add(d)
            d += timedelta(days=1)
    return [month.replace(day=i) for i in range(1, days + 1)
            if month.replace(day=i).weekday() in weekdays and month.replace(day=i) not in holidays]


@transaction.atomic
def generate_payroll(month, deduct_absence=True):
    """Draft payslips: basic + allowances − deductions − absences/unpaid leave − advance installments."""
    from attendance.models import StaffAttendance
    from leaves.models import LeaveRequest
    last = month.replace(day=calendar.monthrange(month.year, month.month)[1])
    wdays = working_days(month)
    created = updated = skipped = 0
    for emp in Employee.objects.filter(status__in=["active", "on_leave"]).select_related("user"):
        existing = Payslip.objects.filter(employee=emp, month=month).first()
        if existing and existing.status != Payslip.Status.DRAFT:
            skipped += 1
            continue
        comps = list(emp.salary_components.filter(is_active=True))
        allowances = sum((c.amount for c in comps if c.kind == "allowance"), ZERO)
        deductions = sum((c.amount for c in comps if c.kind == "deduction"), ZERO)
        att = StaffAttendance.objects.filter(employee=emp, date__range=(month, last))
        absent = att.filter(status="absent").count()
        half = att.filter(status="half_day").count()
        present = att.filter(status__in=["present", "late"]).count()
        unpaid = Decimal(0)
        for leave in LeaveRequest.objects.filter(user=emp.user, status="approved", leave_type__is_paid=False,
                                                 start_date__lte=last, end_date__gte=month):
            d = max(leave.start_date, month)
            while d <= min(leave.end_date, last):
                if d in wdays:
                    unpaid += Decimal("0.5") if leave.half_day else 1
                d += timedelta(days=1)
        per_day = (emp.basic_salary / len(wdays)).quantize(Decimal("0.01")) if wdays else ZERO
        absence_days = Decimal(absent) + Decimal(half) / 2 + unpaid
        absence_ded = ZERO
        if deduct_absence and emp.employment_type != "volunteer":
            absence_ded = (per_day * absence_days).quantize(Decimal("0.01"))
        advance_total, advances = ZERO, {}
        for a in emp.advances.filter(status="approved"):
            amt = min(a.monthly_installment, a.remaining)
            if amt > 0:
                advances[str(a.id)] = str(amt)
                advance_total += amt
        values = dict(basic=emp.basic_salary, allowances=allowances, deductions=deductions, absence_deduction=absence_ded,
                      advance_deduction=advance_total, working_days=len(wdays), present_days=present,
                      unpaid_leave_days=unpaid,
                      breakdown={"components": [{"kind": c.kind, "title": c.title, "amount": str(c.amount)} for c in comps],
                                 "absent_days": absent, "half_days": half, "per_day": str(per_day), "advances": advances})
        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            existing.save()
            updated += 1
        else:
            Payslip.objects.create(employee=emp, month=month, **values)
            created += 1
    return {"created": created, "updated": updated, "skipped": skipped, "working_days": len(wdays)}


@transaction.atomic
def pay_payslip(payslip, *, paid_on, method, by):
    """Mark paid, recover advances and book the salary as an expense."""
    payslip.status = Payslip.Status.PAID
    payslip.paid_on = paid_on
    payslip.method = method or payslip.method
    payslip.save()
    for adv_id, amt in (payslip.breakdown.get("advances") or {}).items():
        adv = SalaryAdvance.objects.filter(pk=adv_id).first()
        if adv:
            adv.recovered += Decimal(str(amt))
            if adv.recovered >= adv.amount:
                adv.status = SalaryAdvance.Status.CLEARED
            adv.save()
    cat, _ = ExpenseCategory.objects.get_or_create(name="Salaries")
    Expense.objects.create(category=cat, title=f"Salary {payslip.month:%B %Y} — {payslip.employee.user.display_name}",
                           amount=payslip.net, date=paid_on, paid_to=payslip.employee.user.display_name,
                           method=payslip.method, status=Expense.Status.APPROVED, created_by=by, approved_by=by,
                           reference=f"Payslip #{payslip.id}")
    notify(payslip.employee.user, f"Salary paid for {payslip.month:%B %Y}", f"Net {payslip.net}", "/payslips", "salary")
