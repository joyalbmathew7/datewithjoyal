from django.urls import path
from .views import available_slots,create_booking

urlpatterns = [
    path("availability/", available_slots, name="available-slots"),
    path("bookings/", create_booking, name="create-booking"),
]
