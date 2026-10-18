from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Availability, Booking
from .serializers import (
    AvailabilitySerializer,
    BookingCreateSerializer,
)

import os
def active_bookings_for(availability):
    """Return confirmed bookings and pending bookings with active holds."""
    now = timezone.now()
    return Booking.objects.filter(
        availability=availability,
    ).filter(
        Q(status=Booking.Status.CONFIRMED)
        | Q(
            status=Booking.Status.PENDING,
            hold_expires_at__gt=now,
        )
    )


@api_view(["GET"])
def available_slots(request):
    today = timezone.localdate()
    now = timezone.localtime()
    slots = Availability.objects.filter(
        is_available=True, date__gt=today
    ).prefetch_related("districts").order_by("date", "start_time")

    visible_slots = []

    for slot in slots:
        if slot.date == today and slot.end_time <= now.time():
            continue

        # Keep the availability visible even if part of its window is booked.
        # The booking API will reject overlapping times.
        visible_slots.append(slot)

    return Response(
        AvailabilitySerializer(visible_slots, many=True).data
    )


@api_view(["POST"])
def create_booking(request):
    serializer = BookingCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    availability_id = serializer.validated_data["availability"].id

    # These values are calculated/validated by BookingCreateSerializer.
    requested_start = serializer.validated_data["start_time"]
    requested_end = serializer.validated_data["end_time"]

    with transaction.atomic():
        availability = Availability.objects.select_for_update().get(
            id=availability_id
        )

        if not availability.is_available:
            return Response(
                {"error": "This time slot is not available."},
                status=status.HTTP_409_CONFLICT,
            )

        # Check whether an existing active booking overlaps the requested time.
        conflict = active_bookings_for(availability).filter(
            start_time__lt=requested_end,
            end_time__gt=requested_start,
        ).exists()

        if conflict:
            return Response(
                {"error": "Already someone booked, sorry change the time or date"},
                status=status.HTTP_409_CONFLICT,
            )

        # Ensure the requested time still fits inside the availability window.
        window_start = (
            availability.start_time.hour * 60
            + availability.start_time.minute
        )
        window_end = (
            availability.end_time.hour * 60
            + availability.end_time.minute
        )
        requested_start_minutes = (
            requested_start.hour * 60 + requested_start.minute
        )
        requested_end_minutes = (
            requested_end.hour * 60 + requested_end.minute
        )

        if (
            requested_start_minutes < window_start
            or requested_end_minutes > window_end
        ):
            return Response(
                {"error": "The selected time is outside the available window."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = serializer.save(
            availability=availability,
            hold_expires_at=timezone.now() + timedelta(minutes=10),
        )

    return Response(
        {
            "id": booking.id,
            "status": booking.status,
            "booked_hours": booking.booked_hours,
            "hourly_rate": str(booking.hourly_rate),
            "total_amount": str(booking.total_amount),
            "hold_expires_at": booking.hold_expires_at,
        },
        status=status.HTTP_201_CREATED,
    )