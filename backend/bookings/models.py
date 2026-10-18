from django.db import models


class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Availability(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=False)
    booking_gap_minutes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Custom gap for this date in minutes. Leave empty to use the global default.",
    )

    districts = models.ManyToManyField(
        District,
        related_name="availabilities",
        blank=True,
    )

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("date", "start_time", "end_time")

    def __str__(self):
        return f"{self.date} | {self.start_time} - {self.end_time}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Payment"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_age = models.PositiveSmallIntegerField()
    district = models.CharField(max_length=100)

    availability = models.ForeignKey(
        Availability,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    activities = models.ManyToManyField(
        "website.Activity",
        related_name="bookings",
        blank=True,
    )

    booked_hours = models.PositiveSmallIntegerField(default=4)

    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    hold_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.availability.date}"

class BookingOutfitSelection(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="outfit_selections",
    )

    outfit_item = models.ForeignKey(
        "website.OutfitItem",
        on_delete=models.PROTECT,
        related_name="booking_selections",
    )

    item_name = models.CharField(max_length=120)
    item_specifications = models.TextField(blank=True)
    item_image = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f"{self.booking} - {self.item_name}"