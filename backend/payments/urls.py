from django.urls import path
from .views import create_order, verify_payment, download_booking_pdf

urlpatterns = [
    path("create-order/", create_order, name="create-order"),
    path("verify-payment/", verify_payment, name="verify-payment"),
    path(
        "booking-pdf/<int:booking_id>/",
        download_booking_pdf,
        name="download-booking-pdf",
    ),
]