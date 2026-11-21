from django.contrib import admin

from .models import (Budget, Concession, Donation, Donor, Expense, ExpenseCategory, FeeHead, FeeStructure, Invoice,
                     InvoiceItem, OtherIncome, Payment, Payslip, SalaryAdvance, SalaryComponent)


@admin.register(FeeHead)
class FeeHeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'description')
    search_fields = ('name', 'description')
    list_filter = ('kind',)


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'department', 'class_level', 'fee_head', 'amount')
    search_fields = ('name',)
    list_filter = ('frequency', 'boarders_only')
    list_select_related = ('academic_year', 'department', 'class_level', 'fee_head')


@admin.register(Concession)
class ConcessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_head', 'kind', 'value', 'reason', 'funded_from')
    search_fields = ('notes',)
    list_filter = ('kind', 'reason', 'funded_from', 'is_active')
    list_select_related = ('student', 'fee_head')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'student', 'title', 'period', 'issue_date', 'due_date')
    search_fields = ('invoice_no', 'title', 'notes')
    list_filter = ('status',)
    list_select_related = ('student', 'created_by')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'fee_head', 'description', 'amount')
    search_fields = ('description',)
    list_select_related = ('invoice', 'fee_head')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'invoice', 'amount', 'date', 'method', 'reference')
    search_fields = ('receipt_no', 'reference', 'notes')
    list_filter = ('method', 'status')
    list_select_related = ('invoice', 'submitted_by', 'received_by')


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'city', 'is_recurring')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('is_recurring',)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'donor', 'donor_name', 'phone', 'email', 'fund')
    search_fields = ('receipt_no', 'donor_name', 'phone')
    list_filter = ('fund', 'method', 'is_anonymous', 'status')
    list_select_related = ('donor', 'sponsored_student', 'received_by')


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'category', 'fund', 'title', 'amount', 'date')
    search_fields = ('voucher_no', 'title', 'paid_to')
    list_filter = ('fund', 'method', 'status')
    list_select_related = ('category', 'created_by', 'approved_by')


@admin.register(OtherIncome)
class OtherIncomeAdmin(admin.ModelAdmin):
    list_display = ('title', 'fund', 'amount', 'date', 'method', 'reference')
    search_fields = ('title', 'reference')
    list_filter = ('fund', 'method')
    list_select_related = ('received_by',)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'category', 'amount', 'notes')
    search_fields = ('notes',)
    list_select_related = ('academic_year', 'category')


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'kind', 'title', 'amount', 'is_active')
    search_fields = ('title',)
    list_filter = ('kind', 'is_active')
    list_select_related = ('employee',)


@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'monthly_installment', 'recovered', 'date', 'reason')
    search_fields = ('reason',)
    list_filter = ('status',)
    list_select_related = ('employee',)


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'basic', 'allowances', 'deductions', 'absence_deduction')
    search_fields = ('notes',)
    list_filter = ('status', 'method')
    list_select_related = ('employee',)
