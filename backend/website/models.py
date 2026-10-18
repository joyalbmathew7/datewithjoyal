from django.db import models

class Profile(models.Model):
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    bio = models.TextField()
    contact_number = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProfilePhoto(models.Model):
    class PhotoType(models.TextChoices):
        PROFILE = "PROFILE", "Profile"
        GALLERY = "GALLERY", "Gallery"
        OUTFIT = "OUTFIT", "Outfit"

    # 👈 These fields must be OUTSIDE the PhotoType class, 
    # directly under ProfilePhoto with standard indentation:
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="profile_photos/")
    photo_type = models.CharField(
        max_length=10,
        choices=PhotoType.choices,
        default=PhotoType.GALLERY,
    )
    caption = models.CharField(max_length=150, blank=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.name} - {self.photo_type}"

class Activity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # price = models.DecimalField(max_digits=10, decimal_places=2)
    # duration_hours = models.PositiveSmallIntegerField(default=1)
    image = models.ImageField(
        upload_to="activities/",
        blank=True,
        null=True,
        )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SiteSettings(models.Model):
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    minimum_booking_hours = models.PositiveSmallIntegerField(
        default=4,
    )

    booking_gap_minutes = models.PositiveSmallIntegerField(
        default=60,
        help_text="Default gap between bookings, in minutes. 60 = 1 hour.",
    )

    def __str__(self):
        return "Website Settings"




class OutfitCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class OutfitItem(models.Model):
    category = models.ForeignKey(
        OutfitCategory,
        on_delete=models.PROTECT,
        related_name="items",
    )
    name = models.CharField(max_length=120)
    image = models.ImageField(upload_to="outfits/")
    specifications = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.category.name})"
