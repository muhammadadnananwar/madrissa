from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("fee-heads", views.FeeHeadViewSet)
router.register("fee-structures", views.FeeStructureViewSet)
router.register("concessions", views.ConcessionViewSet)
router.register("invoices", views.InvoiceViewSet)
router.register("invoice-items", views.InvoiceItemViewSet)
router.register("payments", views.PaymentViewSet)
router.register("donors", views.DonorViewSet)
router.register("donations", views.DonationViewSet)
router.register("expense-categories", views.ExpenseCategoryViewSet)
router.register("expenses", views.ExpenseViewSet)
router.register("other-income", views.OtherIncomeViewSet)
router.register("budgets", views.BudgetViewSet)
router.register("salary-components", views.SalaryComponentViewSet)
router.register("salary-advances", views.SalaryAdvanceViewSet)
router.register("payslips", views.PayslipViewSet)

urlpatterns = [
    path("finance/generate-invoices/", views.GenerateInvoicesView.as_view()),
    path("finance/apply-late-fees/", views.ApplyLateFeesView.as_view()),
    path("finance/invoices/<int:pk>/detail/", views.InvoiceDetailView.as_view()),
    path("finance/payments/<int:pk>/receipt/", views.ReceiptView.as_view()),
    path("finance/my-fees/", views.MyFeesView.as_view()),
    path("finance/defaulters/", views.DefaultersView.as_view()),
    path("finance/defaulters/remind/", views.RemindDefaultersView.as_view()),
    path("finance/summary/", views.FinancialSummaryView.as_view()),
    path("finance/payroll/generate/", views.GeneratePayrollView.as_view()),
    path("finance/payslips/<int:pk>/print/", views.PayslipPrintView.as_view()),
    path("finance/donations/<int:pk>/receipt/", views.DonationReceiptView.as_view()),
    *router.urls,
]
