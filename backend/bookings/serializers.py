
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from website.models import Activity, OutfitItem, SiteSettings
from .models import (
    Availability,
    Booking,
    BookingOutfitSelection,
    District,
)


class AvailabilitySerializer(serializers.ModelSerializer):
    districts = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    booked_periods = serializers.SerializerMethodField()

    class Meta:
        model = Availability
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "districts",
            "booked_periods",
        ]

    def get_booked_periods(self, availability):
        from django.db.models import Q

        now = timezone.now()

        bookings = Booking.objects.filter(
            availability=availability,
            start_time__isnull=False,
            end_time__isnull=False,
        ).filter(
            Q(status=Booking.Status.CONFIRMED)
            | Q(
                status=Booking.Status.PENDING,
                hold_expires_at__gt=now,
            )
        ).values("start_time", "end_time")

        return [
            {
                "start_time": booking["start_time"].strftime("%H:%M"),
                "end_time": booking["end_time"].strftime("%H:%M"),
            }
            for booking in bookings
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField()

    booked_hours = serializers.IntegerField(
        min_value=4,
        max_value=8,
    )

    activity_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Activity.objects.filter(is_available=True),
        source="activities",
        write_only=True,
        required=False,
    )

    outfit_item_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=OutfitItem.objects.filter(is_available=True),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Booking
        fields = [
            "customer_name",
            "customer_phone",
            "customer_age",
            "district",
            "availability",
            "start_time",
            "booked_hours",
            "activity_ids",
            "outfit_item_ids",
        ]

    def validate_district(self, value):
        try:
            district = District.objects.get(name__iexact=value.strip())
        except District.DoesNotExist:
            raise serializers.ValidationError(
                "This district does not exist in the available district list."
            )

        return district.name

    def validate(self, attrs):
        availability = attrs["availability"]
        district = attrs["district"]

        if not availability.districts.filter(
            name__iexact=district
        ).exists():
            raise serializers.ValidationError({
                "district": (
                    "This district is not available for the selected date and time."
                )
            })

        start_time = attrs["start_time"]
        booked_hours = attrs["booked_hours"]

        if not availability.is_available:
            raise serializers.ValidationError(
                {"availability": "This time slot is not available."}
            )

        if availability.date < timezone.localdate():
            raise serializers.ValidationError(
                {"availability": "You cannot book a date in the past."}
            )

        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = start_minutes + booked_hours * 60

        window_start = (
            availability.start_time.hour * 60
            + availability.start_time.minute
        )
        window_end = (
            availability.end_time.hour * 60
            + availability.end_time.minute
        )

        if window_end <= window_start:
            raise serializers.ValidationError(
                {"availability": "This availability window has invalid times."}
            )

        if start_minutes < window_start or end_minutes > window_end:
            raise serializers.ValidationError({
                "start_time": (
                    "Your selected start time and duration must fit "
                    "inside the available time window."
                )
            })

        if availability.date == timezone.localdate():
            now = timezone.localtime()
            current_minutes = now.hour * 60 + now.minute

            if start_minutes <= current_minutes:
                raise serializers.ValidationError(
                    {"start_time": "Choose a future starting time."}
                )

        attrs["end_time"] = (
            datetime.combine(availability.date, start_time)
            + timedelta(hours=booked_hours)
        ).time()

        settings = SiteSettings.objects.first()

        if not settings or settings.hourly_rate <= 0:
            raise serializers.ValidationError(
                "Booking is not available yet."
            )

        attrs["hourly_rate"] = settings.hourly_rate
        attrs["total_amount"] = settings.hourly_rate * booked_hours

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        activities = validated_data.pop("activities", [])
        outfit_items = validated_data.pop("outfit_item_ids", [])

        booking = Booking.objects.create(**validated_data)
        booking.activities.set(activities)

        for item in outfit_items:
            BookingOutfitSelection.objects.create(
                booking=booking,
                outfit_item=item,
                item_name=item.name,
                item_specifications=item.specifications,
                item_image=item.image.url if item.image else "",
            )

        return booking
